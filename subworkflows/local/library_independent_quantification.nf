//
// Library-independent quantification
//

params.options = [:]

def modules = params.modules.clone()

//
// MODULE: Load pyCROQUET
//
def pycroquet_options  = modules['pycroquet']
if (params.pycroquet_lib_indep_options) {
    pycroquet_options.args += " " + params.pycroquet_lib_indep_options
} 
include { PYCROQUET  } from '../../modules/local/pycroquet/main.nf' addParams( options: pycroquet_options )


workflow LIBRARY_INDEPENDENT_QUANTIFICATION {
    take: 
        reads

    main: 
        ch_sample_counts = Channel.empty()
        if (params.library_independent_quantification == "pycroquet") {
            //
            // MODULE: Run pyCROQUET
            //
            PYCROQUET ( 'long-read --unique', reads, params.oligo_library )
            ch_sample_counts = PYCROQUET.out.counts
        }

    emit:
        counts = ch_sample_counts
}
