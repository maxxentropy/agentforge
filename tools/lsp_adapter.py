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

import subprocess
import json
import threading
import queue
import os
import sys
import shutil
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass, field
from pathlib import Path
from enum import IntEnum
import time


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class Location:
    """Source code location."""
    file: str
    line: int  # 0-based (LSP convention)
    column: int  # 0-based
    end_line: Optional[int] = None
    end_column: Optional[int] = None

    def to_1based(self) -> 'Location':
        """Convert to 1-based line numbers (editor convention)."""
        return Location(
            file=self.file,
            line=self.line + 1,
            column=self.column + 1,
            end_line=self.end_line + 1 if self.end_line is not None else None,
            end_column=self.end_column + 1 if self.end_column is not None else None,
        )

    def __str__(self):
        loc = self.to_1based()
        return f"{loc.file}:{loc.line}:{loc.column}"


class SymbolKind(IntEnum):
    """LSP Symbol kinds."""
    FILE = 1
    MODULE = 2
    NAMESPACE = 3
    PACKAGE = 4
    CLASS = 5
    METHOD = 6
    PROPERTY = 7
    FIELD = 8
    CONSTRUCTOR = 9
    ENUM = 10
    INTERFACE = 11
    FUNCTION = 12
    VARIABLE = 13
    CONSTANT = 14
    STRING = 15
    NUMBER = 16
    BOOLEAN = 17
    ARRAY = 18
    OBJECT = 19
    KEY = 20
    NULL = 21
    ENUM_MEMBER = 22
    STRUCT = 23
    EVENT = 24
    OPERATOR = 25
    TYPE_PARAMETER = 26

    @classmethod
    def to_string(cls, kind: int) -> str:
        """Convert numeric kind to string."""
        kind_map = {
            1: "file", 2: "module", 3: "namespace", 4: "package",
            5: "class", 6: "method", 7: "property", 8: "field",
            9: "constructor", 10: "enum", 11: "interface", 12: "function",
            13: "variable", 14: "constant", 15: "string", 16: "number",
            17: "boolean", 18: "array", 19: "object", 20: "key",
            21: "null", 22: "enum_member", 23: "struct", 24: "event",
            25: "operator", 26: "type_parameter",
        }
        return kind_map.get(kind, f"unknown({kind})")


@dataclass
class Symbol:
    """A code symbol (class, method, property, etc.)."""
    name: str
    kind: str  # class, method, property, field, interface, enum, etc.
    location: Location
    container: Optional[str] = None  # Parent class/namespace
    detail: Optional[str] = None  # Type signature
    children: List['Symbol'] = field(default_factory=list)

    def __str__(self):
        if self.container:
            return f"{self.container}.{self.name} ({self.kind})"
        return f"{self.name} ({self.kind})"


@dataclass
class Diagnostic:
    """Compiler error/warning."""
    file: str
    line: int
    column: int
    severity: str  # error, warning, info, hint
    message: str
    code: Optional[str] = None
    source: Optional[str] = None


@dataclass
class HoverInfo:
    """Hover information for a symbol."""
    contents: str  # Markdown formatted
    range: Optional[Location] = None


# =============================================================================
# Exceptions
# =============================================================================

class LSPError(Exception):
    """Base class for LSP errors."""
    pass


class LSPServerNotFound(LSPError):
    """Raised when the language server binary is not found."""

    def __init__(self, server_name: str, install_instructions: str):
        self.server_name = server_name
        self.install_instructions = install_instructions
        super().__init__(
            f"{server_name} not found.\n"
            f"Install with: {install_instructions}"
        )


class LSPInitializationError(LSPError):
    """Raised when the server fails to initialize."""
    pass


class LSPRequestError(LSPError):
    """Raised when an LSP request fails."""

    def __init__(self, method: str, error: dict):
        self.method = method
        self.error = error
        code = error.get('code', 'unknown')
        message = error.get('message', 'Unknown error')
        super().__init__(f"LSP request '{method}' failed: [{code}] {message}")


class LSPTimeoutError(LSPError):
    """Raised when an LSP request times out."""
    pass


# =============================================================================
# LSP Client (JSON-RPC Communication)
# =============================================================================

class LSPClient:
    """
    Low-level LSP client handling JSON-RPC 2.0 communication.

    Manages the language server subprocess and message passing.
    """

    def __init__(self, command: List[str], project_root: str, timeout: float = 30.0):
        """
        Start language server process.

        Args:
            command: Command to start server, e.g., ["csharp-ls"]
            project_root: Root directory of the project
            timeout: Default timeout for requests in seconds
        """
        self.project_root = Path(project_root).resolve()
        self.timeout = timeout
        self.process: Optional[subprocess.Popen] = None
        self.request_id = 0
        self._lock = threading.Lock()
        self._pending_requests: Dict[int, queue.Queue] = {}
        self._reader_thread: Optional[threading.Thread] = None
        self._running = False
        self._diagnostics: Dict[str, List[Diagnostic]] = {}

        self._start_server(command)

    def _start_server(self, command: List[str]):
        """Start the LSP server subprocess."""
        try:
            self.process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.project_root),
                env={**os.environ, 'NO_COLOR': '1'},
            )
        except FileNotFoundError:
            raise LSPServerNotFound(
                command[0],
                f"Command '{' '.join(command)}' not found in PATH"
            )

        self._running = True
        self._reader_thread = threading.Thread(target=self._read_messages, daemon=True)
        self._reader_thread.start()

    def _read_messages(self):
        """Background thread that reads messages from the server."""
        while self._running and self.process and self.process.stdout:
            try:
                # Read Content-Length header
                header_line = self.process.stdout.readline()
                if not header_line:
                    break

                header = header_line.decode('utf-8').strip()
                if not header.startswith('Content-Length:'):
                    continue

                content_length = int(header.split(':')[1].strip())

                # Read blank line
                self.process.stdout.readline()

                # Read content
                content = self.process.stdout.read(content_length).decode('utf-8')
                message = json.loads(content)

                self._handle_message(message)

            except Exception as e:
                if self._running:
                    # Log error but continue
                    print(f"LSP read error: {e}", file=sys.stderr)

    def _handle_message(self, message: dict):
        """Handle an incoming message from the server."""
        if 'id' in message and 'method' not in message:
            # Response to a request
            request_id = message['id']
            if request_id in self._pending_requests:
                self._pending_requests[request_id].put(message)

        elif 'method' in message:
            # Notification or request from server
            method = message['method']

            if method == 'textDocument/publishDiagnostics':
                # Store diagnostics
                params = message.get('params', {})
                uri = params.get('uri', '')
                diagnostics = params.get('diagnostics', [])
                file_path = self._uri_to_path(uri)
                self._diagnostics[file_path] = [
                    self._parse_diagnostic(d, file_path) for d in diagnostics
                ]

            elif method == 'window/logMessage':
                # Log message from server (could be useful for debugging)
                pass

    def _parse_diagnostic(self, diag: dict, file_path: str) -> Diagnostic:
        """Parse a diagnostic from LSP format."""
        range_info = diag.get('range', {})
        start = range_info.get('start', {})
        severity_map = {1: 'error', 2: 'warning', 3: 'info', 4: 'hint'}

        return Diagnostic(
            file=file_path,
            line=start.get('line', 0),
            column=start.get('character', 0),
            severity=severity_map.get(diag.get('severity', 1), 'error'),
            message=diag.get('message', ''),
            code=str(diag.get('code', '')) if diag.get('code') else None,
            source=diag.get('source'),
        )

    def _send_message(self, message: dict):
        """Send a JSON-RPC message to the server."""
        content = json.dumps(message)
        header = f"Content-Length: {len(content)}\r\n\r\n"
        full_message = header + content

        if self.process and self.process.stdin:
            self.process.stdin.write(full_message.encode('utf-8'))
            self.process.stdin.flush()

    def send_request(self, method: str, params: dict, timeout: float = None) -> dict:
        """
        Send JSON-RPC request and wait for response.

        Args:
            method: LSP method name
            params: Request parameters
            timeout: Timeout in seconds (uses default if not specified)

        Returns:
            Response result

        Raises:
            LSPRequestError: If the request returns an error
            LSPTimeoutError: If the request times out
        """
        timeout = timeout or self.timeout

        with self._lock:
            self.request_id += 1
            request_id = self.request_id

        response_queue: queue.Queue = queue.Queue()
        self._pending_requests[request_id] = response_queue

        try:
            message = {
                'jsonrpc': '2.0',
                'id': request_id,
                'method': method,
                'params': params,
            }
            self._send_message(message)

            # Wait for response
            try:
                response = response_queue.get(timeout=timeout)
            except queue.Empty:
                raise LSPTimeoutError(f"Request '{method}' timed out after {timeout}s")

            if 'error' in response:
                raise LSPRequestError(method, response['error'])

            return response.get('result')

        finally:
            del self._pending_requests[request_id]

    def send_notification(self, method: str, params: dict):
        """Send JSON-RPC notification (no response expected)."""
        message = {
            'jsonrpc': '2.0',
            'method': method,
            'params': params,
        }
        self._send_message(message)

    def get_diagnostics(self, file_path: str) -> List[Diagnostic]:
        """Get cached diagnostics for a file."""
        return self._diagnostics.get(file_path, [])

    def _path_to_uri(self, path: str) -> str:
        """Convert file path to URI."""
        abs_path = Path(path)
        if not abs_path.is_absolute():
            abs_path = self.project_root / path
        return f"file://{abs_path}"

    def _uri_to_path(self, uri: str) -> str:
        """Convert URI to file path."""
        if uri.startswith('file://'):
            return uri[7:]
        return uri

    def shutdown(self):
        """Gracefully shutdown the server."""
        self._running = False

        if self.process:
            try:
                # Send shutdown request
                self.send_request('shutdown', {}, timeout=5.0)
                # Send exit notification
                self.send_notification('exit', {})
                # Wait for process to exit
                self.process.wait(timeout=5.0)
            except Exception:
                # Force kill if graceful shutdown fails
                self.process.kill()
            finally:
                self.process = None

        if self._reader_thread:
            self._reader_thread.join(timeout=2.0)


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

        # Check if server is installed
        if not self._check_server_installed():
            raise LSPServerNotFound(self.SERVER_NAME, self.INSTALL_INSTRUCTIONS)

        # Start the client
        self.client = LSPClient(
            self.SERVER_COMMAND,
            str(self.project_path),
        )

        # Send initialize request
        try:
            init_params = self._get_initialize_params()
            result = self.client.send_request('initialize', init_params, timeout=60.0)

            # Send initialized notification
            self.client.send_notification('initialized', {})

            self._initialized = True

            # Give server time to index (especially for C#)
            time.sleep(1.0)

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
                    'documentSymbol': {
                        'hierarchicalDocumentSymbolSupport': True,
                    },
                    'definition': {
                        'linkSupport': True,
                    },
                    'references': {},
                    'hover': {
                        'contentFormat': ['markdown', 'plaintext'],
                    },
                    'publishDiagnostics': {
                        'relatedInformation': True,
                    },
                },
                'workspace': {
                    'symbol': {
                        'symbolKind': {
                            'valueSet': list(range(1, 27)),
                        },
                    },
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
                    'uri': uri,
                    'languageId': self.LANGUAGE_ID,
                    'version': 1,
                    'text': content,
                },
            })
            self._open_documents.add(uri)

            # Give server time to process
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

        self.client.send_notification('textDocument/didClose', {
            'textDocument': {'uri': uri},
        })
        self._open_documents.discard(uri)

    def get_symbols(self, file: str) -> List[Symbol]:
        """
        Get all symbols defined in a file.

        Uses textDocument/documentSymbol request.
        """
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
            # Handle both DocumentSymbol and SymbolInformation formats
            if 'range' in sym:
                # DocumentSymbol format (hierarchical)
                range_info = sym['range']['start']
                kind = SymbolKind.to_string(sym.get('kind', 0))

                symbol = Symbol(
                    name=sym.get('name', ''),
                    kind=kind,
                    location=Location(
                        file=file_path,
                        line=range_info.get('line', 0),
                        column=range_info.get('character', 0),
                    ),
                    container=container,
                    detail=sym.get('detail'),
                )

                # Parse children
                if 'children' in sym:
                    symbol.children = self._parse_document_symbols(
                        sym['children'],
                        file_path,
                        sym.get('name', '')
                    )

                result.append(symbol)

            elif 'location' in sym:
                # SymbolInformation format (flat)
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
        """
        Search for symbols across the workspace.

        Uses workspace/symbol request.
        """
        self._ensure_initialized()

        try:
            result = self.client.send_request('workspace/symbol', {
                'query': query,
            })

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
        """
        Get definition location for symbol at position.

        Uses textDocument/definition request.

        Args:
            file: File path
            line: 0-based line number
            col: 0-based column number
        """
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

            # Result can be Location, Location[], or LocationLink[]
            if isinstance(result, list) and len(result) > 0:
                loc = result[0]
            else:
                loc = result

            # Handle LocationLink
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
        """
        Get all references to symbol at position.

        Uses textDocument/references request.

        Args:
            file: File path
            line: 0-based line number
            col: 0-based column number
            include_declaration: Whether to include the declaration in results
        """
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
        """
        Get hover information (type, docs) for symbol at position.

        Uses textDocument/hover request.

        Args:
            file: File path
            line: 0-based line number
            col: 0-based column number
        """
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

            # Parse contents (can be string, MarkedString, or MarkupContent)
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
        """
        Get compiler errors/warnings for a file.

        Note: Diagnostics are pushed by server, this returns cached values.
        Open the document first to trigger diagnostics.
        """
        self._ensure_initialized()
        self._open_document(file)

        abs_path = Path(file)
        if not abs_path.is_absolute():
            abs_path = self.project_path / file

        # Give server time to compute diagnostics
        time.sleep(0.5)

        return self.client.get_diagnostics(str(abs_path)) if self.client else []

    def shutdown(self):
        """Gracefully shutdown the language server."""
        # Close all open documents
        for uri in list(self._open_documents):
            if self.client:
                self.client.send_notification('textDocument/didClose', {
                    'textDocument': {'uri': uri},
                })
        self._open_documents.clear()

        # Shutdown client
        if self.client:
            self.client.shutdown()
            self.client = None

        self._initialized = False


# =============================================================================
# Language-Specific Adapters
# =============================================================================

class CSharpLSPAdapter(LSPAdapter):
    """
    Adapter for csharp-ls.

    This is the primary target for AgentForge since the user
    focuses on .NET development.

    Installation: dotnet tool install -g csharp-ls
    """

    SERVER_COMMAND = ["csharp-ls"]
    SERVER_NAME = "csharp-ls"
    INSTALL_INSTRUCTIONS = "dotnet tool install -g csharp-ls"
    LANGUAGE_ID = "csharp"
    FILE_EXTENSIONS = [".cs", ".csx"]

    def _get_initialization_options(self) -> dict:
        """csharp-ls specific options."""
        return {}

    def find_solution_or_project(self) -> Optional[str]:
        """Find .sln or .csproj file in project root."""
        # Prefer .sln files
        sln_files = list(self.project_path.glob("*.sln"))
        if sln_files:
            return str(sln_files[0])

        # Fall back to .csproj
        csproj_files = list(self.project_path.glob("**/*.csproj"))
        if csproj_files:
            return str(csproj_files[0])

        return None


class PyrightAdapter(LSPAdapter):
    """
    Adapter for pyright (Python).

    Installation: pip install pyright
    """

    SERVER_COMMAND = ["pyright-langserver", "--stdio"]
    SERVER_NAME = "pyright"
    INSTALL_INSTRUCTIONS = "pip install pyright"
    LANGUAGE_ID = "python"
    FILE_EXTENSIONS = [".py", ".pyi"]


class TypeScriptAdapter(LSPAdapter):
    """
    Adapter for typescript-language-server.

    Installation: npm install -g typescript-language-server typescript
    """

    SERVER_COMMAND = ["typescript-language-server", "--stdio"]
    SERVER_NAME = "typescript-language-server"
    INSTALL_INSTRUCTIONS = "npm install -g typescript-language-server typescript"
    LANGUAGE_ID = "typescript"
    FILE_EXTENSIONS = [".ts", ".tsx", ".js", ".jsx"]


# =============================================================================
# Factory Function
# =============================================================================

def get_adapter_for_project(project_path: str) -> LSPAdapter:
    """
    Get the appropriate LSP adapter for a project.

    Detects the primary language from project files.

    Args:
        project_path: Root directory of the project

    Returns:
        Appropriate LSPAdapter subclass instance
    """
    project = Path(project_path)

    # Check for .NET project
    if list(project.glob("*.sln")) or list(project.glob("**/*.csproj")):
        return CSharpLSPAdapter(project_path)

    # Check for Python project
    if (project / "pyproject.toml").exists() or \
       (project / "setup.py").exists() or \
       list(project.glob("**/*.py")):
        return PyrightAdapter(project_path)

    # Check for TypeScript/JavaScript project
    if (project / "package.json").exists() or \
       (project / "tsconfig.json").exists():
        return TypeScriptAdapter(project_path)

    # Default to C# (primary target)
    return CSharpLSPAdapter(project_path)


# =============================================================================
# CLI for Testing
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Test LSP adapter functionality",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get symbols in a file
  python lsp_adapter.py -p /path/to/project symbols src/Domain/Order.cs

  # Find definition
  python lsp_adapter.py -p /path/to/project definition src/App/Service.cs 45 12

  # Find references
  python lsp_adapter.py -p /path/to/project references src/Domain/Order.cs 10 18

  # Search workspace symbols
  python lsp_adapter.py -p /path/to/project search Order
"""
    )

    parser.add_argument("--project", "-p", required=True, help="Project root path")
    parser.add_argument("--language", "-l", choices=["csharp", "python", "typescript"],
                        help="Force specific language (auto-detect if not specified)")

    subparsers = parser.add_subparsers(dest="command", help="Command")

    # symbols command
    sym_parser = subparsers.add_parser("symbols", help="Get symbols in a file")
    sym_parser.add_argument("file", help="File path")

    # definition command
    def_parser = subparsers.add_parser("definition", help="Find definition")
    def_parser.add_argument("file", help="File path")
    def_parser.add_argument("line", type=int, help="Line number (1-based)")
    def_parser.add_argument("column", type=int, help="Column number (1-based)")

    # references command
    ref_parser = subparsers.add_parser("references", help="Find references")
    ref_parser.add_argument("file", help="File path")
    ref_parser.add_argument("line", type=int, help="Line number (1-based)")
    ref_parser.add_argument("column", type=int, help="Column number (1-based)")

    # hover command
    hover_parser = subparsers.add_parser("hover", help="Get hover info")
    hover_parser.add_argument("file", help="File path")
    hover_parser.add_argument("line", type=int, help="Line number (1-based)")
    hover_parser.add_argument("column", type=int, help="Column number (1-based)")

    # search command
    search_parser = subparsers.add_parser("search", help="Search workspace symbols")
    search_parser.add_argument("query", help="Search query")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Get appropriate adapter
    if args.language:
        adapters = {
            "csharp": CSharpLSPAdapter,
            "python": PyrightAdapter,
            "typescript": TypeScriptAdapter,
        }
        adapter = adapters[args.language](args.project)
    else:
        adapter = get_adapter_for_project(args.project)

    print(f"Using {adapter.SERVER_NAME} for {args.project}")

    try:
        print("Initializing LSP server...")
        adapter.initialize()
        print("Server initialized successfully")

        if args.command == "symbols":
            symbols = adapter.get_symbols(args.file)
            print(f"\nSymbols in {args.file} ({len(symbols)}):")
            for sym in symbols:
                indent = "  " if sym.container else ""
                print(f"{indent}{sym.kind}: {sym.name}")
                if sym.detail:
                    print(f"{indent}  {sym.detail}")
                for child in sym.children:
                    print(f"    {child.kind}: {child.name}")

        elif args.command == "definition":
            # Convert to 0-based
            loc = adapter.get_definition(args.file, args.line - 1, args.column - 1)
            if loc:
                print(f"\nDefinition: {loc}")
            else:
                print("\nNo definition found")

        elif args.command == "references":
            # Convert to 0-based
            refs = adapter.get_references(args.file, args.line - 1, args.column - 1)
            print(f"\nReferences ({len(refs)}):")
            for ref in refs:
                print(f"  {ref}")

        elif args.command == "hover":
            # Convert to 0-based
            info = adapter.get_hover(args.file, args.line - 1, args.column - 1)
            if info:
                print(f"\nHover info:\n{info.contents}")
            else:
                print("\nNo hover info")

        elif args.command == "search":
            symbols = adapter.get_workspace_symbols(args.query)
            print(f"\nWorkspace symbols matching '{args.query}' ({len(symbols)}):")
            for sym in symbols[:20]:
                print(f"  {sym.kind}: {sym.name}")
                print(f"    at {sym.location}")

    except LSPServerNotFound as e:
        print(f"\nError: {e}")
        return 1

    except LSPInitializationError as e:
        print(f"\nError: {e}")
        return 1

    finally:
        print("\nShutting down...")
        adapter.shutdown()

    return 0


if __name__ == "__main__":
    sys.exit(main())
