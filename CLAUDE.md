# CLAUDE.md

## What This Project Is

**AIEOS Schema** (ECO-001) provides machine-readable YAML schema files for every governed artifact specification in the AIEOS framework. Each schema captures hard gates, required template sections, file paths, upstream/downstream dependencies, and artifact metadata.

This is the **keystone ecosystem project** — it unlocks ECO-002 (Evaluation Engine), ECO-004 (System Twin), ECO-006 (Analytics), ECO-007 (Compliance Reporter), and strengthens ECO-009 (Agent Harness).

## Schema Format

Each schema file conforms to `schema/meta-schema.yaml`. See that file for the complete field specification.

## Repository Structure

```
schema/
  meta-schema.yaml     # Defines the schema contract
  eek/                 # One YAML per EEK spec (14 files)
  pik/                 # PIK specs (7 files)
  ssk/                 # SSK specs (3 files)
  rek/                 # REK specs (5 files)
  rrk/                 # RRK specs (4 files)
  iek/                 # IEK specs (2 files)
  odk/                 # ODK specs (4 files)
  qak/                 # QAK specs (4 files)
  sck/                 # SCK specs (4 files)
  dck/                 # DCK specs (4 files)
  pinfk/               # PINFK specs (4 files)
  dkk/                 # DKK specs (4 files)
  prk/                 # PRK specs (1 file)
  bpk/                 # BPK specs (3 files)
  sdk/                 # SDK specs (5 files)
scripts/
  extract-schema.py    # Helper: read Markdown spec → initial YAML
tests/
  test_schema_valid.py # All schemas parse and conform to meta-schema
  test_schema_sync.py  # Schema matches actual Markdown spec
```

## Running Tests

```bash
pytest tests/ -v
```

## Adding a Schema

When a new spec is added to any AIEOS kit:
1. Run `python scripts/extract-schema.py path/to/spec.md --kit KIT --layer N`
2. Review and complete the output (especially hard_gates)
3. Save to `schema/{kit}/{artifact_type}.yaml`
4. Run tests to validate
