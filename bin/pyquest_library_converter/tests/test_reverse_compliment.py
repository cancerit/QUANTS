import unittest
from pyquest_library_converter import reverse_compliment


import unittest


class TestReverseCompliment(unittest.TestCase):
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

    def test_reverse_compliment(self):
        for test_case in self.test_cases:
            with self.subTest(f"{test_case['name']}"):
                self._assert_reverse_compliment(test_case)

    def _assert_reverse_compliment(self, test_case):
        # Given
        input_sequence = test_case["input"]
        expected_output = test_case["expected_output"]

        # When
        actual_output = reverse_compliment(input_sequence)

        # Then
        is_equal = actual_output == expected_output
        self.assertEqual(actual_output, expected_output)
        print(
            f"Input: {input_sequence} | Expected: {expected_output} | Actual: {actual_output} | Is Equal: {is_equal}"
        )


if __name__ == "__main__":
    unittest.main()
