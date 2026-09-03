args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 7) stop("usage: run_czm.R INPUT OUTPUT R_LIBRARY PROVENANCE ZCOMPOSITIONS_VERSION NADA_VERSION TRUNCNORM_VERSION")
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
description_version <- function(package) {
  as.character(utils::packageDescription(package, lib.loc=isolated, fields="Version"))
}
expected_versions <- c(zCompositions=args[[5]], NADA=args[[6]], truncnorm=args[[7]])
observed_versions <- vapply(names(expected_versions), description_version, character(1))
for (package in names(expected_versions)) {
  if (!identical(observed_versions[[package]], expected_versions[[package]])) {
    stop(sprintf("%s version mismatch: expected %s, observed %s", package, expected_versions[[package]], observed_versions[[package]]))
  }
}
x <- as.matrix(utils::read.table(args[[1]], header = FALSE, sep = "\t", check.names = FALSE))
storage.mode(x) <- "double"
if (any(!is.finite(x)) || any(x < 0) || any(rowSums(x) <= 0)) stop("invalid CZM input")
raw_result <- zCompositions::cmultRepl(
  x,
  label = 0,
  method = "CZM",
  output = "prop",
  frac = 0.65,
  threshold = 0.5,
  adjust = TRUE
)
extract_numeric_component <- function(value, expected_dims, path="result") {
  candidates <- list()
  visit <- function(candidate, candidate_path) {
    dims <- dim(candidate)
    matrix_like <- (is.matrix(candidate) || is.data.frame(candidate)) &&
      is.numeric(as.matrix(candidate)) && !is.null(dims) &&
      identical(as.integer(dims), as.integer(expected_dims))
    if (matrix_like) {
      candidates[[length(candidates) + 1L]] <<- list(path=candidate_path, value=as.matrix(candidate))
    } else if (is.list(candidate) && !is.data.frame(candidate)) {
      for (i in seq_along(candidate)) visit(candidate[[i]], paste0(candidate_path, "[[", i, "]]"))
    }
  }
  visit(value, path)
  if (length(candidates) != 1L) stop(sprintf("expected exactly one numeric component with input dimensions, found %d", length(candidates)))
  candidates[[1L]]
}
selected <- extract_numeric_component(raw_result, dim(x))
y <- selected$value
if (any(!is.finite(y)) || any(y <= 0)) stop("invalid CZM output")
utils::write.table(y, file = args[[2]], sep = "\t", row.names = FALSE, col.names = FALSE, quote = FALSE)
runtime <- c(
  R_version = as.character(getRversion()),
  effective_libPaths = paste(normalizePath(.libPaths(), winslash = "/", mustWork = TRUE), collapse = ";"),
  isolated_library = isolated,
  zCompositions_version = observed_versions[["zCompositions"]],
  zCompositions_path = normalizePath(find.package("zCompositions"), winslash = "/", mustWork = TRUE),
  NADA_version = observed_versions[["NADA"]],
  NADA_path = normalizePath(find.package("NADA"), winslash = "/", mustWork = TRUE),
  truncnorm_version = observed_versions[["truncnorm"]],
  truncnorm_path = normalizePath(find.package("truncnorm"), winslash = "/", mustWork = TRUE)
  ,selected_component_path = selected$path
)
utils::write.table(
  data.frame(key = names(runtime), value = unname(runtime)),
  file = args[[4]], sep = "\t", row.names = FALSE, col.names = FALSE, quote = FALSE
)
