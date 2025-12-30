#!/usr/bin/env python3
"""
AST-based Contract Checks
=========================

Code metrics and structural checks using Python's AST module.

Metrics supported:
- Cyclomatic complexity
- Function length
- Nesting depth
- Parameter count
- Class size
- Import count
"""

import ast
from pathlib import Path
from typing import Dict, List, Optional, Any


def execute_ast_check(check_id: str, check_name: str, severity: str,
                      config: Dict, repo_root: Path, file_paths: List[Path],
                      fix_hint: Optional[str]) -> List:
    """
    Execute an AST-based structural/metrics check.

    Uses Python's ast module for code metrics like:
    - Cyclomatic complexity
    - Function length
    - Nesting depth
    - Parameter count
    - Class size
    - Import count
    """
    from tools.contracts import CheckResult

    metric = config.get("metric", "cyclomatic_complexity")
    threshold = config.get("threshold", 10)

    results = []

    for file_path in file_paths:
        if file_path.suffix != ".py":
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError as e:
            results.append(CheckResult(
                check_id=check_id,
                check_name=check_name,
                passed=False,
                severity="warning",
                message=f"Syntax error parsing {file_path.name}: {e}",
                file_path=str(file_path.relative_to(repo_root))
            ))
            continue
        except Exception:
            continue

        relative_path = str(file_path.relative_to(repo_root))
        violations = _get_violations(metric, tree, content, threshold, relative_path)

        for v in violations:
            results.append(CheckResult(
                check_id=check_id,
                check_name=check_name,
                passed=False,
                severity=severity,
                message=v["message"],
                file_path=relative_path,
                line_number=v.get("line"),
                fix_hint=fix_hint
            ))

    return results


def _get_violations(metric: str, tree: ast.AST, content: str,
                    threshold: int, file_path: str) -> List[Dict]:
    """Get violations for the specified metric."""
    metric_funcs = {
        "cyclomatic_complexity": check_cyclomatic_complexity,
        "function_length": check_function_length,
        "nesting_depth": check_nesting_depth,
        "parameter_count": check_parameter_count,
        "class_size": check_class_size,
        "import_count": lambda t, c, th: check_import_count(t, c, th, file_path),
    }
    func = metric_funcs.get(metric)
    return func(tree, content, threshold) if func else []


def check_cyclomatic_complexity(tree: ast.AST, content: str, threshold: int) -> List[Dict]:
    """Check cyclomatic complexity of functions."""
    violations = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            complexity = _calculate_complexity(node)

            if complexity > threshold:
                violations.append({
                    "message": f"Function '{node.name}' has complexity {complexity} (max: {threshold})",
                    "line": node.lineno
                })

    return violations


def _calculate_complexity(node: ast.AST) -> int:
    """Calculate cyclomatic complexity for a function node."""
    complexity = 1  # Base complexity

    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.IfExp)):
            complexity += 1
        elif isinstance(child, (ast.For, ast.AsyncFor)):
            complexity += 1
        elif isinstance(child, ast.While):
            complexity += 1
        elif isinstance(child, ast.ExceptHandler):
            complexity += 1
        elif isinstance(child, (ast.With, ast.AsyncWith)):
            complexity += 1
        elif isinstance(child, ast.Assert):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
        elif isinstance(child, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            complexity += len(child.generators)

    return complexity


def check_function_length(tree: ast.AST, content: str, threshold: int) -> List[Dict]:
    """Check function line counts."""
    violations = []
    lines = content.split("\n")

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start_line = node.lineno
            end_line = node.end_lineno or start_line

            func_lines = 0
            for i in range(start_line - 1, min(end_line, len(lines))):
                line = lines[i].strip()
                if line and not line.startswith("#"):
                    func_lines += 1

            if func_lines > threshold:
                violations.append({
                    "message": f"Function '{node.name}' has {func_lines} lines (max: {threshold})",
                    "line": node.lineno
                })

    return violations


def check_nesting_depth(tree: ast.AST, content: str, threshold: int) -> List[Dict]:
    """Check maximum nesting depth in functions."""
    violations = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            max_depth = _calculate_max_nesting(node)

            if max_depth > threshold:
                violations.append({
                    "message": f"Function '{node.name}' has nesting depth {max_depth} (max: {threshold})",
                    "line": node.lineno
                })

    return violations


def _calculate_max_nesting(node: ast.AST, current_depth: int = 0) -> int:
    """Recursively calculate maximum nesting depth."""
    nesting_nodes = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With,
                     ast.AsyncWith, ast.Try, ast.ExceptHandler)

    max_depth = current_depth

    for child in ast.iter_child_nodes(node):
        if isinstance(child, nesting_nodes):
            child_depth = _calculate_max_nesting(child, current_depth + 1)
        else:
            child_depth = _calculate_max_nesting(child, current_depth)
        max_depth = max(max_depth, child_depth)

    return max_depth


def check_parameter_count(tree: ast.AST, content: str, threshold: int) -> List[Dict]:
    """Check function parameter counts."""
    violations = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = node.args
            param_count = (
                len(args.posonlyargs) +
                len(args.args) +
                len(args.kwonlyargs) +
                (1 if args.vararg else 0) +
                (1 if args.kwarg else 0)
            )

            if args.args and args.args[0].arg in ("self", "cls"):
                param_count -= 1

            if param_count > threshold:
                violations.append({
                    "message": f"Function '{node.name}' has {param_count} parameters (max: {threshold})",
                    "line": node.lineno
                })

    return violations


def check_class_size(tree: ast.AST, content: str, threshold: int) -> List[Dict]:
    """Check class method/property counts."""
    violations = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            member_count = sum(
                1 for item in node.body
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
            )

            if member_count > threshold:
                violations.append({
                    "message": f"Class '{node.name}' has {member_count} methods (max: {threshold})",
                    "line": node.lineno
                })

    return violations


def check_import_count(tree: ast.AST, content: str, threshold: int,
                       file_path: str) -> List[Dict]:
    """Check import count per file."""
    import_count = 0

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            import_count += len(node.names)
        elif isinstance(node, ast.ImportFrom):
            import_count += len(node.names)

    if import_count > threshold:
        return [{
            "message": f"File has {import_count} imports (max: {threshold})",
            "line": 1
        }]

    return []
