//
// Library-dependent quantification
//

params.options = [:]
def modules = params.modules.clone()

//
// MODULE: pyCROQUET
//

// Library-dependent options
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
        if (params.quantification == "pycroquet") {
            //
            // MODULE: Run pyCROQUET
            //
            PYCROQUET ( 'long-read', reads, params.oligo_library )
            ch_sample_library_counts = PYCROQUET.out.library_counts
            ch_sample_read_counts = PYCROQUET.out.read_counts
            ch_sample_stats = PYCROQUET.out.stats
        }

    emit:
        library_counts = ch_sample_library_counts
        read_counts = ch_sample_read_counts
        stats = ch_sample_stats
}
