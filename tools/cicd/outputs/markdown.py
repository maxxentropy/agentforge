# @spec_file: .agentforge/specs/cicd-outputs-v1.yaml
# @spec_id: cicd-outputs-v1
# @component_id: cicd-outputs-markdown
# @test_path: tests/unit/tools/cicd/test_outputs.py

"""
Markdown Output Generator
=========================

Generates Markdown summaries for PR comments and reports.
Designed for clear, actionable feedback in pull request discussions.
"""

from pathlib import Path
from typing import Dict, List, Optional

from tools.cicd.domain import CIResult, CIViolation, BaselineComparison, BaselineEntry


def generate_markdown(result: CIResult, title: str = "AgentForge Conformance Report") -> str:
    """
    Generate Markdown summary from CI result.

    Output structure:
    1. Summary table (pass/fail counts)
    2. New violations (if PR mode) - expanded
    3. Fixed violations (if PR mode) - one-liner celebration
    4. All violations (grouped by file) - collapsible for long lists

    Args:
        result: CI check result
        title: Report title

    Returns:
        Markdown formatted string
    """
    sections = []

    # Header with status badge
    status_emoji = "✅" if result.is_success else "❌"
    sections.append(f"## {status_emoji} {title}\n")

    # Summary table
    sections.append(_generate_summary_table(result))

    # Baseline comparison section (for PR mode)
    if result.comparison:
        sections.append(_generate_comparison_section(result.comparison))

    # Violations by file
    if result.violations:
        sections.append(_generate_violations_section(result.violations))

    # Footer with metadata
    sections.append(_generate_footer(result))

    return "\n".join(sections)


def _generate_summary_table(result: CIResult) -> str:
    """Generate summary statistics table."""
    lines = [
        "### Summary\n",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Mode | {result.mode.value} |",
        f"| Files Checked | {result.files_checked} |",
        f"| Checks Run | {result.checks_run} |",
        f"| Total Violations | {result.total_violations} |",
        f"| Errors | {result.error_count} |",
        f"| Warnings | {result.warning_count} |",
        f"| Duration | {result.duration_seconds:.2f}s |",
        "",
    ]
    return "\n".join(lines)


def _generate_comparison_section(comparison: BaselineComparison) -> str:
    """Generate baseline comparison section for PR mode."""
    lines = ["### Baseline Comparison\n"]

    # Net change indicator
    if comparison.net_change < 0:
        lines.append(f"📉 **Net improvement:** {abs(comparison.net_change)} fewer violations\n")
    elif comparison.net_change > 0:
        lines.append(f"📈 **Net regression:** {comparison.net_change} more violations\n")
    else:
        lines.append("➡️ **No net change** in violation count\n")

    # New violations (expanded, this is the most important section)
    if comparison.new_violations:
        lines.append(f"#### ⚠️ New Violations ({len(comparison.new_violations)})\n")
        lines.append("These violations were introduced in this PR and should be fixed:\n")

        for violation in comparison.new_violations:
            lines.append(_format_violation_item(violation))

        lines.append("")

    # Fixed violations (celebrate!)
    if comparison.fixed_violations:
        lines.append(f"#### 🎉 Fixed Violations ({len(comparison.fixed_violations)})\n")
        lines.append("These violations were fixed in this PR:\n")

        for entry in comparison.fixed_violations[:5]:  # Limit to first 5
            lines.append(f"- ~~`{entry.check_id}` in `{entry.file_path}`~~")

        if len(comparison.fixed_violations) > 5:
            lines.append(f"- *...and {len(comparison.fixed_violations) - 5} more*")

        lines.append("")

    # Existing violations (collapsed)
    if comparison.existing_violations:
        lines.append(
            f"<details>\n"
            f"<summary>📋 Existing Violations ({len(comparison.existing_violations)}) - "
            f"pre-existing tech debt</summary>\n"
        )

        for violation in comparison.existing_violations[:20]:
            lines.append(_format_violation_item(violation, compact=True))

        if len(comparison.existing_violations) > 20:
            lines.append(f"\n*...and {len(comparison.existing_violations) - 20} more*")

        lines.append("\n</details>\n")

    return "\n".join(lines)


def _generate_violations_section(violations: List[CIViolation]) -> str:
    """Generate violations grouped by file."""
    if not violations:
        return ""

    lines = ["### All Violations\n"]

    # Group by file
    by_file: Dict[str, List[CIViolation]] = {}
    for v in violations:
        if v.file_path not in by_file:
            by_file[v.file_path] = []
        by_file[v.file_path].append(v)

    # Collapse if many files
    if len(by_file) > 3:
        lines.append("<details>")
        lines.append(f"<summary>View all {len(violations)} violations in {len(by_file)} files</summary>\n")

    for file_path, file_violations in sorted(by_file.items()):
        lines.append(f"**`{file_path}`** ({len(file_violations)} violations)\n")

        for v in file_violations:
            lines.append(_format_violation_item(v))

        lines.append("")

    if len(by_file) > 3:
        lines.append("</details>\n")

    return "\n".join(lines)


def _format_violation_item(violation: CIViolation, compact: bool = False) -> str:
    """Format a single violation as a list item."""
    severity_icons = {
        "error": "🔴",
        "warning": "🟡",
        "info": "🔵",
    }
    icon = severity_icons.get(violation.severity, "⚪")

    location = f"L{violation.line}" if violation.line else "file"

    if compact:
        return f"- {icon} `{violation.check_id}` at `{violation.file_path}:{location}`"

    lines = [f"- {icon} **{violation.check_id}** at `{location}`"]
    lines.append(f"  - {violation.message}")

    if violation.fix_hint:
        lines.append(f"  - 💡 *{violation.fix_hint}*")

    return "\n".join(lines)


def _generate_footer(result: CIResult) -> str:
    """Generate footer with metadata."""
    lines = [
        "---",
        f"*Generated at {result.completed_at.strftime('%Y-%m-%d %H:%M:%S')} UTC*",
    ]

    if result.commit_sha:
        lines.append(f"*Commit: `{result.commit_sha[:8]}`*")

    if result.errors:
        lines.append("\n⚠️ **Runtime Errors:**")
        for error in result.errors:
            lines.append(f"- {error}")

    return "\n".join(lines)


def write_markdown(
    result: CIResult,
    output_path: Path,
    title: str = "AgentForge Conformance Report"
) -> None:
    """
    Write Markdown to file.

    Args:
        result: CI check result
        output_path: Path to write Markdown file
        title: Report title
    """
    content = generate_markdown(result, title)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)


def generate_pr_comment(result: CIResult) -> str:
    """
    Generate a concise PR comment format.

    Optimized for GitHub/Azure PR comment character limits
    and readability in PR discussions.

    Args:
        result: CI check result

    Returns:
        Markdown string suitable for PR comment
    """
    lines = []

    # Status header
    if result.is_success:
        lines.append("## ✅ AgentForge Conformance: Passed\n")
    else:
        lines.append("## ❌ AgentForge Conformance: Failed\n")

    # Quick stats
    lines.append(f"**{result.total_violations}** violations | ")
    lines.append(f"**{result.error_count}** errors | ")
    lines.append(f"**{result.warning_count}** warnings | ")
    lines.append(f"**{result.duration_seconds:.1f}s** runtime\n")

    # Baseline comparison for PR mode
    if result.comparison:
        if result.comparison.introduces_violations:
            lines.append(f"\n🚨 **{len(result.comparison.new_violations)} new violation(s) introduced**\n")

            for v in result.comparison.new_violations[:5]:
                lines.append(f"- `{v.check_id}` in `{v.file_path}`: {v.message[:80]}...")

            if len(result.comparison.new_violations) > 5:
                lines.append(f"- *...and {len(result.comparison.new_violations) - 5} more*")

        if result.comparison.has_improvements:
            lines.append(f"\n🎉 **{len(result.comparison.fixed_violations)} violation(s) fixed!**")

    lines.append("\n---")
    lines.append("*AgentForge Conformance Check*")

    return "\n".join(lines)
