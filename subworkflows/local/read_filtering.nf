//
// Read filtering
//

params.options = [:]
def modules = params.modules.clone()

//
// MODULE: SeqKit seq
//
def seqkit_seq_options  = modules['seqkit_seq']
if (params.seqkit_seq_options) {
    seqkit_seq_options.args += " " + params.seqkit_seq_options
} 
include { SEQKIT_SEQ  } from '../../modules/local/seqkit_seq/main' addParams( options: seqkit_seq_options )

workflow READ_FILTERING {
    take: 
        reads

    main: 
        ch_filtered_reads = Channel.empty()
        if (params.read_filtering) {
            //
            // MODULE: Run SeqKit seq
            //

            SEQKIT_SEQ ( reads, 'filtered' )
            ch_filtered_reads = SEQKIT_SEQ.out.reads
        }
    emit:
        reads = ch_filtered_reads
        versions = SEQKIT_SEQ.out.version
}
