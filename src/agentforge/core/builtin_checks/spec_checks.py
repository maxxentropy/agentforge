"""
Spec Integrity Checks
=====================

Checks for spec file integrity and bidirectional links.
"""

import re
from pathlib import Path


def _validate_spec_component(comp: dict, index: int, rel_path: str) -> list[dict]:
    """Validate a single component in a spec file."""
    violations = []
    comp_id = comp.get("component_id", comp.get("name", f"component[{index}]"))
    required = [("component_id", "warning", "Add component_id for lineage tracking"),
                ("location", "warning", "Add location path to component"),
                ("test_location", "info", "Add test_location for full traceability")]
    for field, severity, fix_hint in required:
        if field not in comp:
            violations.append({
                "message": f"Component '{comp_id}' missing {field}",
                "file": rel_path, "severity": severity, "fix_hint": fix_hint
            })
    return violations


def _validate_spec_file(spec: dict, rel_path: str, required_fields: list[str]) -> list[dict]:
    """Validate a parsed spec dictionary."""
    violations = []
    for field in required_fields:
        if field not in spec:
            violations.append({
                "message": f"Spec missing required field: {field}",
                "file": rel_path, "severity": "error", "fix_hint": f"Add '{field}' field to spec"
            })
    components = spec.get("components", [])
    if isinstance(components, list):
        for i, comp in enumerate(components):
            if isinstance(comp, dict):
                violations.extend(_validate_spec_component(comp, i, rel_path))
    return violations


def check_spec_integrity(repo_root: Path, file_paths: list[Path],
                         required_fields: list[str] | None = None) -> list[dict]:
    """Verify spec files have required fields and proper structure."""
    import yaml
    violations = []
    required_fields = required_fields or ["spec_id", "name", "components"]

    for file_path in file_paths:
        if file_path.suffix not in ('.yaml', '.yml'):
            continue
        try:
            spec = yaml.safe_load(file_path.read_text(encoding='utf-8'))
        except Exception as e:
            violations.append({
                "message": f"Invalid YAML: {e}", "file": str(file_path.relative_to(repo_root)),
                "severity": "error", "fix_hint": "Fix YAML syntax errors"
            })
            continue
        if isinstance(spec, dict):
            violations.extend(_validate_spec_file(spec, str(file_path.relative_to(repo_root)), required_fields))
    return violations


def _check_file_references_spec(
    repo_root: Path, file_path: Path, expected_spec_id: str, comp_id: str, spec_rel_path: str
) -> list[dict]:
    """Check if a file's lineage references the correct spec."""
    try:
        header = '\n'.join(file_path.read_text(encoding='utf-8').split('\n')[:30])
    except Exception:
        return []
    spec_match = re.search(r'@spec_id:\s*(\S+)', header)
    if not spec_match:
        return []  # No lineage - handled by check_lineage_metadata
    actual_spec_id = spec_match.group(1)
    if actual_spec_id != expected_spec_id:
        return [{
            "message": f"File references wrong spec_id: '{actual_spec_id}' (expected '{expected_spec_id}')",
            "file": str(file_path.relative_to(repo_root)), "severity": "error",
            "fix_hint": f"Update @spec_id to '{expected_spec_id}'"
        }]
    return []


def _check_component_link(
    repo_root: Path, comp: dict, spec_id: str, rel_spec_path: str
) -> list[dict]:
    """Check a single component's impl and test file links."""
    violations = []
    comp_id = comp.get("component_id", comp.get("name"))
    location = comp.get("location")
    test_location = comp.get("test_location")

    for loc, kind, severity in [(location, "file", "error"), (test_location, "test", "warning")]:
        if not loc:
            continue
        path = repo_root / loc
        if not path.exists():
            violations.append({
                "message": f"Component '{comp_id}' references missing {kind}: {loc}",
                "file": rel_spec_path, "severity": severity, "fix_hint": f"Create {loc} or update spec"
            })
        else:
            violations.extend(_check_file_references_spec(repo_root, path, spec_id, comp_id, rel_spec_path))
    return violations


def check_bidirectional_links(repo_root: Path, file_paths: list[Path]) -> list[dict]:
    """Verify spec↔test↔impl links are consistent and files exist."""
    import yaml
    violations = []
    spec_files = [f for f in file_paths if '.agentforge/specs' in str(f) and f.suffix in ('.yaml', '.yml')]

    for spec_path in spec_files:
        try:
            spec = yaml.safe_load(spec_path.read_text(encoding='utf-8'))
        except Exception:
            continue
        if not isinstance(spec, dict) or not spec.get("spec_id"):
            continue

        spec_id = spec.get("spec_id")
        rel_spec_path = str(spec_path.relative_to(repo_root))
        for comp in spec.get("components", []):
            if isinstance(comp, dict):
                violations.extend(_check_component_link(repo_root, comp, spec_id, rel_spec_path))
    return violations


def _check_file_placement(file_path: Path, rel_path: str) -> dict | None:
    """Check if a file is misplaced based on its name/type."""
    # Test files outside tests/
    if file_path.name.startswith("test_") and file_path.suffix == ".py":
        if not rel_path.startswith("tests/"):
            return {"message": "Test file outside tests/ directory", "file": rel_path,
                    "severity": "warning", "fix_hint": "Move test files to tests/ directory"}
    # Spec files outside .agentforge/specs/
    if file_path.suffix in ('.yaml', '.yml') and 'spec' in file_path.name.lower():
        if '.agentforge/specs' not in rel_path and 'contracts' not in rel_path:
            return {"message": "Spec-like file outside .agentforge/specs/", "file": rel_path,
                    "severity": "info", "fix_hint": "Move spec files to .agentforge/specs/"}
    return None


def check_file_structure(repo_root: Path, file_paths: list[Path],
                         structure_rules: dict | None = None) -> list[dict]:
    """Verify files are in expected locations based on structure rules."""
    violations = []
    for file_path in file_paths:
        try:
            rel_path = str(file_path.relative_to(repo_root))
        except ValueError:
            continue
        violation = _check_file_placement(file_path, rel_path)
        if violation:
            violations.append(violation)
    return violations
