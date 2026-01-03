# @spec_file: .agentforge/specs/core-harness-minimal-context-v1.yaml
# @spec_id: core-harness-minimal-context-v1
# @component_id: search-handlers
# @test_path: tests/unit/harness/tool_handlers/test_search_handlers.py

"""
Search Handlers
===============

Handlers for code search operations: search_code, load_context.

search_code supports both regex pattern search and semantic search
(when a vector index is available).

load_context loads additional file content into the agent's working memory.
"""

import fnmatch
import logging
import re
from pathlib import Path
from typing import Any

from .constants import (
    FIND_RELATED_MAX_FILES,
    SEARCH_DEFAULT_MAX_RESULTS,
    SEARCH_LINE_MAX_CHARS,
    WORKING_MEMORY_EXPIRY_STEPS,
    WORKING_MEMORY_MAX_CONTENT_SIZE,
)
from .types import ActionHandler

logger = logging.getLogger(__name__)

# Default file patterns
INCLUDE_PATTERNS = ["*.py", "*.ts", "*.js", "*.cs", "*.java", "*.go", "*.rs"]
EXCLUDE_PATTERNS = [
    "**/node_modules/**",
    "**/.git/**",
    "**/bin/**",
    "**/obj/**",
    "**/__pycache__/**",
    "**/.venv/**",
    "**/venv/**",
    "**/.mypy_cache/**",
    "**/.pytest_cache/**",
]


def _should_exclude(path: Path, base_path: Path) -> bool:
    """Check if a path should be excluded from search."""
    try:
        path_str = str(path.relative_to(base_path))
    except ValueError:
        return True
    return any(fnmatch.fnmatch(path_str, exc) for exc in EXCLUDE_PATTERNS)


def _get_search_files(base_path: Path, file_pattern: str | None) -> list[Path]:
    """Get list of files to search, applying patterns and exclusions."""
    if file_pattern:
        files = list(base_path.glob(file_pattern))
    else:
        files = []
        for inc in INCLUDE_PATTERNS:
            files.extend(base_path.rglob(inc))
    return [f for f in files if f.is_file() and not _should_exclude(f, base_path)]


def _search_file(
    file_path: Path, regex: re.Pattern, base_path: Path, max_results: int, results: list
) -> None:
    """Search a single file and append matches to results."""
    try:
        content = file_path.read_text(errors="ignore")
        for line_num, line in enumerate(content.splitlines(), 1):
            if regex.search(line):
                rel_path = str(file_path.relative_to(base_path))
                results.append((rel_path, line_num, line.strip()[:SEARCH_LINE_MAX_CHARS]))
                if len(results) >= max_results:
                    return
    except Exception:
        pass  # Skip unreadable files


def _format_search_results(results: list, pattern: str, max_results: int) -> str:
    """Format search results as a string."""
    if not results:
        return f"No matches found for pattern: {pattern}"
    output = [f"Found {len(results)} matches for '{pattern}':\n"]
    for file_path, line_num, line_text in results:
        output.append(f"  {file_path}:{line_num}: {line_text}")
    if len(results) == max_results:
        output.append(f"\n  (limited to {max_results} results)")
    return "\n".join(output)


def _regex_search(
    base_path: Path, pattern: str, file_pattern: str | None, max_results: int
) -> str:
    """Grep-style regex search."""
    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        return f"ERROR: Invalid regex pattern: {e}"

    results: list[tuple[str, int, str]] = []
    files = _get_search_files(base_path, file_pattern)

    for file_path in sorted(files):
        if len(results) >= max_results:
            break
        _search_file(file_path, regex, base_path, max_results, results)

    return _format_search_results(results, pattern, max_results)


def _semantic_search(base_path: Path, query: str, max_results: int) -> str:
    """Vector-based semantic search."""
    try:
        from agentforge.tools.vector_search import VectorSearch
    except ImportError:
        return "ERROR: Vector search not available. Use search_type='regex' for pattern matching."

    try:
        vs = VectorSearch(str(base_path))
        if not vs.is_indexed():
            return (
                "Semantic search requires an index. The index is not available.\n"
                "Falling back to regex search.\nConsider running 'agentforge index' first."
            )

        results = vs.search(query, top_k=max_results)
        if not results:
            return f"No semantic matches found for: {query}"

        output = [f"Found {len(results)} semantic matches for '{query}':\n"]
        for r in results:
            score_pct = int(r.score * 100)
            output.append(f"  {r.file_path}:{r.start_line}-{r.end_line} ({score_pct}% match)")
            snippet = r.chunk[:150].replace("\n", " ")
            output.append(f"    {snippet}...")
        return "\n".join(output)
    except Exception as e:
        return f"ERROR: Semantic search failed: {e}"


def create_search_code_handler(project_path: Path | None = None) -> ActionHandler:
    """Create a search_code action handler."""
    base_path = Path(project_path) if project_path else Path.cwd()

    def handler(params: dict[str, Any]) -> str:
        pattern = params.get("pattern", "")
        file_pattern = params.get("file_pattern")
        max_results = params.get("max_results", SEARCH_DEFAULT_MAX_RESULTS)
        search_type = params.get("search_type", "regex")
        logger.debug("search_code: pattern=%s, type=%s", pattern, search_type)

        if not pattern:
            return "ERROR: pattern parameter required"

        try:
            if search_type == "semantic":
                return _semantic_search(base_path, pattern, max_results)
            return _regex_search(base_path, pattern, file_pattern, max_results)
        except Exception as e:
            return f"ERROR: Search failed: {e}"

    return handler


def create_load_context_handler(project_path: Path | None = None) -> ActionHandler:
    """
    Create a load_context action handler.

    Loads additional file content into working memory for the agent to access.

    Args:
        project_path: Project root path

    Returns:
        Handler function: (params: Dict[str, Any]) -> str
    """
    base_path = Path(project_path) if project_path else Path.cwd()

    def handler(params: dict[str, Any]) -> str:
        # Support multiple parameter formats
        item = params.get("item", "")
        path = params.get("path") or params.get("file_path") or params.get("file")
        logger.debug("load_context: item=%s, path=%s", item, path)

        # If path provided directly, treat as file load
        if path:
            item = f"full_file:{path}"

        # If no item specified, provide help
        if not item:
            query = params.get("query", "")
            if query:
                return (
                    "ERROR: Use 'read_file' action to read files, not 'load_context'. "
                    "Try: read_file with path parameter."
                )
            return (
                "ERROR: Missing item or path parameter. "
                "Use 'item=full_file:path/to/file.py' or 'path=path/to/file.py'"
            )

        if item.startswith("full_file:"):
            file_path = item[10:]
            full_path = Path(file_path)
            if not full_path.is_absolute():
                full_path = base_path / file_path

            if not full_path.exists():
                return f"ERROR: File not found: {file_path}"

            if not full_path.is_file():
                return f"ERROR: Not a file: {file_path}"

            try:
                content = full_path.read_text()

                # Get context from params for working memory integration
                context = params.get("_context", {})
                task_id = context.get("task_id")
                current_step = context.get("current_step", 0)

                # Try to store in working memory if we have context
                if task_id:
                    try:
                        from ..state_store import TaskStateStore
                        from ..working_memory import WorkingMemoryManager

                        state_store = TaskStateStore(base_path)
                        task_dir = state_store._task_dir(task_id)
                        memory = WorkingMemoryManager(task_dir)
                        memory.load_context(
                            item,
                            content[:WORKING_MEMORY_MAX_CONTENT_SIZE],
                            current_step,
                            expires_after_steps=WORKING_MEMORY_EXPIRY_STEPS,
                        )
                    except Exception:
                        pass  # Non-critical if working memory integration fails

                return (
                    f"SUCCESS: Loaded {file_path} into context\n"
                    f"  Size: {len(content)} chars\n"
                    f"  Available for next 3 steps"
                )

            except Exception as e:
                return f"ERROR: Failed to load context: {e}"

        # Unknown format
        return (
            f"ERROR: Unknown context item format: {item}\n"
            "Use 'full_file:path/to/file.py' or provide 'path' parameter"
        )

    return handler


def _get_relative_path(path: Path, base_path: Path) -> str:
    """Get relative path, falling back to absolute if not relative to base."""
    try:
        return str(path.relative_to(base_path))
    except ValueError:
        return str(path)


def _find_same_dir_files(
    full_path: Path, base_path: Path, related: list[tuple[str, str]]
) -> None:
    """Find sibling files in the same directory."""
    siblings = [
        f for f in full_path.parent.iterdir()
        if f.is_file() and f != full_path and f.suffix == full_path.suffix
    ]
    for sibling in siblings[:5]:
        related.append(("same_dir", _get_relative_path(sibling, base_path)))


def _find_test_files(
    full_path: Path, base_path: Path, related: list[tuple[str, str]]
) -> None:
    """Find related test files using naming conventions."""
    if full_path.suffix != ".py":
        return
    stem = full_path.stem
    test_patterns = [
        f"test_{stem}.py",
        f"{stem}_test.py",
        f"tests/test_{stem}.py",
        f"tests/unit/test_{stem}.py",
    ]
    for pattern in test_patterns:
        test_file = base_path / pattern
        if test_file.exists():
            related.append(("test", _get_relative_path(test_file, base_path)))


def _find_import_files(
    full_path: Path, base_path: Path, related: list[tuple[str, str]]
) -> None:
    """Find files imported by this Python file."""
    if full_path.suffix != ".py":
        return
    try:
        import ast
        content = full_path.read_text()
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                module_path = node.module.replace(".", "/") + ".py"
                import_file = base_path / module_path
                if import_file.exists():
                    related.append(("imports", module_path))
    except Exception:
        pass


def create_find_related_handler(project_path: Path | None = None) -> ActionHandler:
    """Create a find_related action handler."""
    base_path = Path(project_path) if project_path else Path.cwd()

    def handler(params: dict[str, Any]) -> str:
        path = params.get("path") or params.get("file_path")
        relation_type = params.get("type", "all")
        logger.debug("find_related: path=%s, type=%s", path, relation_type)

        if not path:
            return "ERROR: path parameter required"

        full_path = Path(path) if Path(path).is_absolute() else base_path / path
        if not full_path.exists():
            return f"ERROR: File not found: {path}"

        related: list[tuple[str, str]] = []

        if relation_type in ("same_dir", "all"):
            _find_same_dir_files(full_path, base_path, related)

        if relation_type in ("tests", "all"):
            _find_test_files(full_path, base_path, related)

        if relation_type in ("imports", "all"):
            _find_import_files(full_path, base_path, related)

        if not related:
            return f"No related files found for: {path}"

        output = [f"Related files for {path}:\n"]
        for rel_type, rel_path in related[:FIND_RELATED_MAX_FILES]:
            output.append(f"  [{rel_type}] {rel_path}")
        return "\n".join(output)

    return handler
