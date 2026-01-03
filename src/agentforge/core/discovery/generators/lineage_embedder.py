# @spec_file: .agentforge/specs/core-discovery-generators-v1.yaml
# @spec_id: core-discovery-generators-v1
# @component_id: discovery-generators-lineage-embedder

"""
Lineage Metadata Embedder
=========================

Embeds lineage metadata into source files, enabling the Artifact Parity Principle.
After embedding, brownfield code has the same traceability as greenfield code.

Lineage Format (Python files):
```
# @spec_file: .agentforge/specs/core-v1.yaml
# @spec_id: core-v1
# @component_id: context-models
# @test_path: tests/unit/core/test_context_models.py
```

The orchestration engine uses this metadata to:
1. Find the correct spec for context
2. Identify which tests to run
3. Build the violation → fix → verify chain
"""

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class LineageMetadata:
    """Lineage metadata to embed in a file."""
    spec_file: str
    spec_id: str
    component_id: str
    test_path: str | None = None  # For implementation files
    impl_path: str | None = None  # For test files


@dataclass
class EmbedResult:
    """Result of embedding lineage metadata in a file."""
    file_path: str
    success: bool
    action: str  # "added", "updated", "skipped", "error"
    message: str = ""


class LineageEmbedder:
    """
    Embeds lineage metadata into source file headers.

    Supports:
    - Python files (.py): Uses # comments
    - TypeScript/JavaScript (.ts, .js): Uses // comments
    - C# files (.cs): Uses // comments

    The embedder is idempotent - running it multiple times produces
    the same result. Existing lineage blocks are updated in place.
    """

    # Patterns for detecting existing lineage blocks
    LINEAGE_START = "@spec_file:"
    LINEAGE_END_PATTERN = re.compile(r"^#?\s*@(test_path|impl_path):")

    # Comment prefixes by file extension
    COMMENT_PREFIXES = {
        ".py": "#",
        ".ts": "//",
        ".tsx": "//",
        ".js": "//",
        ".jsx": "//",
        ".cs": "//",
        ".go": "//",
        ".rs": "//",
        ".java": "//",
    }

    def __init__(self, root_path: Path, dry_run: bool = False):
        """
        Initialize the embedder.

        Args:
            root_path: Project root for resolving paths
            dry_run: If True, don't actually modify files
        """
        self.root_path = root_path
        self.dry_run = dry_run
        self._results: list[EmbedResult] = []

    def embed_all(
        self,
        lineage_updates: dict[str, dict[str, str]],
    ) -> list[EmbedResult]:
        """
        Embed lineage metadata into all specified files.

        Args:
            lineage_updates: Dict mapping file_path -> lineage metadata dict
                             (output from AsBuiltSpecGenerator.generate_lineage_updates)

        Returns:
            List of EmbedResult for each file processed
        """
        self._results = []

        for file_path, metadata_dict in lineage_updates.items():
            metadata = LineageMetadata(
                spec_file=metadata_dict.get("spec_file", ""),
                spec_id=metadata_dict.get("spec_id", ""),
                component_id=metadata_dict.get("component_id", ""),
                test_path=metadata_dict.get("test_path"),
                impl_path=metadata_dict.get("impl_path"),
            )

            result = self.embed_file(file_path, metadata)
            self._results.append(result)

        return self._results

    def embed_file(self, file_path: str, metadata: LineageMetadata) -> EmbedResult:
        """
        Embed lineage metadata into a single file.

        Args:
            file_path: Path to the file (relative to root_path)
            metadata: Lineage metadata to embed

        Returns:
            EmbedResult describing what happened
        """
        full_path = self.root_path / file_path

        if not full_path.exists():
            return EmbedResult(
                file_path=file_path,
                success=False,
                action="error",
                message=f"File not found: {full_path}",
            )

        suffix = full_path.suffix.lower()
        if suffix not in self.COMMENT_PREFIXES:
            return EmbedResult(
                file_path=file_path,
                success=False,
                action="skipped",
                message=f"Unsupported file type: {suffix}",
            )

        comment_prefix = self.COMMENT_PREFIXES[suffix]

        try:
            content = full_path.read_text()
        except Exception as e:
            return EmbedResult(
                file_path=file_path,
                success=False,
                action="error",
                message=f"Failed to read file: {e}",
            )

        # Build the lineage block
        lineage_block = self._build_lineage_block(metadata, comment_prefix)

        # Check for existing lineage block
        has_existing, start_line, end_line = self._find_existing_lineage(content, comment_prefix)

        if has_existing:
            # Update existing block
            new_content = self._replace_lineage_block(
                content, lineage_block, start_line, end_line
            )
            action = "updated"
        else:
            # Insert new block
            new_content = self._insert_lineage_block(content, lineage_block, comment_prefix)
            action = "added"

        if new_content == content:
            return EmbedResult(
                file_path=file_path,
                success=True,
                action="skipped",
                message="No changes needed",
            )

        if not self.dry_run:
            try:
                full_path.write_text(new_content)
            except Exception as e:
                return EmbedResult(
                    file_path=file_path,
                    success=False,
                    action="error",
                    message=f"Failed to write file: {e}",
                )

        return EmbedResult(
            file_path=file_path,
            success=True,
            action=action,
            message=f"Lineage metadata {action}",
        )

    def _build_lineage_block(
        self,
        metadata: LineageMetadata,
        comment_prefix: str,
    ) -> str:
        """Build the lineage metadata block."""
        lines = [
            f"{comment_prefix} @spec_file: {metadata.spec_file}",
            f"{comment_prefix} @spec_id: {metadata.spec_id}",
            f"{comment_prefix} @component_id: {metadata.component_id}",
        ]

        if metadata.test_path:
            lines.append(f"{comment_prefix} @test_path: {metadata.test_path}")

        if metadata.impl_path:
            lines.append(f"{comment_prefix} @impl_path: {metadata.impl_path}")

        return "\n".join(lines)

    def _find_existing_lineage(
        self,
        content: str,
        comment_prefix: str,
    ) -> tuple[bool, int, int]:
        """
        Find an existing lineage block in the content.

        Returns:
            (has_existing, start_line, end_line) - line numbers are 0-indexed
        """
        lines = content.split("\n")
        start_line = -1
        end_line = -1

        pattern = re.compile(
            rf"^{re.escape(comment_prefix)}\s*@spec_file:",
            re.IGNORECASE,
        )

        for i, line in enumerate(lines):
            if pattern.match(line):
                start_line = i
                # Find the end of the lineage block
                for j in range(i, min(i + 10, len(lines))):
                    if self._is_lineage_end(lines[j], comment_prefix):
                        end_line = j
                    elif not self._is_lineage_line(lines[j], comment_prefix):
                        break
                if end_line == -1:
                    end_line = start_line
                break

        return (start_line >= 0, start_line, end_line)

    def _is_lineage_line(self, line: str, comment_prefix: str) -> bool:
        """Check if a line is part of a lineage block."""
        stripped = line.strip()
        if not stripped.startswith(comment_prefix):
            return False

        # Remove comment prefix and check for @ tags
        after_prefix = stripped[len(comment_prefix):].strip()
        return after_prefix.startswith("@")

    def _is_lineage_end(self, line: str, comment_prefix: str) -> bool:
        """Check if a line is the last line of a lineage block."""
        stripped = line.strip()
        if not stripped.startswith(comment_prefix):
            return False

        after_prefix = stripped[len(comment_prefix):].strip()
        return after_prefix.startswith("@test_path:") or after_prefix.startswith("@impl_path:")

    def _replace_lineage_block(
        self,
        content: str,
        new_block: str,
        start_line: int,
        end_line: int,
    ) -> str:
        """Replace an existing lineage block with a new one."""
        lines = content.split("\n")

        # Replace the block
        new_lines = (
            lines[:start_line] +
            new_block.split("\n") +
            lines[end_line + 1:]
        )

        return "\n".join(new_lines)

    def _is_standard_header_comment(self, stripped: str) -> bool:
        """Check if line is a standard header comment (copyright, license, author)."""
        return any(s in stripped.lower() for s in ["copyright", "license", "author"])

    def _should_skip_python_line(self, i: int, stripped: str) -> tuple[bool, bool]:
        """Check if Python line should be skipped when finding insert position.

        Returns:
            (should_skip, should_break) - skip means continue, break means stop
        """
        # Check skip conditions
        if self._is_skippable_header_line(i, stripped):
            return True, False

        # Check break conditions
        if self._is_break_point_line(stripped):
            return False, True

        return True, False

    def _is_skippable_header_line(self, i: int, stripped: str) -> bool:
        """Check if line is a skippable header line (shebang, encoding, empty)."""
        # Skip shebang
        if i == 0 and stripped.startswith("#!"):
            return True
        # Skip encoding declaration
        if i <= 1 and (stripped.startswith("# -*-") or "coding" in stripped):
            return True
        # Skip empty lines at start
        if not stripped:
            return True
        # Standard header comments are skippable
        if stripped.startswith("#") and self._is_standard_header_comment(stripped):
            return True
        return False

    def _is_break_point_line(self, stripped: str) -> bool:
        """Check if line is a break point (docstring, code, non-header comment)."""
        # Stop at module docstring
        if stripped.startswith('"""') or stripped.startswith("'''"):
            return True
        # Stop at first non-comment line
        if not stripped.startswith("#"):
            return True
        # Non-standard-header comments are break points
        return not self._is_standard_header_comment(stripped)

    def _find_python_insert_position(self, lines: list[str]) -> int:
        """Find the correct insert position for Python files."""
        insert_position = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            should_skip, should_break = self._should_skip_python_line(i, stripped)
            if should_break:
                break
            if should_skip:
                insert_position = i + 1
        return insert_position

    def _add_spacing(self, lineage_block: str, lines: list[str], position: int) -> str:
        """Add spacing around lineage block as needed."""
        if position > 0 and lines[position - 1].strip():
            lineage_block = "\n" + lineage_block
        if position < len(lines) and lines[position].strip():
            lineage_block = lineage_block + "\n"
        return lineage_block

    def _insert_lineage_block(
        self,
        content: str,
        lineage_block: str,
        comment_prefix: str,
    ) -> str:
        """Insert lineage block at the appropriate location."""
        lines = content.split("\n")

        # For Python files, find the right position after headers
        insert_position = 0
        if comment_prefix == "#":
            insert_position = self._find_python_insert_position(lines)

        # Add spacing and insert
        lineage_block = self._add_spacing(lineage_block, lines, insert_position)
        new_lines = lines[:insert_position] + [lineage_block] + lines[insert_position:]
        return "\n".join(new_lines)

    @property
    def results(self) -> list[EmbedResult]:
        """Get the results from the last embed_all call."""
        return self._results

    def summary(self) -> dict[str, int]:
        """Get a summary of the embedding results."""
        summary = {
            "added": 0,
            "updated": 0,
            "skipped": 0,
            "error": 0,
            "total": len(self._results),
        }

        for result in self._results:
            if result.action in summary:
                summary[result.action] += 1

        return summary
