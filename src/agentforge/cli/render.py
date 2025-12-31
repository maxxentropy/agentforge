"""
Specification rendering utilities.

Contains functions to render YAML specifications to human-readable Markdown.
"""

import sys
import click
import yaml
from pathlib import Path


def _render_metadata(meta: dict) -> list:
    """Render spec metadata section to markdown lines."""
    lines = []
    lines.append(f"# {meta.get('feature_name', 'Specification')}")
    lines.append("")
    lines.append(f"**Version:** {meta.get('version', '1.0')}")
    lines.append(f"**Status:** {meta.get('status', 'draft')}")
    lines.append(f"**Date:** {meta.get('created_date', 'N/A')}")
    lines.append("")
    lines.append("---")
    lines.append("")
    return lines


def _render_overview(overview: dict) -> list:
    """Render overview section to markdown lines."""
    lines = []
    lines.append("## 1. Overview")
    lines.append("")
    lines.append("### 1.1 Purpose")
    lines.append("")
    lines.append(overview.get('purpose', '').strip())
    lines.append("")

    if overview.get('background'):
        lines.append("### 1.2 Background")
        lines.append("")
        lines.append(overview.get('background', '').strip())
        lines.append("")

    lines.append("### 1.3 Scope")
    lines.append("")
    scope = overview.get('scope', {})
    if scope.get('includes'):
        lines.append("**In Scope:**")
        for item in scope.get('includes', []):
            lines.append(f"- {item}")
        lines.append("")
    if scope.get('excludes'):
        lines.append("**Out of Scope:**")
        for item in scope.get('excludes', []):
            lines.append(f"- {item}")
        lines.append("")

    if overview.get('assumptions'):
        lines.append("### 1.4 Assumptions")
        lines.append("")
        for item in overview.get('assumptions', []):
            lines.append(f"- {item}")
        lines.append("")

    if overview.get('constraints'):
        lines.append("### 1.5 Constraints")
        lines.append("")
        for item in overview.get('constraints', []):
            lines.append(f"- {item}")
        lines.append("")

    lines.append("---")
    lines.append("")
    return lines


def _render_acceptance_criteria(criteria: list) -> list:
    """Render acceptance criteria in Gherkin format."""
    lines = []
    lines.append("*Acceptance Criteria:*")
    lines.append("")
    lines.append("```gherkin")
    for ac in criteria:
        lines.append(f"Scenario: {ac.get('id')}")
        lines.append(f"  Given {ac.get('given')}")
        lines.append(f"  When {ac.get('when')}")
        lines.append(f"  Then {ac.get('then')}")
        if ac.get('and_then'):
            for at in ac.get('and_then', []):
                lines.append(f"  And {at}")
        lines.append("")
    lines.append("```")
    lines.append("")
    return lines


def _render_requirements(reqs: dict) -> list:
    """Render requirements section to markdown lines."""
    lines = []
    lines.append("## 2. Requirements")
    lines.append("")
    lines.append("### 2.1 Functional Requirements")
    lines.append("")

    for req in reqs.get('functional', []):
        lines.append(f"**{req.get('id')}: {req.get('title')}**")
        lines.append("")
        lines.append(f"*Priority:* {req.get('priority', 'must').upper()}")
        lines.append("")
        lines.append(req.get('description', '').strip())
        lines.append("")
        if req.get('rationale'):
            lines.append(f"*Rationale:* {req.get('rationale')}")
            lines.append("")
        if req.get('acceptance_criteria'):
            lines.extend(_render_acceptance_criteria(req.get('acceptance_criteria', [])))

    if reqs.get('non_functional'):
        lines.append("### 2.2 Non-Functional Requirements")
        lines.append("")
        for req in reqs.get('non_functional', []):
            lines.append(f"**{req.get('id')}: {req.get('title')}**")
            lines.append("")
            lines.append(req.get('description', '').strip())
            lines.append("")

    lines.append("---")
    lines.append("")
    return lines


def _render_entity(entity: dict) -> list:
    """Render a single entity to markdown lines."""
    lines = []
    lines.append(f"#### {entity.get('name')}")
    lines.append("")
    lines.append(f"**Layer:** {entity.get('layer')} | **Type:** {entity.get('type')}")
    lines.append("")

    if entity.get('description'):
        lines.append(entity.get('description', '').strip())
        lines.append("")

    if entity.get('properties'):
        lines.append("**Properties:**")
        lines.append("")
        lines.append("| Property | Type | Nullable | Constraints | Description |")
        lines.append("|----------|------|----------|-------------|-------------|")
        for prop in entity.get('properties', []):
            constraints = ', '.join(prop.get('constraints', [])) or '-'
            lines.append(
                f"| {prop.get('name')} | {prop.get('type')} | "
                f"{prop.get('nullable', False)} | {constraints} | "
                f"{prop.get('description', '-')} |"
            )
        lines.append("")

    if entity.get('methods'):
        lines.append("**Methods:**")
        lines.append("")
        for method in entity.get('methods', []):
            params = ', '.join([
                f"{p.get('name')}: {p.get('type')}"
                for p in method.get('parameters', [])
            ])
            lines.append(
                f"- `{method.get('name')}({params}) -> {method.get('returns')}`: "
                f"{method.get('description', '')}"
            )
        lines.append("")

    if entity.get('invariants'):
        lines.append("**Invariants:**")
        lines.append("")
        for inv in entity.get('invariants', []):
            lines.append(f"- {inv}")
        lines.append("")

    return lines


def _render_entities(entities: list) -> list:
    """Render entities section to markdown lines."""
    lines = []
    if entities:
        lines.append("## 3. Data Model")
        lines.append("")
        lines.append("### 3.1 Entities")
        lines.append("")
        for entity in entities:
            lines.extend(_render_entity(entity))
    lines.append("---")
    lines.append("")
    return lines


def _render_interface_response(resp: dict) -> list:
    """Render interface response section."""
    lines = [f"**Success Response:** `{resp.get('success', 'N/A')}`", ""]
    if resp.get('error_codes'):
        lines.append("**Error Codes:**")
        for err in resp.get('error_codes', []):
            lines.append(f"- `{err}`")
        lines.append("")
    return lines


def _render_single_interface(iface: dict) -> list:
    """Render a single interface to markdown lines."""
    lines = [
        f"#### {iface.get('name')}", "",
        f"**Type:** {iface.get('type')} | **Path:** `{iface.get('path')}`", ""
    ]
    if iface.get('request'):
        lines.append(f"**Request Body:** `{iface.get('request', {}).get('body', 'N/A')}`")
        lines.append("")
    if iface.get('response'):
        lines.extend(_render_interface_response(iface.get('response', {})))
    return lines


def _render_interfaces(interfaces: list) -> list:
    """Render interfaces section to markdown lines."""
    lines = []
    if interfaces:
        lines.extend(["## 4. Interfaces", ""])
        for iface in interfaces:
            lines.extend(_render_single_interface(iface))
    lines.extend(["---", ""])
    return lines


def _render_workflow(wf: dict) -> list:
    """Render a single workflow to markdown lines."""
    lines = []
    lines.append(f"### {wf.get('name')}")
    lines.append("")
    if wf.get('description'):
        lines.append(wf.get('description'))
        lines.append("")
    lines.append(f"**Trigger:** {wf.get('trigger')}")
    lines.append("")

    if wf.get('steps'):
        lines.append("**Steps:**")
        lines.append("")
        for step in wf.get('steps', []):
            lines.append(
                f"{step.get('step')}. **{step.get('actor', 'System')}:** "
                f"{step.get('action')}"
            )
            if step.get('alternatives'):
                for alt in step.get('alternatives', []):
                    lines.append(f"   - *Alternative:* {alt}")
        lines.append("")

    lines.append(f"**Success:** {wf.get('success_outcome', 'N/A')}")
    lines.append("")
    return lines


def _render_workflows(workflows: list) -> list:
    """Render workflows section to markdown lines."""
    lines = []
    if workflows:
        lines.append("## 5. Workflows")
        lines.append("")
        for wf in workflows:
            lines.extend(_render_workflow(wf))
    lines.append("---")
    lines.append("")
    return lines


def _render_error_handling(errors: list) -> list:
    """Render error handling section to markdown lines."""
    lines = []
    if errors:
        lines.append("## 6. Error Handling")
        lines.append("")
        lines.append("| Error Code | Condition | Response | User Message |")
        lines.append("|------------|-----------|----------|--------------|")
        for err in errors:
            lines.append(
                f"| {err.get('error_code')} | {err.get('condition')} | "
                f"{err.get('response')} | {err.get('user_message', '-')} |"
            )
        lines.append("")
    lines.append("---")
    lines.append("")
    return lines


def _render_testing_notes(testing: dict) -> list:
    """Render testing notes section to markdown lines."""
    lines = []
    if testing:
        lines.append("## 7. Testing Notes")
        lines.append("")
        if testing.get('unit_test_focus'):
            lines.append("### Unit Test Focus")
            lines.append("")
            for item in testing.get('unit_test_focus', []):
                lines.append(f"- {item}")
            lines.append("")
        if testing.get('integration_test_scenarios'):
            lines.append("### Integration Test Scenarios")
            lines.append("")
            for item in testing.get('integration_test_scenarios', []):
                lines.append(f"- {item}")
            lines.append("")
        if testing.get('edge_cases'):
            lines.append("### Edge Cases")
            lines.append("")
            for item in testing.get('edge_cases', []):
                lines.append(f"- {item}")
            lines.append("")
    lines.append("---")
    lines.append("")
    return lines


def _render_glossary(glossary: list) -> list:
    """Render glossary section to markdown lines."""
    lines = []
    if glossary:
        lines.append("## Glossary")
        lines.append("")
        lines.append("| Term | Definition |")
        lines.append("|------|------------|")
        for item in glossary:
            lines.append(f"| {item.get('term')} | {item.get('definition')} |")
        lines.append("")
    return lines


def render_spec_to_markdown(spec: dict) -> str:
    """
    Render a specification dictionary to markdown string.

    Args:
        spec: Parsed YAML specification dictionary

    Returns:
        Markdown string
    """
    lines = []
    lines.extend(_render_metadata(spec.get('metadata', {})))
    lines.extend(_render_overview(spec.get('overview', {})))
    lines.extend(_render_requirements(spec.get('requirements', {})))
    lines.extend(_render_entities(spec.get('entities', [])))
    lines.extend(_render_interfaces(spec.get('interfaces', [])))
    lines.extend(_render_workflows(spec.get('workflows', [])))
    lines.extend(_render_error_handling(spec.get('error_handling', [])))
    lines.extend(_render_testing_notes(spec.get('testing_notes', {})))
    lines.extend(_render_glossary(spec.get('glossary', [])))
    return '\n'.join(lines)


def run_render_spec(args):
    """Render YAML specification to Markdown for human consumption."""
    click.echo()
    click.echo("=" * 60)
    click.echo("RENDER SPECIFICATION")
    click.echo("=" * 60)

    spec_path = Path(args.spec_file)
    if not spec_path.exists():
        click.echo(f"Error: {spec_path} not found")
        click.echo("Run 'python execute.py draft' first")
        sys.exit(1)

    with open(spec_path) as f:
        spec = yaml.safe_load(f)

    # Build markdown document
    markdown = render_spec_to_markdown(spec)
    lines = markdown.split('\n')

    # Write output
    output_path = Path(args.output)
    with open(output_path, 'w') as f:
        f.write(markdown)

    click.echo(f"\nRendered to: {output_path}")
    click.echo(f"   Source: {spec_path}")
    click.echo(f"   Lines: {len(lines)}")
