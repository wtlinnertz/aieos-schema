# AIEOS Schema

Machine-readable YAML schema files for every governed artifact specification in the AIEOS framework. The keystone ecosystem project (ECO-001) that unlocks downstream projects: Evaluation Engine, System Twin, Governance Analytics, Compliance Reporter, and Agent Harness.

## What it captures

Each schema file represents one AIEOS spec and contains:
- Hard gates — names, rules, and failure examples
- Required sections — template section inventory
- File paths — spec, template, prompt, validator locations
- Dependencies — upstream artifacts required, downstream consumers
- Metadata — artifact type, kit, layer, spec version, entry gate flag

## Quick start

```bash
# Run validation tests
pip install pyyaml pytest
PYTHONPATH=. pytest tests/ -v

# Extract a schema from a Markdown spec (starting point, needs manual review)
python scripts/extract-schema.py path/to/spec.md --kit EEK --layer 4
```

## Schema format

Every schema conforms to `schema/meta-schema.yaml`. Example:

```yaml
artifact_type: PRD
kit: EEK
layer: 4
spec_version: "v1.0"
entry_gate: false

hard_gates:
  - name: problem_definition
    rule: "Clear problem statement with identified users and impact"
  - name: goals
    rule: "Explicit goals with measurable success criteria"
  # ...

required_sections:
  - name: "Document Control"
    required: true
  - name: "Problem Statement"
    required: true
  # ...

file_paths:
  spec: "docs/specs/prd-spec.md"
  template: "docs/artifacts/prd-template.md"
  prompt: "docs/prompts/prd-prompt.md"
  validator: "docs/validators/prd-validator.md"

upstream_dependencies:
  - artifact_type: DPRD
    condition: "frozen (Path A) or Product Brief (Path B)"
```

## Coverage

| Kit | Layer | Schemas | Gates |
|-----|-------|---------|-------|
| SDK | 1 | 5 | 28 |
| PIK | 2 | 7 | 45 |
| SSK | 3 | 3 | 16 |
| EEK | 4 | 14 | 99 |
| REK | 5 | 5 | 31 |
| RRK | 6 | 4 | 23 |
| IEK | 7 | 2 | 11 |
| ODK | 8 | 4 | 22 |
| QAK | 9 | 4 | 18 |
| SCK | 10 | 4 | 18 |
| DCK | 11 | 4 | 20 |
| PINFK | 12 | 4 | 22 |
| DKK | 13 | 4 | 19 |
| PRK | 14 | 1 | 5 |
| BPK | 15 | 3 | 14 |
| **Total** | | **68** | **391** |

## Tests

14 validation tests verify:
- All schemas parse as valid YAML
- Required fields present (artifact_type, kit, layer, spec_version, hard_gates, file_paths)
- Artifact types are uppercase, kits are valid, layers in range
- Gate names are snake_case with rules
- Entry gates have no prompt path
- All 15 kits represented, 55+ schemas exist, 300+ gates total

## License

[MIT](LICENSE)
