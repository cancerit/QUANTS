def _read(rel_path):
    import os.path  # noqa: F401
    import codecs  # noqa: F401

    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), "r") as fp:
        return fp.read()


def _get_version(rel_path):
    for line in _read(rel_path).splitlines():
        if line.startswith("__version__"):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


# Do not import the package, but rather read the file directly.
# https://packaging.python.org/en/latest/guides/single-sourcing-package-version/
VERSION = _get_version("__init__.py")
