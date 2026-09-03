import copy
import json
import math
import tempfile
import unittest
import shutil
from unittest.mock import patch
from pathlib import Path

from shotgun_analysis.contracts import (
    EXPECTED_ISOLATED_R_LIBRARY, analysis_role, expected_production_seeds,
    validate_expected_czm_library, validate_production_contract, validate_production_strata,
    normalize_anchor_strata,
)
from shotgun_analysis.core import (
    additive_pseudocount,
    aitchison_distance,
    classified_fraction,
    close_composition,
    clr_transform,
    deterministic_pca,
    diversity_metrics,
    prevalence_filter,
    zero_replacement_diagnostics,
)
from shotgun_analysis.czm import (
    MGSHOTGUN_BIN, RSCRIPT_PATH, exact_czm, expected_package_versions,
    validate_runtime_package_versions,
)
from shotgun_analysis.errors import DegenerateDesignError, DependencyError, InputValidationError
from shotgun_analysis.io import (
    load_common_layer_direct_species_counts, load_direct_species_counts,
    unique_row_index, validate_cohort_manifest, validate_sample_alignment,
)
from shotgun_analysis.permutation import restricted_permutations, validate_block_exchangeability
from shotgun_analysis.pipeline import analyze_cohort, pseudocount_backend
from shotgun_analysis.results import validate_result, write_json
from shotgun_analysis.production_package import analysis_manifest, output_hashes, validate_czm_gate, validate_pinned_czm_gate, PINNED_GATE_ROOT, REQUIRED_ARTIFACTS
from shotgun_analysis.stats import (
    adjust_pvalues, centroid_distance_summaries, distances_to_group_centroid, mann_whitney, permanova,
    permdisp, permdisp_reference_statistics,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "reports_public/formal_cross_cohort_analysis/result_schema.json"
PERMDISP_REFERENCE = ROOT / "tests/fixtures/permdisp_centroid_reference.json"


def fake_rows():
    return [
        {"sample_id": "SYN_001", "run_id": "SYN_RUN_001", "group": "A", "split": "Training"},
        {"sample_id": "SYN_002", "run_id": "SYN_RUN_002", "group": "A", "split": "Test"},
        {"sample_id": "SYN_003", "run_id": "SYN_RUN_003", "group": "B", "split": "Training"},
        {"sample_id": "SYN_004", "run_id": "SYN_RUN_004", "group": "B", "split": "Test"},
    ]


def synthetic_inputs():
    sample_ids = [f"SYN_{index:03d}" for index in range(1, 13)]
    groups = ["A"] * 4 + ["B"] * 4 + ["C"] * 4
    counts = [[8 + i % 3, 1 + (i * 2) % 4, 0 if i % 2 else 2, 1 + i % 5] for i in range(12)]
    return sample_ids, groups, counts


def synthetic_result():
    sample_ids, groups, counts = synthetic_inputs()
    return analyze_cohort(
        cohort_id="SYNTHETIC_COHORT", sample_ids=sample_ids, groups=groups, counts=counts,
        feature_names=["SYN_TAXON_A", "SYN_TAXON_B", "SYN_TAXON_C", "SYN_TAXON_D"],
        total_reads=[1000] * 12, classified_reads=[100 + i for i in range(12)],
        prevalence=0.1, zero_method="additive_pseudocount",
        zero_replacement=pseudocount_backend(0.5), permanova_seed=10, permdisp_seed=11,
        permutations=49, strata=["Training", "Test"] * 6,
        secondary_contrasts=[("A", "B"), ("A", "C"), ("B", "C")],
        provenance={"fixture": "synthetic_test_v2"}, execution_mode="development",
    )


def synthetic_anchor_production_result():
    """Schema-valid synthetic metadata shaped like the frozen production contract."""
    result = synthetic_result()
    group_counts = {
        "Bacterial infection": 114, "Fungal infection": 78,
        "Lung cancer": 122, "Pulmonary tuberculosis": 86,
    }
    groups = [group for group, count in group_counts.items() for _ in range(count)]
    template = result["sample_metrics"][0]
    result["sample_metrics"] = [
        {**template, "sample_id": f"SYN_PRODUCTION_{index:03d}", "group": group}
        for index, group in enumerate(groups, start=1)
    ]
    result.update({
        "execution_mode": "production", "analysis_status": "BIOLOGICAL",
        "analysis_role": "ZERO_METHOD_SENSITIVITY", "cohort": "PRJNA1056765",
        "n": 400, "group_counts": group_counts,
        "contrast_orientation": {
            "type": "omnibus", "levels": list(group_counts), "signed_effect": False,
        },
        "secondary_contrasts": [],
        "permutation_design": {
            "restriction": "within declared strata",
            "block_cross_tabulation": {
                "Training": {
                    "Bacterial infection": 57, "Fungal infection": 39,
                    "Lung cancer": 61, "Pulmonary tuberculosis": 43,
                },
                "Test": {
                    "Bacterial infection": 57, "Fungal infection": 39,
                    "Lung cancer": 61, "Pulmonary tuberculosis": 43,
                },
            },
            "blocking_adjusts_split_or_batch_effect": False,
        },
        "provenance": {
            "python": "synthetic", "manifest_sha256": "0" * 64,
            "counts_sha256": "1" * 64, "sample_qc_sha256": "2" * 64,
            "czm_adapter_sha256": "3" * 64, "implementation_commit": "4" * 40,
            "method_runtime": {"python": "synthetic", "R_required": False},
        },
    })
    result["zero_replacement_diagnostics"]["zero_fraction_per_sample"] = [0.0] * 400
    result["zero_replacement_diagnostics"]["replacement_perturbation_total_variation_per_sample"] = [0.0] * 400
    ordination = result["beta_diversity"]["ordination"]
    coordinate_template = ordination["sample_coordinates"][0]
    ordination["sample_coordinates"] = [
        {**coordinate_template, "sample_id": row["sample_id"], "group": row["group"]}
        for row in result["sample_metrics"]
    ]
    for name, seed in (("permanova", 105777510), ("permdisp", 105777511)):
        result["beta_diversity"][name]["group_counts"] = group_counts
        result["beta_diversity"][name]["permutations"] = 9999
        result["beta_diversity"][name]["seed"] = seed
        result["beta_diversity"][name]["df_between"] = 3
        result["beta_diversity"][name]["df_within"] = 396
    return result


class ManifestAndInputTests(unittest.TestCase):
    def test_exact_expected_group_count_validation(self):
        validate_cohort_manifest(fake_rows(), {"A": 2, "B": 2}, required_columns=["split"])
        with self.assertRaises(InputValidationError):
            validate_cohort_manifest(fake_rows(), {"A": 3, "B": 1})

    def test_duplicate_run_detection(self):
        rows = fake_rows()
        rows[1]["run_id"] = rows[0]["run_id"]
        with self.assertRaisesRegex(InputValidationError, "duplicate run"):
            validate_cohort_manifest(rows, {"A": 2, "B": 2})

    def test_qc_duplicate_identical_rows_fail_before_index(self):
        rows = [{"run": "SYN_RUN_1", "x": "1"}, {"run": "SYN_RUN_1", "x": "1"}]
        with self.assertRaisesRegex(InputValidationError, "SYN_RUN_1"):
            unique_row_index(rows, "run", record_label="sample-QC run")

    def test_qc_duplicate_conflicting_rows_fail_before_index(self):
        rows = [{"run": "SYN_RUN_1", "x": "1"}, {"run": "SYN_RUN_1", "x": "2"}]
        with self.assertRaisesRegex(InputValidationError, "conflicting metadata"):
            unique_row_index(rows, "run", record_label="sample-QC run")

    def test_missing_sample_detection(self):
        with self.assertRaisesRegex(InputValidationError, "missing"):
            validate_sample_alignment(["SYN_001", "SYN_002"], ["SYN_001", "SYN_003"])

    def test_malformed_count_input(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.tsv"
            path.write_text("sample_id\ttax1\nSYN_001\tbad\n")
            with self.assertRaises(InputValidationError):
                load_direct_species_counts(path)

    def test_duplicate_tsv_header_fails_before_mapping(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate_header.tsv"
            path.write_text("sample_id\ttaxon\ttaxon\nSYN_001\t1\t2\n")
            with self.assertRaisesRegex(InputValidationError, "duplicate TSV header"):
                load_direct_species_counts(path)

    def test_taxon_major_common_layer_loading_orientation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "common.tsv"
            path.write_text(
                "taxid\trank\tscientific_name\tprevalence\tpresent_5pct\tpresent_10pct\tpresent_20pct\tSYN_001\tSYN_002\n"
                "11\tS\tSynthetic one\t1\tTrue\tTrue\tTrue\t2\t3\n"
                "22\tS\tSynthetic two\t0.5\tTrue\tTrue\tTrue\t0\t4\n"
            )
            table = load_common_layer_direct_species_counts(path, ["SYN_001", "SYN_002"])
            self.assertEqual(table.feature_names, ["11", "22"])
            self.assertEqual(table.matrix, [[2.0, 0.0], [3.0, 4.0]])

    def test_nan_inf_and_all_zero_rejection(self):
        for matrix in ([[1, math.nan]], [[1, math.inf]], [[0, 0]]):
            with self.assertRaises(InputValidationError):
                prevalence_filter(matrix, ["a", "b"], 0.1)


class CompositionTests(unittest.TestCase):
    def test_prevalence_boundary_and_all_zero_taxon(self):
        matrix = [[1, 0, 0, 1], [0, 1, 0, 1], [0, 0, 1, 1], [0, 0, 0, 1]]
        result = prevalence_filter(matrix, ["a", "b", "c", "always"], 0.25)
        self.assertEqual(result.detected_counts, [1, 1, 1, 4])
        self.assertEqual(prevalence_filter(matrix, ["a", "b", "c", "always"], 0.26).feature_names, ["always"])
        self.assertEqual(prevalence_filter([[1, 0], [2, 0]], ["kept", "never"], 0.5).feature_names, ["kept"])

    def test_all_zero_after_filter_fail_stop(self):
        with self.assertRaisesRegex(InputValidationError, "after prevalence"):
            prevalence_filter([[1, 0], [0, 2], [0, 2]], ["rare", "common"], 2 / 3)

    def test_additive_pseudocount_applies_to_every_feature(self):
        self.assertEqual(additive_pseudocount([[0, 2, 5]], 0.5), [[0.5, 2.5, 5.5]])

    def test_closure_sums_and_clr_centering(self):
        closed = close_composition(additive_pseudocount([[1, 0, 3], [2, 4, 0]]))
        self.assertTrue(all(abs(sum(row) - 1) < 1e-12 for row in closed))
        self.assertTrue(all(abs(sum(row)) < 1e-12 for row in clr_transform(closed)))

    def test_aitchison_properties_and_determinism(self):
        closed = close_composition([[1, 2, 3], [3, 2, 1], [2, 2, 2]])
        first = aitchison_distance(closed)
        self.assertEqual(first, aitchison_distance(closed))
        for i in range(3):
            self.assertEqual(first[i][i], 0)
            for j in range(3):
                self.assertAlmostEqual(first[i][j], first[j][i])

    def test_zero_diagnostics(self):
        diagnostics = zero_replacement_diagnostics([[0, 2], [1, 0]], [[0.5, 2.5], [1.5, 0.5]], ["x", "y"])
        self.assertEqual(diagnostics["zero_cells"], 2)
        self.assertEqual(diagnostics["zero_fraction_overall"], 0.5)
        self.assertEqual(diagnostics["zero_fraction_per_sample"], [0.5, 0.5])
        self.assertFalse(diagnostics["used_for_exclusion"])

    def test_ordination_deterministic_and_centered(self):
        clr = clr_transform(close_composition(additive_pseudocount([[1, 0, 3], [2, 4, 0], [4, 1, 2], [3, 5, 1]])))
        first = deterministic_pca(clr, axes=2)
        second = deterministic_pca(clr, axes=2)
        self.assertEqual(first, second)
        for axis in range(len(first["axis_labels"])):
            self.assertAlmostEqual(sum(row[axis] for row in first["coordinates"]), 0.0, places=8)


class InferenceTests(unittest.TestCase):
    def setUp(self):
        _, self.groups, counts = synthetic_inputs()
        self.distance = aitchison_distance(close_composition(additive_pseudocount(counts)))

    def test_permanova_deterministic_seed_and_effect_sanity(self):
        first = permanova(self.distance, self.groups, permutations=99, seed=20260830)
        self.assertEqual(first, permanova(self.distance, self.groups, permutations=99, seed=20260830))
        self.assertGreaterEqual(first.effect_size, 0)
        self.assertLessEqual(first.effect_size, 1)

    def test_restricted_permutations_stream_and_stay_within_strata(self):
        strata = ["Training", "Test"] * 6
        iterator = restricted_permutations(12, 25, 19, strata)
        self.assertFalse(isinstance(iterator, list))
        for permutation in iterator:
            self.assertTrue(all(strata[target] == strata[source] for target, source in enumerate(permutation)))

    def test_block_exchangeability_cross_tabulation(self):
        table = validate_block_exchangeability(self.groups, ["Training", "Test"] * 6)
        self.assertEqual(table["Training"], {"A": 2, "B": 2, "C": 2})

    def test_block_exchangeability_pathologies_fail(self):
        with self.assertRaisesRegex(InputValidationError, "B=0"):
            validate_block_exchangeability(["A", "A", "B", "B"], ["Training", "Training", "Test", "Test"])
        with self.assertRaisesRegex(InputValidationError, "A=1"):
            validate_block_exchangeability(["A", "B", "A", "B"], ["Training", "Training", "Test", "Test"])

    def test_permdisp_against_trusted_locked_residual_reference(self):
        fixture = json.loads(PERMDISP_REFERENCE.read_text())
        points = fixture["points"]
        distance = [[abs(left - right) for right in points] for left in points]
        observed_distances = distances_to_group_centroid(distance, fixture["groups"])
        self.assertEqual(observed_distances, fixture["observed_distances_to_centroid"])
        observed = permdisp(distance, fixture["groups"], permutations=49, seed=31415)
        self.assertAlmostEqual(observed.statistic, fixture["observed_f"])
        self.assertAlmostEqual(observed.effect_size, fixture["observed_eta_squared"])
        expected = fixture["expected_permuted_f"]
        actual = permdisp_reference_statistics(
            observed_distances, fixture["groups"], fixture["permutation_maps"]
        )
        for left, right in zip(actual, expected):
            self.assertAlmostEqual(left, right, places=12)
        self.assertIn("residual permutation", observed.algorithm)

    def test_permdisp_is_deterministic(self):
        self.assertEqual(
            permdisp(self.distance, self.groups, permutations=49, seed=31415),
            permdisp(self.distance, self.groups, permutations=49, seed=31415),
        )

    def test_non_euclidean_centroid_truncation_is_explicit(self):
        distance = [
            [0, 1, 1, 2, 2, 2],
            [1, 0, 10, 2, 2, 2],
            [1, 10, 0, 2, 2, 2],
            [2, 2, 2, 0, 1, 1],
            [2, 2, 2, 1, 0, 1],
            [2, 2, 2, 1, 1, 0],
        ]
        summary = centroid_distance_summaries(
            distance, ["A", "A", "A", "B", "B", "B"], require_euclidean=False,
        )
        self.assertEqual(summary["negative_squared_distances_truncated_to_zero"], 1)

    def test_degenerate_group_handling(self):
        with self.assertRaises(DegenerateDesignError):
            permanova(self.distance, ["A"] * 12, permutations=9, seed=1)
        with self.assertRaises(DegenerateDesignError):
            permdisp(self.distance, ["A"] * 11 + ["B"], permutations=9, seed=1)

    def test_rank_biserial_orientation_invariant_to_row_order(self):
        first = mann_whitney([10, 11, 1, 2], ["A", "A", "B", "B"], positive_group="A", negative_group="B")
        second = mann_whitney([1, 10, 2, 11], ["B", "A", "B", "A"], positive_group="A", negative_group="B")
        self.assertEqual(first["rank_biserial"], 1.0)
        self.assertEqual(first["rank_biserial"], second["rank_biserial"])

    def test_binary_pipeline_effect_directions_survive_row_reordering(self):
        sample_ids = [f"SYN_EXT_{index}" for index in range(6)]
        groups = ["Drug_Resistance"] * 3 + ["Drug_Sensitive"] * 3
        counts = [[9, 1], [8, 0], [7, 3], [3, 7], [0, 8], [1, 9]]
        classified = [100, 110, 120, 70, 80, 90]

        def run(order):
            return analyze_cohort(
                cohort_id="SYN_EXT", sample_ids=[sample_ids[i] for i in order],
                groups=[groups[i] for i in order], counts=[counts[i] for i in order],
                feature_names=["SYN_TAXON_1", "SYN_TAXON_2"], total_reads=[1000] * 6,
                classified_reads=[classified[i] for i in order], prevalence=0.1,
                zero_method="additive_pseudocount", zero_replacement=pseudocount_backend(),
                permanova_seed=41, permdisp_seed=42, permutations=19,
                binary_orientation=("Drug_Resistance", "Drug_Sensitive"),
            )

        first = run(list(range(6)))
        order = [5, 0, 4, 1, 3, 2]
        second = run(order)
        for endpoint in first["secondary_endpoints"]:
            self.assertEqual(
                first["secondary_endpoints"][endpoint]["rank_biserial"],
                second["secondary_endpoints"][endpoint]["rank_biserial"],
            )
            self.assertEqual(first["secondary_endpoints"][endpoint]["positive_group"], "Drug_Resistance")

    def test_multiplicity_adjustments(self):
        self.assertEqual(adjust_pvalues([0.01, 0.04, 0.03, 0.002], "BH"), [0.02, 0.04, 0.04, 0.008])
        self.assertEqual(adjust_pvalues([0.01, 0.04, 0.03, 0.002], "holm"), [0.03, 0.06, 0.06, 0.008])


class ProductionContractTests(unittest.TestCase):
    def test_verified_anchor_strata_normalization(self):
        self.assertEqual(normalize_anchor_strata(["Training Cohort", "Test Cohort"]), ["Training", "Test"])
        for invalid in (["Training Cohort", ""], ["Training Cohort", "Training Cohort"], ["Training", "Test"]):
            with self.assertRaises(InputValidationError):
                normalize_anchor_strata(invalid)
    def test_allowed_method_cells(self):
        self.assertEqual(analysis_role(0.1, "czm", "Aitchison"), "PRIMARY")
        self.assertEqual(analysis_role(0.05, "czm", "Aitchison"), "FILTER_SENSITIVITY")
        self.assertEqual(analysis_role(0.2, "additive_pseudocount", "Aitchison"), "ZERO_METHOD_SENSITIVITY")
        self.assertEqual(analysis_role(0.1, "none", "Bray-Curtis"), "BRAY_CURTIS_SENSITIVITY")

    def test_arbitrary_production_method_cells_rejected(self):
        for args in ((0.2, "none", "Bray-Curtis"), (0.1, "anything", "Aitchison"), (0.05, "none", "Bray-Curtis")):
            with self.assertRaises(InputValidationError):
                analysis_role(*args)

    def test_production_seed_contract_is_cell_specific_and_fixed(self):
        self.assertEqual(expected_production_seeds("anchor", 0.1, "czm", "Aitchison"), (105676510, 105676511))
        self.assertEqual(expected_production_seeds("external", 0.05, "additive_pseudocount", "Aitchison"), (47085510, 47085511))
        self.assertEqual(expected_production_seeds("external", 0.1, "none", "Bray-Curtis"), (47185010, 47185011))

    def test_wrong_production_n_and_permutations_rejected(self):
        with self.assertRaisesRegex(InputValidationError, "exactly 400"):
            validate_production_contract(
                cohort_key="anchor", cohort_id="PRJNA1056765", sample_ids=["SYN_1"] * 4,
                groups=["Bacterial infection"] * 4, prevalence=0.1, zero_method="czm",
                geometry="Aitchison", permanova_permutations=9999, permdisp_permutations=9999,
                permanova_seed=105676510, permdisp_seed=105676511,
            )

    def test_frozen_species_prefilter_dimensions(self):
        from shotgun_analysis.contracts import COHORT_CONTRACTS
        self.assertEqual(COHORT_CONTRACTS["anchor"]["species_prefilter_features"], 5198)
        self.assertEqual(COHORT_CONTRACTS["external"]["species_prefilter_features"], 4888)
        samples = [f"SYN_{i}" for i in range(400)]
        groups = ["Bacterial infection"] * 114 + ["Fungal infection"] * 78 + ["Lung cancer"] * 122 + ["Pulmonary tuberculosis"] * 86
        with self.assertRaisesRegex(InputValidationError, "exactly 9999"):
            validate_production_contract(
                cohort_key="anchor", cohort_id="PRJNA1056765", sample_ids=samples, groups=groups,
                prevalence=0.1, zero_method="czm", geometry="Aitchison",
                permanova_permutations=99, permdisp_permutations=9999,
                permanova_seed=105676510, permdisp_seed=105676511,
            )

    def test_wrong_production_seed_rejected_before_analysis(self):
        samples = [f"SYN_{i}" for i in range(130)]
        groups = ["Drug_Resistance"] * 49 + ["Drug_Sensitive"] * 81
        with self.assertRaisesRegex(InputValidationError, "frozen cell-specific seeds"):
            validate_production_contract(
                cohort_key="external", cohort_id="PRJCA046985", sample_ids=samples, groups=groups,
                prevalence=0.1, zero_method="czm", geometry="Aitchison",
                permanova_permutations=9999, permdisp_permutations=9999,
                permanova_seed=1, permdisp_seed=2,
            )

    def test_unexpected_production_czm_library_rejected(self):
        with self.assertRaisesRegex(InputValidationError, "frozen isolated path"):
            validate_expected_czm_library("/tmp/SYN_WRONG_LIBRARY")
        self.assertEqual(validate_expected_czm_library(EXPECTED_ISOLATED_R_LIBRARY), EXPECTED_ISOLATED_R_LIBRARY)

    def test_production_strata_names_are_exact(self):
        valid = ["Training"] * 200 + ["Test"] * 200
        validate_production_strata("anchor", valid)
        with self.assertRaisesRegex(InputValidationError, "exactly Training/Test"):
            validate_production_strata("anchor", ["Train"] * 200 + ["Test"] * 200)
        with self.assertRaisesRegex(InputValidationError, "unrestricted"):
            validate_production_strata("external", ["SYN_BLOCK"] * 130)


class EndpointAndSerializationTests(unittest.TestCase):
    def test_alpha_metrics(self):
        result = diversity_metrics([1, 1, 2, 0])
        self.assertEqual(result.richness, 3)
        self.assertAlmostEqual(result.shannon, -(0.25 * math.log(0.25) * 2 + 0.5 * math.log(0.5)))
        self.assertAlmostEqual(result.gini_simpson, 0.625)
        self.assertAlmostEqual(result.dominance, 0.5)

    def test_classified_fraction_denominator(self):
        self.assertEqual(classified_fraction(25, 100), 0.25)
        with self.assertRaises(InputValidationError):
            classified_fraction(101, 100)
        with self.assertRaises(InputValidationError):
            classified_fraction(0, 0)

    def test_pipeline_rejects_direct_species_reads_above_classified_total(self):
        sample_ids, groups, counts = synthetic_inputs()
        with self.assertRaisesRegex(InputValidationError, "exceed all classified"):
            analyze_cohort(
                cohort_id="SYNTHETIC_COHORT", sample_ids=sample_ids, groups=groups,
                counts=counts, feature_names=["a", "b", "c", "d"],
                total_reads=[1000] * 12, classified_reads=[1] * 12,
                prevalence=0.1, zero_method="additive_pseudocount",
                zero_replacement=pseudocount_backend(), permanova_seed=1,
                permdisp_seed=2, permutations=9,
            )

    def test_synthetic_pipeline_schema_and_contract_metadata(self):
        result = synthetic_result()
        validate_result(result, SCHEMA)
        self.assertEqual(result["zero_handling"], {
            "zero_method": "additive_pseudocount", "pseudocount": 0.5,
            "applied_to": "all_retained_features",
        })
        self.assertFalse(result["uncertainty_contract"]["confidence_intervals_generated"])
        self.assertEqual(len(result["secondary_contrasts"]), 15)
        self.assertIsNotNone(result["beta_diversity"]["ordination"])

    def test_schema_rejects_group_count_sum_mismatch(self):
        result = synthetic_result()
        result["group_counts"] = {"A": 2, "B": 2, "C": 2}
        with self.assertRaisesRegex(InputValidationError, "do not sum"):
            validate_result(result, SCHEMA)

    def test_schema_rejects_sample_row_count_mismatch(self):
        result = synthetic_result()
        result["sample_metrics"] = result["sample_metrics"][:-1]
        with self.assertRaisesRegex(InputValidationError, "row count"):
            validate_result(result, SCHEMA)

    def test_schema_rejects_duplicate_sample_ids(self):
        result = synthetic_result()
        result["sample_metrics"][1]["sample_id"] = result["sample_metrics"][0]["sample_id"]
        with self.assertRaisesRegex(InputValidationError, "duplicate"):
            validate_result(result, SCHEMA)

    def test_schema_rejects_classified_fraction_denominator_mismatch(self):
        result = synthetic_result()
        result["sample_metrics"][0]["classified_fraction"] = 0.99
        with self.assertRaisesRegex(InputValidationError, "read denominator"):
            validate_result(result, SCHEMA)

    def test_schema_rejects_zero_method_diagnostic_mismatch(self):
        result = synthetic_result()
        result["zero_replacement_diagnostics"]["replacement_applied"] = False
        with self.assertRaisesRegex(InputValidationError, "zero-method metadata"):
            validate_result(result, SCHEMA)

    def test_schema_rejects_contrast_orientation_mismatch(self):
        result = synthetic_result()
        result["secondary_contrasts"][0]["positive_group"] = "B"
        with self.assertRaisesRegex(InputValidationError, "label differs"):
            validate_result(result, SCHEMA)

    def test_production_schema_accepts_only_frozen_seed_and_algorithm(self):
        result = synthetic_anchor_production_result()
        validate_result(result, SCHEMA)
        wrong_seed = copy.deepcopy(result)
        wrong_seed["beta_diversity"]["permanova"]["seed"] += 1
        with self.assertRaisesRegex(InputValidationError, "frozen cell-specific seeds"):
            validate_result(wrong_seed, SCHEMA)
        wrong_algorithm = copy.deepcopy(result)
        wrong_algorithm["beta_diversity"]["permdisp"]["algorithm"] = "label permutation"
        with self.assertRaisesRegex(InputValidationError, "PERMDISP algorithm"):
            validate_result(wrong_algorithm, SCHEMA)
        wrong_blocks = copy.deepcopy(result)
        wrong_blocks["permutation_design"]["block_cross_tabulation"]["Training"]["Lung cancer"] -= 1
        with self.assertRaisesRegex(InputValidationError, "does not sum"):
            validate_result(wrong_blocks, SCHEMA)

    def test_production_schema_rejects_czm_from_other_library(self):
        result = synthetic_anchor_production_result()
        isolated = str(EXPECTED_ISOLATED_R_LIBRARY)
        result["analysis_role"] = "PRIMARY"
        result["zero_handling"] = {
            "zero_method": "CZM", "implementation": "zCompositions::cmultRepl",
            "version": "1.6.2", "parameters": {
                "label": 0, "method": "CZM", "output": "prop", "frac": 0.65,
                "threshold": 0.5, "adjust": True,
            },
        }
        result["beta_diversity"]["permanova"]["seed"] = 105676510
        result["beta_diversity"]["permdisp"]["seed"] = 105676511
        result["provenance"]["method_runtime"] = {
            "R_version": "4.5.3", "effective_libPaths": isolated + ";/usr/lib/R/library",
            "isolated_library": isolated, "zCompositions_version": "1.6.2",
            "zCompositions_path": isolated + "/zCompositions", "NADA_version": "1.6-1.2",
            "NADA_path": isolated + "/NADA", "truncnorm_version": "1.0-9",
            "truncnorm_path": isolated + "/truncnorm",
        }
        validate_result(result, SCHEMA)
        wrong_parameters = copy.deepcopy(result)
        wrong_parameters["zero_handling"]["parameters"]["threshold"] = 0.4
        with self.assertRaisesRegex(InputValidationError, "result schema validation failed"):
            validate_result(wrong_parameters, SCHEMA)
        result["provenance"]["method_runtime"]["isolated_library"] = "/tmp/SYN_WRONG_LIBRARY"
        with self.assertRaisesRegex(InputValidationError, "unexpected isolated library"):
            validate_result(result, SCHEMA)

    def test_result_serialization_rejects_nan(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(InputValidationError):
                write_json(Path(directory) / "bad.json", {"bad": math.nan})

    def test_czm_interface_fails_closed_without_library(self):
        with self.assertRaises(DependencyError):
            exact_czm([[1, 0], [0, 1]], r_library="/definitely/not/a/library")

    def test_czm_requires_complete_path_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            library = root / "lib"
            library.mkdir()
            fake = root / "fake-rscript"
            fake.write_text(
                "#!/usr/bin/env python3\n"
                "import pathlib,sys\n"
                "inp,out,lib,prov=map(pathlib.Path,sys.argv[3:7])\n"
                "rows=[[float(x) for x in line.split('\\t')] for line in inp.read_text().splitlines()]\n"
                "out.write_text('\\n'.join('\\t'.join(str(x+0.1) for x in row) for row in rows)+'\\n')\n"
                "items={'R_version':'4.5.3','effective_libPaths':str(lib),'isolated_library':str(lib),"
                "'zCompositions_version':'1.6.2','zCompositions_path':str(lib/'zCompositions'),"
                "'NADA_version':'1.6-1.2','NADA_path':str(lib/'NADA'),'truncnorm_version':'1.0-9','truncnorm_path':str(lib/'truncnorm')}\n"
                "prov.write_text('\\n'.join(f'{k}\\t{v}' for k,v in items.items())+'\\n')\n"
            )
            fake.chmod(0o755)
            runtime = {}
            output = exact_czm([[1, 0], [0, 1]], r_library=library, rscript=str(fake), runtime_provenance=runtime)
            self.assertEqual(output, [[1.1, 0.1], [0.1, 1.1]])
            self.assertTrue(runtime["zCompositions_path"].startswith(str(library)))

    def test_exact_lock_format_versions_pass_without_numeric_coercion(self):
        expected = expected_package_versions()
        self.assertEqual(expected, {"zCompositions": "1.6.2", "NADA": "1.6-1.2", "truncnorm": "1.0-9"})
        validate_runtime_package_versions({
            "zCompositions_version": "1.6.2",
            "NADA_version": "1.6-1.2",
            "truncnorm_version": "1.0-9",
        }, expected)

    def test_nada_canonicalized_wrong_and_whitespace_versions_fail_closed(self):
        expected = expected_package_versions()
        for observed in ("1.6-1.1", "1.6-1.2 ", "1.6.1.2"):
            with self.assertRaisesRegex(DependencyError, "NADA version mismatch"):
                validate_runtime_package_versions({
                    "zCompositions_version": "1.6.2", "NADA_version": observed,
                    "truncnorm_version": "1.0-9",
                }, expected)

    def test_truncnorm_and_zcompositions_mismatches_fail_closed(self):
        expected = expected_package_versions()
        for package, key, value in (("truncnorm", "truncnorm_version", "1.0.9"),
                                    ("zCompositions", "zCompositions_version", "1.6.3")):
            observed = {"zCompositions_version": "1.6.2", "NADA_version": "1.6-1.2", "truncnorm_version": "1.0-9"}
            observed[key] = value
            with self.assertRaisesRegex(DependencyError, package + " version mismatch"):
                validate_runtime_package_versions(observed, expected)

    def test_r_adapter_reads_raw_description_versions(self):
        source = (ROOT / "shotgun_analysis/run_czm.R").read_text()
        self.assertIn('packageDescription(package, lib.loc=isolated, fields="Version")', source)
        self.assertNotIn('packageVersion("NADA")', source)
        self.assertNotIn('packageVersion("truncnorm")', source)

    def test_production_czm_default_is_absolute_and_preserves_path(self):
        self.assertEqual(RSCRIPT_PATH, "/home/suma/anaconda3/envs/mgshotgun/bin/Rscript")
        with patch.dict("os.environ", {"PATH": "/usr/local/bin:/usr/bin:/bin"}, clear=True):
            from shotgun_analysis.czm import r_environment
            path = r_environment()["PATH"].split(":")
        self.assertEqual(path[0], MGSHOTGUN_BIN)
        self.assertTrue({"/usr/bin", "/bin"}.issubset(path))

    def test_production_r_adapter_has_robust_return_extraction(self):
        source = (ROOT / "shotgun_analysis/run_czm.R").read_text()
        self.assertIn("is.matrix(candidate) || is.data.frame(candidate)", source)
        self.assertIn("length(candidates) != 1L", source)
        self.assertIn("selected_component_path", source)

    def test_gate_content_and_hash_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "gate.json"
            gate = {"job_id": "wrong"}
            path.write_text(json.dumps(gate))
            with self.assertRaisesRegex(InputValidationError, "incomplete"):
                validate_czm_gate(Path(directory) / "missing")

    def test_pinned_gate_passes_and_mutations_fail_closed(self):
        self.assertEqual(validate_pinned_czm_gate()["job_id"], "20260904T060000Z-0714-zcompositions-1-6-2-isolated-czm-syntax-validation")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "gate"
            shutil.copytree(PINNED_GATE_ROOT, root)
            validation = root / "r_czm_install_validation.json"
            validation.write_bytes(validation.read_bytes()[:-1] + b" ")
            with self.assertRaisesRegex(InputValidationError, "validation evidence SHA256"):
                validate_czm_gate(root)
            shutil.copytree(PINNED_GATE_ROOT, root / "summary_mutation")
            summary = root / "summary_mutation" / "r_czm_install_summary.md"
            summary.write_bytes(summary.read_bytes() + b" ")
            with self.assertRaisesRegex(InputValidationError, "summary evidence SHA256"):
                validate_czm_gate(root / "summary_mutation")

    def test_pinned_gate_semantic_mutations_fail_closed(self):
        mutations = [
            (lambda x: x.update(job_id="wrong"), "job_id"),
            (lambda x: x.update(status="BAD"), "status"),
            (lambda x: x["dependencies"]["zCompositions"].update(version="9.9.9"), "zCompositions version"),
            (lambda x: x["czm_probe"].update(passed=False), "synthetic probe"),
            (lambda x: x["system_library"].update(package_set_changed=True), "system library"),
        ]
        for mutate, message in mutations:
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory) / "gate"
                shutil.copytree(PINNED_GATE_ROOT, root)
                payload = json.loads((root / "r_czm_install_validation.json").read_text())
                mutate(payload)
                changed = json.dumps(payload, indent=2, sort_keys=True) + "\n"
                (root / "r_czm_install_validation.json").write_text(changed)
                provenance = json.loads((root / "czm_gate_provenance.json").read_text())
                provenance["source_validation_sha256"] = __import__("hashlib").sha256(changed.encode()).hexdigest()
                (root / "czm_gate_provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
                with self.assertRaisesRegex(InputValidationError, message):
                    validate_czm_gate(root)

    def test_pinned_gate_wrong_source_hash_and_missing_snapshot_fail_closed(self):
        with self.assertRaisesRegex(InputValidationError, "incomplete"):
            validate_czm_gate(ROOT / "provenance" / "czm_gate" / "missing")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "gate"
            shutil.copytree(PINNED_GATE_ROOT, root)
            provenance = json.loads((root / "czm_gate_provenance.json").read_text())
            provenance["source_validation_sha256"] = "0" * 64
            (root / "czm_gate_provenance.json").write_text(json.dumps(provenance) + "\n")
            with self.assertRaisesRegex(InputValidationError, "SHA256"):
                validate_czm_gate(root)

    def test_output_manifest_is_deterministic_and_nonrecursive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            names = [name for name in REQUIRED_ARTIFACTS if name not in {"analysis_manifest.json", "output_hashes.json"}]
            for name in names:
                (root / name).write_text("x\n")
            hashes = output_hashes(root, names)
            first = analysis_manifest({"analysis_id": "SYNTHETIC"}, hashes)
            self.assertEqual(first, analysis_manifest({"analysis_id": "SYNTHETIC"}, hashes))
            self.assertNotIn("analysis_manifest.json", first["output_hashes"])
            with self.assertRaisesRegex(InputValidationError, "recursive"):
                analysis_manifest({}, {**hashes, "analysis_manifest.json": "0" * 64})

    def test_empty_exclusions_contract_is_header_only(self):
        header = "cohort\tsample_id\treason\n"
        self.assertEqual(header.splitlines(), ["cohort\tsample_id\treason"])


if __name__ == "__main__":
    unittest.main()
