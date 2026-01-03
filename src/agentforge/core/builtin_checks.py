# @spec_file: .agentforge/specs/core-v1.yaml
# @spec_id: core-v1
# @component_id: agentforge-core-builtin_checks
# @test_path: tests/unit/tools/test_builtin_checks_architecture.py

"""
Built-in check implementations for AgentForge contracts.

These functions provide reusable checks that can be invoked from contracts
using the 'custom' check type. They are specifically designed for tasks
that cannot be done via LSP (text patterns, file operations, etc.).

NOTE: For semantic code analysis (public fields, method naming, etc.),
use `lsp_query` check type instead - it leverages our LSP adapters for
accurate, parser-based analysis.

Each function follows the signature:
    func(repo_root: Path, file_paths: List[Path], **params) -> List[Dict]

Return format:
    [
        {
            "message": "Description of the violation",
            "file": "relative/path/to/file.cs",
            "line": 42,
            "severity": "error",  # Optional, defaults to check's severity
            "fix_hint": "How to fix this"  # Optional
        }
    ]
"""

import re
from pathlib import Path

# ==============================================================================
# Text Pattern Checks (appropriate for regex)
# ==============================================================================

def check_todo_comments(repo_root: Path, file_paths: list[Path],
                        require_ticket: bool = False,
                        ticket_patterns: list[str] | None = None) -> list[dict]:
    """
    Check for TODO/FIXME comments, optionally requiring ticket references.

    Args:
        require_ticket: If True, TODOs must have a ticket reference
        ticket_patterns: Patterns to match ticket references (e.g., ['AB#\\d+', 'JIRA-\\d+'])
    """
    violations = []
    ticket_patterns = ticket_patterns or [r'AB#\d+', r'[A-Z]+-\d+', r'GH#\d+']
    ticket_regex = re.compile('|'.join(ticket_patterns))

    todo_pattern = re.compile(r'\b(TODO|FIXME|HACK|XXX)\b', re.IGNORECASE)

    for file_path in file_paths:
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue

        for line_num, line in enumerate(content.split('\n'), 1):
            match = todo_pattern.search(line)
            if match and require_ticket and not ticket_regex.search(line):
                violations.append({
                    "message": f"{match.group(1)} comment without ticket reference",
                    "file": str(file_path.relative_to(repo_root)),
                    "line": line_num,
                    "severity": "warning",
                    "fix_hint": "Add ticket reference (e.g., TODO(AB#1234): ...)"
                })

    return violations


def check_debug_statements(repo_root: Path, file_paths: list[Path],
                           patterns: list[str] | None = None) -> list[dict]:
    """
    Check for debug statements that shouldn't be committed.

    This is appropriate for regex since we're looking for specific text patterns
    like console.log, print(), debugger, etc.

    Args:
        patterns: Additional patterns to check for (beyond defaults)
    """
    violations = []

    # Default debug patterns per file type
    default_patterns = {
        '.py': [r'\bprint\s*\(', r'\bbreakpoint\s*\(', r'\bpdb\.set_trace\s*\('],
        '.js': [r'\bconsole\.(log|debug|info)\s*\(', r'\bdebugger\b'],
        '.jsx': [r'\bconsole\.(log|debug|info)\s*\(', r'\bdebugger\b'],
        '.ts': [r'\bconsole\.(log|debug|info)\s*\(', r'\bdebugger\b'],
        '.tsx': [r'\bconsole\.(log|debug|info)\s*\(', r'\bdebugger\b'],
    }

    for file_path in file_paths:
        suffix = file_path.suffix.lower()
        file_patterns = default_patterns.get(suffix, [])
        if patterns:
            file_patterns = file_patterns + patterns

        if not file_patterns:
            continue

        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue

        combined = re.compile('|'.join(file_patterns))

        for line_num, line in enumerate(content.split('\n'), 1):
            # Skip comments
            stripped = line.strip()
            if stripped.startswith(('#', '//', '/*', '*')):
                continue

            match = combined.search(line)
            if match:
                violations.append({
                    "message": f"Debug statement found: {match.group(0)[:30]}",
                    "file": str(file_path.relative_to(repo_root)),
                    "line": line_num,
                    "fix_hint": "Remove debug statements before committing"
                })

    return violations


# ==============================================================================
# File/Directory Checks
# ==============================================================================

def check_file_size(repo_root: Path, file_paths: list[Path],
                    max_lines: int = 500,
                    max_bytes: int = 50000) -> list[dict]:
    """
    Check that files don't exceed size limits.
    """
    violations = []

    for file_path in file_paths:
        try:
            stat = file_path.stat()
            if stat.st_size > max_bytes:
                violations.append({
                    "message": f"File exceeds size limit ({stat.st_size} bytes > {max_bytes})",
                    "file": str(file_path.relative_to(repo_root)),
                    "severity": "warning",
                    "fix_hint": "Consider splitting into smaller files"
                })
                continue

            content = file_path.read_text(encoding='utf-8', errors='ignore')
            line_count = len(content.split('\n'))
            if line_count > max_lines:
                violations.append({
                    "message": f"File exceeds line limit ({line_count} lines > {max_lines})",
                    "file": str(file_path.relative_to(repo_root)),
                    "severity": "warning",
                    "fix_hint": "Consider splitting into smaller files"
                })
        except Exception:
            continue

    return violations


def check_line_length(repo_root: Path, file_paths: list[Path],
                      max_length: int = 120) -> list[dict]:
    """
    Check that lines don't exceed maximum length.
    """
    violations = []

    for file_path in file_paths:
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue

        for line_num, line in enumerate(content.split('\n'), 1):
            if len(line) > max_length:
                violations.append({
                    "message": f"Line exceeds {max_length} characters ({len(line)} chars)",
                    "file": str(file_path.relative_to(repo_root)),
                    "line": line_num,
                    "severity": "warning"
                })

    return violations


def check_trailing_whitespace(repo_root: Path, file_paths: list[Path]) -> list[dict]:
    """
    Check for trailing whitespace.
    """
    violations = []

    for file_path in file_paths:
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue

        for line_num, line in enumerate(content.split('\n'), 1):
            if line.rstrip() != line:
                violations.append({
                    "message": "Line has trailing whitespace",
                    "file": str(file_path.relative_to(repo_root)),
                    "line": line_num,
                    "severity": "info",
                    "fix_hint": "Remove trailing whitespace"
                })

    return violations


def check_mixed_line_endings(repo_root: Path, file_paths: list[Path]) -> list[dict]:
    """
    Check for mixed line endings (CRLF vs LF).
    """
    violations = []

    for file_path in file_paths:
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
        except Exception:
            continue

        has_crlf = b'\r\n' in content
        # Check for LF not preceded by CR
        has_lf = bool(re.search(b'[^\r]\n', content)) or content.startswith(b'\n')

        if has_crlf and has_lf:
            violations.append({
                "message": "File has mixed line endings (CRLF and LF)",
                "file": str(file_path.relative_to(repo_root)),
                "severity": "warning",
                "fix_hint": "Normalize line endings to LF"
            })

    return violations


# ==============================================================================
# Security Pattern Checks (appropriate for regex)
# ==============================================================================

def check_hardcoded_secrets(repo_root: Path, file_paths: list[Path],
                            additional_patterns: list[str] | None = None) -> list[dict]:
    """
    Check for potential hardcoded secrets in code.

    This uses regex patterns to find potential secrets in string literals.
    It's appropriate for regex since we're looking for text patterns.
    """
    violations = []

    # Patterns that might indicate hardcoded secrets
    secret_patterns = [
        # API keys and tokens
        (r'["\'](?:api[_-]?key|apikey)["\']?\s*[=:]\s*["\'][a-zA-Z0-9]{20,}["\']', "API key"),
        (r'["\'](?:secret|token)["\']?\s*[=:]\s*["\'][a-zA-Z0-9]{20,}["\']', "Secret/Token"),
        # Passwords
        (r'(?:password|passwd|pwd)\s*[=:]\s*["\'][^"\']{8,}["\']', "Password"),
        # AWS
        (r'AKIA[0-9A-Z]{16}', "AWS Access Key"),
        (r'[a-zA-Z0-9/+=]{40}', "Potential AWS Secret Key"),
        # Connection strings
        (r'(?:mongodb|postgres|mysql|redis)://[^"\'\s]+', "Database connection string"),
    ]

    if additional_patterns:
        secret_patterns.extend([(p, "Custom pattern") for p in additional_patterns])

    for file_path in file_paths:
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue

        for pattern, secret_type in secret_patterns:
            try:
                regex = re.compile(pattern, re.IGNORECASE)
                for match in regex.finditer(content):
                    line_num = content[:match.start()].count('\n') + 1
                    violations.append({
                        "message": f"Potential {secret_type} found",
                        "file": str(file_path.relative_to(repo_root)),
                        "line": line_num,
                        "severity": "error",
                        "fix_hint": "Use environment variables or a secrets manager"
                    })
            except re.error:
                continue

    return violations


# ==============================================================================
# Lineage/Audit Trail Checks
# ==============================================================================

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
        from .lineage import parse_lineage_from_file
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


# ==============================================================================
# Spec Integrity Checks
# ==============================================================================

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


# ==============================================================================
# Architecture Checks (AST-based semantic analysis)
# ==============================================================================
# These are imported from a separate module to keep file size manageable

try:
    from .builtin_checks_architecture import (
        check_circular_imports,
        check_constructor_injection,
        check_domain_purity,
        check_layer_imports,
    )
except ImportError:
    from builtin_checks_architecture import (
        check_circular_imports,
        check_constructor_injection,
        check_domain_purity,
        check_layer_imports,
    )

# ==============================================================================
# Minimal Context Architecture Validation
# ==============================================================================

def check_minimal_context_validation(
    repo_root: Path,
    file_paths: list[Path],
    **params
) -> list[dict]:
    """
    Check that the Minimal Context Architecture has proper validation in place.

    Validates that key files contain required validation methods:
    1. EnhancedContextBuilder has _validate_context_integrity
    2. Executor has _validate_response_parameters
    3. PhaseMachine has validate_state

    This ensures runtime validation catches issues early.
    """
    violations = []

    required_validations = {
        "enhanced_context_builder.py": {
            "method": "_validate_context_integrity",
            "description": "context integrity validation",
        },
        "executor.py": {
            "method": "_validate_response_parameters",
            "description": "response parameter validation",
        },
        "phase_machine.py": {
            "method": "validate_state",
            "description": "phase state validation",
        },
    }

    for file_path in file_paths:
        filename = file_path.name
        if filename not in required_validations:
            continue

        req = required_validations[filename]

        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue

        if f"def {req['method']}" not in content:
            violations.append({
                "message": f"Missing {req['description']} method: {req['method']}",
                "file": str(file_path.relative_to(repo_root)),
                "severity": "error",
                "fix_hint": f"Add {req['method']} method for runtime validation"
            })

    return violations


# ==============================================================================
# Architecture checks (AST-based) - Stubs for future implementation
# ==============================================================================


def check_layer_imports(
    repo_root: Path,
    file_paths: list[Path],
    **kwargs,
) -> list[dict]:
    """
    Check that layer imports follow architectural boundaries.

    This is a stub implementation. Future implementation should:
    - Define layer hierarchy (e.g., domain < application < infrastructure)
    - Verify imports don't violate boundaries (e.g., domain shouldn't import infra)

    Args:
        repo_root: Repository root directory
        file_paths: Files to check
        **kwargs: Additional parameters from contract config (layer_detection, layer_rules)

    Returns:
        List of violations (empty for now)
    """
    # TODO: Implement layer boundary checking
    return []


def check_constructor_injection(
    repo_root: Path,
    file_paths: list[Path],
    **kwargs,
) -> list[dict]:
    """
    Check that classes use constructor injection for dependencies.

    This is a stub implementation. Future implementation should:
    - Parse class constructors
    - Verify dependencies are injected via __init__
    - Flag direct instantiation of dependencies

    Args:
        repo_root: Repository root directory
        file_paths: Files to check
        **kwargs: Additional parameters from contract config (class_patterns, etc.)

    Returns:
        List of violations (empty for now)
    """
    # TODO: Implement constructor injection checking
    return []


def check_domain_purity(
    repo_root: Path,
    file_paths: list[Path],
    **kwargs,
) -> list[dict]:
    """
    Check that domain layer has no external dependencies.

    This is a stub implementation. Future implementation should:
    - Identify domain layer files
    - Verify they don't import infrastructure concerns
    - Flag I/O, HTTP, database imports in domain

    Args:
        repo_root: Repository root directory
        file_paths: Files to check
        **kwargs: Additional parameters from contract config (forbidden_imports, etc.)

    Returns:
        List of violations (empty for now)
    """
    # TODO: Implement domain purity checking
    return []


def check_circular_imports(
    repo_root: Path,
    file_paths: list[Path],
    **kwargs,
) -> list[dict]:
    """
    Detect circular import dependencies.

    This is a stub implementation. Future implementation should:
    - Build import graph from AST
    - Detect cycles in the graph
    - Report minimal cycle paths

    Args:
        repo_root: Repository root directory
        file_paths: Files to check
        **kwargs: Additional parameters from contract config (ignore_type_checking, max_depth)

    Returns:
        List of violations (empty for now)
    """
    # TODO: Implement circular import detection
    return []


# ==============================================================================
# Registry of built-in checks
# ==============================================================================

BUILTIN_CHECKS = {
    # Text patterns
    "todo_comments": check_todo_comments,
    "debug_statements": check_debug_statements,
    "hardcoded_secrets": check_hardcoded_secrets,

    # File operations
    "file_size": check_file_size,
    "line_length": check_line_length,
    "trailing_whitespace": check_trailing_whitespace,
    "mixed_line_endings": check_mixed_line_endings,

    # Architecture checks (AST-based)
    "layer_imports": check_layer_imports,
    "constructor_injection": check_constructor_injection,
    "domain_purity": check_domain_purity,
    "circular_imports": check_circular_imports,

    # Lineage/Audit trail
    "lineage_metadata": check_lineage_metadata,

    # Spec integrity and traceability
    "spec_integrity": check_spec_integrity,
    "bidirectional_links": check_bidirectional_links,
    "file_structure": check_file_structure,

    # Minimal Context Architecture
    "minimal_context_validation": check_minimal_context_validation,
}


def get_builtin_check(name: str):
    """Get a built-in check function by name."""
    return BUILTIN_CHECKS.get(name)


def list_builtin_checks() -> list[str]:
    """List all available built-in checks."""
    return list(BUILTIN_CHECKS.keys())
