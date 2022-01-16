//
// Library-dependent quantification
//

params.options = [:]

def modules = params.modules.clone()

//
// MODULE: Load pyCROQUET
//
def pycroquet_options  = modules['pycroquet']
if (params.pycroquet_lib_dep_options) {
    pycroquet_options.args += " " + params.pycroquet_lib_dep_options
} 
include { PYCROQUET  } from '../../modules/local/pycroquet/main.nf' addParams( options: pycroquet_options )


workflow LIBRARY_DEPENDENT_QUANTIFICATION {
    take: 
        reads

    main: 
        ch_sample_counts = Channel.empty()
        if (params.library_dependent_quantification == "pycroquet") {
            //
            // MODULE: Run pyCROQUET
            //
            PYCROQUET ( 'long-read', reads, params.oligo_library )
            ch_sample_counts = PYCROQUET.out.counts
            ch_sample_stats = PYCROQUET.out.stats
        }

    emit:
        counts = ch_sample_counts
        stats = ch_sample_stats
}
