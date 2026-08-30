args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 3) stop("usage: run_czm.R INPUT OUTPUT R_LIBRARY")
.libPaths(c(args[[3]], .libPaths()))
if (!requireNamespace("zCompositions", quietly = TRUE)) stop("zCompositions is unavailable")
observed_version <- as.character(utils::packageVersion("zCompositions"))
if (!identical(observed_version, "1.6.2")) {
  stop(sprintf("zCompositions version mismatch: expected 1.6.2, observed %s", observed_version))
}
x <- as.matrix(utils::read.table(args[[1]], header = FALSE, sep = "\t", check.names = FALSE))
storage.mode(x) <- "double"
if (any(!is.finite(x)) || any(x < 0) || any(rowSums(x) <= 0)) stop("invalid CZM input")
y <- zCompositions::cmultRepl(
  x,
  label = 0,
  method = "CZM",
  output = "prop",
  frac = 0.65,
  threshold = 0.5,
  adjust = TRUE
)
if (any(!is.finite(y)) || any(y <= 0)) stop("invalid CZM output")
utils::write.table(y, file = args[[2]], sep = "\t", row.names = FALSE, col.names = FALSE, quote = FALSE)
