//
// Sequencing QC
//

params.options = [:]

//
// MODULE: Load nf-core modules
//
include { FASTQC  } from '../../modules/nf-core/modules/fastqc/main' addParams( options: [:] )

workflow SEQUENCING_QC {
    take: 
        reads

    main: 
        //
        // MODULE: Run FastQC
        //
        FASTQC ( reads )
    
    emit:
        FASTQC
}

    

    
    