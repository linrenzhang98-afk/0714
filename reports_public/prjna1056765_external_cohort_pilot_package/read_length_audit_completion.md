# PRJCA046985 bounded read-length audit completion

The authorized eight-run audit completed without a stop or deviation event. All files matched the frozen byte counts, passed gzip/FASTQ validation, and produced complete read-length histograms. Cumulative download was exactly **12,866,805 bytes**. No trimming, filtering, host processing, Kraken2, Bracken, taxonomic analysis or biological inference was performed.

| Run | Bytes | Reads | Range (nt) | Distinct lengths | Mode (nt) | Modal fraction | Classification |
|---|---:|---:|---:|---:|---:|---:|---|
| CRR2423961 | 1,531,191 | 37,946 | 15–50 | 28 | 50 | 99.584% | VARIABLE_LENGTH |
| CRR2424000 | 2,000,450 | 56,086 | 15–50 | 28 | 50 | 98.663% | VARIABLE_LENGTH |
| CRR2423957 | 2,539,990 | 72,456 | 50–50 | 1 | 50 | 100.000% | FIXED_LENGTH |
| CRR2423986 | 2,543,406 | 63,514 | 15–50 | 28 | 50 | 99.462% | VARIABLE_LENGTH |
| CRR2423912 | 841,555 | 17,517 | 15–75 | 51 | 75 | 95.513% | VARIABLE_LENGTH |
| CRR2423921 | 956,156 | 22,851 | 15–75 | 47 | 75 | 98.105% | VARIABLE_LENGTH |
| CRR2423991 | 1,216,398 | 32,549 | 15–75 | 57 | 75 | 38.361% | VARIABLE_LENGTH |
| CRR2424010 | 1,237,659 | 38,122 | 15–75 | 57 | 75 | 22.911% | VARIABLE_LENGTH |

The complete 297-row histogram is preserved in `hospital_read_length_audit/complete_read_length_histograms.tsv`; checksums and per-run installed-length fractions are preserved in `hospital_read_length_audit/read_length_audit_summary.json`.

## Interpretation boundary

One of eight files was strictly fixed-length and seven were variable-length. Because variable-length files occurred across nominal 50-nt and 75-nt strata, the pattern is cohort-relevant rather than attributable to a single exceptional run. Near-modal files remain variable-length and are not treated as compatible with a fixed-length Bracken redistribution.

DeepSeek's post-audit verdict is **INSUFFICIENT_EVIDENCE** for choosing fixed-length harmonization, a Kraken2-only cross-cohort layer, validated length-stratified Bracken, or a replacement primary cohort. No additional raw-read audit is needed solely to establish cohort relevance. Any taxonomy-stage method requires a new reviewed plan and separate authorization.
