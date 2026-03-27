"""Validate all schema files parse and conform to meta-schema."""

from __future__ import annotations
import re
from pathlib import Path
import pytest
import yaml


class TestAllSchemasParse:
    """Every YAML file in schema/ must parse without errors."""

    def test_meta_schema_parses(self, meta_schema):
        assert meta_schema is not None
        assert "schema_version" in meta_schema

    def test_all_schemas_parse(self, all_schemas):
        """Every schema file loads as valid YAML."""
        assert len(all_schemas) > 0, "No schema files found"
        for path, data in all_schemas:
            assert data is not None, f"{path} parsed as None"
            assert isinstance(data, dict), f"{path} is not a dict"


class TestSchemaConformance:
    """Every schema must have the required fields from meta-schema."""

    REQUIRED_FIELDS = [
        "artifact_type",
        "kit",
        "layer",
        "spec_version",
        "hard_gates",
        "file_paths",
    ]

    def test_required_fields_present(self, all_schemas):
        """Every schema has all required fields."""
        missing = []
        for path, data in all_schemas:
            for field in self.REQUIRED_FIELDS:
                if field not in data:
                    missing.append(f"{path.name}: missing '{field}'")
        assert not missing, f"Missing required fields:\n" + "\n".join(missing)

    def test_artifact_type_uppercase(self, all_schemas):
        """artifact_type must be uppercase."""
        violations = []
        for path, data in all_schemas:
            at = data.get("artifact_type", "")
            if at != at.upper():
                violations.append(f"{path.name}: '{at}' not uppercase")
        assert not violations, "\n".join(violations)

    def test_kit_valid(self, all_schemas):
        VALID_KITS = {"SDK", "PIK", "SSK", "EEK", "REK", "RRK", "IEK",
                      "ODK", "QAK", "SCK", "DCK", "PINFK", "DKK", "PRK", "BPK"}
        violations = []
        for path, data in all_schemas:
            kit = data.get("kit", "")
            if kit not in VALID_KITS:
                violations.append(f"{path.name}: kit '{kit}' not in valid set")
        assert not violations, "\n".join(violations)

    def test_layer_in_range(self, all_schemas):
        """Layer must be 1-15."""
        violations = []
        for path, data in all_schemas:
            layer = data.get("layer", 0)
            if not (1 <= layer <= 15):
                violations.append(f"{path.name}: layer {layer} out of range")
        assert not violations, "\n".join(violations)

    def test_spec_version_format(self, all_schemas):
        """spec_version must match vN.N pattern."""
        violations = []
        for path, data in all_schemas:
            sv = data.get("spec_version", "")
            if not re.match(r"^v\d+\.\d+$", str(sv)):
                violations.append(f"{path.name}: spec_version '{sv}' invalid")
        assert not violations, "\n".join(violations)

    def test_hard_gates_have_names_and_rules(self, all_schemas):
        """Every hard gate must have name and rule."""
        violations = []
        for path, data in all_schemas:
            gates = data.get("hard_gates", [])
            if not isinstance(gates, list):
                violations.append(f"{path.name}: hard_gates is not a list")
                continue
            for i, gate in enumerate(gates):
                if not isinstance(gate, dict):
                    violations.append(f"{path.name}: gate {i} is not a dict")
                    continue
                if "name" not in gate:
                    violations.append(f"{path.name}: gate {i} missing 'name'")
                if "rule" not in gate:
                    violations.append(f"{path.name}: gate {i} missing 'rule'")
        assert not violations, "\n".join(violations)

    def test_gate_names_snake_case(self, all_schemas):
        """Gate names must be snake_case."""
        violations = []
        for path, data in all_schemas:
            for gate in data.get("hard_gates", []):
                name = gate.get("name", "")
                if not re.match(r"^[a-z][a-z0-9_]*$", name):
                    violations.append(f"{path.name}: gate name '{name}' not snake_case")
        assert not violations, "\n".join(violations)

    def test_file_paths_has_spec(self, all_schemas):
        """file_paths must include spec path."""
        violations = []
        for path, data in all_schemas:
            fp = data.get("file_paths", {})
            if not fp.get("spec"):
                violations.append(f"{path.name}: missing file_paths.spec")
        assert not violations, "\n".join(violations)

    def test_entry_gates_have_no_prompt(self, all_schemas):
        """Entry gates (entry_gate: true) must have prompt: null."""
        violations = []
        for path, data in all_schemas:
            if data.get("entry_gate", False):
                prompt = data.get("file_paths", {}).get("prompt")
                if prompt is not None:
                    violations.append(f"{path.name}: entry_gate=true but prompt is not null")
        assert not violations, "\n".join(violations)


class TestSchemaStatistics:
    """Aggregate statistics for documentation."""

    def test_minimum_schema_count(self, all_schemas):
        """Must have at least 55 schemas (one per spec file)."""
        assert len(all_schemas) >= 55, f"Only {len(all_schemas)} schemas found (expected 55+)"

    def test_all_15_kits_represented(self, all_schemas):
        """All 15 kits must have at least one schema."""
        kits = {data["kit"] for _, data in all_schemas}
        expected = {"SDK", "PIK", "SSK", "EEK", "REK", "RRK", "IEK",
                    "ODK", "QAK", "SCK", "DCK", "PINFK", "DKK", "PRK", "BPK"}
        missing = expected - kits
        assert not missing, f"Missing kit schemas: {missing}"

    def test_total_gate_count(self, all_schemas):
        """Total gates across all schemas should be substantial."""
        total = sum(len(data.get("hard_gates", [])) for _, data in all_schemas)
        assert total >= 300, f"Only {total} total gates (expected 300+)"
        print(f"\nTotal schemas: {len(all_schemas)}, Total gates: {total}")
