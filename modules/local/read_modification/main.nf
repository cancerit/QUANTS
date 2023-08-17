// Import generic module functions
include { initOptions; saveFiles; getSoftwareName } from './functions'

params.options = [:]
options        = initOptions(params.options)

process APPEND_STRINGS_TO_FQ {
    tag "$meta.id"
    label 'process_medium'

    publishDir "${params.outdir}",
        mode: params.publish_dir_mode,
        saveAs: { filename -> saveFiles(filename:filename, options:params.options, publish_dir:'modified_fastq', meta:meta, publish_by_meta:['id']) }

    input:
        tuple val(meta), path(reads)
        val(suffix)

    output:
        tuple val(meta), path("*.modified.fq.gz"), emit: reads

    script:
    def software = getSoftwareName(task.process)
    def prefix   = options.suffix ? "${meta.id}${options.suffix}" : "${meta.id}"
    def input = reads
    def append_start = params.append_start ? params.append_start : ""
    def append_end = params.append_end ? params.append_end : ""
    def append_quality_start = params.append_start ? params.append_quality*append_start.length() : ""
    def append_quality_end = params.append_end ? params.append_quality*append_end.length() : ""
    def output = "${prefix}.modified.fq"

    $/
    zcat ${input} | \
        sed -e '2~4s/^\(.*\)$/${append_start}\1${append_end}/' | \
        sed -e '4~4s/^\(.*\)$/${append_quality_start}\1${append_quality_end}/' > ${output}
    gzip ${output}
    /$
}
