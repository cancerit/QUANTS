# -*- coding: utf-8 -*-

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
