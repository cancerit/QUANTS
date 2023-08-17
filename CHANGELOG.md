# QUANTS: Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Please add to the next release the following and then delete these lines

* Add pyquest library transformer script
* Add manifest transformer script

## 1.0.0.0 - [January 2022]

Initial release of QUANTS, created with the [nf-core](https://nf-co.re/) template.

## 1.1.0.0 - [6th February 2022]

* Rename from nf-core-sge to QUANTS
* Fix SeqPrep->QC file assignment bug
* Add initial documentation

## 1.2.0.0 [30th March 2022]

* Restructure flow of data (technical debt)
* Add subflow for read transform (rev comp, rev, comp)
* Add support for CRAM input
* Remove separate library-independent quantification
* Replace library-dependent quantification with counting unqiue reads + merge with library (pyCROQUET)

## 1.2.1.0 [4th April 2022]

* Allow sample names to start with numeric in post-processing R script

## 1.2.1.1 (9th September 2022)

* Remove meta id tag from pyCROQUET module

## 2.0.0.0 (27th June 2023)

* Replace pyCROQUET with pyQUEST version 1.0
* Add script for converting VaLiAnT meta file (or other CSV/TSV) into pyQUEST-formatted library (not integrated into workflow)
