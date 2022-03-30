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

workflow QUANTIFICATION {
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

//
// MODULE: R quantifying pyCROQUET library with pyCROQUET-generated unique read counts
//

include { QUANTIFY_PYCROQUET_LIBRARY_WITH_UNIQUE_READ_COUNTS  } from '../../modules/local/R/post_pycroquet_quantification/main.nf' addParams( )

workflow POST_PYCROQUET_QUANTIFICATION {
    take: 
        unique_read_counts

    main: 
        ch_sample_counts = Channel.empty()
        if (params.quantification == "pycroquet") {
            //
            // MODULE: Quantify/merge pyCROQUET library with unique read counts from pyCROQUET
            //
            QUANTIFY_PYCROQUET_LIBRARY_WITH_UNIQUE_READ_COUNTS ( unique_read_counts, params.oligo_library)
            ch_sample_library_counts = QUANTIFY_PYCROQUET_LIBRARY_WITH_UNIQUE_READ_COUNTS.out.counts
        }

    emit:
        library_counts = ch_sample_library_counts
}
