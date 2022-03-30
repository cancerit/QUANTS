//
// Check input samplesheet and get read channels
//

// TODO: look into better ways for handling CRAM vs FASTQ input types
// For now, reads can also mean CRAM depending on input_type

params.options = [:]

include { SAMPLESHEET_CHECK_FASTQ; SAMPLESHEET_CHECK_CRAM } from '../../modules/local/samplesheet_check' addParams( options: params.options )

workflow INPUT_CHECK_FASTQ {
    take:
    samplesheet // file: /path/to/samplesheet.csv

    main:
    //TODO: look into doing this as a single step rather than duplicating check loop
    SAMPLESHEET_CHECK_FASTQ ( samplesheet )
        .splitCsv ( header:true, sep:',' )
        .map { create_fastq_channels(it) }
        .set { reads }
    emit:
        reads // channel: [ val(meta), [ reads ] ]
}

// Function to get list of [ meta, [ fastq_1, fastq_2 ] ]
def create_fastq_channels(LinkedHashMap row) {
    def meta = [:]
    meta.id           = row.sample
    meta.single_end   = row.single_end.toBoolean()

    def array = []
    if (!file(row.fastq_1).exists()) {
        exit 1, "ERROR: Please check input samplesheet -> Read 1 FastQ file does not exist!\n${row.fastq_1}"
    }
    if (meta.single_end) {
        array = [ meta, [ file(row.fastq_1) ] ]
    } else {
        if (!file(row.fastq_2).exists()) {
            exit 1, "ERROR: Please check input samplesheet -> Read 2 FastQ file does not exist!\n${row.fastq_2}"
        }
        array = [ meta, [ file(row.fastq_1), file(row.fastq_2) ] ]
    }
    return array
}

workflow INPUT_CHECK_CRAM {
    take:
    samplesheet // file: /path/to/samplesheet.csv

    main:
    //TODO: look into doing this as a single step rather than duplicating check loop
    SAMPLESHEET_CHECK_CRAM ( samplesheet )
        .splitCsv ( header:true, sep:',' )
        .map { create_cram_channels(it) }
        .set { crams }
    emit:
        crams // channel: [ val(meta), [ cram_file ] ]
}

// Function to get list of [ meta, [ cram_file ] ]
def create_cram_channels(LinkedHashMap row) {
    def meta = [:]
    meta.id           = row.sample
    meta.single_end   = row.single_end.toBoolean()

    def array = []
    if (!file(row.cram_file).exists()) {
        exit 1, "ERROR: Please check input samplesheet -> CRAM file does not exist!\n${row.cram_file}"
    }
    array = [ meta, [ file(row.cram_file) ] ]
    return array
}