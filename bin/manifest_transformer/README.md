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
# TODO
```

## Usage - Help

```
# TODO
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
