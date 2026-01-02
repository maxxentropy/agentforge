# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: deliver-phase-executor
# @test_path: tests/unit/pipeline/stages/test_deliver.py

"""DELIVER phase executor for TDD pipeline.

The DELIVER phase packages and delivers the final result.
Supports multiple delivery modes: commit, PR, files, patch.
"""

import logging
import subprocess
from typing import Any

from ..llm_stage_executor import OutputValidation
from ..stage_executor import StageContext, StageExecutor, StageResult

logger = logging.getLogger(__name__)


class DeliveryMode:
    """Delivery modes."""
    COMMIT = "commit"           # Git commit only
    PR = "pr"                   # Create pull request
    FILES = "files"             # Just output files (no git)
    PATCH = "patch"             # Generate patch file


class DeliverPhaseExecutor(StageExecutor):
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
        "files_modified",
        "summary",
    ]

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize DeliverPhaseExecutor."""
        self._config = config or {}
        self.delivery_mode = self._config.get("delivery_mode", DeliveryMode.COMMIT)
        self.auto_commit = self._config.get("auto_commit", False)
        self.branch_prefix = self._config.get("branch_prefix", "feature/")

    def execute(self, context: StageContext) -> StageResult:
        """Execute DELIVER phase."""
        input_artifact = context.input_artifacts

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
            return StageResult.failed(
                error=f"Unknown delivery mode: {mode}",
            )

    def _deliver_commit(
        self,
        context: StageContext,
        artifact: dict[str, Any],
    ) -> StageResult:
        """Deliver as git commit."""
        spec_id = artifact.get("spec_id", "unknown")

        # Generate commit message
        commit_message = self._generate_commit_message(artifact)

        # Stage files
        final_files = artifact.get("final_files", [])
        staged = self._stage_files(context, final_files)

        if not staged:
            return StageResult.success(
                artifacts={
                    "spec_id": spec_id,
                    "request_id": artifact.get("request_id"),
                    "deliverable_type": "commit",
                    "commit_sha": None,
                    "commit_message": commit_message,
                    "files_modified": final_files,
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

        return StageResult.success(
            artifacts={
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
        artifact: dict[str, Any],
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

        return StageResult.success(
            artifacts={
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
        artifact: dict[str, Any],
    ) -> StageResult:
        """Deliver as files only (no git)."""
        spec_id = artifact.get("spec_id", "unknown")
        final_files = artifact.get("final_files", [])

        return StageResult.success(
            artifacts={
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
        artifact: dict[str, Any],
    ) -> StageResult:
        """Deliver as patch file."""
        spec_id = artifact.get("spec_id", "unknown")

        # Generate patch
        patch_content = self._generate_patch(context)

        # Save patch file
        agentforge_path = context.project_path / ".agentforge"
        patch_dir = agentforge_path / "patches"
        patch_dir.mkdir(parents=True, exist_ok=True)

        patch_file = patch_dir / f"{spec_id}.patch"
        patch_file.write_text(patch_content)

        return StageResult.success(
            artifacts={
                "spec_id": spec_id,
                "request_id": artifact.get("request_id"),
                "deliverable_type": "patch",
                "patch_file": str(patch_file),
                "files_modified": artifact.get("final_files", []),
                "summary": self._generate_summary(artifact),
            },
        )

    def _generate_commit_message(self, artifact: dict[str, Any]) -> str:
        """Generate commit message from artifact."""
        spec_id = artifact.get("spec_id", "unknown")

        # Get original request if available
        original_request = artifact.get("original_request", "")
        if not original_request:
            original_request = artifact.get("clarified_requirements", "Implementation")

        # Truncate if too long
        title = original_request[:47] + "..." if len(original_request) > 50 else original_request

        # Build commit message
        message = f"feat: {title}\n\n"
        message += f"Spec: {spec_id}\n"

        # Add files
        files = artifact.get("final_files", [])
        if files:
            message += "\nFiles modified:\n"
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

    def _generate_summary(self, artifact: dict[str, Any]) -> str:
        """Generate human-readable summary."""
        spec_id = artifact.get("spec_id", "unknown")
        files = artifact.get("final_files", [])
        test_results = artifact.get("test_results", {})

        summary = "## Delivery Summary\n\n"
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
        files: list,
    ) -> list[str]:
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
            except FileNotFoundError:
                logger.warning("git not found")
                return []

        return staged

    def _create_commit(
        self,
        context: StageContext,
        message: str,
    ) -> str | None:
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
        artifact: dict[str, Any],
    ) -> str | None:
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

    def validate_output(self, artifact: dict[str, Any] | None) -> OutputValidation:
        """Validate DELIVER phase artifact."""
        if artifact is None:
            return OutputValidation(
                valid=False,
                errors=["No artifact produced"],
                warnings=[],
            )

        errors = []
        warnings = []

        # Check required fields
        if not artifact.get("spec_id"):
            errors.append("Missing spec_id")

        if not artifact.get("deliverable_type"):
            errors.append("Missing deliverable_type")

        if "files_modified" not in artifact:
            warnings.append("Missing files_modified in artifact")

        if not artifact.get("summary"):
            warnings.append("Missing summary in artifact")

        return OutputValidation(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )


def create_deliver_executor(config: dict | None = None) -> DeliverPhaseExecutor:
    """Create DeliverPhaseExecutor instance."""
    return DeliverPhaseExecutor(config)
