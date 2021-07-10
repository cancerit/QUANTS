/*
========================================================================================
    VALIDATE INPUTS
========================================================================================
*/

def summary_params = NfcoreSchema.paramsSummaryMap(workflow, params)
def printErr = System.err.&println

// Validate input parameters
//WorkflowSge.initialise(params, log)

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

// Check read trimming software (if set)
def read_trimming_software = ['cutadapt']
if (params.read_trimming) {
    if ( read_trimming_software.contains( params.read_trimming ) == false ) {
	    printErr("If read_trimming is set, software must be one of: " + read_trimming_software.join(',') + ".")
	    exit 1
    }
}

// Check read merging QC (if set)
if (params.read_merging_qc && !params.read_merging) {
    printErr("Read merging QC cannot be run when read_merging is set to false.")
	exit 1
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

//
// MODULE: Local to the pipeline
//
include { GET_SOFTWARE_VERSIONS } from '../modules/local/get_software_versions' addParams( options: [publish_files : ['tsv':'']] )

//
// SUBWORKFLOW: Consisting of a mix of local and nf-core/modules
//
include { INPUT_CHECK } from '../subworkflows/local/input_check' addParams( options: [:] )
include { READ_MERGING } from '../subworkflows/local/read_merging' addParams( options: [:] )
include { READ_TRIMMING } from '../subworkflows/local/read_trimming' addParams( options: [:] )
include { SEQUENCING_QC as RAW_SEQUENCING_QC; SEQUENCING_QC as MERGED_SEQUENCING_QC; SEQUENCING_QC as TRIMMED_SEQUENCING_QC;} from '../subworkflows/local/sequencing_qc' addParams( options: [:] )

/*
========================================================================================
    IMPORT NF-CORE MODULES/SUBWORKFLOWS
========================================================================================
*/

def multiqc_options   = modules['multiqc']
//multiqc_options.args += params.multiqc_title ? Utils.joinModuleArgs(["--title \"$params.multiqc_title\""]) : ''

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
        //RAW_SEQUENCING_QC ( INPUT_CHECK.out.reads )
    }

    //
    // SUBWORKFLOW: Run adapter/quality trimming
    //
    if (params.read_trimming) {
        READ_TRIMMING ( INPUT_CHECK.out.reads )
        if (params.read_trimming_qc) {
            //TRIMMED_SEQUENCING_QC ( READ_TRIMMING.out.reads )
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
            //MERGED_SEQUENCING_QC ( READ_MERGING.out.reads )
        }
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
