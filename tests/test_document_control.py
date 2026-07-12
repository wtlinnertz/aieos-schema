"""Validate the canonical Document Control block schema (FR-018).

The block in schema/document-control.yaml is the single on-disk representation
of an artifact's freeze status, read and written by all drivers (sherpa,
console, dark factory) and the harness. This test locks its shape.
"""

from __future__ import annotations
from pathlib import Path
import yaml
import pytest

DOC_CONTROL_PATH = Path(__file__).parent.parent / "schema" / "document-control.yaml"

# The freeze lifecycle is the harness ArtifactStatus enum (src/models.py:
# DRAFT/VALIDATED/FREEZE_PENDING/FROZEN) plus the two andon-cord fault states
# (ADR-0004: HALTED/FAULTED). The harness enum must be EXTENDED to add the two
# fault states as a Phase 1 harness task; this canonical file is the source of
# truth that reconciliation targets.
EXPECTED_FREEZE_STATUS = [
    "DRAFT", "VALIDATED", "FREEZE_PENDING", "FROZEN", "HALTED", "FAULTED",
]
EXPECTED_LAST_VALIDATION = ["PASS", "FAIL"]


@pytest.fixture(scope="module")
def doc_control():
    return yaml.safe_load(DOC_CONTROL_PATH.read_text())


def test_parses_as_dict(doc_control):
    assert isinstance(doc_control, dict)


def test_section_name_is_document_control(doc_control):
    assert doc_control["section_name"] == "Document Control"


def test_freeze_status_enum_matches_canonical(doc_control):
    assert doc_control["fields"]["freeze_status"]["enum"] == EXPECTED_FREEZE_STATUS


def test_freeze_status_required_defaults_draft(doc_control):
    fs = doc_control["fields"]["freeze_status"]
    assert fs["required"] is True
    assert fs["default"] == "DRAFT"


def test_last_validation_is_orthogonal_and_optional(doc_control):
    """Validation outcome is a separate, nullable field — not a freeze state."""
    lv = doc_control["fields"]["last_validation"]
    assert lv["enum"] == EXPECTED_LAST_VALIDATION
    assert lv["required"] is False
    assert lv["nullable"] is True


def test_freeze_authority_constraints_present(doc_control):
    ids = {c["id"] for c in doc_control["constraints"]}
    assert "frozen_requires_provenance" in ids
    assert "frozen_writer_authority" in ids
    assert "fault_writer_authority" in ids
