#!/usr/bin/env python3
"""Validate an artifact's Document Control block against the canonical schema.

FR-018 instance-conformance validator. Parses the ``| Field | Value |`` Document
Control table from an AIEOS artifact Markdown file and checks it against
``schema/document-control.yaml``:

  * every ``required`` field is present and non-empty,
  * ``freeze_status`` is one of the canonical enum values,
  * ``last_validation``, if present, is one of its enum values,
  * the ``frozen_requires_provenance`` constraint holds: a FROZEN artifact
    carries both ``frozen_by`` and ``frozen_date``.

The validator is driven by the schema (labels, enums, required flags), so it
stays in sync with the canonical block automatically — add a field or enum
value in the YAML and this validator enforces it with no code change.

Usage:
    validate-document-control.py <artifact.md | docs/sdlc dir> [...]

Exit code:
    0 — every Document Control block checked is conformant.
    1 — at least one block failed (details printed to stderr).
    2 — usage / schema-load error.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import yaml

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema" / "document-control.yaml"


def load_schema(path: Path = SCHEMA_PATH) -> dict[str, Any]:
    return yaml.safe_load(path.read_text())


def parse_document_control(text: str, schema: dict[str, Any]) -> dict[str, str]:
    """Extract canonical field -> value from an artifact's Document Control table.

    Reads each field's on-disk ``label`` from the schema and finds the matching
    ``| <label> | <value> |`` row (case-insensitive). Missing rows are simply
    absent from the returned dict; empty values are returned as "".
    """
    found: dict[str, str] = {}
    for field_name, spec in schema["fields"].items():
        label = spec.get("label", field_name)
        pattern = rf"\|\s*{re.escape(label)}\s*\|\s*(.*?)\s*\|"
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            found[field_name] = m.group(1).strip()
    return found


def validate_block(fields: dict[str, str], schema: dict[str, Any]) -> list[str]:
    """Return a list of issue strings; empty means conformant."""
    issues: list[str] = []
    specs = schema["fields"]

    # Required-field presence (non-empty; "N/A" is allowed for artifact_id per schema).
    for field_name, spec in specs.items():
        if spec.get("required") and not fields.get(field_name):
            issues.append(f"missing required field '{field_name}' (label '{spec.get('label', field_name)}')")

    # Enum membership. On-disk status may be human-cased ("Frozen"); normalize the
    # same way read_frozen_artifacts does before comparing.
    for field_name, spec in specs.items():
        allowed = spec.get("enum")
        raw = fields.get(field_name)
        if allowed and raw:
            normalized = raw.upper().replace(" ", "_")
            if normalized not in allowed:
                issues.append(
                    f"field '{field_name}' value {raw!r} not in {allowed}"
                )

    # Constraint: frozen_requires_provenance.
    status = (fields.get("freeze_status") or "").upper().replace(" ", "_")
    if status == "FROZEN":
        for prov in ("frozen_by", "frozen_date"):
            if not fields.get(prov):
                issues.append(
                    f"freeze_status is FROZEN but '{prov}' is missing "
                    "(constraint: frozen_requires_provenance)"
                )

    return issues


def iter_markdown(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            files.extend(sorted(path.glob("*.md")))
        elif path.is_file():
            files.append(path)
    return files


def validate_file(md_file: Path, schema: dict[str, Any]) -> list[str]:
    text = md_file.read_text()
    # Only artifacts that actually carry a Document Control block are in scope.
    if not re.search(r"\|\s*Artifact\s+ID\s*\|", text, re.IGNORECASE):
        return []
    fields = parse_document_control(text, schema)
    return validate_block(fields, schema)


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        schema = load_schema()
    except (OSError, yaml.YAMLError) as exc:
        print(f"failed to load schema {SCHEMA_PATH}: {exc}", file=sys.stderr)
        return 2

    files = iter_markdown(argv)
    failed = False
    checked = 0
    for md_file in files:
        issues = validate_file(md_file, schema)
        if issues:
            failed = True
            for issue in issues:
                print(f"FAIL {md_file}: {issue}", file=sys.stderr)
        else:
            checked += 1

    if failed:
        return 1
    print(f"OK: {checked} Document Control block(s) conformant")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
