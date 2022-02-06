# QUANTS: Usage

## Pipeline parameters

To see available parameters (assuming you are in the QUANTS pipeline directory):

```
nextflow run . --help
```

For full parameters:

```
nextflow run . --help --show_hidden_params
```

For parameter descriptions, please see [configuration](assets/configuration) documentation.

## Running the pipeline

### With library-dependent quantification enabled

The typical command for running the pipeline when library-dependent quantification is enabled is as follows:

```console
nextflow run QUANTS --input samplesheet.csv --oligo_library library.tsv -profile <docker|singlularity>
```

*Note: library-dependent quantification requires the `library_dependent_quantification` parameter to be set and the path to the library file to be provided with the `oligo_library` parameter.*

### With library-dependent quantification disabled

The typical command for running the pipeline when library-dependent quantification is enabled is as follows:

```console
nextflow run QUANTS --input samplesheet.csv --oligo_library library.tsv -profile <docker|singlularity>
```

*Note: The `oligo_library` parameter is not required when `library_dependent_quantification` is `false`.*

## Core Nextflow arguments

> **NB:** These options are part of Nextflow and use a _single_ hyphen (pipeline parameters use a double-hyphen).

### `-profile`

Use this parameter to choose a configuration profile. Profiles can give configuration presets for different compute environments.

Several generic profiles are bundled with the pipeline which instruct the pipeline to use software packaged using different methods (Docker or Singularity) - see below. When using Biocontainers, most of these software packaging methods pull Docker containers from quay.io e.g [FastQC](https://quay.io/repository/biocontainers/fastqc) except for Singularity which directly downloads Singularity images via https hosted by the [Galaxy project](https://depot.galaxyproject.org/singularity/) for nf-core modules.

Note that multiple profiles can be loaded, for example: `-profile test,docker` - the order of arguments is important!
They are loaded in sequence, so later profiles can overwrite earlier profiles.

If `-profile` is not specified, the pipeline will run locally and expect all software to be installed and available on the `PATH`. This is _not_ recommended.

* `docker`
    * A generic configuration profile to be used with [Docker](https://docker.com/)
* `singularity`
    * A generic configuration profile to be used with [Singularity](https://sylabs.io/docs/)

### `-resume`

Specify this when restarting a pipeline. Nextflow will used cached results from any pipeline steps where the inputs are the same, continuing from where it got to previously.

You can also supply a run name to resume a specific run: `-resume [run-name]`. Use the `nextflow log` command to show previous run names.

### `-c`

Specify the path to a specific config file (this is a core Nextflow command). See the [nf-core](https://nf-co.re/usage/configuration) and [Nextflow](https://www.nextflow.io/docs/latest/config.html) documentation for more information.

Below is a basic example:

```
params {
   single_end: true
   "cutadapt_options": "-a 'AGATCGGAAGAGCGGTTCAGCAGGAATGCCG' -A 'AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT'",
}
```

### `-params-file`

Specify the path to a specific JSON file containing configuration parameters (this is a core Nextflow command). This is similar, but differently formatted, to `-c`. See the [Nextflow](https://www.nextflow.io/docs/latest/config.html) documentation for more information.

For configuration options, please see [configuration](assets/configuration) documentation.

## Core Nextflow outputs

Note that the pipeline will create the following files in your working directory:

```console
work            # Directory containing the nextflow working files
results         # Finished results (configurable)
.nextflow_log   # Log file from Nextflow
# Other nextflow hidden files, eg. history of pipeline runs and old logs.
```