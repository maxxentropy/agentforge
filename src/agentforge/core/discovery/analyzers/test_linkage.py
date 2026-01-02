"""
Test Linkage Analyzer
=====================

Analyzes test files to create source-to-test mappings.
This is critical for the fix workflow to know exactly which tests
verify a given source file.

Detection methods (in order of confidence):
1. Import analysis - test file imports source module (highest confidence)
2. Naming convention - test_X.py tests X.py
3. AST analysis - test methods reference source classes/functions
"""

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

from ..domain import TestAnalysis, TestInventory, TestLinkage


@dataclass
class TestLinkageAnalyzer:
    """
    Analyzes test files to build source-to-test mappings.

    The mapping enables the fix workflow to run exactly the right tests
    when verifying code changes, rather than falling back to conventions.
    """

    root_path: Path
    test_directories: list[str] = field(default_factory=lambda: ["tests", "test"])
    source_directories: list[str] = field(default_factory=lambda: ["src", "tools", "lib"])

    def analyze(self) -> TestAnalysis:
        """
        Analyze the codebase and build source-to-test mappings.

        Returns:
            TestAnalysis with linkages populated
        """
        # Find all test files
        test_files = self._find_test_files()

        # Find all source files
        source_files = self._find_source_files()

        # Build mappings using multiple detection methods
        linkages: dict[str, TestLinkage] = {}

        for test_file in test_files:
            # Analyze imports in test file
            imports = self._extract_imports(test_file)

            # Match imports to source files
            for source_file in source_files:
                source_rel = str(source_file.relative_to(self.root_path))
                test_rel = str(test_file.relative_to(self.root_path))

                # Check import-based linkage
                confidence, method = self._check_import_linkage(
                    source_file, test_file, imports
                )

                if confidence > 0:
                    if source_rel not in linkages:
                        linkages[source_rel] = TestLinkage(
                            source_path=source_rel,
                            test_paths=[],
                            confidence=0.0,
                            detection_method="none",
                        )

                    linkage = linkages[source_rel]
                    if test_rel not in linkage.test_paths:
                        linkage.test_paths.append(test_rel)

                    # Update confidence if this method is better
                    if confidence > linkage.confidence:
                        linkage.confidence = confidence
                        linkage.detection_method = method

        # Also check naming conventions for files without import linkage
        for source_file in source_files:
            source_rel = str(source_file.relative_to(self.root_path))
            if source_rel not in linkages:
                test_path, confidence = self._check_naming_convention(source_file)
                if test_path:
                    linkages[source_rel] = TestLinkage(
                        source_path=source_rel,
                        test_paths=[test_path],
                        confidence=confidence,
                        detection_method="naming",
                    )

        # Build inventory
        inventory = TestInventory(
            total_test_files=len(test_files),
            total_test_methods=self._count_test_methods(test_files),
            frameworks=self._detect_frameworks(test_files),
            categories=self._categorize_tests(test_files),
        )

        return TestAnalysis(
            inventory=inventory,
            linkages=list(linkages.values()),
            estimated_coverage=len(linkages) / max(len(source_files), 1),
        )

    def _find_test_files(self) -> list[Path]:
        """Find all test files in the project."""
        test_files = []
        for test_dir in self.test_directories:
            test_path = self.root_path / test_dir
            if test_path.exists():
                for f in test_path.rglob("test_*.py"):
                    test_files.append(f)
                for f in test_path.rglob("*_test.py"):
                    test_files.append(f)
        return test_files

    def _find_source_files(self) -> list[Path]:
        """Find all source files (non-test Python files)."""
        source_files = []
        for source_dir in self.source_directories:
            source_path = self.root_path / source_dir
            if source_path.exists():
                for f in source_path.rglob("*.py"):
                    # Skip test files and __pycache__
                    if "test_" not in f.name and "__pycache__" not in str(f):
                        source_files.append(f)
        return source_files

    def _extract_imports(self, test_file: Path) -> set[str]:
        """Extract all import statements from a test file."""
        imports = set()
        try:
            content = test_file.read_text()
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module)
                    # Also add the full path for each imported name
                    for alias in node.names:
                        imports.add(f"{node.module}.{alias.name}")
        except (SyntaxError, UnicodeDecodeError):
            pass

        return imports

    def _check_import_linkage(
        self, source_file: Path, test_file: Path, imports: set[str]
    ) -> tuple[float, str]:
        """
        Check if test file imports the source module.

        Returns:
            (confidence, detection_method) tuple
        """
        source_rel = source_file.relative_to(self.root_path)

        # Convert file path to module path
        # e.g., tools/harness/llm_executor_domain.py -> tools.harness.llm_executor_domain
        module_path = str(source_rel).replace("/", ".").replace("\\", ".")
        if module_path.endswith(".py"):
            module_path = module_path[:-3]

        # Check various import patterns
        patterns_to_check = [
            module_path,  # Full path
            module_path.replace("src.", ""),  # Without src prefix
            module_path.replace("src.agentforge.", "agentforge."),  # Common pattern
            source_rel.stem,  # Just the module name
        ]

        for pattern in patterns_to_check:
            for imp in imports:
                if pattern in imp or imp in pattern:
                    return (0.9, "import")

        return (0.0, "none")

    def _check_naming_convention(self, source_file: Path) -> tuple[str | None, float]:
        """
        Check if there's a test file matching naming convention.

        Convention: source.py -> test_source.py or source_test.py
        """
        source_name = source_file.stem

        for test_dir in self.test_directories:
            test_base = self.root_path / test_dir

            # Try to match directory structure
            # e.g., tools/harness/X.py -> tests/unit/tools/harness/test_X.py
            source_rel = source_file.relative_to(self.root_path)
            source_parts = source_rel.parts[:-1]  # Directory parts

            # Common patterns
            patterns = [
                test_base / "unit" / Path(*source_parts) / f"test_{source_name}.py",
                test_base / Path(*source_parts) / f"test_{source_name}.py",
                test_base / f"test_{source_name}.py",
                test_base / "unit" / f"test_{source_name}.py",
            ]

            for pattern in patterns:
                if pattern.exists():
                    return (str(pattern.relative_to(self.root_path)), 0.7)

        return (None, 0.0)

    def _count_test_methods(self, test_files: list[Path]) -> int:
        """Count total test methods across all test files."""
        count = 0
        for test_file in test_files:
            try:
                content = test_file.read_text()
                # Simple regex count for test methods
                count += len(re.findall(r"def test_\w+", content))
            except (OSError, UnicodeDecodeError):
                pass
        return count

    def _detect_frameworks(self, test_files: list[Path]) -> list[str]:
        """Detect test frameworks in use."""
        frameworks = set()
        for test_file in test_files:
            try:
                content = test_file.read_text()
                if "import pytest" in content or "from pytest" in content:
                    frameworks.add("pytest")
                if "import unittest" in content or "from unittest" in content:
                    frameworks.add("unittest")
                if "@pytest.fixture" in content:
                    frameworks.add("pytest")
            except (OSError, UnicodeDecodeError):
                pass
        return list(frameworks)

    def _categorize_tests(self, test_files: list[Path]) -> dict[str, int]:
        """Categorize tests by type (unit, integration, etc.)."""
        categories: dict[str, int] = {}
        for test_file in test_files:
            rel_path = str(test_file.relative_to(self.root_path))
            if "/unit/" in rel_path:
                categories["unit"] = categories.get("unit", 0) + 1
            elif "/integration/" in rel_path:
                categories["integration"] = categories.get("integration", 0) + 1
            elif "/e2e/" in rel_path:
                categories["e2e"] = categories.get("e2e", 0) + 1
            else:
                categories["other"] = categories.get("other", 0) + 1
        return categories
