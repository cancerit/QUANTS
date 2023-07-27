// Import generic module functions
include { initOptions; saveFiles; getSoftwareName } from './functions'

params.options = [:]
options        = initOptions(params.options)

process SEQKIT_STATS {
    tag "$meta.id"
    label 'process_medium'

    publishDir "${params.outdir}",
        mode: params.publish_dir_mode,
        saveAs: { filename -> saveFiles(filename:filename, options:params.options, publish_dir:getSoftwareName(task.process)+'_stats', meta:meta, publish_by_meta:['id']) }

    conda (params.enable_conda ? "bioconda::seqkit=0.15.0" : null)

    if (workflow.containerEngine == 'singularity' && !params.singularity_pull_docker_container) {
        container "https://depot.galaxyproject.org/singularity/seqkit:0.15.0--0"
    } else {
        container "quay.io/biocontainers/seqkit:0.15.0--0"
    }

    input:
        tuple val(meta), path(reads)

    output:
        tuple val(meta), path("*.stats.txt"), emit: stats
        path("*.version.txt")               , emit: version

    script:
    def software = getSoftwareName(task.process)
    def prefix   = options.suffix ? "${meta.id}${options.suffix}" : "${meta.id}"

    if(meta.single_end){
    """
    seqkit \
        stats \
        $options.args \
        --threads $task.cpus \
        --out-file ${prefix}.stats.txt \
        ${reads[0]}

    echo \$(seqkit version 2>&1) | sed 's/^.*seqkit //' > ${software}.version.txt
    """
    } else {
    """
    seqkit \
        stats \
        $options.args \
        --threads $task.cpus \
        --out-file ${prefix}.stats.txt \
        ${reads[0]} \
        ${reads[1]}

    echo \$(seqkit version 2>&1) | sed 's/^.*seqkit //' > ${software}.version.txt
    """
    }
}