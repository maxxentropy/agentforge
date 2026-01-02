"""
Spec workflow Click commands.

Commands: intake, clarify, analyze, draft, validate, revise, adapt
"""

import click


class Args:
    """Simple namespace for passing args to handler functions."""
    pass


@click.command(help='Process initial feature request into structured intake record')
@click.option('--request', '-r', required=True, help='Feature request description')
@click.option('--priority', '-p', type=click.Choice(['critical', 'high', 'medium', 'low']),
              help='Request priority level')
@click.pass_context
def intake(ctx, request, priority):
    """Run INTAKE phase - capture and structure feature request."""
    from agentforge.cli.commands.spec import run_intake

    args = Args()
    args.request = request
    args.priority = priority
    args.use_api = ctx.obj.get('use_api', False)
    run_intake(args)


@click.command(help='Clarify ambiguities in the intake record')
@click.option('--intake-file', default='outputs/intake_record.yaml',
              type=click.Path(), help='Path to intake record')
@click.option('--answer', '-a', help='Answer to previous clarification question')
@click.pass_context
def clarify(ctx, intake_file, answer):
    """Run CLARIFY phase - resolve ambiguities."""
    from agentforge.cli.commands.spec import run_clarify

    args = Args()
    args.intake_file = intake_file
    args.answer = answer
    args.use_api = ctx.obj.get('use_api', False)
    run_clarify(args)


@click.command(help='Analyze codebase context for the feature')
@click.option('--intake-file', default='outputs/intake_record.yaml',
              type=click.Path(exists=True), help='Path to intake record')
@click.option('--clarification-file', default='outputs/clarification_log.yaml',
              type=click.Path(), help='Path to clarification log')
@click.option('--code-context', help='Manual code context to include')
@click.option('--project-path', type=click.Path(exists=True),
              help='Project path for automatic context retrieval')
@click.pass_context
def analyze(ctx, intake_file, clarification_file, code_context, project_path):
    """Run ANALYZE phase - gather implementation context."""
    from agentforge.cli.commands.spec import run_analyze

    args = Args()
    args.intake_file = intake_file
    args.clarification_file = clarification_file
    args.code_context = code_context
    args.project_path = project_path
    args.use_api = ctx.obj.get('use_api', False)
    run_analyze(args)


@click.command(help='Draft specification from analysis')
@click.option('--intake-file', default='outputs/intake_record.yaml',
              type=click.Path(exists=True), help='Path to intake record')
@click.option('--clarification-file', default='outputs/clarification_log.yaml',
              type=click.Path(), help='Path to clarification log')
@click.option('--analysis-file', default='outputs/analysis_report.yaml',
              type=click.Path(exists=True), help='Path to analysis report')
@click.option('--extend-spec', '-e', help='Extend existing spec instead of creating new (prevents fragmentation)')
@click.option('--new-spec', is_flag=True, help='Force creation of new spec (skip placement analysis)')
@click.pass_context
def draft(ctx, intake_file, clarification_file, analysis_file, extend_spec, new_spec):
    """
    Run DRAFT phase - generate specification.

    \b
    Spec Placement:
        By default, DRAFT analyzes the existing spec space and recommends
        whether to extend an existing spec or create a new one. Use flags
        to override:
        --extend-spec cli-v1    Explicitly extend cli-v1 spec
        --new-spec              Force new spec creation
    """
    from agentforge.cli.commands.spec import run_draft

    args = Args()
    args.intake_file = intake_file
    args.clarification_file = clarification_file
    args.analysis_file = analysis_file
    args.extend_spec = extend_spec
    args.new_spec = new_spec
    args.use_api = ctx.obj.get('use_api', False)
    run_draft(args)


@click.command('validate', help='Validate specification for completeness')
@click.option('--spec-file', default='outputs/specification.yaml',
              type=click.Path(exists=True), help='Path to specification')
@click.option('--analysis-file', default='outputs/analysis_report.yaml',
              type=click.Path(), help='Path to analysis report')
@click.pass_context
def validate_spec(ctx, spec_file, analysis_file):
    """Run VALIDATE phase - check specification quality."""
    from agentforge.cli.commands.spec import run_validate

    args = Args()
    args.spec_file = spec_file
    args.analysis_file = analysis_file
    args.use_api = ctx.obj.get('use_api', False)
    run_validate(args)


@click.command(help='Revise specification based on validation feedback')
@click.option('--spec-file', default='outputs/specification.yaml',
              type=click.Path(exists=True), help='Path to specification')
@click.option('--validation-file', default='outputs/validation_report.yaml',
              type=click.Path(exists=True), help='Path to validation report')
@click.option('--auto', is_flag=True, help='Autonomous mode')
@click.option('--continue', '--resume', 'resume', is_flag=True, help='Continue session')
@click.option('--apply', is_flag=True, help='Apply decisions')
@click.option('--status', is_flag=True, help='Show session status')
@click.option('--force', is_flag=True, help='Start fresh session')
@click.pass_context
def revise(ctx, spec_file, validation_file, auto, resume, apply, status, force):
    """Run REVISE phase - fix validation issues."""
    from agentforge.cli.commands.revision import run_revise

    args = Args()
    args.spec_file = spec_file
    args.validation_file = validation_file
    args.auto = auto
    args.resume = resume
    args.apply = apply
    args.status = status
    args.force = force
    args.use_api = ctx.obj.get('use_api', False)
    run_revise(args)


@click.command(help='Adapt external specification to AgentForge format')
@click.option('--input', '-i', 'input_file', required=True,
              type=click.Path(exists=True), help='External spec file (markdown, YAML, or text)')
@click.option('--spec-id', '-s', help='Override spec ID (auto-generated if not provided)')
@click.option('--output', '-o', default='outputs/specification.yaml',
              type=click.Path(), help='Output path for adapted spec')
@click.option('--profile', default='.agentforge/codebase_profile.yaml',
              type=click.Path(), help='Codebase profile for context')
@click.option('--skip-review', is_flag=True, help='Skip SA review (for trusted specs)')
@click.option('--extend-spec', '-e', help='Explicitly extend an existing spec (prevents fragmentation)')
@click.option('--new-spec', is_flag=True, help='Force creation of new spec (skip placement analysis)')
@click.pass_context
def adapt(ctx, input_file, spec_id, output, profile, skip_review, extend_spec, new_spec):
    """
    Adapt external specification to AgentForge codebase conventions.

    This is the ON-RAMP for external specs. It:
    - Takes a rich external spec as PRIMARY INPUT
    - Analyzes spec space to prevent fragmentation
    - Uses SA agent to map concepts to codebase reality
    - Produces a canonical draft compatible with VALIDATE/REVISE/TDFLOW

    The external spec is treated as the SOURCE OF TRUTH.
    ADAPT transforms, it doesn't second-guess.

    \b
    Spec Placement:
        By default, ADAPT analyzes the existing spec space and recommends
        whether to extend an existing spec or create a new one. Use flags
        to override:
        --extend-spec cli-v1    Explicitly extend cli-v1 spec
        --new-spec              Force new spec creation

    \b
    Example:
        agentforge adapt --input external_spec.md
        agentforge adapt --input feature.md --extend-spec core-api-v1
        agentforge validate  # Continue with existing workflow
        agentforge revise
        agentforge tdflow start --spec outputs/specification.yaml
    """
    from agentforge.cli.commands.spec_adapt import run_adapt

    args = Args()
    args.input_file = input_file
    args.spec_id = spec_id
    args.output = output
    args.profile = profile
    args.skip_review = skip_review
    args.extend_spec = extend_spec
    args.new_spec = new_spec
    args.use_api = ctx.obj.get('use_api', False) if ctx.obj else False
    run_adapt(args)
