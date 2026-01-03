# @spec_file: .agentforge/specs/core-contracts-v1.yaml
# @spec_id: core-contracts-v1
# @component_id: contract-cli
# @test_path: tests/unit/contracts/test_cli.py

"""
Task Contract CLI Commands
==========================

CLI commands for task contract management (autonomous execution contracts).

Note: These are distinct from code quality contracts (`agentforge contracts`).
Task contracts govern autonomous pipeline execution with:
- Stage schemas and validation rules
- Escalation triggers for human judgment
- Quality gates between stages

Commands:
- draft: Draft contracts for a request
- review: Review pending drafts
- approve: Approve a draft
- list: List contracts (approved and drafts)
- show: Show contract details

Example usage:
    agentforge task-contracts draft "Add user authentication"
    agentforge task-contracts review DRAFT-20240103-120000
    agentforge task-contracts list --drafts
    agentforge task-contracts list --approved
"""

import sys
from pathlib import Path
from typing import Any

import click

from .draft import ApprovedContracts, ContractDraft
from .drafter import CodebaseContext, ContractDrafter, DrafterConfig
from .registry import ContractRegistry, generate_contract_set_id
from .reviewer import (
    ContractReviewer,
    OverallDecision,
    ReviewDecision,
    ReviewFeedback,
    StageDecision,
)


def get_registry(ctx: click.Context) -> ContractRegistry:
    """Get or create contract registry from context."""
    project_path = ctx.obj.get("project_path", Path.cwd())
    return ContractRegistry(project_path)


def get_llm_client(ctx: click.Context):
    """Get LLM client from context or create one."""
    from agentforge.core.llm.factory import LLMClientFactory

    return LLMClientFactory.create()


@click.group(name="task-contracts")
@click.pass_context
def task_contracts(ctx):
    """Task contract management for autonomous execution."""
    if ctx.obj is None:
        ctx.obj = {}
    if "project_path" not in ctx.obj:
        ctx.obj["project_path"] = Path.cwd()


@task_contracts.command("draft")
@click.argument("request", type=str)
@click.option("--project", "-p", type=click.Path(exists=True), help="Project path")
@click.option("--save/--no-save", default=True, help="Save draft to registry")
@click.pass_context
def draft_command(ctx, request: str, project: str | None, save: bool):
    """Draft contracts for a request.

    REQUEST is the natural language description of the task.

    Example:
        agentforge contract draft "Add user authentication with JWT"
    """
    project_path = Path(project) if project else ctx.obj.get("project_path", Path.cwd())

    click.echo("Drafting contracts...")
    click.echo(f"Request: {request}")
    click.echo()

    try:
        llm_client = get_llm_client(ctx)
    except Exception as e:
        click.echo(f"Error creating LLM client: {e}", err=True)
        click.echo("Set ANTHROPIC_API_KEY or use AGENTFORGE_LLM_MODE=simulated", err=True)
        sys.exit(1)

    # Create drafter
    config = DrafterConfig(use_thinking=True)
    drafter = ContractDrafter(llm_client, config=config)

    # Gather context (could be enhanced with actual codebase profiling)
    context = CodebaseContext(
        project_name=project_path.name,
    )

    # Draft contracts
    try:
        draft = drafter.draft(request, codebase_context=context)
    except Exception as e:
        click.echo(f"Error drafting contracts: {e}", err=True)
        sys.exit(1)

    # Display draft
    reviewer = ContractReviewer()
    click.echo(reviewer.format_for_display(draft))

    # Save if requested
    if save:
        registry = ContractRegistry(project_path)
        draft_id = registry.save_draft(draft)
        click.echo(f"Draft saved: {draft_id}")
        click.echo(f"Review with: agentforge contract review {draft_id}")


@task_contracts.command("review")
@click.argument("draft_id", type=str)
@click.option("--project", "-p", type=click.Path(exists=True), help="Project path")
@click.option("--request-id", "-r", type=str, help="Request ID to associate")
@click.pass_context
def review_command(ctx, draft_id: str, project: str | None, request_id: str | None):
    """Review a contract draft interactively.

    DRAFT_ID is the identifier of the draft to review.

    Example:
        agentforge contract review DRAFT-20240103-120000
    """
    project_path = Path(project) if project else ctx.obj.get("project_path", Path.cwd())
    registry = ContractRegistry(project_path)

    # Load draft
    draft = registry.get_draft(draft_id)
    if draft is None:
        click.echo(f"Draft not found: {draft_id}", err=True)
        sys.exit(1)

    # Start interactive review
    reviewer = ContractReviewer()
    session = reviewer.create_session(draft)

    # Display draft
    click.echo(reviewer.format_for_display(draft))

    # Interactive review loop
    feedback = ReviewFeedback()
    stage_decisions = []

    for stage in draft.stage_contracts:
        click.echo()
        click.echo(reviewer.format_stage_for_review(stage))
        click.echo()

        while True:
            choice = click.prompt(
                f"[A]pprove [M]odify [S]kip for {stage.stage_name}",
                type=click.Choice(["A", "M", "S", "a", "m", "s"], case_sensitive=False),
                default="A",
            )

            if choice.upper() == "A":
                stage_decisions.append(
                    StageDecision(stage.stage_name, ReviewDecision.APPROVE)
                )
                click.echo(f"  {stage.stage_name}: Approved")
                break
            elif choice.upper() == "M":
                notes = click.prompt("Notes for modification", default="")
                stage_decisions.append(
                    StageDecision(stage.stage_name, ReviewDecision.MODIFY, notes=notes)
                )
                click.echo(f"  {stage.stage_name}: Marked for modification")
                break
            elif choice.upper() == "S":
                click.echo(f"  {stage.stage_name}: Skipped")
                break

    feedback.stage_decisions = stage_decisions

    # Handle open questions
    if draft.open_questions:
        click.echo()
        click.echo("OPEN QUESTIONS:")
        answered = {}
        for q in draft.open_questions:
            click.echo(f"  {q.question}")
            if q.suggested_answers:
                for i, ans in enumerate(q.suggested_answers, 1):
                    click.echo(f"    {i}. {ans}")
            answer = click.prompt("Your answer (or press Enter to skip)", default="")
            if answer:
                answered[q.question_id] = answer
        feedback.answered_questions = answered

    # Handle assumptions
    if draft.assumptions:
        click.echo()
        click.echo("ASSUMPTIONS TO VALIDATE:")
        validated = {}
        for a in draft.assumptions:
            click.echo(f"  [{a.confidence:.0%}] {a.statement}")
            if a.impact_if_wrong:
                click.echo(f"      Impact if wrong: {a.impact_if_wrong}")
            valid = click.confirm("Is this assumption correct?", default=True)
            validated[a.assumption_id] = valid
        feedback.validated_assumptions = validated

    # Final decision
    click.echo()
    click.echo("FINAL DECISION:")
    choice = click.prompt(
        "[A]pprove all [R]efine [C]ancel",
        type=click.Choice(["A", "R", "C", "a", "r", "c"], case_sensitive=False),
        default="A" if feedback.all_stages_approved() else "R",
    )

    if choice.upper() == "A":
        feedback.overall_decision = OverallDecision.APPROVE
        session = reviewer.apply_feedback(session, feedback)

        # Generate request ID if not provided
        if not request_id:
            from datetime import UTC, datetime
            request_id = f"REQ-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}"

        approved = reviewer.finalize(session, request_id)
        if approved:
            contract_id = registry.register(approved)
            registry.delete_draft(draft_id)
            click.echo()
            click.echo(f"Contracts approved and registered: {contract_id}")
            click.echo(f"Request ID: {request_id}")
        else:
            click.echo("Could not finalize approval", err=True)

    elif choice.upper() == "R":
        feedback.overall_decision = OverallDecision.REFINE
        click.echo("Draft marked for refinement. Re-run draft with feedback.")

    else:
        click.echo("Review cancelled.")


@task_contracts.command("list")
@click.option("--drafts", is_flag=True, help="List pending drafts")
@click.option("--approved", is_flag=True, help="List approved contracts")
@click.option("--project", "-p", type=click.Path(exists=True), help="Project path")
@click.pass_context
def list_command(ctx, drafts: bool, approved: bool, project: str | None):
    """List contracts and drafts.

    Example:
        agentforge contract list --drafts
        agentforge contract list --approved
    """
    project_path = Path(project) if project else ctx.obj.get("project_path", Path.cwd())
    registry = ContractRegistry(project_path)

    # Default to showing both
    if not drafts and not approved:
        drafts = True
        approved = True

    if drafts:
        draft_list = registry.list_drafts()
        click.echo("PENDING DRAFTS:")
        if draft_list:
            for d in draft_list:
                click.echo(
                    f"  {d['draft_id']}: {d['request_summary'][:50]} "
                    f"({d['detected_scope']}, {d['confidence']:.0%})"
                )
        else:
            click.echo("  (none)")
        click.echo()

    if approved:
        approved_list = registry.list_approved()
        click.echo("APPROVED CONTRACTS:")
        if approved_list:
            for a in approved_list:
                click.echo(
                    f"  {a['contract_set_id']}: request={a['request_id']} "
                    f"(v{a['version']}, {a['stage_count']} stages)"
                )
        else:
            click.echo("  (none)")


@task_contracts.command("show")
@click.argument("contract_id", type=str)
@click.option("--project", "-p", type=click.Path(exists=True), help="Project path")
@click.option("--yaml", "as_yaml", is_flag=True, help="Output as YAML")
@click.pass_context
def show_command(ctx, contract_id: str, project: str | None, as_yaml: bool):
    """Show details of a contract or draft.

    CONTRACT_ID can be a draft ID or approved contract ID.

    Example:
        agentforge contract show DRAFT-20240103-120000
        agentforge contract show CONTRACT-20240103-120000 --yaml
    """
    project_path = Path(project) if project else ctx.obj.get("project_path", Path.cwd())
    registry = ContractRegistry(project_path)

    # Try as draft first
    if contract_id.startswith("DRAFT"):
        item = registry.get_draft(contract_id)
        if item:
            if as_yaml:
                click.echo(item.to_yaml())
            else:
                reviewer = ContractReviewer()
                click.echo(reviewer.format_for_display(item))
            return

    # Try as approved contract
    item = registry.get(contract_id)
    if item:
        if as_yaml:
            click.echo(item.to_yaml())
        else:
            click.echo(f"Contract Set: {item.contract_set_id}")
            click.echo(f"Request ID: {item.request_id}")
            click.echo(f"Version: {item.version}")
            click.echo(f"Approved: {item.approved_at}")
            click.echo(f"Stages: {len(item.stage_contracts)}")
            for sc in item.stage_contracts:
                click.echo(f"  - {sc.stage_name}")
            if item.escalation_triggers:
                click.echo(f"Escalation Triggers: {len(item.escalation_triggers)}")
            if item.quality_gates:
                click.echo(f"Quality Gates: {len(item.quality_gates)}")
        return

    click.echo(f"Contract not found: {contract_id}", err=True)
    sys.exit(1)


@task_contracts.command("approve")
@click.argument("draft_id", type=str)
@click.option("--request-id", "-r", type=str, required=True, help="Request ID")
@click.option("--project", "-p", type=click.Path(exists=True), help="Project path")
@click.pass_context
def approve_command(ctx, draft_id: str, request_id: str, project: str | None):
    """Approve a draft without interactive review.

    DRAFT_ID is the identifier of the draft to approve.

    Example:
        agentforge contract approve DRAFT-20240103-120000 -r REQ-001
    """
    project_path = Path(project) if project else ctx.obj.get("project_path", Path.cwd())
    registry = ContractRegistry(project_path)

    # Load draft
    draft = registry.get_draft(draft_id)
    if draft is None:
        click.echo(f"Draft not found: {draft_id}", err=True)
        sys.exit(1)

    # Create approved contracts directly from draft
    approved = ApprovedContracts.from_draft(
        draft,
        contract_set_id=generate_contract_set_id(),
        request_id=request_id,
    )

    # Register and delete draft
    contract_id = registry.register(approved)
    registry.delete_draft(draft_id)

    click.echo(f"Approved: {contract_id}")
    click.echo(f"Request ID: {request_id}")


@task_contracts.command("delete")
@click.argument("draft_id", type=str)
@click.option("--project", "-p", type=click.Path(exists=True), help="Project path")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete_command(ctx, draft_id: str, project: str | None, force: bool):
    """Delete a draft.

    Example:
        agentforge contract delete DRAFT-20240103-120000
    """
    project_path = Path(project) if project else ctx.obj.get("project_path", Path.cwd())
    registry = ContractRegistry(project_path)

    # Check draft exists
    draft = registry.get_draft(draft_id)
    if draft is None:
        click.echo(f"Draft not found: {draft_id}", err=True)
        sys.exit(1)

    # Confirm
    if not force:
        click.echo(f"Draft: {draft_id}")
        click.echo(f"Summary: {draft.request_summary}")
        if not click.confirm("Delete this draft?"):
            click.echo("Cancelled.")
            return

    if registry.delete_draft(draft_id):
        click.echo(f"Deleted: {draft_id}")
    else:
        click.echo("Failed to delete draft", err=True)
        sys.exit(1)
