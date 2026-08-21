# Variable-length reads with Kraken2 and Bracken: evidence review

## Decision-level summary

Bracken is parameterized by one read length per database redistribution file and one `-r` value per invocation. The software may accept a Kraken report produced from mixed-length reads, but the redistribution probabilities were generated for a single length. Technical acceptance is therefore not evidence of a valid abundance estimate for a broad length mixture.

No official or peer-reviewed validation was found for substituting a sample's maximum, arithmetic mean or mode when lengths vary from 15 to 75 nt. No validated method was found for running Bracken separately by length and aggregating the resulting abundance estimates. Standardized fixed-length trimming is common as a general preprocessing operation, but the reviewed sources do not validate it as an automatic remedy for cross-cohort Bracken inference.

## Answers to the focused questions

### A. Does Bracken require a single representative or fixed read length?

For a scientifically interpretable run, yes. The official workflow builds `databaseXmers.kmer_distrib` for a specified `READ_LEN` and invokes Bracken with one `-r READ_LEN`. The original method calculates the probability that a read of length *r* is assigned to each taxonomic node. This makes read length part of the abundance model, not merely an input-format option.

The documentation does not explicitly reject mixed FASTQ files at parsing time. That is a software behavior distinction: one `-r` can be supplied, but it represents only one redistribution model.

### B. What happens when lengths vary substantially?

Kraken2 still classifies each read from its available k-mers/minimizers. Bracken then re-estimates abundance using probabilities for the single selected length. For a mixture, those probabilities do not represent the mixture of length-specific classification processes. The magnitude and direction of the resulting abundance error depend on the taxon, database and length distribution; they cannot be corrected by a generic scalar adjustment.

### C. Are maximum, mean or modal length defensible?

Not from the evidence reviewed. The official documentation says to use the read length of the data, but gives no validated rule for a wide within-sample distribution. Bracken issue #201 asks how to handle different post-trimming average lengths and remains an unresolved user question rather than an endorsed method.

For `CRR2423909`, maximum and mode are both 75 nt, yet only 32.493% of reads are 75 nt. Selecting 75 would model most reads with the wrong redistribution. A mean would likewise collapse a heterogeneous distribution and may not correspond to an installed or validated redistribution. These shortcuts are rejected.

### D. Is standardized trimming recommended or validated?

Length and quality filtering are routine in published metagenomic pipelines, including Sunbeam and nf-core/taxprofiler. Those practices establish that trimming can be reproducible; they do not establish that a particular target preserves an unbiased community composition or makes independently preprocessed cohorts equivalent.

Fixed-length harmonization is technically possible and could become scientifically defensible only after a prospective target rule, cohort-wide retention audit, paired-read policy, benchmark or sensitivity evidence, and matched consideration of the anchor workflow. It is not adopted here.

### E. Is length-stratified Bracken plus aggregation validated?

No supporting official or peer-reviewed validation was identified. Each stratum could technically use a matching redistribution, but Bracken estimates within a stratum are conditional on that stratum's classified/read population. Combining them requires a prespecified weighting and proof that counts or abundance estimates remain commensurate. Sparse bins and missing installed lengths add further instability. This strategy is technically conceivable but scientifically unsupported for the current study.

### F. Is Kraken2-only preferable to unsupported Bracken approximation?

For technical classification and QC, yes. Kraken2 does not require a single Bracken redistribution length, so it avoids knowingly applying the wrong Bracken model. It does not solve abundance estimation: raw Kraken2 taxonomic counts retain length-, database- and assignment-level biases that Bracken was designed to redistribute.

A Kraken2-only cross-cohort layer could be scientifically considered only as a common classifier-output estimand with cohort-specific analysis, explicit classified-fraction reporting and a matched anchor sensitivity layer. It must not be described as equivalent to Bracken abundance.

### G. Expected impact of 15–50-nt reads

Kraken2's default nucleotide k-mer length is 35. Reads shorter than the operative k-mer cannot contribute a full k-mer; reads just above it contribute few k-mers and carry less discriminatory information. Empirical benchmarks show classification success changes with read length. Very short reads therefore increase nonclassification and ambiguity and can alter taxonomic resolution. The exact effect is database- and taxon-dependent and should not be converted into a universal correction.

## Evidence classification

### Documented or validated

- One Bracken redistribution is generated for one specified read length, and one read length is supplied per Bracken run.
- Bracken's re-estimation probabilities depend on read length.
- Kraken2 is a read-level classifier and can process reads without a Bracken abundance step.
- General metagenomic pipelines commonly perform adapter, quality and minimum-length filtering before taxonomy.
- Shorter reads provide less taxonomic information and can reduce classification success.

### Plausible but unvalidated for this purpose

- Prospective fixed-length harmonization followed by matching Bracken, if retention and bias criteria are satisfied.
- A common Kraken2-only cross-cohort sensitivity layer with matched anchor processing.
- Switching cohorts if a genuinely cleaner, independently mapped fixed-length dataset is established.

### Rejected at present

- Maximum, mean or modal length as a Bracken proxy for a broad mixture.
- Bracken on the unmodified mixed-length `CRR2423909` file.
- Length-stratified Bracken followed by ad hoc averaging or summation.
- Choosing a trimming target solely because a redistribution file is installed.
- Treating raw Kraken2 proportions as interchangeable with Bracken abundance.

## Sources

1. Lu J, Breitwieser FP, Thielen P, Salzberg SL. Bracken: estimating species abundance in metagenomics data. *PeerJ Computer Science*. 2017;3:e104. DOI: [10.7717/peerj-cs.104](https://doi.org/10.7717/peerj-cs.104).
2. Bracken official README. Database generation and `-r READ_LEN` workflow. [GitHub](https://github.com/jenniferlu717/Bracken/blob/master/README.md).
3. Bracken official manual. Read-length-specific database and abundance-estimation parameters. [Johns Hopkins CCB](https://ccb.jhu.edu/software/bracken/index.shtml?t=manual).
4. Bracken issue #201. Unresolved question about selecting read length after adapter trimming. [GitHub](https://github.com/jenniferlu717/Bracken/issues/201).
5. Wood DE, Lu J, Langmead B. Improved metagenomic analysis with Kraken 2. *Genome Biology*. 2019;20:257. DOI: [10.1186/s13059-019-1891-0](https://doi.org/10.1186/s13059-019-1891-0).
6. Clarke EL et al. Sunbeam: an extensible pipeline for analyzing metagenomic sequencing experiments. *Microbiome*. 2019;7:46. DOI: [10.1186/s40168-019-0658-x](https://doi.org/10.1186/s40168-019-0658-x).
7. nf-core/taxprofiler documentation. Read-length filtering and Bracken read-length parameterization. [Usage documentation](https://nf-co.re/taxprofiler/2.0.0/docs/usage).
8. Pearman WS et al. Testing the advantages and disadvantages of short- and long-read eukaryotic metagenomics using simulated reads. *BMC Bioinformatics*. 2020;21:220. PMID: [32471343](https://pubmed.ncbi.nlm.nih.gov/32471343/).
