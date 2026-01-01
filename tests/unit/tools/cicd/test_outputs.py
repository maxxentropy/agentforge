# @spec_file: .agentforge/specs/cicd-outputs-v1.yaml
# @spec_id: cicd-outputs-v1
# @component_id: cicd-outputs-junit
# @impl_path: tools/cicd/outputs/junit.py

"""Unit tests for CI/CD output generators."""

import json
import pytest
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path

from tools.cicd.domain import (
    CIMode,
    ExitCode,
    CIViolation,
    CIResult,
    BaselineComparison,
    BaselineEntry,
)
from tools.cicd.outputs.sarif import generate_sarif, write_sarif, generate_sarif_for_github
from tools.cicd.outputs.junit import generate_junit, write_junit, generate_junit_string
from tools.cicd.outputs.markdown import generate_markdown, write_markdown, generate_pr_comment


@pytest.fixture
def sample_violations():
    """Create sample violations for testing."""
    return [
        CIViolation(
            check_id="naming-check",
            file_path="src/main.py",
            line=10,
            message="Variable name does not match pattern",
            severity="error",
            rule_id="PY001",
            contract_id="python-standards",
            fix_hint="Use snake_case",
        ),
        CIViolation(
            check_id="doc-check",
            file_path="src/utils.py",
            line=25,
            message="Missing docstring",
            severity="warning",
            contract_id="python-standards",
        ),
    ]


@pytest.fixture
def sample_result(sample_violations):
    """Create sample CI result for testing."""
    now = datetime.utcnow()
    return CIResult(
        mode=CIMode.FULL,
        exit_code=ExitCode.VIOLATIONS_FOUND,
        violations=sample_violations,
        comparison=None,
        files_checked=10,
        checks_run=5,
        duration_seconds=1.5,
        started_at=now - timedelta(seconds=2),
        completed_at=now,
        commit_sha="abc123",
    )


@pytest.fixture
def sample_comparison(sample_violations):
    """Create sample baseline comparison for testing."""
    return BaselineComparison(
        new_violations=[sample_violations[0]],
        fixed_violations=[
            BaselineEntry(
                hash="xyz789",
                check_id="old-check",
                file_path="old_file.py",
                line=5,
                message_preview="Fixed issue",
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow(),
            )
        ],
        existing_violations=[sample_violations[1]],
    )


class TestSarifOutput:
    """Tests for SARIF output generation."""

    def test_generate_sarif_structure(self, sample_result):
        """Test SARIF output has correct structure."""
        sarif = generate_sarif(sample_result)

        assert sarif["$schema"].endswith("sarif-schema-2.1.0.json")
        assert sarif["version"] == "2.1.0"
        assert "runs" in sarif
        assert len(sarif["runs"]) == 1

    def test_generate_sarif_tool_info(self, sample_result):
        """Test SARIF includes tool information."""
        sarif = generate_sarif(sample_result, tool_name="test-tool")

        tool = sarif["runs"][0]["tool"]["driver"]
        assert tool["name"] == "test-tool"
        assert "version" in tool
        assert "rules" in tool

    def test_generate_sarif_results(self, sample_result):
        """Test SARIF results match violations."""
        sarif = generate_sarif(sample_result)

        results = sarif["runs"][0]["results"]
        assert len(results) == 2

        # Check first result
        assert results[0]["ruleId"] == "PY001"
        assert results[0]["level"] == "error"
        assert "Variable name" in results[0]["message"]["text"]

    def test_generate_sarif_invocations(self, sample_result):
        """Test SARIF includes invocation info."""
        sarif = generate_sarif(sample_result)

        invocations = sarif["runs"][0]["invocations"]
        assert len(invocations) == 1
        assert invocations[0]["executionSuccessful"] is False  # Has violations

    def test_generate_sarif_rules(self, sample_result):
        """Test SARIF includes rule definitions."""
        sarif = generate_sarif(sample_result)

        rules = sarif["runs"][0]["tool"]["driver"]["rules"]
        assert len(rules) == 2

        rule_ids = [r["id"] for r in rules]
        assert "PY001" in rule_ids
        assert "doc-check" in rule_ids  # Falls back to check_id when no rule_id

    def test_generate_sarif_for_github(self, sample_result):
        """Test GitHub-specific SARIF generation."""
        sarif = generate_sarif_for_github(
            sample_result,
            repository="owner/repo",
            ref="refs/heads/main",
            commit_sha="abc123",
        )

        vcs = sarif["runs"][0]["versionControlProvenance"][0]
        assert vcs["repositoryUri"] == "https://github.com/owner/repo"
        assert vcs["revisionId"] == "abc123"
        assert vcs["branch"] == "main"

    def test_write_sarif(self, sample_result, tmp_path):
        """Test writing SARIF to file."""
        output_path = tmp_path / ".agentforge" / "results.sarif"

        write_sarif(sample_result, output_path)

        assert output_path.exists()
        content = json.loads(output_path.read_text())
        assert "runs" in content


class TestJunitOutput:
    """Tests for JUnit XML output generation."""

    def test_generate_junit_structure(self, sample_result):
        """Test JUnit XML has correct structure."""
        root = generate_junit(sample_result)

        assert root.tag == "testsuites"
        assert root.get("tests") == "2"
        assert root.get("failures") == "2"

    def test_generate_junit_testsuite_grouping(self, sample_result):
        """Test testsuites are grouped by contract."""
        root = generate_junit(sample_result)

        testsuites = root.findall("testsuite")
        # Grouped by contract_id
        assert len(testsuites) == 1  # Both violations have same contract_id

    def test_generate_junit_testcases(self, sample_result):
        """Test testcases have correct content."""
        root = generate_junit(sample_result)

        testcases = root.findall(".//testcase")
        assert len(testcases) == 2

        for testcase in testcases:
            assert "name" in testcase.attrib
            assert "classname" in testcase.attrib
            failure = testcase.find("failure")
            assert failure is not None
            assert "message" in failure.attrib

    def test_generate_junit_failure_details(self, sample_result):
        """Test failure elements contain details."""
        root = generate_junit(sample_result)

        failure = root.find(".//failure")
        assert failure is not None
        assert "File:" in failure.text
        assert "Line:" in failure.text
        assert "Severity:" in failure.text

    def test_write_junit(self, sample_result, tmp_path):
        """Test writing JUnit XML to file."""
        output_path = tmp_path / "results.xml"

        write_junit(sample_result, output_path)

        assert output_path.exists()
        tree = ET.parse(output_path)
        root = tree.getroot()
        assert root.tag == "testsuites"

    def test_generate_junit_string(self, sample_result):
        """Test generating JUnit as string."""
        xml_string = generate_junit_string(sample_result)

        assert xml_string.startswith("<testsuites")
        assert "testcase" in xml_string
        assert "failure" in xml_string


class TestMarkdownOutput:
    """Tests for Markdown output generation."""

    def test_generate_markdown_structure(self, sample_result):
        """Test Markdown has expected sections."""
        md = generate_markdown(sample_result)

        assert "## ❌ AgentForge Conformance Report" in md  # Failed
        assert "### Summary" in md
        assert "### All Violations" in md

    def test_generate_markdown_summary_table(self, sample_result):
        """Test summary table contains key metrics."""
        md = generate_markdown(sample_result)

        assert "Mode | full" in md
        assert "Files Checked | 10" in md
        assert "Total Violations | 2" in md
        assert "Errors | 1" in md
        assert "Warnings | 1" in md

    def test_generate_markdown_success_status(self, sample_violations):
        """Test success status shows checkmark."""
        now = datetime.utcnow()
        result = CIResult(
            mode=CIMode.FULL,
            exit_code=ExitCode.SUCCESS,
            violations=[],
            comparison=None,
            files_checked=10,
            checks_run=5,
            duration_seconds=1.0,
            started_at=now,
            completed_at=now,
        )

        md = generate_markdown(result)

        assert "## ✅" in md

    def test_generate_markdown_with_comparison(self, sample_result, sample_comparison):
        """Test Markdown includes baseline comparison."""
        sample_result.comparison = sample_comparison

        md = generate_markdown(sample_result)

        assert "### Baseline Comparison" in md
        assert "New Violations" in md
        assert "Fixed Violations" in md
        assert "Existing Violations" in md

    def test_generate_markdown_violations_by_file(self, sample_result):
        """Test violations are grouped by file."""
        md = generate_markdown(sample_result)

        assert "**`src/main.py`**" in md
        assert "**`src/utils.py`**" in md

    def test_generate_markdown_severity_icons(self, sample_result):
        """Test severity icons are included."""
        md = generate_markdown(sample_result)

        assert "🔴" in md  # Error
        assert "🟡" in md  # Warning

    def test_generate_markdown_footer(self, sample_result):
        """Test footer includes metadata."""
        md = generate_markdown(sample_result)

        assert "Generated at" in md
        assert "abc123" in md  # Commit SHA

    def test_write_markdown(self, sample_result, tmp_path):
        """Test writing Markdown to file."""
        output_path = tmp_path / "results.md"

        write_markdown(sample_result, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "## " in content

    def test_generate_pr_comment_success(self):
        """Test PR comment format for success."""
        now = datetime.utcnow()
        result = CIResult(
            mode=CIMode.PR,
            exit_code=ExitCode.SUCCESS,
            violations=[],
            comparison=None,
            files_checked=5,
            checks_run=3,
            duration_seconds=0.5,
            started_at=now,
            completed_at=now,
        )

        comment = generate_pr_comment(result)

        assert "✅ AgentForge Conformance: Passed" in comment
        assert "0** violations" in comment

    def test_generate_pr_comment_with_new_violations(self, sample_violations, sample_comparison):
        """Test PR comment highlights new violations."""
        now = datetime.utcnow()
        result = CIResult(
            mode=CIMode.PR,
            exit_code=ExitCode.VIOLATIONS_FOUND,
            violations=sample_violations,
            comparison=sample_comparison,
            files_checked=5,
            checks_run=3,
            duration_seconds=0.5,
            started_at=now,
            completed_at=now,
        )

        comment = generate_pr_comment(result)

        assert "❌ AgentForge Conformance: Failed" in comment
        assert "1 new violation(s) introduced" in comment

    def test_generate_pr_comment_with_fixes(self, sample_violations, sample_comparison):
        """Test PR comment celebrates fixes."""
        now = datetime.utcnow()
        result = CIResult(
            mode=CIMode.PR,
            exit_code=ExitCode.SUCCESS,
            violations=sample_violations,
            comparison=sample_comparison,
            files_checked=5,
            checks_run=3,
            duration_seconds=0.5,
            started_at=now,
            completed_at=now,
        )

        comment = generate_pr_comment(result)

        assert "1 violation(s) fixed!" in comment
