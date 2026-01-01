# @spec_file: .agentforge/specs/refactoring-v1.yaml
# @spec_id: refactoring-v1
# @component_id: tools-refactoring-base
# @test_path: tests/unit/tools/test_contracts_execution_naming.py

"""
Refactoring Provider Base
=========================

Abstract base class for language-specific refactoring providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass
class RefactoringResult:
    """Result of a refactoring operation."""
    success: bool
    new_content: Optional[str] = None
    error: Optional[str] = None
    changes_description: str = ""

    # Details about what was created
    new_function_name: Optional[str] = None
    new_function_location: Optional[Tuple[int, int]] = None  # (start_line, end_line)
    call_replacement: Optional[str] = None

    @classmethod
    def failure(cls, error: str) -> "RefactoringResult":
        return cls(success=False, error=error)

    @classmethod
    def success_result(
        cls,
        new_content: str,
        description: str,
        new_function_name: Optional[str] = None,
    ) -> "RefactoringResult":
        return cls(
            success=True,
            new_content=new_content,
            changes_description=description,
            new_function_name=new_function_name,
        )


@dataclass
class CanExtractResult:
    """Result of checking if extraction is safe."""
    can_extract: bool
    reason: str
    # If extraction is possible, these describe what would happen
    suggested_name: Optional[str] = None
    parameters_needed: List[str] = field(default_factory=list)
    has_early_return: bool = False
    complexity_reduction: Optional[int] = None


class RefactoringProvider(ABC):
    """
    Abstract base for language-specific refactoring.

    Each language should have a provider that uses proper tooling:
    - Python: rope library
    - C#: Roslyn via LSP codeAction
    - TypeScript: tsserver via LSP codeAction

    The key contract: refactoring operations must preserve semantics.
    If a refactoring would break the code, it should fail, not produce broken code.
    """

    # File extensions this provider handles
    FILE_EXTENSIONS: List[str] = []

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)

    @abstractmethod
    def can_extract_function(
        self,
        file_path: Path,
        start_line: int,
        end_line: int,
    ) -> CanExtractResult:
        """
        Check if a code range can be safely extracted into a function.

        This MUST detect:
        - Early returns that would change control flow
        - Variables that would need complex handling
        - Syntax issues (partial blocks, etc.)

        Args:
            file_path: Path to the file
            start_line: Start line (1-indexed)
            end_line: End line (1-indexed, inclusive)

        Returns:
            CanExtractResult with can_extract=True/False and reason
        """
        pass

    @abstractmethod
    def extract_function(
        self,
        file_path: Path,
        start_line: int,
        end_line: int,
        new_function_name: str,
    ) -> RefactoringResult:
        """
        Extract code range into a new function.

        This MUST:
        - Preserve semantics (early returns, exceptions, etc.)
        - Handle parameters correctly
        - Handle return values correctly
        - Produce syntactically valid code

        If the extraction cannot be done safely, return a failure result.

        Args:
            file_path: Path to the file
            start_line: Start line (1-indexed)
            end_line: End line (1-indexed, inclusive)
            new_function_name: Name for the new function

        Returns:
            RefactoringResult with success/failure and new content
        """
        pass

    def supports_file(self, file_path: Path) -> bool:
        """Check if this provider supports the given file type."""
        return file_path.suffix in self.FILE_EXTENSIONS
