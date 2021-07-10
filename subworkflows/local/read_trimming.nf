//
// Adapter/QC trimming
//

params.options = [:]

//
// MODULE: Load nf-core modules
//
include { CUTADAPT  } from '../../modules/nf-core/modules/cutadapt/main' addParams( options: [:] )


workflow READ_TRIMMING {
    take: 
        reads

    main: 
        ch_trimmed_reads = Channel.empty()
        if (params.read_trimming == "cutadapt") {
            //
            // MODULE: Run cutadapt
            //
            CUTADAPT ( reads )
            ch_trimmed_reads = CUTADAPT.out.reads
        }
    emit:
        reads = ch_trimmed_reads
}
