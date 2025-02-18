# Test datasets and files

end-to-end tests for the quants pipeline using the nf-test framework.

Having retrieved data and placed it in the ref and sample-data folders, tests can be run with `nf-test test tests/test[#].main.nf.test`

To confirm that you've retrieved the correct data, and named it appropriately if necessary, run `diff -q <(md5sum tests/sample-data/*) tests/sample-data-checksums` and `diff -q <(md5sum tests/ref/*) tests/ref-checksums`. If the commands return nothing (exit code 0), the data is as expected. Note that if you do not run this command from the top level directory of the repo, it will fail, as md5sum will output relative paths along with checksums.

## Test parameters

| Test | Source | FASTQ or CRAM | SE or PE| RevComp | Read merging | Adapter trimming | Primer Trimming | Read filtering | Read modification | QC | Quantification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `test1.main.nf.test` | Trimmed | FASTQ | SE | Y | N | N | N | N | Y | N | Y |
| `test2.main.nf.test` | Trimmed | FASTQ | SE | Y | N | N | N | N | Y | Y | Y |
| `test3.main.nf.test` | Raw | FASTQ | SE | Y | N | Y | Y | N | Y | Y | Y |
| `test4.main.nf.test` | Raw | CRAM | SE | Y | N | Y | Y | N | Y | Y | Y |
| `test5.main.nf.test` | Raw | FASTQ | PE | N | Y (SeqPrep) | Y | Y | N | N | Y | Y |
| `test6.main.nf.test` | Raw | FASTQ | PE | N | Y (Flash2) | Y | Y | Y | N | Y | Y |
| `test7.main.nf.test` | Raw | FASTQ | PE | N | Y (SeqPrep) | Y | Y | Y | N | Y | Y |
| `test8.main.nf.test` | Raw | FASTQ | PE | N | Y (Flash2) | Y | Y | Y | N | Y | Y |
| `test9.main.nf.test` | Raw | FASTQ | PE | N | Y (Flash2) | Y | Y | Y | N | Y | Y |
| `test10.main.nf.test` | Raw | FASTQ | SE | N | N | Y | Y | Y | N | Y | Y |
| `test11.main.nf.test` | Raw | FASTQ | SE | N | N | Y | Y | N | Y | Y | Y |
| `test12.main.nf.test` | Raw | CRAM | SE | N | N | Y | Y | N | Y | Y | Y |
