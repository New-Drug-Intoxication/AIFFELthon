# Single Cell RNA-seq Cell Type Annotation

## Metadata

**Short Description**: Best practices for annotating cell types in single-cell RNA-seq data using marker-based, automated, and reference-based approaches.

**Authors**: Distilled from single-cell best-practice literature

**Version**: 1.0

**Last Updated**: January 2025

**License**: CC BY 4.0

**Commercial Use**: Allowed

## Overview

Recommended workflow:

1. Quality control and doublet removal.
2. Initial marker-based annotation.
3. Automated annotation for cross-checking.
4. Reference-based transfer for refinement.

Use multiple evidence sources and report confidence per cluster.

## Common Pitfalls

- Over-clustering and unstable labels.
- Batch effects not corrected before annotation.
- Blind reliance on a single classifier.
- Mixing cell states with cell types.
