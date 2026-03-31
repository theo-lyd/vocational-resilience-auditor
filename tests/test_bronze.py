from __future__ import annotations

from pathlib import Path

import pytest

from vra.bronze import SourceSpec, _discover_sources


def test_discover_sources_uses_root_before_samples(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    sample_dir = raw_dir / "samples"
    raw_dir.mkdir(parents=True)
    sample_dir.mkdir(parents=True)

    root_file = raw_dir / "21121-01-05-4-B.csv"
    sample_file = sample_dir / "21121-01-05-4-B.sample.csv"
    root_file.write_text("x", encoding="utf-8")
    sample_file.write_text("y", encoding="utf-8")

    spec = SourceSpec("vocational_enrollment", "21121-01-05-4-B*.csv", "csv")
    matches = _discover_sources(raw_dir, spec)

    assert matches == [root_file]


def test_discover_sources_falls_back_to_samples(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    sample_dir = raw_dir / "samples"
    sample_dir.mkdir(parents=True)

    sample_file = sample_dir / "21121-02-02-4-B.sample.xml"
    sample_file.write_text("<xml />", encoding="utf-8")

    spec = SourceSpec("vocational_graduates", "21121-02-02-4-B*.xml", "xml")
    matches = _discover_sources(raw_dir, spec)

    assert matches == [sample_file]


def test_discover_sources_raises_when_missing(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir(parents=True)

    spec = SourceSpec("hospital_capacity", "23111-01-04-4*.csv", "csv")
    with pytest.raises(FileNotFoundError):
        _discover_sources(raw_dir, spec)
