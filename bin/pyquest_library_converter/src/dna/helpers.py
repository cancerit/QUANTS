import typing as t

from src.exceptions import UndevelopedFeatureError

if t.TYPE_CHECKING:
    from src.report import Report


def find_invalid_chars_in_dna_sequence(
    sequence: str, allow_n: bool, allow_lower_case: bool
) -> t.Tuple[t.List[str], t.Tuple[str]]:
    """
    Find invalid characters in a DNA sequence, returning the invalid characters and the allowed characters.

    :param sequence: The sequence to validate.
    :param allow_n: Whether to allow the character 'N' in the sequence.
    :param allow_lower_case: Whether to allow lower case characters in the sequence.

    """
    allowed_chars = set("ACGT")
    if allow_n:
        allowed_chars.add("N")
    if allow_lower_case:
        allowed_chars.update("acgt")
    if allow_lower_case and allow_n:
        allowed_chars.update("n")
    invalid_chars = find_invalid_chars_in_string(sequence, allowed_chars)

    return invalid_chars, tuple(sorted(allowed_chars))


def find_invalid_chars_in_string(
    string: str, allowed_chars: t.Iterable[str]
) -> t.List[str]:
    """
    Find invalid characters in a string, returning the invalid characters.

    :param string: The string to validate.
    :param allowed_chars: The allowed characters.

    """
    string_set = set(string)
    invalid_chars = string_set - set(allowed_chars)
    return sorted(invalid_chars)


def reverse_complement_sequences(
    dict_rows: t.Iterator[t.Dict[str, str]],
    header: str,
) -> t.Iterable[t.Dict[str, str]]:
    """
    Update each row to have the reverse complement of the sequence.

    Header corresponds to the CSV header for the sequence column.
    """
    for dict_row in dict_rows:
        sequence = dict_row[header]
        reversed_sequence = reverse_complement(sequence)
        dict_row[header] = reversed_sequence
        yield dict_row


def reverse_complement(sequence: str) -> str:
    """
    Reverse complement the sequence (DNA only).
    """
    # Make the translation map
    trans = str.maketrans("ACGT", "TGCA")
    # Translate the sequence and reverse it
    return sequence.translate(trans)[::-1]


def upper_case_sequences(
    dict_rows: t.Iterator[t.Dict[str, str]], sequence_header: str
) -> t.Iterable[t.Dict[str, str]]:
    """
    Upper case the sequences.

    Yield dictionaries of index, name, sequence values from each row, where keys are the new headers.

    Header corresponds to the CSV header for the sequence column.
    """
    for dict_row in dict_rows:
        # Upper case the sequence and update the dictionary
        sequence = dict_row[sequence_header]
        dict_row[sequence_header] = sequence.upper()
        yield dict_row


def lower_case_sequences(
    dict_rows: t.Iterator[t.Dict[str, str]], sequence_header: str
) -> t.Iterable[t.Dict[str, str]]:
    """
    Lower case the sequences.

    Yield dictionaries of index, name, sequence values from each row, where keys are the new headers.

    Header corresponds to the CSV header for the sequence column.
    """
    for dict_row in dict_rows:
        # Lower case the sequence and update the dictionary
        sequence = dict_row[sequence_header]
        dict_row[sequence_header] = sequence.lower()
        yield dict_row


def trim_sequences(
    dict_rows: t.Iterator[t.Dict[str, str]],
    forward_primer: str,
    reverse_primer: str,
    report: "Report",
    sequence_header: str,
    id_header: str,
) -> t.Iterable[t.Dict[str, str]]:
    """
    Trim the forward and reverse primer from the sequence.

    Yield dictionaries of index, name, sequence values from each row, where keys are the new headers.

    Header corresponds to the CSV header for the sequence column.
    """
    for dict_row in dict_rows:
        # Trim the sequence and update the dictionary
        sequence = dict_row[sequence_header]
        (
            trimmed_sequence,
            has_trimmed_forward_primer,
            has_trimmed_reverse_primer,
        ) = trim_sequence(sequence, forward_primer, reverse_primer)
        dict_row[sequence_header] = trimmed_sequence

        # Update the report
        row_id = dict_row[id_header]
        report.add_row(row_id, has_trimmed_forward_primer, has_trimmed_reverse_primer)
        yield dict_row


def trim_sequence(
    sequence: str, forward_primer: str, reverse_primer: str
) -> t.Tuple[str, bool, bool]:
    """
    Trim the forward and reverse primer from the sequence.

    Return the trimmed sequence and whether the forward and reverse primer were trimmed.
    """
    start_index: int = 0
    # None is the end of the string, and works for slicing
    end_index: t.Optional[int] = None
    has_trimmed_forward_primer = False
    has_trimmed_reverse_primer = False

    err_msg = f"The forward and reverse primer overlap in the sequence (no handling in code yet): {forward_primer=}, {reverse_primer=}, {sequence=}"

    forward_primer_exists = len(forward_primer) and sequence.startswith(forward_primer)
    reverse_primer_exists = len(reverse_primer) and sequence.endswith(reverse_primer)

    is_overlapping = False

    if forward_primer_exists:
        temp_index = len(forward_primer)
        reverse_primer_exists_after_trimming = sequence[temp_index:].endswith(
            reverse_primer
        )
        is_overlapping = (
            reverse_primer_exists and not reverse_primer_exists_after_trimming
        )
        start_index = temp_index
        has_trimmed_forward_primer = True

    if reverse_primer_exists:
        temp_index = len(sequence) - len(reverse_primer)
        forward_primer_exists_after_trimming = sequence[:temp_index].startswith(
            forward_primer
        )
        is_overlapping = (
            forward_primer_exists and not forward_primer_exists_after_trimming
        )
        end_index = temp_index
        has_trimmed_reverse_primer = True

    if is_overlapping:
        raise UndevelopedFeatureError(err_msg)

    trimmed_sequence = sequence[start_index:end_index]

    return (trimmed_sequence, has_trimmed_forward_primer, has_trimmed_reverse_primer)


def noop_sequences(
    dict_rows: t.Iterator[t.Dict[str, str]]
) -> t.Iterable[t.Dict[str, str]]:
    """
    Pass through the rows without changing them.
    """
    for dict_row in dict_rows:
        yield dict_row
