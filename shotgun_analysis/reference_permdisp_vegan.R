args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 4) stop("usage: reference_permdisp_vegan.R DISTANCE GROUPS PERMUTATIONS OUTPUT")
if (!requireNamespace("vegan", quietly = TRUE)) stop("vegan is unavailable")
d <- as.matrix(utils::read.table(args[[1]], header = FALSE, sep = "\t", check.names = FALSE))
groups <- scan(args[[2]], what = character(), quiet = TRUE)
permutation_matrix <- as.matrix(utils::read.table(args[[3]], header = FALSE, sep = "\t"))
if (nrow(d) != ncol(d) || nrow(d) != length(groups) || ncol(permutation_matrix) != length(groups)) {
  stop("reference inputs are not aligned")
}
# R permutation matrices are one-based. The caller must provide them that way.
model <- vegan::betadisper(stats::as.dist(d), factor(groups), type = "centroid", bias.adjust = FALSE)
test <- vegan::permutest(model, permutations = permutation_matrix)
observed <- unname(test$statistic[[1]])
permuted <- as.numeric(test$perm[, 1])
utils::write.table(
  data.frame(kind = c("observed", rep("permuted", length(permuted))), value = c(observed, permuted)),
  file = args[[4]], sep = "\t", row.names = FALSE, col.names = FALSE, quote = FALSE
)
