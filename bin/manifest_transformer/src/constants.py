# -*- coding: utf-8 -*-
import typing as t

__VERSION__ = (0, 1, 0)
VERSION = ".".join(map(str, __VERSION__))

HELP__INPUT_FILE = "Input file path."
HELP__OUTPUT_FILE = "By default, input file is overwritten with the output. You can specify a path to write to a specific file or a directory (appends input filename)."
HELP__SKIP_N_ROWS = "Number of rows to skip in the CSV/TSV file before reading the data. By default, 1 row is skipped which assumes a header row. If you use the --name-header or --sequence-header options, you can set this to 0."

ARG_INPUT = "input"
ARG_OUTPUT = "output"
ARG_NAME_HEADER = "name_header"
ARG_NAME_INDEX = "name_index"
ARG_SKIP_N_ROWS = "skip_n_rows"

FILE_HEADER_LINE_PREFIX = "##"
NULL_VALUE__NA = "NA"
NULL_VALUE__NAN = "NAN"
NULL_VALUE__NAN_CASED = "NaN"
NULL_VALUE__N_SLASH_A = "N/A"
NULL_VALUE__NULL = "NULL"
NULL_VALUE__EMPTY = ""


def get_null_values() -> t.List[str]:
    nulls = [
        NULL_VALUE__EMPTY,
        NULL_VALUE__NULL,
        NULL_VALUE__NA,
        NULL_VALUE__NAN,
        NULL_VALUE__NAN_CASED,
        NULL_VALUE__N_SLASH_A,
    ]
    return nulls.copy()


def get_null_values__all_cases() -> t.List:
    nulls = get_null_values()
    nulls__all_cases = transform_to_many_cases(nulls)
    return nulls__all_cases.copy()


def transform_to_many_cases(values: t.Iterable[str]) -> t.List[str]:
    funcs = [
        lambda x: x,  # do nothing - preserve case
        str.lower,
        str.upper,
        str.title,
    ]
    values__all_cases = [func(value) for value in values for func in funcs]
    return values__all_cases
