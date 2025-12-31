"""
JUnit XML Output Generator
==========================

Generates JUnit XML output for Azure DevOps and other CI systems
that consume test results in JUnit format.
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from tools.cicd.domain import CIResult, CIViolation


def generate_junit(result: CIResult, suite_name: str = "AgentForge Conformance") -> ET.Element:
    """
    Generate JUnit XML from CI result.

    Each violation becomes a failed test case.
    Passing checks are not represented (JUnit is failure-focused).

    Args:
        result: CI check result
        suite_name: Name for the test suite

    Returns:
        ElementTree root element
    """
    # Group violations by contract/check for test suites
    by_check: Dict[str, List[CIViolation]] = {}
    for violation in result.violations:
        key = violation.contract_id or violation.check_id
        if key not in by_check:
            by_check[key] = []
        by_check[key].append(violation)

    # Create root element
    testsuites = ET.Element("testsuites")
    testsuites.set("name", suite_name)
    testsuites.set("tests", str(len(result.violations)))
    testsuites.set("failures", str(result.error_count + result.warning_count))
    testsuites.set("errors", "0")
    testsuites.set("time", str(round(result.duration_seconds, 3)))
    testsuites.set("timestamp", result.started_at.isoformat())

    # Create testsuite for each check
    for check_name, violations in by_check.items():
        testsuite = ET.SubElement(testsuites, "testsuite")
        testsuite.set("name", check_name)
        testsuite.set("tests", str(len(violations)))
        testsuite.set("failures", str(len(violations)))
        testsuite.set("errors", "0")
        testsuite.set("time", "0")

        for violation in violations:
            testcase = ET.SubElement(testsuite, "testcase")
            testcase.set("name", _format_testcase_name(violation))
            testcase.set("classname", check_name)
            testcase.set("time", "0")

            failure = ET.SubElement(testcase, "failure")
            failure.set("message", violation.message[:200])  # Truncate long messages
            failure.set("type", violation.severity)
            failure.text = _format_failure_text(violation)

    return testsuites


def _format_testcase_name(violation: CIViolation) -> str:
    """Format testcase name from violation."""
    location = violation.file_path
    if violation.line:
        location += f":{violation.line}"
    return f"{violation.check_id}@{location}"


def _format_failure_text(violation: CIViolation) -> str:
    """Format detailed failure text."""
    lines = [
        f"File: {violation.file_path}",
        f"Line: {violation.line or 'N/A'}",
        f"Severity: {violation.severity}",
        "",
        violation.message,
    ]

    if violation.fix_hint:
        lines.extend(["", "Fix: " + violation.fix_hint])

    if violation.code_snippet:
        lines.extend(["", "Code:", violation.code_snippet])

    return "\n".join(lines)


def write_junit(result: CIResult, output_path: Path, suite_name: str = "AgentForge Conformance") -> None:
    """
    Write JUnit XML to file.

    Args:
        result: CI check result
        output_path: Path to write XML file
        suite_name: Name for the test suite
    """
    root = generate_junit(result, suite_name)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")

    with open(output_path, "wb") as f:
        tree.write(f, encoding="utf-8", xml_declaration=True)


def generate_junit_string(result: CIResult, suite_name: str = "AgentForge Conformance") -> str:
    """
    Generate JUnit XML as string.

    Args:
        result: CI check result
        suite_name: Name for the test suite

    Returns:
        JUnit XML as string
    """
    root = generate_junit(result, suite_name)
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode", method="xml")
