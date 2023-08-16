//
// Read modification
//

params.options = [:]

include { APPEND_STRINGS_TO_FQ  } from '../../modules/local/read_modification/main'

workflow READ_MODIFICATION {
    take:
        reads

    main:
        ch_modified_reads = Channel.empty()
        if (params.read_modification) {
            //
            // MODULE: Append string to reads
            //

            APPEND_STRINGS_TO_FQ ( reads, 'modified' )
            ch_modified_reads = APPEND_STRINGS_TO_FQ.out.reads
        }
    emit:
        reads = ch_modified_reads
}