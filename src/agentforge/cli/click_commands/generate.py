# @spec_file: .agentforge/specs/cli-click-commands-v1.yaml
# @spec_id: cli-click-commands-v1
# @component_id: cli-click_commands-generate
# @test_path: tests/unit/tools/cicd/test_outputs.py

"""
Generate CLI Commands
=====================

Commands for LLM-powered code generation.
"""

import asyncio
from pathlib import Path

import click
import yaml


@click.group("generate", help="LLM code generation commands")
def generate():
    """LLM code generation commands."""
    pass


def _build_generation_context(spec_data: dict, phase: str, component: str | None):
    """Build GenerationContext from spec data and options."""
    from agentforge.core.generate.domain import GenerationContext, GenerationPhase

    phase_map = {
        "red": GenerationPhase.RED,
        "green": GenerationPhase.GREEN,
        "refactor": GenerationPhase.REFACTOR,
    }
    gen_phase = phase_map[phase]

    component_name = component
    if not component_name and spec_data.get("components"):
        component_name = spec_data["components"][0].get("name")

    existing_tests = None
    existing_impl = None
    if gen_phase in (GenerationPhase.GREEN, GenerationPhase.REFACTOR):
        existing_tests = _load_existing_code(spec_data, component_name, "test_file")
    if gen_phase == GenerationPhase.REFACTOR:
        existing_impl = _load_existing_code(spec_data, component_name, "impl_file")

    return GenerationContext(
        spec=spec_data,
        phase=gen_phase,
        component_name=component_name,
        existing_tests=existing_tests,
        existing_impl=existing_impl,
    ), component_name


def _display_generation_result(result, dry_run: bool):
    """Display generation result with appropriate formatting."""
    if result.success:
        click.echo(click.style("✓ Generation successful", fg="green"))
        click.echo(f"  Files: {result.file_count}")
        click.echo(f"  Tokens: {result.tokens_used}")
        click.echo(f"  Duration: {result.duration_seconds:.1f}s")
        click.echo()
        status = "would create" if dry_run else "created"
        for file in result.files:
            click.echo(f"  {status}: {file.path}")
        if result.explanation:
            click.echo()
            click.echo("Explanation:")
            click.echo(result.explanation[:500])
    else:
        click.echo(click.style("✗ Generation failed", fg="red"))
        click.echo(f"  Error: {result.error}")
        if result.raw_response:
            click.echo()
            click.echo("Raw response (first 500 chars):")
            click.echo(result.raw_response[:500])


@generate.command("code")
@click.option(
    "--spec",
    "-s",
    type=click.Path(exists=True),
    required=True,
    help="Path to specification.yaml",
)
@click.option(
    "--phase",
    "-p",
    type=click.Choice(["red", "green", "refactor"]),
    required=True,
    help="Generation phase",
)
@click.option(
    "--component",
    "-c",
    help="Specific component to generate (default: first component)",
)
@click.option(
    "--model",
    "-m",
    default="claude-sonnet-4-20250514",
    help="Model to use for generation",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be generated without writing files",
)
@click.option(
    "--max-tokens",
    type=int,
    default=8192,
    help="Maximum tokens for response",
)
def code(spec: str, phase: str, component: str, model: str, dry_run: bool, max_tokens: int):
    """Generate code from specification using LLM."""
    from agentforge.core.generate.engine import GenerationEngine
    from agentforge.core.generate.provider import ManualProvider, get_provider

    spec_path = Path(spec)
    with open(spec_path) as f:
        spec_data = yaml.safe_load(f)

    context, component_name = _build_generation_context(spec_data, phase, component)
    provider = get_provider(model=model)

    if isinstance(provider, ManualProvider):
        click.echo("No API key found. Using manual mode.")
        click.echo("Set ANTHROPIC_API_KEY environment variable for automatic generation.")
        click.echo()

    engine = GenerationEngine(provider=provider)
    click.echo(f"Generating {phase.upper()} phase code")
    click.echo(f"  Spec: {spec_path}")
    click.echo(f"  Component: {component_name or 'all'}")
    click.echo(f"  Model: {provider.model_name}")
    if dry_run:
        click.echo("  Mode: DRY RUN (no files will be written)")
    click.echo()

    try:
        result = asyncio.run(engine.generate(context, dry_run=dry_run, max_tokens=max_tokens))
    except KeyboardInterrupt:
        click.echo("\nGeneration cancelled.")
        return

    _display_generation_result(result, dry_run)


@generate.command("parse-response")
@click.argument("response_file", type=click.Path(exists=True))
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    help="Directory to write parsed files (default: current directory)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show parsed files without writing",
)
@click.option(
    "--no-validate",
    is_flag=True,
    help="Skip Python syntax validation",
)
def parse_response(response_file: str, output_dir: str, dry_run: bool, no_validate: bool):
    """Parse a manually-obtained LLM response file.

    Use this when running in manual mode without an API key.
    The response file should contain the LLM's response with code blocks.

    Examples:
        agentforge generate parse-response .agentforge/generation_response.txt
        agentforge generate parse-response response.txt --output-dir src/
        agentforge generate parse-response response.txt --dry-run
    """
    from agentforge.core.generate.domain import ParseError
    from agentforge.core.generate.parser import ResponseParser
    from agentforge.core.generate.writer import CodeWriter

    # Read response file
    response_path = Path(response_file)
    response = response_path.read_text()

    # Parse response
    parser = ResponseParser(validate_syntax=not no_validate)

    try:
        files, explanation = parser.parse_with_explanation(response)
    except ParseError as e:
        click.echo(click.style("✗ Parse error", fg="red"))
        click.echo(f"  {e.message}")
        if e.raw_response:
            click.echo()
            click.echo("Response excerpt:")
            click.echo(e.raw_response[:300])
        return

    click.echo(f"Parsed {len(files)} file(s) from response")
    click.echo()

    for file in files:
        click.echo(f"  {file.path} ({file.line_count} lines)")

    if explanation:
        click.echo()
        click.echo("Explanation:")
        click.echo(explanation[:300])

    # Write files unless dry run
    if not dry_run:
        project_root = Path(output_dir) if output_dir else Path.cwd()
        writer = CodeWriter(project_root=project_root, add_header=False)

        try:
            written = writer.write(files)
            click.echo()
            click.echo(click.style("✓ Files written successfully", fg="green"))
            for path in written:
                click.echo(f"  {path}")
        except Exception as e:
            click.echo(click.style(f"✗ Write error: {e}", fg="red"))
    else:
        click.echo()
        click.echo("Dry run - no files written")


@generate.command("prompt")
@click.option(
    "--spec",
    "-s",
    type=click.Path(exists=True),
    required=True,
    help="Path to specification.yaml",
)
@click.option(
    "--phase",
    "-p",
    type=click.Choice(["red", "green", "refactor"]),
    required=True,
    help="Generation phase",
)
@click.option(
    "--component",
    "-c",
    help="Specific component",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file (default: stdout)",
)
def prompt(spec: str, phase: str, component: str, output: str):
    """Generate and display the prompt that would be sent to the LLM.

    Useful for debugging or manual generation workflows.

    Examples:
        agentforge generate prompt --spec spec.yaml --phase red
        agentforge generate prompt --spec spec.yaml --phase green -o prompt.txt
    """
    from agentforge.core.generate.domain import GenerationContext, GenerationPhase
    from agentforge.core.generate.prompt_builder import PromptBuilder

    # Load specification
    spec_path = Path(spec)
    with open(spec_path) as f:
        spec_data = yaml.safe_load(f)

    # Determine phase
    phase_map = {
        "red": GenerationPhase.RED,
        "green": GenerationPhase.GREEN,
        "refactor": GenerationPhase.REFACTOR,
    }
    gen_phase = phase_map[phase]

    # Get component
    component_name = component
    if not component_name and spec_data.get("components"):
        component_name = spec_data["components"][0].get("name")

    # Get existing code for GREEN/REFACTOR
    existing_tests = None
    existing_impl = None

    if gen_phase in (GenerationPhase.GREEN, GenerationPhase.REFACTOR):
        existing_tests = _load_existing_code(spec_data, component_name, "test_file")

    if gen_phase == GenerationPhase.REFACTOR:
        existing_impl = _load_existing_code(spec_data, component_name, "impl_file")

    # Build context
    context = GenerationContext(
        spec=spec_data,
        phase=gen_phase,
        component_name=component_name,
        existing_tests=existing_tests,
        existing_impl=existing_impl,
    )

    # Build prompt
    builder = PromptBuilder()
    prompt_text = builder.build(context)

    # Output
    if output:
        output_path = Path(output)
        output_path.write_text(prompt_text)
        click.echo(f"Prompt written to {output_path}")
        click.echo(f"  Length: {len(prompt_text)} chars (~{len(prompt_text)//4} tokens)")
    else:
        click.echo(prompt_text)


def _load_existing_code(spec_data: dict, component_name: str, file_key: str) -> str | None:
    """Load existing code from component's file if it exists."""
    if not component_name:
        return None

    for comp in spec_data.get("components", []):
        if comp.get("name") == component_name:
            file_path = comp.get(file_key)
            if file_path:
                path = Path(file_path)
                if path.exists():
                    return path.read_text()
    return None
