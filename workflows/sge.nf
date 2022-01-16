/*
========================================================================================
    VALIDATE INPUTS
========================================================================================
*/

def summary_params = NfcoreSchema.paramsSummaryMap(workflow, params)
def printErr = System.err.&println

// Validate input parameters
WorkflowSge.initialise(params, log)

// TODO nf-core: Add all file path parameters for the pipeline to the list below
// Check input path parameters to see if they exist
def checkPathParamList = [ params.input, params.multiqc_config ]
for (param in checkPathParamList) { if (param) { file(param, checkIfExists: true) } }

// Check mandatory parameters
if (params.input) { ch_input = file(params.input) } else { exit 1, 'Input samplesheet not specified!' }

// Check read merging software (if set)
def read_merging_software = ['seqprep', 'flash2']
if (params.read_merging) {
    if ( read_merging_software.contains( params.read_merging ) == false ) {
	    printErr("If read_merging is set, software must be one of: " + read_merging_software.join(',') + ".")
	    exit 1
    }
}

// Check read merging QC (if read merging set)
if (params.read_merging_qc && !params.read_merging) {
    printErr("Read merging QC cannot be run when read_merging is set to false.")
	exit 1
}

// Check read trimming software (if set)
def read_trimming_software = ['cutadapt']
if (params.read_trimming) {
    if ( read_trimming_software.contains( params.read_trimming ) == false ) {
	    printErr("If read_trimming is set, software must be one of: " + read_trimming_software.join(',') + ".")
	    exit 1
    }
}

// Check read trimming QC (if read trimming set)
if (params.read_trimming_qc && !params.read_trimming) {
    printErr("Read trimming QC cannot be run when read_trimming is set to false.")
	exit 1
}

// Check read fitering is valid (if set)
if (params.read_filtering && (!params.single_end && !params.read_merging)) {
    printErr("Read filtering cannot be run when data is paired end or single end, but read merging is set to false.")
	exit 1
}

// Check read trimming QC (if read trimming set)
if (params.read_filtering_qc && !params.read_filtering) {
    printErr("Read filtering QC cannot be run when read_filtering is set to false.")
	exit 1
}

// Check library-dependent quantification software (if set)
def library_dependent_quantification_software = ['pycroquet']
if (params.library_dependent_quantification) {
    if ( library_dependent_quantification_software.contains( params.library_dependent_quantification ) == false ) {
	    printErr("If library_dependent_quantification is set, software must be one of: " + library_dependent_quantification_software.join(',') + ".")
	    exit 1
    }
}

// Check library-dependent quantification library exists (if library_dependent_quantification set)
if (params.library_dependent_quantification && !params.oligo_library) {
    printErr("If library_dependent_quantification is set, a library file must be provided by oligo_library.")
    exit 1
}

// Check library-independent quantification software (if set)
def library_independent_quantification_software = ['pycroquet']
if (params.library_independent_quantification) {
    if ( library_independent_quantification_software.contains( params.library_independent_quantification ) == false ) {
	    printErr("If library_independent_quantification is set, software must be one of: " + library_independent_quantification_software.join(',') + ".")
	    exit 1
    }
}

/*
========================================================================================
    CONFIG FILES
========================================================================================
*/

ch_multiqc_config        = file("$projectDir/assets/multiqc_config.yaml", checkIfExists: true)
ch_multiqc_custom_config = params.multiqc_config ? Channel.fromPath(params.multiqc_config) : Channel.empty()

/*
========================================================================================
    IMPORT LOCAL MODULES/SUBWORKFLOWS
========================================================================================
*/

// Don't overwrite global params.modules, create a copy instead and use that within the main script.
def modules = params.modules.clone()

// MultiQC
def multiqc_options   = modules['multiqc']
multiqc_options.args += params.multiqc_title ? Utils.joinModuleArgs(["--title \"$params.multiqc_title\""]) : ''

//
// MODULE: Local to the pipeline
//
include { GET_SOFTWARE_VERSIONS } from '../modules/local/get_software_versions' addParams( options: [publish_files : ['tsv':'']] )
include { INPUT_CHECK } from '../subworkflows/local/input_check' addParams( options: [:] )
include { READ_MERGING } from '../subworkflows/local/read_merging' addParams( options: [:] )
include { READ_TRIMMING } from '../subworkflows/local/read_trimming' addParams( options: [:] )
include { READ_FILTERING } from '../subworkflows/local/read_filtering' addParams( options: [:] )
include { LIBRARY_DEPENDENT_QUANTIFICATION } from '../subworkflows/local/library_dependent_quantification' addParams( options: [:] )
include { LIBRARY_INDEPENDENT_QUANTIFICATION } from '../subworkflows/local/library_independent_quantification' addParams( options: [:] )
include { SEQUENCING_QC as RAW_SEQUENCING_QC; 
          SEQUENCING_QC as MERGED_SEQUENCING_QC; 
          SEQUENCING_QC as TRIMMED_SEQUENCING_QC;
          SEQUENCING_QC as FILTERED_SEQUENCING_QC
        } from '../subworkflows/local/sequencing_qc' addParams( options: [:] )

//
// MODULE: Installed directly from nf-core/modules
//
include { MULTIQC } from '../modules/nf-core/modules/multiqc/main' addParams( options: multiqc_options   )

/*
========================================================================================
    RUN MAIN WORKFLOW
========================================================================================
*/

// Info required for completion email and summary
def multiqc_report = []

workflow SGE {

    ch_software_versions = Channel.empty()

    //
    // SUBWORKFLOW: Read in samplesheet, validate and stage input files
    //
    INPUT_CHECK ( ch_input )

    //
    // SUBWORKFLOW: Run FASTQC on raw reads
    //
    if (params.raw_sequencing_qc) {
        ch_raw_read_qc = INPUT_CHECK.out.reads.map{it -> [[id: it[0].id + '_raw', single_end: it[0].single_end], it[1]]}
        RAW_SEQUENCING_QC ( ch_raw_read_qc )
    }

    //
    // SUBWORKFLOW: Run adapter/quality trimming
    //
    if (params.read_trimming) {
        READ_TRIMMING ( INPUT_CHECK.out.reads )
        if (params.read_trimming_qc) {
            ch_trimmed_read_qc = READ_TRIMMING.out.reads.map{it -> [[id: it[0].id + '_trimmed', single_end: it[0].single_end], it[1]]}
            TRIMMED_SEQUENCING_QC ( ch_trimmed_read_qc )
        }
    }

    //
    // SUBWORKFLOW: Run PE read merging on raw reads
    //
    if (params.read_merging) {
        if (params.read_trimming) {
            READ_MERGING ( READ_TRIMMING.out.reads )
        } else {
            READ_MERGING ( INPUT_CHECK.out.reads )
        }
        if (params.read_merging_qc) {
            ch_merged_read_qc = READ_MERGING.out.reads.map{it -> [[id: it[0].id + '_merged', single_end: true], it[1][1]]}
            MERGED_SEQUENCING_QC ( ch_merged_read_qc )
        }
    }

    //
    // SUBWORKFLOW: Run SE read filtering
    //
    if (params.read_filtering) {
        if (params.read_merging) {
            READ_FILTERING ( READ_MERGING.out.reads )
        } else if (params.read_trimming) {
            READ_FILTERING ( READ_TRIMMING.out.reads )
        } else {
            READ_FILTERING ( INPUT_CHECK.out.reads )
        }
        if (params.read_filtering_qc) {
            ch_filtered_read_qc = READ_FILTERING.out.reads.map{it -> [[id: it[0].id + '_filtered', single_end: true], it[1]]}
            FILTERED_SEQUENCING_QC ( ch_filtered_read_qc )
        }
    }

    //
    // Set up channel for analysis
    //
    // TODO: look for cleaner method of setting read channel for analysis
    // TODO: check how this performs with -resume 
    ch_reads_to_analyse = Channel.empty()
    if (params.read_filtering) {
        ch_reads_to_analyse = READ_FILTERING.out.reads.map{it -> [[id: it[0].id, single_end: true], it[1]]}
    } else if (params.read_merging) {
        ch_reads_to_analyse = READ_MERGING.out.reads.map{it -> [[id: it[0].id, single_end: true], it[1]]}
    } else if (params.read_trimming) {
        ch_reads_to_analyse = READ_TRIMMING.out.reads
    } else {
        ch_reads_to_analyse = INPUT_CHECK.out.reads
    }

    //
    // SUBWORKFLOW: Run library-dependent quantification
    // Returns the number of reads assigned to each guide from a user-defined library
    //
    if (params.library_dependent_quantification) {
        LIBRARY_DEPENDENT_QUANTIFICATION ( ch_reads_to_analyse )
    }

    //
    // SUBWORKFLOW: Run library-independent quantification
    // Returns the frequency of unique reads
    //
    if (params.library_independent_quantification) {
        LIBRARY_INDEPENDENT_QUANTIFICATION ( ch_reads_to_analyse )
    }

    //
    // MODULE: Pipeline reporting
    //
    ch_software_versions
        .map { it -> if (it) [ it.baseName, it ] }
        .groupTuple()
        .map { it[1][0] }
        .flatten()
        .collect()
        .set { ch_software_versions }

    GET_SOFTWARE_VERSIONS (
        ch_software_versions.map { it }.collect()
    )

    //
    // MODULE: MultiQC
    //
    if (params.raw_sequencing_qc || params.read_trimming_qc || params.read_merging_qc) {
        workflow_summary    = WorkflowSge.paramsSummaryMultiqc(workflow, summary_params)
        ch_workflow_summary = Channel.value(workflow_summary)

        ch_multiqc_files = Channel.empty()
        ch_multiqc_files = ch_multiqc_files.mix(Channel.from(ch_multiqc_config))
        ch_multiqc_files = ch_multiqc_files.mix(ch_multiqc_custom_config.collect().ifEmpty([]))
        ch_multiqc_files = ch_multiqc_files.mix(ch_workflow_summary.collectFile(name: 'workflow_summary_mqc.yaml'))
        ch_multiqc_files = ch_multiqc_files.mix(GET_SOFTWARE_VERSIONS.out.yaml.collect())

        if (params.raw_sequencing_qc) {
            ch_multiqc_files = ch_multiqc_files.mix(RAW_SEQUENCING_QC.out.fastqc_zip.collect{it[1]}.ifEmpty([]))
        }
        if (params.read_trimming_qc) {
            ch_multiqc_files = ch_multiqc_files.mix(TRIMMED_SEQUENCING_QC.out.fastqc_zip.collect{it[1]}.ifEmpty([]))
            ch_multiqc_files = ch_multiqc_files.mix(READ_TRIMMING.out.stats.collect{it[1]}.ifEmpty([]))
        }
        if (params.read_merging_qc) {
            ch_multiqc_files = ch_multiqc_files.mix(MERGED_SEQUENCING_QC.out.fastqc_zip.collect{it[1]}.ifEmpty([]))
        }
        if (params.read_filtering_qc) {
            ch_multiqc_files = ch_multiqc_files.mix(FILTERED_SEQUENCING_QC.out.fastqc_zip.collect{it[1]}.ifEmpty([]))
        }
        
        MULTIQC (
            ch_multiqc_files.collect()
        )

        multiqc_report       = MULTIQC.out.report.toList()
        ch_software_versions = ch_software_versions.mix(MULTIQC.out.version.ifEmpty(null))
    } 
}

/*
========================================================================================
    COMPLETION EMAIL AND SUMMARY
========================================================================================
*/

workflow.onComplete {
    //NfcoreTemplate.email(workflow, params, summary_params, projectDir, log, multiqc_report)
    NfcoreTemplate.summary(workflow, params, log)
}

/*
========================================================================================
    THE END
========================================================================================
*/
