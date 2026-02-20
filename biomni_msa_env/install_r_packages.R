args <- commandArgs(trailingOnly = TRUE)
repo_root <- if (length(args) >= 1) args[[1]] else normalizePath(".")
gen_dir <- file.path(repo_root, "generated")
req_file <- file.path(gen_dir, "requirements.r.txt")
fail_file <- file.path(gen_dir, "failed.r.txt")

if (!file.exists(req_file)) {
  cat("[r] requirements.r.txt not found\n")
  quit(status = 0)
}

pkgs <- readLines(req_file, warn = FALSE)
pkgs <- trimws(pkgs)
pkgs <- pkgs[nzchar(pkgs)]

if (length(pkgs) == 0) {
  cat("[r] no packages to install\n")
  quit(status = 0)
}

ok <- character(0)
fail <- character(0)

bioc_pkgs <- c("DESeq2", "clusterProfiler", "edgeR", "limma")

suppressWarnings(suppressMessages({
  if (!requireNamespace("BiocManager", quietly = TRUE)) {
    install.packages("BiocManager", repos = "https://cloud.r-project.org")
  }
}))

for (pkg in pkgs) {
  status <- TRUE
  suppressWarnings(suppressMessages({
    tryCatch({
      if (pkg %in% bioc_pkgs) {
        BiocManager::install(pkg, ask = FALSE, update = FALSE)
      } else {
        install.packages(pkg, repos = "https://cloud.r-project.org")
      }
      if (!requireNamespace(pkg, quietly = TRUE)) {
        status <- FALSE
      }
    }, error = function(e) {
      status <<- FALSE
    })
  }))
  if (status) {
    ok <- c(ok, pkg)
  } else {
    fail <- c(fail, pkg)
  }
}

cat(sprintf("[r] ok=%d fail=%d\n", length(ok), length(fail)))
if (length(fail) > 0) {
  writeLines(fail, fail_file)
}
