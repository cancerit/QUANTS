import groovy.json.JsonSlurper

//
// takes cutadapt json filenames and stages for the sample and creates a record
//
def compose_cutadapt_jsons(meta, pathList, stageList) {
    def jsonSlurper = new JsonSlurper()
    def record = [:]

    [pathList, stageList].transpose().each() { path, stage ->
        def object = jsonSlurper.parse(path)

        object["read_counts"]["read1_with_adapter_percent"] = 100 * object["read_counts"]["read1_with_adapter"] / object["read_counts"]["input"]
        if (object["read_counts"]["read2_with_adapter"]){
            object["read_counts"]["read2_with_adapter_percent"] = 100 * object["read_counts"]["read2_with_adapter"] / object["read_counts"]["input"]
        } else {
            object["read_counts"]["read2_with_adapter_percent"] = null
        }

        record[stage] = object
    }

    record = [(meta.id): record]
    return record
}
