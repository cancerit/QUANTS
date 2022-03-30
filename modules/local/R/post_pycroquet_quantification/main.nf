// Import generic module functions
include { initOptions; saveFiles; getSoftwareName } from './functions'

params.options = [:]
options        = initOptions(params.options)

process QUANTIFY_PYCROQUET_LIBRARY_WITH_UNIQUE_READ_COUNTS {
    tag "$meta.id"
    label 'process_medium'
    publishDir "${params.outdir}",
        mode: params.publish_dir_mode,
        saveAs: { filename -> saveFiles(filename:filename, options:params.options, publish_dir:'pycroquet', meta:meta, publish_by_meta:['id']) }    conda (params.enable_conda ? "bioconda::r-tidyverse=1.2.1-mro351hf348343_0" : null)

    if (workflow.containerEngine == 'singularity' && !params.singularity_pull_docker_container) {
        container "https://depot.galaxyproject.org/singularity/r-tidyverse:1.2.1"
    } else {
        container "rocker/tidyverse:4.1.2"
    }

    input:
    tuple val(meta), path(unique_read_counts)
    path(pycroquet_library)

    output:
    tuple val(meta), path("*.query_to_library_counts.tsv.gz"), emit: counts
    path "*.version.txt"                            , emit: version

    script:
    def software = getSoftwareName(task.process)
    def script = "${moduleDir}/bin/quantify_pyCROQUET_library_using_unique_read_counts.R"
    def outfile = "${meta.id}.query_to_library_counts.tsv"
    """
    Rscript \\
        $options.args \\
        $script \\
        $pycroquet_library\\
        $unique_read_counts \\
        ${meta.id}
    gzip "${outfile}"
    echo \$(Rscript --version) > ${software}.version.txt
    """
}
