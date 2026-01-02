"""
Click command definitions.

This package contains the Click command groups, organized by feature area.
"""

from agentforge.cli.click_commands.ci import ci
from agentforge.cli.click_commands.config import config
from agentforge.cli.click_commands.conformance import conformance
from agentforge.cli.click_commands.contracts import contracts, exemptions
from agentforge.cli.click_commands.spec import (
    adapt,
    analyze,
    clarify,
    draft,
    intake,
    revise,
    validate_spec,
)
from agentforge.cli.click_commands.tdflow import tdflow
from agentforge.cli.click_commands.utility import context, render_spec, verify
from agentforge.cli.click_commands.workspace import workspace

__all__ = [
    # Spec workflow
    'intake', 'clarify', 'analyze', 'draft', 'validate_spec', 'revise', 'adapt',
    # Utilities
    'context', 'verify', 'render_spec',
    # Groups
    'workspace', 'config', 'contracts', 'exemptions', 'conformance', 'tdflow', 'ci',
]
