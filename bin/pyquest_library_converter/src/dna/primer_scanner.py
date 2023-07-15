import typing as t

from src.dna.helpers import (
    reverse_complement,
    find_invalid_chars_in_dna_sequence,
    find_invalid_chars_in_string,
)
from src.enums import OligoCasing
from src.exceptions import ValidationError, UndevelopedFeatureError


class PrimerScanner:
    """
    PrimmerScanner is a class that scans a CSV file, using the given forward and
    reverse primers and identifies whether to use the orginal or reverse
    complement of each primer for downstream usage, e.g. trimming.
    """

    def __init__(self, forward_primer: str, reverse_primer: str) -> None:
        self._given_forward_primer = forward_primer.upper()
        self._given_reverse_primer = reverse_primer.upper()
        self._given_forward_primer_revcomp = reverse_complement(forward_primer)
        self._given_reverse_primer_revcomp = reverse_complement(reverse_primer)
        self.__init_counters()
        self._has_scanned = False
        _, allowed_chars = find_invalid_chars_in_dna_sequence(
            "", allow_n=True, allow_lower_case=True
        )
        self._allowed_chars = allowed_chars

    def __init_counter_dict(self, original: str, revcomp: str) -> t.Dict[str, int]:
        return {original: 0, revcomp: 0}

    def __init_counters(self):
        self._forward_primer_counter: t.Dict[str, int] = self.__init_counter_dict(
            self._given_forward_primer, self._given_forward_primer_revcomp
        )
        self._reverse_primer_counter: t.Dict[str, int] = self.__init_counter_dict(
            self._given_reverse_primer, self._given_reverse_primer_revcomp
        )
        self._total_oligos_scanned = 0
        self._oligo_casing_set: t.Set[OligoCasing] = set()
        self._invalid_chars_set: t.Set[str] = set()

    def summary(self) -> t.List[str]:
        """
        Get a summary of the scanning results.
        """
        self._assert_has_scanned()
        total = self._total_oligos_scanned
        forward_cnt = self._forward_primer_counter[self._given_forward_primer]
        forward_revcomp_cnt = self._forward_primer_counter[
            self._given_forward_primer_revcomp
        ]
        reverse_cnt = self._reverse_primer_counter[self._given_reverse_primer]
        reverse_revcomp_cnt = self._reverse_primer_counter[
            self._given_reverse_primer_revcomp
        ]
        predicted_fwd_primer = self.predict_forward_primer()
        predicted_rev_primer = self.predict_reverse_primer()
        # If a user speficies a forward primer as an empty string, then we we do not need to document the search for it
        natural_empty_fwd_primer = (
            predicted_fwd_primer == ""
            and predicted_fwd_primer == self._given_forward_primer_revcomp
        )
        natural_empty_rev_primer = (
            predicted_rev_primer == ""
            and predicted_rev_primer == self._given_reverse_primer_revcomp
        )
        search_fwd_lines = [
            f"Forward primer found {forward_cnt} times in {total} sequences scanned.",
            f"Forward primer reverse complement found {forward_revcomp_cnt} times in {total} sequences scanned.",
        ]
        search_rev_lines = [
            f"Reverse primer found {reverse_cnt} times in {total} sequences scanned",
            f"Reverse primer reverse complement found {reverse_revcomp_cnt} times in {total} sequences scanned.",
        ]
        search_fwd_lines = (
            ["Forward primer search was unnecessary because it is an empty string."]
            if natural_empty_fwd_primer
            else search_fwd_lines
        )
        search_rev_lines = (
            ["Reverse primer search was unnecessary because it is an empty string."]
            if natural_empty_rev_primer
            else search_rev_lines
        )

        oligo_cases = ", ".join(case.value for case in self._oligo_casing_set)
        has_error_case = OligoCasing.NONE in self._oligo_casing_set
        single_case_error = " (error)" if has_error_case else ""
        oligo_caseing_lines = (
            [f"Oligo sequences casing is not uniform: {oligo_cases} (error)"]
            if len(self._oligo_casing_set) > 1
            else [
                f"Oligo sequences has a single case: {oligo_cases}{single_case_error}"
            ]
        )

        oligo_invalid_chars = ", ".join(self._invalid_chars_set)
        oligo_invalid_char_lines = (
            [
                f"Oligo sequences contains invalid characters: {oligo_invalid_chars} (error)"
            ]
            if len(self._invalid_chars_set) > 0
            else ["Oligo sequences contain no invalid characters."]
        )

        chosen_fwd_line = self._summary_chosen_primer(
            predicted_primer=predicted_fwd_primer,
            primer_name="forward",
            given_original_primer=self._given_forward_primer,
            given_revcomp_primer=self._given_forward_primer_revcomp,
            original_count=forward_cnt,
            revcomp_count=forward_revcomp_cnt,
        )

        chosen_rev_line = self._summary_chosen_primer(
            predicted_primer=predicted_rev_primer,
            primer_name="reverse",
            given_original_primer=self._given_reverse_primer,
            given_revcomp_primer=self._given_reverse_primer_revcomp,
            original_count=reverse_cnt,
            revcomp_count=reverse_revcomp_cnt,
        )
        lines = (
            [f"Total sequences processed: {total}"]
            + oligo_caseing_lines
            + oligo_invalid_char_lines
            + search_fwd_lines
            + search_rev_lines
            + [chosen_fwd_line, chosen_rev_line]
        )
        return lines

    def _summary_chosen_primer(
        self,
        predicted_primer: str,
        given_original_primer: str,
        given_revcomp_primer: str,
        primer_name: str,
        original_count: int,
        revcomp_count: str,
    ) -> str:
        if not predicted_primer and original_count == 0 and revcomp_count == 0:
            chosen_line = f"WARNING: Chosen {primer_name} primer is an empty string because the forward primer was not found in any of the sequences"
        elif not predicted_primer and not given_original_primer:
            chosen_line = f"Chosen {primer_name} primer is an empty string"
        elif predicted_primer == given_original_primer:
            chosen_line = f"Chosen {primer_name} primer is the same as the given {primer_name} primer"
        elif predicted_primer == given_revcomp_primer:
            chosen_line = f"Chosen {primer_name} primer is the reverse complement of the given {primer_name} primer"
        else:
            raise NotImplementedError("Unhandled case - please report this as a bug")
        return chosen_line + f": {predicted_primer!r}."

    def scan_all(self, oligos: t.List[str]) -> None:
        """
        Scan all oligos and count the number of times the given forward and reverse primers or their respective reverse complements are found.
        """
        self.__init_counters()
        for oligo in oligos:
            self._scan(oligo)
            self._total_oligos_scanned += 1
        if self._total_oligos_scanned == 0:
            raise ValueError("No oligos given to scan")
        self._has_scanned = self._total_oligos_scanned > 0
        return

    def _forward_primer_ratio(self) -> float:
        self._assert_has_scanned()
        total = sum(self._forward_primer_counter.values())
        numerator = self._forward_primer_counter[self._given_forward_primer]
        return numerator / total

    def _reverse_primer_ratio(self) -> float:
        self._assert_has_scanned()
        total = sum(self._reverse_primer_counter.values())
        numerator = self._reverse_primer_counter[self._given_reverse_primer]
        return numerator / total

    def raise_errors(self) -> None:
        """
        Raise an error if there are any errors in the oligos.
        """
        self._assert_has_scanned()
        errors = []
        if len(self._oligo_casing_set) > 1:
            oligo_cases = ", ".join(case.value for case in self._oligo_casing_set)
            msg = f"Oligo casing is not uniform: {oligo_cases}."
            errors.append(msg)
        if OligoCasing.NONE in self._oligo_casing_set:
            msg = "Some oligos have an unknown case - either an oligo is an empty string or it is a mix of upper and lower case characters."
            errors.append(msg)
        if len(self._invalid_chars_set) > 0:
            invalid_chars = ", ".join(self._invalid_chars_set)
            msg = f"Oligo sequences contains invalid characters: {invalid_chars}."
            errors.append(msg)
        if len(errors) > 0:
            error_prefix = (
                "Multiple errors were found"
                if len(errors) > 1
                else "An error was found"
            )
            errors_formatted = " ".join(
                [f"#{i} {error}" for i, error in enumerate(errors, 1)]
            )
            msg = f"{error_prefix} while scanning the input file: {errors_formatted}"
            raise ValidationError(msg)
        return

    def get_oligos_case(self) -> OligoCasing:
        """
        Returns the case of the oligos.
        """
        self._assert_has_scanned()
        if len(self._oligo_casing_set) != 1:
            msg = "Oligo casing is not uniform - this error will only be raised if raise_errors() is not called."
            raise RuntimeError(msg)
        # Do not use pop() on the set because it will exhaust the set
        case = list(self._oligo_casing_set).pop()
        return case

    def predict_forward_primer(self) -> str:
        """
        Predict the forward primer based on the ratio of the number of times the
        given forward primer or its reverse complement is found in the oligos.

        If no primer is found, an empty string is returned.

        If the ratio is greater than 0.5, the given forward primer is returned.
        Otherwise, the reverse complement of the given forward primer is returned.
        """
        self._assert_has_scanned()
        original = self._given_forward_primer
        revcomp = self._given_forward_primer_revcomp
        func = self._forward_primer_ratio
        return self._predict_primer(original, revcomp, func)

    def predict_reverse_primer(self) -> str:
        """
        Predict the reverse primer based on the ratio of the number of times the
        given reverse primer or its reverse complement is found in the oligos.

        If no primer is found, an empty string is returned.

        If the ratio is greater than 0.5, the given reverse primer is returned.
        Otherwise, the reverse complement of the given reverse primer is returned.
        """
        self._assert_has_scanned()
        original = self._given_reverse_primer
        revcomp = self._given_reverse_primer_revcomp
        func = self._reverse_primer_ratio
        return self._predict_primer(original, revcomp, func)

    def _predict_primer(
        self, original: str, revcomp: str, func: t.Callable[[], float]
    ) -> str:
        self._assert_has_scanned()
        try:
            ratio = func()
        except ZeroDivisionError:
            # This happens when the primer is not found in any of the oligos
            primer = ""  # use empty string to indicate no primer found, let caller deal with it
        else:
            primer = original if ratio > 0.5 else revcomp
        return primer

    def _scan(self, oligo: str) -> None:
        self._count_oligo_casing(oligo)
        self._count_invalid_chars(oligo)

        forward_primer_tup = (
            self._given_forward_primer,
            self._given_forward_primer_revcomp,
            self._forward_primer_counter,
        )
        reverse_primer_tup = (
            self._given_reverse_primer,
            self._given_reverse_primer_revcomp,
            self._reverse_primer_counter,
        )
        for original, revcomp, counter in [
            forward_primer_tup,
            reverse_primer_tup,
        ]:
            self._count_primers(oligo, original, revcomp, counter)
        return

    def _count_oligo_casing(self, oligo: str) -> None:
        is_upper_case = oligo.isupper()
        is_lower_case = oligo.islower()

        if is_upper_case:
            self._oligo_casing_set.add(OligoCasing.UPPER)
        elif is_lower_case:
            self._oligo_casing_set.add(OligoCasing.LOWER)
        else:
            self._oligo_casing_set.add(OligoCasing.NONE)
        return

    def _count_invalid_chars(self, oligo: str) -> None:
        invalid_chars = find_invalid_chars_in_string(oligo, self._allowed_chars)
        self._invalid_chars_set.update(invalid_chars)
        return

    def _count_primers(
        self, oligo: str, original: str, revcomp: str, counter: t.Dict[str, int]
    ) -> None:
        if original == "" and revcomp == "":
            has_original = has_revcomp = True
        else:
            (has_original, has_revcomp) = self._find_primers(oligo, original, revcomp)
        counter[original] += 1 if has_original else 0
        counter[revcomp] += 1 if has_revcomp else 0
        return

    def _find_primers(
        self, oligo: str, original: str, revcomp: str
    ) -> t.Tuple[bool, bool]:
        # Matching is only possible if the primers and the oligo are all upper cased. The primers are upper cased at object creation.
        # But the oligo is upper cased at the time of scanning.
        clean_oligo = oligo.upper()

        # Calculate the conditions
        has_original_at_either_end = clean_oligo.startswith(
            original
        ) or clean_oligo.endswith(original)
        has_revcomp_at_either_end = clean_oligo.startswith(
            revcomp
        ) or clean_oligo.endswith(revcomp)
        contains_original = original in clean_oligo
        contains_revcomp = revcomp in clean_oligo

        # Catch dangerous scenarios
        # Edge case 1: a primer is found but not at either end of the oligo
        has_original_not_at_ends = contains_original and not has_original_at_either_end
        has_revcomp_not_at_ends = contains_revcomp and not has_revcomp_at_either_end
        if has_original_not_at_ends or has_revcomp_not_at_ends:
            msg = "Oligo contains a primer that is not found at either end of the oligo; this is not supported at this this time."
            raise UndevelopedFeatureError(msg)

        # Edge case 2: the original and revcomp are found in the same oligo
        has_original_and_revcomp = contains_original and contains_revcomp
        if has_original_and_revcomp:
            msg = "Oligo contains both the original primer and a reverse combinant of that same primer; this is not supported at this time."
            raise UndevelopedFeatureError(msg)

        # Normal case:
        return has_original_at_either_end, has_revcomp_at_either_end

    def _assert_has_scanned(self):
        if not self._has_scanned:
            msg = "Must call 'scan_all()' before calling this method or property"
            raise RuntimeError(msg)
