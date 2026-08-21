# Variable-length strategy review

No option below is authorized or implemented.

| Future option | Information loss | Bias and cohort comparability | Bracken validity | Reproducibility | Effect on scientific estimand |
|---|---|---|---|---|---|
| A. Exclude variable-length runs | Potentially large and presently unknown | Selection may correlate with processing batch, sample quality or group; complete-case cohort may differ systematically | Avoids applying one redistribution to mixed reads | High only after a prospective deposited-length eligibility rule | Changes the eligible-subject population and may change the diagnosis estimand |
| B. Standardized trimming/filtering to a frozen target | Removes shorter reads and truncates longer reads; `CRR2423909` would retain at most the subset meeting the target rule | Retention may vary by run and original processing; could amplify technical differences | Potentially defensible only after independent validation of the exact trimming and redistribution pairing | High if target, tool, version, order and attrition rules are frozen before outcomes | Changes the feature-generating process and possibly the QC population |
| C. Stratify reads by length | Retains more reads but fragments each library and increases sparse strata | Runs contribute unequally across length strata; aggregation is nontrivial | Separate matching redistributions may be valid per fixed stratum, but combining estimates needs validation | Complex; requires frozen strata, minimum counts and aggregation | Produces a length-stratified rather than ordinary sample-level abundance estimand |
| D. Kraken2-only technical QC | Preserves reads and avoids unsupported Bracken abundance redistribution | Classification fractions remain database- and length-dependent | Bracken question is avoided, not solved | High for bounded technical QC | Cannot supply the planned Bracken abundance matrix for community inference |
| E. Another validated abundance estimator | Depends on method | Cross-cohort comparability changes unless the anchor and all external cohorts use the same validated workflow | Does not establish Bracken validity | Requires a separate method freeze, versioned references and validation | Replaces the abundance-estimation estimand and may require reprocessing all cohorts |

The conservative current state is `PRJCA046985_REQUIRES_VARIABLE_LENGTH_STRATEGY_REVIEW`. No biological or taxonomic result was used in reaching it.
