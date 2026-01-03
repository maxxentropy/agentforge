# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @component_id: pipeline-cli-start, pipeline-cli-design, pipeline-cli-implement
# @component_id: pipeline-cli-status, pipeline-cli-resume, pipeline-cli-approve
# @component_id: pipeline-cli-reject, pipeline-cli-abort
# @component_id: pipeline-cli-pipelines, pipeline-cli-artifacts
# @component_id: pipeline-cli-display-result, pipeline-cli-progress-display
# @test_path: tests/unit/cli/test_pipeline_commands.py

"""
Pipeline CLI commands.

Commands for pipeline operations:
- start: Full autonomous pipeline
- design: Design only (exits at SPEC)
- implement: Implementation pipeline
- status: Check pipeline status
- resume: Resume paused pipeline
- approve/reject: Approval workflow
- abort: Cancel pipeline
- pipelines: List pipelines
- artifacts: View artifacts
"""

from pathlib import Path

import click

# =============================================================================
# Progress Display Helper
# =============================================================================


class PipelineProgressDisplay:
    """Real-time progress display for pipeline execution."""

    STAGE_ICONS = {
        "intake": "📥",
        "clarify": "❓",
        "analyze": "🔍",
        "spec": "📋",
        "red": "🔴",
        "green": "🟢",
        "refactor": "♻️",
        "deliver": "📦",
    }

    def display_stage_start(self, stage: str) -> None:
        """Display stage start message."""
        icon = self.STAGE_ICONS.get(stage, "▶️")
        click.echo(f"\n{icon} Stage: {stage.upper()}")
        click.echo("-" * 40)

    def display_stage_complete(self, stage: str, duration: float) -> None:
        """Display stage completion message."""
        click.echo(f"✓ {stage} complete ({duration:.1f}s)")

    def display_stage_failed(self, stage: str, error: str) -> None:
        """Display stage failure message."""
        click.echo(click.style(f"✗ {stage} failed: {error}", fg="red"))

    def display_escalation(self, stage: str, reason: str) -> None:
        """Display escalation warning."""
        click.echo(click.style(f"\n⚠️  Escalation at {stage}:", fg="yellow"))
        click.echo(f"   {reason}")


# =============================================================================
# Display Result Helper
# =============================================================================


def _display_result(result, delivery_mode: str) -> None:
    """Display pipeline execution result."""
    if result.success:
        click.echo(click.style("✅ Pipeline completed successfully!", fg="green"))
        click.echo()
        click.echo(f"Pipeline ID: {result.pipeline_id}")
        click.echo(f"Stages completed: {', '.join(result.stages_completed)}")
        click.echo(f"Duration: {result.total_duration_seconds:.1f}s")

        if result.deliverable:
            click.echo()
            click.echo("Deliverable:")
            if delivery_mode == "commit":
                click.echo(f"  Commit: {result.deliverable.get('commit_sha', 'N/A')}")
            elif delivery_mode == "pr":
                click.echo(f"  PR: {result.deliverable.get('pr_url', 'N/A')}")
            elif delivery_mode == "patch":
                click.echo(f"  Patch: {result.deliverable.get('patch_file', 'N/A')}")
            elif delivery_mode == "files":
                files = result.deliverable.get('files_modified', [])
                click.echo(f"  Files modified: {len(files)}")
                for f in files[:5]:
                    click.echo(f"    - {f}")
                if len(files) > 5:
                    click.echo(f"    ... and {len(files) - 5} more")
    else:
        click.echo(click.style(f"❌ Pipeline failed: {result.error}", fg="red"))
        click.echo()
        click.echo(f"Pipeline ID: {result.pipeline_id}")
        click.echo(f"Failed at stage: {result.current_stage}")
        click.echo(f"Stages completed: {', '.join(result.stages_completed)}")


def _get_controller(project_path: Path | None = None, config_override: dict | None = None):
    """Get PipelineController instance."""
    from agentforge.core.pipeline import PipelineController

    if project_path is None:
        project_path = Path.cwd()

    return PipelineController(
        project_path=project_path,
        config_override=config_override or {},
    )


# =============================================================================
# PRIMARY COMMANDS
# =============================================================================


@click.command("start")
@click.argument("request")
@click.option(
    "--supervised", "-s",
    is_flag=True,
    help="Pause for approval between stages"
)
@click.option(
    "--exit-after",
    type=click.Choice(["intake", "clarify", "analyze", "spec", "red", "green", "refactor"]),
    help="Exit after specified stage"
)
@click.option(
    "--iterate", "-i",
    is_flag=True,
    help="Enable iteration (pause at SPEC for review)"
)
@click.option(
    "--delivery-mode",
    type=click.Choice(["commit", "pr", "files", "patch"]),
    default="commit",
    help="How to deliver the result"
)
@click.option(
    "--timeout",
    type=int,
    default=3600,
    help="Pipeline timeout in seconds"
)
@click.pass_context
def start(ctx, request, supervised, exit_after, iterate, delivery_mode, timeout):
    """
    Start a full autonomous development pipeline.

    Examples:

        agentforge start "Add OAuth2 authentication"

        agentforge start "Fix login bug" --supervised

        agentforge start "Add feature" --exit-after spec
    """
    project_path = Path.cwd()

    # Configure pipeline
    config_override = {
        "supervised": supervised or iterate,
        "exit_after": exit_after,
        "timeout_seconds": timeout,
        "delivery_mode": delivery_mode,
    }

    try:
        controller = _get_controller(project_path, config_override)

        click.echo(f"🚀 Starting pipeline for: {request}")
        click.echo()

        # Execute pipeline
        result = controller.execute(
            user_request=request,
            pipeline_type="implement",
        )

        # Display result
        _display_result(result, delivery_mode)

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        raise click.Abort() from None


@click.command("design")
@click.argument("request")
@click.option("--iterate", "-i", is_flag=True, help="Pause for spec review")
@click.pass_context
def design(ctx, request, iterate):
    """
    Run design pipeline (exits at SPEC stage).

    Produces a detailed technical specification without implementation.

    Examples:

        agentforge design "Add user authentication"

        agentforge design "Refactor payment module" --iterate
    """
    project_path = Path.cwd()

    config_override = {
        "exit_after": "spec",
        "supervised": iterate,
    }

    try:
        controller = _get_controller(project_path, config_override)

        click.echo(f"📐 Starting design pipeline for: {request}")
        click.echo()

        result = controller.execute(
            user_request=request,
            pipeline_type="design",
        )

        if result.success:
            click.echo(click.style("✅ Design complete!", fg="green"))
            spec_id = result.deliverable.get("spec_id") if result.deliverable else "N/A"
            click.echo(f"Specification: {spec_id}")
            click.echo()
            click.echo(f"View: agentforge artifacts {result.pipeline_id}")
            click.echo(f"Implement: agentforge implement --from-spec {spec_id}")
        else:
            click.echo(click.style(f"❌ Design failed: {result.error}", fg="red"))

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        raise click.Abort() from None


@click.command("implement")
@click.argument("request", required=False)
@click.option(
    "--from-spec",
    type=str,
    help="Start from existing specification ID"
)
@click.option(
    "--skip-to",
    type=click.Choice(["red", "green"]),
    help="Skip to a specific stage"
)
@click.option(
    "--delivery-mode",
    type=click.Choice(["commit", "pr", "files", "patch"]),
    default="commit",
)
@click.pass_context
def implement(ctx, request, from_spec, skip_to, delivery_mode):
    """
    Run implementation pipeline.

    Either provide a request or use --from-spec to continue from design.

    Examples:

        agentforge implement "Add caching layer"

        agentforge implement --from-spec SPEC-20260102-0001

        agentforge implement --from-spec SPEC-123 --skip-to green
    """
    if not request and not from_spec:
        raise click.UsageError("Either REQUEST or --from-spec is required")

    project_path = Path.cwd()

    try:
        controller = _get_controller(project_path, {"delivery_mode": delivery_mode})

        if from_spec:
            # Load existing spec and start from there
            click.echo(f"🔧 Implementing from spec: {from_spec}")

            # Load spec artifact
            spec_path = project_path / ".agentforge" / "specs" / f"{from_spec}.yaml"
            if not spec_path.exists():
                raise click.ClickException(f"Specification not found: {from_spec}")

            import yaml
            with open(spec_path) as f:
                spec = yaml.safe_load(f)

            # Determine starting stage
            start_stage = skip_to or "red"

            result = controller.execute(
                user_request=spec.get("overview", {}).get("description", "Implementation"),
                pipeline_type="implement",
                context={"spec": spec, "start_stage": start_stage},
            )
        else:
            click.echo(f"🔧 Starting implementation for: {request}")
            result = controller.execute(
                user_request=request,
                pipeline_type="implement",
            )

        _display_result(result, delivery_mode)

    except click.ClickException:
        raise
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        raise click.Abort() from None


# =============================================================================
# CONTROL COMMANDS
# =============================================================================


_STATUS_COLORS = {
    "running": "yellow",
    "completed": "green",
    "failed": "red",
    "paused": "cyan",
    "awaiting_approval": "magenta",
    "aborted": "red",
}


def _display_pipeline_status(state, verbose: bool) -> None:
    """Display pipeline status information."""
    status_value = state.status.value if hasattr(state.status, 'value') else str(state.status)
    color = _STATUS_COLORS.get(status_value, "white")

    click.echo(f"Pipeline: {state.pipeline_id}")
    click.echo(f"Type: {state.pipeline_type}")
    click.echo(f"Status: {click.style(status_value.upper(), fg=color)}")
    click.echo(f"Current Stage: {state.current_stage or 'N/A'}")
    click.echo(f"Stages Completed: {', '.join(state.completed_stages) or 'None'}")

    if state.error:
        click.echo(f"Error: {click.style(state.error, fg='red')}")

    if verbose:
        click.echo()
        click.echo("Request:")
        click.echo(f"  {state.user_request}")
        click.echo()
        click.echo(f"Created: {state.created_at}")
        click.echo(f"Updated: {state.updated_at}")
        click.echo(f"Tokens Used: {state.total_tokens_used}")
        click.echo(f"Cost: ${state.total_cost_usd:.4f}")

    _display_status_actions(state, status_value)


def _display_status_actions(state, status_value: str) -> None:
    """Display available actions based on pipeline status."""
    click.echo()
    if status_value == "paused":
        click.echo("Actions:")
        click.echo(f"  Resume: agentforge resume {state.pipeline_id}")
        click.echo(f"  Abort:  agentforge abort {state.pipeline_id}")
    elif status_value == "awaiting_approval":
        click.echo("Actions:")
        click.echo(f"  Approve: agentforge approve {state.pipeline_id}")
        click.echo(f"  Reject:  agentforge reject {state.pipeline_id}")
        click.echo(f"  Abort:   agentforge abort {state.pipeline_id}")


@click.command("status")
@click.argument("pipeline_id", required=False)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed status")
@click.pass_context
def status(ctx, pipeline_id, verbose):
    """Check pipeline status."""
    project_path = Path.cwd()

    try:
        controller = _get_controller(project_path)

        if pipeline_id:
            state = controller.get_status(pipeline_id)
        else:
            pipelines = controller.list_pipelines(limit=1)
            state = pipelines[0] if pipelines else None

        if not state:
            click.echo("No pipeline found.")
            return

        _display_pipeline_status(state, verbose)

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        raise click.Abort() from None


@click.command("resume")
@click.argument("pipeline_id")
@click.option("--feedback", "-f", type=str, help="Provide feedback before resuming")
@click.pass_context
def resume(ctx, pipeline_id, feedback):
    """
    Resume a paused pipeline.

    Examples:

        agentforge resume PL-20260102-abc123

        agentforge resume PL-123 --feedback "Use Google OAuth instead"
    """
    project_path = Path.cwd()

    try:
        controller = _get_controller(project_path)

        # Provide feedback if given
        if feedback:
            controller.provide_feedback(pipeline_id, feedback)

        click.echo(f"▶️  Resuming pipeline: {pipeline_id}")

        result = controller.execute(
            user_request="",  # Not used for resume
            resume_pipeline_id=pipeline_id,
        )

        _display_result(result, "commit")

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        raise click.Abort() from None


@click.command("approve")
@click.argument("pipeline_id")
@click.pass_context
def approve(ctx, pipeline_id):
    """
    Approve current stage and continue pipeline.

    Use when pipeline is in 'awaiting_approval' status. This typically
    occurs at SPEC stage (design review) or before DELIVER (final review).

    Examples:

        agentforge approve PL-20260102-abc123

        # Check what needs approval first
        agentforge status PL-123

    After approval, the pipeline continues to the next stage automatically.
    """
    project_path = Path.cwd()

    try:
        controller = _get_controller(project_path)

        success = controller.approve(pipeline_id)

        if success:
            click.echo(click.style("✅ Approved! Pipeline continuing...", fg="green"))
        else:
            click.echo(click.style("❌ Could not approve. Check pipeline status.", fg="red"))

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        raise click.Abort() from None


@click.command("reject")
@click.argument("pipeline_id")
@click.option("--feedback", "-f", type=str, help="Feedback for revision")
@click.option("--abort", "abort_flag", is_flag=True, help="Abort instead of requesting revision")
@click.pass_context
def reject(ctx, pipeline_id, feedback, abort_flag):
    """
    Reject stage output and request revision or abort.

    Use when a stage output doesn't meet requirements. Provide feedback
    to guide the revision, or use --abort to cancel entirely.

    Examples:

        # Request revision with feedback
        agentforge reject PL-123 --feedback "Need more error handling"

        # Request changes to spec
        agentforge reject PL-123 -f "Add pagination to the API design"

        # Abort the pipeline instead of revising
        agentforge reject PL-123 --abort

    The pipeline will re-run the current stage with your feedback context.
    """
    project_path = Path.cwd()

    try:
        controller = _get_controller(project_path)

        if abort_flag:
            controller.abort(pipeline_id, reason="User rejected output")
            click.echo(click.style("Pipeline aborted.", fg="yellow"))
        elif feedback:
            controller.provide_feedback(pipeline_id, feedback)
            click.echo("📝 Feedback provided. Pipeline will revise.")
            # Trigger re-execution of current stage
            controller.execute(user_request="", resume_pipeline_id=pipeline_id)
        else:
            click.echo("Provide --feedback for revision or --abort to cancel.")

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        raise click.Abort() from None


@click.command("abort")
@click.argument("pipeline_id")
@click.option("--reason", "-r", type=str, default="User requested", help="Abort reason")
@click.pass_context
def abort(ctx, pipeline_id, reason):
    """
    Abort a running or paused pipeline.

    Immediately stops pipeline execution and marks it as aborted.
    Use when you want to cancel a pipeline without completing it.

    Examples:

        agentforge abort PL-20260102-abc123

        agentforge abort PL-123 --reason "Requirements changed"

        agentforge abort PL-123 -r "Starting over with new approach"

    Aborted pipelines cannot be resumed. Start a new pipeline instead.
    """
    project_path = Path.cwd()

    try:
        controller = _get_controller(project_path)

        success = controller.abort(pipeline_id, reason)

        if success:
            click.echo(click.style(f"⏹️  Pipeline {pipeline_id} aborted.", fg="yellow"))
        else:
            click.echo(click.style("Could not abort. Pipeline may be completed or not found.", fg="red"))

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        raise click.Abort() from None


# =============================================================================
# LIST COMMANDS
# =============================================================================


@click.command("pipelines")
@click.option(
    "--status", "-s", "status_filter",
    type=click.Choice(["running", "paused", "completed", "failed", "aborted", "all"]),
    default="all",
    help="Filter by status"
)
@click.option("--limit", "-n", type=int, default=10, help="Number of pipelines to show")
@click.pass_context
def pipelines(ctx, status_filter, limit):
    """
    List pipelines.

    Examples:

        agentforge pipelines

        agentforge pipelines --status running

        agentforge pipelines --limit 20
    """
    project_path = Path.cwd()

    try:
        controller = _get_controller(project_path)

        # Map status string to enum if not "all"
        filter_status = None
        if status_filter != "all":
            from agentforge.core.pipeline import PipelineStatus
            filter_status = PipelineStatus(status_filter)

        pipeline_list = controller.list_pipelines(status=filter_status, limit=limit)

        if not pipeline_list:
            click.echo("No pipelines found.")
            return

        # Table header
        click.echo()
        click.echo(f"{'ID':<25} {'TYPE':<12} {'STATUS':<15} {'STAGE':<12} {'CREATED':<20}")
        click.echo("-" * 90)

        for p in pipeline_list:
            status_val = p.status.value if hasattr(p.status, 'value') else str(p.status)
            created = p.created_at.strftime('%Y-%m-%d %H:%M') if hasattr(p.created_at, 'strftime') else str(p.created_at)
            click.echo(
                f"{p.pipeline_id:<25} "
                f"{p.pipeline_type:<12} "
                f"{status_val:<15} "
                f"{(p.current_stage or 'N/A'):<12} "
                f"{created:<20}"
            )

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        raise click.Abort() from None


@click.command("artifacts")
@click.argument("pipeline_id")
@click.option("--stage", "-s", type=str, help="Show specific stage artifact")
@click.option("--output", "-o", type=click.Path(), help="Output to file")
@click.pass_context
def artifacts(ctx, pipeline_id, stage, output):
    """
    View pipeline artifacts.

    Examples:

        agentforge artifacts PL-20260102-abc123

        agentforge artifacts PL-123 --stage spec

        agentforge artifacts PL-123 --stage spec --output spec.yaml
    """
    import yaml

    project_path = Path.cwd()
    artifacts_dir = project_path / ".agentforge" / "artifacts" / pipeline_id

    if not artifacts_dir.exists():
        click.echo(f"No artifacts found for pipeline: {pipeline_id}")
        return

    if stage:
        # Find specific stage artifact
        found = False
        for artifact_file in artifacts_dir.glob(f"*-{stage}.yaml"):
            with open(artifact_file) as f:
                artifact = yaml.safe_load(f)

            if output:
                with open(output, "w") as f:
                    yaml.dump(artifact, f, default_flow_style=False)
                click.echo(f"Saved to: {output}")
            else:
                click.echo(yaml.dump(artifact, default_flow_style=False))
            found = True
            break

        if not found:
            click.echo(f"Artifact for stage '{stage}' not found.")
    else:
        # List all artifacts
        click.echo(f"Artifacts for {pipeline_id}:")
        click.echo()

        for artifact_file in sorted(artifacts_dir.glob("*.yaml")):
            click.echo(f"  {artifact_file.name}")
