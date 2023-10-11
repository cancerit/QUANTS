//
// Adapter/QC trimming
//

params.options = [:]
def modules = params.modules.clone()

//
// MODULE: cutadapt
//
def adapter_cutadapt_options  = modules['cutadapt_adapter']
if (params.adapter_cutadapt_options) {
    adapter_cutadapt_options.args += " " + params.adapter_cutadapt_options
}
include { CUTADAPT as CUTADAPT_ADAPTER  } from '../../modules/local/cutadapt/main' addParams( options: adapter_cutadapt_options )

workflow ADAPTER_TRIMMING {
    take:
        reads

    main:
        ch_trimmed_reads = Channel.empty()
        if (params.adapter_trimming == "cutadapt") {
            //
            // MODULE: Run cutadapt
            //

            CUTADAPT_ADAPTER ( reads )
            ch_trimmed_reads = CUTADAPT_ADAPTER.out.reads
            ch_trimmed_stats = CUTADAPT_ADAPTER.out.json
        }
    emit:
        reads = ch_trimmed_reads
        stats = ch_trimmed_stats
        versions = CUTADAPT_ADAPTER.out.version
}
