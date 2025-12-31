"""
Violation Tools
===============

Tools for reading and managing conformance violations.
These tools enable the agent to understand and fix violations.
"""

import fnmatch
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from .llm_executor_domain import ToolResult


@dataclass
class ViolationInfo:
    """Parsed violation information."""

    violation_id: str
    contract_id: str
    check_id: str
    severity: str
    file_path: str
    message: str
    fix_hint: Optional[str]
    status: str
    detected_at: str

    def to_summary(self) -> str:
        """Create human-readable summary."""
        return f"""Violation: {self.violation_id}
Severity: {self.severity}
File: {self.file_path}
Check: {self.check_id}
Message: {self.message}
Hint: {self.fix_hint or 'No hint available'}"""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "violation_id": self.violation_id,
            "contract_id": self.contract_id,
            "check_id": self.check_id,
            "severity": self.severity,
            "file_path": self.file_path,
            "message": self.message,
            "fix_hint": self.fix_hint,
            "status": self.status,
            "detected_at": self.detected_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ViolationInfo":
        """Deserialize from dict."""
        return cls(
            violation_id=data.get("violation_id", "unknown"),
            contract_id=data.get("contract_id", "unknown"),
            check_id=data.get("check_id", "unknown"),
            severity=data.get("severity", "major"),
            file_path=data.get("file_path", "unknown"),
            message=data.get("message", "No message"),
            fix_hint=data.get("fix_hint"),
            status=data.get("status", "open"),
            detected_at=data.get("detected_at", "unknown"),
        )


class ViolationTools:
    """
    Tools for working with conformance violations.

    Provides read-only access to violation data for the agent.
    """

    def __init__(self, project_path: Path):
        """
        Initialize violation tools.

        Args:
            project_path: Project root directory
        """
        self.project_path = Path(project_path)
        self.violations_dir = self.project_path / ".agentforge" / "violations"

    def read_violation(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """
        Read a specific violation by ID.

        Parameters:
            violation_id: The violation ID (e.g., "V-4734938a9485")

        Returns:
            ToolResult with violation details
        """
        violation_id = params.get("violation_id")
        if not violation_id:
            return ToolResult.failure_result(
                "read_violation", "Missing required parameter: violation_id"
            )

        # Normalize ID
        if not violation_id.startswith("V-"):
            violation_id = f"V-{violation_id}"

        violation_file = self.violations_dir / f"{violation_id}.yaml"

        if not violation_file.exists():
            return ToolResult.failure_result(
                "read_violation", f"Violation not found: {violation_id}"
            )

        try:
            with open(violation_file) as f:
                data = yaml.safe_load(f)

            info = ViolationInfo.from_dict(data)
            info.violation_id = violation_id  # Ensure ID is set

            return ToolResult.success_result("read_violation", info.to_summary())

        except Exception as e:
            return ToolResult.failure_result(
                "read_violation", f"Error reading violation: {e}"
            )

    def list_violations(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """
        List violations with optional filtering.

        Parameters:
            status: Filter by status ("open", "resolved", "all"). Default: "open"
            severity: Filter by severity ("blocker", "critical", "major", "minor")
            file_pattern: Filter by file path pattern (glob)
            limit: Maximum number to return. Default: 20

        Returns:
            ToolResult with list of violation summaries
        """
        status_filter = params.get("status", "open")
        severity_filter = params.get("severity")
        file_pattern = params.get("file_pattern")
        limit = params.get("limit", 20)

        if not self.violations_dir.exists():
            return ToolResult.success_result(
                "list_violations", "No violations directory found"
            )

        try:
            violations: List[Dict[str, Any]] = []

            for vfile in sorted(self.violations_dir.glob("V-*.yaml")):
                if len(violations) >= limit:
                    break

                with open(vfile) as f:
                    data = yaml.safe_load(f)

                # Apply filters
                if status_filter != "all" and data.get("status") != status_filter:
                    continue

                if severity_filter and data.get("severity") != severity_filter:
                    continue

                if file_pattern:
                    if not fnmatch.fnmatch(data.get("file_path", ""), file_pattern):
                        continue

                violations.append(
                    {
                        "id": data.get("violation_id", vfile.stem),
                        "severity": data.get("severity", "unknown"),
                        "file": data.get("file_path", "unknown"),
                        "check": data.get("check_id", "unknown"),
                        "message": data.get("message", "")[:80],  # Truncate
                    }
                )

            if not violations:
                return ToolResult.success_result(
                    "list_violations",
                    f"No violations found matching filters (status={status_filter})",
                )

            # Format as table
            lines = [f"Found {len(violations)} violations:"]
            lines.append("")
            lines.append(f"{'ID':<18} {'Severity':<10} {'File':<40} {'Message'}")
            lines.append("-" * 100)

            for v in violations:
                lines.append(
                    f"{v['id']:<18} {v['severity']:<10} {v['file']:<40} {v['message']}"
                )

            return ToolResult.success_result("list_violations", "\n".join(lines))

        except Exception as e:
            return ToolResult.failure_result(
                "list_violations", f"Error listing violations: {e}"
            )

    def get_violation_context(self, name: str, params: Dict[str, Any]) -> ToolResult:
        """
        Get full context for fixing a violation: violation details + file content.

        Parameters:
            violation_id: The violation ID

        Returns:
            ToolResult with violation info and relevant file content
        """
        violation_id = params.get("violation_id")
        if not violation_id:
            return ToolResult.failure_result(
                "get_violation_context", "Missing required parameter: violation_id"
            )

        # First read the violation
        result = self.read_violation("read_violation", {"violation_id": violation_id})
        if not result.success:
            return result

        # Parse to get file path
        if not violation_id.startswith("V-"):
            violation_id = f"V-{violation_id}"

        violation_file = self.violations_dir / f"{violation_id}.yaml"
        with open(violation_file) as f:
            data = yaml.safe_load(f)

        file_path = data.get("file_path")
        if not file_path:
            return ToolResult.failure_result(
                "get_violation_context", "Violation has no file_path"
            )

        # Read the source file
        source_file = self.project_path / file_path
        if not source_file.exists():
            file_content = f"[File not found: {file_path}]"
        else:
            try:
                file_content = source_file.read_text()
            except Exception as e:
                file_content = f"[Error reading file: {e}]"

        # Build context
        context = f"""=== VIOLATION DETAILS ===
{result.output}

=== FILE CONTENT: {file_path} ===
{file_content}

=== INSTRUCTIONS ===
Fix this violation by modifying the file to comply with the check.
The fix_hint provides guidance on what change is needed.
"""

        return ToolResult.success_result("get_violation_context", context)

    def get_tool_executors(self) -> Dict[str, Any]:
        """Get dict of tool executors for registration."""
        return {
            "read_violation": self.read_violation,
            "list_violations": self.list_violations,
            "get_violation_context": self.get_violation_context,
        }


# Tool definitions for prompt building
VIOLATION_TOOL_DEFINITIONS = [
    {
        "name": "read_violation",
        "description": "Read details of a specific conformance violation",
        "parameters": {
            "violation_id": {
                "type": "string",
                "required": True,
                "description": "Violation ID (e.g., V-4734938a9485)",
            }
        },
    },
    {
        "name": "list_violations",
        "description": "List conformance violations with optional filtering",
        "parameters": {
            "status": {
                "type": "string",
                "required": False,
                "description": "Filter by status: open, resolved, all (default: open)",
            },
            "severity": {
                "type": "string",
                "required": False,
                "description": "Filter by severity: blocker, critical, major, minor",
            },
            "file_pattern": {
                "type": "string",
                "required": False,
                "description": "Filter by file path pattern (glob)",
            },
            "limit": {
                "type": "integer",
                "required": False,
                "description": "Max violations to return (default: 20)",
            },
        },
    },
    {
        "name": "get_violation_context",
        "description": "Get full context for fixing a violation (details + file content)",
        "parameters": {
            "violation_id": {
                "type": "string",
                "required": True,
                "description": "Violation ID to get context for",
            }
        },
    },
]
