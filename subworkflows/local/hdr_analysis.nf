//
// HDR analysis and QC
//

params.options = [:]

def modules = params.modules.clone()

//
// MODULE: Load pyCROQUET
//
def pycroquet_options  = modules['pycroquet']
if (params.pycroquet_options) {
    pycroquet_options.args += " " + params.pycroquet_options
} 
include { PYCROQUET  } from '../../modules/local/pycroquet/main.nf' addParams( options: pycroquet_options )


workflow HDR_ANALYSIS {
    take: 
        reads

    main: 
        ch_sample_counts = Channel.empty()
        if (params.hdr_analysis == "pycroquet") {
            //
            // MODULE: Run pyCROQUET
            //
            PYCROQUET ( reads )
            ch_sample_counts = PYCROQUET.out.counts
        }

    emit:
        counts = ch_sample_counts
}
