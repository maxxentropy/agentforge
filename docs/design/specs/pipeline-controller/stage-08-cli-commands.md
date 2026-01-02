# Pipeline Controller Specification - Stage 8: CLI Commands

**Version:** 1.0  
**Date:** January 2, 2026  
**Status:** Specification  
**Depends On:** Stage 1-7  
**Estimated Effort:** 3-4 days

---

## 1. Overview

### 1.1 Purpose

The CLI provides the user interface for pipeline operations:

```bash
# Primary commands
agentforge start "Add OAuth authentication"     # Full autonomous pipeline
agentforge design "Add OAuth authentication"    # Exits at SPEC
agentforge implement "Add OAuth authentication" # Full implementation
agentforge implement --from-spec SPEC-123       # Skip to RED from existing spec

# Control commands
agentforge status [pipeline_id]                 # Check pipeline status
agentforge resume <pipeline_id>                 # Resume paused pipeline
agentforge approve <pipeline_id>                # Approve and continue
agentforge reject <pipeline_id> [--feedback]    # Reject with feedback
agentforge abort <pipeline_id>                  # Cancel pipeline

# List commands
agentforge pipelines                            # List all pipelines
agentforge pipelines --status running           # Filter by status
```

### 1.2 Command Hierarchy

```
agentforge
├── start         # Full pipeline (INTAKE → DELIVER)
├── design        # Design only (INTAKE → SPEC)
├── implement     # Implementation (from request or spec)
├── test          # Test only (RED phase)
├── fix           # Fix violation (mini pipeline)
│
├── status        # Get pipeline status
├── resume        # Resume paused pipeline
├── approve       # Approve stage output
├── reject        # Reject with feedback
├── abort         # Cancel pipeline
│
├── pipelines     # List pipelines
└── artifacts     # View artifacts
```

---

## 2. Primary Commands

### 2.1 `agentforge start`

```python
# cli/click_commands/pipeline.py

import click
from pathlib import Path


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
    from agentforge.core.pipeline import PipelineController, PipelineConfig
    
    project_path = Path.cwd()
    
    # Configure pipeline
    config_override = {
        "supervised": supervised or iterate,
        "exit_after": exit_after,
        "timeout_seconds": timeout,
    }
    
    # Create controller
    controller = PipelineController(
        project_path=project_path,
        config_override=config_override,
    )
    
    click.echo(f"🚀 Starting pipeline for: {request}")
    click.echo()
    
    # Execute
    result = controller.execute(
        user_request=request,
        pipeline_type="implement",
    )
    
    # Display result
    _display_result(result, delivery_mode)


def _display_result(result, delivery_mode):
    """Display pipeline result."""
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
    else:
        click.echo(click.style(f"❌ Pipeline failed: {result.error}", fg="red"))
        click.echo()
        click.echo(f"Pipeline ID: {result.pipeline_id}")
        click.echo(f"Failed at stage: {result.current_stage}")
        click.echo(f"Stages completed: {', '.join(result.stages_completed)}")
```

### 2.2 `agentforge design`

```python
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
    from agentforge.core.pipeline import PipelineController
    
    project_path = Path.cwd()
    
    controller = PipelineController(
        project_path=project_path,
        config_override={
            "exit_after": "spec",
            "supervised": iterate,
        },
    )
    
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
```

### 2.3 `agentforge implement`

```python
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
    from agentforge.core.pipeline import PipelineController
    
    if not request and not from_spec:
        raise click.UsageError("Either REQUEST or --from-spec is required")
    
    project_path = Path.cwd()
    
    controller = PipelineController(project_path=project_path)
    
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
```

---

## 3. Control Commands

### 3.1 `agentforge status`

```python
@click.command("status")
@click.argument("pipeline_id", required=False)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed status")
@click.pass_context
def status(ctx, pipeline_id, verbose):
    """
    Check pipeline status.
    
    Without PIPELINE_ID, shows most recent pipeline.
    
    Examples:
    
        agentforge status
        
        agentforge status PL-20260102-abc123
        
        agentforge status --verbose
    """
    from agentforge.core.pipeline import PipelineController
    
    project_path = Path.cwd()
    controller = PipelineController(project_path=project_path)
    
    if pipeline_id:
        state = controller.get_status(pipeline_id)
    else:
        # Get most recent
        pipelines = controller.list_pipelines(limit=1)
        state = pipelines[0] if pipelines else None
    
    if not state:
        click.echo("No pipeline found.")
        return
    
    # Display status
    status_colors = {
        "running": "yellow",
        "completed": "green",
        "failed": "red",
        "paused": "cyan",
        "awaiting_approval": "magenta",
        "aborted": "red",
    }
    
    color = status_colors.get(state.status.value, "white")
    
    click.echo(f"Pipeline: {state.pipeline_id}")
    click.echo(f"Type: {state.pipeline_type}")
    click.echo(f"Status: {click.style(state.status.value.upper(), fg=color)}")
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
    
    # Show actions
    click.echo()
    if state.status.value == "paused":
        click.echo("Actions:")
        click.echo(f"  Resume: agentforge resume {state.pipeline_id}")
        click.echo(f"  Abort:  agentforge abort {state.pipeline_id}")
    elif state.status.value == "awaiting_approval":
        click.echo("Actions:")
        click.echo(f"  Approve: agentforge approve {state.pipeline_id}")
        click.echo(f"  Reject:  agentforge reject {state.pipeline_id}")
        click.echo(f"  Abort:   agentforge abort {state.pipeline_id}")
```

### 3.2 `agentforge resume`

```python
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
    from agentforge.core.pipeline import PipelineController
    
    project_path = Path.cwd()
    controller = PipelineController(project_path=project_path)
    
    # Provide feedback if given
    if feedback:
        controller.provide_feedback(pipeline_id, feedback)
    
    click.echo(f"▶️  Resuming pipeline: {pipeline_id}")
    
    result = controller.execute(
        user_request="",  # Not used for resume
        resume_pipeline_id=pipeline_id,
    )
    
    _display_result(result, "commit")
```

### 3.3 `agentforge approve` / `agentforge reject`

```python
@click.command("approve")
@click.argument("pipeline_id")
@click.pass_context
def approve(ctx, pipeline_id):
    """
    Approve current stage and continue pipeline.
    
    Use when pipeline is in 'awaiting_approval' status.
    """
    from agentforge.core.pipeline import PipelineController
    
    project_path = Path.cwd()
    controller = PipelineController(project_path=project_path)
    
    success = controller.approve(pipeline_id)
    
    if success:
        click.echo(click.style("✅ Approved! Pipeline continuing...", fg="green"))
    else:
        click.echo(click.style("❌ Could not approve. Check pipeline status.", fg="red"))


@click.command("reject")
@click.argument("pipeline_id")
@click.option("--feedback", "-f", type=str, help="Feedback for revision")
@click.option("--abort", is_flag=True, help="Abort instead of requesting revision")
@click.pass_context
def reject(ctx, pipeline_id, feedback, abort):
    """
    Reject stage output.
    
    With --feedback: Request revision with feedback
    With --abort: Cancel the pipeline
    """
    from agentforge.core.pipeline import PipelineController
    
    project_path = Path.cwd()
    controller = PipelineController(project_path=project_path)
    
    if abort:
        controller.abort(pipeline_id, reason="User rejected output")
        click.echo(click.style("Pipeline aborted.", fg="yellow"))
    elif feedback:
        controller.provide_feedback(pipeline_id, feedback)
        click.echo(f"📝 Feedback provided. Pipeline will revise.")
        # Trigger re-execution of current stage
        controller.execute(user_request="", resume_pipeline_id=pipeline_id)
    else:
        click.echo("Provide --feedback for revision or --abort to cancel.")
```

### 3.4 `agentforge abort`

```python
@click.command("abort")
@click.argument("pipeline_id")
@click.option("--reason", "-r", type=str, default="User requested", help="Abort reason")
@click.pass_context
def abort(ctx, pipeline_id, reason):
    """
    Abort a running or paused pipeline.
    """
    from agentforge.core.pipeline import PipelineController
    
    project_path = Path.cwd()
    controller = PipelineController(project_path=project_path)
    
    success = controller.abort(pipeline_id, reason)
    
    if success:
        click.echo(click.style(f"⏹️  Pipeline {pipeline_id} aborted.", fg="yellow"))
    else:
        click.echo(click.style("Could not abort. Pipeline may be completed or not found.", fg="red"))
```

---

## 4. List Commands

### 4.1 `agentforge pipelines`

```python
@click.command("pipelines")
@click.option(
    "--status", "-s",
    type=click.Choice(["running", "paused", "completed", "failed", "aborted", "all"]),
    default="all",
    help="Filter by status"
)
@click.option("--limit", "-n", type=int, default=10, help="Number of pipelines to show")
@click.pass_context
def pipelines(ctx, status, limit):
    """
    List pipelines.
    
    Examples:
    
        agentforge pipelines
        
        agentforge pipelines --status running
        
        agentforge pipelines --limit 20
    """
    from agentforge.core.pipeline import PipelineController, PipelineStatus
    
    project_path = Path.cwd()
    controller = PipelineController(project_path=project_path)
    
    # Map status string to enum
    status_filter = None
    if status != "all":
        status_filter = PipelineStatus(status)
    
    pipeline_list = controller.list_pipelines(status=status_filter, limit=limit)
    
    if not pipeline_list:
        click.echo("No pipelines found.")
        return
    
    # Table header
    click.echo()
    click.echo(f"{'ID':<25} {'TYPE':<12} {'STATUS':<15} {'STAGE':<12} {'CREATED':<20}")
    click.echo("-" * 90)
    
    for p in pipeline_list:
        status_str = p.status.value
        click.echo(
            f"{p.pipeline_id:<25} "
            f"{p.pipeline_type:<12} "
            f"{status_str:<15} "
            f"{(p.current_stage or 'N/A'):<12} "
            f"{p.created_at.strftime('%Y-%m-%d %H:%M'):<20}"
        )
```

### 4.2 `agentforge artifacts`

```python
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
        for artifact_file in artifacts_dir.glob(f"*-{stage}.yaml"):
            with open(artifact_file) as f:
                artifact = yaml.safe_load(f)
            
            if output:
                with open(output, "w") as f:
                    yaml.dump(artifact, f, default_flow_style=False)
                click.echo(f"Saved to: {output}")
            else:
                click.echo(yaml.dump(artifact, default_flow_style=False))
            return
        
        click.echo(f"Artifact for stage '{stage}' not found.")
    else:
        # List all artifacts
        click.echo(f"Artifacts for {pipeline_id}:")
        click.echo()
        
        for artifact_file in sorted(artifacts_dir.glob("*.yaml")):
            click.echo(f"  {artifact_file.name}")
```

---

## 5. Command Registration

```python
# cli/click_commands/__init__.py

import click
from .pipeline import (
    start, design, implement, 
    status, resume, approve, reject, abort,
    pipelines, artifacts
)


@click.group()
def cli():
    """AgentForge - Autonomous Development Pipeline"""
    pass


# Register commands
cli.add_command(start)
cli.add_command(design)
cli.add_command(implement)
cli.add_command(status)
cli.add_command(resume)
cli.add_command(approve)
cli.add_command(reject)
cli.add_command(abort)
cli.add_command(pipelines)
cli.add_command(artifacts)
```

---

## 6. Output Formatting

### 6.1 Progress Display

```python
# cli/formatters/progress.py

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
    
    def display_stage_start(self, stage: str):
        icon = self.STAGE_ICONS.get(stage, "▶️")
        click.echo(f"\n{icon} Stage: {stage.upper()}")
        click.echo("-" * 40)
    
    def display_stage_complete(self, stage: str, duration: float):
        click.echo(f"✓ {stage} complete ({duration:.1f}s)")
    
    def display_stage_failed(self, stage: str, error: str):
        click.echo(click.style(f"✗ {stage} failed: {error}", fg="red"))
    
    def display_escalation(self, stage: str, reason: str):
        click.echo(click.style(f"\n⚠️  Escalation at {stage}:", fg="yellow"))
        click.echo(f"   {reason}")
```

---

## 7. Test Specification

```python
# tests/unit/cli/test_pipeline_commands.py

class TestStartCommand:
    def test_start_executes_pipeline(self, cli_runner, mock_controller):
        """start command executes pipeline."""
    
    def test_start_with_supervised_flag(self, cli_runner, mock_controller):
        """--supervised flag enables approval mode."""
    
    def test_start_with_exit_after(self, cli_runner, mock_controller):
        """--exit-after stops at specified stage."""


class TestStatusCommand:
    def test_status_shows_pipeline_info(self, cli_runner, mock_controller):
        """status command displays pipeline information."""
    
    def test_status_without_id_shows_recent(self, cli_runner, mock_controller):
        """status without ID shows most recent pipeline."""


class TestControlCommands:
    def test_approve_calls_controller(self, cli_runner, mock_controller):
        """approve command calls controller.approve()."""
    
    def test_abort_calls_controller(self, cli_runner, mock_controller):
        """abort command calls controller.abort()."""
```

---

## 8. Success Criteria

1. **Commands Work:**
   - [ ] `start` executes full pipeline
   - [ ] `design` exits at SPEC
   - [ ] `implement --from-spec` works
   - [ ] Control commands work correctly

2. **UX Quality:**
   - [ ] Clear progress display
   - [ ] Helpful error messages
   - [ ] Consistent formatting

3. **Integration:**
   - [ ] Commands use PipelineController correctly
   - [ ] State persists between commands

---

*Next: Stage 9 - Configuration System*
