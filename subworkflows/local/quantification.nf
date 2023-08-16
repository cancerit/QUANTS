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

//
// MODULE: pyQUEST library transformer
// Script found in modules/local/pyquest_library_converter/bin/pyquest_library_converter
//
def pyquest_library_converter_options  = modules['pyquest_library_converter']
if (params.pyquest_library_converter_options) {
    pyquest_library_converter_options.args += " " + params.pyquest_library_converter_options
}
include { TRANSFORM_LIBRARY_FOR_PYQUEST  } from '../../modules/local/pyquest_library_converter/main.nf' addParams( options: pyquest_library_converter_options )

workflow QUANTIFICATION {
    take:
        reads
        oligo_library

    main:
        ch_sample_counts = Channel.empty()
        if (params.transform_library) {
            //
            // MODULE: Run Python library transformer
            //
            TRANSFORM_LIBRARY_FOR_PYQUEST ( oligo_library )
        } 

        if (params.quantification == "pyquest") {
            //
            // MODULE: Run pyQUEST
            //
            if (params.transform_library) {
                PYQUEST ( reads, TRANSFORM_LIBRARY_FOR_PYQUEST.out.oligo_library )
            } else {
                PYQUEST ( reads, oligo_library )
            }
            
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
