// Import generic module functions
include { saveFiles } from './functions'

params.options = [:]

process SAMPLESHEET_CHECK_FASTQ {
    tag "$samplesheet"
    publishDir "${params.outdir}",
        mode: params.publish_dir_mode,
        saveAs: { filename -> saveFiles(filename:filename, options:params.options, publish_dir:'pipeline_info', meta:[:], publish_by_meta:[]) }

    container "docker.io/python:3.12.7"

    input:
    path samplesheet

    output:
    path '*.csv'

    script: // This script is bundled with the pipeline, in QUANTS/bin/
    """
    check_samplesheet_fastq.py \\
        $samplesheet \\
        samplesheet.valid.csv
    """
}

process SAMPLESHEET_CHECK_CRAM {
    tag "$samplesheet"
    publishDir "${params.outdir}",
        mode: params.publish_dir_mode,
        saveAs: { filename -> saveFiles(filename:filename, options:params.options, publish_dir:'pipeline_info', meta:[:], publish_by_meta:[]) }

    container "docker.io/python:3.12.7"

    input:
    path samplesheet

    output:
    path '*.csv'

    script: // This script is bundled with the pipeline, in QUANTS/bin/
    """
    check_samplesheet_cram.py \\
        "${params.single_end}" \\
        $samplesheet \\
        samplesheet.valid.csv
    """
}
