//
// Sequencing QC
//

params.options = [:]
def modules = params.modules.clone()

//
// MODULE: Load nf-core modules
//
include { FASTQC  } from '../../modules/nf-core/modules/fastqc/main' addParams( options: [:] )

//
// MODULE: SeqKit stats
//
def seqkit_stats_options  = modules['seqkit_stats']
if (params.seqkit_stats_options) {
    seqkit_stats_options.args += " " + params.seqkit_stats_options
}
include { SEQKIT_STATS  } from '../../modules/local/seqkit_stats/main' addParams( options: seqkit_stats_options )

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

        //
        // MODULE: Run SeqKit stats
        //
        SEQKIT_STATS( reads )
        seqkit_stats = SEQKIT_STATS.out.stats
        seqkit_version = SEQKIT_STATS.out.version

    emit:
        fastqc_zip
        fastqc_version
        seqkit_stats
        seqkit_version
}
