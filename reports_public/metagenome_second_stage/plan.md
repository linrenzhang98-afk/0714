# Metagenome Second-Stage Plan

## Scope

- Input candidate rows: 80
- Shortlisted rows: 61
- Source: PRJNA1056765 production first-pass Kraken2/Bracken output
- No new data download is required for this planning step.

## Group Counts

- Acinetobacter: 4 selected / 4 candidates
- Burkholderia: 1 selected / 1 candidates
- Candida: 2 selected / 2 candidates
- Enterobacterales: 7 selected / 7 candidates
- Enterococcus: 1 selected / 1 candidates
- Haemophilus: 6 selected / 6 candidates
- Mycobacteria: 8 selected / 9 candidates
- Other: 8 selected / 13 candidates
- Pseudomonas: 8 selected / 21 candidates
- Staphylococcus: 5 selected / 5 candidates
- Stenotrophomonas: 4 selected / 4 candidates
- Streptococcus: 7 selected / 7 candidates

## Top Shortlist Examples

- SRR27343490: Staphylococcus aureus (group Staphylococcus, pathogen fraction 0.94962, classified 9.4571%)
- SRR27343272: Klebsiella pneumoniae (group Enterobacterales, pathogen fraction 0.93081, classified 10.4273%)
- SRR27343566: Escherichia coli (group Enterobacterales, pathogen fraction 0.92124, classified 7.6292%)
- SRR27343725: Staphylococcus aureus (group Staphylococcus, pathogen fraction 0.91836, classified 5.9133%)
- SRR27343495: Pseudomonas aeruginosa (group Pseudomonas, pathogen fraction 0.91284, classified 9.9619%)
- SRR27343276: Pseudomonas aeruginosa (group Pseudomonas, pathogen fraction 0.91283, classified 5.7494%)
- SRR27343266: Stenotrophomonas maltophilia (group Stenotrophomonas, pathogen fraction 0.91228, classified 6.7189%)
- SRR27344040: Pseudomonas aeruginosa (group Pseudomonas, pathogen fraction 0.87347, classified 5.242%)
- SRR27343867: Pseudomonas aeruginosa (group Pseudomonas, pathogen fraction 0.87305, classified 4.7008%)
- SRR27343532: Acinetobacter baumannii (group Acinetobacter, pathogen fraction 0.85917, classified 3.9517%)
- SRR27343868: Acinetobacter baumannii (group Acinetobacter, pathogen fraction 0.80919, classified 4.4782%)
- SRR27343543: Pseudomonas aeruginosa (group Pseudomonas, pathogen fraction 0.79386, classified 2.2016%)
- SRR27344012: Pseudomonas aeruginosa (group Pseudomonas, pathogen fraction 0.78688, classified 4.2561%)
- SRR27344039: Pseudomonas aeruginosa (group Pseudomonas, pathogen fraction 0.78654, classified 2.3252%)
- SRR27343475: Candida albicans (group Candida, pathogen fraction 0.78161, classified 6.4664%)
- SRR27343721: Pseudomonas aeruginosa (group Pseudomonas, pathogen fraction 0.75639, classified 3.3178%)
- SRR27343853: Acinetobacter baumannii (group Acinetobacter, pathogen fraction 0.75056, classified 3.8943%)
- SRR27343738: Acinetobacter baumannii (group Acinetobacter, pathogen fraction 0.68751, classified 5.0663%)
- SRR27344035: Haemophilus influenzae (group Haemophilus, pathogen fraction 0.68527, classified 2.1225%)
- SRR27343494: Klebsiella pneumoniae (group Enterobacterales, pathogen fraction 0.63548, classified 7.7738%)

## Recommended Next Analysis

- Review `shortlist.tsv` before any heavy re-analysis.
- Keep first-pass Kraken2/Bracken outputs as the screening baseline.
- If proceeding, run host-removal and QC only on the shortlist, not all 400 samples.
- Defer AMR or functional profiling until the pathogen-group shortlist is reviewed.

## Output Files

- `shortlist.tsv`
- `pathogen_group_counts.tsv`
