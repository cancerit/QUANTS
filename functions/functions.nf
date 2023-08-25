//
// takes channel and SEQUENCING_QC workflow object
// extracts seqkit_stats output channel, combines it with workflow name and appends to input channel
//
def add_seqkit_stats(channel, workflow) {
    return channel.mix(
        workflow.out.seqkit_stats.combine(
            [workflow.name.split(':').last()]
        )
    )
}

//
// each seqkit stat file prepends with two columns for sample and stage
//
def modify_seqkit_stats(meta, path, stage) {
    newLines = []
    file(path)
        .readLines()
        .eachWithIndex { it, i ->
            if (i == 0) {
                line = "sample" + "\t" + "stage" + "\t" + it
            } else {
                line = meta.id + "\t" + stage + "\t" + it
            }
            newLines.add(line)
        }
    return newLines.join("\n") + "\n"
}
