# Han et al. original-pipeline reconstruction

## Evidence boundary

This reconstruction uses Han et al. (npj Digital Medicine 2025; DOI 10.1038/s41746-025-01977-5), Tang et al. (Scientific Data 2025; DOI 10.1038/s41597-025-06171-6), their supplementary/data inventories, Figshare record 29388539, and selected files from the authors’ GitHub repository. PRJNA1056765 is the same source cohort as the frozen analysis, not external validation.

## Cohort and sample split

- The published cohort contains 402 adults with BALF DNA/RNA mNGS: lung cancer 123, bacterial infection 114, fungal infection 79, and pulmonary tuberculosis 86.
- Released group files verify 284 training and 118 test records. The ecological discovery results in Han et al. used the 284-person training set; diagnostic modeling used the internal 284/118 split.
- The frozen pipeline analyzed all 400 downloadable DNA runs. Two mapped WGS records had `size_MB=0` and no downloadable reads. This is an availability difference, not a new cohort.
- Tang et al. describe 32 DNA and 32 RNA negative controls. Exact row-level screening exclusions and the timing of all technical exclusions remain incompletely executable from the released code.

## Preprocessing and taxonomy

- The authors report fastp trimming, BWA/samtools removal of reads mapped to hg38, and Kraken2 followed by Bracken for microbial profiles. RNA host mapping used HISAT2/hg38 and featureCounts.
- The inspected matrix workflow uses KrakenTools `combine_mpa.py`, species/genus rank selection, removal of `Homo`, prefix stripping, and `humann_renorm_table -u relab` for relative abundance.
- The descriptor and repository include bacteria, fungi, viruses, and bacteriophages; host-derived products include gene expression, immune-cell estimates, transposable elements, and CNV/tumor fraction.
- Consequential unresolved parameters include exact fastp/Kraken2/Bracken versions, database build and content, Bracken read length, Kraken confidence, and the operational negative-control subtraction/filtering rule.

## Published ecological analyses

- Alpha diversity included Richness, Chao1, and evenness/diversity indices with Mann–Whitney pairwise comparisons. DNA cancer versus all infections was not significant; Richness and Chao1 differed for cancer versus bacterial infection; RNA alpha-diversity differences were reported.
- Bray–Curtis PERMANOVA in training DNA reported cancer versus infection R²=0.0067, P=0.002; versus bacterial infection R²=0.0193, P=0.001; versus fungal infection R²=0.0128, P=0.002; versus TB R²=0.0283, P=0.001. The headline analysis did not report paired PERMDISP.
- LEfSe used an LDA threshold >2 with adjusted P<0.05. The paper highlighted S. oralis, P. micra, and P. gingivalis in cancer; M. tuberculosis, P. aeruginosa, A. fumigatus, and C. neoformans in infections; and F. nucleatum in bacterial infection.
- Exact abundance filtering, zero treatment, LEfSe version, adjusted-P implementation, and the complete analyzable supplementary taxon list remain unresolved. We do not infer that unhighlighted taxa were absent from supplementary outputs.

## Diagnostic modeling reconstruction

- Six modality families were evaluated: DNA microbe/phage, RNA microbe/phage, host expression plus immune cells, transposable elements, CNV-derived tumor fraction, and an integrated model.
- Repository scripts cover LASSO, random forest, SVM, XGBoost, and ensemble combination. Inspected LASSO code uses `classif.cv_glmnet`, `lambda.min`, nonzero feature extraction, fixed test prediction, and pROC. This is an internal fixed split, not external or nested validation.
- The paper reports 58 individual/ensemble configurations. The integrated model reported AUC 0.937 (95% CI 0.910–0.964) in training and 0.847 (0.776–0.918) in test. Rule-in/rule-out accuracies were 0.896 for TB, 0.915 for fungal infection, and 0.907 for bacterial infection versus cancer.
- No new diagnostic model will be built. These outputs are reconstructed only to define overlap and prevent novelty inflation.

## Reproducibility limit

Processed matrices, scripts, group files, and control metadata make a partial audit possible. Public non-host reads cannot reproduce host removal from raw clinical material, and unresolved databases/control handling prevent assigning discordant taxon findings to biology. Any mismatch must remain a pipeline discrepancy until upstream equivalence is demonstrated.
