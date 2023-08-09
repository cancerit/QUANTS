//
// Primer/QC trimming
//

params.options = [:]
def modules = params.modules.clone()

//
// MODULE: cutadapt
//
def primer_cutadapt_options  = modules['cutadapt_primer']
if (params.primer_cutadapt_options) {
    primer_cutadapt_options.args += " " + params.primer_cutadapt_options
} 
include { CUTADAPT_PRIMER  } from '../../modules/local/cutadapt_primer/main' addParams( options: primer_cutadapt_options )

workflow PRIMER_TRIMMING {
    take: 
        reads

    main: 
        ch_trimmed_reads = Channel.empty()
        if (params.primer_trimming == "cutadapt") {
            //
            // MODULE: Run cutadapt
            //

            CUTADAPT_PRIMER ( reads )
            ch_trimmed_reads = CUTADAPT_PRIMER.out.reads
            ch_trimmed_stats = CUTADAPT_PRIMER.out.log
        }
    emit:
        reads = ch_trimmed_reads
        stats = ch_trimmed_stats
        versions = CUTADAPT_PRIMER.out.version
}
