import unittest
from pyquest_library_converter import reverse_complement, reverse_complement_sequences


import unittest

EXAMPLE_CSV_HEADER = "sequence"


class TestReverseComplement(unittest.TestCase):
    def setUp(self):
        self.test_cases = [
            {
                "name": "case 1",
                "input": "AGCT",
                "expected_output": "AGCT",
            },
            {
                "name": "case 2",
                "input": "CGTA",
                "expected_output": "TACG",
            },
            {
                "name": "case 3",
                "input": "AAAGGGCCCTTT",
                "expected_output": "AAAGGGCCCTTT",
            },
            {
                "name": "case 4",
                "input": "ATCGATCG",
                "expected_output": "CGATCGAT",
            },
            {
                "name": "case 5",
                "input": "",
                "expected_output": "",
            },
            {
                "name": "case 6",
                "input": "CCCTGGGAAGGTAATTTTAGATTTC",
                "expected_output": "GAAATCTAAAATTACCTTCCCAGGG",
            },
        ]

    def test_reverse_complement(self):
        for test_case in self.test_cases:
            with self.subTest(f"{test_case['name']}"):
                self._assert_reverse_complement(
                    input_sequence=test_case["input"],
                    expected_output=test_case["expected_output"],
                )

    def _assert_reverse_complement(self, input_sequence, expected_output):
        # When
        actual_output = reverse_complement(input_sequence)

        # Then
        is_equal = actual_output == expected_output
        self.assertEqual(actual_output, expected_output)


class TestReverseComplementSequences(unittest.TestCase):
    def setUp(self):
        self.test_cases = [
            {
                "name": "case 1",
                "input": [{EXAMPLE_CSV_HEADER: "AGCT"}],
                "expected_output": [{EXAMPLE_CSV_HEADER: "AGCT"}],
            },
            {
                "name": "case 2",
                "input": [{EXAMPLE_CSV_HEADER: "CGTA"}],
                "expected_output": [{EXAMPLE_CSV_HEADER: "TACG"}],
            },
            {
                "name": "case 3",
                "input": [
                    {EXAMPLE_CSV_HEADER: "AAAGGGCCCTTT"},
                    {EXAMPLE_CSV_HEADER: "CCCTGGGAAGGTAATTTTAGATTTC"},
                ],
                "expected_output": [
                    {EXAMPLE_CSV_HEADER: "AAAGGGCCCTTT"},
                    {EXAMPLE_CSV_HEADER: "GAAATCTAAAATTACCTTCCCAGGG"},
                ],
            },
            {
                "name": "case 4",
                "input": [{EXAMPLE_CSV_HEADER: "ATCGATCG"}],
                "expected_output": [{EXAMPLE_CSV_HEADER: "CGATCGAT"}],
            },
        ]

    def test_reverse_complement_sequences(self):
        for test_case in self.test_cases:
            with self.subTest(f"{test_case['name']}"):
                self._assert_reverse_complement_sequences(
                    input_sequence=test_case["input"],
                    expected_output=test_case["expected_output"],
                )

    def _assert_reverse_complement_sequences(self, input_sequence, expected_output):
        # When
        actual_output = list(
            reverse_complement_sequences(input_sequence, header=EXAMPLE_CSV_HEADER)
        )

        # Then
        self.assertEqual(actual_output, expected_output)


if __name__ == "__main__":
    unittest.main()
