#!/usr/bin/env python3
"""
LSP Adapter CLI
===============

Command-line interface for testing LSP adapter functionality.

Extracted from lsp_adapter.py for modularity.
"""

import sys
import argparse


def build_parser():
    """Build argument parser for LSP CLI."""
    parser = argparse.ArgumentParser(
        description="Test LSP adapter functionality",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  python lsp_adapter.py -p /path symbols src/Order.cs\n"
               "  python lsp_adapter.py -p /path definition src/Service.cs 45 12"
    )
    parser.add_argument("--project", "-p", required=True, help="Project root path")
    parser.add_argument("--language", "-l", choices=["csharp", "python", "typescript"],
                        help="Force specific language (auto-detect if not specified)")

    subparsers = parser.add_subparsers(dest="command", help="Command")

    sym_parser = subparsers.add_parser("symbols", help="Get symbols in a file")
    sym_parser.add_argument("file", help="File path")

    for cmd in ["definition", "references", "hover"]:
        p = subparsers.add_parser(cmd, help=f"{'Find' if cmd != 'hover' else 'Get'} {cmd}")
        p.add_argument("file", help="File path")
        p.add_argument("line", type=int, help="Line number (1-based)")
        p.add_argument("column", type=int, help="Column number (1-based)")

    search_parser = subparsers.add_parser("search", help="Search workspace symbols")
    search_parser.add_argument("query", help="Search query")

    return parser


def get_adapter(args):
    """Get appropriate LSP adapter based on args."""
    try:
        from .lsp_adapters import (
            CSharpLSPAdapter, PyrightAdapter, TypeScriptAdapter, get_adapter_for_project
        )
    except ImportError:
        from lsp_adapters import (
            CSharpLSPAdapter, PyrightAdapter, TypeScriptAdapter, get_adapter_for_project
        )

    if args.language:
        adapters = {"csharp": CSharpLSPAdapter, "python": PyrightAdapter, "typescript": TypeScriptAdapter}
        return adapters[args.language](args.project)
    return get_adapter_for_project(args.project)


def print_symbols(adapter, args):
    """Print symbols from a file."""
    symbols = adapter.get_symbols(args.file)
    print(f"\nSymbols in {args.file} ({len(symbols)}):")
    for sym in symbols:
        indent = "  " if sym.container else ""
        print(f"{indent}{sym.kind}: {sym.name}")
        if sym.detail:
            print(f"{indent}  {sym.detail}")
        for child in sym.children:
            print(f"    {child.kind}: {child.name}")


def print_definition(adapter, args):
    """Print definition location."""
    loc = adapter.get_definition(args.file, args.line - 1, args.column - 1)
    print(f"\nDefinition: {loc}" if loc else "\nNo definition found")


def print_references(adapter, args):
    """Print reference locations."""
    refs = adapter.get_references(args.file, args.line - 1, args.column - 1)
    print(f"\nReferences ({len(refs)}):")
    for ref in refs:
        print(f"  {ref}")


def print_hover(adapter, args):
    """Print hover information."""
    info = adapter.get_hover(args.file, args.line - 1, args.column - 1)
    print(f"\nHover info:\n{info.contents}" if info else "\nNo hover info")


def print_search_results(adapter, args):
    """Print workspace symbol search results."""
    symbols = adapter.get_workspace_symbols(args.query)
    print(f"\nWorkspace symbols matching '{args.query}' ({len(symbols)}):")
    for sym in symbols[:20]:
        print(f"  {sym.kind}: {sym.name}\n    at {sym.location}")


def run_command(adapter, args):
    """Run the specified LSP command."""
    handlers = {
        "symbols": print_symbols,
        "definition": print_definition,
        "references": print_references,
        "hover": print_hover,
        "search": print_search_results,
    }
    handler = handlers.get(args.command)
    if handler:
        handler(adapter, args)


def main():
    """Main entry point for CLI."""
    try:
        from .lsp_client import LSPServerNotFound, LSPInitializationError
    except ImportError:
        from lsp_client import LSPServerNotFound, LSPInitializationError

    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    adapter = get_adapter(args)
    print(f"Using {adapter.SERVER_NAME} for {args.project}")

    try:
        print("Initializing LSP server...")
        adapter.initialize()
        print("Server initialized successfully")
        run_command(adapter, args)
    except (LSPServerNotFound, LSPInitializationError) as e:
        print(f"\nError: {e}")
        return 1
    finally:
        print("\nShutting down...")
        adapter.shutdown()

    return 0


if __name__ == "__main__":
    sys.exit(main())
