#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import typing as t
import sys

from functools import partial
from pathlib import Path
import tempfile
import shutil

from src.csv.csv_helper import CSVHelper
from src.csv.filter import filter_rows
from src.csv.write import write_rows
from src.report import Report
from src.dna.primer_scanner import PrimerScanner
from src.dna import helpers as dna_helpers
from src.args.args_parsing import get_argparser
from src.args.args_cleaner import ArgsCleaner
from src.exceptions import (
    ValidationError,
    UndevelopedFeatureError,
)
from src.enums import OligoCasing
from src import constants as const
from src.cli import display_error


if sys.version_info < (3, 8):
    raise RuntimeError("This script requires Python 3.8 or later")


def main(
    input_file: t.Union[str, Path],
    output_file: t.Union[str, Path],
    skip_n_rows: int,
    verbose: bool,
    forward_primer: str,
    reverse_primer: str,
    name_index: int,
    sequence_index: int,
    reverse_complement_flag: bool,
):
    report = Report()
    input_file = Path(input_file)
    output_file = Path(output_file)
    output_headers = [
        const._OUTPUT_HEADER__ID,
        const._OUTPUT_HEADER__NAME,
        const._OUTPUT_HEADER__SEQUENCE,
    ]

    # Scan the file once to auto-detect the best primers
    csv_helper = CSVHelper(input_file, skip_n_rows=skip_n_rows)
    with csv_helper.get_csv_reader() as csv_reader:
        primer_scanner = PrimerScanner(
            forward_primer=forward_primer, reverse_primer=reverse_primer
        )
        dict_rows = filter_rows(
            csv_reader, name_index=name_index, sequence_index=sequence_index
        )
        oligos_to_scan = [row[const._OUTPUT_HEADER__SEQUENCE] for row in dict_rows]
        primer_scanner.scan_all(oligos_to_scan)
        detected_forward_primer = primer_scanner.predict_forward_primer()
        detected_reverse_primer = primer_scanner.predict_reverse_primer()
        report.add_scanning_summary(primer_scanner.summary())
        primer_scanner.raise_errors()
        oligo_case = primer_scanner.get_oligos_case()

    # Prepare closured functions for writing the output file
    _reverse_complement_sequences_closure = partial(
        dna_helpers.reverse_complement_sequences,
        header=const._OUTPUT_HEADER__SEQUENCE,
    )
    trim_sequences_closure = partial(
        dna_helpers.trim_sequences,
        sequence_header=const._OUTPUT_HEADER__SEQUENCE,
        id_header=const._OUTPUT_HEADER__ID,
        forward_primer=detected_forward_primer,
        reverse_primer=detected_reverse_primer,
    )
    conditionally_reverse_complement_sequences = (
        _reverse_complement_sequences_closure
        if reverse_complement_flag
        else dna_helpers.noop_sequences
    )
    _closure_upper_case_sequences = partial(
        dna_helpers.upper_case_sequences, sequence_header=const._OUTPUT_HEADER__SEQUENCE
    )
    conditionally_upper_case_sequences = (
        _closure_upper_case_sequences
        if oligo_case == OligoCasing.LOWER
        else dna_helpers.noop_sequences
    )
    _closure_lower_case_sequences = partial(
        dna_helpers.lower_case_sequences, sequence_header=const._OUTPUT_HEADER__SEQUENCE
    )
    conditionally_lower_case_sequences = (
        _closure_lower_case_sequences
        if oligo_case == OligoCasing.LOWER
        else dna_helpers.noop_sequences
    )

    # Prepare a temporary file to write to
    with tempfile.NamedTemporaryFile(delete=True) as temp_handle:
        temp_file = Path(temp_handle.name)

        # Read the input file and write to a temporary file
        csv_helper = CSVHelper(input_file, skip_n_rows=skip_n_rows)
        with csv_helper.get_csv_reader() as csv_reader:
            dict_rows = filter_rows(
                csv_reader, name_index=name_index, sequence_index=sequence_index
            )
            dict_rows = conditionally_upper_case_sequences(dict_rows)
            dict_rows = trim_sequences_closure(dict_rows, report=report)
            dict_rows = conditionally_reverse_complement_sequences(dict_rows)
            dict_rows = conditionally_lower_case_sequences(dict_rows)
            write_rows(dict_rows, output_file=temp_file, headers=output_headers)

        # Copy the temporary file to the output file
        shutil.copy(temp_file, output_file)

    # At this point, the temporary file has been deleted
    if verbose:
        print("PROCESSING REPORT")
        print(report.summary())
    return


if __name__ == "__main__":  # noqa: C901
    if sys.version_info < (3, 8):
        display_error("Python 3.8 or newer is required.")
        sys.exit(1)
    parser = get_argparser()
    namespace = parser.parse_args()
    args_cleaner = ArgsCleaner(namespace)
    try:
        # Validate the arguments
        args_cleaner.validate()
        if args_cleaner.get_clean_verbose():
            print("ARGUMENT REPORT")
            print(args_cleaner.summary() + "\n")
        # Run the main function
        main(**args_cleaner.to_clean_dict())
    except ValidationError as err:
        display_error("Error: Argument validation!", err)
        sys.exit(1)
    except (UndevelopedFeatureError, NotImplementedError) as err:
        display_error("Error: Not implemented feature!", err)
        sys.exit(1)
