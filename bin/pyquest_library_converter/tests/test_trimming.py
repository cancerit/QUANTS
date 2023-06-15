import unittest
import typing as t

from pyquest_library_converter import trim_sequence, UndevelopedFeatureError


class TestTrimSequence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sequence_AtoI = "ABCDEFGHI"

    def test_trim_sequence_both_change_1(self):
        sequence = self.sequence_AtoI
        forward_primer = "A"
        reverse_primer = "I"
        result = trim_sequence(sequence, forward_primer, reverse_primer)
        self.assertEqual(result, ("BCDEFGH", True, True))

    def test_trim_sequence_both_change_2(self):
        sequence = self.sequence_AtoI
        forward_primer = "AB"
        reverse_primer = "HI"
        result = trim_sequence(sequence, forward_primer, reverse_primer)
        self.assertEqual(result, ("CDEFG", True, True))

    def test_trim_sequence_both_change_3(self):
        sequence = self.sequence_AtoI
        forward_primer = "ABC"
        reverse_primer = "GHI"
        result = trim_sequence(sequence, forward_primer, reverse_primer)
        self.assertEqual(result, ("DEF", True, True))

    def test_trim_sequence_both_change_4(self):
        sequence = self.sequence_AtoI
        forward_primer = "ABCD"
        reverse_primer = "FGHI"
        result = trim_sequence(sequence, forward_primer, reverse_primer)
        self.assertEqual(result, ("E", True, True))

    def test_trim_sequence_both_change_5(self):
        sequence = "ABCDEFGH"
        forward_primer = "ABCD"
        reverse_primer = "EFGH"
        result = trim_sequence(sequence, forward_primer, reverse_primer)
        self.assertEqual(result, ("", True, True))

    def test_trim_sequence_only_forward_primer(self):
        sequence = self.sequence_AtoI
        forward_primer = "ABC"
        reverse_primer = "XYZ"
        result = trim_sequence(sequence, forward_primer, reverse_primer)
        self.assertEqual(result, ("DEFGHI", True, False))

    def test_trim_sequence_only_reverse_primer(self):
        sequence = self.sequence_AtoI
        forward_primer = "XYZ"
        reverse_primer = "GHI"
        result = trim_sequence(sequence, forward_primer, reverse_primer)
        self.assertEqual(result, ("ABCDEF", False, True))

    def test_trim_sequence_no_forward_primer_or_reverse_primer(self):
        sequence = self.sequence_AtoI
        forward_primer = "MNO"
        reverse_primer = "XYZ"
        result = trim_sequence(sequence, forward_primer, reverse_primer)
        self.assertEqual(result, ("ABCDEFGHI", False, False))

    def test_trim_sequence_empty_string(self):
        sequence = ""
        forward_primer = "AB"
        reverse_primer = "HI"
        result = trim_sequence(sequence, forward_primer, reverse_primer)
        self.assertEqual(result, ("", False, False))

    def test_trim_sequence_empty_forward_primer_and_reverse_primer(self):
        sequence = self.sequence_AtoI
        forward_primer = ""
        reverse_primer = ""
        result = trim_sequence(sequence, forward_primer, reverse_primer)
        self.assertEqual(result, ("ABCDEFGHI", False, False))

    def test_trim_sequence_overlapping_forward_primer_and_reverse_primer_1(self):
        sequence = self.sequence_AtoI
        forward_primer = "ABCDE"
        reverse_primer = "EFGHI"
        with self.assertRaises(UndevelopedFeatureError) as context:
            trim_sequence(sequence, forward_primer, reverse_primer)
        self.assertIn("overlap", str(context.exception))

    def test_trim_sequence_overlapping_forward_primer_and_reverse_primer_2(self):
        sequence = self.sequence_AtoI
        forward_primer = "ABCDEF"
        reverse_primer = "DEFGHI"
        with self.assertRaises(UndevelopedFeatureError) as context:
            trim_sequence(sequence, forward_primer, reverse_primer)
        self.assertIn("overlap", str(context.exception))

    def test_trim_sequence_overlapping_forward_primer_and_reverse_primer_3(self):
        sequence = self.sequence_AtoI
        forward_primer = "ABCDEFG"
        reverse_primer = "FGHI"
        with self.assertRaises(UndevelopedFeatureError) as context:
            trim_sequence(sequence, forward_primer, reverse_primer)
        self.assertIn("overlap", str(context.exception))

    def test_trim_sequence_overlapping_forward_primer_and_reverse_primer_4(self):
        sequence = self.sequence_AtoI
        forward_primer = "ABCD"
        reverse_primer = "CDEFGHI"
        with self.assertRaises(UndevelopedFeatureError) as context:
            trim_sequence(sequence, forward_primer, reverse_primer)
        self.assertIn("overlap", str(context.exception))


if __name__ == "__main__":
    unittest.main()
