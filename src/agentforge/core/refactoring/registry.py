"""
Refactoring Provider Registry
=============================

Returns the appropriate refactoring provider for a given file type.
"""

from pathlib import Path
from typing import Optional

from .base import RefactoringProvider
from .rope_provider import RopeRefactoringProvider


# Registry of providers by file extension
_EXTENSION_TO_PROVIDER = {
    ".py": RopeRefactoringProvider,
    ".pyi": RopeRefactoringProvider,
    # Future: add LSP-based providers for other languages
    # ".cs": LSPRefactoringProvider,
    # ".ts": LSPRefactoringProvider,
}


def get_refactoring_provider(
    file_path: Path,
    project_path: Path,
) -> Optional[RefactoringProvider]:
    """
    Get the appropriate refactoring provider for a file.

    Args:
        file_path: Path to the file to refactor
        project_path: Root path of the project

    Returns:
        RefactoringProvider instance or None if no provider supports this file type
    """
    suffix = Path(file_path).suffix.lower()
    provider_class = _EXTENSION_TO_PROVIDER.get(suffix)

    if provider_class is None:
        return None

    return provider_class(project_path)


def supports_file(file_path: Path) -> bool:
    """Check if any provider supports this file type."""
    suffix = Path(file_path).suffix.lower()
    return suffix in _EXTENSION_TO_PROVIDER
