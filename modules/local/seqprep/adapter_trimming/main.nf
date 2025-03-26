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

    container "quay.io/biocontainers/seqprep:1.3.2--h5bf99c6_5"

    input:
    tuple val(meta), path(reads)

    output:
    tuple val(meta), path("*.unmerged.fq.gz"), emit: reads
    path "*.version.txt"                     , emit: version

    script:
    def software = getSoftwareName(task.process)
    def prefix   = options.suffix ? "${meta.id}${options.suffix}" : "${meta.id}"
    def input_reads_forward = "${reads[0]}"
    def input_reads_reverse = "${reads[1]}"
    def output_reads_forward = "${prefix}.R1.unmerged.fq.gz"
    def output_reads_reverse = "${prefix}.R2.unmerged.fq.gz"

    """
    SeqPrep \\
        $options.args \\
        -f $input_reads_forward \\
        -r $input_reads_reverse \\
        -1 $output_reads_forward \\
        -2 $output_reads_reverse
    echo '1.3.2' > ${software}.version.txt
    """
    // FIXME make version dynamic not hardcoded (SeqPrep has no --version option)
}
