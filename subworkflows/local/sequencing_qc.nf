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
        fastqc_zip = FASTQC.out.zip
        fastqc_version = FASTQC.out.version
    
    emit:
        fastqc_zip
        fastqc_version
}

    

    
    