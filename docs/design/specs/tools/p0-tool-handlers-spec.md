# P0 Tool Handlers Implementation Specification

**Version:** 1.1
**Status:** Implemented
**Date:** January 2026
**Scope:** Implementation specs for `edit_file`, `run_check`, `search_code`, `cannot_fix` handlers

---

## Executive Summary

This specification defines the implementation of four critical tool handlers required for the `fix_violation` workflow to function. These handlers bridge the LLM's native tool calls to executable actions.

### P0 Tool Handlers

| Tool | Purpose | Wraps |
|------|---------|-------|
| `edit_file` | Targeted line edits without full rewrites | New implementation |
| `run_check` | Re-run conformance check after fix | `ConformanceManager` |
| `search_code` | Find related code for context | `VectorSearch` + regex |
| `cannot_fix` | Proper escalation when fix impossible | `EscalationManager` |

### Design Principles

1. **Wrap existing infrastructure** - Don't reinvent; integrate
2. **Return structured results** - LLM needs clear success/failure + context
3. **Fail gracefully** - Return errors as tool results, not exceptions
4. **Audit everything** - All tool executions logged for replay

---

## Part 1: edit_file Handler

### 1.1 Purpose

Replace specific lines in a file without rewriting the entire file. This is more precise than `write_file` and produces cleaner diffs.

### 1.2 Tool Definition (Already Exists)

```python
EDIT_FILE = ToolDefinition(
    name="edit_file",
    description="Edit specific lines in a file. Replaces lines between start_line and end_line with new content.",
    input_schema={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file to edit"},
            "start_line": {"type": "integer", "description": "Starting line number (1-indexed)"},
            "end_line": {"type": "integer", "description": "Ending line number (1-indexed, inclusive)"},
            "new_content": {"type": "string", "description": "The new content to insert"},
        },
        "required": ["path", "start_line", "end_line", "new_content"],
    },
)
```

### 1.3 Handler Implementation

```python
# Location: src/agentforge/core/harness/minimal_context/tool_handlers.py

def create_edit_file_handler(project_path: Path = None) -> ActionHandler:
    """
    Create an edit_file action handler.
    
    Replaces lines start_line through end_line (inclusive) with new_content.
    
    Args:
        project_path: Base path for relative file paths
        
    Returns:
        Handler function that takes params dict and returns result string
    """
    base_path = Path(project_path) if project_path else Path.cwd()
    
    def handler(params: Dict[str, Any]) -> str:
        path = params.get("path", "")
        start_line = params.get("start_line", 0)
        end_line = params.get("end_line", 0)
        new_content = params.get("new_content", "")
        
        # Validate parameters
        if not path:
            return "ERROR: path parameter required"
        if start_line < 1:
            return "ERROR: start_line must be >= 1"
        if end_line < start_line:
            return "ERROR: end_line must be >= start_line"
        
        # Resolve file path
        file_path = Path(path)
        if not file_path.is_absolute():
            file_path = base_path / file_path
        
        # Check file exists
        if not file_path.exists():
            return f"ERROR: File not found: {file_path}"
        if not file_path.is_file():
            return f"ERROR: Not a file: {file_path}"
        
        try:
            # Read current content
            lines = file_path.read_text().splitlines(keepends=True)
            original_line_count = len(lines)
            
            # Validate line numbers against file
            if start_line > original_line_count:
                return f"ERROR: start_line {start_line} exceeds file length {original_line_count}"
            
            # Adjust end_line if beyond file (allow appending)
            effective_end = min(end_line, original_line_count)
            
            # Build new content
            # Convert 1-indexed to 0-indexed
            before = lines[:start_line - 1]
            after = lines[effective_end:]
            
            # Ensure new_content ends with newline if it has content
            new_lines = new_content.splitlines(keepends=True)
            if new_lines and not new_lines[-1].endswith('\n'):
                new_lines[-1] += '\n'
            
            # Combine
            result_lines = before + new_lines + after
            
            # Write back
            file_path.write_text(''.join(result_lines))
            
            # Calculate diff stats
            lines_removed = effective_end - start_line + 1
            lines_added = len(new_lines)
            
            return (
                f"SUCCESS: Edited {file_path.name}\n"
                f"  Lines {start_line}-{effective_end} replaced ({lines_removed} lines → {lines_added} lines)\n"
                f"  File now has {len(result_lines)} lines"
            )
            
        except PermissionError:
            return f"ERROR: Permission denied: {file_path}"
        except Exception as e:
            return f"ERROR: Failed to edit file: {e}"
    
    return handler
```

### 1.4 Test Cases

```python
# Location: tests/unit/harness/test_tool_handlers.py

class TestEditFileHandler:
    """Tests for edit_file handler."""
    
    def test_replace_single_line(self, temp_file):
        """Replace a single line in the middle of a file."""
        temp_file.write_text("line1\nline2\nline3\n")
        handler = create_edit_file_handler(temp_file.parent)
        
        result = handler({
            "path": temp_file.name,
            "start_line": 2,
            "end_line": 2,
            "new_content": "replaced",
        })
        
        assert "SUCCESS" in result
        assert temp_file.read_text() == "line1\nreplaced\nline3\n"
    
    def test_replace_multiple_lines(self, temp_file):
        """Replace multiple lines with different count."""
        temp_file.write_text("a\nb\nc\nd\n")
        handler = create_edit_file_handler(temp_file.parent)
        
        result = handler({
            "path": temp_file.name,
            "start_line": 2,
            "end_line": 3,
            "new_content": "X\nY\nZ",
        })
        
        assert "SUCCESS" in result
        assert temp_file.read_text() == "a\nX\nY\nZ\nd\n"
    
    def test_insert_at_beginning(self, temp_file):
        """Insert at line 1."""
        temp_file.write_text("existing\n")
        handler = create_edit_file_handler(temp_file.parent)
        
        result = handler({
            "path": temp_file.name,
            "start_line": 1,
            "end_line": 1,
            "new_content": "new first line",
        })
        
        assert "SUCCESS" in result
        assert temp_file.read_text() == "new first line\n"
    
    def test_file_not_found(self, tmp_path):
        """Error on missing file."""
        handler = create_edit_file_handler(tmp_path)
        
        result = handler({
            "path": "nonexistent.py",
            "start_line": 1,
            "end_line": 1,
            "new_content": "x",
        })
        
        assert "ERROR" in result
        assert "not found" in result.lower()
    
    def test_invalid_line_numbers(self, temp_file):
        """Error on invalid line numbers."""
        temp_file.write_text("line\n")
        handler = create_edit_file_handler(temp_file.parent)
        
        result = handler({
            "path": temp_file.name,
            "start_line": 5,
            "end_line": 3,
            "new_content": "x",
        })
        
        assert "ERROR" in result
```

---

## Part 2: run_check Handler

### 2.1 Purpose

Re-run conformance checking after a fix to verify the violation is resolved. Returns pass/fail with details.

### 2.2 Tool Definition (Already Exists)

```python
RUN_CHECK = ToolDefinition(
    name="run_check",
    description="Run a conformance check to verify the fix. Returns pass/fail and details.",
    input_schema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to check (optional, checks all if not specified)",
            },
            "check_type": {
                "type": "string",
                "description": "Type of check to run (e.g., 'complexity', 'style', 'type')",
            },
        },
        "required": [],
    },
)
```

### 2.3 Handler Implementation

```python
# Location: src/agentforge/core/harness/minimal_context/tool_handlers.py

def create_run_check_handler(project_path: Path = None) -> ActionHandler:
    """
    Create a run_check action handler.
    
    Wraps ConformanceManager to re-run verification checks.
    
    Args:
        project_path: Project root path
        
    Returns:
        Handler function
    """
    base_path = Path(project_path) if project_path else Path.cwd()
    
    def handler(params: Dict[str, Any]) -> str:
        from tools.conformance.manager import ConformanceManager
        from tools.verification_runner import VerificationRunner
        
        file_path = params.get("file_path")
        check_type = params.get("check_type")
        
        try:
            # Initialize managers
            conformance = ConformanceManager(base_path)
            runner = VerificationRunner(project_root=base_path)
            
            # Determine which checks to run
            if check_type:
                # Run specific check type
                checks_to_run = [check_type]
            else:
                # Run all configured checks
                checks_to_run = None  # Will use profile default
            
            # Run verification
            results = runner.run_profile(
                profile="full" if not checks_to_run else None,
                checks=checks_to_run,
                files=[file_path] if file_path else None,
            )
            
            # Count violations
            violations = [r for r in results if r.get("status") == "fail"]
            passes = [r for r in results if r.get("status") == "pass"]
            
            if not violations:
                return (
                    f"✓ CHECK PASSED\n"
                    f"  Checks run: {len(results)}\n"
                    f"  All passing"
                )
            else:
                # Format violation details
                details = []
                for v in violations[:5]:  # Limit to 5 for context
                    details.append(
                        f"  - {v.get('check_id')}: {v.get('message')} "
                        f"({v.get('file')}:{v.get('line', '?')})"
                    )
                
                remaining = len(violations) - 5
                if remaining > 0:
                    details.append(f"  ... and {remaining} more")
                
                return (
                    f"✗ CHECK FAILED\n"
                    f"  Violations: {len(violations)}\n"
                    f"  Passing: {len(passes)}\n"
                    f"  Details:\n" + "\n".join(details)
                )
                
        except FileNotFoundError as e:
            return f"ERROR: Configuration not found: {e}"
        except Exception as e:
            return f"ERROR: Check failed: {e}"
    
    return handler
```

### 2.4 Enhanced Version with Violation Focus

For `fix_violation` workflow, we often want to check if a *specific* violation is fixed:

```python
def create_run_check_handler_v2(project_path: Path = None) -> ActionHandler:
    """
    Enhanced run_check handler with violation-specific checking.
    
    Can verify a specific violation ID was resolved or run general checks.
    """
    base_path = Path(project_path) if project_path else Path.cwd()
    
    def handler(params: Dict[str, Any]) -> str:
        from tools.conformance.manager import ConformanceManager
        from tools.conformance.domain import ViolationStatus
        
        file_path = params.get("file_path")
        check_type = params.get("check_type")
        violation_id = params.get("violation_id")  # Optional: specific violation to check
        
        # Get context from working memory if available
        context = params.get("_context", {})
        target_violation = context.get("violation_id") or violation_id
        
        try:
            conformance = ConformanceManager(base_path)
            
            # If we have a target violation, check if it's resolved
            if target_violation:
                # Load current violation state
                violation = conformance.violation_store.get(target_violation)
                
                if violation is None:
                    return f"ERROR: Violation {target_violation} not found"
                
                # Re-run check for the specific file
                target_file = file_path or violation.file_path
                
                # Run verification on the file
                from tools.verification_runner import VerificationRunner
                runner = VerificationRunner(project_root=base_path)
                
                results = runner.run_profile(
                    profile="full",
                    files=[target_file],
                )
                
                # Check if the specific violation still appears
                violation_found = any(
                    r.get("contract_id") == violation.contract_id and
                    r.get("check_id") == violation.check_id and
                    r.get("file") == str(violation.file_path) and
                    r.get("line") == violation.line_number
                    for r in results if r.get("status") == "fail"
                )
                
                if not violation_found:
                    # Mark as resolved
                    violation.resolve("Fixed by agent")
                    conformance.violation_store.save(violation)
                    
                    return (
                        f"✓ VIOLATION {target_violation} RESOLVED\n"
                        f"  File: {target_file}\n"
                        f"  Check: {violation.check_id}\n"
                        f"  The specific violation no longer appears."
                    )
                else:
                    # Still present
                    return (
                        f"✗ VIOLATION {target_violation} STILL PRESENT\n"
                        f"  File: {target_file}\n"
                        f"  Check: {violation.check_id}\n"
                        f"  Message: {violation.message}\n"
                        f"  The violation was not fixed by the changes."
                    )
            else:
                # General check (same as v1)
                from tools.verification_runner import VerificationRunner
                runner = VerificationRunner(project_root=base_path)
                
                results = runner.run_profile(
                    profile="full",
                    files=[file_path] if file_path else None,
                )
                
                violations = [r for r in results if r.get("status") == "fail"]
                
                if not violations:
                    return f"✓ CHECK PASSED ({len(results)} checks run)"
                else:
                    return f"✗ CHECK FAILED ({len(violations)} violations found)"
                    
        except Exception as e:
            return f"ERROR: Check failed: {e}"
    
    return handler
```

### 2.5 Test Cases

```python
class TestRunCheckHandler:
    """Tests for run_check handler."""
    
    def test_check_passes_clean_file(self, temp_project):
        """Check passes on compliant code."""
        handler = create_run_check_handler(temp_project)
        
        # Create a clean Python file
        (temp_project / "clean.py").write_text("def foo():\n    pass\n")
        
        result = handler({"file_path": "clean.py"})
        
        assert "PASSED" in result or "passing" in result.lower()
    
    def test_check_fails_with_violation(self, temp_project_with_violation):
        """Check fails on non-compliant code."""
        handler = create_run_check_handler(temp_project_with_violation)
        
        result = handler({})
        
        assert "FAILED" in result or "violation" in result.lower()
    
    def test_specific_violation_resolved(self, temp_project_with_violation):
        """Verify specific violation resolution."""
        handler = create_run_check_handler_v2(temp_project_with_violation)
        
        # Fix the violation
        fix_the_code(temp_project_with_violation)
        
        result = handler({"violation_id": "V-001"})
        
        assert "RESOLVED" in result
```

---

## Part 3: search_code Handler

### 3.1 Purpose

Search the codebase for patterns (regex) or semantically related code (vector search). Returns matching locations with context.

### 3.2 Tool Definition (Already Exists)

```python
SEARCH_CODE = ToolDefinition(
    name="search_code",
    description="Search for patterns in the codebase. Returns matching file paths and line numbers.",
    input_schema={
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Regular expression pattern to search for",
            },
            "file_pattern": {
                "type": "string",
                "description": "Glob pattern to filter files (e.g., '*.py', 'src/**/*.ts')",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return (default: 20)",
            },
        },
        "required": ["pattern"],
    },
)
```

### 3.3 Handler Implementation

```python
# Location: src/agentforge/core/harness/minimal_context/tool_handlers.py

import re
import fnmatch
from pathlib import Path
from typing import Any, Dict, List, Tuple

def create_search_code_handler(project_path: Path = None) -> ActionHandler:
    """
    Create a search_code action handler.
    
    Supports both regex pattern search and semantic search (if indexed).
    Falls back to grep-style search if vector index unavailable.
    
    Args:
        project_path: Project root path
        
    Returns:
        Handler function
    """
    base_path = Path(project_path) if project_path else Path.cwd()
    
    # Default patterns to include/exclude
    INCLUDE_PATTERNS = ["*.py", "*.ts", "*.js", "*.cs", "*.java", "*.go", "*.rs"]
    EXCLUDE_PATTERNS = ["**/node_modules/**", "**/.git/**", "**/bin/**", "**/obj/**", "**/__pycache__/**"]
    
    def handler(params: Dict[str, Any]) -> str:
        pattern = params.get("pattern", "")
        file_pattern = params.get("file_pattern")
        max_results = params.get("max_results", 20)
        search_type = params.get("search_type", "regex")  # "regex" or "semantic"
        
        if not pattern:
            return "ERROR: pattern parameter required"
        
        try:
            if search_type == "semantic":
                return _semantic_search(base_path, pattern, max_results)
            else:
                return _regex_search(base_path, pattern, file_pattern, max_results)
                
        except Exception as e:
            return f"ERROR: Search failed: {e}"
    
    def _regex_search(
        base_path: Path,
        pattern: str,
        file_pattern: str,
        max_results: int,
    ) -> str:
        """Grep-style regex search."""
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            return f"ERROR: Invalid regex pattern: {e}"
        
        results: List[Tuple[str, int, str]] = []  # (file, line_num, line_text)
        
        # Determine files to search
        if file_pattern:
            files = list(base_path.glob(file_pattern))
        else:
            files = []
            for inc in INCLUDE_PATTERNS:
                files.extend(base_path.rglob(inc))
        
        # Filter exclusions
        def should_exclude(path: Path) -> bool:
            path_str = str(path.relative_to(base_path))
            return any(fnmatch.fnmatch(path_str, exc) for exc in EXCLUDE_PATTERNS)
        
        files = [f for f in files if not should_exclude(f)]
        
        # Search files
        for file_path in files:
            if len(results) >= max_results:
                break
                
            try:
                content = file_path.read_text(errors="ignore")
                for line_num, line in enumerate(content.splitlines(), 1):
                    if regex.search(line):
                        rel_path = str(file_path.relative_to(base_path))
                        results.append((rel_path, line_num, line.strip()[:100]))
                        if len(results) >= max_results:
                            break
            except Exception:
                continue  # Skip unreadable files
        
        if not results:
            return f"No matches found for pattern: {pattern}"
        
        # Format results
        output = [f"Found {len(results)} matches for '{pattern}':\n"]
        for file_path, line_num, line_text in results:
            output.append(f"  {file_path}:{line_num}: {line_text}")
        
        if len(results) == max_results:
            output.append(f"\n  (limited to {max_results} results)")
        
        return "\n".join(output)
    
    def _semantic_search(base_path: Path, query: str, max_results: int) -> str:
        """Vector-based semantic search."""
        try:
            from tools.vector_search import VectorSearch
        except ImportError:
            return "ERROR: Vector search not available. Use regex search."
        
        vs = VectorSearch(str(base_path))
        
        if not vs.is_indexed():
            return (
                "Semantic search requires index. Building index...\n"
                "This may take a moment.\n"
                "Consider running 'agentforge index' first."
            )
        
        results = vs.search(query, top_k=max_results)
        
        if not results:
            return f"No semantic matches found for: {query}"
        
        output = [f"Found {len(results)} semantic matches for '{query}':\n"]
        for r in results:
            score_pct = int(r.score * 100)
            output.append(f"  {r.file_path}:{r.start_line}-{r.end_line} ({score_pct}% match)")
            # Include snippet preview
            snippet = r.chunk[:150].replace("\n", " ")
            output.append(f"    {snippet}...")
        
        return "\n".join(output)
    
    return handler
```

### 3.4 Test Cases

```python
class TestSearchCodeHandler:
    """Tests for search_code handler."""
    
    def test_regex_search_finds_pattern(self, temp_project):
        """Regex search finds matching lines."""
        (temp_project / "src" / "module.py").parent.mkdir(exist_ok=True)
        (temp_project / "src" / "module.py").write_text(
            "def calculate_total(items):\n"
            "    return sum(items)\n"
        )
        
        handler = create_search_code_handler(temp_project)
        
        result = handler({"pattern": "calculate_total"})
        
        assert "module.py" in result
        assert "1:" in result or "line 1" in result.lower()
    
    def test_regex_search_with_file_pattern(self, temp_project):
        """File pattern limits search scope."""
        (temp_project / "a.py").write_text("def foo(): pass")
        (temp_project / "b.txt").write_text("def foo(): pass")
        
        handler = create_search_code_handler(temp_project)
        
        result = handler({"pattern": "foo", "file_pattern": "*.py"})
        
        assert "a.py" in result
        assert "b.txt" not in result
    
    def test_regex_no_matches(self, temp_project):
        """No matches returns informative message."""
        (temp_project / "empty.py").write_text("")
        
        handler = create_search_code_handler(temp_project)
        
        result = handler({"pattern": "nonexistent_symbol_xyz"})
        
        assert "No matches" in result
    
    def test_invalid_regex(self, temp_project):
        """Invalid regex returns error."""
        handler = create_search_code_handler(temp_project)
        
        result = handler({"pattern": "[invalid("})
        
        assert "ERROR" in result
        assert "Invalid regex" in result
```

---

## Part 4: cannot_fix Handler

### 4.1 Purpose

Signal that a violation cannot be fixed with the current approach. Creates an escalation record with reasoning and alternatives.

### 4.2 Tool Definition (Already Exists)

```python
CANNOT_FIX = ToolDefinition(
    name="cannot_fix",
    description="Indicate that the issue cannot be fixed with the current approach or constraints.",
    input_schema={
        "type": "object",
        "properties": {
            "reason": {
                "type": "string",
                "description": "Why the fix is not possible",
            },
            "constraints": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Constraints preventing the fix",
            },
            "alternatives": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Alternative approaches that might work",
            },
        },
        "required": ["reason"],
    },
)
```

### 4.3 Handler Implementation

```python
# Location: src/agentforge/core/harness/minimal_context/tool_handlers.py

from datetime import datetime
import yaml

def create_cannot_fix_handler(project_path: Path = None) -> ActionHandler:
    """
    Create a cannot_fix action handler.
    
    Records the inability to fix a violation with detailed reasoning.
    Creates an escalation record for human review.
    
    Args:
        project_path: Project root path
        
    Returns:
        Handler function
    """
    base_path = Path(project_path) if project_path else Path.cwd()
    
    def handler(params: Dict[str, Any]) -> str:
        reason = params.get("reason", "")
        constraints = params.get("constraints", [])
        alternatives = params.get("alternatives", [])
        
        if not reason:
            return "ERROR: reason parameter required"
        
        # Get context from working memory
        context = params.get("_context", {})
        violation_id = context.get("violation_id", "unknown")
        task_id = context.get("task_id", "unknown")
        
        try:
            # Create escalation record
            escalation_dir = base_path / ".agentforge" / "escalations"
            escalation_dir.mkdir(parents=True, exist_ok=True)
            
            escalation_id = f"ESC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            escalation_record = {
                "escalation_id": escalation_id,
                "type": "cannot_fix",
                "violation_id": violation_id,
                "task_id": task_id,
                "created_at": datetime.now().isoformat(),
                "status": "pending",
                "reason": reason,
                "constraints": constraints,
                "alternatives": alternatives,
                "agent_analysis": {
                    "attempted_approaches": context.get("attempted_approaches", []),
                    "files_examined": context.get("files_examined", []),
                    "understanding": context.get("understanding", []),
                },
            }
            
            escalation_file = escalation_dir / f"{escalation_id}.yaml"
            with open(escalation_file, "w") as f:
                yaml.dump(escalation_record, f, default_flow_style=False)
            
            # Update violation status if we have access
            if violation_id != "unknown":
                try:
                    from tools.conformance.manager import ConformanceManager
                    from tools.conformance.domain import ViolationStatus
                    
                    conformance = ConformanceManager(base_path)
                    violation = conformance.violation_store.get(violation_id)
                    if violation:
                        # Mark as requiring human review
                        violation.status = ViolationStatus.OPEN  # Keep open
                        violation.agent_notes = f"Cannot fix: {reason}"
                        conformance.violation_store.save(violation)
                except Exception:
                    pass  # Non-critical
            
            # Format response
            response_parts = [
                f"CANNOT_FIX: Escalation created",
                f"  Escalation ID: {escalation_id}",
                f"  Violation: {violation_id}",
                f"  Reason: {reason}",
            ]
            
            if constraints:
                response_parts.append("  Constraints:")
                for c in constraints:
                    response_parts.append(f"    - {c}")
            
            if alternatives:
                response_parts.append("  Suggested alternatives:")
                for a in alternatives:
                    response_parts.append(f"    - {a}")
            
            response_parts.append(f"\n  Escalation file: {escalation_file.relative_to(base_path)}")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            return f"ERROR: Failed to create escalation: {e}"
    
    return handler
```

### 4.4 Integration with EscalationManager

For more sophisticated escalation handling:

```python
def create_cannot_fix_handler_v2(project_path: Path = None) -> ActionHandler:
    """
    Enhanced cannot_fix handler using EscalationManager.
    """
    base_path = Path(project_path) if project_path else Path.cwd()
    
    def handler(params: Dict[str, Any]) -> str:
        from tools.harness.escalation_manager import EscalationManager
        from tools.harness.escalation_domain import (
            Escalation,
            EscalationType,
            EscalationPriority,
        )
        
        reason = params.get("reason", "")
        constraints = params.get("constraints", [])
        alternatives = params.get("alternatives", [])
        context = params.get("_context", {})
        
        if not reason:
            return "ERROR: reason parameter required"
        
        try:
            manager = EscalationManager(base_path / ".agentforge" / "escalations")
            
            escalation = Escalation(
                type=EscalationType.CANNOT_FIX,
                priority=EscalationPriority.MEDIUM,
                title=f"Cannot fix: {context.get('violation_id', 'unknown')}",
                description=reason,
                context={
                    "violation_id": context.get("violation_id"),
                    "task_id": context.get("task_id"),
                    "constraints": constraints,
                    "alternatives": alternatives,
                    "attempted": context.get("attempted_approaches", []),
                },
            )
            
            created = manager.create_escalation(escalation)
            
            return (
                f"CANNOT_FIX: Escalation {created.id} created\n"
                f"  Reason: {reason}\n"
                f"  Human review required."
            )
            
        except Exception as e:
            return f"ERROR: Failed to escalate: {e}"
    
    return handler
```

### 4.5 Test Cases

```python
class TestCannotFixHandler:
    """Tests for cannot_fix handler."""
    
    def test_creates_escalation_file(self, temp_project):
        """Creates escalation YAML file."""
        handler = create_cannot_fix_handler(temp_project)
        
        result = handler({
            "reason": "Code is auto-generated and should not be modified",
            "constraints": ["File is marked as auto-generated", "Changes would be overwritten"],
            "alternatives": ["Update the generator template instead"],
            "_context": {"violation_id": "V-001", "task_id": "T-123"},
        })
        
        assert "CANNOT_FIX" in result
        assert "ESC-" in result
        
        # Check file was created
        escalations = list((temp_project / ".agentforge" / "escalations").glob("ESC-*.yaml"))
        assert len(escalations) == 1
    
    def test_records_reason_and_alternatives(self, temp_project):
        """Escalation file contains all details."""
        handler = create_cannot_fix_handler(temp_project)
        
        handler({
            "reason": "Test reason",
            "alternatives": ["Alt 1", "Alt 2"],
            "_context": {"violation_id": "V-002"},
        })
        
        escalation_file = next((temp_project / ".agentforge" / "escalations").glob("*.yaml"))
        with open(escalation_file) as f:
            data = yaml.safe_load(f)
        
        assert data["reason"] == "Test reason"
        assert data["alternatives"] == ["Alt 1", "Alt 2"]
        assert data["violation_id"] == "V-002"
    
    def test_requires_reason(self, temp_project):
        """Error without reason parameter."""
        handler = create_cannot_fix_handler(temp_project)
        
        result = handler({})
        
        assert "ERROR" in result
        assert "reason" in result.lower()
```

---

## Part 5: Integration

### 5.1 Updated create_standard_handlers

```python
# Location: src/agentforge/core/harness/minimal_context/tool_handlers.py

def create_standard_handlers(project_path: Path = None) -> Dict[str, ActionHandler]:
    """
    Create standard action handlers for all base tools.
    
    Args:
        project_path: Base path for file operations
        
    Returns:
        Dict of action name to handler function
    """
    return {
        # File operations
        "read_file": create_read_file_handler(project_path),
        "write_file": create_write_file_handler(project_path),
        "edit_file": create_edit_file_handler(project_path),
        
        # Search and context
        "search_code": create_search_code_handler(project_path),
        "load_context": create_load_context_handler(project_path),
        
        # Verification
        "run_check": create_run_check_handler_v2(project_path),
        "run_tests": create_run_tests_handler(project_path),
        
        # Terminal actions
        "complete": create_complete_handler(),
        "escalate": create_escalate_handler(),
        "cannot_fix": create_cannot_fix_handler(project_path),
    }
```

### 5.2 Handler Module Structure

```
src/agentforge/core/harness/minimal_context/
├── tool_handlers/
│   ├── __init__.py           # Exports create_standard_handlers
│   ├── file_handlers.py      # read_file, write_file, edit_file
│   ├── search_handlers.py    # search_code, load_context
│   ├── verify_handlers.py    # run_check, run_tests
│   └── terminal_handlers.py  # complete, escalate, cannot_fix
├── native_tool_executor.py   # Uses tool_handlers
└── executor.py               # Main executor
```

### 5.3 Test Infrastructure

```python
# tests/conftest.py additions

@pytest.fixture
def temp_project_with_violation(tmp_path):
    """Create a temp project with a conformance violation."""
    project = tmp_path / "test_project"
    project.mkdir()
    
    # Create .agentforge structure
    (project / ".agentforge").mkdir()
    (project / ".agentforge" / "violations").mkdir()
    (project / ".agentforge" / "conformance_report.yaml").write_text(
        "schema_version: '1.0'\nviolation_count: 1\n"
    )
    
    # Create violation file
    violation = {
        "violation_id": "V-001",
        "contract_id": "complexity",
        "check_id": "cyclomatic-complexity",
        "severity": "warning",
        "file_path": "src/complex.py",
        "line_number": 10,
        "message": "Function has complexity 15 (max 10)",
        "status": "open",
    }
    with open(project / ".agentforge" / "violations" / "V-001.yaml", "w") as f:
        yaml.dump(violation, f)
    
    # Create the violating file
    (project / "src").mkdir()
    (project / "src" / "complex.py").write_text(
        "def complex_function(a, b, c, d, e):\n"
        "    if a: return 1\n"
        "    elif b: return 2\n"
        "    # ... lots of branches ...\n"
    )
    
    return project
```

---

## Part 6: Acceptance Criteria

### 6.1 edit_file Handler ✅

- [x] Replaces specified line range with new content
- [x] Handles 1-indexed line numbers correctly
- [x] Preserves content before start_line and after end_line
- [x] Handles edge cases (first line, last line, beyond file)
- [x] Returns clear success/error messages
- [x] Works with relative and absolute paths

### 6.2 run_check Handler ✅

- [x] Runs conformance checks on specified file or all files
- [x] Returns pass/fail with violation details
- [x] Can verify specific violation was resolved
- [x] Updates violation status when resolved
- [x] Handles missing configuration gracefully

### 6.3 search_code Handler ✅

- [x] Performs regex search across codebase
- [x] Respects file pattern filters
- [x] Excludes common noise directories (node_modules, .git)
- [x] Returns file paths with line numbers
- [x] Limits results to max_results
- [x] Falls back gracefully if vector search unavailable

### 6.4 cannot_fix Handler ✅

- [x] Creates escalation record with timestamp
- [x] Includes reason, constraints, and alternatives
- [x] Captures agent's analysis context
- [x] Returns escalation ID for tracking
- [x] Persists to disk for human review

---

## Part 7: Implementation Status

### Completed Phases

| Phase | Status | Notes |
|-------|--------|-------|
| Module Structure | ✅ Complete | `tool_handlers/` with 6 files |
| Core Handlers | ✅ Complete | All 15 handlers implemented |
| Unit Tests | ✅ Complete | 110 tests passing |
| Integration Tests | ✅ Complete | 27 tests (context + workflow) |
| Code Review | ✅ Complete | Security, constants, logging added |

### Test Summary

```
tests/unit/harness/tool_handlers/     - 110 tests
tests/integration/tool_handlers/      - 10 tests
tests/integration/workflows/          - 17 tests
Total:                                  137 tests passing
```

---

## Appendix A: Existing Infrastructure Reference

### ConformanceManager API

```python
class ConformanceManager:
    def __init__(self, repo_root: Path): ...
    def run_conformance_check(self, verification_results, ...) -> ConformanceReport: ...
    def get_violation(self, violation_id: str) -> Optional[Violation]: ...
    
class ViolationStore:
    def get(self, violation_id: str) -> Optional[Violation]: ...
    def save(self, violation: Violation) -> None: ...
    def find_by_status(self, status: ViolationStatus) -> List[Violation]: ...
```

### VectorSearch API

```python
class VectorSearch:
    def __init__(self, project_path: str, config: dict = None): ...
    def index(self, force_rebuild: bool = False) -> IndexStats: ...
    def search(self, query: str, top_k: int = 10) -> List[SearchResult]: ...
    def is_indexed(self) -> bool: ...
```

### VerificationRunner API

```python
class VerificationRunner:
    def __init__(self, config_path: Path = None, project_root: Path = None): ...
    def run_profile(self, profile: str, checks: List[str] = None, 
                    files: List[str] = None) -> List[Dict]: ...
```

---

**End of Specification**
