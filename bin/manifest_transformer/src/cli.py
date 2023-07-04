import sys


def display_error(error: Exception, prefix: str = "Error: ") -> None:
    """
    Prints an error message to stderr, prefixed with "Error: ".
    """
    error_msg = f"{prefix}{error}"
    print(error_msg, file=sys.stderr)
