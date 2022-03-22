//
// Library-dependent quantification
//

params.options = [:]
def modules = params.modules.clone()

//
// MODULE: R-library_independent_quantification
//

include { LIBRARY_INDEPENDENT_QUANTIFICATION  } from '../../modules/local/R/library_independent_quantification/main.nf' addParams( )

workflow COMBINE_UNIQUE_READ_COUNTS_WITH_LIBRARY {
    take: 
        unique_read_counts

    main: 
        ch_sample_counts = Channel.empty()
        if (params.quantification == "pycroquet") {
            //
            // MODULE: Run pyCROQUET
            //
            LIBRARY_INDEPENDENT_QUANTIFICATION ( unique_read_counts, params.oligo_library)
            ch_sample_library_counts = LIBRARY_INDEPENDENT_QUANTIFICATION.out.counts
        }

    emit:
        library_counts = ch_sample_library_counts
}
