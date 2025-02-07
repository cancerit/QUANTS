// Import generic module functions
include { initOptions; saveFiles; getSoftwareName } from './functions'

params.options = [:]
options        = initOptions(params.options)

process FLASH2 {
    tag "$meta.id"
    label 'process_medium'
    publishDir "${params.outdir}",
        mode: params.publish_dir_mode,
        saveAs: { filename -> saveFiles(filename:filename, options:params.options, publish_dir:getSoftwareName(task.process), meta:meta, publish_by_meta:['id']) }    conda (params.enable_conda ? "bioconda::flash=2.2.00" : null)

    container "quay.io/biocontainers/flash2:2.2.00--h5bf99c6_3"

    input:
    tuple val(meta), path(reads)

    output:
    tuple val(meta), path("*.merged.extendedFrags*.fastq.gz"), emit: reads
    tuple val(meta), path("*.merged.notCombined*.fastq.gz")  , emit: uncombined_reads
    path "*.hist"                                            , emit: hist
    path "*.version.txt"                                     , emit: version

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
    flash2 --version | awk 'NR==1{print \$2}' > ${software}.version.txt
    """
}
