"""
Context retrieval command.

Tests and manages the context retrieval system for code intelligence.
Uses LSP and/or vector search to find relevant code context.
"""

import sys
import json
import click
from pathlib import Path


def _ensure_context_tools():
    """Add tools directory to path for context imports."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'tools'))


def run_context(args):
    """Test context retrieval system."""
    click.echo()
    click.echo("=" * 60)
    click.echo("CONTEXT RETRIEVAL")
    click.echo("=" * 60)

    _ensure_context_tools()

    try:
        from context_retrieval import ContextRetriever
    except ImportError as e:
        click.echo(f"\nError: Could not import context_retrieval: {e}")
        sys.exit(1)

    click.echo(f"\n  Project: {args.project}")

    provider = getattr(args, 'provider', None)
    retriever = ContextRetriever(args.project, provider=provider)

    try:
        if args.check:
            _run_check(retriever)
        elif args.index:
            _run_index(retriever, args.force)
            if args.query:
                _run_query(retriever, args)
        elif args.query:
            _run_query(retriever, args)
        else:
            _print_usage()
    finally:
        retriever.shutdown()


def _run_check(retriever):
    """Check available components."""
    click.echo("\nChecking components...")
    status = retriever.check_dependencies()

    _print_lsp_status(status["lsp"])
    _print_embedding_providers()
    _print_vector_status(status["vector"])


def _print_lsp_status(lsp):
    """Print LSP status."""
    click.echo("\n  LSP (Language Server Protocol):")
    if lsp["available"]:
        click.echo(f"    Status: Available")
        click.echo(f"    Server: {lsp.get('server', 'unknown')}")
    else:
        click.echo(f"    Status: Not available")
        if lsp.get("error"):
            click.echo(f"    Error: {lsp['error']}")
        if lsp.get("install_instructions"):
            click.echo(f"    Install: {lsp['install_instructions']}")


def _print_embedding_providers():
    """Print embedding provider status."""
    click.echo("\n  Embedding Providers:")
    try:
        from embedding_providers import list_providers, get_available_providers
        providers = list_providers()
        available = get_available_providers()
        current = available[0] if available else None

        for p in providers:
            mark = "[Y]" if p["available"] else "[N]"
            default = " (current)" if p["name"] == current else ""
            api_note = "" if not p["requires_api_key"] else " (needs API key)"
            click.echo(f"    {mark} {p['name']}{api_note}{default}")
            if not p["available"] and p["install_instructions"]:
                click.echo(f"      Install: {p['install_instructions']}")
    except ImportError:
        click.echo("    Could not load embedding providers")


def _print_vector_status(vec):
    """Print vector search status."""
    click.echo("\n  Vector Search:")
    if vec["available"]:
        click.echo(f"    Status: Available")
        click.echo(f"    Indexed: {'Yes' if vec.get('indexed') else 'No'}")
    else:
        click.echo(f"    Status: Not available")
        if vec.get("error"):
            click.echo(f"    Error: {vec['error']}")
        click.echo("    Install: pip install sentence-transformers faiss-cpu")


def _run_index(retriever, force: bool):
    """Build vector index."""
    click.echo("\nBuilding vector index...")
    stats = retriever.index(force_rebuild=force)
    click.echo(f"  Files indexed: {stats.file_count}")
    click.echo(f"  Chunks created: {stats.chunk_count}")
    click.echo(f"  Duration: {stats.duration_ms}ms")
    if stats.errors:
        click.echo(f"  Errors: {len(stats.errors)}")


def _run_query(retriever, args):
    """Run context query."""
    click.echo(f"\n  Query: {args.query}")
    click.echo(f"  Budget: {args.budget} tokens")
    click.echo()
    click.echo("-" * 60)
    click.echo("Searching...")
    click.echo("-" * 60)

    context = retriever.retrieve(
        args.query,
        budget_tokens=args.budget,
        use_lsp=not args.no_lsp,
        use_vector=not args.no_vector,
    )

    click.echo(f"\n  Found {len(context.files)} files")
    click.echo(f"  Found {len(context.symbols)} symbols")
    click.echo(f"  Total tokens: {context.total_tokens}")
    click.echo()
    click.echo("-" * 60)
    click.echo("RESULTS")
    click.echo("-" * 60)

    _output_context(context, args.format)
    _save_context(context)


def _output_context(context, fmt: str):
    """Output context in specified format."""
    if fmt == 'yaml':
        click.echo(context.to_yaml())
    elif fmt == 'json':
        click.echo(json.dumps(context.to_dict(), indent=2))
    else:
        click.echo(context.to_prompt_text())


def _save_context(context):
    """Save context to file."""
    output_dir = Path('outputs')
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / 'context_retrieval.yaml'

    with open(output_path, 'w') as f:
        f.write(context.to_yaml())

    click.echo(f"\nSaved to: {output_path}")


def _print_usage():
    """Print usage information."""
    click.echo("\nNo action specified. Use --query, --check, or --index")
    click.echo("  python execute.py context -p /path/to/project --check")
    click.echo("  python execute.py context -p /path/to/project --index")
    click.echo("  python execute.py context -p /path/to/project -q 'order processing'")
