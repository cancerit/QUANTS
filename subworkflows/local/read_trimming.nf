//
// Adapter/QC trimming
//

params.options = [:]
def modules = params.modules.clone()

//
// MODULE: cutadapt
//
def cutadapt_options  = modules['cutadapt']
if (params.cutadapt_options) {
    cutadapt_options.args += " " + params.cutadapt_options
} 
include { CUTADAPT  } from '../../modules/nf-core/modules/cutadapt/main' addParams( options: cutadapt_options )

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
            ch_trimmed_stats = CUTADAPT.out.log
        }
    emit:
        reads = ch_trimmed_reads
        stats = ch_trimmed_stats
        versions = CUTADAPT.out.version
}
