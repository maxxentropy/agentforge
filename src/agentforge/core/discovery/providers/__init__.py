"""
Language Providers for Brownfield Discovery
============================================

Provides language-specific analysis capabilities.
"""

from .base import Dependency, Import, LanguageProvider, Symbol
from .dotnet_provider import DotNetProvider
from .python_provider import PythonProvider

__all__ = [
    "LanguageProvider", "Symbol", "Import", "Dependency",
    "PythonProvider", "DotNetProvider",
]


def _get_lsp_adapter():
    """Get LSP adapter for .NET projects (used by DotNetProvider)."""
    try:
        import os

        from agentforge.core.lsp_adapters import get_adapter_for_project
        return get_adapter_for_project(os.getcwd())
    except Exception:
        return None
