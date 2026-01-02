#!/usr/bin/env python3
"""
Schema Validator
================

Validate YAML/JSON files against JSON Schema.

Usage:
    python validate_schema.py <schema_file> <data_file>
    python validate_schema.py schemas/intake_record.schema.yaml outputs/intake_record.yaml
"""

import json
import sys
from pathlib import Path

import yaml

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


def load_yaml_or_json(filepath: Path) -> dict:
    """Load a YAML or JSON file."""
    with open(filepath) as f:
        content = f.read()

    # Try YAML first (also handles JSON)
    try:
        return yaml.safe_load(content)
    except yaml.YAMLError:
        pass

    # Try JSON
    return json.loads(content)


def validate(schema_path: Path, data_path: Path) -> tuple[bool, list[str]]:
    """
    Validate data against schema.

    Returns:
        (is_valid, list_of_errors)
    """
    if not HAS_JSONSCHEMA:
        return False, ["jsonschema not installed. Run: pip install jsonschema"]

    schema = load_yaml_or_json(schema_path)
    data = load_yaml_or_json(data_path)

    validator = jsonschema.Draft7Validator(schema)
    errors = list(validator.iter_errors(data))

    if not errors:
        return True, []

    error_messages = []
    for error in errors:
        path = " -> ".join(str(p) for p in error.absolute_path) or "(root)"
        error_messages.append(f"  {path}: {error.message}")

    return False, error_messages


def main():
    if len(sys.argv) != 3:
        print("Usage: python validate_schema.py <schema_file> <data_file>")
        print()
        print("Examples:")
        print("  python validate_schema.py schemas/intake_record.schema.yaml outputs/intake_record.yaml")
        print("  python validate_schema.py schemas/analysis_report.schema.yaml outputs/analysis_report.yaml")
        sys.exit(1)

    schema_path = Path(sys.argv[1])
    data_path = Path(sys.argv[2])

    if not schema_path.exists():
        print(f"Error: Schema file not found: {schema_path}")
        sys.exit(1)

    if not data_path.exists():
        print(f"Error: Data file not found: {data_path}")
        sys.exit(1)

    print(f"Schema: {schema_path}")
    print(f"Data:   {data_path}")
    print()

    is_valid, errors = validate(schema_path, data_path)

    if is_valid:
        print("✅ VALID")
        sys.exit(0)
    else:
        print("❌ INVALID")
        print()
        print("Errors:")
        for error in errors:
            print(error)
        sys.exit(1)


if __name__ == "__main__":
    main()
