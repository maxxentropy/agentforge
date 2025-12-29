# Executor Abstraction Architecture
## Supporting Human-in-Loop to Autonomous API Transition

## 1. Overview

AgentForge is designed to work identically across different execution modes:

| Mode | Description | Cost | Use Case |
|------|-------------|------|----------|
| **Human-in-Loop** | User copies prompts to Claude subscription | $0 | Development, refinement, critical workflows |
| **API Sequential** | Direct API calls, one at a time | Per-token | Standard workflows, unattended |
| **API Parallel** | Multiple concurrent API calls | Per-token | Routine tasks, batch processing |

**Key Principle:** Same prompts + same verification = same outputs, regardless of execution mode.

## 2. Executor Interface

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
import asyncio
import time

class ExecutionMode(Enum):
    HUMAN_IN_LOOP = "human"
    API_SEQUENTIAL = "api_sequential"
    API_PARALLEL = "api_parallel"

@dataclass
class ExecutionRequest:
    """A request to execute a prompt."""
    prompt: str
    context: dict
    expected_output_schema: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.0  # Deterministic by default
    task_id: Optional[str] = None
    state_name: Optional[str] = None
    attempt: int = 1

@dataclass
class ExecutionResponse:
    """Response from execution."""
    content: str
    tokens_used: int
    execution_time_ms: int
    mode: ExecutionMode
    cost_usd: float = 0.0
    request: Optional[ExecutionRequest] = None

@dataclass
class ExecutionBatch:
    """A batch of requests for parallel execution."""
    requests: List[ExecutionRequest]
    max_concurrency: int = 5
    
class Executor(ABC):
    """
    Abstract executor interface.
    
    Implementations must produce identical outputs for identical inputs.
    The only difference is HOW the LLM is invoked.
    """
    
    @property
    @abstractmethod
    def mode(self) -> ExecutionMode:
        """The execution mode this executor implements."""
        pass
    
    @abstractmethod
    async def execute(self, request: ExecutionRequest) -> ExecutionResponse:
        """Execute a single request."""
        pass
    
    async def execute_batch(
        self, 
        batch: ExecutionBatch
    ) -> List[ExecutionResponse]:
        """
        Execute multiple requests.
        
        Default implementation is sequential.
        Override for parallel execution.
        """
        responses = []
        for request in batch.requests:
            response = await self.execute(request)
            responses.append(response)
        return responses
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Verify executor is ready."""
        pass
```

## 3. Human-in-Loop Executor

For use with Claude subscription (Phase 1):

```python
import sys

class HumanInLoopExecutor(Executor):
    """
    Executor for subscription-based usage.
    
    Displays prompts for user to copy to Claude,
    then accepts pasted responses.
    """
    
    @property
    def mode(self) -> ExecutionMode:
        return ExecutionMode.HUMAN_IN_LOOP
    
    async def execute(self, request: ExecutionRequest) -> ExecutionResponse:
        start_time = time.time()
        
        # Format and display the prompt
        self._display_prompt(request)
        
        # Collect response from user
        content = self._collect_response()
        
        execution_time = int((time.time() - start_time) * 1000)
        
        return ExecutionResponse(
            content=content,
            tokens_used=0,  # Unknown in subscription mode
            execution_time_ms=execution_time,
            mode=self.mode,
            cost_usd=0.0,
            request=request
        )
    
    def _display_prompt(self, request: ExecutionRequest):
        """Display prompt for user to copy."""
        print("\n" + "=" * 70)
        print(f"📋 PROMPT FOR: {request.state_name or 'Unknown State'}")
        print(f"   Task: {request.task_id or 'Unknown'}")
        print(f"   Attempt: {request.attempt}")
        print("=" * 70)
        print()
        print(request.prompt)
        print()
        print("=" * 70)
        print("📋 Copy the above prompt to Claude")
        print("=" * 70)
    
    def _collect_response(self) -> str:
        """Collect response pasted by user."""
        print("\n📥 Paste Claude's response below.")
        print("   (End with a line containing only 'END')")
        print("-" * 70)
        
        lines = []
        while True:
            try:
                line = input()
                if line.strip() == "END":
                    break
                lines.append(line)
            except EOFError:
                break
        
        return "\n".join(lines)
    
    async def health_check(self) -> bool:
        """Always ready - user is the executor."""
        return True


class FileBasedHumanExecutor(HumanInLoopExecutor):
    """
    Variant that writes prompts to files and reads responses from files.
    
    Useful for:
    - Long prompts that are hard to copy
    - Preserving exact formatting
    - Integration with external tools
    """
    
    def __init__(self, prompt_dir: str = ".agentforge/prompts"):
        self.prompt_dir = Path(prompt_dir)
        self.prompt_dir.mkdir(parents=True, exist_ok=True)
    
    def _display_prompt(self, request: ExecutionRequest):
        # Write prompt to file
        prompt_file = self.prompt_dir / f"prompt_{request.task_id}_{request.attempt}.md"
        prompt_file.write_text(request.prompt)
        
        print(f"\n📄 Prompt written to: {prompt_file}")
        print("   1. Open the file and copy contents to Claude")
        print("   2. Save Claude's response to:")
        
        response_file = self.prompt_dir / f"response_{request.task_id}_{request.attempt}.md"
        print(f"      {response_file}")
        print("   3. Press Enter when ready...")
        input()
        
        self._response_file = response_file
    
    def _collect_response(self) -> str:
        if not self._response_file.exists():
            raise FileNotFoundError(f"Response file not found: {self._response_file}")
        return self._response_file.read_text()
```

## 4. API Executor

For direct Anthropic API calls (Phase 2):

```python
import anthropic
from typing import Optional

# Pricing as of 2025 (update as needed)
PRICING = {
    "claude-sonnet-4-20250514": {
        "input_per_1k": 0.003,
        "output_per_1k": 0.015
    },
    "claude-opus-4-20250514": {
        "input_per_1k": 0.015,
        "output_per_1k": 0.075
    },
    "claude-haiku-4-20250514": {
        "input_per_1k": 0.00025,
        "output_per_1k": 0.00125
    }
}

@dataclass
class APIConfig:
    api_key: str
    model: str = "claude-sonnet-4-20250514"
    max_retries: int = 3
    timeout_seconds: int = 120
    
    # Cost controls
    daily_budget_usd: float = 10.0
    per_task_limit_usd: float = 2.0

class AnthropicAPIExecutor(Executor):
    """
    Executor using Anthropic API directly.
    
    Features:
    - Cost tracking
    - Budget enforcement
    - Automatic retries
    """
    
    def __init__(self, config: APIConfig):
        self.config = config
        self.client = anthropic.Anthropic(api_key=config.api_key)
        self._daily_cost = 0.0
        self._daily_reset = datetime.now().date()
    
    @property
    def mode(self) -> ExecutionMode:
        return ExecutionMode.API_SEQUENTIAL
    
    async def execute(self, request: ExecutionRequest) -> ExecutionResponse:
        # Check budget
        self._check_budget(request)
        
        start_time = time.time()
        
        response = self.client.messages.create(
            model=self.config.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            messages=[{"role": "user", "content": request.prompt}]
        )
        
        execution_time = int((time.time() - start_time) * 1000)
        
        # Calculate cost
        cost = self._calculate_cost(
            response.usage.input_tokens,
            response.usage.output_tokens
        )
        self._daily_cost += cost
        
        return ExecutionResponse(
            content=response.content[0].text,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            execution_time_ms=execution_time,
            mode=self.mode,
            cost_usd=cost,
            request=request
        )
    
    def _check_budget(self, request: ExecutionRequest):
        """Enforce budget limits."""
        # Reset daily counter if new day
        today = datetime.now().date()
        if today > self._daily_reset:
            self._daily_cost = 0.0
            self._daily_reset = today
        
        # Check daily budget
        if self._daily_cost >= self.config.daily_budget_usd:
            raise BudgetExceededError(
                f"Daily budget of ${self.config.daily_budget_usd} exceeded"
            )
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD."""
        pricing = PRICING.get(self.config.model, PRICING["claude-sonnet-4-20250514"])
        input_cost = (input_tokens / 1000) * pricing["input_per_1k"]
        output_cost = (output_tokens / 1000) * pricing["output_per_1k"]
        return input_cost + output_cost
    
    async def health_check(self) -> bool:
        """Verify API is accessible."""
        try:
            # Minimal API call
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return True
        except Exception:
            return False


class ParallelAPIExecutor(AnthropicAPIExecutor):
    """
    Executor for parallel API calls.
    
    Uses asyncio to run multiple requests concurrently.
    """
    
    def __init__(self, config: APIConfig, max_concurrency: int = 5):
        super().__init__(config)
        self.max_concurrency = max_concurrency
        self._semaphore = asyncio.Semaphore(max_concurrency)
    
    @property
    def mode(self) -> ExecutionMode:
        return ExecutionMode.API_PARALLEL
    
    async def execute_batch(
        self, 
        batch: ExecutionBatch
    ) -> List[ExecutionResponse]:
        """Execute requests in parallel with concurrency limit."""
        
        async def execute_with_semaphore(request: ExecutionRequest):
            async with self._semaphore:
                return await self.execute(request)
        
        tasks = [execute_with_semaphore(r) for r in batch.requests]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error responses
        results = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                results.append(ExecutionResponse(
                    content=f"ERROR: {str(response)}",
                    tokens_used=0,
                    execution_time_ms=0,
                    mode=self.mode,
                    cost_usd=0.0,
                    request=batch.requests[i]
                ))
            else:
                results.append(response)
        
        return results
```

## 5. Executor Factory

```python
class ExecutorFactory:
    """Create appropriate executor based on configuration."""
    
    @staticmethod
    def create(config: dict) -> Executor:
        mode = config.get("mode", "human")
        
        if mode == "human":
            use_files = config.get("use_files", False)
            if use_files:
                return FileBasedHumanExecutor(
                    prompt_dir=config.get("prompt_dir", ".agentforge/prompts")
                )
            return HumanInLoopExecutor()
        
        elif mode == "api":
            api_config = APIConfig(
                api_key=config["api_key"],
                model=config.get("model", "claude-sonnet-4-20250514"),
                daily_budget_usd=config.get("daily_budget", 10.0),
                per_task_limit_usd=config.get("per_task_limit", 2.0)
            )
            return AnthropicAPIExecutor(api_config)
        
        elif mode == "parallel":
            api_config = APIConfig(
                api_key=config["api_key"],
                model=config.get("model", "claude-sonnet-4-20250514"),
                daily_budget_usd=config.get("daily_budget", 10.0)
            )
            return ParallelAPIExecutor(
                api_config,
                max_concurrency=config.get("max_concurrency", 5)
            )
        
        else:
            raise ValueError(f"Unknown execution mode: {mode}")
```

## 6. Workflow Criticality

Different workflows have different requirements for human oversight:

```yaml
# config/criticality.yaml

criticality_levels:
  critical:
    description: "Requires human oversight at every step"
    allowed_modes: [human]
    examples:
      - "SPEC workflow (requirements are foundational)"
      - "Security-related changes"
      - "Production deployments"
      - "First run of any new workflow"
    human_checkpoints: "every_state"
    
  standard:
    description: "Autonomous execution, human reviews final output"
    allowed_modes: [human, api_sequential]
    examples:
      - "TDFLOW for well-specified features"
      - "Refactoring with good test coverage"
      - "Bug fixes with reproduction tests"
    human_checkpoints: "terminal_states_only"
    
  routine:
    description: "Fully autonomous, batch processing OK"
    allowed_modes: [human, api_sequential, api_parallel]
    examples:
      - "Documentation generation"
      - "Code formatting"
      - "Test generation for existing code"
      - "Dependency updates (non-breaking)"
    human_checkpoints: "on_failure_only"

workflow_criticality:
  SPEC: critical
  TDFLOW: standard
  BUGFIX: standard
  REFACTOR: standard
  DOCUMENT: routine
  FORMAT: routine
  TEST_GEN: routine

# Criticality can be overridden per-task
task_criticality_override:
  allowed: true
  requires_confirmation: true
  cannot_decrease_from: critical  # Can't make critical tasks routine
```

## 7. Cost Management

```python
@dataclass
class CostTracker:
    """Track API costs across sessions."""
    
    daily_budget: float
    per_task_budget: float
    
    # State
    daily_spent: float = 0.0
    daily_reset_date: date = field(default_factory=date.today)
    task_costs: dict = field(default_factory=dict)
    
    def record_cost(self, task_id: str, cost: float):
        """Record cost for a task."""
        self._check_daily_reset()
        
        self.daily_spent += cost
        self.task_costs[task_id] = self.task_costs.get(task_id, 0) + cost
    
    def can_execute(self, task_id: str, estimated_cost: float = 0.1) -> tuple[bool, str]:
        """Check if execution is allowed within budget."""
        self._check_daily_reset()
        
        # Check daily budget
        if self.daily_spent + estimated_cost > self.daily_budget:
            return False, f"Would exceed daily budget (${self.daily_budget})"
        
        # Check per-task budget
        task_spent = self.task_costs.get(task_id, 0)
        if task_spent + estimated_cost > self.per_task_budget:
            return False, f"Would exceed task budget (${self.per_task_budget})"
        
        return True, "OK"
    
    def _check_daily_reset(self):
        """Reset daily counter if new day."""
        today = date.today()
        if today > self.daily_reset_date:
            self.daily_spent = 0.0
            self.daily_reset_date = today
    
    def get_summary(self) -> dict:
        """Get cost summary."""
        return {
            "daily_spent": self.daily_spent,
            "daily_budget": self.daily_budget,
            "daily_remaining": self.daily_budget - self.daily_spent,
            "tasks": self.task_costs
        }
```

## 8. Configuration

```yaml
# config/execution.yaml

# Default execution mode
default_mode: human  # human | api | parallel

# API configuration (when mode is api or parallel)
api:
  # API key from environment variable
  api_key_env: "ANTHROPIC_API_KEY"
  
  # Model selection
  model: "claude-sonnet-4-20250514"
  
  # Cost controls
  daily_budget_usd: 10.00
  per_task_limit_usd: 2.00
  alert_threshold_pct: 80  # Alert when 80% of budget used
  
  # Parallel execution
  max_concurrency: 5
  
  # Reliability
  max_retries: 3
  timeout_seconds: 120
  retry_delay_seconds: 5

# Human-in-loop configuration
human:
  # Use file-based prompts (better for long prompts)
  use_files: false
  prompt_dir: ".agentforge/prompts"
  
  # Clipboard integration (future)
  auto_copy_to_clipboard: true

# Mode selection per workflow
workflow_modes:
  SPEC: human  # Always human for requirements
  TDFLOW: ${default_mode}
  BUGFIX: ${default_mode}
  REFACTOR: ${default_mode}
  DOCUMENT: ${default_mode}
  TEST_GEN: ${default_mode}
```

## 9. Transition Strategy

### Phase 1: Human-in-Loop Development
```
- All workflows use HumanInLoopExecutor
- Focus on prompt quality and verification
- Build confidence in outputs
- Zero API cost
```

### Phase 2: API Validation
```
- Add AnthropicAPIExecutor implementation
- Run same prompts through API
- Verify outputs match human-in-loop results
- Small test budget ($5-20)
```

### Phase 3: Hybrid Operation
```
- Critical workflows: Human-in-loop
- Standard workflows: API Sequential
- Routine workflows: API Parallel (where applicable)
```

### Phase 4: Full Autonomy
```
- Most workflows unattended
- Human reviews final outputs
- Human handles escalations
- Cost-managed API usage
```

## 10. Testing Strategy

```python
class ExecutorTestSuite:
    """
    Tests to verify execution mode equivalence.
    
    Key principle: Same prompt should produce functionally
    equivalent output regardless of execution mode.
    """
    
    def test_output_schema_compliance(self):
        """Output must match expected schema in all modes."""
        pass
    
    def test_verification_pass_rate(self):
        """Verification pass rate should be similar across modes."""
        pass
    
    def test_determinism(self):
        """Same prompt with temperature=0 should produce consistent output."""
        pass
    
    def test_cost_tracking(self):
        """API mode must accurately track costs."""
        pass
    
    def test_budget_enforcement(self):
        """Budget limits must be enforced."""
        pass
```
