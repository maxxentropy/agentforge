#!/usr/bin/env python3
"""
Context Retrieval CLI
=====================

Command-line interface for context retrieval.

Extracted from context_retrieval.py for modularity.
"""

import sys
import argparse


def build_parser():
    """Build argument parser for context retrieval CLI."""
    parser = argparse.ArgumentParser(
        description="AgentForge Context Retrieval",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  python context_retrieval.py -p /path check\n"
               "  python context_retrieval.py -p /path search 'order processing'"
    )
    parser.add_argument("--project", "-p", required=True, help="Project root path")
    parser.add_argument("--config", "-c", help="Config file path")

    subparsers = parser.add_subparsers(dest="command", help="Command")
    subparsers.add_parser("check", help="Check available components")

    idx_parser = subparsers.add_parser("index", help="Build/rebuild index")
    idx_parser.add_argument("--force", "-f", action="store_true", help="Force rebuild")

    search_parser = subparsers.add_parser("search", help="Search for code context")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--budget", "-b", type=int, default=6000, help="Token budget")
    search_parser.add_argument("--no-lsp", action="store_true", help="Disable LSP")
    search_parser.add_argument("--no-vector", action="store_true", help="Disable vector search")
    search_parser.add_argument("--format", "-f", choices=["text", "yaml", "json"], default="text")

    sym_parser = subparsers.add_parser("symbol", help="Get context for a symbol")
    sym_parser.add_argument("name", help="Symbol name")

    return parser


def run_check_command(retriever, project: str):
    """Run the check command to display component status."""
    print(f"Checking components for: {project}\n")
    status = retriever.check_dependencies()

    print("LSP (Language Server Protocol):")
    lsp = status["lsp"]
    if lsp["available"]:
        print(f"  Status: Available\n  Server: {lsp['server']}")
    else:
        print("  Status: Not available")
        if lsp.get("error"):
            print(f"  Error: {lsp['error']}")
        if lsp.get("install_instructions"):
            print(f"  Install: {lsp['install_instructions']}")

    print("\nVector Search:")
    vec = status["vector"]
    if vec["available"]:
        print(f"  Status: Available\n  Indexed: {'Yes' if vec['indexed'] else 'No (run: index command)'}")
    else:
        print("  Status: Not available")
        if vec.get("error"):
            print(f"  Error: {vec['error']}")
        print("  Install: pip install openai faiss-cpu")


def run_index_command(retriever, project: str, force: bool):
    """Run the index command to build vector index."""
    print(f"Indexing: {project}")
    stats = retriever.index(force_rebuild=force)
    print(f"\nIndex complete:\n  Files: {stats.file_count}\n  Chunks: {stats.chunk_count}\n  Duration: {stats.duration_ms}ms")
    if stats.errors:
        print(f"  Errors: {len(stats.errors)}")
        for err in stats.errors[:5]:
            print(f"    - {err}")


def run_search_command(retriever, args) -> int:
    """Run the search command."""
    print(f"Searching: {args.query}\nProject: {args.project}\nBudget: {args.budget} tokens\n")
    context = retriever.retrieve(
        args.query,
        budget_tokens=args.budget,
        use_lsp=not args.no_lsp,
        use_vector=not args.no_vector
    )

    if args.format == "yaml":
        print(context.to_yaml())
    elif args.format == "json":
        import json
        print(json.dumps(context.to_dict(), indent=2))
    else:
        print(context.to_prompt_text())

    return 0


def run_symbol_command(retriever, name: str) -> int:
    """Run the symbol command."""
    print(f"Getting context for symbol: {name}")
    context = retriever.get_symbol_context(name)
    if context:
        print(context.to_prompt_text())
        return 0
    print(f"Symbol not found: {name}")
    return 1


def dispatch_command(retriever, args) -> int:
    """Dispatch to appropriate command handler."""
    if args.command == "check":
        run_check_command(retriever, args.project)
        return 0
    if args.command == "index":
        run_index_command(retriever, args.project, args.force)
        return 0
    if args.command == "search":
        return run_search_command(retriever, args)
    if args.command == "symbol":
        return run_symbol_command(retriever, args.name)
    return 1


def main():
    """Main entry point for CLI."""
    try:
        from .context_retrieval import ContextRetriever
    except ImportError:
        from context_retrieval import ContextRetriever

    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    retriever = ContextRetriever(args.project, args.config)

    try:
        return dispatch_command(retriever, args)
    except KeyboardInterrupt:
        print("\nInterrupted")
        return 130
    except Exception as e:
        print(f"\nError: {e}")
        return 1
    finally:
        retriever.shutdown()


if __name__ == "__main__":
    sys.exit(main())
