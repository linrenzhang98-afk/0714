args <- commandArgs(trailingOnly=TRUE)
if (length(args) != 2L) stop("usage: pathogen_profile_stats.R INPUT.tsv OUTPUT.tsv")
input <- read.delim(args[[1]], sep="\t", quote="", check.names=FALSE, stringsAsFactors=FALSE)

parse_counts <- function(text) as.numeric(strsplit(text, ",", fixed=TRUE)[[1]])
fmt <- function(value) if (length(value) == 0L || is.na(value)) "" else format(value, digits=17, scientific=TRUE)
rows <- vector("list", nrow(input))
for (i in seq_len(nrow(input))) {
  kind <- input$type[[i]]
  values <- parse_counts(input$counts[[i]])
  method <- ""
  statistic <- df <- p_value <- estimate <- ci_low <- ci_high <- NA_real_
  if (kind == "prevalence_ci") {
    fit <- binom.test(values[[1]], values[[2]], conf.level=0.95)
    method <- "Clopper-Pearson exact binomial"
    estimate <- unname(fit$estimate)
    ci_low <- fit$conf.int[[1]]
    ci_high <- fit$conf.int[[2]]
  } else {
    nr <- as.integer(input$nrow[[i]])
    nc <- as.integer(input$ncol[[i]])
    table <- matrix(values, nrow=nr, ncol=nc, byrow=TRUE)
    if (any(rowSums(table) == 0) || any(colSums(table) == 0)) {
      method <- "degenerate table; no between-group variation"
      p_value <- 1
    } else if (kind == "fisher_2x2") {
      fit <- fisher.test(table, conf.level=0.95)
      method <- "Fisher exact two-sided"
      p_value <- fit$p.value
      estimate <- unname(fit$estimate)
      ci_low <- fit$conf.int[[1]]
      ci_high <- fit$conf.int[[2]]
    } else {
      chi <- suppressWarnings(chisq.test(table, correct=FALSE))
      if (all(chi$expected >= 5)) {
        fit <- chi
        method <- "Pearson chi-square; all expected cells >=5"
        statistic <- unname(fit$statistic)
        df <- unname(fit$parameter)
        p_value <- fit$p.value
      } else {
        exact <- tryCatch(fisher.test(table), error=function(e) NULL)
        if (!is.null(exact)) {
          method <- "Fisher-Freeman-Halton exact"
          p_value <- exact$p.value
        } else {
          set.seed(as.integer(input$seed[[i]]))
          fit <- fisher.test(table, simulate.p.value=TRUE, B=99999)
          method <- "Fisher-Freeman-Halton Monte Carlo; B=99999"
          p_value <- fit$p.value
        }
      }
    }
  }
  rows[[i]] <- data.frame(test_id=input$test_id[[i]], method=method,
                          statistic=fmt(statistic), df=fmt(df), p_value=fmt(p_value),
                          estimate=fmt(estimate), ci_low=fmt(ci_low), ci_high=fmt(ci_high),
                          stringsAsFactors=FALSE)
}
output <- do.call(rbind, rows)
write.table(output, args[[2]], sep="\t", quote=FALSE, row.names=FALSE, na="")
