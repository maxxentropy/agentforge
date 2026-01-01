# @spec_file: .agentforge/specs/core-harness-v1.yaml
# @spec_id: core-harness-v1
# @component_id: core-harness-conformance_tools
# @test_path: tests/unit/harness/test_selfhosting_tools.py

"""
Conformance Tools
=================

Tools for running conformance checks and verifying fixes.

Key improvements in this version:
- `run_conformance_check`: Directly runs a specific check by ID (fast, structured)
- `get_check_definition`: Returns the check definition so agent understands requirements
- Original tools preserved for backwards compatibility
"""

import subprocess
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional

from .llm_executor_domain import ToolResult

# Import contracts system for direct check execution
try:
    from ..contracts_registry import ContractRegistry
    from ..contracts_execution import execute_check
    from ..contracts_types import CheckResult
except ImportError:
    from agentforge.core.contracts_registry import ContractRegistry
    from agentforge.core.contracts_execution import execute_check
    from agentforge.core.contracts_types import CheckResult


class ConformanceTools:
    """
    Tools for conformance checking.

    Enables agent to verify that fixes resolve violations.
    """

    def __init__(self, project_path: Path, timeout: int = 60):
        """
        Initialize conformance tools.

        Args:
            project_path: Project root directory
            timeout: Default timeout for commands in seconds
        """
        self.project_path = Path(project_path)
        self.timeout = timeout
        self._registry: Optional[ContractRegistry] = None
        self._check_cache: Dict[str, Dict[str, Any]] = {}

    def _get_registry(self) -> ContractRegistry:
        """Lazy-load the contract registry."""
        if self._registry is None:
            self._registry = ContractRegistry(self.project_path)
        return self._registry

    def _find_check_by_id(self, check_id: str) -> Optional[Dict[str, Any]]:
        """
        Find a check definition by its ID across all contracts.

        Args:
            check_id: The check ID to find

        Returns:
            Check definition dict or None
        """
        # Check cache first
        if check_id in self._check_cache:
            return self._check_cache[check_id]

        registry = self._get_registry()
        contracts = registry.get_enabled_contracts()

        for contract in contracts:
            for check in contract.all_checks():
                if check.get("id") == check_id:
                    self._check_cache[check_id] = check
                    return check

        return None

    def check_file(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """
        Run conformance check on a specific file.

        Parameters:
            file_path: Path to file to check

        Returns:
            ToolResult with check results
        """
        file_path = params.get("file_path")
        if not file_path:
            return ToolResult.failure_result(
                "check_file", "Missing required parameter: file_path"
            )

        try:
            # Run conformance check via CLI
            cmd = [
                "python",
                "execute.py",
                "conformance",
                "check",
                "--file",
                file_path,
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=str(self.project_path),
            )

            if result.returncode == 0:
                # Parse output for violations
                if "No violations" in result.stdout or "0 violations" in result.stdout:
                    return ToolResult.success_result(
                        "check_file", f"No violations found in {file_path}"
                    )
                else:
                    return ToolResult.success_result(
                        "check_file", f"Violations found:\n{result.stdout}"
                    )
            else:
                return ToolResult.failure_result(
                    "check_file", f"Check failed: {result.stderr or result.stdout}"
                )

        except subprocess.TimeoutExpired:
            return ToolResult.failure_result(
                "check_file", f"Conformance check timed out ({self.timeout}s)"
            )
        except Exception as e:
            return ToolResult.failure_result("check_file", f"Error running check: {e}")

    def verify_violation_fixed(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """
        Verify that a specific violation has been fixed.

        Parameters:
            violation_id: The violation ID to verify

        Returns:
            ToolResult indicating if violation is resolved
        """
        violation_id = params.get("violation_id")
        if not violation_id:
            return ToolResult.failure_result(
                "verify_violation_fixed", "Missing required parameter: violation_id"
            )

        if not violation_id.startswith("V-"):
            violation_id = f"V-{violation_id}"

        # Read current violation status
        violations_dir = self.project_path / ".agentforge" / "violations"
        violation_file = violations_dir / f"{violation_id}.yaml"

        if not violation_file.exists():
            return ToolResult.failure_result(
                "verify_violation_fixed", f"Violation file not found: {violation_id}"
            )

        try:
            with open(violation_file) as f:
                data = yaml.safe_load(f)

            file_path = data.get("file_path")
            check_id = data.get("check_id")

            # Run conformance check on the file
            check_result = self.check_file("check_file", {"file_path": file_path})

            if not check_result.success:
                return check_result

            # Check if this specific violation still exists
            if violation_id in str(check_result.output) or check_id in str(
                check_result.output
            ):
                return ToolResult.failure_result(
                    "verify_violation_fixed",
                    f"Violation {violation_id} still present after fix attempt",
                )

            return ToolResult.success_result(
                "verify_violation_fixed",
                f"Violation {violation_id} appears to be fixed",
            )

        except Exception as e:
            return ToolResult.failure_result(
                "verify_violation_fixed", f"Error verifying fix: {e}"
            )

    def run_full_check(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """
        Run full conformance check on the project.

        Parameters:
            None

        Returns:
            ToolResult with summary of all violations
        """
        try:
            cmd = ["python", "execute.py", "conformance", "check"]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes for full check
                cwd=str(self.project_path),
            )

            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]: {result.stderr}"

            # Limit output size
            if len(output) > 5000:
                output = output[:5000] + "\n... (output truncated)"

            return ToolResult.success_result("run_full_check", output)

        except subprocess.TimeoutExpired:
            return ToolResult.failure_result(
                "run_full_check", "Full conformance check timed out (5 min)"
            )
        except Exception as e:
            return ToolResult.failure_result("run_full_check", f"Error running check: {e}")

    def run_conformance_check(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """
        Run a specific conformance check by ID on a file.

        This directly executes the check that detected the violation,
        allowing precise verification of fixes.

        Parameters:
            check_id: The check ID (e.g., 'max-cyclomatic-complexity')
            file_path: Path to the file to check

        Returns:
            ToolResult with pass/fail and any violations found
        """
        check_id = params.get("check_id")
        file_path = params.get("file_path")

        if not check_id:
            return ToolResult.failure_result(
                "run_conformance_check", "Missing required parameter: check_id"
            )

        if not file_path:
            return ToolResult.failure_result(
                "run_conformance_check", "Missing required parameter: file_path"
            )

        # Find the check definition
        check = self._find_check_by_id(check_id)
        if not check:
            return ToolResult.failure_result(
                "run_conformance_check",
                f"Check not found: '{check_id}'. Ensure it's defined in a contract."
            )

        # Resolve file path
        target_path = self.project_path / file_path
        if not target_path.exists():
            return ToolResult.failure_result(
                "run_conformance_check", f"File not found: {file_path}"
            )

        try:
            # Execute the check directly
            results: List[CheckResult] = execute_check(
                check, self.project_path, [target_path]
            )

            # Format results
            if not results:
                return ToolResult.success_result(
                    "run_conformance_check",
                    f"✓ Check '{check_id}' PASSED for {file_path}\n"
                    "No violations found."
                )

            # Check has violations
            violations = []
            for r in results:
                if not r.passed:
                    v_str = f"- Line {r.line_number or '?'}: {r.message}"
                    if r.fix_hint:
                        v_str += f"\n  Hint: {r.fix_hint}"
                    violations.append(v_str)

            if violations:
                output_msg = (
                    f"✗ Check '{check_id}' FAILED for {file_path}\n"
                    f"Violations ({len(violations)}):\n" + "\n".join(violations)
                )
                return ToolResult(
                    tool_name="run_conformance_check",
                    success=False,
                    output=output_msg,
                    error=f"Check failed with {len(violations)} violation(s)",
                )
            else:
                return ToolResult.success_result(
                    "run_conformance_check",
                    f"✓ Check '{check_id}' PASSED for {file_path}"
                )

        except Exception as e:
            return ToolResult.failure_result(
                "run_conformance_check", f"Error executing check: {e}"
            )

    def get_check_definition(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """
        Get the definition of a conformance check.

        Helps understand what a check requires before attempting fixes.

        Parameters:
            check_id: The check ID to look up

        Returns:
            ToolResult with check definition including type, config, and fix_hint
        """
        check_id = params.get("check_id")

        if not check_id:
            return ToolResult.failure_result(
                "get_check_definition", "Missing required parameter: check_id"
            )

        check = self._find_check_by_id(check_id)
        if not check:
            # List available checks to help
            registry = self._get_registry()
            contracts = registry.get_enabled_contracts()
            available_ids = set()
            for contract in contracts:
                for c in contract.all_checks():
                    if c.get("enabled", True):
                        available_ids.add(c.get("id", "unknown"))

            return ToolResult.failure_result(
                "get_check_definition",
                f"Check not found: '{check_id}'\n"
                f"Available checks: {', '.join(sorted(available_ids)[:10])}"
                + ("..." if len(available_ids) > 10 else "")
            )

        # Format the check definition
        definition = {
            "id": check.get("id"),
            "name": check.get("name", check.get("id")),
            "type": check.get("type"),
            "severity": check.get("severity", "warning"),
            "enabled": check.get("enabled", True),
        }

        if check.get("description"):
            definition["description"] = check["description"]

        if check.get("config"):
            definition["config"] = check["config"]

        if check.get("fix_hint"):
            definition["fix_hint"] = check["fix_hint"]

        if check.get("applies_to"):
            definition["applies_to"] = check["applies_to"]

        # Format as YAML for readability
        output = yaml.dump(definition, default_flow_style=False, sort_keys=False)

        return ToolResult.success_result(
            "get_check_definition",
            f"Check Definition for '{check_id}':\n{output}"
        )

    def get_tool_executors(self) -> Dict[str, Any]:
        """Get dict of tool executors for registration."""
        return {
            "check_file": self.check_file,
            "verify_violation_fixed": self.verify_violation_fixed,
            "run_full_check": self.run_full_check,
            # New domain-specific tools
            "run_conformance_check": self.run_conformance_check,
            "get_check_definition": self.get_check_definition,
        }


# Tool definitions for prompt building
CONFORMANCE_TOOL_DEFINITIONS = [
    {
        "name": "run_conformance_check",
        "description": "Run a specific conformance check by ID on a file. Use this to verify fixes.",
        "parameters": {
            "check_id": {
                "type": "string",
                "required": True,
                "description": "Check ID (e.g., 'max-cyclomatic-complexity')",
            },
            "file_path": {
                "type": "string",
                "required": True,
                "description": "Path to file to check",
            },
        },
    },
    {
        "name": "get_check_definition",
        "description": "Get the definition of a check to understand what it requires",
        "parameters": {
            "check_id": {
                "type": "string",
                "required": True,
                "description": "Check ID to look up",
            }
        },
    },
    {
        "name": "check_file",
        "description": "Run all conformance checks on a specific file (slower)",
        "parameters": {
            "file_path": {
                "type": "string",
                "required": True,
                "description": "Path to file to check",
            }
        },
    },
    {
        "name": "verify_violation_fixed",
        "description": "Verify that a specific violation has been fixed",
        "parameters": {
            "violation_id": {
                "type": "string",
                "required": True,
                "description": "Violation ID to verify",
            }
        },
    },
    {
        "name": "run_full_check",
        "description": "Run full conformance check on the entire project",
        "parameters": {},
    },
]
