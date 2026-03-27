#!/usr/bin/env python3
"""Extract a YAML schema from an AIEOS Markdown spec file.

Reads a spec file, extracts hard gates, version, and structural info,
and outputs a YAML schema conforming to meta-schema.yaml.

Usage:
    python scripts/extract-schema.py path/to/spec.md --kit EEK --layer 4
    python scripts/extract-schema.py path/to/spec.md --kit EEK --layer 4 --template path/to/template.md
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def extract_artifact_type(spec_path: Path) -> str:
    """Derive artifact type from filename: prd-spec.md → PRD."""
    name = spec_path.stem  # e.g., prd-spec
    name = name.replace("-spec", "")
    return name.upper().replace("-", "")


def extract_version(content: str) -> str:
    """Extract Version: vN.N from spec content."""
    match = re.search(r"^Version:\s*(v\d+\.\d+)", content, re.MULTILINE)
    return match.group(1) if match else "v1.0"


def extract_hard_gates(content: str) -> list[dict]:
    """Extract hard gate definitions from spec content.

    Looks for patterns like:
    - ### N. gate_name or #### N. gate_name
    - | gate_name | rule description |
    - **gate_name**: description
    """
    gates = []

    # Pattern 1: ### N. gate_name or #### gate_name sections
    # Common in EEK specs: "#### 1. problem_definition"
    section_pattern = re.compile(
        r"^#{3,4}\s*(?:\d+\.?\s*)?[`*]*(\w+)[`*]*\s*$", re.MULTILINE
    )
    for match in section_pattern.finditer(content):
        gate_name = match.group(1).lower()
        # Skip non-gate headings
        if gate_name in (
            "purpose", "scope", "authority", "upstream", "downstream",
            "content", "rules", "format", "output", "document", "hard",
            "additional", "notes", "constraints", "error", "input",
            "preconditions", "postconditions",
        ):
            continue
        # Extract rule text: next paragraph after the heading
        after = content[match.end():match.end() + 500]
        rule_match = re.search(r"\n\s*[-*]?\s*(.+?)(?:\n\n|\n[-*#])", after)
        rule = rule_match.group(1).strip() if rule_match else ""
        # Clean up rule
        rule = re.sub(r"^\*\*Rules?\*\*:?\s*", "", rule)
        rule = re.sub(r"^[-*]\s*", "", rule)
        if rule and len(rule) > 10:
            gates.append({"name": gate_name, "rule": rule})

    # Pattern 2: Table rows | gate_name | rule |
    table_pattern = re.compile(
        r"^\|\s*`?(\w+)`?\s*\|\s*(.+?)\s*\|", re.MULTILINE
    )
    for match in table_pattern.finditer(content):
        gate_name = match.group(1).lower()
        rule = match.group(2).strip()
        # Skip table headers and non-gate rows
        if gate_name in ("gate", "gate_name", "name", "hard_gate", "---", "field"):
            continue
        if rule.startswith("---") or rule.startswith("Rule") or rule.startswith("Description"):
            continue
        if re.match(r"^[a-z_]+$", gate_name) and rule and len(rule) > 10:
            # Don't duplicate if already found via section pattern
            existing_names = {g["name"] for g in gates}
            if gate_name not in existing_names:
                gates.append({"name": gate_name, "rule": rule})

    return gates


def extract_sections_from_template(template_path: Path) -> list[dict]:
    """Extract required sections from a template file."""
    if not template_path.exists():
        return []
    content = template_path.read_text()
    sections = []
    for match in re.finditer(r"^##\s+(.+)$", content, re.MULTILINE):
        section_name = match.group(1).strip()
        # Skip numbered prefixes like "0. Document Control"
        section_name = re.sub(r"^\d+\.?\s*", "", section_name)
        if section_name:
            sections.append({"name": section_name, "required": True})
    return sections


def detect_entry_gate(content: str, prompt_path: Path | None) -> bool:
    """Detect if this is a human-authored entry gate."""
    if prompt_path and not prompt_path.exists():
        return True
    if re.search(r"human.authored|entry.gate|intake.form", content, re.IGNORECASE):
        return True
    return False


def extract_upstream(content: str) -> list[dict]:
    """Extract upstream dependency references from spec content."""
    deps = []
    # Look for "Upstream Dependencies" section
    upstream_match = re.search(
        r"(?:Upstream|Input|Dependencies).*?\n((?:[-*].*\n)*)",
        content, re.IGNORECASE
    )
    if upstream_match:
        for line in upstream_match.group(1).split("\n"):
            # Extract artifact types mentioned
            types = re.findall(r"\b(PRD|SAD|TDD|WDD|ORD|ACF|DCF|DPRD|KER|WCR|PFD|VH|AR|EL|SDR|SOER|VER|RER|RCF|RP|RR|TM|SAR|CER|DAR|CSPEC|FFLR|DSR|QGR)\b", line)
            for t in types:
                if t not in {d["artifact_type"] for d in deps}:
                    condition = "frozen"
                    if "optional" in line.lower():
                        condition = "optional"
                    deps.append({"artifact_type": t, "condition": condition})
    return deps


def build_schema(
    spec_path: Path,
    kit: str,
    layer: int,
    template_path: Path | None = None,
    prompt_path: Path | None = None,
    validator_path: Path | None = None,
) -> dict:
    """Build a complete schema dict from a spec file."""
    content = spec_path.read_text()
    artifact_type = extract_artifact_type(spec_path)

    # Derive file paths relative to kit root
    kit_root = spec_path.parent.parent.parent  # docs/specs/xxx-spec.md → kit root
    spec_rel = str(spec_path.relative_to(kit_root))

    template_rel = None
    if template_path:
        template_rel = str(template_path.relative_to(kit_root))
    else:
        # Guess template path
        template_guess = spec_path.parent.parent / "artifacts" / spec_path.name.replace("-spec", "-template")
        if template_guess.exists():
            template_rel = str(template_guess.relative_to(kit_root))
            template_path = template_guess

    prompt_rel = None
    if prompt_path:
        prompt_rel = str(prompt_path.relative_to(kit_root))
    else:
        prompt_guess = spec_path.parent.parent / "prompts" / spec_path.name.replace("-spec", "-prompt")
        if prompt_guess.exists():
            prompt_rel = str(prompt_guess.relative_to(kit_root))
            prompt_path = prompt_guess

    validator_rel = None
    if validator_path:
        validator_rel = str(validator_path.relative_to(kit_root))
    else:
        validator_guess = spec_path.parent.parent / "validators" / spec_path.name.replace("-spec", "-validator")
        if validator_guess.exists():
            validator_rel = str(validator_guess.relative_to(kit_root))

    is_entry_gate = detect_entry_gate(content, prompt_path)

    schema = {
        "artifact_type": artifact_type,
        "kit": kit,
        "layer": layer,
        "spec_version": extract_version(content),
        "entry_gate": is_entry_gate,
        "hard_gates": extract_hard_gates(content),
        "required_sections": extract_sections_from_template(template_path) if template_path else [],
        "file_paths": {
            "spec": spec_rel,
            "template": template_rel,
            "prompt": prompt_rel if not is_entry_gate else None,
            "validator": validator_rel,
        },
        "upstream_dependencies": extract_upstream(content),
    }

    return schema


def schema_to_yaml(schema: dict) -> str:
    """Convert schema dict to YAML string (manual formatting for readability)."""
    lines = []
    lines.append(f"# Schema for {schema['artifact_type']} ({schema['kit']} — Layer {schema['layer']})")
    lines.append(f"# Auto-extracted from {schema['file_paths']['spec']}")
    lines.append(f"# Review and verify before use.")
    lines.append("")
    lines.append(f"artifact_type: {schema['artifact_type']}")
    lines.append(f"kit: {schema['kit']}")
    lines.append(f"layer: {schema['layer']}")
    lines.append(f"spec_version: \"{schema['spec_version']}\"")
    lines.append(f"entry_gate: {str(schema['entry_gate']).lower()}")
    lines.append("")

    # Hard gates
    lines.append("hard_gates:")
    if schema["hard_gates"]:
        for gate in schema["hard_gates"]:
            lines.append(f"  - name: {gate['name']}")
            # Escape quotes in rule
            rule = gate["rule"].replace('"', '\\"')
            lines.append(f'    rule: "{rule}"')
    else:
        lines.append("  []  # No gates extracted — manual review needed")
    lines.append("")

    # Required sections
    lines.append("required_sections:")
    if schema["required_sections"]:
        for section in schema["required_sections"]:
            lines.append(f'  - name: "{section["name"]}"')
            lines.append(f"    required: {str(section.get('required', True)).lower()}")
    else:
        lines.append("  []  # No sections extracted — add from template")
    lines.append("")

    # File paths
    lines.append("file_paths:")
    lines.append(f"  spec: \"{schema['file_paths']['spec']}\"")
    if schema["file_paths"]["template"]:
        lines.append(f"  template: \"{schema['file_paths']['template']}\"")
    else:
        lines.append("  template: null  # Not found — verify path")
    if schema["file_paths"]["prompt"]:
        lines.append(f"  prompt: \"{schema['file_paths']['prompt']}\"")
    else:
        lines.append("  prompt: null")
    if schema["file_paths"]["validator"]:
        lines.append(f"  validator: \"{schema['file_paths']['validator']}\"")
    else:
        lines.append("  validator: null  # Not found — verify path")
    lines.append("")

    # Upstream dependencies
    if schema["upstream_dependencies"]:
        lines.append("upstream_dependencies:")
        for dep in schema["upstream_dependencies"]:
            lines.append(f"  - artifact_type: {dep['artifact_type']}")
            lines.append(f"    condition: \"{dep['condition']}\"")
    else:
        lines.append("upstream_dependencies: []")
    lines.append("")

    # Downstream consumers (empty — needs manual population)
    lines.append("downstream_consumers: []  # Populate from flow-reference.md")

    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Extract YAML schema from AIEOS Markdown spec")
    parser.add_argument("spec", help="Path to the spec .md file")
    parser.add_argument("--kit", required=True, help="Kit abbreviation (EEK, PIK, etc.)")
    parser.add_argument("--layer", required=True, type=int, help="Layer number (1-15)")
    parser.add_argument("--template", help="Path to the template .md file")
    parser.add_argument("--output", help="Output YAML path (default: stdout)")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    if not spec_path.exists():
        print(f"Error: spec file not found: {spec_path}", file=sys.stderr)
        sys.exit(1)

    template_path = Path(args.template) if args.template else None

    schema = build_schema(spec_path, args.kit, args.layer, template_path)
    yaml_output = schema_to_yaml(schema)

    if args.output:
        Path(args.output).write_text(yaml_output)
        print(f"Schema written to {args.output}", file=sys.stderr)
    else:
        print(yaml_output)


if __name__ == "__main__":
    main()
