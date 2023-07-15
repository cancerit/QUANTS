_ARG_INPUT = "input"
_ARG_OUTPUT = "output"
_ARG_VERBOSE = "verbose"
_ARG_FORWARD_PRIMER = "forward_primer"
_ARG_REVERSE_PRIMER = "reverse_primer"
_ARG_REVERSE_COMPLEMENT_FLAG = "reverse_complement_flag"
_ARG_NAME_HEADER = "name_header"
_ARG_NAME_INDEX = "name_index"
_ARG_SEQ_HEADER = "sequence_header"
_ARG_SEQ_INDEX = "sequence_index"
_ARG_SKIP_N_ROWS = "skip_n_rows"


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
_HELP__SKIP_N_ROWS = "Number of rows to skip in the CSV/TSV file before reading the data. By default, 1 row is skipped which assumes a header row. If you use the --name-header or --sequence-header options, you can set this to 0."
_HELP__REVERSE_COMPLEMENT_FLAG = "Reverse complement the oligo sequence."
