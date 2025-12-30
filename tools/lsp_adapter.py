#!/usr/bin/env python3
"""
LSP Adapter
===========

Wraps language servers for compiler-accurate code intelligence.

This is the foundation of context retrieval - LSP gives us the compiler's
view of the code, which is the only source of truth.

Supported servers:
- csharp-ls (C#/.NET) - PRIMARY TARGET
- pyright (Python)
- typescript-language-server (TypeScript)

Usage:
    adapter = CSharpLSPAdapter("/path/to/project")
    adapter.initialize()

    # Get all symbols in a file
    symbols = adapter.get_symbols("src/Domain/Order.cs")

    # Find where a symbol is defined
    definition = adapter.get_definition("src/App/OrderService.cs", line=45, col=12)

    # Find all usages of a symbol
    references = adapter.get_references("src/Domain/Order.cs", line=10, col=18)

    adapter.shutdown()

LSP Protocol Notes:
- Uses JSON-RPC 2.0 over stdin/stdout
- Lifecycle: initialize → initialized → requests → shutdown → exit
- Documents must be opened before querying (textDocument/didOpen)
- Line/column numbers are 0-based in LSP (unlike editors which are 1-based)
"""

import os
import sys
import shutil
import time
from typing import Optional, List
from pathlib import Path

from .lsp_types import Location, Symbol, SymbolKind, Diagnostic, HoverInfo
from .lsp_client import (
    LSPClient, LSPError, LSPServerNotFound, LSPInitializationError,
    LSPRequestError, LSPTimeoutError
)


# =============================================================================
# LSP Adapter Base Class
# =============================================================================

class LSPAdapter:
    """Abstract adapter for language servers."""

    SERVER_COMMAND: List[str] = []
    SERVER_NAME: str = "unknown"
    INSTALL_INSTRUCTIONS: str = ""
    LANGUAGE_ID: str = "text"
    FILE_EXTENSIONS: List[str] = []

    def __init__(self, project_path: str):
        """
        Initialize adapter for a project.

        Args:
            project_path: Root directory of the project
        """
        self.project_path = Path(project_path).resolve()
        self.client: Optional[LSPClient] = None
        self._initialized = False
        self._open_documents: set = set()

    def _check_server_installed(self) -> bool:
        """Check if the language server is installed."""
        if not self.SERVER_COMMAND:
            return False
        return shutil.which(self.SERVER_COMMAND[0]) is not None

    def initialize(self) -> bool:
        """
        Initialize the language server.

        Returns:
            True if initialization successful

        Raises:
            LSPServerNotFound: If server binary not found
            LSPInitializationError: If server fails to initialize
        """
        if self._initialized:
            return True

        if not self._check_server_installed():
            raise LSPServerNotFound(self.SERVER_NAME, self.INSTALL_INSTRUCTIONS)

        self.client = LSPClient(self.SERVER_COMMAND, str(self.project_path))

        try:
            init_params = self._get_initialize_params()
            self.client.send_request('initialize', init_params, timeout=60.0)
            self.client.send_notification('initialized', {})
            self._initialized = True
            time.sleep(1.0)  # Give server time to index
            return True

        except Exception as e:
            self.shutdown()
            raise LSPInitializationError(f"Failed to initialize {self.SERVER_NAME}: {e}")

    def _get_initialize_params(self) -> dict:
        """Get initialization parameters for the server."""
        return {
            'processId': os.getpid(),
            'rootUri': f"file://{self.project_path}",
            'rootPath': str(self.project_path),
            'capabilities': {
                'textDocument': {
                    'documentSymbol': {'hierarchicalDocumentSymbolSupport': True},
                    'definition': {'linkSupport': True},
                    'references': {},
                    'hover': {'contentFormat': ['markdown', 'plaintext']},
                    'publishDiagnostics': {'relatedInformation': True},
                },
                'workspace': {
                    'symbol': {'symbolKind': {'valueSet': list(range(1, 27))}},
                },
            },
            'initializationOptions': self._get_initialization_options(),
        }

    def _get_initialization_options(self) -> dict:
        """Get server-specific initialization options. Override in subclass."""
        return {}

    def _ensure_initialized(self):
        """Ensure the server is initialized."""
        if not self._initialized:
            self.initialize()

    def _open_document(self, file_path: str):
        """Open a document in the server."""
        if not self.client:
            return

        abs_path = Path(file_path)
        if not abs_path.is_absolute():
            abs_path = self.project_path / file_path

        uri = f"file://{abs_path}"
        if uri in self._open_documents:
            return

        try:
            with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

            self.client.send_notification('textDocument/didOpen', {
                'textDocument': {
                    'uri': uri, 'languageId': self.LANGUAGE_ID,
                    'version': 1, 'text': content,
                },
            })
            self._open_documents.add(uri)
            time.sleep(0.1)
        except Exception:
            pass

    def _close_document(self, file_path: str):
        """Close a document in the server."""
        if not self.client:
            return

        abs_path = Path(file_path)
        if not abs_path.is_absolute():
            abs_path = self.project_path / file_path

        uri = f"file://{abs_path}"
        if uri not in self._open_documents:
            return

        self.client.send_notification('textDocument/didClose', {'textDocument': {'uri': uri}})
        self._open_documents.discard(uri)

    def get_symbols(self, file: str) -> List[Symbol]:
        """Get all symbols defined in a file."""
        self._ensure_initialized()
        self._open_document(file)

        abs_path = Path(file)
        if not abs_path.is_absolute():
            abs_path = self.project_path / file

        try:
            result = self.client.send_request('textDocument/documentSymbol', {
                'textDocument': {'uri': f"file://{abs_path}"},
            })
            if not result:
                return []
            return self._parse_document_symbols(result, str(abs_path))
        except LSPRequestError:
            return []

    def _parse_document_symbols(self, symbols: list, file_path: str, container: str = None) -> List[Symbol]:
        """Parse document symbols from LSP response."""
        result = []
        for sym in symbols:
            if 'range' in sym:
                range_info = sym['range']['start']
                symbol = Symbol(
                    name=sym.get('name', ''),
                    kind=SymbolKind.to_string(sym.get('kind', 0)),
                    location=Location(
                        file=file_path,
                        line=range_info.get('line', 0),
                        column=range_info.get('character', 0),
                    ),
                    container=container,
                    detail=sym.get('detail'),
                )
                if 'children' in sym:
                    symbol.children = self._parse_document_symbols(
                        sym['children'], file_path, sym.get('name', ''))
                result.append(symbol)

            elif 'location' in sym:
                loc = sym['location']
                range_info = loc.get('range', {}).get('start', {})
                symbol = Symbol(
                    name=sym.get('name', ''),
                    kind=SymbolKind.to_string(sym.get('kind', 0)),
                    location=Location(
                        file=self._uri_to_path(loc.get('uri', '')),
                        line=range_info.get('line', 0),
                        column=range_info.get('character', 0),
                    ),
                    container=sym.get('containerName'),
                )
                result.append(symbol)
        return result

    def _uri_to_path(self, uri: str) -> str:
        """Convert URI to file path."""
        if uri.startswith('file://'):
            return uri[7:]
        return uri

    def get_workspace_symbols(self, query: str) -> List[Symbol]:
        """Search for symbols across the workspace."""
        self._ensure_initialized()

        try:
            result = self.client.send_request('workspace/symbol', {'query': query})
            if not result:
                return []

            symbols = []
            for sym in result:
                loc = sym.get('location', {})
                range_info = loc.get('range', {}).get('start', {})
                symbols.append(Symbol(
                    name=sym.get('name', ''),
                    kind=SymbolKind.to_string(sym.get('kind', 0)),
                    location=Location(
                        file=self._uri_to_path(loc.get('uri', '')),
                        line=range_info.get('line', 0),
                        column=range_info.get('character', 0),
                    ),
                    container=sym.get('containerName'),
                ))
            return symbols
        except LSPRequestError:
            return []

    def get_definition(self, file: str, line: int, col: int) -> Optional[Location]:
        """Get definition location for symbol at position (0-based line/col)."""
        self._ensure_initialized()
        self._open_document(file)

        abs_path = Path(file)
        if not abs_path.is_absolute():
            abs_path = self.project_path / file

        try:
            result = self.client.send_request('textDocument/definition', {
                'textDocument': {'uri': f"file://{abs_path}"},
                'position': {'line': line, 'character': col},
            })

            if not result:
                return None

            loc = result[0] if isinstance(result, list) and len(result) > 0 else result

            if 'targetUri' in loc:
                uri = loc['targetUri']
                range_info = loc.get('targetRange', {}).get('start', {})
            else:
                uri = loc.get('uri', '')
                range_info = loc.get('range', {}).get('start', {})

            return Location(
                file=self._uri_to_path(uri),
                line=range_info.get('line', 0),
                column=range_info.get('character', 0),
            )
        except LSPRequestError:
            return None

    def get_references(self, file: str, line: int, col: int, include_declaration: bool = True) -> List[Location]:
        """Get all references to symbol at position (0-based line/col)."""
        self._ensure_initialized()
        self._open_document(file)

        abs_path = Path(file)
        if not abs_path.is_absolute():
            abs_path = self.project_path / file

        try:
            result = self.client.send_request('textDocument/references', {
                'textDocument': {'uri': f"file://{abs_path}"},
                'position': {'line': line, 'character': col},
                'context': {'includeDeclaration': include_declaration},
            })

            if not result:
                return []

            locations = []
            for loc in result:
                range_info = loc.get('range', {}).get('start', {})
                locations.append(Location(
                    file=self._uri_to_path(loc.get('uri', '')),
                    line=range_info.get('line', 0),
                    column=range_info.get('character', 0),
                ))
            return locations
        except LSPRequestError:
            return []

    def get_hover(self, file: str, line: int, col: int) -> Optional[HoverInfo]:
        """Get hover information for symbol at position (0-based line/col)."""
        self._ensure_initialized()
        self._open_document(file)

        abs_path = Path(file)
        if not abs_path.is_absolute():
            abs_path = self.project_path / file

        try:
            result = self.client.send_request('textDocument/hover', {
                'textDocument': {'uri': f"file://{abs_path}"},
                'position': {'line': line, 'character': col},
            })

            if not result or 'contents' not in result:
                return None

            contents = result['contents']
            if isinstance(contents, str):
                text = contents
            elif isinstance(contents, dict):
                text = contents.get('value', str(contents))
            elif isinstance(contents, list):
                text = '\n'.join(
                    c.get('value', str(c)) if isinstance(c, dict) else str(c)
                    for c in contents
                )
            else:
                text = str(contents)

            return HoverInfo(contents=text)
        except LSPRequestError:
            return None

    def get_diagnostics(self, file: str) -> List[Diagnostic]:
        """Get compiler errors/warnings for a file."""
        self._ensure_initialized()
        self._open_document(file)

        abs_path = Path(file)
        if not abs_path.is_absolute():
            abs_path = self.project_path / file

        time.sleep(0.5)  # Give server time to compute diagnostics
        return self.client.get_diagnostics(str(abs_path)) if self.client else []

    def shutdown(self):
        """Gracefully shutdown the language server."""
        for uri in list(self._open_documents):
            if self.client:
                self.client.send_notification('textDocument/didClose', {'textDocument': {'uri': uri}})
        self._open_documents.clear()

        if self.client:
            self.client.shutdown()
            self.client = None
        self._initialized = False


# =============================================================================
# Re-exports for backwards compatibility
# =============================================================================

# Import language-specific adapters for re-export
# Done at module level to avoid circular imports
def _get_adapters():
    from .lsp_adapters import (
        CSharpLSPAdapter, OmniSharpAdapter, PyrightAdapter, TypeScriptAdapter,
        get_adapter_for_project
    )
    return CSharpLSPAdapter, OmniSharpAdapter, PyrightAdapter, TypeScriptAdapter, get_adapter_for_project


# =============================================================================
# CLI for Testing
# =============================================================================

def _build_lsp_cli_parser():
    """Build argument parser for LSP CLI."""
    import argparse
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


def _get_lsp_adapter(args):
    """Get appropriate LSP adapter based on args."""
    CSharpLSPAdapter, OmniSharpAdapter, PyrightAdapter, TypeScriptAdapter, get_adapter_for_project = _get_adapters()
    if args.language:
        adapters = {"csharp": CSharpLSPAdapter, "python": PyrightAdapter, "typescript": TypeScriptAdapter}
        return adapters[args.language](args.project)
    return get_adapter_for_project(args.project)


def _print_symbols(adapter, args):
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


def _print_definition(adapter, args):
    """Print definition location."""
    loc = adapter.get_definition(args.file, args.line - 1, args.column - 1)
    print(f"\nDefinition: {loc}" if loc else "\nNo definition found")


def _print_references(adapter, args):
    """Print reference locations."""
    refs = adapter.get_references(args.file, args.line - 1, args.column - 1)
    print(f"\nReferences ({len(refs)}):")
    for ref in refs:
        print(f"  {ref}")


def _print_hover(adapter, args):
    """Print hover information."""
    info = adapter.get_hover(args.file, args.line - 1, args.column - 1)
    print(f"\nHover info:\n{info.contents}" if info else "\nNo hover info")


def _print_search_results(adapter, args):
    """Print workspace symbol search results."""
    symbols = adapter.get_workspace_symbols(args.query)
    print(f"\nWorkspace symbols matching '{args.query}' ({len(symbols)}):")
    for sym in symbols[:20]:
        print(f"  {sym.kind}: {sym.name}\n    at {sym.location}")


def _run_lsp_command(adapter, args):
    """Run the specified LSP command."""
    handlers = {
        "symbols": _print_symbols, "definition": _print_definition,
        "references": _print_references, "hover": _print_hover,
        "search": _print_search_results,
    }
    handler = handlers.get(args.command)
    if handler:
        handler(adapter, args)


def main():
    parser = _build_lsp_cli_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    adapter = _get_lsp_adapter(args)
    print(f"Using {adapter.SERVER_NAME} for {args.project}")

    try:
        print("Initializing LSP server...")
        adapter.initialize()
        print("Server initialized successfully")
        _run_lsp_command(adapter, args)
    except (LSPServerNotFound, LSPInitializationError) as e:
        print(f"\nError: {e}")
        return 1
    finally:
        print("\nShutting down...")
        adapter.shutdown()

    return 0


if __name__ == "__main__":
    sys.exit(main())
