# @spec_file: .agentforge/specs/core-harness-minimal-context-v1.yaml
# @spec_id: core-harness-minimal-context-v1
# @component_id: harness-minimal_context-context_schemas
# @test_path: tests/unit/harness/test_enhanced_context.py

"""
Context Schemas
===============

Defines context schemas for different task types.
Each schema specifies what data is included in the context and how to format it.
"""

import yaml
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .state_store import TaskState
from .token_budget import TokenBudget, estimate_tokens, compress_file_content


@dataclass
class AvailableAction:
    """Definition of an action the agent can take."""
    name: str
    description: str
    parameters: Optional[Dict[str, Any]] = None


class ContextSchema(ABC):
    """Base class for context schemas."""

    schema_name: str = "base"
    max_tokens: int = 6000

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.token_budget = TokenBudget()

    @abstractmethod
    def get_current_state(self, state: TaskState) -> Dict[str, Any]:
        """
        Get the current_state section for this task type.

        Args:
            state: Current task state

        Returns:
            Dict representing current state
        """
        pass

    @abstractmethod
    def get_available_actions(self, state: TaskState) -> List[AvailableAction]:
        """
        Get available actions for current phase.

        Args:
            state: Current task state

        Returns:
            List of available actions
        """
        pass

    def get_system_prompt(self, state: TaskState) -> str:
        """
        Get phase-appropriate system prompt.

        Args:
            state: Current task state

        Returns:
            System prompt string
        """
        return SYSTEM_PROMPTS.get(
            f"{self.schema_name}_{state.phase.value}",
            SYSTEM_PROMPTS.get(self.schema_name, DEFAULT_SYSTEM_PROMPT)
        )

    def format_task_frame(self, state: TaskState) -> str:
        """Format the task frame section."""
        max_steps = 20  # Match MinimalContextFixWorkflow default
        steps_remaining = max_steps - state.current_step
        return yaml.dump({
            "id": state.task_id,
            "goal": state.goal,
            "step": f"{state.current_step} of {max_steps}",
            "steps_remaining": steps_remaining,
            "phase": state.phase.value,
            "success_criteria": state.success_criteria,
            "constraints": state.constraints or [],
            "URGENT": "Make edits NOW" if steps_remaining <= 15 else None,
        }, default_flow_style=False)

    def format_verification_status(self, state: TaskState) -> str:
        """Format verification status."""
        return yaml.dump({
            "checks_passing": state.verification.checks_passing,
            "checks_failing": state.verification.checks_failing,
            "tests_passing": state.verification.tests_passing,
            "ready_for_completion": state.verification.ready_for_completion,
        }, default_flow_style=False)

    def format_available_actions(self, state: TaskState) -> str:
        """Format available actions."""
        actions = self.get_available_actions(state)
        return yaml.dump([
            {"name": a.name, "description": a.description}
            for a in actions
        ], default_flow_style=False)

    def _read_file_bounded(self, path: Path, max_tokens: int = 2000) -> str:
        """Read file content with token limit."""
        if not path.exists():
            return f"# File not found: {path}"

        content = path.read_text()
        if estimate_tokens(content) > max_tokens:
            content = compress_file_content(content, max_tokens)

        return content


class FixViolationSchema(ContextSchema):
    """Context schema for fix_violation tasks."""

    schema_name = "fix_violation"
    max_tokens = 8000  # Increased to accommodate pre-computed context

    def get_current_state(self, state: TaskState) -> Dict[str, Any]:
        """Build current state for fix_violation task."""
        ctx = state.context_data

        # Violation info
        violation = {
            "id": ctx.get("violation_id", "unknown"),
            "check_id": ctx.get("check_id", "unknown"),
            "severity": ctx.get("severity", "unknown"),
            "file_path": ctx.get("file_path", "unknown"),
            "line_number": ctx.get("line_number"),
            "message": ctx.get("message", ""),
            "fix_hint": ctx.get("fix_hint"),
        }

        result = {"violation": violation}

        # Include pre-computed analysis (from AST, deterministic)
        precomputed = ctx.get("precomputed", {})
        if precomputed:
            # Function source - this is critical for making accurate edits
            if precomputed.get("function_source"):
                result["target_function"] = {
                    "name": precomputed.get("violating_function"),
                    "lines": precomputed.get("function_lines"),
                    "source": precomputed.get("function_source"),
                }

            # Analysis metrics - tells the agent what needs fixing
            if precomputed.get("analysis"):
                analysis = precomputed["analysis"]
                result["analysis"] = {
                    "complexity": analysis.get("complexity"),
                    "threshold": 10,  # Standard threshold
                    "nesting_depth": analysis.get("nesting_depth"),
                    "branches": analysis.get("branches", []),
                }

            # Extraction suggestions - pre-computed recommendations
            if precomputed.get("extraction_suggestions"):
                result["extraction_suggestions"] = precomputed["extraction_suggestions"]

            # Check definition
            if precomputed.get("check_definition"):
                result["check_definition"] = precomputed["check_definition"]

            # Class context if this is a method
            if precomputed.get("parent_class"):
                result["class_context"] = {
                    "name": precomputed["parent_class"],
                    "methods": precomputed.get("class_methods", []),
                }

        # Verification details
        verification = None
        if state.verification.last_check_time:
            verification = {
                "last_check_result": f"{state.verification.checks_passing} of {state.verification.checks_passing + state.verification.checks_failing} passing",
                "remaining_issues": state.verification.details.get("remaining_issues", []),
            }

        if verification:
            result["verification"] = verification

        return result

    def get_available_actions(self, state: TaskState) -> List[AvailableAction]:
        """Get available actions for current phase."""
        # Semantic refactoring tools (PREFERRED - handle indentation automatically)
        actions = [
            AvailableAction(
                "extract_function",
                "Extract code into helper function (PREFERRED for complexity). "
                "Auto-handles params & indentation. "
                "Parameters: file_path, source_function, start_line, end_line, new_function_name"
            ),
            AvailableAction(
                "simplify_conditional",
                "Convert if/else to guard clause (reduces nesting). "
                "Parameters: file_path, function_name, if_line"
            ),
            AvailableAction(
                "run_check",
                "Run conformance check to verify fix."
            ),
        ]

        # Lower priority text-based tools (only if semantic tools can't help)
        actions.extend([
            AvailableAction(
                "replace_lines",
                "Replace lines by number (fallback if semantic tools fail). "
                "Parameters: file_path, start_line, end_line, new_content"
            ),
            AvailableAction(
                "read_file",
                "Read a file (usually not needed - check precomputed context). Parameters: path"
            ),
        ])

        # Phase-specific actions
        if state.phase.value in ["analyze", "plan", "implement", "init"]:
            actions.extend([
                AvailableAction(
                    "edit_file",
                    "Edit a file. Parameters: path, old_text (text to replace), new_text (replacement)"
                ),
                AvailableAction(
                    "run_tests",
                    "Run tests. Parameters: path (optional, specific test file)"
                ),
            ])

        if state.phase.value == "verify":
            actions.append(
                AvailableAction("run_full_check", "Run full conformance check on all files")
            )

        if state.phase.value in ["verify", "commit"]:
            actions.append(
                AvailableAction("complete", "Mark task complete (only when checks pass)")
            )

        # Always available
        actions.extend([
            AvailableAction(
                "load_context",
                "Load file into context. Parameters: path (e.g., 'src/file.py')"
            ),
            AvailableAction("escalate", "Request human help when stuck"),
        ])

        return actions


class ImplementFeatureSchema(ContextSchema):
    """Context schema for implement_feature tasks."""

    schema_name = "implement_feature"
    max_tokens = 8000

    def get_current_state(self, state: TaskState) -> Dict[str, Any]:
        """Build current state for implement_feature task."""
        ctx = state.context_data

        result = {}

        # Specification
        if ctx.get("spec"):
            result["spec"] = {
                "title": ctx.get("spec_title", "Feature"),
                "requirements": ctx.get("requirements", []),
                "constraints": ctx.get("spec_constraints", []),
            }

        # Target files
        if ctx.get("target_files"):
            result["target_files"] = []
            for tf in ctx.get("target_files", []):
                file_info = {
                    "path": tf.get("path"),
                    "status": tf.get("status", "to_modify"),
                }
                if tf.get("status") == "to_modify":
                    full_path = self.project_path / tf["path"]
                    if full_path.exists():
                        file_info["relevant_section"] = self._read_file_bounded(
                            full_path, max_tokens=1000
                        )
                result["target_files"].append(file_info)

        # Test requirements
        if ctx.get("test_requirements"):
            result["test_requirements"] = ctx.get("test_requirements")

        return result

    def get_available_actions(self, state: TaskState) -> List[AvailableAction]:
        """Get available actions for current phase."""
        actions = [
            AvailableAction("read_file", "Read file contents"),
            AvailableAction("edit_file", "Modify file contents"),
            AvailableAction("create_file", "Create a new file"),
            AvailableAction("run_tests", "Run tests"),
            AvailableAction("run_check", "Run conformance check"),
            AvailableAction("load_context", "Load additional context"),
        ]

        if state.phase.value in ["verify", "commit"]:
            actions.append(AvailableAction("complete", "Mark task complete"))

        actions.append(AvailableAction("escalate", "Request human help"))

        return actions


class WriteTestsSchema(ContextSchema):
    """Context schema for write_tests (RED phase) tasks."""

    schema_name = "write_tests"
    max_tokens = 6000

    def get_current_state(self, state: TaskState) -> Dict[str, Any]:
        """Build current state for write_tests task."""
        ctx = state.context_data
        result = {}

        # Spec requirements
        if ctx.get("requirements"):
            result["spec"] = {
                "requirements": [
                    {
                        "id": r.get("id"),
                        "acceptance_criteria": r.get("acceptance_criteria"),
                    }
                    for r in ctx.get("requirements", [])
                ]
            }

        # Test patterns from codebase
        if ctx.get("test_pattern_file"):
            pattern_path = self.project_path / ctx["test_pattern_file"]
            if pattern_path.exists():
                result["test_patterns"] = {
                    "example_test": self._read_file_bounded(pattern_path, max_tokens=500),
                }

        # Target test file
        if ctx.get("target_test_file"):
            result["target_test_file"] = {
                "path": ctx["target_test_file"],
                "existing_content": None,
            }
            test_path = self.project_path / ctx["target_test_file"]
            if test_path.exists():
                result["target_test_file"]["existing_content"] = self._read_file_bounded(
                    test_path, max_tokens=1000
                )

        return result

    def get_available_actions(self, state: TaskState) -> List[AvailableAction]:
        """Get available actions."""
        return [
            AvailableAction("read_file", "Read file contents"),
            AvailableAction("create_file", "Create a new file"),
            AvailableAction("edit_file", "Modify file contents"),
            AvailableAction("run_tests", "Run tests (should fail initially)"),
            AvailableAction("complete", "Mark test writing complete"),
            AvailableAction("load_context", "Load additional context"),
            AvailableAction("escalate", "Request human help"),
        ]


# ═══════════════════════════════════════════════════════════════════════════════
# System Prompts
# ═══════════════════════════════════════════════════════════════════════════════


DEFAULT_SYSTEM_PROMPT = """You are an autonomous agent fixing issues in a codebase.

Process:
1. Understand the task and current state
2. Take one action at a time
3. Verify results after each action
4. Complete when all criteria are met

Rules:
- Make minimal, focused changes
- Verify before marking complete
- Escalate if stuck after 3 different approaches

Respond with a single action in this format:
```action
name: action_name
parameters:
  param1: value1
  param2: value2
```

Or to complete:
```action
name: complete
```
"""


SYSTEM_PROMPTS = {
    "fix_violation": """You are fixing a conformance violation.

YOU HAVE PRE-COMPUTED CONTEXT:
- target_function.source: The EXACT source code you need to refactor
- extraction_suggestions: Pre-computed, VALIDATED recommendations (if available)
- extraction_not_possible: Explanation if no safe extractions exist

WORKFLOW (when extraction_suggestions are available):
1. Use extract_function with line numbers from extraction_suggestions
2. Check result - extraction auto-runs verification and refreshes context
3. Repeat until "✓ Check PASSED" appears, then use 'complete'

WORKFLOW (when extraction_not_possible is set):
The code contains control flow (early returns, break/continue) that prevents safe extraction.
Options:
1. Use simplify_conditional to convert early returns to guard clauses first
2. Use 'cannot_fix' action with reason explaining the limitation
Do NOT repeatedly attempt extractions that the tool has already rejected.

IMPORTANT: After each extract_function:
- Verification runs AUTOMATICALLY (you see "✓ Check PASSED" or "○ Check still failing")
- Context is REFRESHED with new line numbers (old suggestions become invalid)
- ALWAYS use NEW line numbers from the refreshed extraction_suggestions

FOR max-function-length (max 50 lines):
Extract any logical blocks. Each extraction reduces line count.
Focus on extractable blocks from extraction_suggestions.

FOR max-cyclomatic-complexity (threshold=10):
Extract branches (if blocks, loops) to reduce complexity.

EXAMPLE - Extract nested logic into helper:
```action
name: extract_function
parameters:
  file_path: tools/tdflow/phases/refactor.py
  source_function: execute
  start_line: 83
  end_line: 94
  new_function_name: _handle_no_changes_case
```

The tool will:
- Auto-detect which variables need to be parameters
- Create proper method signature with self
- Handle all indentation automatically
- Validate the result is syntactically correct
- Replace original code with a function call
- AUTO-RUN verification and REFRESH context with new line numbers

RESPONSE FORMAT - One action per response:
```action
name: action_name
parameters:
  key: value
```

When you see "✓ Check PASSED" in the result:
```action
name: complete
```

PREFER SEMANTIC TOOLS:
- extract_function: Extracts code into helper (auto-verifies!)
- simplify_conditional: Converts if/else to guard clause
- write_file: Create new files (e.g., conftest.py for fixture violations)

FOR "fixtures-in-conftest" violations:
1. Read the fixture from the test file
2. Create conftest.py using write_file with the fixture code
3. Remove the fixture from the original test file using edit_file
4. Run run_check to verify

AVOID TEXT-BASED TOOLS (error-prone):
- edit_file, replace_lines: Only if semantic tools can't help
""",

    "fix_violation_analyze": """You are analyzing a conformance violation.

Your goal: Understand what needs to be fixed.

ACTIONS TO TAKE:
1. Use get_check_definition to understand what the check enforces
2. Read the file to see the actual code at the violation line
3. Identify what specific change is needed

For complexity violations: Look for nested conditionals, loops, or long functions
that can be split into smaller helper functions.

```action
name: get_check_definition
parameters:
  check_id: "check-id-from-violation"
```

Or to read the file:
```action
name: read_file
parameters:
  path: "path/from/violation"
```
""",

    "fix_violation_implement": """You are implementing a fix for a conformance violation.

Make the minimal edit needed to fix the issue.

For complexity violations: Extract helper functions to reduce cyclomatic complexity.
For pattern violations: Change the code to match required patterns.

After making an edit, you MUST run the check to verify:
```action
name: run_check
parameters: {}
```

Edit format:
```action
name: edit_file
parameters:
  path: "path/to/file.py"
  old_text: |
    exact text to replace (copy from file)
  new_text: |
    new code with fix
```
""",

    "fix_violation_verify": """You are verifying a fix for a conformance violation.

Run the conformance check to verify the fix worked.

```action
name: run_check
parameters: {}
```

The check will automatically use the check_id and file_path from the violation.

If the check PASSES (shows ✓), complete the task:
```action
name: complete
```

If the check FAILS (shows ✗), you need to make more edits.
""",

    "implement_feature": """You are implementing a feature based on a specification.

Your goal: Implement the feature so all tests pass.

Process:
1. Understand requirements and acceptance criteria
2. Plan the implementation
3. Make changes incrementally
4. Run tests after each change
5. Complete when all tests pass

Rules:
- Follow existing code patterns
- Make focused, incremental changes
- Test after each change
- Escalate if requirements are unclear

Respond with a single action.
""",

    "write_tests": """You are writing failing tests for a specification.

Your goal: Create tests that define expected behavior.

Process:
1. Read the requirements and acceptance criteria
2. Write tests that would pass if the feature worked
3. Verify tests fail (implementation doesn't exist yet)

Rules:
- One test per acceptance criterion minimum
- Tests must be runnable
- Tests must currently fail
- Follow existing test patterns in codebase

Respond with a single action.
""",
}


# ═══════════════════════════════════════════════════════════════════════════════
# Schema Registry
# ═══════════════════════════════════════════════════════════════════════════════


SCHEMA_REGISTRY = {
    "fix_violation": FixViolationSchema,
    "implement_feature": ImplementFeatureSchema,
    "write_tests": WriteTestsSchema,
}


def get_schema_for_task(task_type: str, project_path: Path) -> ContextSchema:
    """
    Get the appropriate schema for a task type.

    Args:
        task_type: Type of task
        project_path: Project root path

    Returns:
        ContextSchema instance
    """
    schema_class = SCHEMA_REGISTRY.get(task_type)
    if schema_class:
        return schema_class(project_path)

    # Default to fix_violation schema
    return FixViolationSchema(project_path)
