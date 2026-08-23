# PRJCA028177 pipeline compatibility audit

## Published pipeline

The paper reports the following workflow for BALF DNA and RNA libraries:

- single-end 50 bp sequencing on DIFSEQ-200; the public archive records the platform as MGISEQ-200;
- `bcl2fastq2` demultiplexing/splitting;
- Trimmomatic removal of low-quality, adapter-contaminated, duplicated, and short (`<36 bp`) reads;
- human-read removal by Bowtie2 alignment to `hs37d5`;
- Kraken 2 microbial identification;
- Bracken species-abundance estimation;
- a microorganism database built from bacterial, fungal, viral, and parasite genomes/scaffolds downloaded from GenBank release 238;
- subtraction of microbial-community background observed in a normal population.

The paper does not provide a cryptographic database identity, a complete database build manifest, exact Kraken 2/Bracken versions, or all command-line parameters.

## Comparison with the harmonized cross-cohort route

| Component | Assessment | Basis |
|---|---|---|
| Public DNA libraries | `SAME` | The archive explicitly labels 127 libraries as DNA-mNGS BALF libraries. |
| Native-read input possibility | `COMPATIBLE_BUT_NOT_IDENTICAL` | Public single-end FASTQ files could conceptually be evaluated with the harmonized native-read route, but no analysis was run in this audit. |
| Read length/layout | `COMPATIBLE_BUT_NOT_IDENTICAL` | Published single-end 50 bp is compatible with native-read Kraken2 processing, but it is not proof of identical read characteristics across cohorts. |
| Quality trimming | `INCOMPATIBLE` | The paper used Trimmomatic; the current harmonized sensitivity route does not trim. |
| Host filtering | `INCOMPATIBLE` | The paper removed hs37d5-mapped reads; the current native-read sensitivity route does not host-filter. |
| Kraken 2 classifier family | `SAME` | Both use Kraken 2 conceptually. Exact versions/commands are not reported for this paper. |
| Kraken database | `UNKNOWN` | GenBank release 238 source categories are reported, but no reproducible build identity or hash establishes equality with the harmonized database. |
| Bracken | `INCOMPATIBLE` | The published pipeline used Bracken; the current native-read common sensitivity estimand is Kraken2-only. |
| Normal-population background subtraction | `INCOMPATIBLE` | This paper-specific post-processing step is outside the harmonized native-read classification method. |

## Overall assessment

`COMPATIBLE_BUT_NOT_IDENTICAL`

The public DNA FASTQ libraries are technically plausible inputs for the existing harmonized native-read Kraken2-only sensitivity route. The published outputs cannot be treated as directly harmonized because preprocessing, host removal, Bracken, background subtraction, and database provenance differ or remain unresolved. No database identity equivalence is claimed.
