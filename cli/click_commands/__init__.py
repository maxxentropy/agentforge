"""
Click command definitions.

This package contains the Click command groups, organized by feature area.
"""

from cli.click_commands.spec import intake, clarify, analyze, draft, validate_spec, revise
from cli.click_commands.utility import context, verify, render_spec
from cli.click_commands.workspace import workspace
from cli.click_commands.config import config
from cli.click_commands.contracts import contracts, exemptions
from cli.click_commands.conformance import conformance

__all__ = [
    # Spec workflow
    'intake', 'clarify', 'analyze', 'draft', 'validate_spec', 'revise',
    # Utilities
    'context', 'verify', 'render_spec',
    # Groups
    'workspace', 'config', 'contracts', 'exemptions', 'conformance',
]
