import groovy.json.JsonOutput

// Import generic module functions
include { compose_cutadapt_jsons } from './functions'

process COLLATE_CUTADAPT_JSONS {
    label 'process_low'
    publishDir "${params.outdir}/cutadapt", mode: params.publish_dir_mode

    input:
    val inputList  // list of tuples [meta, [list of jsons], [list of stages]]

    output:
    path 'cutadapt.json', emit: json

    exec:
    String filename = [task.workDir, 'cutadapt.json'].join(File.separator)

    new File(filename).withWriter { writer ->
        writer.writeLine('{')

        inputList.eachWithIndex { e, index ->
            def (meta, pathList, stageList) = e
            def record = compose_cutadapt_jsons(meta, pathList, stageList)
            String record_string = JsonOutput.toJson(record)
            String comma = index + 1 < inputList.size() ? ',' : ''
            String output_string = '  ' + record_string[1..-2] + comma
            writer.writeLine(output_string)
        }

        writer.writeLine('}')
    }
}
