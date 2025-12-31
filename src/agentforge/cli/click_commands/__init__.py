"""
Click command definitions.

This package contains the Click command groups, organized by feature area.
"""

from agentforge.cli.click_commands.spec import intake, clarify, analyze, draft, validate_spec, revise
from agentforge.cli.click_commands.utility import context, verify, render_spec
from agentforge.cli.click_commands.workspace import workspace
from agentforge.cli.click_commands.config import config
from agentforge.cli.click_commands.contracts import contracts, exemptions
from agentforge.cli.click_commands.conformance import conformance
from agentforge.cli.click_commands.tdflow import tdflow
from agentforge.cli.click_commands.ci import ci

__all__ = [
    # Spec workflow
    'intake', 'clarify', 'analyze', 'draft', 'validate_spec', 'revise',
    # Utilities
    'context', 'verify', 'render_spec',
    # Groups
    'workspace', 'config', 'contracts', 'exemptions', 'conformance', 'tdflow', 'ci',
]
