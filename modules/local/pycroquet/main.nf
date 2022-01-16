// Import generic module functions
include { initOptions; saveFiles; getSoftwareName } from './functions'

params.options = [:]
options        = initOptions(params.options)

process PYCROQUET {
    tag "$meta.id"
    label 'process_medium'
    publishDir "${params.outdir}",
        mode: params.publish_dir_mode,
        saveAs: { filename -> saveFiles(filename:filename, options:params.options, publish_dir:getSoftwareName(task.process), meta:meta, publish_by_meta:['id']) }    conda (params.enable_conda ? null : null)

    // Keep for when container is public
    /*
    if (workflow.containerEngine == 'singularity' && !params.singularity_pull_docker_container) {
        container "https://depot.galaxyproject.org/singularity/flash2:2.2.00--h5bf99c6_3"
    } else {
        container "quay.io/biocontainers/flash2:2.2.00--h5bf99c6_3"
    }
    */
    container "quay.io/wtsicgp/pycroquet:1.5.0"

    input:
        val(subcommand)
        tuple val(meta), path(reads)
        path(guides)

    output:
        tuple val(meta), path("*counts.tsv.gz")            , emit: counts
        tuple val(meta), path("*.stats.json")               , optional: true, emit: stats
        tuple val(meta), path("*.cram"), path("*.cram.crai"), optional: true, emit: cram
        path "*.version.txt"                                , emit: version

    script:
        def software    = getSoftwareName(task.process)
        def queries     = guides ? "-q ${reads} -g ${guides}" : "-q ${reads}"
        def sample      = options.suffix ? "-s ${meta.id}${options.suffix}" : "-s ${meta.id}"
        def output      = options.suffix ? "-o ${meta.id}${options.suffix}" : "-o ${meta.id}"

    """
    pycroquet \\
        $subcommand \\
        $options.args \\
        --cpus $task.cpus \\
        $queries\\
        $sample\\
        $output
    echo \$(pycroquet --version) > ${software}.version.txt
    """
}
