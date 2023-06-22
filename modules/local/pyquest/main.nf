// Import generic module functions
include { initOptions; saveFiles; getSoftwareName } from './functions'

params.options = [:]
options        = initOptions(params.options)

process PYQUEST {
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
    container "quay.io/wtsicgp/pyquest:1.0.0"

    input:
        tuple val(meta), path(reads)

    output:
        tuple val(meta), path("*query_counts.tsv.gz")       , emit: read_counts
        tuple val(meta), path("*lib_counts.tsv.gz")         , optional: true, emit: library_counts
        tuple val(meta), path("*.stats.json")               , optional: true, emit: stats
        path "*.version.txt"                                , emit: version

    script:
        def software    = getSoftwareName(task.process)
        def queries     = params.oligo_library ? "-l ${params.oligo_library}" : ""
        def sample      = options.suffix ? "-s ${meta.id}${options.suffix}" : "-s ${meta.id}"
        def output      = options.suffix ? "-o ${meta.id}${options.suffix}" : "-o ${meta.id}"
        def reads       = reads

    """
    pyquest \\
        $options.args \\
        --cpus $task.cpus \\
        $queries \\
        $sample \\
        $output \\
        $reads
    echo \$(pyquest --version) > ${software}.version.txt
    """
}
