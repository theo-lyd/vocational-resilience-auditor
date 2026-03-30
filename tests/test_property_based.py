from __future__ import annotations

import math
import re

from hypothesis import assume, given
from hypothesis import strategies as st

from vra.normalization import normalize_ags, parse_genesis_coordinate, parse_german_number
from vra.resilience_methodology import compute_sensitivity


@given(st.from_regex(r"\d{5}", fullmatch=True))
def test_normalize_ags_preserves_valid_district_codes(token: str) -> None:
    assert normalize_ags(token) == token


@given(st.from_regex(r"\d{8}", fullmatch=True))
def test_normalize_ags_rolls_up_valid_municipality_codes(token: str) -> None:
    assert normalize_ags(token) == token[:5]


@given(st.text(min_size=1, max_size=12))
def test_normalize_ags_rejects_non_digit_or_wrong_length_tokens(token: str) -> None:
    normalized = token.strip()
    assume(not (re.fullmatch(r"\d{5}", normalized) or re.fullmatch(r"\d{8}", normalized)))
    assert normalize_ags(token) is None


@given(st.integers(min_value=0, max_value=10**11))
def test_parse_german_number_parses_thousand_separator_format(value: int) -> None:
    german = f"{value:,}".replace(",", ".")
    assert parse_german_number(german) == float(value)


@given(
    st.dictionaries(
        keys=st.from_regex(r"[A-Z]{2,6}", fullmatch=True),
        values=st.from_regex(r"[A-Z0-9_%]{1,12}", fullmatch=True),
        min_size=1,
        max_size=6,
    )
)
def test_parse_genesis_coordinate_roundtrip(pairs: dict[str, str]) -> None:
    coordinate = "(" + ",".join(f"[{k}].[{v}]" for k, v in pairs.items()) + ")"
    assert parse_genesis_coordinate(coordinate) == pairs


@given(
    graduates=st.floats(min_value=1.0, max_value=10_000.0, allow_nan=False, allow_infinity=False),
    beds=st.floats(min_value=1.0, max_value=10_000.0, allow_nan=False, allow_infinity=False),
    bed_change_percent=st.floats(min_value=0.0, max_value=0.95, allow_nan=False, allow_infinity=False),
)
def test_compute_sensitivity_matches_expected_formula(
    graduates: float,
    beds: float,
    bed_change_percent: float,
) -> None:
    sensitivity = compute_sensitivity(graduates=graduates, beds=beds, bed_change_percent=bed_change_percent)
    assert sensitivity is not None
    expected = (1 / (1 - bed_change_percent) - 1) * 100
    assert math.isclose(sensitivity, expected, rel_tol=1e-9, abs_tol=1e-9)


@given(
    graduates=st.floats(min_value=1.0, max_value=10_000.0, allow_nan=False, allow_infinity=False),
    beds=st.floats(min_value=1.0, max_value=10_000.0, allow_nan=False, allow_infinity=False),
    bed_change_percent=st.one_of(
        st.floats(max_value=-1e-6, allow_nan=False, allow_infinity=False),
        st.floats(min_value=1.0, max_value=2.0, allow_nan=False, allow_infinity=False),
    ),
)
def test_compute_sensitivity_rejects_out_of_range_bed_change(
    graduates: float,
    beds: float,
    bed_change_percent: float,
) -> None:
    assert compute_sensitivity(graduates=graduates, beds=beds, bed_change_percent=bed_change_percent) is None
