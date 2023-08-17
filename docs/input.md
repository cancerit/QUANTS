# QUANTS: Input

## Samplesheet

You will need to create a samplesheet with information about the samples you would like to analyse before running the pipeline. If you are using library-dependent quantification, you should only include samples which were generated against that library i.e. each library should be a separate run.

Use the `input` parameter to specify its location.

```console
--input '[path to samplesheet file]'
```

The samplesheet has to be a **comma-separated** file with 2 (for single end sequencing) or 3 (for paired end sequencing) columns, and a header row as shown in the examples below.

### Single end sequencing

Minimum of two columns with the headings `sample` and `fastq1` where `sample` represents the sample name and `fastq1` is the path to the corresponding FASTQ file.

```csv
sample,fastq_1
SAMPLE_D4_R1,SAMPLE_D4_R1_S1_L002_R1_001.fastq.gz
SAMPLE_D4_R2,SAMPLE_D4_R2_S1_L003_R1_001.fastq.gz
SAMPLE_D4_R3,SAMPLE_D4_R3_S1_L004_R1_001.fastq.gz
```

### Paired end sequencing

Minimum of two columns with the headings `sample`, `fastq1` and `fastq2` where `sample` represents the sample name and `fastq1` and `fastq2` represent the paths to the corresponding FASTQ files R1 and R2 respectively.

```csv
sample,fastq_1,fastq_2
SAMPLE_D4_R1,SAMPLE_D4_R1_S1_L002_R1_001.fastq.gz,SAMPLE_D4_R1_S1_L002_R2_001.fastq.gz
SAMPLE_D4_R2,SAMPLE_D4_R2_S1_L003_R1_001.fastq.gz,SAMPLE_D4_R2_S1_L003_R2_001.fastq.gz
SAMPLE_D4_R3,SAMPLE_D4_R3_S1_L004_R1_001.fastq.gz,SAMPLE_D4_R3_S1_L004_R2_001.fastq.gz
```

The pipeline will auto-detect whether a sample is single- or paired-end using the information provided in the samplesheet. The samplesheet can have as many columns as you desire, however, there is a strict requirement for the first 2 (for single end sequencing) or 3 (for paired end sequencing) columns. to match those defined in the table below.

A final samplesheet file consisting of both single- and paired-end data may look something like the one below. This is for 3 samples, each with 3 replicates.

```csv
sample,fastq_1,fastq_2
SAMPLE_D4_R1,SAMPLE_D4_R1_S1_L002_R1_001.fastq.gz,SAMPLE_D4_R1_S1_L002_R2_001.fastq.gz
SAMPLE_D4_R2,SAMPLE_D4_R2_S1_L003_R1_001.fastq.gz,SAMPLE_D4_R2_S1_L003_R2_001.fastq.gz
SAMPLE_D4_R3,SAMPLE_D4_R3_S1_L004_R1_001.fastq.gz,SAMPLE_D4_R3_S1_L004_R2_001.fastq.gz
SAMPLE_D8_R1,SAMPLE_D8_R1_S1_L002_R1_001.fastq.gz,SAMPLE_D8_R1_S1_L002_R2_001.fastq.gz
SAMPLE_D8_R2,SAMPLE_D8_R2_S1_L003_R1_001.fastq.gz,SAMPLE_D8_R2_S1_L003_R2_001.fastq.gz
SAMPLE_D8_R3,SAMPLE_D8_R3_S1_L004_R1_001.fastq.gz,SAMPLE_D8_R3_S1_L004_R2_001.fastq.gz
SAMPLE_D21_R1,SAMPLE_D21_R1_S1_L002_R1_001.fastq.gz,SAMPLE_D21_R1_S1_L002_R2_001.fastq.gz
SAMPLE_D21_R2,SAMPLE_D21_R2_S1_L003_R1_001.fastq.gz,SAMPLE_D21_R2_S1_L003_R2_001.fastq.gz
SAMPLE_D21_R3,SAMPLE_D21_R3_S1_L004_R1_001.fastq.gz,SAMPLE_D21_R3_S1_L004_R2_001.fastq.gz
```

| Column         | Description                                                                                                                |
|----------------|----------------------------------------------------------------------------------------------------------------------------|
| `sample`       | Custom sample name. Spaces in sample names are automatically converted to underscores (`_`).                               |
| `fastq_1`      | Full path to FastQ file for Illumina short reads 1. File has to be gzipped and have the extension ".fastq.gz" or ".fq.gz". |
| `fastq_2`      | Full path to FastQ file for Illumina short reads 2. File has to be gzipped and have the extension ".fastq.gz" or ".fq.gz". |

Example samplesheets for [single end](../assets/samplesheet.single.csv) and [paired end](../assets/samplesheet.single.csv) has been provided with the pipeline.

## Library (required only if library-dependent quantification is enabled)

Library-dependent quantification calculates the abundances of user-specified oligo sequences in FASTQ reads. When library-dependent quantification is enabled (`library_dependent_quantification`), a library file containing oligo sequences must be provided, using the `oligo_library` parameter to specify its location.

```console
--input '[path to samplesheet file]' --oligo_library '[path to library file]'
```

### pyQUEST

Information on the required library format for [pyQUEST](https://github.com/cancerit/pyQUEST) can be found [here](https://github.com/cancerit/pyQUEST#library) along with other usage details.
