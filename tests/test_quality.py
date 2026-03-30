from vra.quality import classify_age_days, classify_ratio


def test_classify_age_days_returns_pass_warn_fail() -> None:
    assert classify_age_days(10.0, max_age_days=100) == "pass"
    assert classify_age_days(90.0, max_age_days=100) == "warn"
    assert classify_age_days(101.0, max_age_days=100) == "fail"


def test_classify_ratio_returns_pass_warn_fail() -> None:
    assert classify_ratio(0.01, max_ratio=0.05) == "pass"
    assert classify_ratio(0.045, max_ratio=0.05) == "warn"
    assert classify_ratio(0.051, max_ratio=0.05) == "fail"