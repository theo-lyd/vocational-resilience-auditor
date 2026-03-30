from __future__ import annotations

import csv
import hashlib
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Callable

import pandas as pd

from .normalization import (
    decode_text_file,
    normalize_whitespace,
    parse_genesis_coordinate,
    parse_german_number,
)

NS = {"genml": "https://www-genesis.destatis.de/xml/GENESIS-ML_V0_3"}


@dataclass(frozen=True)
class BronzeConfig:
    raw_dir: Path
    bronze_dir: Path


@dataclass(frozen=True)
class SourceSpec:
    logical_name: str
    pattern: str
    format: str


SOURCE_SPECS = (
    SourceSpec("vocational_enrollment", "21121-01-05-4-B*.csv", "csv"),
    SourceSpec("hospital_capacity", "23111-01-04-4*.csv", "csv"),
    SourceSpec("vocational_graduates", "21121-02-02-4-B*.xml", "xml"),
)


def _find_start_line(lines: list[str], marker_predicate: Callable[[str], bool]) -> int:
    for idx, line in enumerate(lines):
        if marker_predicate(line):
            return idx
    raise ValueError("Could not locate first data row in input file")


def _checksum_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _union_by_name(frames: list[pd.DataFrame]) -> pd.DataFrame:
    if not frames:
        return pd.DataFrame()

    all_columns: list[str] = []
    for frame in frames:
        for col in frame.columns:
            if col not in all_columns:
                all_columns.append(col)

    aligned = [frame.reindex(columns=all_columns) for frame in frames]
    return pd.concat(aligned, ignore_index=True)


def _discover_sources(raw_dir: Path, spec: SourceSpec) -> list[Path]:
    matches = sorted(raw_dir.glob(spec.pattern))
    if not matches:
        raise FileNotFoundError(
            f"No input files found for {spec.logical_name} with pattern '{spec.pattern}' in {raw_dir}"
        )
    return matches


def ingest_vocational_enrollment(path: Path) -> pd.DataFrame:
    text = decode_text_file(path)
    lines = text.splitlines()
    start = _find_start_line(lines, lambda line: line.startswith("202") and ";" in line)

    reader = csv.reader(StringIO("\n".join(lines[start:])), delimiter=";")
    rows = []
    for row in reader:
        if len(row) < 8:
            continue
        year = row[0].strip()
        if not year.isdigit():
            continue

        rows.append(
            {
                "year": int(year),
                "ags": row[1].strip(),
                "district_name": normalize_whitespace(row[2]),
                "school_type": normalize_whitespace(row[3]),
                "schools_count": parse_german_number(row[4]),
                "students_total": parse_german_number(row[5]),
                "students_female": parse_german_number(row[6]),
                "students_foreign": parse_german_number(row[7]),
                "source_file": path.name,
            }
        )

    return pd.DataFrame(rows)


def ingest_hospital_capacity(path: Path) -> pd.DataFrame:
    text = decode_text_file(path)
    lines = text.splitlines()
    start = _find_start_line(lines, lambda line: line.startswith("31.12.") and ";" in line)

    metric_columns = [
        "hospitals_count",
        "total_beds",
        "beds_ophthalmology",
        "beds_surgery",
        "beds_gynecology_obstetrics",
        "beds_ent",
        "beds_dermatology",
        "beds_internal_medicine",
        "beds_geriatrics",
        "beds_pediatrics",
        "beds_neurology",
        "beds_orthopedics",
        "beds_urology",
        "beds_other_general",
        "beds_child_psychiatry",
        "beds_psychiatry",
        "beds_psychotherapeutic",
    ]

    reader = csv.reader(StringIO("\n".join(lines[start:])), delimiter=";")
    rows = []
    for row in reader:
        if len(row) < 3 + len(metric_columns):
            continue

        date = row[0].strip()
        ags = row[1].strip()
        district_name = normalize_whitespace(row[2])

        record: dict[str, object] = {
            "date": date,
            "year": int(date[-4:]) if date[-4:].isdigit() else None,
            "ags": ags,
            "district_name": district_name,
            "source_file": path.name,
        }

        for idx, col_name in enumerate(metric_columns):
            record[col_name] = parse_german_number(row[3 + idx])

        rows.append(record)

    return pd.DataFrame(rows)


def ingest_vocational_graduates_xml(path: Path) -> pd.DataFrame:
    root = ET.parse(path).getroot()
    records: list[dict[str, object]] = []

    datasets = root.findall(".//genml:DATASET", NS)
    for dataset in datasets:
        dataset_name = dataset.attrib.get("NAME", "")
        values = dataset.find("genml:VALUES", NS)
        if values is None:
            continue

        for value_node in values.findall("genml:VALUE", NS):
            attrs = value_node.attrib
            coordinate = attrs.get("COORDINATE", "")
            coordinate_map = parse_genesis_coordinate(coordinate)

            year_token = coordinate_map.get("JAHR")
            ags_token = coordinate_map.get("KREISE")

            records.append(
                {
                    "dataset_name": dataset_name,
                    "year": int(year_token) if year_token and year_token.isdigit() else None,
                    "ags": ags_token,
                    "gender_code": coordinate_map.get("GES"),
                    "degree_code": coordinate_map.get("BILAG3"),
                    "metric_content": attrs.get("CONTENT"),
                    "quality_code": attrs.get("QUALITY"),
                    "value": parse_german_number(attrs.get("ORIG")),
                    "raw_coordinate": coordinate,
                    "source_file": path.name,
                }
            )

    return pd.DataFrame(records)


def write_bronze_outputs(config: BronzeConfig) -> dict[str, Path]:
    config.bronze_dir.mkdir(parents=True, exist_ok=True)

    ingestion_started_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    enrollment_sources = _discover_sources(config.raw_dir, SOURCE_SPECS[0])
    hospital_sources = _discover_sources(config.raw_dir, SOURCE_SPECS[1])
    graduate_sources = _discover_sources(config.raw_dir, SOURCE_SPECS[2])

    enrollment = _union_by_name([ingest_vocational_enrollment(path) for path in enrollment_sources])
    hospitals = _union_by_name([ingest_hospital_capacity(path) for path in hospital_sources])
    graduates = _union_by_name([ingest_vocational_graduates_xml(path) for path in graduate_sources])

    metadata_rows: list[dict[str, object]] = []
    for spec, paths in (
        (SOURCE_SPECS[0], enrollment_sources),
        (SOURCE_SPECS[1], hospital_sources),
        (SOURCE_SPECS[2], graduate_sources),
    ):
        for source_path in paths:
            source_mtime = datetime.fromtimestamp(
                source_path.stat().st_mtime, tz=timezone.utc
            ).replace(microsecond=0)
            metadata_rows.append(
                {
                    "ingestion_started_at": ingestion_started_at,
                    "logical_name": spec.logical_name,
                    "source_format": spec.format,
                    "source_file": source_path.name,
                    "source_path": str(source_path),
                    "source_last_modified_at": source_mtime.isoformat(),
                    "source_checksum_sha256": _checksum_sha256(source_path),
                    "source_size_bytes": source_path.stat().st_size,
                }
            )

    output_paths = {
        "vocational_enrollment": config.bronze_dir / "vocational_enrollment.parquet",
        "hospital_capacity": config.bronze_dir / "hospital_capacity.parquet",
        "vocational_graduates": config.bronze_dir / "vocational_graduates.parquet",
        "ingestion_metadata": config.bronze_dir / "ingestion_metadata.parquet",
    }

    enrollment.to_parquet(output_paths["vocational_enrollment"], index=False)
    hospitals.to_parquet(output_paths["hospital_capacity"], index=False)
    graduates.to_parquet(output_paths["vocational_graduates"], index=False)
    pd.DataFrame(metadata_rows).to_parquet(output_paths["ingestion_metadata"], index=False)

    return output_paths
