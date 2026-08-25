# Isolated zCompositions installation plan

The ETYY job downloads exactly the three source tarballs locked in `cran_dependency_lock.json` through the bounded acquisition mechanism from `cran.r-project.org`. The downloader verifies source byte counts and SHA-256 values before any installation command runs. Installation then uses only local tarball paths and the existing mgshotgun R executable, with no R repository access.

The target library is `/mnt/disk1/0714_control/r_libs/zCompositions-1.6.2-R-4.5.3`. Its parent is checked against `/mnt/disk1/0714_control/r_libs`; a pre-existing non-empty target is a fail-closed validation result and is never deleted or reused. The existing `/home/suma/anaconda3/envs/mgshotgun/lib/R/library` is snapshotted before and after installation. Its package names and versions must be identical.

The installer validates system `MASS` and `survival` before use, installs `NADA`, `truncnorm`, then `zCompositions` into the isolated library with `R CMD INSTALL --library=<isolated>` and local tarballs, and confirms the isolated library contains only the three locked new packages. Validation sets `.libPaths()` in-process to the isolated library followed by the read-only system library, verifies zCompositions 1.6.2 resolves from the isolated path, and runs the same small synthetic `cmultRepl(method="CZM", output="prop")` matrix twice.

The job exits cleanly after writing a compact validation result even when the install is not ready, so the immutable failure reason can be handed off. It never reads biological matrices or clinical data.
