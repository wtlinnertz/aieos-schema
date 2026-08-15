"""Validate the FR-014 calibration contracts (slice 2, PR 1).

Three top-level cross-cutting records, same carve-out as lock.yaml:
intentionally not swept by the per-kit conformance tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

SCHEMA_DIR = Path(__file__).parent.parent / "schema"


@pytest.fixture(scope="module")
def gold_case():
    return yaml.safe_load((SCHEMA_DIR / "gold-case.yaml").read_text())


@pytest.fixture(scope="module")
def report():
    return yaml.safe_load((SCHEMA_DIR / "calibration-report.yaml").read_text())


@pytest.fixture(scope="module")
def lock():
    return yaml.safe_load((SCHEMA_DIR / "calibration-lock.yaml").read_text())


class TestGoldCaseSchema:
    def test_parses(self, gold_case):
        assert gold_case["gold_case_version"] == "1.0"
        assert gold_case["serialization"] == "yaml"
        assert gold_case["path"].startswith("tests/gold/")

    def test_activation_floor_matches_ratified_decision(self, gold_case):
        # Ratified 2026-08-12 (build spec item 3): floor of 12,
        # >= 2 spec-exemption cases, both labels mechanically present.
        floor = gold_case["activation_floor"]
        assert floor["min_cases"] == 12
        assert floor["min_spec_exemption_cases"] == 2
        assert floor["min_pass_cases"] >= 1
        assert floor["min_fail_cases"] >= 1

    def test_required_fields_present(self, gold_case):
        fields = gold_case["fields"]
        for name in [
            "case_id", "artifact_type", "validator", "input_path",
            "input_sha256", "expected_gates", "spec_exemption_case",
            "labeled_by", "labeled_date", "source",
        ]:
            assert name in fields, f"missing field {name}"
            assert fields[name].get("required") is True
        assert fields["dispute_ref"].get("required") is False

    def test_input_is_pointer_not_inline(self, gold_case):
        fields = gold_case["fields"]
        assert "input_path" in fields and "input_sha256" in fields
        assert "content" not in fields  # 60K-char artifacts stay in fixtures

    def test_constraints_cover_key_rules(self, gold_case):
        ids = {c["id"] for c in gold_case["constraints"]}
        for expected in [
            "human_labeled_only", "content_pinned", "activation_floor",
            "accretion_rule", "relabel_with_spec",
        ]:
            assert expected in ids, f"missing constraint {expected}"


class TestCalibrationReportSchema:
    def test_parses(self, report):
        assert report["calibration_report_version"] == "1.0"
        assert report["serialization"] == "json"

    def test_runs_per_case_is_three(self, report):
        # Ratified: three identical runs; any flip is a calibration FAIL.
        assert report["runs_per_case"] == 3

    def test_thresholds_match_ratified_decision(self, report):
        # Ratified 2026-08-12 (build spec item 2): 0.9 freeze-gate / 0.75
        # advisory; false-PASS bar only for freeze-gate.
        th = report["thresholds"]
        assert th["freeze-gate"]["gate_agreement_min"] == 0.9
        assert th["freeze-gate"]["false_pass_max"] == 0
        assert th["advisory"]["gate_agreement_min"] == 0.75
        assert th["advisory"]["false_pass_max"] is None

    def test_required_fields_present(self, report):
        fields = report["fields"]
        for name in [
            "report_version", "validator", "artifact_type", "role", "judge",
            "run_date", "case_count", "runs_per_case", "gate_agreement",
            "false_pass_count", "stability_flips", "kappa", "verdict", "gates",
        ]:
            assert name in fields, f"missing field {name}"
            assert fields[name].get("required") is True

    def test_role_and_verdict_enums(self, report):
        fields = report["fields"]
        assert set(fields["role"]["enum"]) == {"freeze-gate", "advisory"}
        assert set(fields["verdict"]["enum"]) == {"PASS", "FAIL"}

    def test_constraints_cover_asymmetric_gates(self, report):
        ids = {c["id"] for c in report["constraints"]}
        for expected in [
            "kappa_never_gates", "zero_false_pass_freeze_gate",
            "any_flip_fails", "thresholds_per_role",
            "report_is_evidence_not_contract",
        ]:
            assert expected in ids, f"missing constraint {expected}"


class TestCalibrationLockSchema:
    def test_parses(self, lock):
        assert lock["calibration_lock_version"] == "1.0"
        assert lock["path"] == "calibration.lock"
        assert lock["serialization"] == "json"  # ratified 2026-08-12

    def test_structure_and_entry_fields(self, lock):
        assert lock["structure"]["validators"]["type"] == "map"
        fields = lock["fields"]
        for name in [
            "prompt_sha256", "model", "gate_agreement",
            "false_pass_count", "calibrated_at", "report_ref",
        ]:
            assert name in fields, f"missing field {name}"
            assert fields[name].get("required") is True

    def test_constraints_cover_key_rules(self, lock):
        ids = {c["id"] for c in lock["constraints"]}
        for expected in [
            "hash_compare_only", "recalibration_triggers",
            "measures_never_corrects", "conductor_precondition",
            "committed_artifact",
        ]:
            assert expected in ids, f"missing constraint {expected}"
