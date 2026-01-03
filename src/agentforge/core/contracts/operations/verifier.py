# @spec_file: .agentforge/specs/core-contracts-v1.yaml
# @spec_id: core-contracts-v1
# @component_id: operation-contract-verifier

"""
Operation Contract Verifier
===========================

Executes operation contract rules against code, bridging the declarative
rules in operation contracts to the executable checks in the verification
infrastructure.

This creates the feedback loop: contracts → verification → violations → fixes.
"""

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .loader import OperationContractManager, OperationContract, OperationRule


@dataclass
class Violation:
    """A single contract violation."""

    rule_id: str
    rule_description: str
    contract_id: str
    file_path: str
    line_number: int | None
    message: str
    severity: str
    fix_hint: str | None = None

    def __str__(self) -> str:
        loc = f"{self.file_path}:{self.line_number}" if self.line_number else self.file_path
        return f"[{self.severity.upper()}] {loc}: {self.message}"


@dataclass
class VerificationReport:
    """Report from running operation contract verification."""

    contracts_checked: list[str] = field(default_factory=list)
    rules_checked: int = 0
    files_scanned: int = 0
    violations: list[Violation] = field(default_factory=list)

    @property
    def is_passed(self) -> bool:
        """Check passed if no errors (warnings allowed)."""
        return not any(v.severity == "error" for v in self.violations)

    @property
    def error_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "warning")

    @property
    def info_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "info")

    def violations_by_file(self) -> dict[str, list[Violation]]:
        """Group violations by file path."""
        by_file: dict[str, list[Violation]] = {}
        for v in self.violations:
            by_file.setdefault(v.file_path, []).append(v)
        return by_file

    def summary(self) -> str:
        """Generate human-readable summary."""
        parts = [
            f"Contracts: {len(self.contracts_checked)}",
            f"Rules: {self.rules_checked}",
            f"Files: {self.files_scanned}",
            f"Violations: {len(self.violations)} "
            f"({self.error_count} errors, {self.warning_count} warnings, {self.info_count} info)",
        ]
        return " | ".join(parts)


# =============================================================================
# Naming Check Helpers (extracted to reduce class complexity)
# =============================================================================

# Good prefixes for boolean names
_BOOL_PREFIXES = ("is_", "has_", "can_", "should_", "will_", "did_", "was_")

# Generic names to avoid
_BAD_NAMES = {"data", "info", "temp", "tmp", "val", "value", "item", "obj", "result", "res"}

# Allowed short names
_ALLOWED_SHORT = {"i", "j", "k", "x", "y", "z", "e", "f", "n", "_", "id", "db"}


def _has_bool_naming_issue(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Check if function returns bool and has non-compliant name."""
    if not node.returns or not isinstance(node.returns, ast.Name):
        return False
    if node.returns.id != "bool":
        return False
    # Strip leading underscores for private functions
    name = node.name.lstrip("_")
    return not name.startswith(_BOOL_PREFIXES)


def _check_bool_variable(node: ast.AnnAssign) -> str | None:
    """Check if annotated assignment is bool with non-compliant name. Returns name or None."""
    if not isinstance(node.annotation, ast.Name):
        return None
    if node.annotation.id != "bool":
        return None
    if not isinstance(node.target, ast.Name):
        return None
    name = node.target.id
    if name.startswith(_BOOL_PREFIXES) or name.startswith("_"):
        return None
    return name


def _is_name_too_short(name: str) -> bool:
    """Check if function name is too short."""
    if name.startswith("_"):
        return False
    return len(name) <= 2 and name not in _ALLOWED_SHORT


def _is_name_generic(name: str) -> bool:
    """Check if variable name is generic."""
    return name.lower() in _BAD_NAMES


def _create_violation(rule: OperationRule, contract: OperationContract, **details) -> Violation:
    """Create a Violation from rule/contract context and details."""
    return Violation(
        rule_id=rule.rule_id,
        rule_description=rule.description,
        contract_id=contract.contract_id,
        file_path=details.get("file_path", ""),
        line_number=details.get("line"),
        message=details.get("message", ""),
        severity=details.get("severity") or rule.severity or "warning",
        fix_hint=details.get("fix_hint"),
    )


# =============================================================================
# Main Verifier Class
# =============================================================================

class OperationContractVerifier:
    """
    Verifies code against operation contract rules.

    This bridges the gap between declarative operation contracts and
    executable verification checks.
    """

    def __init__(
        self,
        contract_manager: OperationContractManager | None = None,
        repo_root: Path | None = None,
    ):
        self.manager = contract_manager or OperationContractManager()
        self.repo_root = (repo_root or Path.cwd()).resolve()
        self._init_handlers()

    def _init_handlers(self) -> None:
        """Initialize check type handlers."""
        self._handlers: dict[str, Callable] = {
            "code_metric": self._check_code_metric,
            "safety_pattern": self._check_safety_pattern,
            "naming_convention": self._check_naming_convention,
        }
        # No hardcoded mapping - handlers read directly from rule.details

    def verify(
        self,
        path: Path,
        contract_ids: list[str] | None = None,
        check_types: list[str] | None = None,
    ) -> VerificationReport:
        """Verify code against operation contracts."""
        report = VerificationReport()
        file_paths = self._collect_files(path)
        report.files_scanned = len(file_paths)

        if not file_paths:
            return report

        contracts = self._get_contracts(contract_ids)
        report.contracts_checked = [c.contract_id for c in contracts]

        automatable = {"code_metric", "safety_pattern", "naming_convention"}
        active_types = set(check_types) if check_types else automatable

        self._run_checks(contracts, active_types, file_paths, report)
        return report

    def _run_checks(
        self,
        contracts: list[OperationContract],
        active_types: set[str],
        file_paths: list[Path],
        report: VerificationReport,
    ) -> None:
        """Run checks for all contracts and collect violations."""
        for contract in contracts:
            for rule in contract.rules:
                if rule.check_type not in active_types:
                    continue
                handler = self._handlers.get(rule.check_type)
                if not handler:
                    continue

                report.rules_checked += 1
                violations = handler(rule, contract, file_paths)
                report.violations.extend(violations)

    def verify_rule(self, rule_id: str, path: Path) -> VerificationReport:
        """Verify code against a single rule by ID."""
        report = VerificationReport()
        file_paths = self._collect_files(path)
        report.files_scanned = len(file_paths)

        for contract in self.manager.contracts.values():
            rule = contract.get_rule(rule_id)
            if rule:
                report.contracts_checked = [contract.contract_id]
                report.rules_checked = 1
                handler = self._handlers.get(rule.check_type)
                if handler:
                    report.violations.extend(handler(rule, contract, file_paths))
                break

        return report

    def _collect_files(self, path: Path) -> list[Path]:
        """Collect Python files to scan."""
        path = path.resolve()
        if path.is_file():
            return [path] if path.suffix == ".py" else []

        skip_dirs = {".", "venv", "__pycache__", "node_modules"}
        return [
            f.resolve() for f in path.rglob("*.py")
            if not any(p.startswith(".") or p in skip_dirs for p in f.parts)
        ]

    def _get_contracts(self, contract_ids: list[str] | None) -> list[OperationContract]:
        """Get contracts to check."""
        if contract_ids:
            return [self.manager.contracts[c] for c in contract_ids if c in self.manager.contracts]
        return list(self.manager.contracts.values())

    # =========================================================================
    # Check Type Handlers
    # =========================================================================

    def _check_code_metric(
        self,
        rule: OperationRule,
        contract: OperationContract,
        file_paths: list[Path],
    ) -> list[Violation]:
        """Handle code_metric rules - reads metric/threshold from rule.details."""
        from agentforge.core.contracts_ast import execute_ast_check
        from agentforge.core.contracts_execution import CheckContext

        details = rule.details or {}
        metric = details.get("metric")
        threshold = details.get("threshold", 10)

        if not metric:
            return []  # Rule doesn't specify which metric to check

        ctx = CheckContext(
            check_id=rule.rule_id, check_name=rule.description,
            severity=rule.severity or "warning",
            config={"metric": metric, "threshold": threshold},
            repo_root=self.repo_root, file_paths=file_paths, fix_hint=rule.rationale,
        )
        return self._results_to_violations(execute_ast_check(ctx), rule, contract)

    def _results_to_violations(self, results: list, rule: OperationRule, contract: OperationContract) -> list[Violation]:
        """Convert CheckResults to Violations."""
        return [
            Violation(
                rule_id=rule.rule_id, rule_description=rule.description,
                contract_id=contract.contract_id, file_path=r.file_path or "",
                line_number=r.line_number, message=r.message,
                severity=r.severity, fix_hint=rule.rationale,
            )
            for r in results if not r.passed
        ]

    def _check_safety_pattern(
        self,
        rule: OperationRule,
        contract: OperationContract,
        file_paths: list[Path],
    ) -> list[Violation]:
        """Handle safety_pattern rules."""
        if rule.rule_id != "no-secrets-in-code":
            return []

        from agentforge.core.builtin_checks import check_hardcoded_secrets
        return [
            Violation(
                rule_id=rule.rule_id,
                rule_description=rule.description,
                contract_id=contract.contract_id,
                file_path=r.get("file", ""),
                line_number=r.get("line"),
                message=r.get("message", ""),
                severity=r.get("severity", rule.severity or "error"),
                fix_hint=r.get("fix_hint"),
            )
            for r in check_hardcoded_secrets(self.repo_root, file_paths)
        ]

    def _check_naming_convention(
        self,
        rule: OperationRule,
        contract: OperationContract,
        file_paths: list[Path],
    ) -> list[Violation]:
        """Handle naming_convention rules."""
        if rule.rule_id == "boolean-naming":
            return self._check_boolean_naming(rule, contract, file_paths)
        if rule.rule_id == "descriptive-naming":
            return self._check_descriptive_naming(rule, contract, file_paths)
        return []

    def _check_boolean_naming(
        self,
        rule: OperationRule,
        contract: OperationContract,
        file_paths: list[Path],
    ) -> list[Violation]:
        """Check boolean variables have proper naming."""
        violations = []

        for file_path, tree in self._parse_files(file_paths):
            rel_path = str(file_path.relative_to(self.repo_root))

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if _has_bool_naming_issue(node):
                        violations.append(_create_violation(
                            rule, contract, file_path=rel_path, line=node.lineno,
                            message=f"Boolean function '{node.name}' should start with is_/has_/can_/should_",
                            fix_hint="Rename to express a yes/no question",
                        ))

                if isinstance(node, ast.AnnAssign):
                    name = _check_bool_variable(node)
                    if name:
                        violations.append(_create_violation(
                            rule, contract, file_path=rel_path, line=node.lineno,
                            message=f"Boolean variable '{name}' should start with is_/has_/can_/should_",
                            fix_hint="Rename to express a yes/no question",
                        ))

        return violations

    def _check_descriptive_naming(
        self,
        rule: OperationRule,
        contract: OperationContract,
        file_paths: list[Path],
    ) -> list[Violation]:
        """Check for non-descriptive names."""
        violations = []

        for file_path, tree in self._parse_files(file_paths):
            rel_path = str(file_path.relative_to(self.repo_root))
            violations.extend(self._find_naming_issues(tree, rule, contract, rel_path))

        return violations

    def _find_naming_issues(
        self, tree: ast.AST, rule: OperationRule, contract: OperationContract, rel_path: str
    ) -> list[Violation]:
        """Find naming issues in an AST tree."""
        violations = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and _is_name_too_short(node.name):
                violations.append(_create_violation(
                    rule, contract, file_path=rel_path, line=node.lineno,
                    message=f"Function name '{node.name}' is too short to be descriptive",
                    fix_hint="Use descriptive names that reveal intent",
                ))
            if isinstance(node, ast.Assign):
                generic_targets = [t.id for t in node.targets if isinstance(t, ast.Name) and _is_name_generic(t.id)]
                for name in generic_targets:
                    violations.append(_create_violation(
                        rule, contract, file_path=rel_path, line=node.lineno,
                        message=f"Variable name '{name}' is generic",
                        fix_hint="Name should describe what the variable contains", severity="info",
                    ))
        return violations

    # =========================================================================
    # Helpers
    # =========================================================================

    def _parse_files(self, file_paths: list[Path]):
        """Parse Python files and yield (path, tree) pairs."""
        for file_path in file_paths:
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(content, filename=str(file_path))
                yield file_path, tree
            except (SyntaxError, Exception):
                continue


# =============================================================================
# Convenience Function
# =============================================================================

def verify_operations(
    path: Path | str,
    contract_ids: list[str] | None = None,
    repo_root: Path | str | None = None,
) -> VerificationReport:
    """
    Verify code against operation contracts.

    Args:
        path: File or directory to verify
        contract_ids: Specific contracts to check (None = all)
        repo_root: Repository root (default: current directory)

    Returns:
        VerificationReport with violations
    """
    verifier = OperationContractVerifier(repo_root=Path(repo_root) if repo_root else None)
    return verifier.verify(Path(path), contract_ids=contract_ids)
