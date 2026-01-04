"""
Lineage/Audit Trail Checks
==========================

Checks for lineage metadata in source files.
"""

from pathlib import Path


def check_lineage_metadata(repo_root: Path, file_paths: list[Path]) -> list[dict]:
    """
    Check that files have lineage metadata for audit trail.

    Files generated through TDFLOW or other code generation pipelines should
    have embedded lineage metadata that links them back to their spec.

    The lineage chain is: Spec → Test → Implementation
    Each generated file should have @spec_file, @spec_id, @component_id
    in its header comments.

    This check helps enforce the audit trail, making it possible to trace
    any piece of code back to its requirements and associated tests.
    """
    violations = []

    # Import lineage module
    try:
        from ..lineage import parse_lineage_from_file
    except ImportError:
        try:
            from agentforge.core.lineage import parse_lineage_from_file
        except ImportError:
            # Lineage module not available - skip check
            return violations

    for file_path in file_paths:
        try:
            # Parse lineage from file header
            lineage = parse_lineage_from_file(file_path)

            if lineage is None:
                # No lineage metadata found
                rel_path = str(file_path.relative_to(repo_root))

                # Determine if this is likely a generated file
                # (vs hand-written legacy code)
                is_test = "test_" in file_path.name or "/tests/" in str(file_path)

                violations.append({
                    "message": "File missing lineage metadata (no audit trail)",
                    "file": rel_path,
                    "line": 1,
                    "severity": "info",
                    "fix_hint": (
                        "Add lineage header to file:\n"
                        "# @spec_file: .agentforge/specs/your-spec-v1.yaml\n"
                        "# @spec_id: your-spec-v1\n"
                        "# @component_id: component-name\n"
                        + ("# @impl_path: path/to/implementation.py\n" if is_test else "# @test_path: tests/path/to/test.py\n")
                        + "Or regenerate file through TDFLOW to get proper lineage."
                    )
                })

        except Exception:
            # Skip files that can't be read
            continue

    return violations
