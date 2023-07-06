import toml

from src import version


def test_version_between_pyproject_and_package_is_the_same():
    pyproject = toml.load("pyproject.toml")
    assert version.VERSION == pyproject["tool"]["poetry"]["version"]
