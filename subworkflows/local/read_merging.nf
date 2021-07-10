//
// Merge paired end reads
//

params.options = [:]

//
// MODULE: Local modules
//
include { FLASH2 } from '../../modules/local/flash2/main.nf' addParams( options: [:]   )
include { SEQPREP } from '../../modules/local/seqprep/read_merging/main.nf' addParams( options: [:]   )

workflow READ_MERGING {
    take: 
        reads

    main: 
        ch_merged_reads = Channel.empty()
        if (params.read_merging == "flash2") {
            //
            // MODULE: Run FLASH
            //
            FLASH2 ( reads )
            ch_merged_reads = FLASH2.out.reads
        }
        
        if (params.read_merging == "seqprep") {
            //
            // MODULE: Run SeqPrep
            //
            SEQPREP ( reads )
            ch_merged_reads = SEQPREP.out.reads
        }

        ch_merged_reads = ch_merged_reads.map{it -> [[id: it[0].id + '_merged', single_end: 'true'], [it[1]]]}

    emit:
        reads = ch_merged_reads
}
