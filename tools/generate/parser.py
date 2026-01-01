# @spec_file: .agentforge/specs/generate-v1.yaml
# @spec_id: generate-v1
# @component_id: tools-generate-parser
# @test_path: tests/unit/tools/generate/test_parser.py

"""
Response Parser
===============

Extracts code files from LLM responses.
Handles markdown code blocks with file path markers.
"""

import ast
import re
from pathlib import Path
from typing import List, Optional, Tuple

from tools.generate.domain import GeneratedFile, FileAction, ParseError


class ResponseParser:
    """
    Parses LLM responses to extract generated code files.

    Expects code blocks in the format:
    ```python:path/to/file.py
    # code here
    ```

    Also supports language-only blocks that are associated with
    a file path mentioned in the surrounding text.
    """

    # Pattern for code blocks with explicit file paths
    # Matches: ```python:path/to/file.py or ```py:path/to/file.py
    FILE_PATTERN = re.compile(
        r"```(?:python|py):([^\n]+)\n(.*?)```",
        re.DOTALL
    )

    # Pattern for generic python code blocks (fallback)
    CODE_PATTERN = re.compile(
        r"```(?:python|py)\n(.*?)```",
        re.DOTALL
    )

    # Pattern to find file path mentions in text
    # Matches: "file: path.py", "output to: path.py", "create path.py", "write to `path.py`"
    PATH_MENTION_PATTERN = re.compile(
        r"(?:file|output|create|write|to)[:\s]+[`'\"]?([a-zA-Z0-9_/.-]+\.py)[`'\"]?",
        re.IGNORECASE
    )

    def __init__(self, validate_syntax: bool = True):
        """
        Initialize parser.

        Args:
            validate_syntax: Whether to validate Python syntax with ast.parse()
        """
        self.validate_syntax = validate_syntax

    def parse(self, response: str) -> List[GeneratedFile]:
        """
        Parse LLM response and extract code files.

        Args:
            response: Raw LLM response text

        Returns:
            List of GeneratedFile objects

        Raises:
            ParseError: If no valid code files found
        """
        files = []

        # First, try to extract files with explicit paths
        for match in self.FILE_PATTERN.finditer(response):
            file_path = match.group(1).strip()
            content = match.group(2)

            # Clean up the content
            content = self._clean_content(content)

            # Validate syntax if enabled
            if self.validate_syntax:
                self._validate_python_syntax(content, file_path)

            files.append(GeneratedFile(
                path=Path(file_path),
                content=content,
                action=FileAction.CREATE,
            ))

        # If no explicit paths found, try to infer from context
        if not files:
            files = self._parse_implicit_paths(response)

        if not files:
            raise ParseError(
                "No code files found in response",
                raw_response=response[:500] if len(response) > 500 else response,
            )

        return files

    def _parse_implicit_paths(self, response: str) -> List[GeneratedFile]:
        """
        Try to extract code blocks and infer paths from context.

        Looks for path mentions before code blocks.
        """
        files = []

        # Find all code blocks
        code_matches = list(self.CODE_PATTERN.finditer(response))

        for code_match in code_matches:
            content = self._clean_content(code_match.group(1))

            # Look for path mention before this code block
            text_before = response[:code_match.start()]
            path_matches = list(self.PATH_MENTION_PATTERN.finditer(text_before))

            if path_matches:
                # Use the last mentioned path
                file_path = path_matches[-1].group(1)

                if self.validate_syntax:
                    self._validate_python_syntax(content, file_path)

                files.append(GeneratedFile(
                    path=Path(file_path),
                    content=content,
                    action=FileAction.CREATE,
                ))

        return files

    def _clean_content(self, content: str) -> str:
        """
        Clean up extracted code content.

        - Removes trailing whitespace
        - Ensures proper line endings
        - Removes common leading indentation
        """
        # Strip trailing whitespace from each line
        lines = content.rstrip().split('\n')

        # Remove completely empty lines at start and end
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()

        if not lines:
            return ""

        # Don't dedent - preserve original indentation
        return '\n'.join(lines) + '\n'

    def _validate_python_syntax(self, content: str, file_path: str) -> None:
        """
        Validate Python syntax using ast.parse().

        Args:
            content: Python code to validate
            file_path: Path for error messages

        Raises:
            ParseError: If syntax is invalid
        """
        try:
            ast.parse(content)
        except SyntaxError as e:
            raise ParseError(
                f"Invalid Python syntax in {file_path}: {e.msg}",
                raw_response=content[:200],
                position=e.lineno,
            )

    def extract_explanation(self, response: str) -> str:
        """
        Extract non-code explanation text from response.

        Removes code blocks and returns remaining text.

        Args:
            response: Raw LLM response

        Returns:
            Explanation text without code blocks
        """
        # Remove all code blocks
        text = self.FILE_PATTERN.sub('', response)
        text = self.CODE_PATTERN.sub('', text)

        # Clean up multiple blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()

    def parse_with_explanation(
        self,
        response: str
    ) -> Tuple[List[GeneratedFile], str]:
        """
        Parse response and extract both files and explanation.

        Args:
            response: Raw LLM response

        Returns:
            Tuple of (files, explanation)

        Raises:
            ParseError: If no valid code files found
        """
        files = self.parse(response)
        explanation = self.extract_explanation(response)
        return files, explanation


class MultiLanguageParser(ResponseParser):
    """
    Extended parser that handles multiple languages.

    Supports Python, TypeScript, C#, and other common languages.
    """

    # Pattern for any language with file path
    MULTI_LANG_PATTERN = re.compile(
        r"```(\w+):([^\n]+)\n(.*?)```",
        re.DOTALL
    )

    # Language to file extension mapping
    LANG_EXTENSIONS = {
        "python": ".py",
        "py": ".py",
        "typescript": ".ts",
        "ts": ".ts",
        "javascript": ".js",
        "js": ".js",
        "csharp": ".cs",
        "cs": ".cs",
        "java": ".java",
        "go": ".go",
        "rust": ".rs",
        "yaml": ".yaml",
        "yml": ".yaml",
        "json": ".json",
    }

    def parse(self, response: str) -> List[GeneratedFile]:
        """
        Parse response for multiple languages.

        Still validates Python syntax for .py files.
        """
        files = []

        for match in self.MULTI_LANG_PATTERN.finditer(response):
            language = match.group(1).lower()
            file_path = match.group(2).strip()
            content = self._clean_content(match.group(3))

            # Validate Python syntax for Python files
            if language in ("python", "py") and self.validate_syntax:
                self._validate_python_syntax(content, file_path)

            files.append(GeneratedFile(
                path=Path(file_path),
                content=content,
                action=FileAction.CREATE,
            ))

        # Fall back to parent implementation if no matches
        if not files:
            return super().parse(response)

        return files


def parse_response(
    response: str,
    validate_syntax: bool = True,
) -> List[GeneratedFile]:
    """
    Convenience function to parse LLM response.

    Args:
        response: Raw LLM response text
        validate_syntax: Whether to validate Python syntax

    Returns:
        List of GeneratedFile objects

    Raises:
        ParseError: If no valid code files found
    """
    parser = ResponseParser(validate_syntax=validate_syntax)
    return parser.parse(response)
