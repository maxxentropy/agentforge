#!/usr/bin/env python3
"""
LSP Client
==========

Low-level JSON-RPC 2.0 communication with language servers.

Extracted from lsp_adapter.py for modularity.
"""

import subprocess
import json
import threading
import queue
import os
import sys
from typing import Optional, List, Dict
from pathlib import Path

from .lsp_types import Diagnostic


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
# LSP Client
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
                header_line = self.process.stdout.readline()
                if not header_line:
                    break

                header = header_line.decode('utf-8').strip()
                if not header.startswith('Content-Length:'):
                    continue

                content_length = int(header.split(':')[1].strip())
                self.process.stdout.readline()  # blank line
                content = self.process.stdout.read(content_length).decode('utf-8')
                message = json.loads(content)
                self._handle_message(message)

            except Exception as e:
                if self._running:
                    print(f"LSP read error: {e}", file=sys.stderr)

    def _handle_message(self, message: dict):
        """Handle an incoming message from the server."""
        if 'id' in message and 'method' not in message:
            request_id = message['id']
            if request_id in self._pending_requests:
                self._pending_requests[request_id].put(message)

        elif 'method' in message:
            method = message['method']
            if method == 'textDocument/publishDiagnostics':
                params = message.get('params', {})
                uri = params.get('uri', '')
                diagnostics = params.get('diagnostics', [])
                file_path = self._uri_to_path(uri)
                self._diagnostics[file_path] = [
                    self._parse_diagnostic(d, file_path) for d in diagnostics
                ]

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
                self.send_request('shutdown', {}, timeout=5.0)
                self.send_notification('exit', {})
                self.process.wait(timeout=5.0)
            except Exception:
                self.process.kill()
            finally:
                self.process = None

        if self._reader_thread:
            self._reader_thread.join(timeout=2.0)
