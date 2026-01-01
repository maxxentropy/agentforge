# @spec_file: .agentforge/specs/cicd-outputs-v1.yaml
# @spec_id: cicd-outputs-v1
# @component_id: cicd-outputs-sarif
# @test_path: tests/unit/tools/cicd/test_outputs.py

"""
SARIF Output Generator
======================

Generates SARIF (Static Analysis Results Interchange Format) output
for GitHub Code Scanning integration.

SARIF specification: https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from tools.cicd.domain import CIResult, CIViolation


SARIF_VERSION = "2.1.0"
SARIF_SCHEMA = "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json"


def generate_sarif(result: CIResult, tool_name: str = "agentforge") -> Dict[str, Any]:
    """
    Generate SARIF 2.1.0 compliant output from CI result.

    Args:
        result: CI check result
        tool_name: Name of the analysis tool

    Returns:
        SARIF document as dictionary
    """
    # Collect unique rules from violations
    rules = _collect_rules(result.violations)

    # Build SARIF results
    sarif_results = [v.to_sarif_result() for v in result.violations]

    sarif_doc = {
        "$schema": SARIF_SCHEMA,
        "version": SARIF_VERSION,
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": tool_name,
                        "version": "1.0.0",
                        "informationUri": "https://github.com/agentforge/agentforge",
                        "rules": rules,
                    }
                },
                "results": sarif_results,
                "invocations": [
                    {
                        "executionSuccessful": result.exit_code.value == 0,
                        "startTimeUtc": result.started_at.isoformat() + "Z",
                        "endTimeUtc": result.completed_at.isoformat() + "Z",
                    }
                ],
            }
        ],
    }

    # Add version control info if available
    if result.commit_sha:
        sarif_doc["runs"][0]["versionControlProvenance"] = [
            {
                "repositoryUri": "",  # Would need to be passed in
                "revisionId": result.commit_sha,
            }
        ]

    return sarif_doc


def _collect_rules(violations: List[CIViolation]) -> List[Dict[str, Any]]:
    """
    Collect unique rule definitions from violations.

    Each unique check_id becomes a rule in the SARIF output.
    """
    seen_rules: Dict[str, Dict[str, Any]] = {}

    for violation in violations:
        rule_id = violation.rule_id or violation.check_id
        if rule_id not in seen_rules:
            seen_rules[rule_id] = {
                "id": rule_id,
                "name": rule_id,
                "shortDescription": {
                    "text": f"Check: {violation.check_id}"
                },
                "defaultConfiguration": {
                    "level": _map_severity_to_level(violation.severity)
                },
            }

            # Add help text if fix_hint available
            if violation.fix_hint:
                seen_rules[rule_id]["help"] = {
                    "text": violation.fix_hint
                }

    return list(seen_rules.values())


def _map_severity_to_level(severity: str) -> str:
    """Map AgentForge severity to SARIF level."""
    mapping = {
        "error": "error",
        "warning": "warning",
        "info": "note",
    }
    return mapping.get(severity, "warning")


def write_sarif(result: CIResult, output_path: Path, tool_name: str = "agentforge") -> None:
    """
    Write SARIF output to file.

    Args:
        result: CI check result
        output_path: Path to write SARIF file
        tool_name: Name of the analysis tool
    """
    sarif_doc = generate_sarif(result, tool_name)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(sarif_doc, f, indent=2)


def generate_sarif_for_github(
    result: CIResult,
    repository: str,
    ref: str,
    commit_sha: str,
    tool_name: str = "agentforge"
) -> Dict[str, Any]:
    """
    Generate SARIF with GitHub-specific metadata.

    Args:
        result: CI check result
        repository: GitHub repository (owner/repo)
        ref: Git ref (e.g., refs/heads/main)
        commit_sha: Commit SHA being analyzed
        tool_name: Name of the analysis tool

    Returns:
        SARIF document with GitHub metadata
    """
    sarif_doc = generate_sarif(result, tool_name)

    # Add GitHub-specific version control provenance
    sarif_doc["runs"][0]["versionControlProvenance"] = [
        {
            "repositoryUri": f"https://github.com/{repository}",
            "revisionId": commit_sha,
            "branch": ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else ref,
        }
    ]

    return sarif_doc
