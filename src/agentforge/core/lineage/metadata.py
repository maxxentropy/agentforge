"""
Lineage Metadata
================

Data structures and utilities for embedding and extracting lineage
information from generated source files.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class LineageMetadata:
    """
    Metadata embedded in generated files for audit trail.

    This is the core data structure that connects:
    - Specs (requirements) → Tests → Implementation → Violations

    Every generated file should have this metadata in its header,
    making the entire chain auditable and traceable.
    """

    # When and how this file was generated
    generated_at: datetime
    generator: str  # e.g., "tdflow.red.v1", "tdflow.green.v1"

    # Spec traceability
    spec_file: str  # Path to spec file (relative to project root)
    spec_id: str  # Unique spec identifier
    component_id: str  # Component within spec

    # Method-level traceability (optional, for partial generation)
    method_ids: list[str] = field(default_factory=list)

    # Cross-file linkage
    test_path: str | None = None  # Path to test file (for impl files)
    impl_path: str | None = None  # Path to impl file (for test files)

    # Additional context
    session_id: str | None = None  # TDFLOW session that generated this

    def to_header_comments(self, comment_prefix: str = "#") -> str:
        """
        Generate header comment block for embedding in source files.

        Args:
            comment_prefix: Comment character(s) for the language (# for Python, // for JS)

        Returns:
            Formatted comment block ready to insert at file top
        """
        p = comment_prefix
        lines = [
            f"{p} {'═' * 77}",
            f"{p} LINEAGE METADATA - DO NOT EDIT THIS BLOCK",
            f"{p} {'═' * 77}",
            f"{p} @generated: {self.generated_at.isoformat()}",
            f"{p} @generator: {self.generator}",
            f"{p} @spec_file: {self.spec_file}",
            f"{p} @spec_id: {self.spec_id}",
            f"{p} @component_id: {self.component_id}",
        ]

        if self.method_ids:
            lines.append(f"{p} @method_ids: {','.join(self.method_ids)}")

        if self.test_path:
            lines.append(f"{p} @test_path: {self.test_path}")

        if self.impl_path:
            lines.append(f"{p} @impl_path: {self.impl_path}")

        if self.session_id:
            lines.append(f"{p} @session_id: {self.session_id}")

        lines.append(f"{p} {'═' * 77}")

        return "\n".join(lines)


# Regex patterns for parsing lineage metadata from file headers
_LINEAGE_PATTERNS = {
    "generated_at": re.compile(r"@generated:\s*(.+)"),
    "generator": re.compile(r"@generator:\s*(.+)"),
    "spec_file": re.compile(r"@spec_file:\s*(.+)"),
    "spec_id": re.compile(r"@spec_id:\s*(.+)"),
    "component_id": re.compile(r"@component_id:\s*(.+)"),
    "method_ids": re.compile(r"@method_ids:\s*(.+)"),
    "test_path": re.compile(r"@test_path:\s*(.+)"),
    "impl_path": re.compile(r"@impl_path:\s*(.+)"),
    "session_id": re.compile(r"@session_id:\s*(.+)"),
}


def parse_lineage_from_file(file_path: Path) -> LineageMetadata | None:
    """
    Extract lineage metadata from a source file's header comments.

    Reads the first 30 lines of the file looking for @-prefixed metadata
    within a lineage block (marked by ═══ borders).

    Args:
        file_path: Path to the source file

    Returns:
        LineageMetadata if found, None if no lineage block present
    """
    if not file_path.exists():
        return None

    try:
        content = file_path.read_text()
    except Exception:
        return None

    # Only scan first 50 lines for performance
    lines = content.split("\n")[:50]
    header_text = "\n".join(lines)

    # Check if this file has lineage metadata
    if "@spec_id:" not in header_text:
        return None

    # Extract values
    values = {}
    for key, pattern in _LINEAGE_PATTERNS.items():
        match = pattern.search(header_text)
        if match:
            values[key] = match.group(1).strip()

    # Validate required fields
    required = ["generated_at", "generator", "spec_file", "spec_id", "component_id"]
    if not all(key in values for key in required):
        return None

    # Parse datetime
    try:
        generated_at = datetime.fromisoformat(values["generated_at"])
    except ValueError:
        generated_at = datetime.utcnow()

    # Parse method_ids list
    method_ids = []
    if "method_ids" in values:
        method_ids = [m.strip() for m in values["method_ids"].split(",")]

    return LineageMetadata(
        generated_at=generated_at,
        generator=values["generator"],
        spec_file=values["spec_file"],
        spec_id=values["spec_id"],
        component_id=values["component_id"],
        method_ids=method_ids,
        test_path=values.get("test_path"),
        impl_path=values.get("impl_path"),
        session_id=values.get("session_id"),
    )


def generate_lineage_header(
    generator: str,
    spec_file: str,
    spec_id: str,
    component_id: str,
    method_ids: list[str] | None = None,
    test_path: str | None = None,
    impl_path: str | None = None,
    session_id: str | None = None,
    comment_prefix: str = "#",
) -> str:
    """
    Convenience function to generate a lineage header block.

    Args:
        generator: Name of the generator (e.g., "tdflow.red.v1")
        spec_file: Path to the spec file
        spec_id: Unique spec identifier
        component_id: Component ID within the spec
        method_ids: Optional list of method IDs covered
        test_path: Path to associated test file
        impl_path: Path to associated implementation file
        session_id: Optional TDFLOW session ID
        comment_prefix: Comment character for the language

    Returns:
        Formatted header comment block
    """
    metadata = LineageMetadata(
        generated_at=datetime.utcnow(),
        generator=generator,
        spec_file=spec_file,
        spec_id=spec_id,
        component_id=component_id,
        method_ids=method_ids or [],
        test_path=test_path,
        impl_path=impl_path,
        session_id=session_id,
    )
    return metadata.to_header_comments(comment_prefix)


def get_test_path_from_lineage(file_path: Path) -> str | None:
    """
    Get the test path for a file from its lineage metadata.

    This is the primary interface for the violation/fix system.
    Instead of computing test paths from conventions, we read
    the explicit linkage from the file itself.

    Args:
        file_path: Path to the source file

    Returns:
        Test path if found in lineage, None otherwise
    """
    metadata = parse_lineage_from_file(file_path)
    if metadata:
        return metadata.test_path
    return None
