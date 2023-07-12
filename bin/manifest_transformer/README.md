# manifest-transformer

This is a Python 3.8 dropin script for QUANTS that transfroms CSV/TSV manifest files.

It checks for the following:
- The manifest file is a CSV or TSV file
- Has required columns, otherwise will raise an error
- Has optional columns, otherwise will raise a warning
- Has only truthy values for required columns, otherwise will raise an error
    - Empty cells, NULL, NA are considered falsy

It will transform in the following ways:
- A new CSV/TSV is created with only the required columns and any optional columns present.
- All unspecified columns are dropped.
- The output file can be specified to be a CSV or TSV file.


For portability this script just uses the standard library.

## Usage - Quickstart

```bash
# Easy JSON parameter usage (see json parameters file section below)
manifest_transformer.py json my_params.json

# Or from the CLI
manifest_transformer.py column-names manifest.csv transformed.csv -c col_1 col_2

# If you need to the output file to be a TSV
manifest_transformer.py column-names manifest.csv transformed.tsv --output-as-tsv -c col_1 col_2

# If you want to reheader the output file
manifest_transformer.py column-names manifest.csv transformed.csv -c col_1 col_2 -r col_1=COL1 col_2=COL2

# If you want to include optional columns
manifest_transformer.py column-names manifest.csv transformed.csv -c col_1 col_2 -C col_3 col_4

# If you want to specify the order of the columns in the output file: e.g. col_2, col_1, col_3, col_5, col_4
manifest_transformer.py column-names manifest.csv transformed.csv -c col_2 col_1 -C col_3 -c col_5 -C col_4

# More advanced usage
manifest_transformer.py column-names --help
manifest_transformer.py column-indices --help

```

## JSON parameters file

```jsonc
{
    // The mode for preparing, validating, trimming, and reheadering the tabular manifest file.
    // Allowed values are "column-names" and "column-indices".
    "mode": "column-names",

    // The path to the input file, which should be a tabular manifest file (CSV/TSV).
    "input_file": "manifest.csv",

    // The path to the output file where the transformed tabular manifest file (CSV/TSV) will be written.
    "output_file": "transformed.csv",

    // The path to the file where the summary of the runtime will be written in JSON format.
    // If 'null', a summary file will be witten to the same directory as then input file.
    "summary_file": "summary.json",

    // An array listing the column order in the tabular manifest file.
    // The order is inferred from the list.
    // If the mode is "column-indices", the values in the list should be integers or strings that can be converted to integers.
    "column_order": [
        "oligo_name",
        "species",
        "assembly",
        "gene_id",
        "transcript_id",
        "src_type",
        "ref_chr",
        "ref_strand",
        "ref_start",
        "ref_end"
    ],

    // An array listing the columns that are required in the tabular manifest file.
    // If any of the required columns are missing, the script will raise an error.
    // If any of the required columns are not also in the column order list, the script will raise an error.
    // If the mode is "column-indices", the values in the list should be integers or strings that can be converted to integers.
    "required_columns": [
        "oligo_name",
        "species",
        "assembly",
        "gene_id",
        "transcript_id"
    ],

    // An array listing the columns that are optional in the tabular manifest file.
    // If any of the missing columns are missing, the script will write a warning.
    // If any of the optional columns are not also in the column order list, the script will raise an error.
    // If the mode is "column-indices", the values in the list should be integers or strings that can be converted to integers.
    "optional_columns": [
        "src_type",
        "ref_chr",
        "ref_strand",
        "ref_start",
        "ref_end"
    ],

    // A map that replaces the original column headers with new ones in the transformed tabular manifest file.
    // The order is inferred from the column order list.
    // If the mode is "column-indices", the keys in the mapping should be integers or strings that can be converted to integers.
    "reheader_mapping": {
        "oligo_name": "OLIGO_NAME",
        "species": "SPECIES",
        "assembly": "ASSEMBLY",
        "gene_id": "GENE_ID"
    },

    // A boolean that decides whether the reheader mapping should append to the head of the output file.
    // By default, it is set to false, and the reheader mapping replaces the column header row.
    // If set to true, the reheader mapping will append a row to the head of the output file.
    "reheader_append": false,

    // The delimiter of the output file. By default, the output file is a CSV, so the delimiter is a comma.
    // If you want the output file to be a TSV, you can specify the delimiter to be a tab.
    "output_file_delimiter": ",",

    // The forced delimiter of the input file.
    // By default, the script auto-detects the delimiter. You can specify a delimiter to override the auto-detected one.
    "forced_input_file_delimiter": null,

    // The forced index for the column header row in the input file.
    // By default, the script auto-detects the index. You can specify an index to override the auto-detected one.
    "forced_header_row_index": null
}
```

## Usage - with Json parameters

```
manifest_transformer.py json [-h] input_file

A script to prepare, validate, trim and re-header tabular manifest files.

positional arguments:
  input_file  Input file path to a JSON file containing parameters for the script.

optional arguments:
  -h, --help  show this help message and exit
```

## Usage - with command line parameters (using column names)

```
manifest_transformer.py column-names [-h] [--output-as-tsv] [-s SUMMARY] -c NAME [NAME ...] [-C NAME [NAME ...]] [-r NAME=NEW_NAME [NAME=NEW_NAME ...]] [--reheader-append] [--force-comma | --force-tab]
                                            [--force-header-row-index INDEX]
                                            INPUT OUTPUT

A script to prepare, validate, trim and re-header tabular manifest files.

positional arguments:
  INPUT                 Input file path to a tabular manifest file (CSV/TSV).
  OUTPUT                Output file path for the transformed tabular manifest file (CSV/TSV). You can specify a path to write to a specific file or a directory (appends input filename).

optional arguments:
  -h, --help            show this help message and exit
  --output-as-tsv       Write output file as a TSV. By default, the output file is a CSV.
  -s SUMMARY, --summary SUMMARY
                        By default, no runtime summary JSON file is written. You can specify a path to write to a specific file or a directory (appends script+timestamp filename).
  -c NAME [NAME ...], --columns NAME [NAME ...]
                        Required columns identified by column header name. Column order is inferred from this list.
  -C NAME [NAME ...], --optional-columns NAME [NAME ...]
                        Optional columns identified by column header name. Column order is inferred from this list.
  -r NAME=NEW_NAME [NAME=NEW_NAME ...], --reheader NAME=NEW_NAME [NAME=NEW_NAME ...]
                        Reheader columns. Provide a list of column names mappings to reheadder the output file. Column order is NOT inferred from this list (see required & optional column args). The format is: --reheader
                        col1=COL1 col2=COL2 col3=COL3
  --reheader-append     By default, the reheader mapping replaces the column header row. You can append the reheader mapping to the head of the output file instead, by setting this flag.
  --force-comma         Force input file delimiter to be a comma ','. By default, the script auto-detects the delimiter.
  --force-tab           Force input file delimiter to be a tab '\t'. By default, the script auto-detects the delimiter.
  --force-header-row-index INDEX
                        Force the input file parser to use this index for the column header row (1-index). By default, the script auto-detects the index of column header row, if any.
```

## Usage - with command line parameters (using column indices)

```
manifest_transformer.py column-indices [-h] [--output-as-tsv] [-s SUMMARY] -c INDEX [INDEX ...] [-C INDEX [INDEX ...]] [-r INDEX=NEW_NAME [INDEX=NEW_NAME ...]] [--reheader-append] [--force-comma | --force-tab]
                                              [--force-header-row-index INDEX]
                                              INPUT OUTPUT

A script to prepare, validate, trim and re-header tabular manifest files.

positional arguments:
  INPUT                 Input file path to a tabular manifest file (CSV/TSV).
  OUTPUT                Output file path for the transformed tabular manifest file (CSV/TSV). You can specify a path to write to a specific file or a directory (appends input filename).

optional arguments:
  -h, --help            show this help message and exit
  --output-as-tsv       Write output file as a TSV. By default, the output file is a CSV.
  -s SUMMARY, --summary SUMMARY
                        By default, no runtime summary JSON file is written. You can specify a path to write to a specific file or a directory (appends script+timestamp filename).
  -c INDEX [INDEX ...], --columns INDEX [INDEX ...]
                        Required columns identified by column index (1-index). Column order is inferred from this list.
  -C INDEX [INDEX ...], --optional-columns INDEX [INDEX ...]
                        Optional columns identified by column index (1-index). Column order is inferred from this list.
  -r INDEX=NEW_NAME [INDEX=NEW_NAME ...], --reheader INDEX=NEW_NAME [INDEX=NEW_NAME ...]
                        Reheader columns. Provide a list of column names indices to reheadder the output file. Column order is NOT inferred from this list (see required & optional column args). The format is: --reheader 1=COL1
                        2=COL2 3=COL3
  --reheader-append     By default, the reheader mapping replaces the column header row. You can append the reheader mapping to the head of the output file instead, by setting this flag.
  --force-comma         Force input file delimiter to be a comma ','. By default, the script auto-detects the delimiter.
  --force-tab           Force input file delimiter to be a tab '\t'. By default, the script auto-detects the delimiter.
  --force-header-row-index INDEX
                        Force the input file parser to use this index for the column header row (1-index). By default, the script auto-detects the index of column header row, if any.
```

## Dependencies

There are no dependencies for this script.

There are no dependencies for testing this script. The built-in `unittest` module is used.

There are optional tool-chain dependencies for development which require Poetry:
- [Poetry](https://python-poetry.org/docs/#installation)
- [pre-commit](https://pre-commit.com/#install)

## Testing
To run the tests, run `pytest` if inside a virtual environment. Run this command from the directory containing this README.

## Tool-chain setup via Poetry
Optional.

1. Install Poetry
    - Do `curl -sSL https://install.python-poetry.org | python3 -`
    - This will install Poetry to `~/.local/share/pypoetry` and add a symlink to `~/.local/bin/poetry`
    - Add `export PATH="$HOME/.local/bin:$PATH"` to your `.bashrc` or `.zshrc`
2. Create a virtual environment with Poetry
    - Do `poetry env use python3.8` to create a virtual environment with Python 3.8
        - This assumes your host has Python 3.8 installed
    - Do `poetry shell` to activate the virtual environment if you are not already in it
    - Do `poetry install --no-root` to install the dependencies
3. Install pre-commit's hooks
    - Do `pre-commit install --install-hooks` to install the pre-commit hooks
    - Do `pre-commit run --all-files` to run the pre-commit hooks on all files

## Tool-chain setup via Pip
Optional.

1. Create a virtual environment with Python 3.8
    - Do `python3.8 -m venv .venv` to create a virtual environment with Python 3.8
    - Do `source .venv/bin/activate` to activate the virtual environment
2. Install the dependencies
    - Do `pip install -r requirements.txt` to install the dependencies

Dependencies for pip can become out of date as pyproject.toml is the source of
truth for dependencies. To update the requirements.txt file, do
`poetry export -f "requirements.txt" -o "requirements.txt" --with "dev" --without-hashes`.
