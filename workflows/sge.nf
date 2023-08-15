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

// Check input_type
def input_type_options = ['fastq', 'cram']
if ( input_type_options.contains( params.input_type ) == false ) {
    printErr("input_type must be one of: " + input_type_options.join(',') + ".")
    exit 1
}

// Check adapter and primer trimming software (if set)
def read_trimming_software = ['cutadapt']
if (params.adapter_trimming) {
    if ( read_trimming_software.contains( params.adapter_trimming ) == false ) {
        printErr("If adapter_trimming is set, software must be one of: " + read_trimming_software.join(',') + ".")
        exit 1
    }
}
if (params.primer_trimming) {
    if ( read_trimming_software.contains( params.primer_trimming ) == false ) {
        printErr("If primer_trimming is set, software must be one of: " + read_trimming_software.join(',') + ".")
        exit 1
    }
}

// Check adapter and primer trimming QC (if read trimming set)
if (params.adapter_trimming_qc && !params.adapter_trimming) {
    printErr("Adapter trimming QC cannot be run when adapter_trimming is set to false.")
    exit 1
}
if (params.primer_trimming_qc && !params.primer_trimming) {
    printErr("Primer trimming QC cannot be run when primer_trimming is set to false.")
    exit 1
}

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

// Check transformation (if set)
def read_transformation_options = ['reverse', 'complement', 'reverse_complement']
if (params.read_transform) {
    if ( read_transformation_options.contains( params.read_transform ) == false ) {
        printErr("If read_transform is set, value must be one of: " + read_transformation_options.join(',') + ".")
        exit 1
    }
}

// Check read fitering is valid (if set)
if (params.read_filtering && (!params.single_end && !params.read_merging)) {
    printErr("Read filtering cannot be run when data is paired end or single end, but read merging is set to false.")
    exit 1
}

// Check read filtering QC (if read filtering set)
if (params.read_filtering_qc && !params.read_filtering) {
    printErr("Read filtering QC cannot be run when read_filtering is set to false.")
    exit 1
}

// Check quantification is set if library is provided
if (params.oligo_library && !params.quantification) {
    printErr("If a library file is provided by oligo_library, quantification must be set to true.")
    exit 1
}

// Check quantification software (if set)
def quantification_software = ['pyquest']
if (params.quantification) {
    if ( quantification_software.contains( params.quantification ) == false ) {
        printErr("If quantification is set, software must be one of: " + quantification_software.join(',') + ".")
        exit 1
    }
}

// Check that read merging is enabled if quantification is set and data is PE
if (((params.quantification || params.quantification ) && !params.single_end) && !params.read_merging) {
    printErr("Read merging must be enabled when quantification is requested and input is paired end.")
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

// MultiQC
def multiqc_options   = modules['multiqc']
multiqc_options.args += params.multiqc_title ? Utils.joinModuleArgs(["--title \"$params.multiqc_title\""]) : ''

//
// MODULE: Local to the pipeline
//
// editorconfig-checker-disable
include { GET_SOFTWARE_VERSIONS } from '../modules/local/get_software_versions' addParams( options: [publish_files : ['tsv':'']] )
include { INPUT_CHECK_FASTQ;
          INPUT_CHECK_CRAM } from '../subworkflows/local/input_check' addParams( options: [:] )
include { CRAM_TO_FASTQ } from '../subworkflows/local/cram_to_fastq' addParams( options: [:] )
include { READ_TRANSFORM } from '../subworkflows/local/read_transform' addParams( options: [:] )
include { READ_MERGING } from '../subworkflows/local/read_merging' addParams( options: [:] )
// TO DO: Both trimming steps use cutadapt - once stable, look at combining / abstraction to avoid duplication here
include { ADAPTER_TRIMMING } from '../subworkflows/local/adapter_trimming' addParams( options: [:] )
include { PRIMER_TRIMMING } from '../subworkflows/local/primer_trimming' addParams( options: [:] )
include { READ_FILTERING } from '../subworkflows/local/read_filtering' addParams( options: [:] )
include { QUANTIFICATION } from '../subworkflows/local/quantification' addParams( options: [:] )
include { SEQUENCING_QC as RAW_SEQUENCING_QC;
          SEQUENCING_QC as MERGED_SEQUENCING_QC;
          SEQUENCING_QC as ADAPTER_TRIMMED_SEQUENCING_QC;
          SEQUENCING_QC as PRIMER_TRIMMED_SEQUENCING_QC;
          SEQUENCING_QC as FILTERED_SEQUENCING_QC
        } from '../subworkflows/local/sequencing_qc' addParams( options: [:] )
// editorconfig-checker-disable

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
    // Set up empty channels
    ch_software_versions = Channel.empty()

    if (params.input_type == 'cram') {
        //
        // SUBWORKFLOW: Read in samplesheet, validate and stage input files
        //
        INPUT_CHECK_CRAM ( ch_input )

        //
        // SUBWORKFLOW: Convert CRAM to FASTQ
        //
        CRAM_TO_FASTQ(INPUT_CHECK_CRAM.out.crams)
        ch_raw_reads = CRAM_TO_FASTQ.out.reads
        ch_adapter_trim = ch_raw_reads
        ch_software_versions = ch_software_versions.mix(CRAM_TO_FASTQ.out.versions)
    } else {
        //
        // SUBWORKFLOW: Read in samplesheet, validate and stage input files
        //
        INPUT_CHECK_FASTQ ( ch_input )
        ch_raw_reads = INPUT_CHECK_FASTQ.out.reads
        ch_adapter_trim = INPUT_CHECK_FASTQ.out.reads
    }

    //
    // SUBWORKFLOW: Run FASTQC on raw reads
    //
    if (params.raw_sequencing_qc) {
        ch_raw_read_qc = ch_raw_reads.map{it -> [[id: it[0].id + '_raw', single_end: it[0].single_end], it[1]]}
        RAW_SEQUENCING_QC ( ch_raw_read_qc )
        ch_software_versions = ch_software_versions.mix(RAW_SEQUENCING_QC.out.fastqc_version, RAW_SEQUENCING_QC.out.seqkit_version)
    }

    //
    // SUBWORKFLOW: Run adapter trimming
    //
    if (params.adapter_trimming) {
        // Run adapter trimming
        ADAPTER_TRIMMING ( ch_adapter_trim )
        ch_software_versions = ch_software_versions.mix(ADAPTER_TRIMMING.out.versions)
        //
        //SUBWORKFLOW: Run FASTQC on adapter trimmed reads
        //
        if (params.adapter_trimming_qc) {
            ch_adapter_trimming_qc = ADAPTER_TRIMMING.out.reads.map{it -> [[id: it[0].id + '_adapter_trimmed', single_end: it[0].single_end], it[1]]}
            ADAPTER_TRIMMED_SEQUENCING_QC ( ch_adapter_trimming_qc )
            ch_software_versions = ch_software_versions.mix(ADAPTER_TRIMMED_SEQUENCING_QC.out.fastqc_version, ADAPTER_TRIMMED_SEQUENCING_QC.out.seqkit_version)
        }
        // Send to next stage
        ch_primer_trim = ADAPTER_TRIMMING.out.reads
    } else {
        ch_primer_trim = ch_adapter_trim
    }

    //
    // SUBWORKFLOW: Run primer trimming
    //
    if (params.primer_trimming) {
        // Run primer trimming
        PRIMER_TRIMMING ( ch_primer_trim )
        ch_software_versions = ch_software_versions.mix(PRIMER_TRIMMING.out.versions)
        //
        //SUBWORKFLOW: Run FASTQC on primer trimmed reads
        //
        if (params.primer_trimming_qc) {
            ch_primer_trimming_qc = PRIMER_TRIMMING.out.reads.map{it -> [[id: it[0].id + '_primer_trimmed', single_end: it[0].single_end], it[1]]}
            PRIMER_TRIMMED_SEQUENCING_QC ( ch_primer_trimming_qc )
            ch_software_versions = ch_software_versions.mix(PRIMER_TRIMMED_SEQUENCING_QC.out.fastqc_version, PRIMER_TRIMMED_SEQUENCING_QC.out.seqkit_version)
        }
        // Send to next stage
        ch_read_merge = PRIMER_TRIMMING.out.reads
    } else {
        ch_read_merge = ch_primer_trim
    }

    //
    // SUBWORKFLOW: Run read merging (PE only)
    //
    if (params.read_merging) {
        READ_MERGING ( ch_read_merge )
        ch_read_transform = READ_MERGING.out.reads.map{it -> [[id: it[0].id + '_merged', single_end: true], it[1]]}
        ch_software_versions = ch_software_versions.mix(READ_MERGING.out.versions)

        //
        // SUBWORKFLOW: Run FASTQC on merged reads
        //
        if (params.read_merging_qc) {
            ch_merged_read_qc = ch_read_transform
            MERGED_SEQUENCING_QC ( ch_merged_read_qc )
            ch_software_versions = ch_software_versions.mix(MERGED_SEQUENCING_QC.out.fastqc_version, MERGED_SEQUENCING_QC.out.seqkit_version)
        }
    } else {
        ch_read_transform = ch_read_merge
    }

    //
    // SUBWORKFLOW: Read transformation (reverse, complement or reverse_complement)
    // Data must be SE by this stage
    //
    if (params.read_transform ) {
        READ_TRANSFORM ( ch_read_transform )
        ch_read_filter = READ_TRANSFORM.out.reads
        ch_software_versions = ch_software_versions.mix(READ_TRANSFORM.out.versions)
    } else {
        ch_read_filter = ch_read_transform
    }

    //
    // SUBWORKFLOW: Run read filtering (data must be SE by this stage)
    //

    if (params.read_filtering) {
        READ_FILTERING ( ch_read_filter )
        ch_reads_to_analyse = READ_FILTERING.out.reads
        ch_software_versions = ch_software_versions.mix(READ_FILTERING.out.versions)

        //
        // SUBWORKFLOW: Run FASTQC on filtered reads
        //
        if (params.read_filtering_qc) {
            ch_filtered_read_qc = READ_FILTERING.out.reads.map{it -> [[id: it[0].id + '_filtered', single_end: true], it[1]]}
            FILTERED_SEQUENCING_QC ( ch_filtered_read_qc )
            ch_software_versions = ch_software_versions.mix(FILTERED_SEQUENCING_QC.out.fastqc_version, FILTERED_SEQUENCING_QC.out.seqkit_version)
        }
    } else {
        ch_reads_to_analyse = ch_read_filter
    }

    //
    // SUBWORKFLOW: Run quantification
    // Returns the number of reads assigned to each guide from a user-defined library
    //
    if (params.quantification) {
        QUANTIFICATION ( ch_reads_to_analyse )
        ch_software_versions = ch_software_versions.mix(QUANTIFICATION.out.versions)
    }

    //
    // MODULE: Pipeline reporting
    //
    ch_software_versions
        .map { it -> if (it) [ it.baseName, it ] }
        .groupTuple()
        .map { it[1][0] }
        .flatten()
        .set { ch_software_versions }

    GET_SOFTWARE_VERSIONS (
        ch_software_versions.map { it }.collect()
    )

    //
    // MODULE: MultiQC
    //
    if (params.raw_sequencing_qc || params.adapter_trimming_qc || params.primer_trimming_qc || params.read_merging_qc) {
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
        if (params.adapter_trimming_qc) {
            ch_multiqc_files = ch_multiqc_files.mix(ADAPTER_TRIMMED_SEQUENCING_QC.out.fastqc_zip.collect{it[1]}.ifEmpty([]))
            ch_multiqc_files = ch_multiqc_files.mix(ADAPTER_TRIMMING.out.stats.collect{it[1]}.ifEmpty([]))
        }
        if (params.primer_trimming_qc) {
            ch_multiqc_files = ch_multiqc_files.mix(PRIMER_TRIMMED_SEQUENCING_QC.out.fastqc_zip.collect{it[1]}.ifEmpty([]))
            ch_multiqc_files = ch_multiqc_files.mix(PRIMER_TRIMMING.out.stats.collect{it[1]}.ifEmpty([]))
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
