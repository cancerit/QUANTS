import groovy.json.JsonSlurper
import groovy.json.JsonOutput

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
// removes stage suffix from the sample name
//
def trim_sample_name(sample_name) {
    sample_name
        .replaceFirst(/_raw$/, "")
        .replaceFirst(/_primer_trimmed$/, "")
        .replaceFirst(/_adapter_trimmed$/, "")
        .replaceFirst(/_merged$/, "")
        .replaceFirst(/_merged_filtered$/, "")
}

//
// each seqkit stat file prepends with two columns for sample and stage
//
def modify_seqkit_stats(meta, path, stage) {
    // TODO should be removed in the future once sample name handling in the pipeline is consistent
    def sample_name = trim_sample_name(meta.id)

    newLines = []
    file(path)
        .readLines()
        .eachWithIndex { it, i ->
            if (i == 0) {
                line = "sample" + "\t" + "stage" + "\t" + it
            } else {
                line = sample_name + "\t" + stage + "\t" + it
            }
            newLines.add(line)
        }

    return newLines.join("\n") + "\n"

def compose_cutadapt_jsons(meta, pathList) {
    def jsonSlurper = new JsonSlurper()
    def record = [:]

    for (path in pathList) {
        def stage = path.name.split("\\.")[-3]
        def object = jsonSlurper.parse(path)
        record[stage] = object
    }

    record = [(meta.id): record]
    return record
}

def collate_cutadapt_jsons(jsonList) {
    def output = [:]

    for (json in jsonList) {
        output.putAll(json)
    }

    def output_string = JsonOutput.toJson(output)
    return output_string
}
