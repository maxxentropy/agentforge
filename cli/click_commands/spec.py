"""
Spec workflow Click commands.

Commands: intake, clarify, analyze, draft, validate, revise
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
    from cli.commands.spec import run_intake

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
    from cli.commands.spec import run_clarify

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
    from cli.commands.spec import run_analyze

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
@click.pass_context
def draft(ctx, intake_file, clarification_file, analysis_file):
    """Run DRAFT phase - generate specification."""
    from cli.commands.spec import run_draft

    args = Args()
    args.intake_file = intake_file
    args.clarification_file = clarification_file
    args.analysis_file = analysis_file
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
    from cli.commands.spec import run_validate

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
    from cli.commands.revision import run_revise

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
