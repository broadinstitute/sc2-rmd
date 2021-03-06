# SARS-CoV-2 Rmarkdown reporting tools

This repository provides parameterized rmarkdown templates, wrapper scripts, and WDL workflows for producing routine (e.g. weekly) reports to US state and local public health agencies on SARS-CoV-2 sequencing activities from your viral sequencing lab. Defaults are currently configured for the Broad Institute.

The required inputs include:
1. A per-assembly metadata file, as would normally be produced by the `sarscov2_illumina_full` WDL workflow.
2. A tsv mapping sample IDs to collaborator original IDs

Examples of these two input files, as well as example output files, are provided in the `examples` directory. A WDL workflow wrapper is provided as well.

Outputs include two files for every US state represented in the input data:
1. A PDF narrative report with key numbers, tables, and charts.
2. An XLSX spreadsheet with detailed metrics for every sample.
