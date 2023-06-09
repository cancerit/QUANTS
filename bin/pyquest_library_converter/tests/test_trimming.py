import unittest
import typing as t

from pyquest_library_converter import trim_sequence


class TestTrimSequence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sequence_AtoI = "ABCDEFGHI"

    def test_trim_sequence_both_change_1(self):
        sequence = self.sequence_AtoI
        prefix = "A"
        suffix = "I"
        result = trim_sequence(sequence, prefix, suffix)
        self.assertEqual(result, ("BCDEFGH", True, True))

    def test_trim_sequence_both_change_2(self):
        sequence = self.sequence_AtoI
        prefix = "AB"
        suffix = "HI"
        result = trim_sequence(sequence, prefix, suffix)
        self.assertEqual(result, ("CDEFG", True, True))

    def test_trim_sequence_both_change_3(self):
        sequence = self.sequence_AtoI
        prefix = "ABC"
        suffix = "GHI"
        result = trim_sequence(sequence, prefix, suffix)
        self.assertEqual(result, ("DEF", True, True))

    def test_trim_sequence_both_change_4(self):
        sequence = self.sequence_AtoI
        prefix = "ABCD"
        suffix = "FGHI"
        result = trim_sequence(sequence, prefix, suffix)
        self.assertEqual(result, ("E", True, True))

    def test_trim_sequence_both_change_5(self):
        sequence = "ABCDEFGH"
        prefix = "ABCD"
        suffix = "EFGH"
        result = trim_sequence(sequence, prefix, suffix)
        self.assertEqual(result, ("", True, True))

    def test_trim_sequence_only_prefix(self):
        sequence = self.sequence_AtoI
        prefix = "ABC"
        suffix = "XYZ"
        result = trim_sequence(sequence, prefix, suffix)
        self.assertEqual(result, ("DEFGHI", True, False))

    def test_trim_sequence_only_suffix(self):
        sequence = self.sequence_AtoI
        prefix = "XYZ"
        suffix = "GHI"
        result = trim_sequence(sequence, prefix, suffix)
        self.assertEqual(result, ("ABCDEF", False, True))

    def test_trim_sequence_no_prefix_or_suffix(self):
        sequence = self.sequence_AtoI
        prefix = "MNO"
        suffix = "XYZ"
        result = trim_sequence(sequence, prefix, suffix)
        self.assertEqual(result, ("ABCDEFGHI", False, False))

    def test_trim_sequence_empty_string(self):
        sequence = ""
        prefix = "AB"
        suffix = "HI"
        result = trim_sequence(sequence, prefix, suffix)
        self.assertEqual(result, ("", False, False))

    def test_trim_sequence_empty_prefix_and_suffix(self):
        sequence = self.sequence_AtoI
        prefix = ""
        suffix = ""
        result = trim_sequence(sequence, prefix, suffix)
        self.assertEqual(result, ("ABCDEFGHI", False, False))

    def test_trim_sequence_overlapping_prefix_and_suffix_1(self):
        sequence = self.sequence_AtoI
        prefix = "ABCDE"
        suffix = "EFGHI"
        with self.assertRaises(NotImplementedError) as context:
            trim_sequence(sequence, prefix, suffix)
        self.assertIn("overlap", str(context.exception))

    def test_trim_sequence_overlapping_prefix_and_suffix_2(self):
        sequence = self.sequence_AtoI
        prefix = "ABCDEF"
        suffix = "DEFGHI"
        with self.assertRaises(NotImplementedError) as context:
            trim_sequence(sequence, prefix, suffix)
        self.assertIn("overlap", str(context.exception))

    def test_trim_sequence_overlapping_prefix_and_suffix_3(self):
        sequence = self.sequence_AtoI
        prefix = "ABCDEFG"
        suffix = "FGHI"
        with self.assertRaises(NotImplementedError) as context:
            trim_sequence(sequence, prefix, suffix)
        self.assertIn("overlap", str(context.exception))

    def test_trim_sequence_overlapping_prefix_and_suffix_4(self):
        sequence = self.sequence_AtoI
        prefix = "ABCD"
        suffix = "CDEFGHI"
        with self.assertRaises(NotImplementedError) as context:
            trim_sequence(sequence, prefix, suffix)
        self.assertIn("overlap", str(context.exception))


if __name__ == "__main__":
    unittest.main()
