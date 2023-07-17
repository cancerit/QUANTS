# pyquest-library-transformer

This is a Python 3.8 dropin script for Pyquest that transfroms TSV files into a Pyquest compatible format for NextFlow.

The script allows you to select the two oligo name and sequence columns and return a new TSV with three columns:
- row number (1-indexed)
- oligo name
- oligo sequence
with the option to have the 5' and 3' ends of the oligo sequence trimmed.

For portability this script just uses the standard library.

## Usage - Quickstart

```bash
IN="example_data_1.in.csv"
OUT="example_data_1.out.csv"
FORWARD="AATGATACGGCGACCACCGATCCTGCGCCTTCTCTCCTC"
REVERSE="CATCATGGAAGATTACTTTGCGTATCGCGGCTTTAAATACCTCAGGCTTGATGGTGAGTATGAGCCAGTGAGGCGTTTCTTACAGGGTTTTGTTGTTGTGGCTCGTATGCCGTCTTCTGCTTG"

# Example usage with headers
./pyquest_library_converter.py $IN  -o $OUT -n "oligo_name" -s "mseq" --skip 0 -v

# Example usage with column indices
./pyquest_library_converter.py $IN  -o $OUT -N 1 -S 24 -v

# Example usage where the output csv has reverse complements for the output sequence
./pyquest_library_converter.py $IN  -o $OUT -N 1 -S 24 -v --revcomp

# Example usage with a reverse that needs to be removed
./pyquest_library_converter.py $IN  -o $OUT -N 1 -S 24 --reverse $REVERSE -v

# Example usage with a forward that needs to be removed
./pyquest_library_converter.py $IN  -o $OUT -N 1 -S 24 --forward $FORWARD -v

# Example usage with both a forward and reverse that needs to be removed
./pyquest_library_converter.py $IN  -o $OUT -N 1 -S 24 --forward $FORWARD --reverse $REVERSE -v
```

## Usage - Auto-detect primer
```bash
IN="example_data_2.in.csv"
OUT="example_data_2.out.csv"
FORWARD="ATTCACGTTATGCTGTCCAATCTCT"  # Exists at the start of oligo
REVERSE="CCCTGGGAAGGTAATTTTAGATTTC"  # Exists at the end of oligo, but as reverse compliment

./pyquest_library_converter.py $IN -o $OUT -n "oligo_name" -s "mseq" --skip 0 -v --forward $FORWARD --reverse $REVERSE
```
The script will try to identify whether to treat each primer as a typical sequence of as a reverse complement sequence.

In this case the script will print a message similar to:
```
Total seqeunces processed: 1
Forward primer found 1 times in 1 sequences scanned.
Forward primer reverse complement found 0 times in 1 sequences scanned.
Reverse primer found 0 times in 1 sequences scanned
Reverse primer reverse complement found 1 times in 1 sequences scanned.
Chosen forward primer is the same as the given forward primer: 'ATTCACGTTATGCTGTCCAATCTCT'.
Chosen reverse primer is the reverse complement of the given reverse primer: 'GAAATCTAAAATTACCTTCCCAGGG'.
Forward primer trimmed in 1 of 1 sequences.
Reverse primer trimmed in 1 of 1 sequences.
Forward + reverse primer trimmed in 1 out of 1 sequences
```
## Usage - Output

```bash
# You can over-write the input file
./pyquest_library_converter.py $IN -N 1 -S 24

# You can specify the output file as a directory (as long as it exists)
OUT_DIR="/out"
./pyquest_library_converter.py $IN -o $OUT -N 1 -S 24

# The --skip option allows you to skip the first N rows
./pyquest_library_converter.py $IN -o $OUT -N 1 -S 24 --skip 3 # Great for skipping comment and hearder rows
```

## Usage - Help

```
Transforms oligo sequences to a format that can be used in PyQuest

positional arguments:
  input                 Input file path.

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        By default, input file is overwritten with the output. You can specify a path to write to a specific file or a
                        directory (appends input filename).
  -v, --verbose         Print a summary.
  --forward FORWARD     DNA primer to be removed from the start of the oligo sequence if provided.
  --reverse REVERSE     DNA primer to be removed from the end of the oligo sequence if provided.
  --skip SKIP_N_ROWS    Number of rows to skip in the CSV/TSV file before reading the data. By default, 1 row is skipped which assumes
                        a header row. If you use the --name-header or --sequence-header options, you can set this to 0.
  -n NAME_HEADER, --name-header NAME_HEADER
                        The column name or header in the CSV/TSV for the oligo sequence name.
  -N NAME_INDEX, --name-index NAME_INDEX
                        1-indexed integer for the column index in a CSV/TSV for the oligo sequence name.
  -s SEQUENCE_HEADER, --sequence-header SEQUENCE_HEADER
                        The column name or header in the CSV/TSV for the oligo sequence itself.
  -S SEQUENCE_INDEX, --sequence-index SEQUENCE_INDEX
                        1-indexed integer for the column index in a CSV/TSV for the oligo sequence itself.
```

## Dependencies

There are no dependencies for this script.

There are no dependencies for testing this script. The built-in `unittest` module is used.

There are optional tool-chain dependencies for development which require Poetry:
- [Poetry](https://python-poetry.org/docs/#installation)
- [pre-commit](https://pre-commit.com/#install)

## Testing
To run the tests, run `python -m unittest` if inside a virtual environment or `python3.8 -m unittest` if not. Run this command from the directory containing this README.

**OR if the optional tool-chain dependencies are installed**

To run the tests, run `pytest`. Run this command from the directory containing this README.



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
    - Do `pip install -r requirements.dev-only.txt` to install the dependencies

Dependencies for pip can become out of date as pyproject.toml is the source of
truth for dependencies. To update the requirements.dev-only.txt file, do
`poetry export -f "requirements.dev-only.txt" -o "requirements.dev-only.txt" --with "dev" --without-hashes`.
