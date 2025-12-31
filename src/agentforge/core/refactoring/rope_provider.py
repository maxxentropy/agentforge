"""
Rope Refactoring Provider
=========================

Python refactoring using the rope library.

Rope is the standard Python refactoring library, used by many IDEs.
It properly handles:
- Control flow (early returns, break, continue)
- Variable scope and parameter detection
- Return value handling
- Exception handling

This is a world-class solution, not hand-rolled AST manipulation.
"""

import ast
from pathlib import Path
from typing import Optional

from rope.base.project import Project
from rope.base import libutils
from rope.refactor.extract import ExtractMethod

from .base import RefactoringProvider, RefactoringResult, CanExtractResult


class RopeRefactoringProvider(RefactoringProvider):
    """
    Python refactoring using rope.

    Rope's ExtractMethod handles all the complexity:
    - Detects which variables need to be parameters
    - Detects which variables are defined and returned
    - Handles early returns by raising ExtractMethodError
    - Validates the extraction is semantically valid
    """

    FILE_EXTENSIONS = [".py", ".pyi"]

    def __init__(self, project_path: Path):
        super().__init__(project_path)
        self._project: Optional[Project] = None

    def _get_project(self) -> Project:
        """Get or create rope project."""
        if self._project is None:
            # Create rope project with sane defaults
            self._project = Project(
                str(self.project_path),
                ropefolder=None,  # Don't create .ropeproject folder
            )
        return self._project

    def _get_resource(self, file_path: Path):
        """Get rope resource for a file."""
        project = self._get_project()
        # Make path relative to project if absolute
        if file_path.is_absolute():
            try:
                rel_path = file_path.relative_to(self.project_path)
            except ValueError:
                # File is outside project, use absolute path
                rel_path = file_path
        else:
            rel_path = file_path
        return project.get_resource(str(rel_path))

    def _lines_to_offset(self, content: str, line: int) -> int:
        """Convert 1-indexed line number to character offset."""
        lines = content.split('\n')
        offset = 0
        for i in range(min(line - 1, len(lines))):
            offset += len(lines[i]) + 1  # +1 for newline
        return offset

    def _get_line_range_offsets(
        self, content: str, start_line: int, end_line: int
    ) -> tuple[int, int]:
        """Get character offsets for a line range."""
        lines = content.split('\n')
        start_offset = self._lines_to_offset(content, start_line)

        # End offset is the end of end_line
        end_offset = self._lines_to_offset(content, end_line)
        if end_line <= len(lines):
            end_offset += len(lines[end_line - 1])

        return start_offset, end_offset

    def can_extract_function(
        self,
        file_path: Path,
        start_line: int,
        end_line: int,
    ) -> CanExtractResult:
        """
        Check if extraction is safe using rope's analysis.

        Rope will tell us if the extraction is valid by attempting the refactoring.
        If it fails, we get a descriptive error explaining why.
        """
        try:
            resource = self._get_resource(file_path)
            content = resource.read()

            start_offset, end_offset = self._get_line_range_offsets(
                content, start_line, end_line
            )

            # Try to create the extractor and get changes
            # Rope validates the extraction during get_changes()
            extractor = ExtractMethod(
                self._get_project(),
                resource,
                start_offset,
                end_offset,
            )

            # This will raise RefactoringError if extraction is invalid
            # We use a dummy name just to test - we won't apply the changes
            extractor.get_changes("_test_can_extract")

            return CanExtractResult(
                can_extract=True,
                reason="Extraction is valid - rope validated the selection",
                has_early_return=False,
            )

        except Exception as e:
            # Rope raises exceptions for invalid extractions
            error_msg = str(e)

            # Detect common issues and provide helpful messages
            has_return = "return" in error_msg.lower()
            if has_return:
                return CanExtractResult(
                    can_extract=False,
                    reason=f"Cannot extract: {error_msg}. Try extracting the code INSIDE the if block, or the entire if/else as a whole.",
                    has_early_return=True,
                )
            elif "break" in error_msg.lower() or "continue" in error_msg.lower():
                return CanExtractResult(
                    can_extract=False,
                    reason=f"Cannot extract: {error_msg}. Break/continue must stay within their loop.",
                )
            elif "bad region" in error_msg.lower():
                return CanExtractResult(
                    can_extract=False,
                    reason=f"Cannot extract: Invalid selection. Ensure you're selecting complete statements.",
                )
            else:
                return CanExtractResult(
                    can_extract=False,
                    reason=f"Cannot extract: {error_msg}",
                )

    def extract_function(
        self,
        file_path: Path,
        start_line: int,
        end_line: int,
        new_function_name: str,
    ) -> RefactoringResult:
        """
        Extract code into a new function using rope.

        Rope handles all the complexity correctly:
        - Parameters are automatically detected
        - Return values are handled
        - Early returns cause the extraction to fail (not silently break code)
        """
        try:
            resource = self._get_resource(file_path)
            content = resource.read()

            start_offset, end_offset = self._get_line_range_offsets(
                content, start_line, end_line
            )

            # Create the extractor
            extractor = ExtractMethod(
                self._get_project(),
                resource,
                start_offset,
                end_offset,
            )

            # Get changes (this validates the extraction)
            changes = extractor.get_changes(new_function_name)

            # Rope's changes.do() would modify the file directly
            # Instead, we want to get the new content without modifying the file
            # We can use rope's change preview mechanism
            from rope.base.change import ChangeContents

            # Get the new content from the change set
            new_content = None
            for change in changes.changes:
                if isinstance(change, ChangeContents):
                    if change.resource.path == resource.path:
                        new_content = change.new_contents
                        break

            if new_content is None:
                # Fallback: calculate new content from the description
                # This shouldn't happen for ExtractMethod, but just in case
                return RefactoringResult.failure(
                    "Could not determine new file content from rope changes"
                )

            # Validate the result
            try:
                ast.parse(new_content)
            except SyntaxError as e:
                return RefactoringResult.failure(
                    f"Rope produced invalid Python (bug in rope?): {e}"
                )

            return RefactoringResult.success_result(
                new_content=new_content,
                description=f"Extracted '{new_function_name}' from lines {start_line}-{end_line}",
                new_function_name=new_function_name,
            )

        except Exception as e:
            error_msg = str(e)

            # Provide helpful error messages
            if "return" in error_msg.lower():
                return RefactoringResult.failure(
                    f"Cannot extract: code contains early returns that would change control flow. "
                    f"Try extracting a complete if/else block, or the code inside the if body. "
                    f"Details: {error_msg}"
                )
            elif "break" in error_msg.lower() or "continue" in error_msg.lower():
                return RefactoringResult.failure(
                    f"Cannot extract: code contains break/continue that would break loop control. "
                    f"Details: {error_msg}"
                )
            elif "bad region" in error_msg.lower():
                return RefactoringResult.failure(
                    f"Cannot extract: Invalid selection. Ensure you're selecting complete statements. "
                    f"Details: {error_msg}"
                )
            elif "start of a block" in error_msg.lower():
                return RefactoringResult.failure(
                    f"Cannot extract: Selection includes the start of a block (if/for/while) "
                    f"without including the entire block. Include all statements in the block. "
                    f"Details: {error_msg}"
                )
            else:
                return RefactoringResult.failure(
                    f"Extraction failed: {error_msg}"
                )

    def close(self):
        """Clean up rope project."""
        if self._project is not None:
            self._project.close()
            self._project = None
