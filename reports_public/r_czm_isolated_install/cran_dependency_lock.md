# CRAN dependency lock: zCompositions 1.6.2

The target is [`zCompositions` 1.6.2](https://cran.r-project.org/src/contrib/zCompositions_1.6.2.tar.gz), verified against the official [CRAN PACKAGES index](https://cran.r-project.org/src/contrib/PACKAGES). The source package declares only `Depends: R (>= 2.14.0), methods, MASS, NADA, truncnorm`; it has no `Imports` or `LinkingTo` fields.

`MASS` and `survival` are R recommended packages and are reused only from the read-only mgshotgun system library after their presence is verified. `methods` and R itself are base components and are not installed. The only new source packages are installed in this exact order:

1. `NADA` 1.6-1.2 — 72,167 bytes; CRAN MD5 `ec8f3a8868ac4e55b174106702427067`; SHA-256 `837dc66bc880285985ce1c0da9897f437207fad6ec69c3f0879fbaf4a4ace2b4`.
2. `truncnorm` 1.0-9 — 11,629 bytes; CRAN MD5 `878c944c50c6eeaea3e4e6d9586216d3`; SHA-256 `5156acc4d63243bf95326d6285b0ba3cdf710697d67c233a12ae56f3d87ec708`.
3. `zCompositions` 1.6.2 — 64,212 bytes; CRAN MD5 `c2c389e09eb77e76aae234c09f4549a0`; SHA-256 `8f50ab81c4aa2ea8ff8c52678d14af456cdb0ee04b22a567a9f18722dc49d98a`.

Total expected acquisition is 148,008 bytes. `testthat` is `truncnorm` Suggests only and is excluded. `NADA` and `truncnorm` are both hard requirements because `zCompositions` declares them in `Depends`; this lock does not make a stronger claim that the CZM branch calls either package directly. The ETYY synthetic validation records the packages actually loaded during the successful call.
