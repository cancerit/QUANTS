import pytest
from src.dna.helpers import reverse_complement, reverse_complement_sequences


EXAMPLE_CSV_HEADER = "sequence"

REV_COMP_PARAMS = [
    pytest.param("AGCT", "AGCT", id="case1"),
    pytest.param("CGTA", "TACG", id="case2"),
    pytest.param("AAAGGGCCCTTT", "AAAGGGCCCTTT", id="case3"),
    pytest.param("ATCGATCG", "CGATCGAT", id="case4"),
    pytest.param("", "", id="case5"),
    pytest.param("CCCTGGGAAGGTAATTTTAGATTTC", "GAAATCTAAAATTACCTTCCCAGGG", id="case6"),
]


@pytest.mark.parametrize("input_sequence, expected_output", REV_COMP_PARAMS)
def test_reverse_complement(input_sequence, expected_output):
    # When
    actual_output = reverse_complement(input_sequence)

    # Then
    assert actual_output == expected_output


REV_COMP_SEQUENCES_PARAMS = [
    pytest.param([{"sequence": "AGCT"}], [{"sequence": "AGCT"}], id="case1"),
    pytest.param([{"sequence": "CGTA"}], [{"sequence": "TACG"}], id="case2"),
    pytest.param(
        [
            {"sequence": "AAAGGGCCCTTT"},
            {"sequence": "CCCTGGGAAGGTAATTTTAGATTTC"},
        ],
        [
            {"sequence": "AAAGGGCCCTTT"},
            {"sequence": "GAAATCTAAAATTACCTTCCCAGGG"},
        ],
        id="case3",
    ),
    pytest.param([{"sequence": "ATCGATCG"}], [{"sequence": "CGATCGAT"}], id="case4"),
]


@pytest.mark.parametrize("input_sequence, expected_output", REV_COMP_SEQUENCES_PARAMS)
def test_reverse_complement_sequences(input_sequence, expected_output):
    # When
    actual_output = list(
        reverse_complement_sequences(input_sequence, header=EXAMPLE_CSV_HEADER)
    )

    # Then
    assert actual_output == expected_output
