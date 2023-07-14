# -*- coding: utf-8 -*-
import typing as t

HELP__PROG_DESCRIPTION = (
    "A script to prepare, validate, trim and re-header tabular manifest files."
)
HELP__INPUT_FILE = "REQUIRED. Input file path to a tabular manifest file (CSV/TSV)."
HELP__JSON_INPUT_FILE = (
    "Input file path to a JSON file containing parameters for the script."
)

HELP__OUTPUT_FILE = "REQUIRED. Output file path for the transformed tabular manifest file (CSV/TSV). You can specify a path to write to a specific file or a directory (appends input filename)."
HELP__SUMMARY_FILE = "By default, no runtime summary JSON file is written. You can specify a path to write to a specific file or a directory (appends script+timestamp filename)."
HELP__CAST_OUTPUT_AS_TSV = (
    "Write output file as a TSV. By default, the output file is a CSV."
)
HELP__VERSION = "Show the script's version and exit."
HELP__FORCE_COMMA_DELIMITER = "Force input file delimiter to be a comma ','. By default, the script auto-detects the delimiter."
HELP__FORCE_TAB_DELIMITER = "Force input file delimiter to be a tab '\\t'. By default, the script auto-detects the delimiter."
HELP__FORCE_HEADER_ROW_INDEX = "Force the input file parser to use this index for the column header row (1-index). By default, the script auto-detects the index of column header row, if any."
HELP__REQUIRED_COLUMNS_BY_NAME = "REQUIRED columns identified by column header name. Column order is inferred from this list."
HELP__REQUIRED_COLUMNS_BY_INDEX = "REQUIRED columns identified by column index (1-index). Column order is inferred from this list."
HELP__OPTIONAL_COLUMNS_BY_NAME = "Optional columns identified by column header name. Column order is inferred from this list."
HELP__OPTIONAL_COLUMNS_BY_INDEX = "Optional columns identified by column index (1-index). Column order is inferred from this list."
HELP__REHEADER_BY_NAME = "Reheader columns. Provide a list of column names mappings to reheadder the output file. Column order is NOT inferred from this list (see required & optional column args). The format is: --reheader col1=COL1 col2=COL2 col3=COL3"
HELP__REHEADER_BY_INDEX = "Reheader columns. Provide a list of column names indices to reheadder the output file. Column order is NOT inferred from this list (see required & optional column args). The format is: --reheader 1=COL1 2=COL2 3=COL3"
HELP__REHEADER_APPEND = "By default, the reheader mapping replaces the column header row. You can append the reheader mapping to the head of the output file instead, by setting this flag."


ARG_COLUMNS = "columns"

ARGPREFIX__REQUIRED_COLUMN = "REQUIRED_COLUMN:"
ARGPREFIX__OPTIONAL_COLUMN = "OPTIONAL_COLUMN:"

SUBCOMMAND__COLUMN_NAMES = "column-names"
SUBCOMMAND__COLUMN_INDICES = "column-indices"
SUBCOMMAND__JSON = "json"


FILE_HEADER_LINE_PREFIX = "##"
NULL_VALUE__NA = "NA"
NULL_VALUE__NAN = "NAN"
NULL_VALUE__NAN_CASED = "NaN"
NULL_VALUE__N_SLASH_A = "N/A"
NULL_VALUE__NULL = "NULL"
NULL_VALUE__EMPTY = ""

DELIMITER__COMMA = ","
DELIMITER__TAB = "\t"


def allowed_delimiters() -> t.List[str]:
    return [DELIMITER__COMMA, DELIMITER__TAB].copy()


JSON_PARAM__MODE = ARG_SUBCOMMAND = "mode"
JSON_PARAM__INPUT_FILE = ARG_INPUT = "input_file"
JSON_PARAM__OUTPUT_FILE = ARG_OUTPUT = "output_file"
JSON_PARAM__SUMMARY_FILE = ARG_SUMMARY = "summary_file"
JSON_PARAM__COLUMN_ORDER = "column_order"
JSON_PARAM__REQUIRED_COLUMNS = "required_columns"
JSON_PARAM__OPTIONAL_COLUMNS = "optional_columns"
JSON_PARAM__REHEADER = ARG_REHEADER = "reheader_mapping"
JSON_PARAM__REHEADER_APPEND = ARG_REHEADER_APPEND = "reheader_append"
JSON_PARAM__OUTPUT_DELIMITER = ARG_OUTPUT_DELIMITER = "output_file_delimiter"
JSON_PARAM__FORCED_INPUT_DELIMITER = (
    ARG_FORCE_INPUT_DELIMITER
) = "forced_input_file_delimiter"
JSON_PARAM__FORCED_HEADER_ROW_INDEX = (
    ARG_FORCE_HEADER_ROW_INDEX
) = "forced_header_row_index"

JSON_SUMMARY__VERSION = "version"
JSON_SUMMARY__COMMAND = "command"
JSON_SUMMARY__INPUT_FILE = "input_file"
JSON_SUMMARY__OUTPUT_FILE = "output_file"
JSON_SUMMARY__TIMESTAMP = "timestamp"
JSON_SUMMARY__JSON_PARAMS_FILE = "json_params_file"
JSON_SUMMARY__JSON_PARAMS = "json_params"

WARN__NO_HEADERS_FOUND__STRING_MATCHING = (
    "No headers detected in file by string matching algorithm."
)
WARN__NO_HEADERS_FOUND__HEURISTIC = (
    "No headers detected in file by heuristic algorithm."
)
WARN__NO_HEADERS_FOUND__BOTH_ALGORITHMS = (
    "No headers detected in file by both string matching and heuristic algorithms."
)


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
