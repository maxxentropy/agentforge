"""
CI/CD Platform Integrations
===========================

Platform-specific integrations for:
- GitHub Actions (PR comments, Code Scanning)
- Azure DevOps (PR comments, build results)
"""

from tools.cicd.platforms.github import GITHUB_WORKFLOW_TEMPLATE, generate_github_pr_comment_body
from tools.cicd.platforms.azure import AZURE_PIPELINE_TEMPLATE, generate_azure_pr_comment_body

__all__ = [
    "GITHUB_WORKFLOW_TEMPLATE",
    "generate_github_pr_comment_body",
    "AZURE_PIPELINE_TEMPLATE",
    "generate_azure_pr_comment_body",
]
