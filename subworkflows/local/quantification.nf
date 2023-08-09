//
// Quantification
//

params.options = [:]
def modules = params.modules.clone()

//
// MODULE: pyQUEST
//

def pyquest_options  = modules['pyquest']
include { PYQUEST  } from '../../modules/local/pyquest/main.nf' addParams( options: pyquest_options )

workflow QUANTIFICATION {
    take: 
        reads

    main: 
        ch_sample_counts = Channel.empty()
        if (params.quantification == "pyquest") {
            //
            // MODULE: Run pyQUEST
            //
            PYQUEST ( reads )
            ch_sample_library_counts = PYQUEST.out.library_counts
            ch_sample_read_counts = PYQUEST.out.read_counts
            ch_sample_stats = PYQUEST.out.stats
            versions = PYQUEST.out.version
        }

    emit:
        library_counts = ch_sample_library_counts
        read_counts = ch_sample_read_counts
        stats = ch_sample_stats
        versions
}