import unittest
import typing as t
import string
import pytest

from pyquest_library_converter import (
    reverse_complement,
    PrimerScanner,
    find_invalid_chars_in_dna_sequence,
)

EXAMPLE_CSV_HEADER = "sequence"

EXAMPLE_FWD_PRIMER = "AATGATACGGCGACCACCGATCCTG"
EXAMPLE_FWD_PRIMER_2 = "GACCACCGATCCTGAATGATACGGC"
EXAMPLE_REV_PRIMER = "TGGCTCGTATGCCGTCTTCTGCTTG"
EXAMPLE_REV_PRIMER_2 = "GTCTTCTGCTTGTGGCTCGTATGCC"
EXAMPLE_FWD_PRIMER_REVCOMP = reverse_complement(EXAMPLE_FWD_PRIMER)
EXAMPLE_REV_PRIMER_REVCOMP = reverse_complement(EXAMPLE_REV_PRIMER)
EXAMPLE_MIDDLE_OLIGO_1 = (
    "CGCCTTCTCTCCTCCTCCTCCACACTCCAGGCTGGACCTGTACCGAGCCTCGGGTAAATTTGAGCTTCTTGATAGA"
    "ATTCTTCCCAAACTCCGAGCAACCAACCACAAAGTGCTGCTGTTCTGTCAGATGACTTCCCTCATGACCATCATGG"
    "AAGATTACTTTGCGTATCGCGGCTTTAAATACCTCAGGCTTGATGGTGAGTATGAGCCAGTGAGGCGTTTCTTACA"
    "GGGTTTTGTTGTTG"
)
EXAMPLE_MIDDLE_OLIGO_2 = (
    "CGCCTTCTCTCCTCCTCCTCCACACTCCAGGCTGGACCTGTACCGAGCCTCGGGTAAATTTGAGCTTCTTGATAGA"
    "ATTCTTCCCAAACTCCGAGCAACCAACCACAAAGTGCTGCTGTTCTGTCAGATGACTTCCCTCATGACCATCATGG"
    "GGGTTTTGTTGTTG"
)
EXAMPLE_MIDDLE_OLIGO_3 = (
    "CGCCTTCTCTCCTCCTCCTCCACACTCCAGGCTGGACCTGTACCGAGCCTCGGGTAAATTTGAGCTTCTTGATAGA"
)
TEMPLATE_OLIGO = "{fwd}{middle}{rev}"


TYPICAL_CASES = [
    {
        "name": "just fwd primer",
        "forward_primer": EXAMPLE_FWD_PRIMER,
        "reverse_primer": "",
        "oligos": [
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER,
                middle=EXAMPLE_MIDDLE_OLIGO_1,
                rev=EXAMPLE_REV_PRIMER,
            ),
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER,
                middle=EXAMPLE_MIDDLE_OLIGO_2,
                rev=EXAMPLE_REV_PRIMER,
            ),
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER,
                middle=EXAMPLE_MIDDLE_OLIGO_3,
                rev=EXAMPLE_REV_PRIMER,
            ),
        ],
        "expected_forward_primer": EXAMPLE_FWD_PRIMER,
        "expected_reverse_primer": "",
    },
    {
        "name": "just rev primer",
        "forward_primer": "",
        "reverse_primer": EXAMPLE_REV_PRIMER,
        "oligos": [
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER,
                middle=EXAMPLE_MIDDLE_OLIGO_1,
                rev=EXAMPLE_REV_PRIMER,
            ),
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER,
                middle=EXAMPLE_MIDDLE_OLIGO_2,
                rev=EXAMPLE_REV_PRIMER,
            ),
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER,
                middle=EXAMPLE_MIDDLE_OLIGO_3,
                rev=EXAMPLE_REV_PRIMER,
            ),
        ],
        "expected_forward_primer": "",
        "expected_reverse_primer": EXAMPLE_REV_PRIMER,
    },
    {
        "name": "both fwd+rev primer",
        "forward_primer": EXAMPLE_FWD_PRIMER,
        "reverse_primer": EXAMPLE_REV_PRIMER,
        "oligos": [
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER,
                middle=EXAMPLE_MIDDLE_OLIGO_1,
                rev=EXAMPLE_REV_PRIMER,
            ),
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER,
                middle=EXAMPLE_MIDDLE_OLIGO_2,
                rev=EXAMPLE_REV_PRIMER,
            ),
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER,
                middle=EXAMPLE_MIDDLE_OLIGO_3,
                rev=EXAMPLE_REV_PRIMER,
            ),
        ],
        "expected_forward_primer": EXAMPLE_FWD_PRIMER,
        "expected_reverse_primer": EXAMPLE_REV_PRIMER,
    },
]

NON_MATCHING_PRIMERS_CASES = [
    {
        "name": "just fwd primer but there is not match",
        "forward_primer": EXAMPLE_FWD_PRIMER_2,
        "reverse_primer": "",
        "oligos": [
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER,
                middle=EXAMPLE_MIDDLE_OLIGO_1,
                rev=EXAMPLE_REV_PRIMER,
            ),
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER,
                middle=EXAMPLE_MIDDLE_OLIGO_2,
                rev=EXAMPLE_REV_PRIMER,
            ),
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER,
                middle=EXAMPLE_MIDDLE_OLIGO_3,
                rev=EXAMPLE_REV_PRIMER,
            ),
        ],
        "expected_forward_primer": "",
        "expected_reverse_primer": "",
    },
    {
        "name": "just rev primer but there is not match",
        "forward_primer": "",
        "reverse_primer": EXAMPLE_REV_PRIMER_2,
        "oligos": [
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER,
                middle=EXAMPLE_MIDDLE_OLIGO_1,
                rev=EXAMPLE_REV_PRIMER,
            ),
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER,
                middle=EXAMPLE_MIDDLE_OLIGO_2,
                rev=EXAMPLE_REV_PRIMER,
            ),
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER,
                middle=EXAMPLE_MIDDLE_OLIGO_3,
                rev=EXAMPLE_REV_PRIMER,
            ),
        ],
        "expected_forward_primer": "",
        "expected_reverse_primer": "",
    },
    {
        "name": "wd+rev primer but there is not match",
        "forward_primer": EXAMPLE_FWD_PRIMER_2,
        "reverse_primer": EXAMPLE_REV_PRIMER_2,
        "oligos": [
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER,
                middle=EXAMPLE_MIDDLE_OLIGO_1,
                rev=EXAMPLE_REV_PRIMER,
            ),
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER,
                middle=EXAMPLE_MIDDLE_OLIGO_2,
                rev=EXAMPLE_REV_PRIMER,
            ),
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER,
                middle=EXAMPLE_MIDDLE_OLIGO_3,
                rev=EXAMPLE_REV_PRIMER,
            ),
        ],
        "expected_forward_primer": "",
        "expected_reverse_primer": "",
    },
]

MATCHING_BUT_REVCOMP_CASES = [
    {
        "name": "just fwd-revcomp primer",
        "forward_primer": EXAMPLE_FWD_PRIMER_REVCOMP,
        "reverse_primer": "",
        "oligos": [
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER_REVCOMP,
                middle=EXAMPLE_MIDDLE_OLIGO_1,
                rev=EXAMPLE_REV_PRIMER,
            ),
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER_REVCOMP,
                middle=EXAMPLE_MIDDLE_OLIGO_2,
                rev=EXAMPLE_REV_PRIMER,
            ),
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER_REVCOMP,
                middle=EXAMPLE_MIDDLE_OLIGO_3,
                rev=EXAMPLE_REV_PRIMER,
            ),
        ],
        "expected_forward_primer": EXAMPLE_FWD_PRIMER_REVCOMP,
        "expected_reverse_primer": "",
    },
    {
        "name": "just rev-revcomp primer",
        "forward_primer": "",
        "reverse_primer": EXAMPLE_REV_PRIMER_REVCOMP,
        "oligos": [
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER_REVCOMP,
                middle=EXAMPLE_MIDDLE_OLIGO_1,
                rev=EXAMPLE_REV_PRIMER_REVCOMP,
            ),
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER_REVCOMP,
                middle=EXAMPLE_MIDDLE_OLIGO_2,
                rev=EXAMPLE_REV_PRIMER_REVCOMP,
            ),
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER_REVCOMP,
                middle=EXAMPLE_MIDDLE_OLIGO_3,
                rev=EXAMPLE_REV_PRIMER_REVCOMP,
            ),
        ],
        "expected_forward_primer": "",
        "expected_reverse_primer": EXAMPLE_REV_PRIMER_REVCOMP,
    },
    {
        "name": "just fwd-revcomp+rev-revcomp primer",
        "forward_primer": EXAMPLE_FWD_PRIMER_REVCOMP,
        "reverse_primer": EXAMPLE_REV_PRIMER_REVCOMP,
        "oligos": [
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER_REVCOMP,
                middle=EXAMPLE_MIDDLE_OLIGO_1,
                rev=EXAMPLE_REV_PRIMER_REVCOMP,
            ),
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER_REVCOMP,
                middle=EXAMPLE_MIDDLE_OLIGO_2,
                rev=EXAMPLE_REV_PRIMER_REVCOMP,
            ),
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER_REVCOMP,
                middle=EXAMPLE_MIDDLE_OLIGO_3,
                rev=EXAMPLE_REV_PRIMER_REVCOMP,
            ),
        ],
        "expected_forward_primer": EXAMPLE_FWD_PRIMER_REVCOMP,
        "expected_reverse_primer": EXAMPLE_REV_PRIMER_REVCOMP,
    },
]


MATCHING_BUT_REVCOMP_CASES = [
    {
        "name": "just fwd-revcomp primer",
        "forward_primer": EXAMPLE_FWD_PRIMER_REVCOMP,
        "reverse_primer": "",
        "oligos": [
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER_REVCOMP,
                middle=EXAMPLE_MIDDLE_OLIGO_1,
                rev=EXAMPLE_REV_PRIMER,
            ),
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER_REVCOMP,
                middle=EXAMPLE_MIDDLE_OLIGO_2,
                rev=EXAMPLE_REV_PRIMER,
            ),
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER_REVCOMP,
                middle=EXAMPLE_MIDDLE_OLIGO_3,
                rev=EXAMPLE_REV_PRIMER,
            ),
        ],
        "expected_forward_primer": EXAMPLE_FWD_PRIMER_REVCOMP,
        "expected_reverse_primer": "",
    },
    {
        "name": "just rev-revcomp primer",
        "forward_primer": "",
        "reverse_primer": EXAMPLE_REV_PRIMER_REVCOMP,
        "oligos": [
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER_REVCOMP,
                middle=EXAMPLE_MIDDLE_OLIGO_1,
                rev=EXAMPLE_REV_PRIMER_REVCOMP,
            ),
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER_REVCOMP,
                middle=EXAMPLE_MIDDLE_OLIGO_2,
                rev=EXAMPLE_REV_PRIMER_REVCOMP,
            ),
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER_REVCOMP,
                middle=EXAMPLE_MIDDLE_OLIGO_3,
                rev=EXAMPLE_REV_PRIMER_REVCOMP,
            ),
        ],
        "expected_forward_primer": "",
        "expected_reverse_primer": EXAMPLE_REV_PRIMER_REVCOMP,
    },
    {
        "name": "just fwd-revcomp+rev-revcomp primer",
        "forward_primer": EXAMPLE_FWD_PRIMER_REVCOMP,
        "reverse_primer": EXAMPLE_REV_PRIMER_REVCOMP,
        "oligos": [
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER_REVCOMP,
                middle=EXAMPLE_MIDDLE_OLIGO_1,
                rev=EXAMPLE_REV_PRIMER_REVCOMP,
            ),
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER_REVCOMP,
                middle=EXAMPLE_MIDDLE_OLIGO_2,
                rev=EXAMPLE_REV_PRIMER_REVCOMP,
            ),
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER_REVCOMP,
                middle=EXAMPLE_MIDDLE_OLIGO_3,
                rev=EXAMPLE_REV_PRIMER_REVCOMP,
            ),
        ],
        "expected_forward_primer": EXAMPLE_FWD_PRIMER_REVCOMP,
        "expected_reverse_primer": EXAMPLE_REV_PRIMER_REVCOMP,
    },
]


MIXTURE_ORGINAL_AND_REVCOMP_CASES = [
    {
        "name": "input: fwd primer-orignal, expected: fwd primer-original, oligos: 2 fwd-original, 1 fwd-revcomp",
        "forward_primer": EXAMPLE_FWD_PRIMER,
        "reverse_primer": "",
        "oligos": [
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER,
                middle=EXAMPLE_MIDDLE_OLIGO_1,
                rev=EXAMPLE_REV_PRIMER,
            ),
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER,
                middle=EXAMPLE_MIDDLE_OLIGO_2,
                rev=EXAMPLE_REV_PRIMER,
            ),
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER_REVCOMP,
                middle=EXAMPLE_MIDDLE_OLIGO_3,
                rev=EXAMPLE_REV_PRIMER,
            ),
        ],
        "expected_forward_primer": EXAMPLE_FWD_PRIMER,
        "expected_reverse_primer": "",
    },
    {
        "name": "input: fwd primer-original, expected: fwd primer-original, oligos: 1 fwd-original, 2 fwd-revcomp",
        "forward_primer": EXAMPLE_FWD_PRIMER,
        "reverse_primer": "",
        "oligos": [
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER,
                middle=EXAMPLE_MIDDLE_OLIGO_1,
                rev=EXAMPLE_REV_PRIMER,
            ),
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER_REVCOMP,
                middle=EXAMPLE_MIDDLE_OLIGO_2,
                rev=EXAMPLE_REV_PRIMER,
            ),
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER_REVCOMP,
                middle=EXAMPLE_MIDDLE_OLIGO_3,
                rev=EXAMPLE_REV_PRIMER,
            ),
        ],
        "expected_forward_primer": EXAMPLE_FWD_PRIMER_REVCOMP,
        "expected_reverse_primer": "",
    },
    {
        "name": "input: rev primer-orignal, expected: rev primer-original, oligos: 2 rev-original, 1 rev-revcomp",
        "forward_primer": "",
        "reverse_primer": EXAMPLE_REV_PRIMER,
        "oligos": [
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER,
                middle=EXAMPLE_MIDDLE_OLIGO_1,
                rev=EXAMPLE_REV_PRIMER,
            ),
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER,
                middle=EXAMPLE_MIDDLE_OLIGO_2,
                rev=EXAMPLE_REV_PRIMER,
            ),
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER,
                middle=EXAMPLE_MIDDLE_OLIGO_3,
                rev=EXAMPLE_REV_PRIMER_REVCOMP,
            ),
        ],
        "expected_forward_primer": "",
        "expected_reverse_primer": EXAMPLE_REV_PRIMER,
    },
    {
        "name": "input: rev primer-orignal, expected: rev primer-original, oligos: 1 rev-original, 2 rev-revcomp",
        "forward_primer": "",
        "reverse_primer": EXAMPLE_REV_PRIMER,
        "oligos": [
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER,
                middle=EXAMPLE_MIDDLE_OLIGO_1,
                rev=EXAMPLE_REV_PRIMER,
            ),
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER,
                middle=EXAMPLE_MIDDLE_OLIGO_2,
                rev=EXAMPLE_REV_PRIMER_REVCOMP,
            ),
            TEMPLATE_OLIGO.format(
                fwd=EXAMPLE_FWD_PRIMER,
                middle=EXAMPLE_MIDDLE_OLIGO_3,
                rev=EXAMPLE_REV_PRIMER_REVCOMP,
            ),
        ],
        "expected_forward_primer": "",
        "expected_reverse_primer": EXAMPLE_REV_PRIMER_REVCOMP,
    },
]


class TestPrimerScanner(unittest.TestCase):
    def setUp(self):
        self.test_cases = (
            TYPICAL_CASES
            + NON_MATCHING_PRIMERS_CASES
            + MIXTURE_ORGINAL_AND_REVCOMP_CASES
        )

    def test_primer_scanner__find_primers(self):
        for test_case in self.test_cases:
            with self.subTest(f"{test_case['name']}"):
                self._assert_primer_scanner__find_primers(
                    forward_primer=test_case["forward_primer"],
                    reverse_primer=test_case["reverse_primer"],
                    oligos=test_case["oligos"],
                    expected_forward_primer=test_case["expected_forward_primer"],
                    expected_reverse_primer=test_case["expected_reverse_primer"],
                )

    def _assert_primer_scanner__find_primers(
        self,
        forward_primer: str,
        reverse_primer: str,
        oligos: t.List[str],
        expected_forward_primer: str,
        expected_reverse_primer: str,
    ):
        # Given
        scanner = PrimerScanner(
            forward_primer=forward_primer, reverse_primer=reverse_primer
        )

        # When
        scanner.scan_all(oligos)

        actual_forward_primer = scanner.predict_forward_primer()
        actual_reverse_primer = scanner.predict_reverse_primer()

        # Then
        self.assertEqual(actual_forward_primer, expected_forward_primer)
        self.assertEqual(actual_reverse_primer, expected_reverse_primer)


PRIMER_TEST_CASES = (
    [
        # sequence, expected, expected_allow_n, expected_allow_lower, allow_both
        # simple positive cases
        ("A", [], [], [], []),
        ("C", [], [], [], []),
        ("G", [], [], [], []),
        ("T", [], [], [], []),
        # simple negative cases
        ("", [], [], [], []),
        ("N", ["N"], [], ["N"], []),
        ("a", ["a"], ["a"], [], []),
        ("c", ["c"], ["c"], [], []),
        ("g", ["g"], ["g"], [], []),
        ("t", ["t"], ["t"], [], []),
        ("n", ["n"], ["n"], ["n"], []),
    ]
    + [
        # simple negative cases: lowers
        (char, [char], [char], [char], [char])
        for char in string.ascii_lowercase
        if char not in "atcgn"
    ]
    + [
        # simple negative cases: uppers
        (char, [char], [char], [char], [char])
        for char in string.ascii_uppercase
        if char not in "ATCGN"
    ]
    + [
        # simple negative cases: digits + symbols
        (char, [char], [char], [char], [char])
        for char in string.digits + string.punctuation
    ]
    + [
        # complex postive cases
        ("ATCG", [], [], [], []),
        ("ATCGATCG", [], [], [], []),
        ("ATCGATCGATCGATCG", [], [], [], []),
        ("CATGAGGGAAGTCATCTGACAGAACAGCAGCACTTTGTGGTTGGTTGCTCGGAGTTTGG", [], [], [], []),
        # complex negative cases: illegal characters
        ("ATCGN", ["N"], [], ["N"], []),
        ("atcg", ["a", "c", "g", "t"], ["a", "c", "g", "t"], [], []),
        ("ATCGatcg", ["a", "c", "g", "t"], ["a", "c", "g", "t"], [], []),
        ("ATCGATCGatcg", ["a", "c", "g", "t"], ["a", "c", "g", "t"], [], []),
        ("AZCG", ["Z"], ["Z"], ["Z"], ["Z"]),
        ("ATCGAACB", ["B"], ["B"], ["B"], ["B"]),
        (
            "CATGAGGGAAGTCANCTGACAGA3CAGCAGCACTTTZTGGTTGGTTNNNCGGAGTTTGG",
            ["3", "N", "Z"],
            ["3", "Z"],
            ["3", "N", "Z"],
            ["3", "Z"],
        ),
        (
            "CATGAGGGAAGTCATCTGACAGA3CAGCAGCACTTTGTGGTTGGTTGCTCGGAGTTTGG",
            ["3"],
            ["3"],
            ["3"],
            ["3"],
        ),
        (
            "CATGAGGGAAGTCATCTGACAGA?CAGCAGCACTTTGTGGTTGGTTGCTCGGAGTTTGG",
            ["?"],
            ["?"],
            ["?"],
            ["?"],
        ),
        (
            "CATGAGGGAAGTCATCTGACAGAzCAGCAGCACTTTGTGGTTGGTTGCTCGGAGTTTGG",
            ["z"],
            ["z"],
            ["z"],
            ["z"],
        ),
    ]
)


@pytest.mark.parametrize(
    "sequence, expected, expected_allow_n, expected_allow_lower, expected_allow_both",
    PRIMER_TEST_CASES,
)
def test_find_invalid_chars_in_dna_sequence(
    sequence, expected, expected_allow_n, expected_allow_lower, expected_allow_both
):
    # Given
    expected_allowed = tuple(sorted("ACGT"))
    expected_allowed_n = tuple(sorted("ACGTN"))
    expected_allow_lower = tuple(sorted("ACGTacgt"))
    expected_allow_both = tuple(sorted("ACGTNacgtn"))

    # When
    actual, actual_allowed = find_invalid_chars_in_dna_sequence(
        sequence, allow_n=False, allow_lower_case=False
    )
    actual_allow_n, actual_allowed_n = find_invalid_chars_in_dna_sequence(
        sequence, allow_n=True, allow_lower_case=False
    )
    actual_allow_lower, actual_allow_lower = find_invalid_chars_in_dna_sequence(
        sequence, allow_n=False, allow_lower_case=True
    )
    actual_allow_both, actual_allow_both = find_invalid_chars_in_dna_sequence(
        sequence, allow_n=True, allow_lower_case=True
    )

    # Then
    assert actual_allowed == expected_allowed
    assert actual_allowed_n == expected_allowed_n
    assert actual_allow_lower == expected_allow_lower
    assert actual_allow_both == expected_allow_both
    assert actual == expected
    assert actual_allow_n == expected_allow_n
    assert actual_allow_lower == expected_allow_lower
    assert actual_allow_both == expected_allow_both
