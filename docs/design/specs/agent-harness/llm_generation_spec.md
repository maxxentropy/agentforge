# LLM Generation Component Specification

## The Missing Piece

This component adds actual code generation to AgentForge, transforming TDFLOW from a state-tracking system into a real code generation engine.

```
BEFORE (Current):
  TDFLOW RED → "You are in RED phase" → Human writes tests
  TDFLOW GREEN → "You are in GREEN phase" → Human writes code

AFTER (With LLM Generation):
  TDFLOW RED → Calls Claude API → Returns actual test code
  TDFLOW GREEN → Calls Claude API → Returns actual implementation
  AgentForge Conformance → Verifies generated code
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LLM GENERATION COMPONENT                             │
│                                                                              │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────────┐    │
│  │  Prompt Builder │────>│   LLM Provider  │────>│  Response Parser    │    │
│  │                 │     │                 │     │                     │    │
│  │ - Spec context  │     │ - Claude API    │     │ - Extract code      │    │
│  │ - Phase rules   │     │ - (Future: others)│   │ - Parse files       │    │
│  │ - Patterns      │     │ - Rate limiting │     │ - Validate syntax   │    │
│  │ - Examples      │     │ - Retry logic   │     │                     │    │
│  └─────────────────┘     └─────────────────┘     └─────────────────────┘    │
│           │                                                │                 │
│           │              ┌─────────────────┐               │                 │
│           └─────────────>│  Code Writer    │<──────────────┘                 │
│                          │                 │                                 │
│                          │ - Write files   │                                 │
│                          │ - Track changes │                                 │
│                          │ - Backup orig   │                                 │
│                          └─────────────────┘                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EXISTING AGENTFORGE                                  │
│                                                                              │
│  TDFLOW Workflow ←── Calls generation at RED/GREEN phases                    │
│  Conformance ←────── Verifies generated code                                 │
│  Context Assembly ←─ Provides context for prompts                            │
│  Discovery ←──────── Provides patterns for prompts                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## SPEC Intake Prompt

Use this with `agentforge intake`:

```
Create an LLM Generation component for AgentForge that enables actual code 
generation from specifications during TDFLOW workflow phases.

CONTEXT:
- AgentForge has SPEC workflow (creates specifications)
- AgentForge has TDFLOW workflow (tracks red/green/refactor phases)
- AgentForge has Conformance (verifies code against patterns)
- MISSING: Actual code generation - currently humans write all code
- This component bridges the gap by calling LLM APIs to generate code

CORE PURPOSE:
Transform TDFLOW from state-tracking into actual code generation:
- RED phase: Generate real, failing tests from specification
- GREEN phase: Generate real implementation to pass tests
- REFACTOR phase: Generate improved code while maintaining tests

REQUIREMENTS:

1. LLM Provider Abstraction
   - Support Claude API (Anthropic) as primary provider
   - Abstract interface for future providers (OpenAI, local models)
   - Handle API authentication via environment variables or config
   - Support model selection (claude-sonnet-4-20250514, opus, etc.)
   - Implement rate limiting and retry with exponential backoff
   - Track token usage and costs

2. Prompt Builder
   - Assemble context from multiple sources:
     * Specification (from SPEC workflow output)
     * Phase requirements (what RED/GREEN/REFACTOR means)
     * Project patterns (from Discovery profile)
     * Existing code examples (from codebase)
     * Previous attempts (if retry)
     * Error context (if fixing failure)
   - Apply token budgeting (fit within model context)
   - Use structured prompt format (XML tags for sections)
   - Include output format instructions (file markers, etc.)

3. Response Parser
   - Extract code blocks from LLM response
   - Parse file boundaries (multiple files in one response)
   - Identify file paths from markers or conventions
   - Validate basic syntax (Python parseable)
   - Handle partial/incomplete responses
   - Extract explanations separate from code

4. Code Writer
   - Write generated code to correct locations
   - Backup original files before overwriting
   - Track all file changes for rollback
   - Create directories as needed
   - Preserve file permissions

5. TDFLOW Integration
   - Hook into existing TDFLOW phase transitions
   - RED phase: Generate tests in tests/ directory
   - GREEN phase: Generate implementation in tools/ directory
   - REFACTOR phase: Modify existing files
   - Pass generation results to verification

6. Generation Modes
   - full: Generate complete file(s) from scratch
   - incremental: Add to existing file
   - fix: Modify specific code based on error
   - refactor: Restructure while preserving behavior

7. Error Handling
   - API failures: Retry with backoff, then fail gracefully
   - Invalid response: Request regeneration with feedback
   - Syntax errors: Attempt auto-fix or report
   - Token overflow: Summarize context and retry

8. Configuration
   - .agentforge/generation.yaml for settings
   - Environment variables for secrets (ANTHROPIC_API_KEY)
   - Per-project model preferences
   - Token budget limits
   - Retry policies

INTERFACES:

Primary Interface:
  generate(
    spec: Specification,
    phase: "red" | "green" | "refactor",
    mode: "full" | "incremental" | "fix",
    context: Optional[ErrorContext]
  ) -> GenerationResult

GenerationResult:
  success: bool
  files: list[GeneratedFile]  # path, content, action (create/modify)
  explanation: str            # LLM's reasoning
  tokens_used: int
  model: str
  
CLI Commands:
  agentforge generate --spec <path> --phase red
  agentforge generate --spec <path> --phase green
  agentforge generate --spec <path> --phase refactor
  agentforge generate --fix <error_context>

CONSTRAINTS:
- Must work without API key (graceful degradation to manual mode)
- Must not store API keys in code or config files
- Must log all LLM interactions for debugging
- Must respect token budgets (no runaway costs)
- Must integrate cleanly with existing TDFLOW
- Generated code must be clearly marked (header comment)

RELATED FILES:
- tools/tdflow/domain.py (TDFLOW workflow)
- tools/tdflow/engine.py (phase transitions)
- tools/context_assembler.py (context building)
- tools/discovery/domain.py (patterns)
- .agentforge/codebase_profile.yaml (project patterns)

OUTPUT LOCATIONS:
- tools/generate/ (new module)
  - __init__.py
  - domain.py (entities: GenerationResult, GeneratedFile, etc.)
  - provider.py (LLM provider abstraction)
  - prompt_builder.py (context assembly)
  - parser.py (response parsing)
  - writer.py (file writing)
  - engine.py (main orchestration)
- cli/click_commands/generate.py (CLI)
- tests/unit/tools/generate/ (tests)
```

---

## Expected Clarifications

```yaml
clarifications:
  - question: "Should generation work offline/without API key?"
    answer: "Yes. If no API key, print the assembled prompt to stdout so 
             human can manually use it with Claude. Log warning about 
             missing key. This preserves the workflow even without API."

  - question: "How should API keys be provided?"
    answer: "Priority order: 
             1. ANTHROPIC_API_KEY environment variable
             2. .agentforge/secrets.yaml (gitignored)
             3. Prompt user interactively (don't store)
             Never commit keys. Add secrets.yaml to .gitignore template."

  - question: "What model should be default?"
    answer: "claude-sonnet-4-20250514 for balance of speed/quality. 
             Allow override via config or --model flag. 
             Use opus for complex generation if specified."

  - question: "How should multiple files be handled in one generation?"
    answer: "LLM response uses markers:
             ```python:path/to/file.py
             # code here
             ```
             Parser extracts path from marker. If no path, infer from 
             phase (tests go to tests/, impl goes to tools/)."

  - question: "What's the token budget strategy?"
    answer: "Default 8000 tokens for context, 4000 for response.
             If spec + context exceeds budget:
             1. Summarize large code files
             2. Include only most relevant examples
             3. Truncate history
             Track and report actual usage."

  - question: "How should generation failures be handled?"
    answer: "On LLM error: Retry 3x with exponential backoff.
             On invalid code: Feed error back to LLM for fix (1 retry).
             On persistent failure: Save prompt to file, exit with 
             instructions for manual completion."

  - question: "Should generated code be marked?"
    answer: "Yes. Add header comment:
             # Generated by AgentForge LLM Generation
             # Spec: {spec_name}
             # Phase: {phase}
             # Model: {model}
             # Date: {timestamp}
             This helps with debugging and audit."

  - question: "How does this integrate with TDFLOW verify?"
    answer: "After generation, TDFLOW verify runs:
             1. Syntax check (Python parse)
             2. Test execution (pytest)
             3. Conformance check
             If any fail, can trigger generate --fix with error context."
```

---

## Design Decisions

### D1: Prompt Structure

Use XML-tagged sections for clear LLM parsing:

```xml
<context>
  <specification>
    {full specification YAML}
  </specification>
  
  <phase>
    {phase name and requirements}
  </phase>
  
  <patterns>
    {discovered patterns to follow}
  </patterns>
  
  <examples>
    {similar code from project}
  </examples>
  
  <error_context>
    {if fixing: what went wrong}
  </error_context>
</context>

<instructions>
  Generate {phase} code for the specification above.
  
  Requirements:
  - Follow the patterns shown in <patterns>
  - Match the style of <examples>
  - Output complete, working code
  - Use markers for file paths: ```python:path/to/file.py
  
  {phase-specific instructions}
</instructions>
```

### D2: Phase-Specific Instructions

**RED Phase:**
```
Generate pytest test files that:
- Test all functional requirements in the specification
- Test error cases and edge cases
- Use fixtures for setup/teardown
- Follow existing test patterns in the project
- Tests MUST FAIL (no implementation exists yet)
- Include clear test names describing behavior
```

**GREEN Phase:**
```
Generate implementation that:
- Makes all tests from RED phase pass
- Follows the interfaces defined in specification
- Uses patterns from the project (Result type, etc.)
- Includes docstrings and type hints
- Handles all error cases from specification
- Minimal code - just enough to pass tests
```

**REFACTOR Phase:**
```
Improve the implementation:
- Reduce duplication
- Improve naming
- Extract helpers if needed
- Optimize if obvious wins
- DO NOT change behavior (tests must still pass)
```

### D3: File Output Convention

```python
# Response format from LLM:

```python:tests/unit/harness/test_session.py
import pytest
from tools.harness.session import SessionManager

class TestSessionManager:
    def test_create_session(self):
        # test code
```

```python:tests/unit/harness/test_session_persistence.py
import pytest
# more tests
```

Parser extracts:
- File path from marker after ```python:
- Content until next marker or end
- Creates list of GeneratedFile objects
```

### D4: Graceful Degradation

```
┌─────────────────────────────────────────────────────────────┐
│                  DEGRADATION HIERARCHY                       │
│                                                              │
│  Level 1: Full Auto (API key + working API)                  │
│    → Generate code, write files, continue workflow           │
│                                                              │
│  Level 2: Interactive (API key + rate limited)               │
│    → Generate code, prompt user to confirm before writing    │
│                                                              │
│  Level 3: Manual (No API key)                                │
│    → Print assembled prompt to stdout                        │
│    → User copies to Claude UI, pastes response               │
│    → agentforge parse-response <file> to continue            │
│                                                              │
│  Level 4: Offline (No API, no internet)                      │
│    → Save prompt to file                                     │
│    → Print instructions for later completion                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Order

### Step 1: Domain Entities
```python
# tools/generate/domain.py

@dataclass
class GeneratedFile:
    path: Path
    content: str
    action: Literal["create", "modify", "delete"]
    original_content: Optional[str] = None

@dataclass
class GenerationResult:
    success: bool
    files: list[GeneratedFile]
    explanation: str
    tokens_used: int
    model: str
    prompt_tokens: int
    completion_tokens: int
    error: Optional[str] = None

@dataclass  
class GenerationContext:
    spec: Specification
    phase: Literal["red", "green", "refactor"]
    mode: Literal["full", "incremental", "fix"]
    patterns: dict
    examples: list[CodeExample]
    error_context: Optional[ErrorContext] = None

class GenerationError(Exception):
    """Base error for generation failures."""
    pass

class APIError(GenerationError):
    """LLM API call failed."""
    pass

class ParseError(GenerationError):
    """Could not parse LLM response."""
    pass
```

### Step 2: LLM Provider
```python
# tools/generate/provider.py

from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, max_tokens: int) -> str:
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        pass

class ClaudeProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
    
    async def generate(self, prompt: str, max_tokens: int = 4096) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

class ManualProvider(LLMProvider):
    """Fallback when no API key - prints prompt for manual use."""
    
    async def generate(self, prompt: str, max_tokens: int) -> str:
        print("=" * 60)
        print("NO API KEY - Manual mode")
        print("=" * 60)
        print("\nCopy this prompt to Claude:\n")
        print(prompt)
        print("\n" + "=" * 60)
        print("Paste Claude's response (end with EOF on new line):")
        
        lines = []
        while True:
            line = input()
            if line == "EOF":
                break
            lines.append(line)
        
        return "\n".join(lines)
```

### Step 3: Prompt Builder
```python
# tools/generate/prompt_builder.py

class PromptBuilder:
    def __init__(self, context_assembler: ContextAssembler):
        self.context = context_assembler
    
    def build(self, gen_context: GenerationContext) -> str:
        return f"""<context>
<specification>
{yaml.dump(gen_context.spec)}
</specification>

<phase>{gen_context.phase}</phase>

<patterns>
{self._format_patterns(gen_context.patterns)}
</patterns>

<examples>
{self._format_examples(gen_context.examples)}
</examples>

{self._format_error_context(gen_context.error_context)}
</context>

<instructions>
{self._get_phase_instructions(gen_context.phase)}

Output format:
- Use ```python:path/to/file.py markers for each file
- Include complete, working code
- Add header comment with generation metadata
</instructions>"""
```

### Step 4: Response Parser
```python
# tools/generate/parser.py

class ResponseParser:
    FILE_PATTERN = re.compile(r'```python:(.+?)\n(.*?)```', re.DOTALL)
    
    def parse(self, response: str) -> list[GeneratedFile]:
        files = []
        
        for match in self.FILE_PATTERN.finditer(response):
            path = Path(match.group(1).strip())
            content = match.group(2)
            
            # Validate Python syntax
            try:
                ast.parse(content)
            except SyntaxError as e:
                raise ParseError(f"Invalid Python in {path}: {e}")
            
            files.append(GeneratedFile(
                path=path,
                content=content,
                action="create" if not path.exists() else "modify"
            ))
        
        if not files:
            raise ParseError("No code files found in response")
        
        return files
```

### Step 5: Generation Engine
```python
# tools/generate/engine.py

class GenerationEngine:
    def __init__(
        self,
        provider: LLMProvider,
        prompt_builder: PromptBuilder,
        parser: ResponseParser,
        writer: CodeWriter
    ):
        self.provider = provider
        self.prompt_builder = prompt_builder
        self.parser = parser
        self.writer = writer
    
    async def generate(self, context: GenerationContext) -> GenerationResult:
        # Build prompt
        prompt = self.prompt_builder.build(context)
        
        # Call LLM
        try:
            response = await self.provider.generate(prompt)
        except Exception as e:
            return GenerationResult(
                success=False,
                files=[],
                explanation="",
                tokens_used=0,
                model=self.provider.model,
                error=str(e)
            )
        
        # Parse response
        try:
            files = self.parser.parse(response)
        except ParseError as e:
            return GenerationResult(
                success=False,
                files=[],
                explanation=response,
                tokens_used=0,
                model=self.provider.model,
                error=str(e)
            )
        
        # Write files
        self.writer.write(files)
        
        return GenerationResult(
            success=True,
            files=files,
            explanation=self._extract_explanation(response),
            tokens_used=self.provider.count_tokens(prompt + response),
            model=self.provider.model
        )
```

### Step 6: CLI Integration
```python
# cli/click_commands/generate.py

@click.group()
def generate():
    """LLM code generation commands."""
    pass

@generate.command()
@click.option('--spec', required=True, help='Path to specification')
@click.option('--phase', type=click.Choice(['red', 'green', 'refactor']))
@click.option('--model', default='claude-sonnet-4-20250514')
@click.option('--dry-run', is_flag=True, help='Print prompt without calling API')
def code(spec, phase, model, dry_run):
    """Generate code from specification."""
    engine = create_engine(model)
    context = load_generation_context(spec, phase)
    
    if dry_run:
        prompt = engine.prompt_builder.build(context)
        click.echo(prompt)
        return
    
    result = asyncio.run(engine.generate(context))
    
    if result.success:
        click.echo(f"✓ Generated {len(result.files)} file(s)")
        for f in result.files:
            click.echo(f"  - {f.path} ({f.action})")
    else:
        click.echo(f"✗ Generation failed: {result.error}")
```

### Step 7: TDFLOW Integration
```python
# Modify tools/tdflow/engine.py

class TDFlowEngine:
    def __init__(self, ..., generator: Optional[GenerationEngine] = None):
        self.generator = generator
    
    async def run_red(self, spec: Specification) -> PhaseResult:
        if self.generator:
            # Auto-generate tests
            context = GenerationContext(
                spec=spec,
                phase="red",
                mode="full",
                patterns=self.load_patterns(),
                examples=self.find_test_examples()
            )
            result = await self.generator.generate(context)
            
            if not result.success:
                return PhaseResult(success=False, error=result.error)
        
        # Run tests (should fail)
        test_result = self.run_tests()
        
        if test_result.all_passed:
            return PhaseResult(
                success=False, 
                error="Tests should FAIL in RED phase"
            )
        
        return PhaseResult(success=True, files=result.files)
```

---

## Configuration

### .agentforge/generation.yaml

```yaml
# LLM Generation Configuration

provider:
  name: claude
  model: claude-sonnet-4-20250514
  # For complex generation:
  # model: claude-opus-4-20250514

tokens:
  max_context: 8000
  max_response: 4096
  
retry:
  max_attempts: 3
  base_delay_seconds: 1
  max_delay_seconds: 30

output:
  add_header_comment: true
  backup_existing: true
  
# Phase-specific settings
phases:
  red:
    test_directory: tests/unit
    
  green:
    implementation_directory: tools
    
  refactor:
    require_tests_pass: true
```

### Environment Variables

```bash
# Required for auto mode
export ANTHROPIC_API_KEY=sk-ant-...

# Optional overrides
export AGENTFORGE_MODEL=claude-opus-4-20250514
export AGENTFORGE_MAX_TOKENS=16000
```

---

## Success Criteria

After implementation:

1. **Basic Generation**
   - [ ] `agentforge generate --spec X --phase red` produces valid test files
   - [ ] `agentforge generate --spec X --phase green` produces valid implementation
   - [ ] Generated code follows project patterns

2. **TDFLOW Integration**
   - [ ] `agentforge tdflow red` calls generation automatically
   - [ ] `agentforge tdflow green` calls generation automatically
   - [ ] `agentforge tdflow verify` validates generated code

3. **Graceful Degradation**
   - [ ] Works without API key (manual mode)
   - [ ] Handles API errors gracefully
   - [ ] Retries on transient failures

4. **Quality**
   - [ ] Generated code passes conformance
   - [ ] Generated tests actually test requirements
   - [ ] Generated implementation passes tests

---

## What This Enables

Once LLM Generation is complete:

```bash
# Full autonomous workflow
agentforge intake "Build session manager for agent harness"
# → Creates specification

agentforge tdflow start --spec outputs/specification.yaml
# → Initializes TDFLOW

agentforge tdflow red
# → GENERATES real tests via Claude API
# → Verifies tests fail

agentforge tdflow green  
# → GENERATES real implementation via Claude API
# → Verifies tests pass
# → Verifies conformance passes

agentforge tdflow refactor
# → GENERATES improved code
# → Verifies tests still pass

# Done - real code, automatically generated and verified
```

This transforms AgentForge from a verification tool into a complete code generation system.
