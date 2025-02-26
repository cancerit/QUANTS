process SEQTK_SAMPLE {
    tag "$meta.id"
    label 'process_single'

    container "quay.io/biocontainers/seqtk:1.4--he4a0461_1"

    input:
    tuple val(meta), path(reads)

    output:
    tuple val(meta), path("*.fq.gz")   , emit: reads
    path "versions.yml"                , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def prefix = task.ext.prefix ?: "${meta.id}"
    def sample_size = params.downsampling_size
    def seed = params.downsampling_seed
    if ( !sample_size ) {
        error "SEQTK/SAMPLE must have a sample_size value included"
    }
    """
    seqtk \\
        sample \\
        -s$seed \\
        "$reads" \\
        $sample_size \\
        | gzip --no-name > ${prefix}_downsampled.fq.gz

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        seqtk: \$(echo \$(seqtk 2>&1) | sed 's/^.*Version: //; s/ .*\$//')
    END_VERSIONS
    """

    stub:
    def prefix = task.ext.prefix ?: "${meta.id}"

    """
    echo "" | gzip > ${prefix}.fq.gz

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        seqtk: \$(echo \$(seqtk 2>&1) | sed 's/^.*Version: //; s/ .*\$//')
    END_VERSIONS
    """

}
