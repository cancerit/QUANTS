// Import generic module functions
include { initOptions; saveFiles; getSoftwareName } from './functions'

params.options = [:]
options        = initOptions(params.options)

process CUTADAPT {
    tag "$meta.id"
    label 'process_medium'
    publishDir "${params.outdir}",
        mode: params.publish_dir_mode,
        saveAs: { filename -> saveFiles(filename:filename, options:params.options, publish_dir:getSoftwareName(task.process), meta:meta, publish_by_meta:['id']) }

    conda (params.enable_conda ? 'bioconda::cutadapt=4.4' : null)
    container 'quay.io/biocontainers/cutadapt:4.4--py39hf95cd2a_1'
    

    input:
    tuple val(meta), path(reads)

    output:
    tuple val(meta), path('*_trimmed{,_1,_2}.fastq.gz')  , emit: reads
    tuple val(meta), path('*_untrimmed{,_1,_2}.fastq.gz'), emit: untrimmed_reads, optional: true
    tuple val(meta), path('*.log')                       , emit: log
    tuple val(meta), path('*.json')                      , emit: json
    path '*.version.txt'                                 , emit: version

    script:
    def software       = getSoftwareName(task.process)
    def prefix         = options.suffix ? "${meta.id}${options.suffix}" : "${meta.id}"
    def trimmed        = meta.single_end ? "-o ${prefix}_trimmed.fastq.gz" : "-o ${prefix}_trimmed_1.fastq.gz -p ${prefix}_trimmed_2.fastq.gz"
    def untrimmed_cmd  = meta.single_end ? "--untrimmed-output ${prefix}_untrimmed.fastq.gz" : "--untrimmed-output ${prefix}_untrimmed_1.fastq.gz --untrimmed-paired-output ${prefix}_untrimmed_2.fastq.gz"
    def untrimmed      = params.options.untrimmed ? untrimmed_cmd : ''

    """
    cutadapt \\
        --cores $task.cpus \\
        --json=${prefix}.cutadapt.json \\
        $options.args \\
        $trimmed \\
        $untrimmed \\
        $reads \\
        > ${prefix}.cutadapt.log
    echo \$(cutadapt --version) > ${software}.version.txt
    """
}
