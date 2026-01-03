"""
CI/CD Output Generators
=======================

Output format generators for CI/CD integration:
- SARIF: GitHub Code Scanning integration
- JUnit: Azure DevOps test results
- Markdown: PR comment summaries
"""

from agentforge.core.cicd.outputs.sarif import generate_sarif, write_sarif, generate_sarif_for_github
from agentforge.core.cicd.outputs.junit import generate_junit, write_junit, generate_junit_string
from agentforge.core.cicd.outputs.markdown import generate_markdown, write_markdown, generate_pr_comment

__all__ = [
    "generate_sarif",
    "write_sarif",
    "generate_sarif_for_github",
    "generate_junit",
    "write_junit",
    "generate_junit_string",
    "generate_markdown",
    "write_markdown",
    "generate_pr_comment",
]
