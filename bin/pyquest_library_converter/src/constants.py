import typing as t

_ARG_INPUT = "input_file"
_ARG_OUTPUT = "output_file"
_ARG_SKIP_N_ROWS = "skip_n_rows"
_ARG_FORCE_HEADER_INDEX = "force_header_index"
_ARG_VERBOSE = "verbose"
_ARG_FORWARD_PRIMER = "forward_primer"
_ARG_REVERSE_PRIMER = "reverse_primer"
_ARG_REVERSE_COMPLEMENT_FLAG = "reverse_complement_flag"
_ARG_NAME_HEADER = "name_header"
_ARG_NAME_INDEX = "name_index"
_ARG_SEQ_HEADER = "sequence_header"
_ARG_SEQ_INDEX = "sequence_index"
_ARG_WARN_NULL_DATA = "warn_null_data"


_OUTPUT_HEADER__ID = "#id"
_OUTPUT_DELIMITER = "\t"
_OUTPUT_HEADER__NAME = "name"
_OUTPUT_HEADER__SEQUENCE = "sequence"

_TEMPLATE_GROUP_HEADER = "The column name or header in the CSV/TSV for the {}."
_TEMPLATE_GROUP_IDX = "1-indexed integer for the column index in a CSV/TSV for the {}."

_HELP__INPUT_FILE = "Input file path."
_HELP__OUTPUT_FILE = "Output file path. You can specify a path to write to a specific file or a directory (appends input filename)."
_HELP__GROUP_SEQ = _TEMPLATE_GROUP_HEADER.format("oligo sequence itself")
_HELP__GROUP_SEQ_IDX = _TEMPLATE_GROUP_IDX.format("oligo sequence itself")
_HELP__GROUP_NAME = _TEMPLATE_GROUP_HEADER.format("oligo sequence name")
_HELP__GROUP_NAME_IDX = _TEMPLATE_GROUP_IDX.format("oligo sequence name")
_HELP__VERBOSE = "Print a summary."
_HELP__FORWARD_PRIMER = (
    "DNA primer to be removed from the start of the oligo sequence if provided."
)
_HELP__REVERSE_PRIMER = (
    "DNA primer to be removed from the end of the oligo sequence if provided."
)
_HELP__SKIP_N_ROWS = "Choose how many data rows to skip before processing. Any headers or comments are always automatically skipped. If unset defaults to 0. E.g 0 (no data rows skipped), 1 (skip first row) and N (skip N data rows)."
_HELP__FORCE_HEADER_INDEX = "Force the input file parser to use this index for the column header row (1-index). By default, the script auto-detects the index of column header row, if any. If also using '--skip', the script will automatically skip all rows up to and including index before then skipping the speficied N data rows."
_HELP__REVERSE_COMPLEMENT_FLAG = "Reverse complement the oligo sequence."


FILE_HEADER_LINE_PREFIX = "##"

WARN__NO_HEADERS_FOUND__STRING_MATCHING = (
    "No headers detected in file by string matching algorithm."
)
WARN__NO_HEADERS_FOUND__HEURISTIC = (
    "No headers detected in file by heuristic algorithm."
)
WARN__NO_HEADERS_FOUND__BOTH_ALGORITHMS = (
    "No headers detected in file by both string matching and heuristic algorithms."
)
WARN_HEADER_SCAN_ABORTED = "Insufficient lines (<10) for header detection. Assumption: no header. If inaccurate, specify header with '--force-header-index' or use column names. File comments/headers will be detect as normal."

KEY_ADJUSTED_SKIP_N_ROWS = "adjusted_skip_n_rows"

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
    nulls__all_cases = _transform_to_many_cases(nulls)
    return nulls__all_cases.copy()


def _transform_to_many_cases(values: t.Iterable[str]) -> t.List[str]:
    funcs = [
        lambda x: x,  # do nothing - preserve case
        str.lower,
        str.upper,
        str.title,
    ]
    values__all_cases = [func(value) for value in values for func in funcs]
    return values__all_cases


_HELP__WARN_NULL_DATA = "Suppress errors and instead warn if null data is detected in the input file. Null data is defined as any of the following: {}".format(
    ", ".join(get_null_values())
)
