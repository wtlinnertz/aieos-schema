"""Validate the canonical cross-driver lock schema (FR-019)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

LOCK_PATH = Path(__file__).parent.parent / "schema" / "lock.yaml"


@pytest.fixture(scope="module")
def lock_schema():
    return yaml.safe_load(LOCK_PATH.read_text())


class TestLockSchema:
    def test_parses(self, lock_schema):
        assert isinstance(lock_schema, dict)
        assert lock_schema["lock_version"] == "1.0"
        assert lock_schema["granularity"] == "whole-initiative"
        assert lock_schema["path"] == ".aieos/lock"

    def test_required_fields_present(self, lock_schema):
        fields = lock_schema["fields"]
        for name in [
            "lock_version", "owner", "driver", "session_id", "hostname",
            "pid", "acquired_at", "renewed_at", "lease_ttl_seconds",
            "heartbeat_interval_seconds",
        ]:
            assert name in fields, f"missing field {name}"

    def test_driver_enum(self, lock_schema):
        assert set(lock_schema["fields"]["driver"]["enum"]) == {
            "console", "dark-factory", "sherpa"
        }

    def test_lease_defaults_match_decisions_log(self, lock_schema):
        # Q4: 60s heartbeat / 5min TTL
        assert lock_schema["fields"]["lease_ttl_seconds"]["default"] == 300
        assert lock_schema["fields"]["heartbeat_interval_seconds"]["default"] == 60

    def test_constraints_cover_key_rules(self, lock_schema):
        ids = {c["id"] for c in lock_schema["constraints"]}
        for expected in [
            "session_id_is_ownership", "hostname_scoped_liveness",
            "lease_expiry_takeover", "takeover_writes_halt", "not_a_freeze",
            "frozen_boundary_handoff",
        ]:
            assert expected in ids, f"missing constraint {expected}"
