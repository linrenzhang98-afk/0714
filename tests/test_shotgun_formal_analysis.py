import json
import math
import tempfile
import unittest
from pathlib import Path

from shotgun_analysis.core import (
    aitchison_distance,
    classified_fraction,
    close_composition,
    clr_transform,
    diversity_metrics,
    prevalence_filter,
    pseudocount_replace,
)
from shotgun_analysis.czm import exact_czm
from shotgun_analysis.errors import DegenerateDesignError, DependencyError, InputValidationError
from shotgun_analysis.io import load_common_layer_direct_species_counts, load_direct_species_counts, validate_cohort_manifest, validate_sample_alignment
from shotgun_analysis.permutation import restricted_permutations
from shotgun_analysis.pipeline import analyze_cohort, pseudocount_backend
from shotgun_analysis.results import validate_result, write_json
from shotgun_analysis.stats import adjust_pvalues, permanova, permdisp


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "reports_public/formal_cross_cohort_analysis/result_schema.json"


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
    counts = [
        [8 + (i % 3), 1 + ((i * 2) % 4), 0 if i % 2 else 2, 1 + (i % 5)]
        for i in range(12)
    ]
    return sample_ids, groups, counts


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

    def test_missing_sample_detection(self):
        with self.assertRaisesRegex(InputValidationError, "missing"):
            validate_sample_alignment(["SYN_001", "SYN_002"], ["SYN_001", "SYN_003"])

    def test_malformed_count_input(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.tsv"
            path.write_text("sample_id\ttax1\nSYN_001\tbad\n")
            with self.assertRaises(InputValidationError):
                load_direct_species_counts(path)

    def test_taxon_major_common_layer_loading(self):
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
    def test_prevalence_and_boundary_and_all_zero_taxon(self):
        matrix = [[1, 0, 0], [0, 1, 0], [0, 0, 0], [0, 0, 0]]
        # The core correctly stops all-zero samples before filtering.
        with self.assertRaisesRegex(InputValidationError, "all-zero sample"):
            prevalence_filter(matrix, ["a", "b", "never"], 0.25)
        matrix = [[1, 0, 0, 1], [0, 1, 0, 1], [0, 0, 1, 1], [0, 0, 0, 1]]
        result = prevalence_filter(matrix, ["a", "b", "c", "always"], 0.25)
        self.assertEqual(result.feature_names, ["a", "b", "c", "always"])
        self.assertEqual(result.detected_counts, [1, 1, 1, 4])
        strict = prevalence_filter(matrix, ["a", "b", "c", "always"], 0.26)
        self.assertEqual(strict.feature_names, ["always"])
        zero_removed = prevalence_filter([[1, 0], [2, 0]], ["kept", "never"], 0.5)
        self.assertEqual(zero_removed.feature_names, ["kept"])

    def test_all_zero_after_filter_fail_stop(self):
        with self.assertRaisesRegex(InputValidationError, "after prevalence"):
            prevalence_filter([[1, 0], [0, 2], [0, 2]], ["rare", "common"], 2 / 3)

    def test_closure_sums_and_clr_centering(self):
        closed = close_composition(pseudocount_replace([[1, 0, 3], [2, 4, 0]]))
        self.assertTrue(all(abs(sum(row) - 1) < 1e-12 for row in closed))
        clr = clr_transform(closed)
        self.assertTrue(all(abs(sum(row)) < 1e-12 for row in clr))

    def test_aitchison_properties_and_determinism(self):
        closed = close_composition([[1, 2, 3], [3, 2, 1], [2, 2, 2]])
        first = aitchison_distance(closed)
        second = aitchison_distance(closed)
        self.assertEqual(first, second)
        for i in range(3):
            self.assertEqual(first[i][i], 0)
            for j in range(3):
                self.assertAlmostEqual(first[i][j], first[j][i])

    def test_czm_interface_fails_closed_without_library(self):
        with self.assertRaises(DependencyError):
            exact_czm([[1, 0], [0, 1]], r_library="/definitely/not/a/library")


class InferenceTests(unittest.TestCase):
    def setUp(self):
        _, self.groups, counts = synthetic_inputs()
        self.distance = aitchison_distance(close_composition(pseudocount_replace(counts)))

    def test_permanova_deterministic_seed(self):
        first = permanova(self.distance, self.groups, permutations=99, seed=20260830)
        second = permanova(self.distance, self.groups, permutations=99, seed=20260830)
        self.assertEqual(first, second)

    def test_restricted_permutations_stay_within_strata(self):
        strata = ["Training", "Test"] * 6
        for permutation in restricted_permutations(12, 25, 19, strata):
            self.assertTrue(all(strata[target] == strata[source] for target, source in enumerate(permutation)))

    def test_permdisp_behavior_and_determinism(self):
        first = permdisp(self.distance, self.groups, permutations=49, seed=31415)
        second = permdisp(self.distance, self.groups, permutations=49, seed=31415)
        self.assertEqual(first, second)
        self.assertGreaterEqual(first.effect_size, 0)
        self.assertLessEqual(first.p_value, 1)

    def test_degenerate_group_handling(self):
        with self.assertRaises(DegenerateDesignError):
            permanova(self.distance, ["A"] * 12, permutations=9, seed=1)
        with self.assertRaises(DegenerateDesignError):
            permdisp(self.distance, ["A"] * 11 + ["B"], permutations=9, seed=1)

    def test_bh_adjustment(self):
        self.assertEqual(adjust_pvalues([0.01, 0.04, 0.03, 0.002], "BH"), [0.02, 0.04, 0.04, 0.008])

    def test_holm_adjustment(self):
        self.assertEqual(adjust_pvalues([0.01, 0.04, 0.03, 0.002], "holm"), [0.03, 0.06, 0.06, 0.008])


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

    def test_mocked_czm_pipeline_and_result_schema(self):
        sample_ids, groups, counts = synthetic_inputs()
        # A precomputed/mocked positive replacement is allowed only in synthetic tests.
        result = analyze_cohort(
            cohort_id="SYNTHETIC_COHORT", sample_ids=sample_ids, groups=groups, counts=counts,
            feature_names=["SYN_TAXON_A", "SYN_TAXON_B", "SYN_TAXON_C", "SYN_TAXON_D"],
            total_reads=[1000] * 12, classified_reads=[100 + i for i in range(12)],
            prevalence=0.1, zero_method="MOCK_PRECOMPUTED_CZM_FIXTURE",
            zero_replacement=pseudocount_backend(0.5), permanova_seed=10, permdisp_seed=11,
            permutations=49, strata=["Training", "Test"] * 6,
            secondary_contrasts=[("A", "B"), ("A", "C"), ("B", "C")],
            provenance={"fixture": "synthetic_test_v1"},
        )
        validate_result(result, SCHEMA)
        self.assertEqual(result["analysis_status"], "SYNTHETIC")
        self.assertFalse(result["interpretation_boundary"]["classified_fraction_is_bacterial_biomass"])
        self.assertEqual(len(result["secondary_contrasts"]), 15)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "result.json"
            write_json(output, result, SCHEMA)
            self.assertEqual(json.loads(output.read_text())["schema_version"], "1.0.0")

    def test_result_schema_rejects_malformed(self):
        with self.assertRaises(InputValidationError):
            validate_result({"schema_version": "1.0.0"}, SCHEMA)

    def test_result_serialization_rejects_nan(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(InputValidationError):
                write_json(Path(directory) / "bad.json", {"bad": math.nan})


if __name__ == "__main__":
    unittest.main()
