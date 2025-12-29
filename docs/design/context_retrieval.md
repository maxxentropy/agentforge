# Context Retrieval Architecture
## Hybrid LSP + Vector Search System

## 1. Overview

The Context Retrieval Engine provides intelligent code retrieval by combining:
- **Structural Analysis (via LSP):** Precise, compiler-accurate code relationships
- **Semantic Search (via Embeddings):** Conceptual similarity across code and documentation

Neither alone is sufficient. Together they provide comprehensive retrieval.

## 2. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CONTEXT RETRIEVAL ENGINE                             │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      INDEXING PIPELINE                               │   │
│  │                      (Background Process)                            │   │
│  │                                                                      │   │
│  │   Source Files ──┬──> LSP Analysis ──> Structure Index (SQLite)     │   │
│  │                  │                                                   │   │
│  │                  └──> Chunker ──> Embedder ──> Vector Index (HNSW)  │   │
│  │                                                                      │   │
│  │   File Watcher ──> Incremental Updates                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      RETRIEVAL PIPELINE                              │   │
│  │                      (On-Demand)                                     │   │
│  │                                                                      │   │
│  │   Query ──┬──> Entity Extractor ──> LSP Queries ──> Structural      │   │
│  │           │                                         Candidates       │   │
│  │           │                                              │           │   │
│  │           └──> Query Embedder ──> Vector Search ──> Semantic        │   │
│  │                                                    Candidates        │   │
│  │                                                          │           │   │
│  │                                                          ▼           │   │
│  │                                              ┌─────────────────┐     │   │
│  │                                              │  Fusion Ranker  │     │   │
│  │                                              │  + Budget Mgr   │     │   │
│  │                                              └─────────────────┘     │   │
│  │                                                          │           │   │
│  │                                                          ▼           │   │
│  │                                              Ranked Context Chunks   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 3. LSP Adapter Layer

### 3.1 Supported Language Servers

| Language | LSP Implementation | Plugin Name |
|----------|-------------------|-------------|
| C# | OmniSharp/Roslyn | csharp-lsp |
| Python | Pyright | pyright-lsp |
| C/C++ | clangd | clangd-lsp |
| TypeScript | tsserver | (future) |
| Go | gopls | (future) |

### 3.2 LSP Operations Used

```yaml
operations:
  # Find all symbols (classes, methods, etc.) in a file
  document_symbols:
    method: "textDocument/documentSymbol"
    use_case: "Index file structure"
    
  # Find where a symbol is defined
  definition:
    method: "textDocument/definition"  
    use_case: "Trace to source"
    
  # Find all places a symbol is used
  references:
    method: "textDocument/references"
    use_case: "Find dependents (what uses this?)"
    
  # Get type and documentation info
  hover:
    method: "textDocument/hover"
    use_case: "Extract type info, docstrings"
    
  # Get compilation errors without full build
  diagnostics:
    method: "textDocument/publishDiagnostics"
    use_case: "Quick verification"
    
  # Search symbols across entire workspace
  workspace_symbols:
    method: "workspace/symbol"
    use_case: "Find symbols by name"
```

### 3.3 Unified LSP Client Interface

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Symbol:
    name: str
    qualified_name: str
    kind: str  # class, interface, method, property, function
    file_path: str
    start_line: int
    end_line: int
    signature: Optional[str] = None
    docstring: Optional[str] = None

@dataclass
class Reference:
    symbol: Symbol
    file_path: str
    line: int
    context: str  # The line of code

@dataclass
class Dependency:
    from_symbol: Symbol
    to_symbol: Symbol
    dependency_type: str  # inherits, implements, calls, uses

class LSPAdapter(ABC):
    """Abstract interface for language server adapters."""
    
    @abstractmethod
    async def initialize(self, workspace_path: str) -> None:
        """Start the language server for a workspace."""
        pass
    
    @abstractmethod
    async def get_document_symbols(self, file_path: str) -> List[Symbol]:
        """Get all symbols defined in a file."""
        pass
    
    @abstractmethod
    async def find_definition(self, file_path: str, line: int, column: int) -> Optional[Symbol]:
        """Find where a symbol at position is defined."""
        pass
    
    @abstractmethod
    async def find_references(self, symbol: Symbol) -> List[Reference]:
        """Find all references to a symbol."""
        pass
    
    @abstractmethod
    async def get_hover_info(self, file_path: str, line: int, column: int) -> Optional[str]:
        """Get hover information (type, docs) at position."""
        pass
    
    @abstractmethod
    async def search_workspace_symbols(self, query: str) -> List[Symbol]:
        """Search for symbols by name across workspace."""
        pass
    
    @abstractmethod
    async def get_diagnostics(self, file_path: str) -> List[dict]:
        """Get compilation diagnostics for a file."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Stop the language server."""
        pass
```

### 3.4 LSP Adapter Registry

```python
class LSPRegistry:
    """Registry of language server adapters."""
    
    adapters: dict[str, type[LSPAdapter]] = {}
    
    @classmethod
    def register(cls, language: str, adapter_class: type[LSPAdapter]):
        cls.adapters[language] = adapter_class
    
    @classmethod
    def get_adapter(cls, language: str) -> LSPAdapter:
        if language not in cls.adapters:
            raise ValueError(f"No LSP adapter for language: {language}")
        return cls.adapters[language]()
    
    @classmethod
    def detect_language(cls, file_path: str) -> str:
        """Detect language from file extension."""
        extension_map = {
            '.cs': 'csharp',
            '.py': 'python',
            '.c': 'c',
            '.cpp': 'cpp',
            '.h': 'c',
            '.hpp': 'cpp',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.js': 'javascript',
            '.go': 'go',
        }
        ext = Path(file_path).suffix.lower()
        return extension_map.get(ext, 'unknown')
```

## 4. Structure Index (SQLite Cache)

### 4.1 Schema

```sql
-- Track indexed files
CREATE TABLE files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE NOT NULL,
    language TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    last_indexed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    line_count INTEGER
);

CREATE INDEX idx_files_path ON files(path);
CREATE INDEX idx_files_language ON files(language);

-- Store symbols discovered via LSP
CREATE TABLE symbols (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    qualified_name TEXT NOT NULL,
    kind TEXT NOT NULL,  -- class, interface, method, property, function, etc.
    visibility TEXT,     -- public, private, protected, internal
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    signature TEXT,      -- For methods: return type + params
    docstring TEXT,
    
    UNIQUE(file_id, qualified_name)
);

CREATE INDEX idx_symbols_name ON symbols(name);
CREATE INDEX idx_symbols_qualified ON symbols(qualified_name);
CREATE INDEX idx_symbols_kind ON symbols(kind);
CREATE INDEX idx_symbols_file ON symbols(file_id);

-- Store relationships between symbols
CREATE TABLE dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_symbol_id INTEGER NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    to_symbol_id INTEGER NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    dependency_type TEXT NOT NULL,  -- inherits, implements, calls, uses, imports
    
    UNIQUE(from_symbol_id, to_symbol_id, dependency_type)
);

CREATE INDEX idx_deps_from ON dependencies(from_symbol_id);
CREATE INDEX idx_deps_to ON dependencies(to_symbol_id);
CREATE INDEX idx_deps_type ON dependencies(dependency_type);

-- Store where symbols are referenced
CREATE TABLE symbol_references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol_id INTEGER NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    referencing_file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    line_number INTEGER NOT NULL,
    context TEXT  -- The line of code containing the reference
);

CREATE INDEX idx_refs_symbol ON symbol_references(symbol_id);
CREATE INDEX idx_refs_file ON symbol_references(referencing_file_id);
```

### 4.2 Query Examples

```python
class StructureIndex:
    """Query interface for the structure index."""
    
    def find_symbol(self, name: str, kind: str = None) -> List[Symbol]:
        """Find symbols by name, optionally filtered by kind."""
        query = """
            SELECT s.*, f.path as file_path
            FROM symbols s
            JOIN files f ON s.file_id = f.id
            WHERE s.name = ? OR s.qualified_name LIKE ?
        """
        params = [name, f"%{name}%"]
        if kind:
            query += " AND s.kind = ?"
            params.append(kind)
        return self._execute(query, params)
    
    def get_dependencies(self, symbol_id: int, depth: int = 1) -> List[Dependency]:
        """Get what this symbol depends on (what it uses)."""
        # Recursive CTE for multi-level dependencies
        query = """
            WITH RECURSIVE deps AS (
                SELECT from_symbol_id, to_symbol_id, dependency_type, 1 as depth
                FROM dependencies WHERE from_symbol_id = ?
                
                UNION ALL
                
                SELECT d.from_symbol_id, d.to_symbol_id, d.dependency_type, deps.depth + 1
                FROM dependencies d
                JOIN deps ON d.from_symbol_id = deps.to_symbol_id
                WHERE deps.depth < ?
            )
            SELECT DISTINCT * FROM deps
        """
        return self._execute(query, [symbol_id, depth])
    
    def get_dependents(self, symbol_id: int, depth: int = 1) -> List[Dependency]:
        """Get what depends on this symbol (what uses it)."""
        # Reverse direction
        query = """
            WITH RECURSIVE deps AS (
                SELECT from_symbol_id, to_symbol_id, dependency_type, 1 as depth
                FROM dependencies WHERE to_symbol_id = ?
                
                UNION ALL
                
                SELECT d.from_symbol_id, d.to_symbol_id, d.dependency_type, deps.depth + 1
                FROM dependencies d
                JOIN deps ON d.to_symbol_id = deps.from_symbol_id
                WHERE deps.depth < ?
            )
            SELECT DISTINCT * FROM deps
        """
        return self._execute(query, [symbol_id, depth])
    
    def find_tests_for_symbol(self, symbol_id: int) -> List[Symbol]:
        """Find test methods/classes that reference this symbol."""
        query = """
            SELECT s.*, f.path as file_path
            FROM symbols s
            JOIN files f ON s.file_id = f.id
            JOIN symbol_references r ON r.referencing_file_id = f.id
            WHERE r.symbol_id = ?
            AND (f.path LIKE '%test%' OR f.path LIKE '%Test%' OR s.name LIKE '%Test%')
        """
        return self._execute(query, [symbol_id])
```

## 5. Vector Index

### 5.1 Configuration

```yaml
vector_index:
  engine: hnswlib
  
  embedding:
    model: text-embedding-3-small  # OpenAI
    dimensions: 1536
    # Alternative: local model
    # model: sentence-transformers/all-MiniLM-L6-v2
    # dimensions: 384
  
  index_params:
    space: cosine
    ef_construction: 200
    M: 16
    ef_search: 100
  
  chunking:
    strategy: symbol_based
    max_chunk_tokens: 500
    include_context: true
    
  storage:
    path: ".agentforge/vector_index/"
    auto_save: true
```

### 5.2 Chunking Strategy

```python
@dataclass
class CodeChunk:
    id: str
    file_path: str
    symbol_id: Optional[int]  # Link to structure index
    chunk_type: str  # symbol, documentation, comment
    content: str
    token_count: int
    start_line: int
    end_line: int
    metadata: dict

class SymbolBasedChunker:
    """Create one chunk per symbol (class, method, function)."""
    
    def chunk_file(self, file_path: str, symbols: List[Symbol]) -> List[CodeChunk]:
        content = Path(file_path).read_text()
        lines = content.splitlines()
        chunks = []
        
        for symbol in symbols:
            # Extract symbol content
            symbol_lines = lines[symbol.start_line - 1:symbol.end_line]
            symbol_content = '\n'.join(symbol_lines)
            
            # Add metadata header for embedding
            metadata_header = f"""
Language: {self.detect_language(file_path)}
File: {file_path}
Type: {symbol.kind}
Name: {symbol.qualified_name}
---
"""
            
            full_content = metadata_header + symbol_content
            
            # Check token count
            tokens = self.count_tokens(full_content)
            if tokens > self.max_tokens:
                # Split large symbols (e.g., large classes)
                chunks.extend(self._split_large_symbol(symbol, symbol_content))
            else:
                chunks.append(CodeChunk(
                    id=f"{file_path}:{symbol.qualified_name}",
                    file_path=file_path,
                    symbol_id=symbol.id,
                    chunk_type='symbol',
                    content=full_content,
                    token_count=tokens,
                    start_line=symbol.start_line,
                    end_line=symbol.end_line,
                    metadata={'kind': symbol.kind, 'name': symbol.name}
                ))
        
        return chunks
```

## 6. Fusion Retrieval Pipeline

### 6.1 Query Processing

```python
@dataclass
class ProcessedQuery:
    original: str
    entities: List[Entity]
    expanded_queries: List[str]
    intent: str

class QueryProcessor:
    """Process natural language queries for retrieval."""
    
    async def process(self, query: str) -> ProcessedQuery:
        # Use LLM to extract entities and understand intent
        prompt = f"""
Analyze this query for code retrieval:
"{query}"

Extract:
1. Named entities (likely class names, method names, concepts)
2. The intent (what kind of code is being requested)
3. 2-3 alternative phrasings for semantic search

Output JSON:
{{
  "entities": [{{"name": "...", "type": "class|method|concept", "confidence": 0.9}}],
  "intent": "...",
  "alternatives": ["...", "..."]
}}
"""
        response = await self.llm.complete(prompt)
        parsed = json.loads(response)
        
        return ProcessedQuery(
            original=query,
            entities=[Entity(**e) for e in parsed['entities']],
            expanded_queries=[query] + parsed['alternatives'],
            intent=parsed['intent']
        )
```

### 6.2 Parallel Retrieval

```python
class HybridRetriever:
    """Combine LSP structural and vector semantic retrieval."""
    
    def __init__(
        self,
        structure_index: StructureIndex,
        vector_index: VectorIndex,
        lsp_adapters: dict[str, LSPAdapter]
    ):
        self.structure = structure_index
        self.vectors = vector_index
        self.lsp = lsp_adapters
    
    async def retrieve(
        self,
        query: str,
        budget_tokens: int = 4000
    ) -> List[CodeChunk]:
        # Step 1: Process query
        processed = await self.query_processor.process(query)
        
        # Step 2: Parallel retrieval
        structural_task = asyncio.create_task(
            self._structural_retrieval(processed)
        )
        semantic_task = asyncio.create_task(
            self._semantic_retrieval(processed)
        )
        
        structural_candidates = await structural_task
        semantic_candidates = await semantic_task
        
        # Step 3: Fusion ranking
        fused = self._fusion_rank(structural_candidates, semantic_candidates)
        
        # Step 4: Budget management
        selected = self._select_within_budget(fused, budget_tokens)
        
        return selected
    
    async def _structural_retrieval(
        self,
        processed: ProcessedQuery
    ) -> List[Candidate]:
        candidates = []
        
        for entity in processed.entities:
            # Find symbols matching entity
            symbols = self.structure.find_symbol(
                entity.name,
                kind='class' if entity.type == 'class' else None
            )
            
            for symbol in symbols:
                candidates.append(Candidate(
                    source='lsp_direct',
                    symbol=symbol,
                    score=entity.confidence
                ))
                
                # Get dependencies
                deps = self.structure.get_dependencies(symbol.id, depth=1)
                for dep in deps:
                    candidates.append(Candidate(
                        source='lsp_dependency',
                        symbol=dep.to_symbol,
                        score=entity.confidence * 0.8
                    ))
                
                # Get tests
                tests = self.structure.find_tests_for_symbol(symbol.id)
                for test in tests:
                    candidates.append(Candidate(
                        source='lsp_test',
                        symbol=test,
                        score=entity.confidence * 0.7
                    ))
        
        return candidates
    
    async def _semantic_retrieval(
        self,
        processed: ProcessedQuery
    ) -> List[Candidate]:
        candidates = []
        
        for query in processed.expanded_queries:
            results = self.vectors.search(query, top_k=20)
            for result in results:
                candidates.append(Candidate(
                    source='vector',
                    chunk=result.chunk,
                    score=result.similarity
                ))
        
        return candidates
```

### 6.3 Fusion Ranking (Reciprocal Rank Fusion)

```python
def _fusion_rank(
    self,
    structural: List[Candidate],
    semantic: List[Candidate],
    k: int = 60
) -> List[Candidate]:
    """
    Reciprocal Rank Fusion (RRF) to combine rankings.
    
    RRF score = Σ 1/(k + rank_i) for each list
    """
    # Deduplicate by content
    all_candidates = {}
    
    # Score structural candidates
    for rank, candidate in enumerate(sorted(structural, key=lambda c: -c.score)):
        key = self._candidate_key(candidate)
        if key not in all_candidates:
            all_candidates[key] = {'candidate': candidate, 'rrf_score': 0}
        all_candidates[key]['rrf_score'] += 1 / (k + rank)
    
    # Score semantic candidates
    for rank, candidate in enumerate(sorted(semantic, key=lambda c: -c.score)):
        key = self._candidate_key(candidate)
        if key not in all_candidates:
            all_candidates[key] = {'candidate': candidate, 'rrf_score': 0}
        all_candidates[key]['rrf_score'] += 1 / (k + rank)
    
    # Sort by fused score
    ranked = sorted(
        all_candidates.values(),
        key=lambda x: -x['rrf_score']
    )
    
    return [item['candidate'] for item in ranked]
```

### 6.4 Budget Management

```python
def _select_within_budget(
    self,
    ranked: List[Candidate],
    budget_tokens: int
) -> List[CodeChunk]:
    """Select top candidates within token budget."""
    selected = []
    remaining = budget_tokens
    
    # Reserve space for essentials
    reserved = {
        'project_context': 500,
        'task_context': 200,
        'buffer': 300
    }
    available = remaining - sum(reserved.values())
    
    # Track diversity
    seen_files = set()
    
    for candidate in ranked:
        chunk = self._get_chunk(candidate)
        
        if chunk.token_count > available:
            continue
        
        # Diversity penalty
        diversity_factor = 1.0
        if chunk.file_path in seen_files:
            diversity_factor = 0.7
        
        # Accept if above threshold
        if candidate.score * diversity_factor > 0.3:
            selected.append(chunk)
            available -= chunk.token_count
            seen_files.add(chunk.file_path)
        
        if available < 100:
            break
    
    return selected
```

## 7. Indexing Pipeline

### 7.1 Initial Indexing

```python
class IndexingPipeline:
    """Index a project for retrieval."""
    
    async def index_project(self, project_path: str):
        """Full project indexing."""
        
        # Discover files
        files = self._discover_files(project_path)
        
        # Group by language
        by_language = defaultdict(list)
        for file in files:
            lang = LSPRegistry.detect_language(file)
            by_language[lang].append(file)
        
        # Index each language group
        for language, lang_files in by_language.items():
            if language == 'unknown':
                continue
            
            # Get LSP adapter
            adapter = LSPRegistry.get_adapter(language)
            await adapter.initialize(project_path)
            
            try:
                # Extract structure via LSP
                for file in lang_files:
                    await self._index_file_structure(file, adapter)
                
                # Resolve cross-file dependencies
                await self._resolve_dependencies(adapter)
                
            finally:
                await adapter.shutdown()
        
        # Build vector index
        await self._build_vector_index()
    
    async def _index_file_structure(self, file_path: str, adapter: LSPAdapter):
        """Extract and store symbols from a file."""
        # Get symbols from LSP
        symbols = await adapter.get_document_symbols(file_path)
        
        # Store in structure index
        file_id = self.structure.upsert_file(file_path)
        for symbol in symbols:
            self.structure.upsert_symbol(file_id, symbol)
    
    async def _resolve_dependencies(self, adapter: LSPAdapter):
        """Build dependency graph using LSP references."""
        for symbol in self.structure.get_all_symbols():
            # Find what this symbol references
            refs = await adapter.find_references(symbol)
            for ref in refs:
                # Find the symbol being referenced
                target = await adapter.find_definition(
                    ref.file_path, ref.line, 0
                )
                if target:
                    self.structure.add_dependency(
                        from_id=symbol.id,
                        to_id=target.id,
                        dep_type=self._classify_dependency(symbol, target)
                    )
```

### 7.2 Incremental Updates

```python
class IncrementalIndexer:
    """Keep index up to date with file changes."""
    
    def __init__(self, pipeline: IndexingPipeline):
        self.pipeline = pipeline
        self.observer = Observer()
    
    def start_watching(self, project_path: str):
        """Start watching for file changes."""
        handler = FileChangeHandler(self)
        self.observer.schedule(handler, project_path, recursive=True)
        self.observer.start()
    
    async def on_file_changed(self, file_path: str):
        """Handle file modification."""
        # Check if content actually changed
        current_hash = self._hash_file(file_path)
        stored_hash = self.pipeline.structure.get_file_hash(file_path)
        
        if current_hash == stored_hash:
            return
        
        # Re-index file
        language = LSPRegistry.detect_language(file_path)
        adapter = LSPRegistry.get_adapter(language)
        
        await self.pipeline._index_file_structure(file_path, adapter)
        await self.pipeline._update_vector_chunks(file_path)
    
    async def on_file_deleted(self, file_path: str):
        """Handle file deletion."""
        self.pipeline.structure.delete_file(file_path)
        self.pipeline.vectors.delete_chunks_for_file(file_path)
    
    async def on_file_created(self, file_path: str):
        """Handle new file."""
        await self.on_file_changed(file_path)
```

## 8. Usage Example

```python
# Initialize retrieval engine
engine = ContextRetrievalEngine(
    project_path="/path/to/project",
    config=RetrievalConfig(
        embedding_model="text-embedding-3-small",
        lsp_adapters=["csharp-lsp", "pyright-lsp"]
    )
)

# Index project (first time or refresh)
await engine.index()

# Retrieve context for a query
context = await engine.retrieve(
    query="Add discount calculation to orders",
    budget_tokens=4000
)

# Context is a list of CodeChunk objects
for chunk in context:
    print(f"{chunk.file_path}:{chunk.start_line}-{chunk.end_line}")
    print(f"  Type: {chunk.chunk_type}")
    print(f"  Tokens: {chunk.token_count}")
```
