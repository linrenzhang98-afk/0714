# Deposited-file host-depletion resolution

## DRR770839

**Final status: RAW**, with an important qualification.

The paper explicitly describes CRA024916 as the deposit of “raw sequence data.” Its Methods place BALF Tween/Benzonase treatment before extraction and library construction, while SNAP mapping to hg38 appears later in the computational analysis. The most conservative traceable interpretation is therefore:

- physical host-nucleic-acid depletion occurred before sequencing;
- the deposited file is the authors' raw sequencing deposit;
- computational hg38 subtraction was not performed before deposition under the reported ordering.

This resolves the question relevant to accidental *repeat computational filtering*. A future pilot may inspect integrity and may apply the single prespecified computational host-removal stage only after authorization. It must preserve the unmodified downloaded file and record the wet-lab depletion context.

The repository-derived 40-nt length conflicts with the paper's statement that Trimmomatic removed reads shorter than 70 bp. This discrepancy does not overturn the authors' raw-deposit statement, but it requires FASTQ inspection during any authorized technical pilot before host removal. It cannot be resolved by filenames or by downloading reads in this phase.

No FASTQ was downloaded and no host filtering was performed.
