# Clinical-label circularity assessment

The publication calls clinical etiological diagnosis the reference standard and says pathogen classes were determined by the chief physician "in conjunction with other tests." It evaluates whether Illumina, Nanopore and culture results matched that diagnosis; it also says clinicians accepted or did not accept results from those three methods. This does **not** prove an mNGS-free adjudication workflow.

There is some evidence against a trivial identity between label and mNGS: among the 13 patients ultimately excluded from infection, the paper reports four Illumina-positive and nine Nanopore-positive cases. That observation is insufficient to prove that every group label was created independently of either mNGS platform.

Accordingly, `INFECTION_LABEL_USES_MNGS=unresolved`, `INCORPORATION_BIAS=unresolved`, and `CIRCULAR_GROUP_DEFINITION=unresolved`. These are fail-closed results for a future microbiome-ecology comparison, not assertions that the diagnostic study itself is invalid. Treatment-guidance labels explicitly use detection results and are circular for predictor-outcome ecology.
