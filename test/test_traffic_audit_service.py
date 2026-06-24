import json
from datetime import datetime
from pathlib import Path

import pytest

from src.services.traffic_audit_service import (
    TrafficAuditValidationError,
    analyze_case_data,
    build_report,
    new_case,
    parse_dataset,
)

FIXTURES = Path(__file__).parent / "fixtures" / "traffic_audit"
LARGE_FIXTURES = FIXTURES / "large_sample"


def load_case(plate_number: str):
    case = new_case(
        title=f"{plate_number} 测试案件",
        plate_number=plate_number,
        started_at=datetime.fromisoformat("2026-01-02T07:00:00"),
        ended_at=datetime.fromisoformat("2026-01-02T10:00:00"),
        department_id=1,
        created_by="pytest",
    )
    case.datasets = {
        dataset_type: parse_dataset(dataset_type, path.name, path.read_bytes())
        for dataset_type, path in {
            "vehicles": FIXTURES / "vehicles.csv",
            "transactions": FIXTURES / "transactions.csv",
            "passages": FIXTURES / "passages.csv",
        }.items()
    }
    return case


def load_large_case(plate_number: str, window_start: str, window_end: str):
    case = new_case(
        title=f"{plate_number} large sample case",
        plate_number=plate_number,
        started_at=datetime.fromisoformat(window_start),
        ended_at=datetime.fromisoformat(window_end),
        department_id=1,
        created_by="pytest",
    )
    case.datasets = {
        dataset_type: parse_dataset(dataset_type, path.name, path.read_bytes())
        for dataset_type, path in {
            "vehicles": LARGE_FIXTURES / "vehicles.csv",
            "transactions": LARGE_FIXTURES / "transactions.csv",
            "passages": LARGE_FIXTURES / "passages.csv",
        }.items()
    }
    return case


def test_parse_dataset_normalizes_plate_and_deduplicates_records():
    content = (
        "record_id,plate_number,plate_color,vehicle_type\n"
        "v1, 鄂a10001 ,蓝,小型客车\n"
        "v1,鄂A10001,蓝,小型客车\n"
    ).encode()

    parsed = parse_dataset("vehicles", "vehicles.csv", content)

    assert len(parsed["records"]) == 1
    assert parsed["records"][0]["plate_number"] == "鄂A10001"
    assert parsed["records"][0]["source"]["row_number"] == 2


def test_parse_dataset_rejects_missing_boundary_fields():
    with pytest.raises(TrafficAuditValidationError, match="缺少字段"):
        parse_dataset("passages", "passages.csv", b"record_id,plate_number\np1,A12345\n")


def test_analysis_rejects_case_without_target_vehicle_records():
    case = load_case("鄂A10001")
    case.datasets["vehicles"]["records"] = []

    with pytest.raises(TrafficAuditValidationError, match="没有案件目标车辆"):
        analyze_case_data(case)


@pytest.mark.parametrize(
    ("plate_number", "expected_anomaly"),
    [
        ("鄂A10002", "missing_endpoint"),
        ("鄂A10003", "time_conflict"),
        ("鄂A10004", "route_discontinuity"),
        ("鄂A10005", "fee_mismatch"),
    ],
)
def test_each_audit_rule_produces_traceable_evidence(plate_number, expected_anomaly):
    result = analyze_case_data(load_case(plate_number))

    evidence = next(item for item in result["evidence"] if item["anomaly_type"] == expected_anomaly)
    assert evidence["sources"]
    assert all(source["record_id"] and source["row_number"] for source in evidence["sources"])
    assert evidence["rule_basis"]


def test_normal_case_has_stable_route_and_no_evidence():
    case = load_case("鄂A10001")

    first = analyze_case_data(case)
    second = analyze_case_data(case)

    assert first["route"] == second["route"]
    assert first["evidence"] == second["evidence"] == []


def test_report_marks_result_as_unconfirmed_and_includes_sources():
    case = load_case("鄂A10005")
    report = build_report(case, analyze_case_data(case))

    assert "正式结论：未经人工确认" in report
    assert "transactions.csv:6(t5)" in report


def test_large_acceptance_dataset_matches_manifest_expectations():
    manifest = json.loads((LARGE_FIXTURES / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["counts"] == {
        "vehicles": 180,
        "transactions": 180,
        "passages": 670,
        "cases": 180,
    }

    for item in manifest["cases"]:
        result = analyze_case_data(
            load_large_case(item["plate_number"], item["window_start"], item["window_end"])
        )
        actual = {evidence["anomaly_type"] for evidence in result["evidence"]}
        expected = set(item["expected_anomalies"])

        assert expected <= actual
        if item["scenario"] in {"normal", "green_review"}:
            assert actual == set()
        for evidence in result["evidence"]:
            assert evidence["sources"]
            assert all(
                source["source_file"] and source["row_number"] and source["record_id"]
                for source in evidence["sources"]
            )
