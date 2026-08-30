args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 4) stop("usage: run_czm.R INPUT OUTPUT R_LIBRARY PROVENANCE")
isolated <- normalizePath(args[[3]], winslash = "/", mustWork = TRUE)
.libPaths(c(isolated, .libPaths()))
if (!identical(as.character(getRversion()), "4.5.3")) {
  stop(sprintf("R version mismatch: expected 4.5.3, observed %s", as.character(getRversion())))
}
packages <- c("zCompositions", "NADA", "truncnorm")
for (package in packages) {
  if (!requireNamespace(package, quietly = TRUE)) stop(sprintf("%s is unavailable", package))
  package_path <- normalizePath(find.package(package), winslash = "/", mustWork = TRUE)
  if (!(identical(package_path, isolated) || startsWith(package_path, paste0(isolated, "/")))) {
    stop(sprintf("%s resolved outside isolated library: %s", package, package_path))
  }
}
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
runtime <- c(
  R_version = as.character(getRversion()),
  effective_libPaths = paste(normalizePath(.libPaths(), winslash = "/", mustWork = TRUE), collapse = ";"),
  isolated_library = isolated,
  zCompositions_version = as.character(utils::packageVersion("zCompositions")),
  zCompositions_path = normalizePath(find.package("zCompositions"), winslash = "/", mustWork = TRUE),
  NADA_version = as.character(utils::packageVersion("NADA")),
  NADA_path = normalizePath(find.package("NADA"), winslash = "/", mustWork = TRUE),
  truncnorm_version = as.character(utils::packageVersion("truncnorm")),
  truncnorm_path = normalizePath(find.package("truncnorm"), winslash = "/", mustWork = TRUE)
)
utils::write.table(
  data.frame(key = names(runtime), value = unname(runtime)),
  file = args[[4]], sep = "\t", row.names = FALSE, col.names = FALSE, quote = FALSE
)
