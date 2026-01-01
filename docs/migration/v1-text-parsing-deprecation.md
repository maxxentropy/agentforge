# V1 Text-Parsing Execution Deprecation Guide

> **Status**: Deprecated in v2.0, removal planned for v3.0
> **Last Updated**: 2025-01-01

## Overview

The V1 execution model used YAML-based text parsing to extract agent actions from LLM responses. This approach has been superseded by **native tool calls** using the Anthropic `tool_use` API.

## Why the Change?

### V1 Approach (Deprecated)

```python
# V1: Agent returns YAML in response text
response = """
I'll read the file to understand the issue.

```action
name: read_file
parameters:
  path: /src/module.py
```
"""

# Parser extracts action from text
action_name, params = executor._parse_action(response)
```

**Problems with V1:**
1. **Unreliable parsing**: LLM might produce malformed YAML
2. **Prompt injection risk**: Content could include fake action blocks
3. **Token inefficiency**: Response format instructions consume tokens
4. **No structured validation**: Parameters not validated before execution

### V2 Approach (Current)

```python
# V2: Agent uses native tool calls
response = client.complete(
    messages=messages,
    tools=[
        {
            "name": "read_file",
            "description": "Read file contents",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"}
                },
                "required": ["path"]
            }
        }
    ]
)

# Tool call is structured, validated by API
tool_call = response.get_first_tool_call()
# tool_call.name = "read_file"
# tool_call.input = {"path": "/src/module.py"}
```

**Benefits of V2:**
1. **Structured responses**: Tool calls are parsed by the API, not regex
2. **Type validation**: Input schemas enforce parameter types
3. **Security**: No prompt injection via response parsing
4. **Token efficiency**: No format instructions needed
5. **Better observability**: Tool calls appear in API logs

## Migration Guide

### Step 1: Update Executor Instantiation

```python
# Before (V1)
from agentforge.core.harness.minimal_context import MinimalContextExecutor

executor = MinimalContextExecutor(
    project_path=project_path,
    task_type="fix_violation",
)
# Ran with: executor.run_until_complete(task_id)

# After (V2)
from agentforge.core.harness.minimal_context import MinimalContextExecutor
from agentforge.core.llm import LLMClientFactory

executor = MinimalContextExecutor(
    project_path=project_path,
    task_type="fix_violation",
)
client = LLMClientFactory.create()
# Run with: executor.run_task_native(task_id, domain_context, llm_client=client)
```

### Step 2: Update Action Handlers

```python
# Before (V1) - Action executors received parsed dict
def read_file_handler(action_name, params, state):
    path = params.get("path")
    content = Path(path).read_text()
    return {"status": "success", "content": content}

executor.register_action("read_file", read_file_handler)

# After (V2) - Use NativeToolExecutor handlers
from agentforge.core.harness.minimal_context.native_tool_executor import (
    NativeToolExecutor,
    ToolResult,
)

def read_file_handler(tool_call):
    path = tool_call.input.get("path")
    content = Path(path).read_text()
    return ToolResult(content=content, is_error=False)

executor.native_tool_executor.register_action("read_file", read_file_handler)
```

### Step 3: Update Tool Definitions

Tools are now defined with JSON Schema:

```python
from agentforge.core.llm import get_tools_for_task

# Built-in tools for common task types
tools = get_tools_for_task("fix_violation")

# Or define custom tools
custom_tools = [
    {
        "name": "my_custom_tool",
        "description": "Does something custom",
        "input_schema": {
            "type": "object",
            "properties": {
                "arg1": {"type": "string"},
                "arg2": {"type": "integer", "minimum": 0},
            },
            "required": ["arg1"],
        },
    }
]
```

### Step 4: Check Environment Variable

Native tools can be enabled via environment:

```bash
# Enable native tools (default in v2)
export AGENTFORGE_NATIVE_TOOLS=true
```

Or check programmatically:

```python
from agentforge.core.harness.minimal_context import should_use_native_tools

if should_use_native_tools():
    result = executor.run_task_native(task_id, context, client)
else:
    result = executor.run_until_complete(task_id)  # Legacy
```

## API Changes

### Deprecated Methods

| V1 Method | V2 Replacement | Notes |
|-----------|---------------|-------|
| `execute_step()` | `run_task_native()` | Single step → full task loop |
| `run_until_complete()` | `run_task_native()` | Uses native tools |
| `_parse_action()` | Native tool parsing | Handled by API |

### Deprecated Classes

| V1 Class | V2 Replacement | Notes |
|----------|---------------|-------|
| `ContextBuilder` | `TemplateContextBuilder` | Template-based |
| `EnhancedContextBuilder` | `TemplateContextBuilder` | Merged into unified |
| `TokenBudget` | `CompactionManager` | Integrated compaction |

### Deprecated Modules

```python
# V1 imports (deprecated)
from agentforge.core.harness.minimal_context.deprecated import (
    ContextBuilder,           # Use TemplateContextBuilder
    EnhancedContextBuilder,   # Use TemplateContextBuilder
    TokenBudget,              # Use CompactionManager
    ContextSchema,            # Use templates
)

# V2 imports (current)
from agentforge.core.harness.minimal_context import (
    MinimalContextExecutor,
    TemplateContextBuilder,
)
from agentforge.core.context import CompactionManager
```

## Timeline

| Version | Status | Notes |
|---------|--------|-------|
| v1.x | Active | Text-parsing available |
| v2.0 | Current | Native tools default, text-parsing deprecated |
| v2.x | Planned | Deprecation warnings for V1 methods |
| v3.0 | Future | V1 text-parsing removed |

## Checking Your Code

Run the following to find deprecated imports:

```bash
# Find deprecated imports
grep -r "from.*deprecated import" src/
grep -r "ContextBuilder\|EnhancedContextBuilder" src/ --include="*.py"
grep -r "_parse_action\|run_until_complete" src/ --include="*.py"
```

## FAQ

### Can I still use `execute_step()` for debugging?

Yes, `execute_step()` remains available for single-step debugging. However, for production use, `run_task_native()` is recommended.

### What about thinking/extended thinking?

Native tools fully support extended thinking via `ThinkingConfig`:

```python
from agentforge.core.llm import ThinkingConfig

thinking = ThinkingConfig(enabled=True, budget_tokens=8000)
result = executor.run_task_native(
    task_id=task_id,
    domain_context=context,
    llm_client=client,
    # Thinking is configured in executor.config.defaults
)
```

### Are custom action executors still supported?

Yes, register them with both the executor and native tool executor:

```python
executor.register_action("my_action", my_handler)
# This automatically registers with native_tool_executor too
```

## Support

If you encounter issues during migration:

1. Check the [test examples](../tests/unit/harness/test_executor.py)
2. Review [native tool executor](../src/agentforge/core/harness/minimal_context/native_tool_executor.py)
3. File an issue with the `migration` label
