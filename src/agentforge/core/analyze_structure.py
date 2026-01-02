#!/usr/bin/env python3
"""
Analyze Python file structure for refactoring.

This tool produces AST analysis that can be fed into the SPEC workflow
for refactoring tasks. It identifies logical groupings, dependencies,
and natural module boundaries.

Usage:
    python tools/analyze_structure.py execute.py
    python tools/analyze_structure.py execute.py --format json
"""

import ast
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class ClassInfo:
    """Information about a class in the file."""
    name: str
    line_start: int
    line_end: int
    length: int
    methods: list[str]
    bases: list[str]
    decorators: list[str]
    docstring: str | None


@dataclass
class FunctionInfo:
    """Information about a top-level function."""
    name: str
    line_start: int
    line_end: int
    length: int
    parameters: list[str]
    calls: list[str]
    is_public: bool
    is_async: bool
    decorators: list[str]
    docstring: str | None


@dataclass
class ImportInfo:
    """Information about imports."""
    module: str
    names: list[str]
    is_from_import: bool
    line: int


@dataclass
class LogicalGroup:
    """A group of related functions/classes."""
    name: str
    description: str
    members: list[str]
    total_lines: int
    shared_imports: list[str]
    cohesion_score: float


@dataclass
class FileAnalysis:
    """Complete analysis of a Python file."""
    file_path: str
    total_lines: int
    imports: list[ImportInfo]
    classes: list[ClassInfo]
    functions: list[FunctionInfo]
    logical_groups: list[LogicalGroup]
    suggested_splits: list[dict]

    def to_dict(self) -> dict:
        return asdict(self)

    def to_yaml(self) -> str:
        import yaml
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict(), indent=2)


class StructureAnalyzer(ast.NodeVisitor):
    """AST visitor that extracts structural information."""

    def __init__(self, source: str):
        self.source = source
        self.source_lines = source.splitlines()
        self.imports: list[ImportInfo] = []
        self.classes: list[ClassInfo] = []
        self.functions: list[FunctionInfo] = []
        self._current_class = None

    def visit_Import(self, node: ast.Import):
        self.imports.append(ImportInfo(
            module="",
            names=[alias.name for alias in node.names],
            is_from_import=False,
            line=node.lineno
        ))
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        self.imports.append(ImportInfo(
            module=node.module or "",
            names=[alias.name for alias in node.names],
            is_from_import=True,
            line=node.lineno
        ))
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(item.name)

        docstring = ast.get_docstring(node)

        self.classes.append(ClassInfo(
            name=node.name,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            length=(node.end_lineno or node.lineno) - node.lineno + 1,
            methods=methods,
            bases=[ast.unparse(b) for b in node.bases],
            decorators=[ast.unparse(d) for d in node.decorator_list],
            docstring=docstring[:100] + "..." if docstring and len(docstring) > 100 else docstring
        ))
        # Don't visit children - we don't want nested functions as top-level

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._visit_function(node, is_async=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._visit_function(node, is_async=True)

    def _extract_function_calls(self, node) -> list:
        """Extract all function call names from AST node."""
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(child.func.attr)
        return list(set(calls))

    def _truncate_docstring(self, docstring: str | None) -> str | None:
        """Truncate docstring to 100 chars if needed."""
        if docstring and len(docstring) > 100:
            return docstring[:100] + "..."
        return docstring

    def _visit_function(self, node, is_async: bool):
        """Process a function definition node."""
        if node.col_offset != 0:
            return

        self.functions.append(FunctionInfo(
            name=node.name,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            length=(node.end_lineno or node.lineno) - node.lineno + 1,
            parameters=[arg.arg for arg in node.args.args],
            calls=self._extract_function_calls(node),
            is_public=not node.name.startswith('_'),
            is_async=is_async,
            decorators=[ast.unparse(d) for d in node.decorator_list],
            docstring=self._truncate_docstring(ast.get_docstring(node))
        ))


def _extract_function_prefix(name: str) -> str:
    """Extract grouping prefix from function name."""
    parts = name.split('_')
    if len(parts) < 2:
        return 'misc'
    if parts[0] == 'run' and len(parts) >= 3:
        return f"{parts[0]}_{parts[1]}"
    if parts[0] in ('_', ''):
        return '_helpers'
    return parts[0]


# Prefix descriptions for logical groups
_PREFIX_DESCRIPTIONS = {
    'run_workspace': 'Workspace management commands',
    'run_config': 'Configuration management commands',
    'run_contracts': 'Contract management commands',
    'run_exemptions': 'Exemption management commands',
    '_render': 'Spec rendering helpers',
    'run': 'CLI command handlers',
    '_helpers': 'Internal helper functions',
    'call': 'External API/CLI callers',
}


def identify_logical_groups(functions: list[FunctionInfo]) -> list[LogicalGroup]:
    """Identify logical groupings based on naming patterns and call relationships."""
    prefix_groups = defaultdict(list)
    for func in functions:
        prefix_groups[_extract_function_prefix(func.name)].append(func)

    groups = []
    for prefix, funcs in prefix_groups.items():
        if len(funcs) >= 2:
            groups.append(LogicalGroup(
                name=prefix,
                description=_PREFIX_DESCRIPTIONS.get(prefix, f'Functions with {prefix} prefix'),
                members=[f.name for f in funcs],
                total_lines=sum(f.length for f in funcs),
                shared_imports=[],
                cohesion_score=0.8 if len(funcs) >= 3 else 0.5
            ))

    return sorted(groups, key=lambda g: -g.total_lines)


def suggest_splits(groups: list[LogicalGroup], total_lines: int) -> list[dict]:
    """Suggest how to split the file based on logical groups."""
    suggestions = []

    # Only suggest splits for groups that are substantial
    for group in groups:
        if group.total_lines >= 100:  # At least 100 lines
            pct = (group.total_lines / total_lines) * 100
            suggestions.append({
                'proposed_module': f"{group.name.replace('run_', '')}.py",
                'functions_to_move': group.members,
                'line_count': group.total_lines,
                'percentage_of_file': round(pct, 1),
                'rationale': group.description,
                'cohesion': group.cohesion_score
            })

    return suggestions


def analyze_file(path: Path) -> FileAnalysis:
    """Analyze a Python file's structure."""
    source = path.read_text()
    tree = ast.parse(source)

    analyzer = StructureAnalyzer(source)
    analyzer.visit(tree)

    total_lines = len(source.splitlines())
    logical_groups = identify_logical_groups(analyzer.functions)
    suggested_splits = suggest_splits(logical_groups, total_lines)

    return FileAnalysis(
        file_path=str(path),
        total_lines=total_lines,
        imports=analyzer.imports,
        classes=analyzer.classes,
        functions=analyzer.functions,
        logical_groups=logical_groups,
        suggested_splits=suggested_splits
    )


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Analyze Python file structure for refactoring'
    )
    parser.add_argument('file', help='Python file to analyze')
    parser.add_argument('--format', choices=['yaml', 'json'], default='yaml',
                        help='Output format (default: yaml)')
    parser.add_argument('--summary', action='store_true',
                        help='Show summary only')

    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"Error: {path} not found", file=sys.stderr)
        sys.exit(1)

    analysis = analyze_file(path)

    if args.summary:
        print(f"File: {analysis.file_path}")
        print(f"Total lines: {analysis.total_lines}")
        print(f"Classes: {len(analysis.classes)}")
        print(f"Functions: {len(analysis.functions)}")
        print(f"Logical groups: {len(analysis.logical_groups)}")
        print()
        print("Suggested splits:")
        for split in analysis.suggested_splits:
            print(f"  {split['proposed_module']}: {split['line_count']} lines ({split['percentage_of_file']}%)")
            print(f"    {len(split['functions_to_move'])} functions - {split['rationale']}")
    else:
        if args.format == 'json':
            print(analysis.to_json())
        else:
            print(analysis.to_yaml())


if __name__ == "__main__":
    main()
