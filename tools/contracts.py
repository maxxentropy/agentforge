"""
Contract loading, resolution, and execution for AgentForge.

Contracts define machine-verifiable code correctness rules that can be:
- Inherited from builtin contracts (_base, _patterns-csharp, etc.)
- Defined at global, workspace, or repo level
- Exempted with documented justifications

This module handles:
- Contract discovery across all three tiers
- Inheritance resolution (extends keyword)
- Exemption loading and matching
- Check execution delegation
"""

import fnmatch
import os
import re
import subprocess
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import yaml

from tools.contracts_ast import execute_ast_check as _execute_ast_check
from tools.contracts_lsp import execute_lsp_query_check as _execute_lsp_query_check

# Builtin contracts directory (relative to this file)
BUILTIN_CONTRACTS_DIR = Path(__file__).parent.parent / "contracts" / "builtin"


@dataclass
class CheckResult:
    """Result of running a single check."""
    check_id: str
    check_name: str
    passed: bool
    severity: str  # error, warning, info
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    column: Optional[int] = None
    fix_hint: Optional[str] = None
    exempted: bool = False
    exemption_id: Optional[str] = None


@dataclass
class ContractResult:
    """Result of running all checks in a contract."""
    contract_name: str
    contract_type: str
    passed: bool
    check_results: List[CheckResult] = field(default_factory=list)

    @property
    def errors(self) -> List[CheckResult]:
        return [r for r in self.check_results if not r.passed and r.severity == "error" and not r.exempted]

    @property
    def warnings(self) -> List[CheckResult]:
        return [r for r in self.check_results if not r.passed and r.severity == "warning" and not r.exempted]

    @property
    def exempted_count(self) -> int:
        return len([r for r in self.check_results if r.exempted])


@dataclass
class Exemption:
    """Loaded exemption with scope information."""
    id: str
    contract: str
    checks: List[str]  # Check IDs covered
    reason: str
    approved_by: str
    scope_files: List[str] = field(default_factory=list)
    scope_functions: List[str] = field(default_factory=list)
    scope_lines: Dict[str, List[Tuple[int, int]]] = field(default_factory=dict)
    scope_global: bool = False
    expires: Optional[date] = None
    ticket: Optional[str] = None
    status: str = "active"

    def is_expired(self) -> bool:
        """Check if exemption has expired."""
        if self.expires is None:
            return False
        return date.today() > self.expires

    def is_active(self) -> bool:
        """Check if exemption is currently active."""
        return self.status == "active" and not self.is_expired()

    def covers_file(self, file_path: str) -> bool:
        """Check if exemption covers a specific file."""
        if self.scope_global:
            return True
        if not self.scope_files:
            return False
        # Normalize path for matching
        normalized = file_path.replace("\\", "/")
        for pattern in self.scope_files:
            if fnmatch.fnmatch(normalized, pattern):
                return True
        return False

    def covers_line(self, file_path: str, line_number: int) -> bool:
        """Check if exemption covers a specific line in a file."""
        if self.scope_global:
            return True
        if not self.covers_file(file_path):
            return False
        # If no line restrictions, file coverage is sufficient
        normalized = file_path.replace("\\", "/")
        if normalized not in self.scope_lines:
            return True
        # Check line ranges
        for start, end in self.scope_lines[normalized]:
            if start <= line_number <= end:
                return True
        return False


@dataclass
class Contract:
    """Loaded contract with resolved inheritance."""
    name: str
    type: str
    description: Optional[str] = None
    version: str = "1.0.0"
    enabled: bool = True
    extends: List[str] = field(default_factory=list)
    applies_to: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    checks: List[Dict[str, Any]] = field(default_factory=list)
    source_path: Optional[Path] = None
    tier: str = "repo"  # global, workspace, repo, builtin

    # Resolved parent contracts (populated by resolve_inheritance)
    _resolved: bool = False
    _inherited_checks: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def is_abstract(self) -> bool:
        """
        Check if this is an abstract contract (building block, not run directly).

        Abstract contracts are identified by underscore prefix in their name.
        They serve as templates/libraries to be extended by concrete contracts.
        Only concrete contracts (no underscore) are meant to be applied to projects.
        """
        return self.name.startswith("_")

    def all_checks(self) -> List[Dict[str, Any]]:
        """Get all checks including inherited ones."""
        if not self._resolved:
            return self.checks
        # Inherited checks first, then own checks (own checks can override)
        check_ids = set()
        result = []
        # Own checks take precedence
        for check in self.checks:
            check_ids.add(check.get("id"))
            result.append(check)
        # Add inherited checks not overridden
        for check in self._inherited_checks:
            if check.get("id") not in check_ids:
                result.append(check)
        return result


class ContractRegistry:
    """
    Registry for loading, resolving, and executing contracts.

    Handles:
    - Discovery across global/workspace/repo tiers
    - Builtin contract loading
    - Inheritance resolution
    - Exemption matching
    """

    def __init__(self, repo_root: Path, workspace_root: Optional[Path] = None,
                 global_root: Optional[Path] = None):
        """
        Initialize contract registry.

        Args:
            repo_root: Root directory of the repository
            workspace_root: Optional workspace contracts directory
            global_root: Optional global contracts directory (~/.agentforge/contracts)
        """
        self.repo_root = Path(repo_root)
        self.workspace_root = Path(workspace_root) if workspace_root else None
        self.global_root = Path(global_root) if global_root else None

        # Caches
        self._contracts: Dict[str, Contract] = {}
        self._exemptions: List[Exemption] = []
        self._loaded = False

    def discover_contracts(self) -> Dict[str, Contract]:
        """
        Discover and load all contracts from all tiers.

        Priority (later overrides earlier):
        1. Builtin contracts (_base, _patterns-*)
        2. Global contracts (~/.agentforge/contracts/)
        3. Workspace contracts
        4. Repo contracts

        Returns:
            Dict mapping contract name to Contract object
        """
        if self._loaded:
            return self._contracts

        # 1. Load builtin contracts
        self._load_contracts_from_dir(BUILTIN_CONTRACTS_DIR, tier="builtin")

        # 2. Load global contracts
        if self.global_root and self.global_root.exists():
            self._load_contracts_from_dir(self.global_root, tier="global")

        # 3. Load workspace contracts
        if self.workspace_root and self.workspace_root.exists():
            self._load_contracts_from_dir(self.workspace_root, tier="workspace")

        # 4. Load repo contracts
        repo_contracts = self.repo_root / "contracts"
        if repo_contracts.exists():
            self._load_contracts_from_dir(repo_contracts, tier="repo")

        # Also check .agentforge/contracts in repo
        agentforge_contracts = self.repo_root / ".agentforge" / "contracts"
        if agentforge_contracts.exists():
            self._load_contracts_from_dir(agentforge_contracts, tier="repo")

        self._loaded = True
        return self._contracts

    def _load_contracts_from_dir(self, directory: Path, tier: str):
        """Load all contract files from a directory."""
        if not directory.exists():
            return

        for yaml_file in directory.glob("**/*.contract.yaml"):
            try:
                contract = self._load_contract_file(yaml_file, tier)
                if contract:
                    self._contracts[contract.name] = contract
            except Exception as e:
                print(f"Warning: Failed to load contract {yaml_file}: {e}")

    def _load_contract_file(self, path: Path, tier: str) -> Optional[Contract]:
        """Load a single contract file."""
        with open(path, "r") as f:
            data = yaml.safe_load(f)

        if not data or "contract" not in data:
            return None

        contract_data = data["contract"]
        checks_data = data.get("checks", [])

        # Handle extends - normalize to list
        extends = contract_data.get("extends", [])
        if isinstance(extends, str):
            extends = [extends]

        return Contract(
            name=contract_data["name"],
            type=contract_data["type"],
            description=contract_data.get("description"),
            version=contract_data.get("version", "1.0.0"),
            enabled=contract_data.get("enabled", True),
            extends=extends,
            applies_to=contract_data.get("applies_to", {}),
            tags=contract_data.get("tags", []),
            checks=checks_data,
            source_path=path,
            tier=tier
        )

    def resolve_inheritance(self, contract: Contract) -> Contract:
        """
        Resolve inheritance chain for a contract.

        Populates _inherited_checks from parent contracts.
        """
        if contract._resolved:
            return contract

        inherited_checks = []
        visited = {contract.name}  # Prevent cycles

        for parent_name in contract.extends:
            # Resolve parent reference
            parent = self._resolve_contract_reference(parent_name)
            if parent is None:
                print(f"Warning: Contract '{contract.name}' extends unknown '{parent_name}'")
                continue

            if parent.name in visited:
                continue
            visited.add(parent.name)

            # Recursively resolve parent
            self.resolve_inheritance(parent)

            # Collect parent's checks (including its inherited ones)
            inherited_checks.extend(parent.all_checks())

        contract._inherited_checks = inherited_checks
        contract._resolved = True
        return contract

    def _resolve_contract_reference(self, reference: str) -> Optional[Contract]:
        """
        Resolve a contract reference to a Contract object.

        Reference formats:
        - "_base" - builtin contract
        - "workspace:name" - workspace contract
        - "./path.yaml" - relative path
        - "name" - lookup by name
        """
        # Builtin reference (starts with underscore)
        if reference.startswith("_"):
            return self._contracts.get(reference)

        # Workspace reference
        if reference.startswith("workspace:"):
            name = reference[10:]
            return self._contracts.get(name)

        # Relative path reference
        if reference.startswith("./") or reference.startswith("../"):
            # Would need context of referring contract to resolve
            # For now, try direct lookup
            pass

        # Direct name lookup
        return self._contracts.get(reference)

    def load_exemptions(self) -> List[Exemption]:
        """Load all exemption files from repo."""
        if self._exemptions:
            return self._exemptions

        # Check multiple locations
        exemption_dirs = [
            self.repo_root / "exemptions",
            self.repo_root / ".agentforge" / "exemptions",
            self.repo_root / "contracts" / "exemptions",
        ]

        for exemption_dir in exemption_dirs:
            if exemption_dir.exists():
                self._load_exemptions_from_dir(exemption_dir)

        return self._exemptions

    def _load_exemptions_from_dir(self, directory: Path):
        """Load all exemption files from a directory."""
        for yaml_file in directory.glob("**/*.exemptions.yaml"):
            try:
                with open(yaml_file, "r") as f:
                    data = yaml.safe_load(f)

                if not data or "exemptions" not in data:
                    continue

                for exemption_data in data["exemptions"]:
                    exemption = self._parse_exemption(exemption_data)
                    if exemption:
                        self._exemptions.append(exemption)
            except Exception as e:
                print(f"Warning: Failed to load exemptions from {yaml_file}: {e}")

    def _parse_exemption(self, data: Dict) -> Optional[Exemption]:
        """Parse exemption data into Exemption object."""
        # Normalize checks to list
        checks = data.get("check", [])
        if isinstance(checks, str):
            checks = [checks]

        # Parse scope
        scope = data.get("scope", {})
        scope_lines = {}
        if "lines" in scope:
            for file_path, ranges in scope["lines"].items():
                scope_lines[file_path] = [(r[0], r[1]) for r in ranges]

        # Parse expiration date
        expires = None
        if "expires" in data:
            try:
                expires = date.fromisoformat(data["expires"])
            except ValueError:
                pass

        return Exemption(
            id=data["id"],
            contract=data["contract"],
            checks=checks,
            reason=data["reason"],
            approved_by=data["approved_by"],
            scope_files=scope.get("files", []),
            scope_functions=scope.get("functions", []),
            scope_lines=scope_lines,
            scope_global=scope.get("global", False),
            expires=expires,
            ticket=data.get("ticket"),
            status=data.get("status", "active")
        )

    def find_exemption(self, contract_name: str, check_id: str,
                       file_path: Optional[str] = None,
                       line_number: Optional[int] = None) -> Optional[Exemption]:
        """
        Find an active exemption that covers a specific violation.

        Args:
            contract_name: Name of the contract
            check_id: ID of the check
            file_path: Optional file where violation occurred
            line_number: Optional line number of violation

        Returns:
            Exemption if found and active, None otherwise
        """
        self.load_exemptions()

        for exemption in self._exemptions:
            # Check contract match
            if exemption.contract != contract_name:
                continue

            # Check if this check is covered
            if check_id not in exemption.checks:
                continue

            # Check if exemption is active
            if not exemption.is_active():
                continue

            # Check scope if file provided
            if file_path:
                if line_number is not None:
                    if not exemption.covers_line(file_path, line_number):
                        continue
                elif not exemption.covers_file(file_path):
                    continue

            return exemption

        return None

    def _contract_matches_filters(self, contract: Contract, language: Optional[str],
                                   repo_type: Optional[str], include_abstract: bool) -> bool:
        """Check if a contract matches the specified filters."""
        if not contract.enabled:
            return False
        if not include_abstract and contract.is_abstract:
            return False
        applies_to = contract.applies_to
        if language and "languages" in applies_to and language not in applies_to["languages"]:
            return False
        if repo_type and "repo_types" in applies_to and repo_type not in applies_to["repo_types"]:
            return False
        return True

    def get_enabled_contracts(self, language: Optional[str] = None,
                              repo_type: Optional[str] = None,
                              include_abstract: bool = True) -> List[Contract]:
        """
        Get all enabled contracts, optionally filtered.

        Args:
            language: Filter by language (e.g., "csharp")
            repo_type: Filter by repo type (e.g., "service")
            include_abstract: If False, skip abstract contracts (underscore prefix)

        Returns:
            List of enabled contracts matching filters
        """
        self.discover_contracts()

        result = []
        for contract in self._contracts.values():
            if not self._contract_matches_filters(contract, language, repo_type, include_abstract):
                continue
            self.resolve_inheritance(contract)
            result.append(contract)

        return result

    def get_applicable_contracts(self, language: Optional[str] = None,
                                  repo_type: Optional[str] = None) -> List[Contract]:
        """
        Get concrete contracts that apply to this project.

        This is the primary method for running contract checks. It:
        1. Skips abstract contracts (underscore prefix) - they are building blocks only
        2. Returns only concrete contracts whose applies_to matches
        3. Each returned contract has its full inheritance chain resolved

        Abstract contracts (e.g., _base, _patterns-python) are templates meant
        to be extended. Concrete contracts (e.g., agentforge) are entry points
        meant to be applied to projects.

        Args:
            language: Filter by language (e.g., "python")
            repo_type: Filter by repo type (e.g., "service")

        Returns:
            List of concrete, applicable contracts with inheritance resolved
        """
        return self.get_enabled_contracts(
            language=language,
            repo_type=repo_type,
            include_abstract=False
        )

    def get_contract(self, name: str) -> Optional[Contract]:
        """Get a specific contract by name."""
        self.discover_contracts()
        contract = self._contracts.get(name)
        if contract:
            self.resolve_inheritance(contract)
        return contract


# ==============================================================================
# Check Execution
# ==============================================================================

def execute_check(check: Dict[str, Any], repo_root: Path,
                  file_paths: Optional[List[Path]] = None) -> List[CheckResult]:
    """
    Execute a single check against the repo or specific files.

    Args:
        check: Check configuration from contract
        repo_root: Repository root directory
        file_paths: Optional list of specific files to check

    Returns:
        List of CheckResult for any violations found
    """
    check_type = check.get("type")
    check_id = check.get("id", "unknown")
    check_name = check.get("name", check_id)
    severity = check.get("severity", "error")
    config = check.get("config", {})
    fix_hint = check.get("fix_hint")

    # Get files to check
    if file_paths is None:
        file_paths = _get_files_for_check(check, repo_root)

    # Dispatch to appropriate handler
    handlers = {
        "regex": _execute_regex_check,
        "lsp_query": _execute_lsp_query_check,
        "ast_check": _execute_ast_check,
        "command": _execute_command_check,
        "file_exists": _execute_file_exists_check,
        "custom": _execute_custom_check,
    }

    handler = handlers.get(check_type)
    if handler is None:
        return [CheckResult(
            check_id=check_id,
            check_name=check_name,
            passed=False,
            severity="error",
            message=f"Unknown check type: {check_type}"
        )]

    return handler(check_id, check_name, severity, config, repo_root, file_paths, fix_hint)


def _get_files_for_check(check: Dict[str, Any], repo_root: Path) -> List[Path]:
    """Get list of files this check should run against."""
    applies_to = check.get("applies_to", {})
    paths = applies_to.get("paths", ["**/*"])
    exclude_paths = applies_to.get("exclude_paths", [])

    # If check is in a contract, inherit contract's applies_to
    # (This would be handled by the caller)

    all_files = []
    for pattern in paths:
        all_files.extend(repo_root.glob(pattern))

    # Filter out excluded paths
    result = []
    for f in all_files:
        if not f.is_file():
            continue
        relative = str(f.relative_to(repo_root))
        excluded = False
        for exclude in exclude_paths:
            if fnmatch.fnmatch(relative, exclude):
                excluded = True
                break
        if not excluded:
            result.append(f)

    return result


def _compile_regex(pattern: str, multiline: bool, case_insensitive: bool):
    """Compile regex with flags. Returns (regex, error_message)."""
    flags = 0
    if multiline:
        flags |= re.MULTILINE | re.DOTALL
    if case_insensitive:
        flags |= re.IGNORECASE
    try:
        return re.compile(pattern, flags), None
    except re.error as e:
        return None, str(e)


def _check_forbid_matches(matches, content: str, check_id: str, check_name: str,
                          severity: str, file_path: Path, repo_root: Path,
                          fix_hint: Optional[str]) -> List[CheckResult]:
    """Generate results for forbidden pattern matches."""
    results = []
    for match in matches:
        line_num = content[:match.start()].count("\n") + 1
        results.append(CheckResult(
            check_id=check_id, check_name=check_name, passed=False, severity=severity,
            message=f"Forbidden pattern found: '{match.group()}'",
            file_path=str(file_path.relative_to(repo_root)), line_number=line_num, fix_hint=fix_hint
        ))
    return results


def _execute_regex_check(check_id: str, check_name: str, severity: str,
                         config: Dict, repo_root: Path, file_paths: List[Path],
                         fix_hint: Optional[str]) -> List[CheckResult]:
    """Execute a regex-based check."""
    pattern = config.get("pattern")
    mode = config.get("mode", "forbid")

    if not pattern:
        return [CheckResult(check_id=check_id, check_name=check_name, passed=False,
                           severity="error", message="Regex check missing 'pattern' in config")]

    regex, error = _compile_regex(pattern, config.get("multiline", False), config.get("case_insensitive", False))
    if error:
        return [CheckResult(check_id=check_id, check_name=check_name, passed=False,
                           severity="error", message=f"Invalid regex pattern: {error}")]

    results = []
    for file_path in file_paths:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        matches = list(regex.finditer(content))

        if mode == "forbid":
            results.extend(_check_forbid_matches(matches, content, check_id, check_name,
                                                  severity, file_path, repo_root, fix_hint))
        elif mode == "require" and not matches:
            results.append(CheckResult(
                check_id=check_id, check_name=check_name, passed=False, severity=severity,
                message=f"Required pattern not found: '{pattern}'",
                file_path=str(file_path.relative_to(repo_root)), fix_hint=fix_hint
            ))

    return results


def _execute_command_check(check_id: str, check_name: str, severity: str,
                           config: Dict, repo_root: Path, file_paths: List[Path],
                           fix_hint: Optional[str]) -> List[CheckResult]:
    """Execute a command-based check."""
    command = config.get("command")
    args = config.get("args", [])
    working_dir = config.get("working_dir")
    timeout = config.get("timeout", 60)
    expected_exit_code = config.get("expected_exit_code", 0)

    if not command:
        return [CheckResult(
            check_id=check_id, check_name=check_name, passed=False,
            severity="error", message="Command check missing 'command' in config"
        )]

    # Resolve working directory
    cwd = repo_root
    if working_dir:
        cwd = repo_root / working_dir

    try:
        result = subprocess.run(
            [command] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode != expected_exit_code:
            return [CheckResult(
                check_id=check_id,
                check_name=check_name,
                passed=False,
                severity=severity,
                message=f"Command failed with exit code {result.returncode}: {result.stderr or result.stdout}",
                fix_hint=fix_hint
            )]

        return []  # Passed

    except subprocess.TimeoutExpired:
        return [CheckResult(
            check_id=check_id, check_name=check_name, passed=False,
            severity=severity, message=f"Command timed out after {timeout}s"
        )]
    except FileNotFoundError:
        return [CheckResult(
            check_id=check_id, check_name=check_name, passed=False,
            severity=severity, message=f"Command not found: {command}"
        )]
    except Exception as e:
        return [CheckResult(
            check_id=check_id, check_name=check_name, passed=False,
            severity="error", message=f"Command execution failed: {e}"
        )]


def _execute_file_exists_check(check_id: str, check_name: str, severity: str,
                                config: Dict, repo_root: Path, file_paths: List[Path],
                                fix_hint: Optional[str]) -> List[CheckResult]:
    """Execute a file existence check."""
    required_files = config.get("required_files", [])
    forbidden_files = config.get("forbidden_files", [])

    results = []

    # Check required files
    for pattern in required_files:
        matches = list(repo_root.glob(pattern))
        if not matches:
            results.append(CheckResult(
                check_id=check_id,
                check_name=check_name,
                passed=False,
                severity=severity,
                message=f"Required file not found: '{pattern}'",
                fix_hint=fix_hint
            ))

    # Check forbidden files
    for pattern in forbidden_files:
        matches = list(repo_root.glob(pattern))
        for match in matches:
            results.append(CheckResult(
                check_id=check_id,
                check_name=check_name,
                passed=False,
                severity=severity,
                message=f"Forbidden file exists: '{match.relative_to(repo_root)}'",
                file_path=str(match.relative_to(repo_root)),
                fix_hint=fix_hint
            ))

    return results


def _execute_custom_check(check_id: str, check_name: str, severity: str,
                          config: Dict, repo_root: Path, file_paths: List[Path],
                          fix_hint: Optional[str]) -> List[CheckResult]:
    """Execute a custom Python check."""
    module_name = config.get("module")
    function_name = config.get("function")
    params = config.get("params", {})

    if not module_name or not function_name:
        return [CheckResult(
            check_id=check_id, check_name=check_name, passed=False,
            severity="error", message="Custom check missing 'module' or 'function' in config"
        )]

    try:
        # Import the module dynamically
        import importlib.util

        # Search paths for modules (in order of preference)
        search_paths = [
            repo_root / "contracts" / "checks" / f"{module_name}.py",
            repo_root / ".agentforge" / "checks" / f"{module_name}.py",
            # Builtin modules in the tools directory
            Path(__file__).parent / f"{module_name}.py",
        ]

        module_path = None
        for path in search_paths:
            if path.exists():
                module_path = path
                break

        if module_path is None:
            return [CheckResult(
                check_id=check_id, check_name=check_name, passed=False,
                severity="error", message=f"Custom check module not found: {module_name}"
            )]

        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Get the function
        func = getattr(module, function_name, None)
        if func is None:
            return [CheckResult(
                check_id=check_id, check_name=check_name, passed=False,
                severity="error", message=f"Function '{function_name}' not found in {module_name}"
            )]

        # Call the function
        # Expected signature: func(repo_root, file_paths, **params) -> List[Dict]
        violations = func(repo_root, file_paths, **params)

        results = []
        for v in violations:
            results.append(CheckResult(
                check_id=check_id,
                check_name=check_name,
                passed=False,
                severity=v.get("severity", severity),
                message=v.get("message", "Custom check violation"),
                file_path=v.get("file"),
                line_number=v.get("line"),
                fix_hint=v.get("fix_hint", fix_hint)
            ))

        return results

    except Exception as e:
        return [CheckResult(
            check_id=check_id, check_name=check_name, passed=False,
            severity="error", message=f"Custom check execution failed: {e}"
        )]


# ==============================================================================
# High-Level API
# ==============================================================================

def run_contract(contract: Contract, repo_root: Path,
                 registry: ContractRegistry,
                 file_paths: Optional[List[Path]] = None) -> ContractResult:
    """
    Run all checks in a contract.

    Args:
        contract: Contract to run
        repo_root: Repository root directory
        registry: ContractRegistry for exemption lookup
        file_paths: Optional specific files to check

    Returns:
        ContractResult with all check results
    """
    all_results = []

    for check in contract.all_checks():
        if not check.get("enabled", True):
            continue

        # Apply contract-level applies_to if check doesn't override
        effective_check = dict(check)
        if "applies_to" not in effective_check:
            effective_check["applies_to"] = contract.applies_to

        # Execute check
        check_results = execute_check(effective_check, repo_root, file_paths)

        # Check for exemptions
        for result in check_results:
            if not result.passed:
                exemption = registry.find_exemption(
                    contract.name,
                    result.check_id,
                    result.file_path,
                    result.line_number
                )
                if exemption:
                    result.exempted = True
                    result.exemption_id = exemption.id

        all_results.extend(check_results)

    # Determine overall pass/fail (only errors that aren't exempted count)
    passed = not any(
        r for r in all_results
        if not r.passed and r.severity == "error" and not r.exempted
    )

    return ContractResult(
        contract_name=contract.name,
        contract_type=contract.type,
        passed=passed,
        check_results=all_results
    )


def run_all_contracts(repo_root: Path,
                      workspace_root: Optional[Path] = None,
                      global_root: Optional[Path] = None,
                      language: Optional[str] = None,
                      repo_type: Optional[str] = None,
                      file_paths: Optional[List[Path]] = None,
                      include_abstract: bool = False) -> List[ContractResult]:
    """
    Run all applicable contracts for a repository.

    By default, only runs CONCRETE contracts (no underscore prefix).
    Abstract contracts (e.g., _base, _patterns-python) are building blocks
    meant to be extended, not run directly. Concrete contracts (e.g., agentforge)
    inherit from abstract contracts and are the entry points for projects.

    Args:
        repo_root: Repository root directory
        workspace_root: Optional workspace contracts directory
        global_root: Optional global contracts directory
        language: Filter by language
        repo_type: Filter by repo type
        file_paths: Optional specific files to check
        include_abstract: If True, also run abstract contracts (not recommended)

    Returns:
        List of ContractResult for each contract
    """
    registry = ContractRegistry(repo_root, workspace_root, global_root)

    if include_abstract:
        contracts = registry.get_enabled_contracts(language, repo_type, include_abstract=True)
    else:
        contracts = registry.get_applicable_contracts(language, repo_type)

    results = []
    for contract in contracts:
        result = run_contract(contract, repo_root, registry, file_paths)
        results.append(result)

    return results
