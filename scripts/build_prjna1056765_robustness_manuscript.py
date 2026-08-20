#!/usr/bin/env python3
"""Build the PRJNA1056765 robustness manuscript, figures, and supplement.

This is a packaging and visualization script. It reads frozen results and
performs no inferential calculation.
"""
from __future__ import annotations

import csv
import hashlib
import html
import json
import shutil
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports_public/prjna1056765_robustness_manuscript"
GRID = ROOT / "reports_public/metagenome_400_sensitivity_v2/frozen_sensitivity_grid.tsv"
GRID_MANIFEST = ROOT / "reports_public/metagenome_400_sensitivity_v2/manifest.json"


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, delimiter="\t", extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def esc(value) -> str:
    return html.escape(str(value))


class SVG:
    def __init__(self, title: str, width=1400, height=900):
        self.width, self.height = width, height
        self.parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            '<rect width="100%" height="100%" fill="#ffffff"/>',
            '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#20252b}.title{font-size:28px;font-weight:700}.panel{font-size:22px;font-weight:700}.head{font-size:18px;font-weight:700}.body{font-size:15px}.small{font-size:13px;fill:#4b5563}.tiny{font-size:11px;fill:#4b5563}</style>',
            f'<text x="45" y="45" class="title">{esc(title)}</text>',
        ]

    def rect(self, x, y, w, h, fill="#ffffff", stroke="#aeb7c2", sw=1, rx=4):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" rx="{rx}"/>')

    def line(self, x1, y1, x2, y2, stroke="#52606d", sw=1, dash=None):
        extra = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"{extra}/>' )

    def text(self, x, y, value, cls="body", anchor="start", fill=None):
        style = f' style="fill:{fill}"' if fill else ""
        self.parts.append(f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}"{style}>{esc(value)}</text>')

    def circle(self, x, y, r, fill, stroke="#ffffff", sw=1.5):
        self.parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def path(self, points, stroke, sw=2, fill="none"):
        coords = " ".join(f"{x},{y}" for x, y in points)
        self.parts.append(f'<polyline points="{coords}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def arrow(self, x1, y1, x2, y2, stroke="#52606d"):
        self.line(x1, y1, x2, y2, stroke, 2)
        self.parts.append(f'<polygon points="{x2},{y2} {x2-10},{y2-6} {x2-10},{y2+6}" fill="{stroke}"/>')

    def finish(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(self.parts + ["</svg>"]) + "\n", encoding="utf-8")


def section(text: str, start: str, end: str | None) -> str:
    begin = text.index(start) + len(start)
    finish = text.index(end, begin) if end else len(text)
    return text[begin:finish].strip()


def build_manuscript():
    stage1 = (ROOT / "manuscript_stage1_A-D.md").read_text(encoding="utf-8")
    stage2 = (ROOT / "manuscript_stage2_E-G.md").read_text(encoding="utf-8")
    legends = (ROOT / "figure_legends_stage1.md").read_text(encoding="utf-8")
    abstract = section(stage1, "## C. Structured abstract", "## D. Results")
    results = section(stage1, "## D. Results", "## Evidence map for drafting")
    methods = section(stage2, "## E. Methods", "## F. Discussion")
    discussion = section(stage2, "## F. Discussion", "## G. Introduction")
    introduction = section(stage2, "## G. Introduction", "## References cited in Stages 1 and 2")
    references = section(stage2, "## References cited in Stages 1 and 2", None)
    legend_body = section(legends, "# Stage 1 figure legends", None)
    title = "Analytical robustness of cross-disease BALF microbiome variation in PRJNA1056765"
    manuscript = f"""# {title}

## Abstract

{abstract}

## Introduction

{introduction}

## Methods

{methods}

## Results

{results}

## Discussion

{discussion}

## References

{references}

## Figure legends

{legend_body}
"""
    manuscript_dir = OUT / "manuscript"
    manuscript_dir.mkdir(parents=True, exist_ok=True)
    (manuscript_dir / "manuscript_full_draft.md").write_text(manuscript, encoding="utf-8")
    titles = section(stage1, "## A. Final title options", "## B. Scientific storyline")
    storyline = section(stage1, "## B. Scientific storyline", "## C. Structured abstract")
    (manuscript_dir / "editorial_summary.md").write_text(
        f"# Editorial summary\n\n## Title options\n\n{titles}\n\n## Approved scientific storyline\n\n{storyline}\n",
        encoding="utf-8",
    )


def axis(svg: SVG, x, y, w, h, ymax, ticks):
    svg.line(x, y, x, y + h, "#374151", 1.5)
    svg.line(x, y + h, x + w, y + h, "#374151", 1.5)
    for value in ticks:
        yy = y + h - value / ymax * h
        svg.line(x - 5, yy, x + w, yy, "#d9dee5", 1)
        svg.text(x - 10, yy + 4, f"{value:.2f}", "small", "end")


def figure1(figdir: Path):
    source = [
        {"stage": "Published source cohort", "n": 402, "role": "Han/Tang source cohort", "independent": "No"},
        {"stage": "Published ecology population", "n": 284, "role": "Han et al. training ecology", "independent": "No"},
        {"stage": "Published internal test", "n": 118, "role": "Diagnostic-model test split", "independent": "No"},
        {"stage": "Downloadable DNA runs", "n": 400, "role": "Current four-level omnibus", "independent": "No"},
        {"stage": "Unavailable DNA records", "n": 2, "role": "No downloadable reads", "independent": "No"},
        {"stage": "Pipeline-dependent sensitivity population", "n": 119, "role": "Frozen QC sensitivity", "independent": "No"},
    ]
    write_tsv(figdir / "source_data/Figure1_source.tsv", source)
    s = SVG("Figure 1. Cohort provenance and analytical populations")
    s.text(45, 78, "A", "panel")
    s.text(80, 78, "Published study", "head")
    s.rect(85, 125, 300, 100, "#eef4f8")
    s.text(235, 165, "402 patients", "head", "middle")
    s.text(235, 193, "BALF DNA and RNA resource", "small", "middle")
    s.arrow(385, 175, 500, 175)
    s.rect(500, 105, 250, 75, "#f5f7fa")
    s.text(625, 140, "Training n=284", "head", "middle")
    s.text(625, 163, "published ecology", "small", "middle")
    s.rect(500, 200, 250, 75, "#f5f7fa")
    s.text(625, 235, "Test n=118", "head", "middle")
    s.text(625, 258, "internal model split", "small", "middle")
    s.text(45, 345, "B", "panel")
    s.text(80, 345, "Current analytical populations", "head")
    s.rect(85, 390, 300, 105, "#e9f5ef")
    s.text(235, 430, "400 downloadable DNA runs", "head", "middle")
    s.text(235, 457, "four-level diagnosis omnibus", "small", "middle")
    s.text(235, 480, "same source cohort", "small", "middle")
    s.rect(85, 530, 300, 85, "#fff5e8")
    s.text(235, 565, "2 unavailable records", "head", "middle")
    s.text(235, 590, "data-availability difference", "small", "middle")
    s.arrow(385, 442, 520, 442)
    s.rect(520, 390, 350, 105, "#f4ecf7")
    s.text(695, 428, "n=119", "head", "middle")
    s.text(695, 455, "pipeline-dependent sensitivity", "body", "middle")
    s.text(695, 480, "population; changed estimand", "small", "middle")
    s.text(45, 690, "C", "panel")
    s.text(80, 690, "Interpretive boundary", "head")
    statements = [
        "No population is an independent cohort",
        "n=400 is not Han et al.'s n=284 contrast",
        "n=119 is not a replication population",
    ]
    for i, value in enumerate(statements):
        s.rect(100 + i * 410, 735, 360, 70, "#f8fafc")
        s.text(280 + i * 410, 777, value, "body", "middle")
    s.finish(figdir / "Figure1.svg")


def figure2(figdir: Path):
    rows = read_tsv(ROOT / "pipeline_difference_matrix.tsv")
    write_tsv(figdir / "source_data/Figure2_source.tsv", rows)
    selected = [
        "cohort", "analysis split", "taxonomic classifier", "database and versions",
        "negative controls", "normalization", "primary contrast", "beta diversity",
        "dispersion", "differential taxa",
    ]
    rows = [row for row in rows if row["item"] in selected]
    s = SVG("Figure 2. Original and current pipelines define non-equivalent analyses", 1600, 1020)
    widths = [240, 410, 410, 410]
    xs = [35, 275, 685, 1095]
    headers = ["Audit item", "Han et al.", "Current frozen analysis", "Interpretation"]
    for x, width, value in zip(xs, widths, headers):
        s.rect(x, 75, width, 55, "#e9eef3")
        s.text(x + 12, 109, value, "head")
    y = 130
    for i, row in enumerate(rows):
        h = 82
        fill = "#ffffff" if i % 2 == 0 else "#f8fafc"
        for x, width in zip(xs, widths):
            s.rect(x, y, width, h, fill, "#d6dde5", 1, 0)
        s.text(xs[0] + 10, y + 28, row["item"], "body")
        for x, key in [(xs[1], "Han_original_pipeline"), (xs[2], "current_frozen_400_pipeline"), (xs[3], "interpretation")]:
            words = row[key].split()
            line1, line2 = " ".join(words[:7]), " ".join(words[7:14])
            s.text(x + 10, y + 28, line1, "small")
            if line2:
                s.text(x + 10, y + 50, line2, "small")
        y += h
    s.text(45, 985, "Taxon overlap or mismatch is pipeline/statistical concordance or discrepancy, not biological agreement or disagreement.", "small")
    s.finish(figdir / "Figure2.svg")


def effect_figure(figdir: Path, rows: list[dict[str, str]], population: str, number: int, title: str):
    data = [r for r in rows if r["population"] == population and r["metric"] == "Aitchison"]
    data.sort(key=lambda r: (float(r["prevalence_threshold"]), r["pseudocount_rule"]))
    write_tsv(figdir / f"source_data/Figure{number}_source.tsv", data)
    s = SVG(title)
    s.text(55, 82, "PERMANOVA R² with paired dispersion qualification", "head")
    x, y, w, h, ymax = 130, 125, 1120, 550, 0.08
    axis(s, x, y, w, h, ymax, [0, .02, .04, .06, .08])
    thresholds = [.05, .10, .20]
    xmap = {value: x + 150 + index * 390 for index, value in enumerate(thresholds)}
    colors = {"P1_half_minimum": "#1f77b4", "P2_tenth_minimum": "#d95f02"}
    labels = {"P1_half_minimum": "P1 half-minimum", "P2_tenth_minimum": "P2 tenth-minimum"}
    for rule in colors:
        subset = [r for r in data if r["pseudocount_rule"] == rule]
        points = []
        for row in subset:
            xx = xmap[float(row["prevalence_threshold"])]
            yy = y + h - float(row["permanova_R2"]) / ymax * h
            points.append((xx, yy))
            qualified = float(row["permdisp_p"]) < .05
            s.circle(xx, yy, 10, colors[rule], "#b91c1c" if qualified else "#ffffff", 4 if qualified else 1.5)
            s.text(xx, yy - 18, f"{float(row['permanova_R2']):.4f}", "small", "middle")
            s.text(xx, yy + 30, f"disp P={float(row['permdisp_p']):.4g}", "tiny", "middle")
        s.path(points, colors[rule], 2)
    for value in thresholds:
        count = next(r["retained_features"] for r in data if float(r["prevalence_threshold"]) == value)
        s.text(xmap[value], y + h + 35, f"{int(value*100)}% prevalence", "body", "middle")
        s.text(xmap[value], y + h + 58, f"{count} species", "small", "middle")
    s.text(130, 755, "Blue: P1 half-minimum", "body", fill=colors["P1_half_minimum"])
    s.text(390, 755, "Orange: P2 tenth-minimum", "body", fill=colors["P2_tenth_minimum"])
    s.circle(700, 750, 9, "#ffffff", "#b91c1c", 4)
    s.text(720, 755, "red outline: PERMDISP P<0.05", "body")
    if population == "full":
        s.text(130, 815, "The 10% P1 point is the exact anchor replay. Feature spaces are not pooled or ranked.", "small")
    else:
        s.text(130, 815, "n=119 is a pipeline-dependent sensitivity population. Values are not direct changes from n=400.", "small")
    s.finish(figdir / f"Figure{number}.svg")


def figure5(figdir: Path):
    rows = [
        {"class": "Supported within frozen pipeline", "claim": "Exact replay of the 30-species Aitchison anchor", "status": "supported"},
        {"class": "Supported within frozen pipeline", "claim": "Very small conditional diagnosis variance component", "status": "supported"},
        {"class": "Supported within frozen pipeline", "claim": "Stability to two prespecified pseudocounts", "status": "supported"},
        {"class": "Analytically dependent", "claim": "Effect-size estimate depends on feature space and QC population", "status": "qualified"},
        {"class": "Analytically dependent", "claim": "Full-cohort Bray differences are dispersion-qualified", "status": "qualified"},
        {"class": "Analytically dependent", "claim": "Taxon overlap or mismatch is pipeline/statistical only", "status": "qualified"},
        {"class": "Not supported", "claim": "Stable disease fingerprint or clinical subtype", "status": "unsupported"},
        {"class": "Not supported", "claim": "Biomarker or diagnostic signal", "status": "unsupported"},
        {"class": "Not supported", "claim": "Disease-specific taxon discovery or mechanism", "status": "unsupported"},
    ]
    write_tsv(figdir / "source_data/Figure5_source.tsv", rows)
    s = SVG("Figure 5. Supported conclusions and claim limits", 1450, 930)
    columns = [
        ("Supported within frozen pipeline", "#e9f5ef", "#217a4b"),
        ("Analytically dependent", "#fff5e8", "#a35d00"),
        ("Not supported", "#fbecec", "#a22b2b"),
    ]
    for index, (heading, fill, stroke) in enumerate(columns):
        x = 45 + index * 470
        s.rect(x, 90, 430, 730, fill, stroke, 1.5, 6)
        s.text(x + 215, 135, heading, "head", "middle", stroke)
        subset = [row for row in rows if row["class"] == heading]
        for j, row in enumerate(subset):
            yy = 195 + j * 180
            s.rect(x + 30, yy, 370, 125, "#ffffff", "#d2d8df", 1, 4)
            words = row["claim"].split()
            line1, line2, line3 = " ".join(words[:6]), " ".join(words[6:12]), " ".join(words[12:])
            s.text(x + 215, yy + 42, line1, "body", "middle")
            if line2:
                s.text(x + 215, yy + 68, line2, "body", "middle")
            if line3:
                s.text(x + 215, yy + 94, line3, "small", "middle")
    s.text(45, 875, "This is an analytical robustness audit. It does not reproduce the complete Han et al. workflow.", "small")
    s.finish(figdir / "Figure5.svg")


def supplementary_figure(figdir: Path, rows: list[dict[str, str]]):
    data = [r for r in rows if r["metric"] == "Bray-Curtis"]
    data.sort(key=lambda r: (r["population"], float(r["prevalence_threshold"])))
    write_tsv(figdir / "source_data/FigureS1_source.tsv", data)
    s = SVG("Supplementary Figure S1. Bray–Curtis and PERMDISP comparator", 1450, 950)
    panels = [("full", 80, "Full cohort n=400"), ("strict_QC", 760, "Pipeline-dependent sensitivity population n=119")]
    for population, x, heading in panels:
        s.text(x, 100, heading, "head")
        axis(s, x + 70, 145, 520, 480, .09, [0, .03, .06, .09])
        subset = [r for r in data if r["population"] == population]
        for index, row in enumerate(subset):
            xx = x + 150 + index * 180
            yy = 145 + 480 - float(row["permanova_R2"]) / .09 * 480
            qualified = float(row["permdisp_p"]) < .05
            s.circle(xx, yy, 11, "#6b7280", "#b91c1c" if qualified else "#ffffff", 4 if qualified else 1.5)
            s.text(xx, yy - 20, f"R²={float(row['permanova_R2']):.4f}", "small", "middle")
            s.text(xx, yy + 32, f"disp P={float(row['permdisp_p']):.4g}", "tiny", "middle")
            s.text(xx, 660, f"{int(float(row['prevalence_threshold'])*100)}%", "body", "middle")
            s.text(xx, 683, f"{row['retained_features']} species", "small", "middle")
    s.circle(110, 765, 9, "#ffffff", "#b91c1c", 4)
    s.text(130, 770, "red outline: dispersion-qualified", "body")
    s.text(80, 825, "All full-cohort Bray–Curtis cells are dispersion-qualified and support only location and/or dispersion language.", "small")
    s.text(80, 860, "The two populations represent different estimands and are not linked as direct changes.", "small")
    s.finish(figdir / "FigureS1.svg")


def build_supplement(grid_rows: list[dict[str, str]]):
    supplement = OUT / "supplement"
    tables = supplement / "tables"
    figures = OUT / "figures"
    tables.mkdir(parents=True, exist_ok=True)
    shutil.copy2(GRID, tables / "TableS1_complete_frozen_v5_grid.tsv")
    qc = read_tsv(ROOT / "reports_public/metagenome_400_formal/qc/cohort_qc.tsv")
    qc_fields = ["run", "diagnosis", "cohort", "classified_fraction", "bracken_assigned_reads_estimate", "observed_species", "qc_flags", "sensitivity_included"]
    write_tsv(tables / "TableS2_QC_population.tsv", qc, qc_fields)
    shutil.copy2(ROOT / "pipeline_difference_matrix.tsv", tables / "TableS3_pipeline_difference_matrix.tsv")
    shutil.copy2(ROOT / "reports_public/metagenome_400_formal/statistics/permanova_permdisp.tsv", tables / "TableS4_frozen_primary_PERMANOVA_PERMDISP.tsv")
    shutil.copy2(ROOT / "reports_public/metagenome_400_formal/associations/diagnosis_species_differential.tsv", tables / "TableS5_frozen_species_associations.tsv")
    shutil.copy2(ROOT / "reports_public/metagenome_400_formal/clustering/cluster_diagnostics.tsv", tables / "TableS6_clustering_diagnostics.tsv")
    legend = """# Supplementary legends

## Supplementary Figure S1

Bray–Curtis and paired PERMDISP comparator for all six prespecified cells. Red outlines identify PERMDISP P<0.05. All full-cohort cells were dispersion-qualified. The n=119 results describe only a pipeline-dependent sensitivity population.

## Supplementary Table S1

Complete frozen v5 sensitivity grid. All 18 prespecified cells are included with effect sizes, permutation results, dispersion results, seeds, and hashes.

## Supplementary Table S2

Frozen QC fields for all 400 runs. `sensitivity_included=True` identifies the n=119 pipeline-dependent sensitivity population.

## Supplementary Table S3

Original-versus-current pipeline difference matrix. Taxon overlap or mismatch is limited to pipeline/statistical concordance or discrepancy.

## Supplementary Table S4

Previously frozen primary PERMANOVA and PERMDISP results.

## Supplementary Table S5

Previously frozen species-level association table. These results are not a new v5 taxon discovery analysis.

## Supplementary Table S6

Previously frozen clustering diagnostics for k=2–10 under Bray–Curtis and Aitchison representations.
"""
    (supplement / "supplementary_legends.md").write_text(legend, encoding="utf-8")
    index = """# Supplement index

- Figure S1: Bray–Curtis and PERMDISP comparator (`../figures/FigureS1.svg`)
- Table S1: complete frozen v5 grid
- Table S2: QC population fields
- Table S3: pipeline comparison
- Table S4: frozen primary PERMANOVA/PERMDISP
- Table S5: frozen species associations
- Table S6: clustering diagnostics
- Figure source data: `../figures/source_data/`
- Provenance and consistency reports: `../audit/`
"""
    (supplement / "index.md").write_text(index, encoding="utf-8")


def citation_evidence_audit():
    rows = [
        {"claim": "402-patient source cohort and n=284/118 split", "type": "external", "source": "Han et al. 2025; Tang et al. 2025", "status": "PASS"},
        {"claim": "32 DNA and 32 RNA negative controls", "type": "external", "source": "Tang et al. 2025", "status": "PASS"},
        {"claim": "Low-biomass and contamination context", "type": "external", "source": "Charlson et al. 2011; Drengenes et al. 2019", "status": "PASS"},
        {"claim": "Oral-taxa inflammatory precedent", "type": "external", "source": "Segal et al. 2013; Segal et al. 2016; Dickson et al. 2017", "status": "PASS"},
        {"claim": "Compositional and dispersion rationale", "type": "external", "source": "Fernandes et al. 2014; Anderson 2006", "status": "PASS"},
        {"claim": "Exact 30-species anchor replay", "type": "our result", "source": "v5 manifest and Table S1", "status": "PASS"},
        {"claim": "All full-cohort Bray cells dispersion-qualified", "type": "our result", "source": "Table S1 and Figure S1", "status": "PASS"},
        {"claim": "n=119 pipeline-dependent sensitivity population", "type": "our result", "source": "Table S2", "status": "PASS"},
        {"claim": "Taxon overlap/mismatch limited to pipeline/statistical interpretation", "type": "inference boundary", "source": "Table S3; original overlap audit", "status": "PASS"},
    ]
    write_tsv(OUT / "audit/citation_evidence_audit.tsv", rows)


def consistency_gate(grid_rows: list[dict[str, str]]):
    manifest = json.loads(GRID_MANIFEST.read_text(encoding="utf-8"))
    manuscript = (OUT / "manuscript/manuscript_full_draft.md").read_text(encoding="utf-8")
    checks = []
    def check(name, condition, evidence):
        checks.append({"check": name, "status": "PASS" if condition else "FAIL", "evidence": str(evidence)})
    check("grid rows", len(grid_rows) == 18, len(grid_rows))
    check("grid hash", sha256(GRID) == manifest["output_sha256"], sha256(GRID))
    check("anchor exact", manifest["anchor_replay_verified_exactly"] and manifest["anchor_expected"] == manifest["anchor_observed"], manifest["anchor_observed"])
    check("all full Bray dispersion-qualified", all(float(r["permdisp_p"]) < .05 for r in grid_rows if r["population"] == "full" and r["metric"] == "Bray-Curtis"), "3/3")
    required = ["1.94%", "0.0194095", "0.487", "0.0003349", "0.0163698", "0.0019795", "0.0695841", "0.0263302", "0.0009", "n=119 pipeline-dependent sensitivity population"]
    for token in required:
        check(f"manuscript contains {token}", token in manuscript, token)
    forbidden = ["diagnosis-associated boundary", "validation cohort", "cleaner cohort", "higher-quality biological cohort", "replication cohort", "reproducibility study", "reproducibility audit"]
    lower = manuscript.lower()
    for token in forbidden:
        check(f"forbidden phrase absent: {token}", token not in lower, token)
    check("Figure 3 internal note excluded from submission draft", "Figure 3 remains a provisional main-text figure" not in manuscript, "editorial artifact absent")
    check("Supplement full grid", (OUT / "supplement/tables/TableS1_complete_frozen_v5_grid.tsv").is_file(), "Table S1")
    check("Supplement Bray", (OUT / "figures/FigureS1.svg").is_file(), "Figure S1")
    failed = [row for row in checks if row["status"] == "FAIL"]
    report = {"status": "PASS" if not failed else "FAIL", "checks": checks}
    (OUT / "audit/consistency_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_tsv(OUT / "audit/consistency_checks.tsv", checks)
    if failed:
        raise SystemExit("consistency gate failed: " + ", ".join(row["check"] for row in failed))


def final_manifest():
    files = []
    for path in sorted(OUT.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            files.append({"path": str(path.relative_to(OUT)), "bytes": path.stat().st_size, "sha256": sha256(path)})
    manifest = {"package": str(OUT.relative_to(ROOT)), "file_count": len(files), "files": files}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "audit").mkdir(parents=True)
    figdir = OUT / "figures"
    grid_rows = read_tsv(GRID)
    build_manuscript()
    figure1(figdir)
    figure2(figdir)
    effect_figure(figdir, grid_rows, "full", 3, "Figure 3. Prespecified Aitchison robustness in the full cohort")
    effect_figure(figdir, grid_rows, "strict_QC", 4, "Figure 4. Aitchison results in the pipeline-dependent sensitivity population")
    figure5(figdir)
    supplementary_figure(figdir, grid_rows)
    build_supplement(grid_rows)
    citation_evidence_audit()
    consistency_gate(grid_rows)
    shutil.copy2(GRID_MANIFEST, OUT / "audit/frozen_v5_manifest.json")
    shutil.copy2(ROOT / "frozen_sensitivity_precompute_manifest.json", OUT / "audit/precompute_manifest.json")
    shutil.copy2(ROOT / "deepseek_final_manuscript_review.md", OUT / "audit/deepseek_final_manuscript_review.md")
    final_manifest()
    print(OUT)


if __name__ == "__main__":
    main()
