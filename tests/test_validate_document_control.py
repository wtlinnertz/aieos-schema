"""Tests for the FR-018 Document Control instance-conformance validator."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "scripts" / "validate-document-control.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("validate_document_control", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


vdc = _load_module()
SCHEMA = vdc.load_schema()


def block(rows: dict) -> str:
    lines = ["## Document Control", "", "| Field | Value |", "|-------|-------|"]
    for k, v in rows.items():
        lines.append(f"| {k} | {v} |")
    return "\n".join(lines) + "\n"


def check(rows: dict) -> list[str]:
    return vdc.validate_block(vdc.parse_document_control(block(rows), SCHEMA), SCHEMA)


# --- valid cases -----------------------------------------------------------

def test_valid_draft_passes():
    assert check({"Artifact ID": "SAD-X-001", "Owner": "Todd", "Status": "DRAFT"}) == []


def test_valid_frozen_with_provenance_passes():
    assert check({
        "Artifact ID": "SAD-X-001", "Owner": "Todd", "Status": "FROZEN",
        "Frozen By": "Todd", "Frozen Date": "2026-07-11",
    }) == []


def test_halted_and_faulted_accepted():
    for s in ("HALTED", "FAULTED"):
        assert check({"Artifact ID": "SAD-X-001", "Owner": "Todd", "Status": s}) == []


def test_human_cased_status_normalizes():
    # "Frozen" -> FROZEN passes the enum; provenance present so constraint holds.
    assert check({
        "Artifact ID": "SAD-X-001", "Owner": "Todd", "Status": "Frozen",
        "Frozen By": "Todd", "Frozen Date": "2026-07-11",
    }) == []


def test_valid_last_validation_passes():
    assert check({
        "Artifact ID": "SAD-X-001", "Owner": "Todd", "Status": "VALIDATED",
        "Last Validation": "PASS",
    }) == []


# --- failure cases ---------------------------------------------------------

def test_frozen_without_provenance_fails():
    issues = check({"Artifact ID": "SAD-X-001", "Owner": "Todd", "Status": "FROZEN"})
    assert any("frozen_by" in i for i in issues)
    assert any("frozen_date" in i for i in issues)


def test_missing_owner_fails():
    issues = check({"Artifact ID": "SAD-X-001", "Status": "DRAFT"})
    assert any("owner" in i for i in issues)


def test_missing_artifact_id_fails_at_block_level():
    issues = check({"Owner": "Todd", "Status": "DRAFT"})
    assert any("artifact_id" in i for i in issues)


def test_invalid_status_rejected():
    issues = check({"Artifact ID": "SAD-X-001", "Owner": "Todd", "Status": "Bogus"})
    assert any("freeze_status" in i for i in issues)


def test_invalid_last_validation_rejected():
    issues = check({
        "Artifact ID": "SAD-X-001", "Owner": "Todd", "Status": "VALIDATED",
        "Last Validation": "MAYBE",
    })
    assert any("last_validation" in i for i in issues)


# --- file / CLI level ------------------------------------------------------

def test_file_without_document_control_is_skipped(tmp_path):
    f = tmp_path / "readme.md"
    f.write_text("# Just prose, no Document Control block\n")
    assert vdc.validate_file(f, SCHEMA) == []


def test_main_returns_0_on_conformant_dir(tmp_path, capsys):
    (tmp_path / "05-sad.md").write_text(block(
        {"Artifact ID": "SAD-X-001", "Owner": "Todd", "Status": "DRAFT"}
    ))
    assert vdc.main([str(tmp_path)]) == 0


def test_main_returns_1_on_nonconformant_file(tmp_path):
    bad = tmp_path / "05-sad.md"
    bad.write_text(block({"Artifact ID": "SAD-X-001", "Status": "FROZEN"}))
    assert vdc.main([str(bad)]) == 1


def test_main_returns_2_on_no_args():
    assert vdc.main([]) == 2
