// Import generic module functions
include { initOptions; saveFiles; getSoftwareName } from './functions'

params.options = [:]
options        = initOptions(params.options)

process APPEND_STRINGS_TO_FQ {
    tag "$meta.id"
    label 'process_low'

    publishDir "${params.outdir}",
        mode: params.publish_dir_mode,
        saveAs: { filename -> saveFiles(filename:filename, options:params.options, publish_dir:'modified_fastq', meta:meta, publish_by_meta:['id']) }

    input:
        tuple val(meta), path(reads)

    output:
        tuple val(meta), path("*.modified.fq.gz"), emit: reads

    script:
    def software = getSoftwareName(task.process)
    def prefix = options.suffix ? "${meta.id}${options.suffix}" : "${meta.id}"
    def input = reads
    def append_start = params.append_start ? params.append_start : ""
    def append_end = params.append_end ? params.append_end : ""
    def append_quality_start = params.append_start ? params.append_quality*append_start.length() : ""
    def append_quality_end = params.append_end ? params.append_quality*append_end.length() : ""
    def output = "${prefix}.modified.fq.gz"
    """
    zcat ${input} | awk -v append_start="${append_start}" -v append_end="${append_end}" -v append_quality_start="${append_quality_start}" -v append_quality_end="${append_quality_end}" '
        NR % 4 == 2 { print append_start \$0 append_end; next }
        NR % 4 == 0 { print append_quality_start \$0 append_quality_end; next }
        { print \$0 }
        ' | gzip > ${output}
    """

    
    // "zcat ${input} | sed -e '2~4s/^\(.*\)$/${append_start}\1${append_end}/' -e '4~4s/^\(.*\)$/${append_quality_start}\1${append_quality_end}/' | gzip > ${output}'

    // $/
    //     zcat ${input} | \
    //     sed -e '2~4s/^\(.*\)$/${append_start}\1${append_end}/' -e '4~4s/^\(.*\)$/${append_quality_start}\1${append_quality_end}/' | \
    //     gzip > ${output}
    // /$
}
