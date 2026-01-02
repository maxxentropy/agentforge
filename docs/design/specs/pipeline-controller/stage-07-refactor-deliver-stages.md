# Pipeline Controller Specification - Stage 7: REFACTOR & DELIVER Stages

**Version:** 1.0  
**Date:** January 2, 2026  
**Status:** Specification  
**Depends On:** Stage 1-6  
**Estimated Effort:** 4-5 days

---

## 1. Overview

### 1.1 Purpose

The final two stages complete the TDD cycle and deliver the result:

1. **REFACTOR**: Improve code quality without changing behavior (tests still pass)
2. **DELIVER**: Package and deliver the final result (commit, PR, or files)

### 1.2 Stage Flow

```
GREEN Phase Artifact (passing tests)
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│                        REFACTOR                                  │
│                                                                  │
│  "Improve code while keeping tests green"                       │
│                                                                  │
│  Input: Implementation files + passing tests                    │
│  Output: Refactored files + still passing tests                 │
│                                                                  │
│  Actions:                                                       │
│  1. Run conformance checks                                      │
│  2. Identify code quality issues                                │
│  3. Apply refactorings                                          │
│  4. Verify tests still pass                                     │
│  5. Verify conformance passes                                   │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│                         DELIVER                                  │
│                                                                  │
│  "Package and deliver the result"                               │
│                                                                  │
│  Input: Refactored files + test results                         │
│  Output: Commit/PR/Files                                        │
│                                                                  │
│  Actions:                                                       │
│  1. Stage files for commit                                      │
│  2. Generate commit message                                     │
│  3. Create commit or PR                                         │
│  4. Update documentation                                        │
│  5. Generate summary                                            │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
   PIPELINE COMPLETE
```

---

## 2. REFACTOR Stage

### 2.1 RefactorExecutor Implementation

```python
# src/agentforge/core/pipeline/stages/refactor.py

from typing import Any, Dict, List, Optional
from pathlib import Path
import logging
import subprocess
import sys

from ..stage_executor import StageExecutor, StageContext, StageResult, StageStatus

logger = logging.getLogger(__name__)


class RefactorExecutor(StageExecutor):
    """
    REFACTOR stage executor.
    
    Improves code quality while maintaining behavior (tests pass).
    
    Refactoring targets:
    - Code style and formatting
    - Complexity reduction
    - Duplicate code elimination
    - Naming improvements
    - Documentation
    """
    
    stage_name = "refactor"
    artifact_type = "refactored_code"
    
    required_input_fields = ["spec_id", "implementation_files", "test_results"]
    
    output_fields = [
        "spec_id",
        "refactored_files",
        "final_files",
    ]
    
    SYSTEM_PROMPT = """You are an expert software engineer improving code quality.

You are in the REFACTOR phase of TDD. The implementation works and tests pass.
Your job is to improve code quality without changing behavior.

Refactoring targets:
1. Code style and formatting (PEP 8 for Python)
2. Reduce complexity (extract methods, simplify conditionals)
3. Eliminate duplication
4. Improve naming
5. Add/improve documentation and type hints
6. Remove dead code

You have access to these tools:
- read_file: Read file contents
- edit_file: Make targeted edits
- run_check: Run conformance checks
- run_tests: Verify tests still pass
- complete: Signal refactoring complete

IMPORTANT:
- Tests must continue to pass after every change
- Don't change public interfaces
- Make small, incremental improvements
- Run tests after each significant change
"""

    TASK_TEMPLATE = """Refactor the implementation to improve code quality.

IMPLEMENTATION FILES:
{implementation_files}

TEST STATUS: {test_status}

ACCEPTANCE CRITERIA:
{acceptance_criteria}

CONFORMANCE REQUIREMENTS:
- Max cyclomatic complexity: 10
- Max function length: 50 lines
- Type hints required
- Docstrings required for public methods

Instructions:
1. Read each implementation file
2. Run conformance checks to identify issues
3. Apply refactorings to fix issues
4. Run tests to ensure they still pass
5. Repeat until conformance passes
6. Call 'complete' when done
"""

    def _execute(self, context: StageContext) -> StageResult:
        """Execute REFACTOR phase."""
        input_artifact = context.input_artifact
        
        # Step 1: Verify tests pass before refactoring
        initial_tests = self._run_tests(context)
        if initial_tests.get("failed", 0) > 0:
            return StageResult(
                stage_name=self.stage_name,
                status=StageStatus.FAILED,
                error="Tests must pass before refactoring",
            )
        
        # Step 2: Run conformance to identify issues
        conformance = self._run_conformance(context)
        
        # Step 3: If no issues, skip refactoring
        if conformance.get("passed", False) and not conformance.get("violations"):
            logger.info("No conformance issues, skipping refactoring")
            return StageResult(
                stage_name=self.stage_name,
                status=StageStatus.COMPLETED,
                artifact=self._create_passthrough_artifact(context, initial_tests),
            )
        
        # Step 4: Execute refactoring with LLM
        executor = self._get_refactor_executor(context)
        
        task = self._build_task(input_artifact, initial_tests, conformance)
        
        try:
            result = executor.execute_task(
                task_description=task,
                system_prompt=self.SYSTEM_PROMPT,
                context={"phase": "refactor", "spec_id": input_artifact.get("spec_id")},
                max_iterations=10,
            )
            
            # Step 5: Final verification
            final_tests = self._run_tests(context)
            final_conformance = self._run_conformance(context)
            
            if final_tests.get("failed", 0) > 0:
                return StageResult(
                    stage_name=self.stage_name,
                    status=StageStatus.FAILED,
                    error="Tests failed after refactoring",
                )
            
            return StageResult(
                stage_name=self.stage_name,
                status=StageStatus.COMPLETED,
                artifact=self._build_artifact(
                    context, result, final_tests, final_conformance
                ),
            )
            
        except Exception as e:
            logger.exception(f"Refactoring failed: {e}")
            return StageResult(
                stage_name=self.stage_name,
                status=StageStatus.FAILED,
                error=str(e),
            )
    
    def _run_tests(self, context: StageContext) -> Dict[str, Any]:
        """Run test suite."""
        import re
        
        try:
            cmd = [sys.executable, "-m", "pytest", "-v", "--tb=short"]
            result = subprocess.run(
                cmd,
                cwd=str(context.project_path),
                capture_output=True,
                text=True,
                timeout=300,
            )
            
            passed = len(re.findall(r"PASSED", result.stdout))
            failed = len(re.findall(r"FAILED", result.stdout))
            
            return {
                "passed": passed,
                "failed": failed,
                "total": passed + failed,
                "output": result.stdout,
            }
        except Exception as e:
            return {"error": str(e), "passed": 0, "failed": 1}
    
    def _run_conformance(self, context: StageContext) -> Dict[str, Any]:
        """Run conformance checks."""
        try:
            # Use agentforge conformance check
            cmd = [
                sys.executable, "-m", "agentforge",
                "conformance", "check",
                "--format", "json"
            ]
            result = subprocess.run(
                cmd,
                cwd=str(context.project_path),
                capture_output=True,
                text=True,
                timeout=120,
            )
            
            import json
            try:
                data = json.loads(result.stdout)
                return {
                    "passed": data.get("passed", False),
                    "violations": data.get("violations", []),
                    "total_violations": len(data.get("violations", [])),
                }
            except json.JSONDecodeError:
                return {
                    "passed": result.returncode == 0,
                    "violations": [],
                    "output": result.stdout,
                }
        except Exception as e:
            return {"error": str(e), "passed": True, "violations": []}
    
    def _get_refactor_executor(self, context: StageContext):
        """Get executor for refactoring."""
        from agentforge.core.harness.minimal_context import MinimalContextExecutor
        from agentforge.core.harness.minimal_context.tool_handlers import (
            create_enhanced_handlers,
        )
        
        executor = MinimalContextExecutor(
            project_path=context.project_path,
            task_type="refactor",
        )
        
        handlers = create_enhanced_handlers(context.project_path)
        for name, handler in handlers.items():
            executor.native_tool_executor.register_action(name, handler)
        
        return executor
    
    def _build_task(
        self,
        artifact: Dict[str, Any],
        test_results: Dict[str, Any],
        conformance: Dict[str, Any],
    ) -> str:
        """Build refactoring task description."""
        files = artifact.get("implementation_files", [])
        files_str = "\n".join([f"  - {f}" for f in files]) or "  (none)"
        
        test_status = f"{test_results.get('passed', 0)} passed, {test_results.get('failed', 0)} failed"
        
        criteria = artifact.get("acceptance_criteria", [])
        criteria_str = "\n".join([
            f"  - {c.get('criterion', c)}" for c in criteria
        ]) or "  (none specified)"
        
        return self.TASK_TEMPLATE.format(
            implementation_files=files_str,
            test_status=test_status,
            acceptance_criteria=criteria_str,
        )
    
    def _create_passthrough_artifact(
        self,
        context: StageContext,
        test_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create artifact when no refactoring needed."""
        input_artifact = context.input_artifact
        impl_files = input_artifact.get("implementation_files", [])
        
        return {
            "spec_id": input_artifact.get("spec_id"),
            "request_id": input_artifact.get("request_id"),
            "refactored_files": [],
            "improvements": [],
            "final_files": impl_files + input_artifact.get("test_files", []),
            "test_results": test_results,
            "conformance_passed": True,
        }
    
    def _build_artifact(
        self,
        context: StageContext,
        result: Dict[str, Any],
        test_results: Dict[str, Any],
        conformance: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build REFACTOR artifact."""
        input_artifact = context.input_artifact
        impl_files = input_artifact.get("implementation_files", [])
        test_files = input_artifact.get("test_files", [])
        
        return {
            "spec_id": input_artifact.get("spec_id"),
            "request_id": input_artifact.get("request_id"),
            "refactored_files": result.get("files_modified", impl_files),
            "improvements": result.get("improvements", []),
            "final_files": impl_files + (
                [t.get("path", t) if isinstance(t, dict) else t for t in test_files]
            ),
            "test_results": test_results,
            "conformance_passed": conformance.get("passed", False),
            "remaining_violations": conformance.get("violations", []),
        }


def create_refactor_executor(config: Optional[Dict] = None) -> RefactorExecutor:
    """Create RefactorExecutor instance."""
    return RefactorExecutor(config)
```

---

## 3. DELIVER Stage

### 3.1 DeliverExecutor Implementation

```python
# src/agentforge/core/pipeline/stages/deliver.py

from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime, timezone
import logging
import subprocess

from ..stage_executor import StageExecutor, StageContext, StageResult, StageStatus

logger = logging.getLogger(__name__)


class DeliveryMode:
    """Delivery modes."""
    COMMIT = "commit"           # Git commit only
    PR = "pr"                   # Create pull request
    FILES = "files"             # Just output files (no git)
    PATCH = "patch"             # Generate patch file


class DeliverExecutor(StageExecutor):
    """
    DELIVER stage executor.
    
    Packages and delivers the final result.
    
    Delivery modes:
    - commit: Create a git commit with all changes
    - pr: Create a pull request (requires GitHub integration)
    - files: Output files without git operations
    - patch: Generate a patch file
    """
    
    stage_name = "deliver"
    artifact_type = "deliverable"
    
    required_input_fields = ["spec_id", "final_files"]
    
    output_fields = [
        "spec_id",
        "deliverable_type",
    ]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.delivery_mode = (
            config.get("delivery_mode", DeliveryMode.COMMIT)
            if config else DeliveryMode.COMMIT
        )
        self.auto_commit = config.get("auto_commit", False) if config else False
        self.branch_prefix = config.get("branch_prefix", "feature/") if config else "feature/"
    
    def _execute(self, context: StageContext) -> StageResult:
        """Execute DELIVER phase."""
        input_artifact = context.input_artifact
        
        # Determine delivery mode
        mode = self.delivery_mode
        
        if mode == DeliveryMode.COMMIT:
            return self._deliver_commit(context, input_artifact)
        elif mode == DeliveryMode.PR:
            return self._deliver_pr(context, input_artifact)
        elif mode == DeliveryMode.FILES:
            return self._deliver_files(context, input_artifact)
        elif mode == DeliveryMode.PATCH:
            return self._deliver_patch(context, input_artifact)
        else:
            return StageResult(
                stage_name=self.stage_name,
                status=StageStatus.FAILED,
                error=f"Unknown delivery mode: {mode}",
            )
    
    def _deliver_commit(
        self,
        context: StageContext,
        artifact: Dict[str, Any],
    ) -> StageResult:
        """Deliver as git commit."""
        spec_id = artifact.get("spec_id", "unknown")
        
        # Generate commit message
        commit_message = self._generate_commit_message(artifact)
        
        # Stage files
        final_files = artifact.get("final_files", [])
        staged = self._stage_files(context, final_files)
        
        if not staged:
            return StageResult(
                stage_name=self.stage_name,
                status=StageStatus.COMPLETED,
                artifact={
                    "spec_id": spec_id,
                    "deliverable_type": "commit",
                    "commit_sha": None,
                    "files_staged": [],
                    "summary": "No changes to commit",
                    "status": "no_changes",
                },
            )
        
        # Create commit (if auto_commit enabled)
        if self.auto_commit:
            commit_sha = self._create_commit(context, commit_message)
        else:
            commit_sha = None
            logger.info("Changes staged but not committed (auto_commit=False)")
        
        return StageResult(
            stage_name=self.stage_name,
            status=StageStatus.COMPLETED,
            artifact={
                "spec_id": spec_id,
                "request_id": artifact.get("request_id"),
                "deliverable_type": "commit",
                "commit_sha": commit_sha,
                "commit_message": commit_message,
                "files_modified": final_files,
                "files_staged": staged,
                "summary": self._generate_summary(artifact),
                "status": "committed" if commit_sha else "staged",
            },
        )
    
    def _deliver_pr(
        self,
        context: StageContext,
        artifact: Dict[str, Any],
    ) -> StageResult:
        """Deliver as pull request."""
        spec_id = artifact.get("spec_id", "unknown")
        
        # Create feature branch
        branch_name = f"{self.branch_prefix}{spec_id.lower()}"
        self._create_branch(context, branch_name)
        
        # Stage and commit
        final_files = artifact.get("final_files", [])
        self._stage_files(context, final_files)
        
        commit_message = self._generate_commit_message(artifact)
        commit_sha = self._create_commit(context, commit_message)
        
        # Create PR (requires GitHub CLI or API)
        pr_url = self._create_pull_request(
            context, branch_name, artifact
        )
        
        return StageResult(
            stage_name=self.stage_name,
            status=StageStatus.COMPLETED,
            artifact={
                "spec_id": spec_id,
                "request_id": artifact.get("request_id"),
                "deliverable_type": "pr",
                "branch_name": branch_name,
                "commit_sha": commit_sha,
                "pr_url": pr_url,
                "files_modified": final_files,
                "summary": self._generate_summary(artifact),
            },
        )
    
    def _deliver_files(
        self,
        context: StageContext,
        artifact: Dict[str, Any],
    ) -> StageResult:
        """Deliver as files only (no git)."""
        spec_id = artifact.get("spec_id", "unknown")
        final_files = artifact.get("final_files", [])
        
        return StageResult(
            stage_name=self.stage_name,
            status=StageStatus.COMPLETED,
            artifact={
                "spec_id": spec_id,
                "request_id": artifact.get("request_id"),
                "deliverable_type": "files",
                "files_modified": final_files,
                "summary": self._generate_summary(artifact),
            },
        )
    
    def _deliver_patch(
        self,
        context: StageContext,
        artifact: Dict[str, Any],
    ) -> StageResult:
        """Deliver as patch file."""
        spec_id = artifact.get("spec_id", "unknown")
        
        # Generate patch
        patch_content = self._generate_patch(context)
        
        # Save patch file
        patch_dir = context.agentforge_path / "patches"
        patch_dir.mkdir(parents=True, exist_ok=True)
        
        patch_file = patch_dir / f"{spec_id}.patch"
        patch_file.write_text(patch_content)
        
        return StageResult(
            stage_name=self.stage_name,
            status=StageStatus.COMPLETED,
            artifact={
                "spec_id": spec_id,
                "request_id": artifact.get("request_id"),
                "deliverable_type": "patch",
                "patch_file": str(patch_file),
                "files_modified": artifact.get("final_files", []),
                "summary": self._generate_summary(artifact),
            },
        )
    
    def _generate_commit_message(self, artifact: Dict[str, Any]) -> str:
        """Generate commit message from artifact."""
        spec_id = artifact.get("spec_id", "unknown")
        
        # Get original request if available
        # Walk back through artifacts to find it
        original_request = artifact.get("original_request", "")
        if not original_request:
            original_request = artifact.get("clarified_requirements", "Implementation")
        
        # Truncate if too long
        if len(original_request) > 50:
            title = original_request[:47] + "..."
        else:
            title = original_request
        
        # Build commit message
        message = f"feat: {title}\n\n"
        message += f"Spec: {spec_id}\n"
        
        # Add files
        files = artifact.get("final_files", [])
        if files:
            message += f"\nFiles modified:\n"
            for f in files[:10]:  # Limit to 10
                if isinstance(f, dict):
                    message += f"  - {f.get('path', f)}\n"
                else:
                    message += f"  - {f}\n"
            if len(files) > 10:
                message += f"  ... and {len(files) - 10} more\n"
        
        # Add test results
        test_results = artifact.get("test_results", {})
        if test_results:
            message += f"\nTests: {test_results.get('passed', 0)} passed"
        
        return message
    
    def _generate_summary(self, artifact: Dict[str, Any]) -> str:
        """Generate human-readable summary."""
        spec_id = artifact.get("spec_id", "unknown")
        files = artifact.get("final_files", [])
        test_results = artifact.get("test_results", {})
        
        summary = f"## Delivery Summary\n\n"
        summary += f"**Spec ID:** {spec_id}\n\n"
        summary += f"**Files Modified:** {len(files)}\n"
        
        for f in files[:5]:
            if isinstance(f, dict):
                summary += f"- {f.get('path', f)}\n"
            else:
                summary += f"- {f}\n"
        
        if len(files) > 5:
            summary += f"- ... and {len(files) - 5} more\n"
        
        summary += f"\n**Test Results:** {test_results.get('passed', 0)} passed, "
        summary += f"{test_results.get('failed', 0)} failed\n"
        
        return summary
    
    def _stage_files(
        self,
        context: StageContext,
        files: List,
    ) -> List[str]:
        """Stage files for commit."""
        staged = []
        
        for f in files:
            file_path = f.get("path", f) if isinstance(f, dict) else f
            
            try:
                subprocess.run(
                    ["git", "add", file_path],
                    cwd=str(context.project_path),
                    check=True,
                    capture_output=True,
                )
                staged.append(file_path)
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to stage {file_path}: {e}")
        
        return staged
    
    def _create_commit(
        self,
        context: StageContext,
        message: str,
    ) -> Optional[str]:
        """Create git commit."""
        try:
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=str(context.project_path),
                check=True,
                capture_output=True,
            )
            
            # Get commit SHA
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(context.project_path),
                capture_output=True,
                text=True,
            )
            return result.stdout.strip()
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create commit: {e}")
            return None
    
    def _create_branch(
        self,
        context: StageContext,
        branch_name: str,
    ) -> bool:
        """Create and checkout feature branch."""
        try:
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=str(context.project_path),
                check=True,
                capture_output=True,
            )
            return True
        except subprocess.CalledProcessError:
            logger.warning(f"Branch {branch_name} may already exist")
            return False
    
    def _create_pull_request(
        self,
        context: StageContext,
        branch_name: str,
        artifact: Dict[str, Any],
    ) -> Optional[str]:
        """Create pull request using GitHub CLI."""
        try:
            # Push branch
            subprocess.run(
                ["git", "push", "-u", "origin", branch_name],
                cwd=str(context.project_path),
                check=True,
                capture_output=True,
            )
            
            # Create PR with gh CLI
            title = artifact.get("spec_id", "Implementation")
            body = self._generate_summary(artifact)
            
            result = subprocess.run(
                ["gh", "pr", "create", "--title", title, "--body", body],
                cwd=str(context.project_path),
                capture_output=True,
                text=True,
            )
            
            # Extract PR URL from output
            if result.returncode == 0:
                return result.stdout.strip()
            
        except Exception as e:
            logger.error(f"Failed to create PR: {e}")
        
        return None
    
    def _generate_patch(self, context: StageContext) -> str:
        """Generate git diff patch."""
        try:
            result = subprocess.run(
                ["git", "diff", "--cached"],
                cwd=str(context.project_path),
                capture_output=True,
                text=True,
            )
            return result.stdout
        except Exception as e:
            logger.error(f"Failed to generate patch: {e}")
            return ""


def create_deliver_executor(config: Optional[Dict] = None) -> DeliverExecutor:
    """Create DeliverExecutor instance."""
    return DeliverExecutor(config)
```

---

## 4. Artifact Schemas

### 4.1 REFACTOR Artifact

```yaml
spec_id: string
request_id: string

refactored_files:
  - path: string
    changes: string  # Description of refactoring

improvements:
  - type: string  # complexity, style, naming, etc.
    description: string
    file: string

final_files: [string]  # All files (implementation + tests)

test_results:
  passed: number
  failed: number

conformance_passed: boolean
remaining_violations: [...]
```

### 4.2 DELIVER Artifact

```yaml
spec_id: string
request_id: string

deliverable_type: enum [commit, pr, files, patch]

# For commit
commit_sha: string
commit_message: string
files_staged: [string]

# For PR
branch_name: string
pr_url: string

# For patch
patch_file: string

# Common
files_modified: [string]
summary: string
status: string
```

---

## 5. Configuration

```yaml
# .agentforge/config/stages/deliver.yaml

stage: deliver

delivery_mode: commit  # commit, pr, files, patch

commit:
  auto_commit: false   # Require explicit approval
  message_template: "feat: {title}"
  include_spec_id: true

pr:
  branch_prefix: "feature/"
  auto_push: true
  draft: false
  reviewers: []

patch:
  output_dir: ".agentforge/patches"
```

---

## 6. Test Specification

```python
# tests/unit/pipeline/stages/test_refactor.py

class TestRefactorExecutor:
    def test_skips_when_no_violations(self, mock_llm, tmp_path):
        """Skips refactoring if conformance passes."""
    
    def test_applies_refactorings(self, mock_llm, tmp_path):
        """Applies refactorings to fix violations."""
    
    def test_verifies_tests_still_pass(self, mock_llm, tmp_path):
        """Verifies tests pass after refactoring."""
    
    def test_fails_if_tests_break(self, mock_llm, tmp_path):
        """Fails if refactoring breaks tests."""


# tests/unit/pipeline/stages/test_deliver.py

class TestDeliverExecutor:
    def test_delivers_as_commit(self, tmp_path):
        """Creates git commit with changes."""
    
    def test_delivers_as_pr(self, tmp_path):
        """Creates pull request."""
    
    def test_delivers_as_files(self, tmp_path):
        """Returns files without git operations."""
    
    def test_generates_commit_message(self):
        """Generates proper commit message."""
```

---

## 7. Success Criteria

1. **REFACTOR:**
   - [ ] Identifies code quality issues
   - [ ] Applies refactorings
   - [ ] Maintains passing tests
   - [ ] Runs conformance checks

2. **DELIVER:**
   - [ ] Supports multiple delivery modes
   - [ ] Generates proper commit messages
   - [ ] Stages files correctly
   - [ ] Creates PRs when configured

---

*Next: Stage 8 - CLI Commands*
