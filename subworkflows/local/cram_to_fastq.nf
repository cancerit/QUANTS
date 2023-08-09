//
// Convert CRAM to FASTQ
//

params.options = [:]
def modules = params.modules.clone()

//
// MODULE: samtools/bam2fq
//

include { SAMTOOLS_BAM2FQ } from '../../modules/local/samtools/bam2fq/main' addParams()

workflow CRAM_TO_FASTQ {
    take: 
        crams

    main: 
        ch_parsed_reads = Channel.empty()
        //
        // MODULE: Run samtools bam2fq
        //
        if (params.single_end) {
            SAMTOOLS_BAM2FQ ( crams, true )
        } else {
            SAMTOOLS_BAM2FQ ( crams, false )
        }
        ch_parsed_reads = SAMTOOLS_BAM2FQ.out.reads

    emit:
        reads = ch_parsed_reads
        versions = SAMTOOLS_BAM2FQ.out.versions
}
