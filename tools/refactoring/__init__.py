"""
Refactoring Providers
=====================

Language-aware refactoring using proper tooling:
- Python: rope library (battle-tested, understands control flow)
- C#: LSP codeAction via OmniSharp/Roslyn
- TypeScript: LSP codeAction via tsserver

This replaces the hand-rolled AST manipulation with real refactoring tools.
"""

from .base import RefactoringProvider, RefactoringResult, CanExtractResult
from .rope_provider import RopeRefactoringProvider
from .registry import get_refactoring_provider

__all__ = [
    "RefactoringProvider",
    "RefactoringResult",
    "CanExtractResult",
    "RopeRefactoringProvider",
    "get_refactoring_provider",
]
