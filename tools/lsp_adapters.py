#!/usr/bin/env python3
"""
Language-Specific LSP Adapters
==============================

Concrete LSP adapter implementations for different languages.

Extracted from lsp_adapter.py for modularity.
"""

import os
from typing import Optional, List
from pathlib import Path

from .lsp_adapter import LSPAdapter


class CSharpLSPAdapter(LSPAdapter):
    """
    Adapter for csharp-ls.

    Lightweight C# language server.

    Installation: dotnet tool install -g csharp-ls
    """

    SERVER_COMMAND = ["csharp-ls"]
    SERVER_NAME = "csharp-ls"
    INSTALL_INSTRUCTIONS = "dotnet tool install -g csharp-ls"
    LANGUAGE_ID = "csharp"
    FILE_EXTENSIONS = [".cs", ".csx"]

    def _get_initialization_options(self) -> dict:
        """csharp-ls specific options."""
        return {}

    def find_solution_or_project(self) -> Optional[str]:
        """Find .sln or .csproj file in project root."""
        sln_files = list(self.project_path.glob("*.sln"))
        if sln_files:
            return str(sln_files[0])
        csproj_files = list(self.project_path.glob("**/*.csproj"))
        if csproj_files:
            return str(csproj_files[0])
        return None


class OmniSharpAdapter(LSPAdapter):
    """
    Adapter for OmniSharp (C#/.NET).

    Full-featured C# language server with Roslyn.

    Installation: Download from https://github.com/OmniSharp/omnisharp-roslyn/releases
    """

    OMNISHARP_PATH = os.path.expanduser("~/.local/share/omnisharp/OmniSharp")
    SERVER_NAME = "omnisharp"
    INSTALL_INSTRUCTIONS = "Download from https://github.com/OmniSharp/omnisharp-roslyn/releases"
    LANGUAGE_ID = "csharp"
    FILE_EXTENSIONS = [".cs", ".csx"]

    @property
    def SERVER_COMMAND(self) -> List[str]:
        """OmniSharp command with LSP mode enabled."""
        solution = self.find_solution_or_project()
        cmd = [self.OMNISHARP_PATH, "-lsp"]
        if solution:
            cmd.extend(["-s", solution])
        return cmd

    def _get_initialization_options(self) -> dict:
        """OmniSharp-specific options."""
        return {
            "RoslynExtensionsOptions": {
                "EnableAnalyzersSupport": False,
                "EnableImportCompletion": True,
            },
            "FormattingOptions": {
                "EnableEditorConfigSupport": True,
            },
        }

    def find_solution_or_project(self) -> Optional[str]:
        """Find .sln or .csproj file in project root."""
        sln_files = list(self.project_path.glob("*.sln"))
        if sln_files:
            return str(sln_files[0])
        csproj_files = list(self.project_path.glob("**/*.csproj"))
        if csproj_files:
            return str(csproj_files[0])
        return None

    @classmethod
    def is_available(cls) -> bool:
        """Check if OmniSharp is installed."""
        return os.path.isfile(cls.OMNISHARP_PATH) and os.access(cls.OMNISHARP_PATH, os.X_OK)


class PyrightAdapter(LSPAdapter):
    """
    Adapter for pyright (Python).

    Installation: pip install pyright
    """

    SERVER_COMMAND = ["pyright-langserver", "--stdio"]
    SERVER_NAME = "pyright"
    INSTALL_INSTRUCTIONS = "pip install pyright"
    LANGUAGE_ID = "python"
    FILE_EXTENSIONS = [".py", ".pyi"]


class TypeScriptAdapter(LSPAdapter):
    """
    Adapter for typescript-language-server.

    Installation: npm install -g typescript-language-server typescript
    """

    SERVER_COMMAND = ["typescript-language-server", "--stdio"]
    SERVER_NAME = "typescript-language-server"
    INSTALL_INSTRUCTIONS = "npm install -g typescript-language-server typescript"
    LANGUAGE_ID = "typescript"
    FILE_EXTENSIONS = [".ts", ".tsx", ".js", ".jsx"]


# =============================================================================
# Factory Functions
# =============================================================================

def _is_dotnet_project(project: Path) -> bool:
    """Check if project contains .NET files."""
    return bool(list(project.glob("*.sln")) or list(project.glob("**/*.csproj")))


def _is_python_project(project: Path) -> bool:
    """Check if project contains Python files."""
    return ((project / "pyproject.toml").exists() or
            (project / "setup.py").exists() or
            bool(list(project.glob("**/*.py"))))


def _is_typescript_project(project: Path) -> bool:
    """Check if project contains TypeScript/JavaScript files."""
    return (project / "package.json").exists() or (project / "tsconfig.json").exists()


def _get_csharp_adapter(project_path: str, prefer_omnisharp: bool) -> LSPAdapter:
    """Get appropriate C# adapter based on preference."""
    if prefer_omnisharp and OmniSharpAdapter.is_available():
        return OmniSharpAdapter(project_path)
    return CSharpLSPAdapter(project_path)


def get_adapter_for_project(project_path: str, prefer_omnisharp: bool = True) -> LSPAdapter:
    """
    Get the appropriate LSP adapter for a project.

    Detects the primary language from project files.

    Args:
        project_path: Root directory of the project
        prefer_omnisharp: For C# projects, prefer OmniSharp over csharp-ls

    Returns:
        Appropriate LSPAdapter subclass instance
    """
    project = Path(project_path)

    if _is_dotnet_project(project):
        return _get_csharp_adapter(project_path, prefer_omnisharp)

    if _is_python_project(project):
        return PyrightAdapter(project_path)

    if _is_typescript_project(project):
        return TypeScriptAdapter(project_path)

    # Default to C# (primary target)
    return _get_csharp_adapter(project_path, prefer_omnisharp)
