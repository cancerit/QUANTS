#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-

import unittest
import argparse
from pathlib import Path

from pyquest_library_converter import (
    ArgsCleaner,
)

from tests import test_data


class _ArgsCleaner_Method_Tests_Mixin:
    def test_validate__with_valid_namespace(self):
        namespace = self.valid_namespace
        args_cleaner = ArgsCleaner(namespace)
        args_cleaner.validate()

    def test_validate__with_valid_namespace_with_headers(self):
        namespace = self.valid_namespace_with_headers
        args_cleaner = ArgsCleaner(namespace)
        args_cleaner.validate()

    def test_validate_codependent_input_args(self):
        namespace = self.valid_namespace
        args_cleaner = ArgsCleaner(namespace)
        args_cleaner._validate_codependent_input_args()

    def test_validate_output(self):
        namespace = self.valid_namespace
        args_cleaner = ArgsCleaner(namespace)
        args_cleaner._validate_output()

    def test_validate_forward_primer(self):
        namespace = self.valid_namespace
        args_cleaner = ArgsCleaner(namespace)
        args_cleaner._validate_forward_primer()

    def test_validate_reverse_primer(self):
        namespace = self.valid_namespace
        args_cleaner = ArgsCleaner(namespace)
        args_cleaner._validate_reverse_primer()

    def test_validate_name_index(self):
        namespace = self.valid_namespace
        args_cleaner = ArgsCleaner(namespace)

        with self.assertRaises(RuntimeError):
            args_cleaner._validate_name_index()

        # Rescue the validation by calling _validate_codependent_input_args first
        args_cleaner._validate_codependent_input_args()
        args_cleaner._validate_name_index()

    def test_validate_name_index_with_header(self):
        namespace = self.valid_namespace_with_headers
        args_cleaner = ArgsCleaner(namespace)

        with self.assertRaises(RuntimeError):
            args_cleaner._validate_name_index()

        # Rescue the validation by calling _validate_codependent_input_args first
        args_cleaner._validate_codependent_input_args()
        args_cleaner._validate_name_index()

    def test_validate_sequence_index(self):
        namespace = self.valid_namespace
        args_cleaner = ArgsCleaner(namespace)

        with self.assertRaises(RuntimeError):
            args_cleaner._validate_sequence_index()

        # Rescue the validation by calling _validate_codependent_input_args first
        args_cleaner._validate_codependent_input_args()
        args_cleaner._validate_sequence_index()

    def test_validate_sequence_index_with_header(self):
        namespace = self.valid_namespace_with_headers
        args_cleaner = ArgsCleaner(namespace)

        with self.assertRaises(RuntimeError):
            args_cleaner._validate_sequence_index()

        # Rescue the validation by calling _validate_codependent_input_args first
        args_cleaner._validate_codependent_input_args()
        args_cleaner._validate_sequence_index()

    def test_get_clean_input(self):
        # Given
        namespace = self.valid_namespace
        expected_input = self.csv_path
        args_cleaner = ArgsCleaner(namespace)

        # When
        args_cleaner.validate()
        actual_input = args_cleaner.get_clean_input()

        # Then
        self.assertEqual(expected_input, actual_input)

    def test_get_clean_skip_n_rows(self):
        # Given
        expected_skip_n_rows = self.valid_namespace.skip_n_rows
        namespace = self.valid_namespace
        args_cleaner = ArgsCleaner(namespace)

        # When
        args_cleaner.validate()
        actual_skip_n_rows = args_cleaner.get_clean_skip_n_rows()

        # Then
        self.assertEqual(expected_skip_n_rows, actual_skip_n_rows)

    def test_get_clean_skip_n_rows__with_headers(self):
        # Given
        expected_skip_n_rows = self.valid_namespace_with_headers.skip_n_rows + 1
        namespace = self.valid_namespace_with_headers
        args_cleaner = ArgsCleaner(namespace)

        # When
        args_cleaner.validate()
        actual_skip_n_rows = args_cleaner.get_clean_skip_n_rows()

        # Then
        self.assertEqual(expected_skip_n_rows, actual_skip_n_rows)

    def test_get_clean_output__with_specific_output_file_that_does_exist(self):
        # Given
        expected_output = self.csv_path
        namespace = self.valid_namespace
        namespace.output = self.csv_path
        args_cleaner = ArgsCleaner(namespace)

        # When
        args_cleaner.validate()
        actual_output = args_cleaner.get_clean_output()

        # Then
        self.assertEqual(expected_output, actual_output)

    def test_get_clean_output__with_specific_output_file_that_doesnt_exist(self):
        # Given
        expected_output = self.csv_path.parent / "foo.csv"
        namespace = self.valid_namespace
        namespace.output = expected_output
        args_cleaner = ArgsCleaner(namespace)

        # When
        args_cleaner.validate()
        actual_output = args_cleaner.get_clean_output()

        # Then
        self.assertEqual(expected_output, actual_output)

    def test_get_clean_output__with_specific_output_dir(self):
        # Given
        expected_output = self.csv_path
        namespace = self.valid_namespace
        namespace.output = self.csv_path.parent
        args_cleaner = ArgsCleaner(namespace)

        # When
        args_cleaner.validate()
        actual_output = args_cleaner.get_clean_output()

        # Then
        self.assertEqual(expected_output, actual_output)

    def test_get_clean_forward_primer(self):
        # Given
        expected_forward_primer = ""
        namespace = self.valid_namespace
        namespace.forward_primer = expected_forward_primer
        args_cleaner = ArgsCleaner(namespace)

        # When
        args_cleaner.validate()
        actual_forward_primer = args_cleaner.get_clean_forward_primer()

        # Then
        self.assertEqual(expected_forward_primer, actual_forward_primer)

    def test_get_clean_forward_primer__with_chars(self):
        # Given
        expected_forward_primer = "AATTAACG"
        namespace = self.valid_namespace
        namespace.forward_primer = expected_forward_primer
        args_cleaner = ArgsCleaner(namespace)

        # When
        args_cleaner.validate()
        actual_forward_primer = args_cleaner.get_clean_forward_primer()

        # Then
        self.assertEqual(expected_forward_primer, actual_forward_primer)

    def test_get_clean_reverse_primer(self):
        # Given
        expected_reverse_primer = ""
        namespace = self.valid_namespace
        namespace.reverse_primer = expected_reverse_primer
        args_cleaner = ArgsCleaner(namespace)

        # When
        args_cleaner.validate()
        actual_reverse_primer = args_cleaner.get_clean_reverse_primer()

        # Then
        self.assertEqual(expected_reverse_primer, actual_reverse_primer)

    def test_get_clean_reverse_primer__with_chars(self):
        # Given
        expected_reverse_primer = "AATTAACG"
        namespace = self.valid_namespace
        namespace.reverse_primer = expected_reverse_primer
        args_cleaner = ArgsCleaner(namespace)

        # When
        args_cleaner.validate()
        actual_reverse_primer = args_cleaner.get_clean_reverse_primer()

        # Then
        self.assertEqual(expected_reverse_primer, actual_reverse_primer)

    def test_get_clean_verbose(self):
        # Given
        expected_verbose = True
        namespace = self.valid_namespace
        namespace.verbose = expected_verbose
        args_cleaner = ArgsCleaner(namespace)

        # When
        args_cleaner.validate()
        actual_verbose = args_cleaner.get_clean_verbose()

        # Then
        self.assertEqual(expected_verbose, actual_verbose)

    def test_get_clean_name_index(self):
        # Given
        expected_name_index = self.oligo_seq_name_index
        namespace = self.valid_namespace
        args_cleaner = ArgsCleaner(namespace)

        # When
        args_cleaner.validate()
        actual_name_index = args_cleaner.get_clean_name_index()

        # Then
        self.assertEqual(expected_name_index, actual_name_index)

    def test_get_clean_name_index_with_header(self):
        # Given
        expected_name_index = self.oligo_seq_name_index
        namespace = self.valid_namespace_with_headers
        args_cleaner = ArgsCleaner(namespace)

        # When
        args_cleaner.validate()
        actual_name_index = args_cleaner.get_clean_name_index()

        # Then
        self.assertEqual(expected_name_index, actual_name_index)

    def test_get_clean_sequence_index(self):
        # Given
        expected_sequence_index = self.oligo_seq_index
        namespace = self.valid_namespace
        args_cleaner = ArgsCleaner(namespace)

        # When
        args_cleaner.validate()
        actual_sequence_index = args_cleaner.get_clean_sequence_index()

        # Then
        self.assertEqual(expected_sequence_index, actual_sequence_index)

    def test_get_clean_sequence_index_with_header(self):
        # Given
        expected_sequence_index = self.oligo_seq_index
        namespace = self.valid_namespace_with_headers
        args_cleaner = ArgsCleaner(namespace)

        # When
        args_cleaner.validate()
        actual_sequence_index = args_cleaner.get_clean_sequence_index()

        # Then
        self.assertEqual(expected_sequence_index, actual_sequence_index)


class _ExampleData1_Mixin:
    @classmethod
    def setUpClass(cls):
        # This method is called before each test
        cls.csv_path = test_data.get.example_data_1_csv()
        cls.oligo_seq_name_header = "oligo_name"
        cls.oligo_seq_name_index = 1  # 1-based indexing
        cls.oligo_seq_header = "mseq"
        cls.oligo_seq_index = 24  # 1-based indexing
        cls.valid_namespace = argparse.Namespace(
            input=cls.csv_path,
            output=None,
            forward_primer="",
            reverse_primer="",
            skip_n_rows=0,
            name_header=None,
            name_index=cls.oligo_seq_name_index,
            sequence_index=cls.oligo_seq_index,
            sequence_header=None,
            verbose=False,
        )
        cls.valid_namespace_with_headers = argparse.Namespace(
            input=cls.csv_path,
            output=None,
            forward_primer="",
            reverse_primer="",
            skip_n_rows=0,
            name_header=cls.oligo_seq_name_header,
            name_index=None,
            sequence_header=cls.oligo_seq_header,
            sequence_index=None,
            verbose=False,
        )


class _ExampleData2_Mixin:
    @classmethod
    def setUpClass(cls):
        # This method is called before each test
        cls.csv_path = test_data.get.example_data_2_tsv()
        if not cls.csv_path.exists():
            raise FileNotFoundError(f"Could not find {cls.csv_path}")
        cls.oligo_seq_name_header = "#id"
        cls.oligo_seq_name_index = 1  # 1-based indexing
        cls.oligo_seq_header = "sgrna_seqs"
        cls.oligo_seq_index = 3  # 1-based indexing
        cls.valid_namespace = argparse.Namespace(
            input=cls.csv_path,
            output=None,
            forward_primer="",
            reverse_primer="",
            skip_n_rows=3,
            name_header=None,
            name_index=cls.oligo_seq_name_index,
            sequence_index=cls.oligo_seq_index,
            sequence_header=None,
            verbose=False,
        )
        cls.valid_namespace_with_headers = argparse.Namespace(
            input=cls.csv_path,
            output=None,
            forward_primer="",
            reverse_primer="",
            skip_n_rows=2,
            name_header=cls.oligo_seq_name_header,
            name_index=None,
            sequence_header=cls.oligo_seq_header,
            sequence_index=None,
            verbose=False,
        )


class ExampleData1_ArgsCleaner(
    _ExampleData1_Mixin, _ArgsCleaner_Method_Tests_Mixin, unittest.TestCase
):
    pass


class ExampleData2_ArgsCleaner(
    _ExampleData2_Mixin, _ArgsCleaner_Method_Tests_Mixin, unittest.TestCase
):
    pass


if __name__ == "__main__":
    unittest.main()
