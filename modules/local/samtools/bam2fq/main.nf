process SAMTOOLS_BAM2FQ {
    tag "$meta.id"
    label 'process_low'

    conda (params.enable_conda ? "bioconda::samtools=1.15" : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/samtools:1.15--h1170115_1' :
        'quay.io/biocontainers/samtools:1.15--h1170115_1' }"

    input:
    tuple val(meta), path(inputbam)
    val single_end

    output:
    tuple val(meta), path("*[12].fq.gz")        , emit: reads
    tuple val(meta), path("*_other.fq.gz")      , emit: other_reads optional true
    tuple val(meta), path("*_singleton.fq.gz")  , emit: singleton_reads optional true
    path "versions.yml"                         , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.id}"

    if (single_end){
        """
        samtools \\
            bam2fq \\
            $args \\
            -@ $task.cpus \\
            $inputbam >${prefix}_1.fq

        gzip ${prefix}_1.fq

        cat <<-END_VERSIONS > versions.yml
        "${task.process}":
            samtools: \$(echo \$(samtools --version 2>&1) | sed 's/^.*samtools //; s/Using.*\$//')
        END_VERSIONS
        """
    } else {
        """
        samtools \\
            bam2fq \\
            $args \\
            -@ $task.cpus \\
            -1 ${prefix}_1.fq \\
            -2 ${prefix}_2.fq \\
            -0 ${prefix}_other.fq \\
            -s ${prefix}_singleton.fq \\
            $inputbam

        gzip ${prefix}*.fq

        cat <<-END_VERSIONS > versions.yml
        "${task.process}":
            samtools: \$(echo \$(samtools --version 2>&1) | sed 's/^.*samtools //; s/Using.*\$//')
        END_VERSIONS
        """
    }
}
