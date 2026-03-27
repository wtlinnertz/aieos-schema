"""Shared fixtures for AIEOS Schema tests."""

from __future__ import annotations
from pathlib import Path
import pytest
import yaml


SCHEMA_ROOT = Path(__file__).parent.parent / "schema"
META_SCHEMA_PATH = SCHEMA_ROOT / "meta-schema.yaml"

# All kit directories
KIT_DIRS = [d for d in SCHEMA_ROOT.iterdir() if d.is_dir()]


@pytest.fixture(scope="session")
def meta_schema():
    """Load the meta-schema."""
    return yaml.safe_load(META_SCHEMA_PATH.read_text())


@pytest.fixture(scope="session")
def all_schemas():
    """Load all schema files as (path, data) tuples."""
    schemas = []
    for kit_dir in KIT_DIRS:
        for schema_file in sorted(kit_dir.glob("*.yaml")):
            data = yaml.safe_load(schema_file.read_text())
            schemas.append((schema_file, data))
    return schemas


@pytest.fixture(scope="session")
def schema_root():
    return SCHEMA_ROOT
