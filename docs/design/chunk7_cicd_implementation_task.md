# Implementation Task: Chunk 7 - CI/CD Integration

## Overview

Implement CI/CD integration for AgentForge. This enables automated conformance checking in pipelines with PR comments, baseline comparison, and multiple output formats.

**Read the full specification first:** `chunk7_cicd_specification.md`  
**Read design decisions:** `chunk7_cicd_design_decisions.md`

---

## Architecture Summary

```
tools/cicd/
├── __init__.py                 # Public exports
├── domain.py                   # Domain entities
├── runner.py                   # CI-optimized conformance runner
├── baseline.py                 # Baseline management
├── outputs/
│   ├── __init__.py
│   ├── sarif.py                # SARIF generator
│   ├── junit.py                # JUnit XML generator
│   └── markdown.py             # Markdown summary
├── platforms/
│   ├── __init__.py
│   ├── github.py               # GitHub Actions integration
│   └── azure.py                # Azure DevOps integration
└── config.py                   # CI configuration loader

cli/click_commands/ci.py        # CLI commands

templates/
├── github-workflow.yml         # GitHub Actions template
└── azure-pipeline.yml          # Azure DevOps template
```

---

## Phase 1: Domain Model

### 1.1 `tools/cicd/domain.py`

```python
"""
CI/CD Domain Model
==================

Domain entities for CI/CD integration.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any


class CIMode(Enum):
    """CI execution mode."""
    FULL = "full"              # Check entire codebase
    INCREMENTAL = "incremental" # Check only changed files
    PR = "pr"                   # PR mode with baseline comparison


class ExitCode(Enum):
    """CI exit codes."""
    SUCCESS = 0
    VIOLATIONS_FOUND = 1
    CONFIG_ERROR = 2
    RUNTIME_ERROR = 3
    BASELINE_NOT_FOUND = 4


@dataclass
class CIViolation:
    """A violation in CI context."""
    check_id: str
    rule_id: str
    file: Path
    line: Optional[int]
    column: Optional[int]
    message: str
    severity: str  # error | warning | info
    fix_hint: Optional[str] = None
    
    def to_sarif_result(self) -> Dict[str, Any]:
        """Convert to SARIF result format."""
        return {
            "ruleId": self.rule_id,
            "level": self.severity,
            "message": {"text": self.message},
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {"uri": str(self.file)},
                    "region": {
                        "startLine": self.line or 1,
                        "startColumn": self.column or 1,
                    }
                }
            }]
        }
    
    @property
    def hash(self) -> str:
        """Unique hash for baseline comparison."""
        import hashlib
        content = f"{self.check_id}:{self.file}:{self.line}:{self.message}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class BaselineEntry:
    """Entry in baseline file."""
    check_id: str
    file: str
    line: Optional[int]
    hash: str


@dataclass
class Baseline:
    """Baseline of known violations."""
    schema_version: str = "1.0"
    generated_at: datetime = field(default_factory=datetime.utcnow)
    commit: Optional[str] = None
    branch: Optional[str] = None
    entries: List[BaselineEntry] = field(default_factory=list)
    
    def contains(self, violation: CIViolation) -> bool:
        """Check if violation exists in baseline."""
        return any(e.hash == violation.hash for e in self.entries)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at.isoformat(),
            "commit": self.commit,
            "branch": self.branch,
            "summary": {
                "total_entries": len(self.entries),
            },
            "entries": [
                {
                    "check_id": e.check_id,
                    "file": e.file,
                    "line": e.line,
                    "hash": e.hash,
                }
                for e in self.entries
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Baseline":
        """Deserialize from dict."""
        return cls(
            schema_version=data.get("schema_version", "1.0"),
            generated_at=datetime.fromisoformat(data["generated_at"]),
            commit=data.get("commit"),
            branch=data.get("branch"),
            entries=[
                BaselineEntry(
                    check_id=e["check_id"],
                    file=e["file"],
                    line=e.get("line"),
                    hash=e["hash"],
                )
                for e in data.get("entries", [])
            ]
        )


@dataclass
class BaselineComparison:
    """Result of comparing violations against baseline."""
    new_violations: List[CIViolation] = field(default_factory=list)
    fixed_violations: List[BaselineEntry] = field(default_factory=list)
    existing_violations: List[CIViolation] = field(default_factory=list)
    
    @property
    def introduces_violations(self) -> bool:
        """True if PR introduces new violations."""
        return len(self.new_violations) > 0
    
    @property
    def net_change(self) -> int:
        """Net change in violation count."""
        return len(self.new_violations) - len(self.fixed_violations)
    
    @property
    def has_improvements(self) -> bool:
        """True if PR fixes some violations."""
        return len(self.fixed_violations) > 0


@dataclass
class CIResult:
    """Result of CI run."""
    mode: CIMode
    success: bool
    exit_code: ExitCode
    
    # Check results
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    
    # Violations
    violations: List[CIViolation] = field(default_factory=list)
    
    # Baseline comparison (PR mode)
    comparison: Optional[BaselineComparison] = None
    
    # Timing
    duration_seconds: float = 0.0
    
    # Metadata
    commit: Optional[str] = None
    branch: Optional[str] = None
    base_ref: Optional[str] = None
    
    @property
    def error_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "error")
    
    @property
    def warning_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "warning")


@dataclass
class CIConfig:
    """CI configuration."""
    default_mode: CIMode = CIMode.PR
    
    # Fail conditions
    fail_on_new_errors: bool = True
    fail_on_new_warnings: bool = False
    fail_on_total_errors_exceed: Optional[int] = None
    
    # Checks
    skip_checks: List[str] = field(default_factory=list)
    warn_only_checks: List[str] = field(default_factory=list)
    
    # Performance
    parallel_enabled: bool = True
    parallel_max_workers: int = 4
    cache_enabled: bool = True
    cache_ttl_hours: int = 24
    
    # Baseline
    baseline_file: str = ".agentforge/baseline.json"
    auto_update_baseline: bool = True
```

---

## Phase 2: CI Runner

### 2.1 `tools/cicd/runner.py`

```python
"""
CI Runner
=========

CI-optimized conformance check execution.
"""

import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional, Set

from .domain import CIMode, CIResult, CIViolation, CIConfig, ExitCode
from .baseline import BaselineManager


class CIRunner:
    """
    Optimized conformance runner for CI environments.
    
    Features:
    - Parallel check execution
    - Incremental checking (changed files only)
    - Caching for faster subsequent runs
    """
    
    def __init__(
        self,
        project_path: Path = Path("."),
        config: Optional[CIConfig] = None,
    ):
        self.project_path = project_path
        self.config = config or CIConfig()
        self.baseline_manager = BaselineManager(project_path)
    
    def run(
        self,
        mode: CIMode = CIMode.FULL,
        base_ref: Optional[str] = None,
        head_ref: Optional[str] = None,
    ) -> CIResult:
        """
        Run conformance checks in CI mode.
        
        Args:
            mode: Execution mode (full, incremental, pr)
            base_ref: Base reference for comparison
            head_ref: Head reference (default: HEAD)
        """
        start_time = time.time()
        
        # Determine files to check
        if mode in (CIMode.INCREMENTAL, CIMode.PR):
            changed_files = self._get_changed_files(base_ref, head_ref or "HEAD")
        else:
            changed_files = None  # Check all
        
        # Load checks and filter
        checks = self._load_checks()
        if changed_files is not None:
            checks = self._filter_checks_for_files(checks, changed_files)
        
        # Execute checks
        if self.config.parallel_enabled:
            violations = self._run_parallel(checks)
        else:
            violations = self._run_sequential(checks)
        
        # Apply warn-only overrides
        violations = self._apply_severity_overrides(violations)
        
        # Baseline comparison for PR mode
        comparison = None
        if mode == CIMode.PR:
            baseline = self.baseline_manager.load()
            if baseline:
                comparison = self.baseline_manager.compare(violations, baseline)
        
        # Determine success/exit code
        success, exit_code = self._determine_result(violations, comparison)
        
        duration = time.time() - start_time
        
        return CIResult(
            mode=mode,
            success=success,
            exit_code=exit_code,
            total_checks=len(checks),
            passed_checks=len(checks) - len(set(v.check_id for v in violations)),
            failed_checks=len(set(v.check_id for v in violations)),
            violations=violations,
            comparison=comparison,
            duration_seconds=duration,
            commit=self._get_current_commit(),
            branch=self._get_current_branch(),
            base_ref=base_ref,
        )
    
    def _get_changed_files(self, base_ref: str, head_ref: str) -> List[Path]:
        """Get files changed between refs."""
        result = subprocess.run(
            ["git", "diff", "--name-only", base_ref, head_ref],
            capture_output=True,
            text=True,
            cwd=self.project_path,
        )
        if result.returncode != 0:
            return []
        
        return [Path(f) for f in result.stdout.strip().split("\n") if f]
    
    def _load_checks(self) -> List:
        """Load all conformance checks."""
        # Import from conformance system
        from tools.conformance import ConformanceChecker
        
        checker = ConformanceChecker(self.project_path)
        return checker.load_all_checks()
    
    def _filter_checks_for_files(self, checks: List, files: List[Path]) -> List:
        """Filter checks to those applicable to changed files."""
        applicable = []
        file_set = set(str(f) for f in files)
        
        for check in checks:
            # Check if any file matches the check's applies_to patterns
            if self._check_applies_to_files(check, file_set):
                applicable.append(check)
        
        return applicable
    
    def _check_applies_to_files(self, check, file_set: Set[str]) -> bool:
        """Check if a check applies to any of the given files."""
        import fnmatch
        
        patterns = check.applies_to.get("paths", ["**/*"])
        for pattern in patterns:
            for file in file_set:
                if fnmatch.fnmatch(file, pattern):
                    return True
        return False
    
    def _run_parallel(self, checks: List) -> List[CIViolation]:
        """Run checks in parallel."""
        violations = []
        
        with ThreadPoolExecutor(max_workers=self.config.parallel_max_workers) as executor:
            futures = {executor.submit(self._run_single_check, check): check for check in checks}
            
            for future in as_completed(futures):
                try:
                    check_violations = future.result()
                    violations.extend(check_violations)
                except Exception as e:
                    check = futures[future]
                    # Log error but continue
                    print(f"Error running check {check.id}: {e}")
        
        return violations
    
    def _run_sequential(self, checks: List) -> List[CIViolation]:
        """Run checks sequentially."""
        violations = []
        for check in checks:
            try:
                check_violations = self._run_single_check(check)
                violations.extend(check_violations)
            except Exception as e:
                print(f"Error running check {check.id}: {e}")
        return violations
    
    def _run_single_check(self, check) -> List[CIViolation]:
        """Run a single check and return violations."""
        # Use existing conformance check execution
        from tools.conformance import CheckRunner
        
        runner = CheckRunner(self.project_path)
        result = runner.run_check(check)
        
        return [
            CIViolation(
                check_id=check.id,
                rule_id=check.id,
                file=Path(v.file),
                line=v.line,
                column=v.column,
                message=v.message,
                severity=check.severity,
                fix_hint=check.fix_hint,
            )
            for v in result.violations
        ]
    
    def _apply_severity_overrides(self, violations: List[CIViolation]) -> List[CIViolation]:
        """Apply warn-only overrides from config."""
        for v in violations:
            if v.check_id in self.config.warn_only_checks:
                v.severity = "warning"
        return violations
    
    def _determine_result(
        self, 
        violations: List[CIViolation],
        comparison: Optional["BaselineComparison"]
    ) -> tuple:
        """Determine success and exit code."""
        # PR mode: check new violations only
        if comparison is not None:
            new_errors = [v for v in comparison.new_violations if v.severity == "error"]
            new_warnings = [v for v in comparison.new_violations if v.severity == "warning"]
            
            if self.config.fail_on_new_errors and new_errors:
                return False, ExitCode.VIOLATIONS_FOUND
            if self.config.fail_on_new_warnings and new_warnings:
                return False, ExitCode.VIOLATIONS_FOUND
            
            return True, ExitCode.SUCCESS
        
        # Full/incremental mode: check all violations
        errors = [v for v in violations if v.severity == "error"]
        
        if self.config.fail_on_total_errors_exceed:
            if len(errors) > self.config.fail_on_total_errors_exceed:
                return False, ExitCode.VIOLATIONS_FOUND
        
        if errors:
            return False, ExitCode.VIOLATIONS_FOUND
        
        return True, ExitCode.SUCCESS
    
    def _get_current_commit(self) -> Optional[str]:
        """Get current git commit."""
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=self.project_path,
        )
        return result.stdout.strip() if result.returncode == 0 else None
    
    def _get_current_branch(self) -> Optional[str]:
        """Get current git branch."""
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            cwd=self.project_path,
        )
        return result.stdout.strip() if result.returncode == 0 else None
```

---

## Phase 3: Output Generators

### 3.1 `tools/cicd/outputs/sarif.py`

```python
"""
SARIF Output Generator
======================

Generate SARIF 2.1.0 compliant output for GitHub Code Scanning.
"""

import json
from pathlib import Path
from typing import List, Dict, Any

from ..domain import CIResult, CIViolation


class SARIFGenerator:
    """Generate SARIF output from CI results."""
    
    SARIF_VERSION = "2.1.0"
    SCHEMA_URI = "https://json.schemastore.org/sarif-2.1.0.json"
    
    def generate(self, result: CIResult) -> Dict[str, Any]:
        """Generate SARIF document."""
        return {
            "$schema": self.SCHEMA_URI,
            "version": self.SARIF_VERSION,
            "runs": [
                {
                    "tool": self._build_tool_section(),
                    "results": [v.to_sarif_result() for v in result.violations],
                    "invocations": [self._build_invocation(result)],
                }
            ]
        }
    
    def _build_tool_section(self) -> Dict[str, Any]:
        """Build SARIF tool section with rules."""
        return {
            "driver": {
                "name": "AgentForge",
                "version": "1.0.0",
                "informationUri": "https://github.com/maxxentropy/agentforge",
                "rules": self._build_rules(),
            }
        }
    
    def _build_rules(self) -> List[Dict[str, Any]]:
        """Build rule definitions."""
        # Load from conformance contracts
        from tools.conformance import ContractLoader
        
        rules = []
        contracts = ContractLoader().load_all()
        
        for contract in contracts:
            for check in contract.checks:
                rules.append({
                    "id": check.id,
                    "name": check.name,
                    "shortDescription": {"text": check.description},
                    "defaultConfiguration": {
                        "level": check.severity,
                    },
                    "helpUri": f"https://docs.agentforge.dev/checks/{check.id}",
                })
        
        return rules
    
    def _build_invocation(self, result: CIResult) -> Dict[str, Any]:
        """Build invocation metadata."""
        return {
            "executionSuccessful": result.success,
            "exitCode": result.exit_code.value,
        }
    
    def write(self, result: CIResult, output_path: Path) -> None:
        """Write SARIF to file."""
        sarif = self.generate(result)
        output_path.write_text(json.dumps(sarif, indent=2))
```

### 3.2 `tools/cicd/outputs/junit.py`

```python
"""
JUnit XML Output Generator
==========================

Generate JUnit XML for Azure DevOps and other CI systems.
"""

from pathlib import Path
from xml.etree import ElementTree as ET

from ..domain import CIResult


class JUnitGenerator:
    """Generate JUnit XML output."""
    
    def generate(self, result: CIResult) -> ET.Element:
        """Generate JUnit XML element."""
        testsuites = ET.Element("testsuites")
        testsuites.set("name", "AgentForge Conformance")
        testsuites.set("tests", str(result.total_checks))
        testsuites.set("failures", str(result.failed_checks))
        testsuites.set("errors", "0")
        testsuites.set("time", str(result.duration_seconds))
        
        # Group violations by check
        violations_by_check = {}
        for v in result.violations:
            if v.check_id not in violations_by_check:
                violations_by_check[v.check_id] = []
            violations_by_check[v.check_id].append(v)
        
        # Create testsuite for conformance
        testsuite = ET.SubElement(testsuites, "testsuite")
        testsuite.set("name", "conformance")
        testsuite.set("tests", str(result.total_checks))
        testsuite.set("failures", str(result.failed_checks))
        
        # Create testcase for each check
        for check_id, violations in violations_by_check.items():
            testcase = ET.SubElement(testsuite, "testcase")
            testcase.set("name", check_id)
            testcase.set("classname", "conformance")
            
            # Add failure element
            failure = ET.SubElement(testcase, "failure")
            failure.set("message", f"{len(violations)} violation(s)")
            failure.text = "\n".join([
                f"{v.file}:{v.line}: {v.message}"
                for v in violations
            ])
        
        return testsuites
    
    def write(self, result: CIResult, output_path: Path) -> None:
        """Write JUnit XML to file."""
        root = self.generate(result)
        tree = ET.ElementTree(root)
        tree.write(output_path, encoding="UTF-8", xml_declaration=True)
```

### 3.3 `tools/cicd/outputs/markdown.py`

```python
"""
Markdown Summary Generator
==========================

Generate Markdown for PR comments.
"""

from ..domain import CIResult, BaselineComparison


class MarkdownGenerator:
    """Generate Markdown summary."""
    
    def generate(self, result: CIResult) -> str:
        """Generate Markdown summary."""
        lines = [
            "## AgentForge Conformance Report",
            "",
            self._build_summary_table(result),
            "",
        ]
        
        if result.comparison:
            lines.extend(self._build_comparison_section(result.comparison))
        else:
            lines.extend(self._build_violations_section(result))
        
        lines.extend([
            "",
            "---",
            "*Powered by [AgentForge](https://github.com/maxxentropy/agentforge)*",
        ])
        
        return "\n".join(lines)
    
    def _build_summary_table(self, result: CIResult) -> str:
        """Build summary table."""
        status = "✅ Passed" if result.success else "❌ Failed"
        
        return f"""### Summary
| Metric | Value |
|--------|-------|
| Status | {status} |
| Checks Run | {result.total_checks} |
| Errors | {result.error_count} |
| Warnings | {result.warning_count} |
| Duration | {result.duration_seconds:.1f}s |"""
    
    def _build_comparison_section(self, comparison: BaselineComparison) -> list:
        """Build comparison section for PR mode."""
        lines = []
        
        # New violations
        if comparison.new_violations:
            lines.append("### ❌ New Violations (introduced in this PR)")
            lines.append("")
            lines.append("| Rule | File | Line | Message |")
            lines.append("|------|------|------|---------|")
            for v in comparison.new_violations[:10]:
                lines.append(f"| {v.check_id} | `{v.file}` | {v.line or '-'} | {v.message} |")
            if len(comparison.new_violations) > 10:
                lines.append(f"| ... | | | *+{len(comparison.new_violations) - 10} more* |")
            lines.append("")
        
        # Fixed violations
        if comparison.fixed_violations:
            lines.append(f"### 🎉 Fixed Violations ({len(comparison.fixed_violations)})")
            lines.append("")
            for v in comparison.fixed_violations[:5]:
                lines.append(f"- `{v.check_id}` in `{v.file}`")
            lines.append("")
        
        # Existing violations
        if comparison.existing_violations:
            lines.append(f"### ⚠️ Pre-existing Violations ({len(comparison.existing_violations)})")
            lines.append("")
            lines.append("<details>")
            lines.append("<summary>Click to expand</summary>")
            lines.append("")
            lines.append("| Rule | File | Message |")
            lines.append("|------|------|---------|")
            for v in comparison.existing_violations[:20]:
                lines.append(f"| {v.check_id} | `{v.file}` | {v.message} |")
            lines.append("")
            lines.append("</details>")
        
        return lines
    
    def _build_violations_section(self, result: CIResult) -> list:
        """Build violations section for full mode."""
        lines = []
        
        if result.violations:
            lines.append("### Violations")
            lines.append("")
            lines.append("| Rule | File | Line | Message |")
            lines.append("|------|------|------|---------|")
            for v in result.violations[:20]:
                lines.append(f"| {v.check_id} | `{v.file}` | {v.line or '-'} | {v.message} |")
            if len(result.violations) > 20:
                lines.append(f"| ... | | | *+{len(result.violations) - 20} more* |")
        else:
            lines.append("### ✅ No violations found!")
        
        return lines
```

---

## Phase 4: Baseline Management

### 4.1 `tools/cicd/baseline.py`

```python
"""
Baseline Management
===================

Manage baseline files for PR comparison.
"""

import json
from pathlib import Path
from typing import List, Optional

from .domain import Baseline, BaselineEntry, BaselineComparison, CIViolation


class BaselineManager:
    """Manage conformance baselines."""
    
    DEFAULT_PATH = Path(".agentforge/baseline.json")
    
    def __init__(self, project_path: Path = Path(".")):
        self.project_path = project_path
        self.baseline_path = project_path / self.DEFAULT_PATH
    
    def load(self, path: Optional[Path] = None) -> Optional[Baseline]:
        """Load baseline from file."""
        path = path or self.baseline_path
        
        if not path.exists():
            return None
        
        data = json.loads(path.read_text())
        return Baseline.from_dict(data)
    
    def save(self, baseline: Baseline, path: Optional[Path] = None) -> Path:
        """Save baseline to file."""
        path = path or self.baseline_path
        path.parent.mkdir(parents=True, exist_ok=True)
        
        path.write_text(json.dumps(baseline.to_dict(), indent=2))
        return path
    
    def create_from_violations(self, violations: List[CIViolation]) -> Baseline:
        """Create baseline from current violations."""
        import subprocess
        
        # Get current commit/branch
        commit_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True
        )
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True
        )
        
        entries = [
            BaselineEntry(
                check_id=v.check_id,
                file=str(v.file),
                line=v.line,
                hash=v.hash,
            )
            for v in violations
        ]
        
        return Baseline(
            commit=commit_result.stdout.strip() if commit_result.returncode == 0 else None,
            branch=branch_result.stdout.strip() if branch_result.returncode == 0 else None,
            entries=entries,
        )
    
    def compare(
        self, 
        violations: List[CIViolation], 
        baseline: Baseline
    ) -> BaselineComparison:
        """Compare current violations against baseline."""
        new_violations = []
        existing_violations = []
        
        current_hashes = {v.hash for v in violations}
        baseline_hashes = {e.hash for e in baseline.entries}
        
        # Categorize violations
        for v in violations:
            if v.hash in baseline_hashes:
                existing_violations.append(v)
            else:
                new_violations.append(v)
        
        # Find fixed violations
        fixed_violations = [
            e for e in baseline.entries
            if e.hash not in current_hashes
        ]
        
        return BaselineComparison(
            new_violations=new_violations,
            fixed_violations=fixed_violations,
            existing_violations=existing_violations,
        )
```

---

## Phase 5: CLI Commands

### 5.1 `cli/click_commands/ci.py`

```python
"""
CI CLI Commands
===============

Commands for CI/CD integration.
"""

import click
import sys
from pathlib import Path

from tools.cicd import CIRunner, CIMode, CIConfig
from tools.cicd.baseline import BaselineManager
from tools.cicd.outputs.sarif import SARIFGenerator
from tools.cicd.outputs.junit import JUnitGenerator
from tools.cicd.outputs.markdown import MarkdownGenerator


@click.group('ci', help='CI/CD integration commands')
def ci():
    """CI/CD integration commands."""
    pass


@ci.command('run')
@click.option('--mode', '-m', type=click.Choice(['full', 'incremental', 'pr']),
              default='full', help='Check mode')
@click.option('--base-ref', '-b', help='Base reference for comparison')
@click.option('--head-ref', '-h', help='Head reference (default: HEAD)')
@click.option('--output-sarif', type=click.Path(), help='Output SARIF file')
@click.option('--output-junit', type=click.Path(), help='Output JUnit XML file')
@click.option('--output-markdown', type=click.Path(), help='Output Markdown file')
@click.option('--output-json', type=click.Path(), help='Output JSON file')
@click.option('--fail-on', type=click.Choice(['error', 'warning', 'any']),
              default='error', help='When to fail')
@click.option('--parallel/--no-parallel', default=True, help='Run in parallel')
def run(mode, base_ref, head_ref, output_sarif, output_junit, output_markdown, output_json, fail_on, parallel):
    """Run conformance checks in CI mode."""
    config = CIConfig(
        parallel_enabled=parallel,
        fail_on_new_warnings=(fail_on in ('warning', 'any')),
    )
    
    runner = CIRunner(config=config)
    ci_mode = CIMode(mode)
    
    result = runner.run(
        mode=ci_mode,
        base_ref=base_ref,
        head_ref=head_ref,
    )
    
    # Generate outputs
    if output_sarif:
        SARIFGenerator().write(result, Path(output_sarif))
        click.echo(f"SARIF written to {output_sarif}")
    
    if output_junit:
        JUnitGenerator().write(result, Path(output_junit))
        click.echo(f"JUnit XML written to {output_junit}")
    
    if output_markdown:
        md = MarkdownGenerator().generate(result)
        Path(output_markdown).write_text(md)
        click.echo(f"Markdown written to {output_markdown}")
    
    if output_json:
        import json
        # Serialize result to JSON
        Path(output_json).write_text(json.dumps({
            "success": result.success,
            "violations": len(result.violations),
            "errors": result.error_count,
            "warnings": result.warning_count,
        }, indent=2))
    
    # Print summary
    status = "✅ PASSED" if result.success else "❌ FAILED"
    click.echo(f"\n{status}")
    click.echo(f"Checks: {result.passed_checks}/{result.total_checks} passed")
    click.echo(f"Violations: {result.error_count} errors, {result.warning_count} warnings")
    
    # Exit with appropriate code
    sys.exit(result.exit_code.value)


@ci.group('baseline')
def baseline():
    """Baseline management commands."""
    pass


@baseline.command('save')
@click.option('--output', '-o', type=click.Path(), help='Output file')
def baseline_save(output):
    """Save current violations as baseline."""
    runner = CIRunner()
    result = runner.run(mode=CIMode.FULL)
    
    manager = BaselineManager()
    baseline = manager.create_from_violations(result.violations)
    
    output_path = Path(output) if output else None
    saved_path = manager.save(baseline, output_path)
    
    click.echo(f"Baseline saved to {saved_path}")
    click.echo(f"Entries: {len(baseline.entries)}")


@baseline.command('compare')
@click.option('--baseline', '-b', type=click.Path(exists=True), required=True,
              help='Baseline file to compare against')
def baseline_compare(baseline):
    """Compare current state against baseline."""
    runner = CIRunner()
    result = runner.run(mode=CIMode.FULL)
    
    manager = BaselineManager()
    baseline_data = manager.load(Path(baseline))
    
    if not baseline_data:
        click.echo("Failed to load baseline", err=True)
        sys.exit(1)
    
    comparison = manager.compare(result.violations, baseline_data)
    
    click.echo(f"\nNew violations: {len(comparison.new_violations)}")
    click.echo(f"Fixed violations: {len(comparison.fixed_violations)}")
    click.echo(f"Existing violations: {len(comparison.existing_violations)}")
    
    if comparison.introduces_violations:
        sys.exit(1)


@ci.command('init')
@click.option('--platform', '-p', type=click.Choice(['github', 'azure', 'gitlab']),
              required=True, help='CI platform')
def init(platform):
    """Generate CI workflow files."""
    from importlib import resources
    
    if platform == 'github':
        output_dir = Path(".github/workflows")
        template_name = "github-workflow.yml"
        output_name = "agentforge.yml"
    elif platform == 'azure':
        output_dir = Path("azure-pipelines")
        template_name = "azure-pipeline.yml"
        output_name = "agentforge.yml"
    else:
        click.echo(f"Platform {platform} not yet supported", err=True)
        sys.exit(1)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / output_name
    
    # Load template (would be from package resources in real implementation)
    # For now, generate inline
    if platform == 'github':
        template = GITHUB_TEMPLATE
    else:
        template = AZURE_TEMPLATE
    
    output_path.write_text(template)
    click.echo(f"Created {output_path}")


# Templates would be loaded from package resources
GITHUB_TEMPLATE = """# AgentForge Conformance Check
name: AgentForge Conformance

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  conformance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install AgentForge
        run: pip install agentforge
      
      - name: Run Conformance Checks
        run: |
          agentforge ci run --mode pr \\
            --base-ref ${{ github.event.pull_request.base.sha || 'HEAD~1' }} \\
            --output-sarif results.sarif \\
            --output-markdown summary.md
        continue-on-error: true
      
      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: results.sarif
        if: always()
"""

AZURE_TEMPLATE = """# AgentForge Conformance Check
trigger:
  - main

pr:
  - main

pool:
  vmImage: 'ubuntu-latest'

steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: '3.11'
  
  - script: pip install agentforge
    displayName: 'Install AgentForge'
  
  - script: |
      agentforge ci run --mode full \\
        --output-junit results.xml
    displayName: 'Run Conformance Checks'
    continueOnError: true
  
  - task: PublishTestResults@2
    inputs:
      testResultsFormat: 'JUnit'
      testResultsFiles: 'results.xml'
"""
```

---

## Phase 6: Testing

### Test Structure

```
tests/unit/tools/cicd/
├── __init__.py
├── test_domain.py
├── test_runner.py
├── test_baseline.py
└── outputs/
    ├── test_sarif.py
    ├── test_junit.py
    └── test_markdown.py
```

---

## Validation Checklist

### Phase 1: Domain Model
- [ ] All domain entities serialize/deserialize correctly
- [ ] Exit codes cover all scenarios
- [ ] Baseline comparison logic is correct

### Phase 2: CI Runner
- [ ] Full mode runs all checks
- [ ] Incremental mode filters by changed files
- [ ] PR mode compares to baseline
- [ ] Parallel execution works

### Phase 3: Output Formats
- [ ] SARIF validates against schema
- [ ] JUnit XML parseable by CI tools
- [ ] Markdown renders correctly in GitHub

### Phase 4: Baseline
- [ ] Save creates valid baseline file
- [ ] Load parses baseline correctly
- [ ] Comparison identifies new/fixed/existing

### Phase 5: CLI
- [ ] All commands work
- [ ] Exit codes are correct
- [ ] Output files are created

### Phase 6: Integration
- [ ] GitHub Actions workflow works
- [ ] Azure DevOps pipeline works
- [ ] PR comments post correctly
