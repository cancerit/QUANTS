//
// Read transformation - complement
//

params.options = [:]
def modules = params.modules.clone()

//
// MODULE: SeqKit seq
//
def seqkit_seq_options  = modules['seqkit_seq']
if (params.read_transform != null && params.read_transform.contains('complement')) {
    seqkit_seq_options.args += " -p"
}
if (params.read_transform != null && params.read_transform.contains('reverse')) {
    seqkit_seq_options.args += " -r"
}

include { SEQKIT_SEQ  } from '../../modules/local/seqkit_seq/main' addParams( options: seqkit_seq_options )

workflow READ_TRANSFORM {
    take: 
        reads

    main: 
        ch_transform_reads = Channel.empty()
        //
        // MODULE: Run SeqKit seq
        //

        SEQKIT_SEQ ( reads, "${params.read_transform}" )
        ch_transform_reads = SEQKIT_SEQ.out.reads
    emit:
        reads = ch_transform_reads
}
