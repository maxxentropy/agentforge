"""
Language Providers for Brownfield Discovery
============================================

Provides language-specific analysis capabilities.
"""

from .base import LanguageProvider, Symbol, Import, Dependency
from .python_provider import PythonProvider
from .dotnet_provider import DotNetProvider

__all__ = [
    "LanguageProvider", "Symbol", "Import", "Dependency",
    "PythonProvider", "DotNetProvider",
]


def _get_lsp_adapter():
    """Get LSP adapter for .NET projects (used by DotNetProvider)."""
    try:
        from agentforge.core.lsp_adapters import get_adapter_for_project
        import os
        return get_adapter_for_project(os.getcwd())
    except Exception:
        return None
