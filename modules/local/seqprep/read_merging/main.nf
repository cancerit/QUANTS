// Import generic module functions
include { initOptions; saveFiles; getSoftwareName } from './functions'

params.options = [:]
options        = initOptions(params.options)

process SEQPREP {
    tag "$meta.id"
    label 'process_medium'
    publishDir "${params.outdir}",
        mode: params.publish_dir_mode,
        saveAs: { filename -> saveFiles(filename:filename, options:params.options, publish_dir:getSoftwareName(task.process), meta:meta, publish_by_meta:['id']) }    conda (params.enable_conda ? "bioconda::seqprep=1.3.2" : null)

    if (workflow.containerEngine == 'singularity' && !params.singularity_pull_docker_container) {
        container "https://depot.galaxyproject.org/singularity/seqprep:1.3.2--h5bf99c6_5"
    } else {
        container "quay.io/biocontainers/seqprep:1.3.2--h5bf99c6_5"
    }

    input:
    tuple val(meta), path(reads)

    output:
    tuple val(meta), path("*.merged.fq.gz"), emit: reads
    tuple val(meta), path("*.merged.aln.gz"),   emit: alignment
    path "*.version.txt"                      , emit: version

    script:
    def software = getSoftwareName(task.process)
    def VERSION = '1.3.2'
    def prefix   = options.suffix ? "${meta.id}${options.suffix}" : "${meta.id}"
    def input_reads_forward = "${reads[0]}"
    def input_reads_reverse = "${reads[1]}"
    def output_reads_forward = "${prefix}.R1.unmerged.fq.gz"
    def output_reads_reverse = "${prefix}.R2.unmerged.fq.gz"
    def output_reads_merged = "${prefix}.merged.fq.gz"
    def output_alignment = "${prefix}.merged.aln.gz"

    """
    SeqPrep \\
        $options.args \\
        -f $input_reads_forward \\
        -r $input_reads_reverse \\
        -1 $output_reads_forward \\
        -2 $output_reads_reverse \\
        -s $output_reads_merged \\
        -E $output_alignment
    echo $VERSION >${software}.version.txt
    """
}
