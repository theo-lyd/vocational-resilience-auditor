from vra.normalization import normalize_ags, parse_genesis_coordinate, parse_german_number


def test_parse_german_number_handles_special_tokens() -> None:
    assert parse_german_number("-") is None
    assert parse_german_number("x") is None


def test_parse_german_number_handles_german_formats() -> None:
    assert parse_german_number("1.234") == 1234.0
    assert parse_german_number("1,5K") == 1500.0
    assert parse_german_number("2,0 Mio") == 2_000_000.0


def test_parse_genesis_coordinate() -> None:
    parsed = parse_genesis_coordinate("([GES].[%TOTAL%],[JAHR].[2024],[KREISE].[01001])")
    assert parsed["GES"] == "%TOTAL%"
    assert parsed["JAHR"] == "2024"
    assert parsed["KREISE"] == "01001"


def test_normalize_ags_rolls_up_municipality_codes() -> None:
    assert normalize_ags("01001") == "01001"
    assert normalize_ags("03241001") == "03241"


def test_normalize_ags_rejects_invalid_tokens() -> None:
    assert normalize_ags("DG") is None
    assert normalize_ags("  ") is None
    assert normalize_ags("1234") is None
