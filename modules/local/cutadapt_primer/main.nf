// Import generic module functions
include { initOptions; saveFiles; getSoftwareName } from './functions'

params.options = [:]
options        = initOptions(params.options)

process CUTADAPT_PRIMER {
    tag "$meta.id"
    label 'process_medium'
    publishDir "${params.outdir}",
        mode: params.publish_dir_mode,
        saveAs: { filename -> saveFiles(filename:filename, options:params.options, publish_dir:getSoftwareName(task.process), meta:meta, publish_by_meta:['id']) }

    conda (params.enable_conda ? 'bioconda::cutadapt=4.4' : null)
    if (workflow.containerEngine == 'singularity' && !params.singularity_pull_docker_container) {
        container 'https://depot.galaxyproject.org/singularity/cutadapt:4.4--py39hf95cd2a_1'
    } else {
        container 'quay.io/biocontainers/cutadapt:4.4--py39hf95cd2a_1'
    }

    input:
    tuple val(meta), path(reads)

    output:
    tuple val(meta), path('*.primer_trimmed.fastq.gz'), emit: reads
    tuple val(meta), path('*.log')          , emit: log
    path '*.version.txt'                    , emit: version

    script:
    def software = getSoftwareName(task.process)
    def prefix   = options.suffix ? "${meta.id}${options.suffix}" : "${meta.id}"
    def trimmed  = meta.single_end ? "-o ${prefix}.primer_trimmed.fastq.gz" : "-o ${prefix}_1.primer_trimmed.fastq.gz -p ${prefix}_2.primer_trimmed.fastq.gz"
    """
    cutadapt \\
        --cores $task.cpus \\
        $options.args \\
        $trimmed \\
        $reads \\
        > ${prefix}.primer.cutadapt.log
    echo \$(cutadapt --version) > ${software}.version.txt
    """
}
