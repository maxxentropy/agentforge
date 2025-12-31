"""
AgentForge - Autonomous AI agent framework with verified execution.

AgentForge removes the human bottleneck from software development by creating
a trust infrastructure where verified processes replace manual review.

Usage:
    agentforge init           # Initialize a project
    agentforge design "goal"  # Design specifications
    agentforge implement      # Full implementation pipeline
    agentforge status         # Check task status
"""

__version__ = "0.1.0"
__author__ = "AgentForge Team"

# Re-export key components for convenience
from agentforge.core.init import initialize_project

__all__ = [
    "__version__",
    "initialize_project",
]
