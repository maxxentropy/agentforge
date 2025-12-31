# Revised Implementation Plan

## Priority Change: Build LLM Generation First

The original plan assumed TDFLOW generates code. It doesn't. We need to fix that first.

```
ORIGINAL PLAN (FLAWED):
  Phase 1-7: Build Agent Harness components using TDFLOW
  Problem: TDFLOW doesn't generate code, humans do

REVISED PLAN:
  Phase 0: Build LLM Generation component (makes TDFLOW useful)
  Phase 1-7: Build Agent Harness using now-functional TDFLOW
```

---

## New Phase 0: LLM Generation Component

**Duration:** 1-2 weeks  
**Dependency:** None  
**Output:** AgentForge can generate real code

### What We're Building

```
tools/generate/
├── __init__.py
├── domain.py          # GenerationResult, GeneratedFile, etc.
├── provider.py        # Claude API integration
├── prompt_builder.py  # Context → Prompt assembly
├── parser.py          # Response → Code extraction
├── writer.py          # Write files to disk
└── engine.py          # Main orchestration

cli/click_commands/generate.py  # CLI commands
tests/unit/tools/generate/      # Tests
```

### Implementation Steps

Since we don't have LLM generation yet, we'll build this component manually with Claude Code (bootstrapping).

---

## Step 0.1: Create Directory Structure

Tell Claude Code:

```
Create the directory structure for the LLM generation component:

mkdir -p tools/generate
mkdir -p tests/unit/tools/generate
touch tools/generate/__init__.py
touch tests/unit/tools/generate/__init__.py

Also create the configuration file:
.agentforge/generation.yaml with defaults for Claude API
```

---

## Step 0.2: Domain Entities

Tell Claude Code:

```
Create tools/generate/domain.py with these entities:

1. GeneratedFile (dataclass):
   - path: Path
   - content: str  
   - action: Literal["create", "modify", "delete"]
   - original_content: Optional[str]

2. GenerationResult (dataclass):
   - success: bool
   - files: list[GeneratedFile]
   - explanation: str
   - tokens_used: int
   - model: str
   - prompt_tokens: int
   - completion_tokens: int
   - error: Optional[str]

3. GenerationContext (dataclass):
   - spec: dict (the specification)
   - phase: Literal["red", "green", "refactor"]
   - mode: Literal["full", "incremental", "fix"]
   - patterns: dict
   - examples: list[dict]
   - error_context: Optional[dict]

4. Exceptions:
   - GenerationError (base)
   - APIError
   - ParseError

Follow patterns from tools/spec/domain.py and tools/tdflow/domain.py.
Write tests in tests/unit/tools/generate/test_domain.py.
```

---

## Step 0.3: LLM Provider Abstraction

Tell Claude Code:

```
Create tools/generate/provider.py with:

1. Abstract base class LLMProvider:
   - async generate(prompt: str, max_tokens: int) -> str
   - count_tokens(text: str) -> int

2. ClaudeProvider(LLMProvider):
   - Uses anthropic library
   - Reads API key from ANTHROPIC_API_KEY env var
   - Supports model selection
   - Implements retry with exponential backoff
   - Tracks token usage

3. ManualProvider(LLMProvider):
   - Fallback when no API key
   - Prints prompt to stdout
   - Reads response from stdin
   - Allows workflow to continue manually

Include in __init__:
   def get_provider() -> LLMProvider:
       # Returns ClaudeProvider if API key exists, else ManualProvider

Add anthropic to requirements.txt if not present.
Write tests using mocks (don't call real API in tests).
```

---

## Step 0.4: Prompt Builder

Tell Claude Code:

```
Create tools/generate/prompt_builder.py with:

class PromptBuilder:
    def build(self, context: GenerationContext) -> str:
        """Assemble prompt from context."""

The prompt should use XML structure:

<context>
  <specification>{yaml dump of spec}</specification>
  <phase>{phase name}</phase>
  <phase_instructions>{instructions for this phase}</phase_instructions>
  <patterns>{discovered patterns}</patterns>
  <examples>{code examples from project}</examples>
  <error_context>{if fixing an error}</error_context>
</context>

<instructions>
Generate {phase} code following the specification.
Output format: Use ```python:path/to/file.py markers
</instructions>

Phase-specific instructions:
- RED: Generate pytest tests that FAIL (no implementation)
- GREEN: Generate minimal implementation to PASS tests
- REFACTOR: Improve code without changing behavior

Use tools/context_assembler.py for loading project context.
Write tests with sample specs and expected prompt structure.
```

---

## Step 0.5: Response Parser

Tell Claude Code:

```
Create tools/generate/parser.py with:

class ResponseParser:
    FILE_PATTERN = re.compile(r'```python:(.+?)\n(.*?)```', re.DOTALL)
    
    def parse(self, response: str) -> list[GeneratedFile]:
        """Extract code files from LLM response."""

Requirements:
1. Extract file path from ```python:path/to/file.py marker
2. Extract content until closing ```
3. Validate Python syntax with ast.parse()
4. Handle multiple files in one response
5. Raise ParseError if no files found or invalid syntax

Also add:
    def extract_explanation(self, response: str) -> str:
        """Extract non-code explanation text."""

Write comprehensive tests with sample LLM responses.
```

---

## Step 0.6: Code Writer

Tell Claude Code:

```
Create tools/generate/writer.py with:

class CodeWriter:
    def write(self, files: list[GeneratedFile]) -> None:
        """Write generated files to disk."""

Requirements:
1. Create parent directories if needed
2. Backup existing files before overwriting
3. Add header comment to generated files:
   # Generated by AgentForge
   # Spec: {spec_name}
   # Phase: {phase}
   # Date: {timestamp}
4. Track all changes for potential rollback
5. Atomic writes (write to temp, then rename)

Also add:
    def rollback(self) -> None:
        """Restore original files from backup."""

Write tests using temp directories.
```

---

## Step 0.7: Generation Engine

Tell Claude Code:

```
Create tools/generate/engine.py with:

class GenerationEngine:
    def __init__(
        self,
        provider: LLMProvider,
        prompt_builder: PromptBuilder,
        parser: ResponseParser,
        writer: CodeWriter
    ):
        ...
    
    async def generate(self, context: GenerationContext) -> GenerationResult:
        """Main generation workflow."""

Workflow:
1. Build prompt from context
2. Call LLM provider
3. Parse response into files
4. Write files to disk
5. Return result

Handle errors at each step:
- API error: Retry, then return failure result
- Parse error: Return failure with raw response
- Write error: Rollback and return failure

Write integration tests with mocked provider.
```

---

## Step 0.8: CLI Commands

Tell Claude Code:

```
Create cli/click_commands/generate.py with:

@click.group()
def generate():
    """LLM code generation commands."""

@generate.command()
@click.option('--spec', required=True, type=click.Path(exists=True))
@click.option('--phase', type=click.Choice(['red', 'green', 'refactor']))
@click.option('--model', default='claude-sonnet-4-20250514')
@click.option('--dry-run', is_flag=True)
def code(spec, phase, model, dry_run):
    """Generate code from specification."""

Also add:
@generate.command()
@click.argument('response_file', type=click.Path(exists=True))
def parse_response(response_file):
    """Parse a manually-obtained LLM response."""
    # For manual mode workflow

Register in cli/main.py:
from cli.click_commands.generate import generate
cli.add_command(generate)

Write CLI tests.
```

---

## Step 0.9: TDFLOW Integration

Tell Claude Code:

```
Modify tools/tdflow/engine.py to use LLM generation:

1. Add optional generator parameter to TDFlowEngine

2. In run_red():
   - If generator available, call generator.generate(spec, phase="red")
   - Write generated test files
   - Run tests (should fail)

3. In run_green():
   - If generator available, call generator.generate(spec, phase="green")
   - Write generated implementation
   - Run tests (should pass)
   - Run conformance check

4. In run_refactor():
   - If generator available, call generator.generate(spec, phase="refactor")
   - Run tests (should still pass)

5. If no generator (no API key):
   - Print assembled prompt
   - Wait for manual input
   - Parse response and continue

Update cli/click_commands/tdflow.py to pass generator to engine.
```

---

## Step 0.10: Verification

Tell Claude Code:

```
Run full verification of the LLM generation component:

1. pytest tests/unit/tools/generate/ -v
2. python execute.py conformance check
3. Test manually:
   - Create a simple spec
   - Run: python execute.py generate code --spec test_spec.yaml --phase red --dry-run
   - Verify prompt looks correct
   - If you have API key, test actual generation

Fix any issues found.
```

---

## After Phase 0: Resume Agent Harness

Once LLM generation works:

```bash
# Now TDFLOW actually generates code!

agentforge tdflow start --spec outputs/specification.yaml
agentforge tdflow red   # → Generates real tests via Claude API
agentforge tdflow green # → Generates real implementation
agentforge tdflow verify

# Continue with Phase 1: Session Manager
# But now TDFLOW does the work, not just tracks state
```

---

## Quick Reference: Claude Code Prompts

### Start Session
```
We're building the LLM Generation component for AgentForge.
Read specs/agent-harness/llm_generation_spec.md for full requirements.
Current step: [step number]
```

### After Each Step
```
Run tests for what we just built:
pytest tests/unit/tools/generate/[test_file].py -v

Then conformance:
python execute.py conformance check

Show me any failures.
```

### End Session
```
Update progress, commit:
git add -A
git commit -m "LLM Generation: Step 0.X complete - [description]"
```

---

## Timeline

| Step | Description | Duration |
|------|-------------|----------|
| 0.1 | Directory structure | 10 min |
| 0.2 | Domain entities | 1-2 hours |
| 0.3 | LLM Provider | 2-3 hours |
| 0.4 | Prompt Builder | 2-3 hours |
| 0.5 | Response Parser | 1-2 hours |
| 0.6 | Code Writer | 1-2 hours |
| 0.7 | Generation Engine | 2-3 hours |
| 0.8 | CLI Commands | 1-2 hours |
| 0.9 | TDFLOW Integration | 2-3 hours |
| 0.10 | Verification | 1-2 hours |

**Total: ~2-3 days focused work**

After this, every subsequent phase uses working LLM generation.
