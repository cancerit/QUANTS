# QUANTS: Configuration

**Note**: use full paths where file paths are required

## Input/output options

```console
--input                               [string]  Path to comma-separated file containing information about the samples in the experiment.
--single_end                          [boolean] If data is single-ended reads instead of paired-end.
--outdir                              [string]  Path to the output directory where the results will be saved. [default: ./results]
--multiqc_title                       [string]  MultiQC report title. Printed as page header, used for filename if not otherwise specified.
```

## Quality control

```console
--raw_sequencing_qc                   [boolean] Define whether the pipeline should run sequencing QC for raw input data.
--read_merging_qc                     [boolean] Define whether the pipeline should run sequencing QC for merged reads (only suitable for paired-end data with read merging enabled).
--adapter_trimming_qc                 [boolean] Define whether the pipeline should run sequencing QC for adapter trimmed reads (only suitable when adapter trimming enabled).
--primer_trimming_qc                  [boolean] Define whether the pipeline should run sequencing QC for primer trimmed reads (only suitable when primer trimming enabled).
--read_filtering_qc                   [boolean] Define whether the pipeline should run sequencing QC for filtered reads (only suitable when read filtering enabled).
--seqkit_stats_options                [string]  Define options for SeqKit stats (only suitable when at least one qc is enabled).
```

## Read merging options

```console
--read_merging                        [string]  Define whether the pipeline should merge reads (only suitable for paired-end data).
--seqprep_options                     [string]  Define options for SeqPrep (only suitable for pair-end data with SeqPrep enabled).
--flash2_options                      [string]  Define options for FLASH2 (only suitable for pair-end data with FLASH2 enabled).
```

## Read trimming options

```console
--adapter_trimming                    [string]  Define whether the pipeline should trim adapters from reads.
--adapter_cutadapt_options            [string]  Define options for cutadapt (only suitable when cutadapt enabled for adapter trimming).
--primer_trimming                     [string]  Define whether the pipeline should trim primers from reads.
--primer_cutadapt_options             [string]  Define options for cutadapt (only suitable when cutadapt enabled for primer trimming).
```

## Read filtering options

```console
--read_filtering                      [string]  Define whether the pipeline should filter reads (only suitable when input is single-end or read merging is enabled).
--seqkit_seq_options                  [string]  Define options for SeqKit seq (only suitable when read_filtering enabled).
```

## Library-dependent quantification options

```console
--oligo_library                       [string]  Path to tab-delimited file containing information about the oligos in the experiment (only suitable when library-dependent quantification enabled).
```

## Downsampling options

```console
--downsampling                        [boolean] Define whether the pipeline should downsample the input data
--downsampling_size                   [integer] Number of counts to downsample the input data to
--downsampling_seed                   [integer] Optional seed to give to the downsampler. 100 by default
```

## Useful core options

```console
-config
    Add the specified file to configuration set
-name
    Assign a mnemonic name to the a pipeline run
-params-file
    Load script parameters from a JSON/YAML file
-profile
    Choose a configuration profile
-resume
    Execute the script using the cached results, useful to continue executions that was stopped by an error
-w, -work-dir
    Directory where intermediate result files are stored
```
