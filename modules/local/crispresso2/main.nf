// Import generic module functions
include { initOptions; saveFiles; getSoftwareName } from './functions'

params.options = [:]
options        = initOptions(params.options)

process CRISPRESSO2 {
    tag "$meta.id"
    label 'process_medium'
    publishDir "${params.outdir}",
        mode: params.publish_dir_mode,
        saveAs: { filename -> saveFiles(filename:filename, options:params.options, publish_dir:getSoftwareName(task.process), meta:meta, publish_by_meta:['id']) }    conda (params.enable_conda ? "bioconda::crispresso2=2.1.2" : null)

    if (workflow.containerEngine == 'singularity' && !params.singularity_pull_docker_container) {
        container "https://depot.galaxyproject.org/singularity/crispresso2:2.1.2--py27heb79e2c_0"
    } else {
        container "quay.io/biocontainers/crispresso2:2.1.2--py27heb79e2c_0"
    }

    input:
    tuple val(meta), path(reads)

    output:
    tuple val(meta), path("*.merged.*.fastq.gz"), emit: reads
    path "*.hist"                            , emit: hist
    path "*.version.txt"                      , emit: version

    script:
    def software = getSoftwareName(task.process)
    def prefix   = options.suffix ? "${meta.id}${options.suffix}" : "${meta.id}"
    def merged   = "-o ${prefix}.merged"
    def input_reads = "${reads[0]} ${reads[1]}"
    """
    flash2 \\
        $options.args \\
        $merged \\
        -z \\
        $input_reads
    echo \$(flash2 --version) > ${software}.version.txt
    """
}
