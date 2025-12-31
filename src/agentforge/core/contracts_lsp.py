#!/usr/bin/env python3
"""
LSP-based Contract Checks
=========================

Semantic code analysis using Language Server Protocol.

Query types supported:
- symbols: Document symbols with kind/visibility/modifier filtering
- references: Symbol reference analysis
- diagnostics: Compiler errors/warnings
- call_hierarchy: Call graph analysis
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .contracts_execution import CheckContext


def execute_lsp_query_check(ctx: "CheckContext") -> List:
    """Execute an LSP-based semantic code analysis check."""
    from agentforge.core.contracts import CheckResult

    try:
        from agentforge.core.lsp_adapter import get_lsp_adapter
    except ImportError:
        return [CheckResult(check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
                           severity="warning", message="LSP adapter not available - skipping semantic check")]

    query_type = ctx.config.get("query", "symbols")
    filter_config = ctx.config.get("filter", {})
    exclude_config = ctx.config.get("exclude", {})
    assertion = ctx.config.get("assertion", "none_exist")
    results = []

    for file_path in ctx.file_paths:
        try:
            adapter = get_lsp_adapter(file_path)
            if adapter is None:
                continue
        except Exception:
            continue

        try:
            matches = _run_lsp_query(adapter, file_path, query_type, filter_config, exclude_config)
            rel_path = str(file_path.relative_to(ctx.repo_root))

            if assertion in ("none_exist", "count_zero"):
                for match in matches:
                    results.append(CheckResult(
                        check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
                        severity=ctx.severity, file_path=rel_path, fix_hint=ctx.fix_hint,
                        message=f"Found {match.get('kind', 'symbol')}: {match.get('name', 'unknown')}",
                        line_number=match.get("line"), column=match.get("column"),
                    ))
            elif assertion in ("all_exist", "count_nonzero") and not matches:
                results.append(CheckResult(
                    check_id=ctx.check_id, check_name=ctx.check_name, passed=False,
                    severity=ctx.severity, file_path=rel_path, fix_hint=ctx.fix_hint,
                    message=f"Required pattern not found in {file_path.name}",
                ))
        except Exception as e:
            results.append(CheckResult(
                check_id=ctx.check_id, check_name=ctx.check_name, passed=False, severity="warning",
                message=f"LSP query failed for {file_path.name}: {e}",
                file_path=str(file_path.relative_to(ctx.repo_root))
            ))

    return results


def _run_lsp_query(adapter, file_path: Path, query_type: str,
                   filter_config: Dict, exclude_config: Dict) -> list:
    """Run LSP query based on query type."""
    query_funcs = {
        "symbols": _lsp_query_symbols,
        "references": _lsp_query_references,
        "diagnostics": _lsp_query_diagnostics,
        "call_hierarchy": _lsp_query_call_hierarchy,
    }
    func = query_funcs.get(query_type)
    return func(adapter, file_path, filter_config, exclude_config) if func else []


# =============================================================================
# Symbol Filtering Helpers
# =============================================================================

def _symbol_matches_kind(symbol: Dict, kind_filter) -> bool:
    """Check if symbol matches kind filter."""
    if not kind_filter:
        return True
    kinds = [kind_filter] if isinstance(kind_filter, str) else kind_filter
    return symbol.get("kind", "").lower() in [k.lower() for k in kinds]


def _symbol_matches_visibility(symbol: Dict, visibility_filter) -> bool:
    """Check if symbol matches visibility filter."""
    if not visibility_filter:
        return True
    return symbol.get("visibility", "").lower() == visibility_filter.lower()


def _symbol_matches_name(symbol: Dict, name_pattern) -> bool:
    """Check if symbol matches name pattern filter."""
    if not name_pattern:
        return True
    return bool(re.match(name_pattern, symbol.get("name", "")))


def _symbol_has_modifiers(symbol: Dict, required_modifiers: list) -> bool:
    """Check if symbol has all required modifiers."""
    if not required_modifiers:
        return True
    symbol_modifiers = [m.lower() for m in symbol.get("modifiers", [])]
    return all(m.lower() in symbol_modifiers for m in required_modifiers)


def _symbol_excluded_by_modifiers(symbol: Dict, exclude_modifiers: list) -> bool:
    """Check if symbol is excluded by modifier rules."""
    if not exclude_modifiers:
        return False
    symbol_modifiers = [m.lower() for m in symbol.get("modifiers", [])]
    for excl in exclude_modifiers:
        excl_parts = [p.lower() for p in excl.split()]
        if all(p in symbol_modifiers for p in excl_parts):
            return True
    return False


def _symbol_excluded_by_name(symbol: Dict, exclude_pattern) -> bool:
    """Check if symbol is excluded by name pattern."""
    if not exclude_pattern:
        return False
    return bool(re.match(exclude_pattern, symbol.get("name", "")))


def _symbol_excluded_by_container(symbol: Dict, exclude_containers: list) -> bool:
    """Check if symbol is excluded by container."""
    if not exclude_containers:
        return False
    container = symbol.get("container", "")
    return any(c.lower() in container.lower() for c in exclude_containers)


# =============================================================================
# LSP Query Implementations
# =============================================================================

def _lsp_query_symbols(adapter, file_path: Path, filter_config: Dict,
                       exclude_config: Dict) -> List[Dict]:
    """Query document symbols and filter by criteria."""
    try:
        symbols = adapter.document_symbols(str(file_path))
    except Exception:
        symbols = []

    matches = []
    for symbol in symbols:
        if not _symbol_matches_kind(symbol, filter_config.get("kind")):
            continue
        if not _symbol_matches_visibility(symbol, filter_config.get("visibility")):
            continue
        if not _symbol_matches_name(symbol, filter_config.get("name_pattern")):
            continue
        if not _symbol_has_modifiers(symbol, filter_config.get("has_modifier", [])):
            continue

        if _symbol_excluded_by_modifiers(symbol, exclude_config.get("modifiers", [])):
            continue
        if _symbol_excluded_by_name(symbol, exclude_config.get("name_pattern")):
            continue
        if _symbol_excluded_by_container(symbol, exclude_config.get("containers", [])):
            continue

        matches.append(symbol)

    return matches


def _lsp_query_references(adapter, file_path: Path, filter_config: Dict,
                          exclude_config: Dict) -> List[Dict]:
    """Query references - placeholder for future implementation."""
    return []


def _lsp_query_diagnostics(adapter, file_path: Path, filter_config: Dict,
                           exclude_config: Dict) -> List[Dict]:
    """Query compiler diagnostics."""
    try:
        diagnostics = adapter.diagnostics(str(file_path))
    except Exception:
        diagnostics = []

    matches = []
    for diag in diagnostics:
        severity_filter = filter_config.get("severity")
        if severity_filter and diag.get("severity", "").lower() != severity_filter.lower():
            continue

        matches.append({
            "name": diag.get("message", ""),
            "kind": "diagnostic",
            "line": diag.get("line"),
            "column": diag.get("column")
        })

    return matches


def _lsp_query_call_hierarchy(adapter, file_path: Path, filter_config: Dict,
                              exclude_config: Dict) -> List[Dict]:
    """Query call hierarchy - placeholder for future implementation."""
    return []
