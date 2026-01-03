## ✅ AgentForge Conformance Report

### Summary

| Metric | Value |
|--------|-------|
| Mode | full |
| Files Checked | 0 |
| Checks Run | 158 |
| Total Violations | 4705 |
| Errors | 0 |
| Warnings | 392 |
| Duration | 18.78s |

### All Violations

<details>
<summary>View all 4705 violations in 414 files</summary>

**`<unknown>`** (4 violations)

- 🟡 **require-package-json** at `file`
  - Required file not found: 'package.json'
  - 💡 *Run 'npm init' to create package.json*
- 🟡 **require-csproj** at `file`
  - Required file not found: '**/*.csproj'
  - 💡 *Create a .csproj file for the project*
- 🟡 **require-csproj** at `file`
  - Required file not found: '**/*.csproj'
  - 💡 *Create a .csproj file for the project*
- 🟡 **require-package-json** at `file`
  - Required file not found: 'package.json'
  - 💡 *Run 'npm init' to create package.json*

**`docs/design/specs/agent-harness/agent_monitor_spec.yaml`** (2 violations)

- 🔵 **file-structure** at `file`
  - Spec-like file outside .agentforge/specs/
  - 💡 *Move spec files to .agentforge/specs/*
- 🔵 **file-structure** at `file`
  - Spec-like file outside .agentforge/specs/
  - 💡 *Move spec files to .agentforge/specs/*

**`docs/design/specs/agent-harness/agent_orchestrator_spec.yaml`** (2 violations)

- 🔵 **file-structure** at `file`
  - Spec-like file outside .agentforge/specs/
  - 💡 *Move spec files to .agentforge/specs/*
- 🔵 **file-structure** at `file`
  - Spec-like file outside .agentforge/specs/
  - 💡 *Move spec files to .agentforge/specs/*

**`docs/design/specs/agent-harness/human_escalation_spec.yaml`** (2 violations)

- 🔵 **file-structure** at `file`
  - Spec-like file outside .agentforge/specs/
  - 💡 *Move spec files to .agentforge/specs/*
- 🔵 **file-structure** at `file`
  - Spec-like file outside .agentforge/specs/
  - 💡 *Move spec files to .agentforge/specs/*

**`docs/design/specs/agent-harness/memory_system_spec.yaml`** (2 violations)

- 🔵 **file-structure** at `file`
  - Spec-like file outside .agentforge/specs/
  - 💡 *Move spec files to .agentforge/specs/*
- 🔵 **file-structure** at `file`
  - Spec-like file outside .agentforge/specs/
  - 💡 *Move spec files to .agentforge/specs/*

**`docs/design/specs/agent-harness/minimal_context_architecture_spec.yaml`** (2 violations)

- 🔵 **file-structure** at `file`
  - Spec-like file outside .agentforge/specs/
  - 💡 *Move spec files to .agentforge/specs/*
- 🔵 **file-structure** at `file`
  - Spec-like file outside .agentforge/specs/
  - 💡 *Move spec files to .agentforge/specs/*

**`docs/design/specs/agent-harness/recovery_strategies_spec.yaml`** (2 violations)

- 🔵 **file-structure** at `file`
  - Spec-like file outside .agentforge/specs/
  - 💡 *Move spec files to .agentforge/specs/*
- 🔵 **file-structure** at `file`
  - Spec-like file outside .agentforge/specs/
  - 💡 *Move spec files to .agentforge/specs/*

**`docs/design/specs/agent-harness/tool_selector_spec.yaml`** (2 violations)

- 🔵 **file-structure** at `file`
  - Spec-like file outside .agentforge/specs/
  - 💡 *Move spec files to .agentforge/specs/*
- 🔵 **file-structure** at `file`
  - Spec-like file outside .agentforge/specs/
  - 💡 *Move spec files to .agentforge/specs/*

**`docs/specs/chunk3-conformance/specification.yaml`** (2 violations)

- 🔵 **file-structure** at `file`
  - Spec-like file outside .agentforge/specs/
  - 💡 *Move spec files to .agentforge/specs/*
- 🔵 **file-structure** at `file`
  - Spec-like file outside .agentforge/specs/
  - 💡 *Move spec files to .agentforge/specs/*

**`docs/specs/chunk4-brownfield-discovery/specification.yaml`** (2 violations)

- 🔵 **file-structure** at `file`
  - Spec-like file outside .agentforge/specs/
  - 💡 *Move spec files to .agentforge/specs/*
- 🔵 **file-structure** at `file`
  - Spec-like file outside .agentforge/specs/
  - 💡 *Move spec files to .agentforge/specs/*

**`outputs/specification.yaml`** (2 violations)

- 🔵 **file-structure** at `file`
  - Spec-like file outside .agentforge/specs/
  - 💡 *Move spec files to .agentforge/specs/*
- 🔵 **file-structure** at `file`
  - Spec-like file outside .agentforge/specs/
  - 💡 *Move spec files to .agentforge/specs/*

**`run_contract.py`** (10 violations)

- 🔵 **single-responsibility-modules** at `L49`
  - Class 'ContractRunner' has 11 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **default-result-return-types** at `L58`
  - Method '_load_project_context' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L66`
  - Method 'load_contract' returns 'Dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L75`
  - Method '_build_system_message' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L80`
  - Method '_should_include_section' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L88`
  - Method '_build_user_message' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L98`
  - Method '_substitute_variables' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L107`
  - Method 'assemble_prompt' returns 'Dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L155`
  - Method 'save_prompt' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L175`
  - Method 'save_output' returns 'Path', expected pattern 'Result|Either|Success|Failure'

**`schemas/specification.schema.yaml`** (2 violations)

- 🔵 **file-structure** at `file`
  - Spec-like file outside .agentforge/specs/
  - 💡 *Move spec files to .agentforge/specs/*
- 🔵 **file-structure** at `file`
  - Spec-like file outside .agentforge/specs/
  - 💡 *Move spec files to .agentforge/specs/*

**`src/agentforge/__main__.py`** (3 violations)

- 🔵 **cli-has-version** at `file`
  - Required pattern not found: '@click\.version_option|--version|version_callback'
  - 💡 *Add @click.version_option() to main command*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/cli/__init__.py`** (1 violations)

- 🔵 **cli-proper-exit-codes** at `file`
  - Required pattern not found: 'sys\.exit\s*\(\s*[012]\s*\)|raise\s+(SystemExit|click\.Abort|typer\.Abort)'
  - 💡 *Use sys.exit(0) for success, sys.exit(1) for errors*

**`src/agentforge/cli/click_commands/__init__.py`** (1 violations)

- 🔵 **cli-proper-exit-codes** at `file`
  - Required pattern not found: 'sys\.exit\s*\(\s*[012]\s*\)|raise\s+(SystemExit|click\.Abort|typer\.Abort)'
  - 💡 *Use sys.exit(0) for success, sys.exit(1) for errors*

**`src/agentforge/cli/click_commands/agent.py`** (3 violations)

- 🔵 **cli-proper-exit-codes** at `file`
  - Required pattern not found: 'sys\.exit\s*\(\s*[012]\s*\)|raise\s+(SystemExit|click\.Abort|typer\.Abort)'
  - 💡 *Use sys.exit(0) for success, sys.exit(1) for errors*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/cli/click_commands/bridge.py`** (4 violations)

- 🟡 **max-parameter-count** at `L47`
  - Function 'generate' has 8 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🔵 **cli-proper-exit-codes** at `file`
  - Required pattern not found: 'sys\.exit\s*\(\s*[012]\s*\)|raise\s+(SystemExit|click\.Abort|typer\.Abort)'
  - 💡 *Use sys.exit(0) for success, sys.exit(1) for errors*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/cli/click_commands/ci.py`** (4 violations)

- 🟡 **max-parameter-count** at `L51`
  - Function 'ci_run' has 16 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🔵 **cli-proper-exit-codes** at `file`
  - Required pattern not found: 'sys\.exit\s*\(\s*[012]\s*\)|raise\s+(SystemExit|click\.Abort|typer\.Abort)'
  - 💡 *Use sys.exit(0) for success, sys.exit(1) for errors*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/cli/click_commands/config.py`** (5 violations)

- 🟡 **max-parameter-count** at `L54`
  - Function 'config_set' has 6 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🔵 **cli-proper-exit-codes** at `file`
  - Required pattern not found: 'sys\.exit\s*\(\s*[012]\s*\)|raise\s+(SystemExit|click\.Abort|typer\.Abort)'
  - 💡 *Use sys.exit(0) for success, sys.exit(1) for errors*
- 🔵 **cli-config-from-env** at `file`
  - Required pattern not found: '(envvar\s*=|os\.environ|getenv)'
  - 💡 *Add envvar parameter: @click.option('--api-key', envvar='API_KEY')*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/cli/click_commands/conformance.py`** (4 violations)

- 🟡 **max-parameter-count** at `L115`
  - Function 'violations_list' has 7 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🔵 **cli-proper-exit-codes** at `file`
  - Required pattern not found: 'sys\.exit\s*\(\s*[012]\s*\)|raise\s+(SystemExit|click\.Abort|typer\.Abort)'
  - 💡 *Use sys.exit(0) for success, sys.exit(1) for errors*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/cli/click_commands/contracts.py`** (7 violations)

- 🟡 **max-parameter-count** at `L42`
  - Function 'contracts_list' has 6 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🟡 **max-parameter-count** at `L82`
  - Function 'contracts_check' has 8 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🟡 **max-parameter-count** at `L165`
  - Function 'contracts_verify_ops' has 7 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🟡 **max-parameter-count** at `L316`
  - Function 'exemptions_add' has 8 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L250`
  - Method '_report_to_dict' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/cli/click_commands/discover.py`** (4 violations)

- 🟡 **max-parameter-count** at `L32`
  - Function 'discover' has 11 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🔵 **cli-proper-exit-codes** at `file`
  - Required pattern not found: 'sys\.exit\s*\(\s*[012]\s*\)|raise\s+(SystemExit|click\.Abort|typer\.Abort)'
  - 💡 *Use sys.exit(0) for success, sys.exit(1) for errors*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/cli/click_commands/generate.py`** (7 violations)

- 🟡 **max-cyclomatic-complexity** at `L63`
  - Function 'code' has complexity 15 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L63`
  - Function 'code' has 73 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-parameter-count** at `L63`
  - Function 'code' has 6 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🔵 **cli-proper-exit-codes** at `file`
  - Required pattern not found: 'sys\.exit\s*\(\s*[012]\s*\)|raise\s+(SystemExit|click\.Abort|typer\.Abort)'
  - 💡 *Use sys.exit(0) for success, sys.exit(1) for errors*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L335`
  - Method '_load_existing_code' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/cli/click_commands/pipeline.py`** (13 violations)

- 🟡 **max-cyclomatic-complexity** at `L331`
  - Function 'status' has complexity 12 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L331`
  - Function 'status' has 59 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-nesting-depth** at `L73`
  - Function '_display_result' has nesting depth 7 (max: 4)
  - 💡 *Use early returns, guard clauses, or extract nested logic*
- 🟡 **max-parameter-count** at `L154`
  - Function 'start' has 7 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🟡 **max-file-lines** at `file`
  - File exceeds line limit (682 lines > 500)
  - 💡 *Consider splitting into smaller files*
- 🔵 **single-responsibility-modules** at `L34`
  - Class 'PipelineProgressDisplay' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L48`
  - Method 'display_stage_start' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L54`
  - Method 'display_stage_complete' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L58`
  - Method 'display_stage_failed' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L62`
  - Method 'display_escalation' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L73`
  - Method '_display_result' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/cli/click_commands/spec.py`** (6 violations)

- 🟡 **max-parameter-count** at `L79`
  - Function 'draft' has 6 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🟡 **max-parameter-count** at `L131`
  - Function 'revise' has 8 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🟡 **max-parameter-count** at `L159`
  - Function 'adapt' has 8 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🔵 **cli-proper-exit-codes** at `file`
  - Required pattern not found: 'sys\.exit\s*\(\s*[012]\s*\)|raise\s+(SystemExit|click\.Abort|typer\.Abort)'
  - 💡 *Use sys.exit(0) for success, sys.exit(1) for errors*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/cli/click_commands/tdflow.py`** (3 violations)

- 🔵 **cli-proper-exit-codes** at `file`
  - Required pattern not found: 'sys\.exit\s*\(\s*[012]\s*\)|raise\s+(SystemExit|click\.Abort|typer\.Abort)'
  - 💡 *Use sys.exit(0) for success, sys.exit(1) for errors*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/cli/click_commands/utility.py`** (5 violations)

- 🟡 **max-parameter-count** at `L32`
  - Function 'context' has 11 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🟡 **max-parameter-count** at `L68`
  - Function 'verify' has 8 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🔵 **cli-proper-exit-codes** at `file`
  - Required pattern not found: 'sys\.exit\s*\(\s*[012]\s*\)|raise\s+(SystemExit|click\.Abort|typer\.Abort)'
  - 💡 *Use sys.exit(0) for success, sys.exit(1) for errors*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/cli/click_commands/workspace.py`** (5 violations)

- 🟡 **max-parameter-count** at `L37`
  - Function 'workspace_init' has 8 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🟡 **max-parameter-count** at `L81`
  - Function 'workspace_add_repo' has 9 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🔵 **cli-proper-exit-codes** at `file`
  - Required pattern not found: 'sys\.exit\s*\(\s*[012]\s*\)|raise\s+(SystemExit|click\.Abort|typer\.Abort)'
  - 💡 *Use sys.exit(0) for success, sys.exit(1) for errors*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/cli/commands/__init__.py`** (2 violations)

- 🔵 **cli-proper-exit-codes** at `file`
  - Required pattern not found: 'sys\.exit\s*\(\s*[012]\s*\)|raise\s+(SystemExit|click\.Abort|typer\.Abort)'
  - 💡 *Use sys.exit(0) for success, sys.exit(1) for errors*
- 🔵 **cli-proper-exit-codes** at `file`
  - Required pattern not found: 'sys\.exit\s*\(\s*[012]\s*\)|raise\s+(SystemExit|click\.Abort|typer\.Abort)'
  - 💡 *Use sys.exit(0) for success, sys.exit(1) for errors*

**`src/agentforge/cli/commands/agent.py`** (23 violations)

- 🟡 **max-cyclomatic-complexity** at `L116`
  - Function 'run_status' has complexity 14 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L374`
  - Function 'run_fix_violation' has 87 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L491`
  - Function 'run_fix_violations_batch' has 71 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-file-lines** at `file`
  - File exceeds line limit (627 lines > 500)
  - 💡 *Consider splitting into smaller files*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L56`
  - Method '_get_current_session_id' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L64`
  - Method '_set_current_session_id' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L71`
  - Method '_clear_current_session' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L78`
  - Method 'run_start' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L116`
  - Method 'run_status' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L154`
  - Method 'run_resume' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L173`
  - Method 'run_pause' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L191`
  - Method 'run_stop' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L213`
  - Method 'run_step' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L240`
  - Method 'run_until_complete' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L267`
  - Method 'run_list' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L326`
  - Method 'run_history' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L355`
  - Method 'run_cleanup' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L374`
  - Method 'run_fix_violation' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L491`
  - Method 'run_fix_violations_batch' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L583`
  - Method 'run_approve_commit' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L610`
  - Method 'run_list_violations' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/cli/commands/bridge.py`** (6 violations)

- 🟡 **max-cyclomatic-complexity** at `L17`
  - Function 'run_bridge_generate' has complexity 13 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-cyclomatic-complexity** at `L145`
  - Function 'run_bridge_mappings' has complexity 11 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L17`
  - Function 'run_bridge_generate' has 65 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-parameter-count** at `L17`
  - Function 'run_bridge_generate' has 8 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/cli/commands/ci.py`** (227 violations)

- 🟡 **max-cyclomatic-complexity** at `L187`
  - Function 'run_baseline_compare' has complexity 12 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-cyclomatic-complexity** at `L459`
  - Function 'run_warnings_list' has complexity 16 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L30`
  - Function 'run_ci_check' has 53 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L187`
  - Function 'run_baseline_compare' has 51 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-file-lines** at `file`
  - File exceeds line limit (520 lines > 500)
  - 💡 *Consider splitting into smaller files*
- 🔵 **use-click-echo** at `L75`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L85`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L89`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L93`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L97`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L107`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L113`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L114`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L115`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L116`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L117`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L118`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L119`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L120`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L121`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L124`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L126`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L128`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L130`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L132`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L134`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L135`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L136`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L137`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L138`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L141`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L142`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L144`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L146`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L147`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L157`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L166`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L182`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L184`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L194`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L203`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L214`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L226`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L228`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L229`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L230`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L231`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L232`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L233`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L234`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L237`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L239`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L241`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L244`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L246`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L248`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L259`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L262`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L263`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L264`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L265`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L266`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L268`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L270`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L271`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L273`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L275`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L276`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L279`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L298`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L299`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L308`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L309`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L310`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L311`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L312`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L313`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L321`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L322`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L331`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L332`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L333`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L334`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L335`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L336`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L386`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L398`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L399`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L401`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L402`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L424`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L425`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L426`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L427`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L428`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L429`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L431`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L439`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L445`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L451`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L452`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L456`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L465`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L466`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L503`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L504`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L506`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L510`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L517`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L519`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L75`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L85`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L89`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L93`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L97`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L107`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L113`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L114`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L115`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L116`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L117`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L118`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L119`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L120`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L121`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L124`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L126`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L128`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L130`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L132`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L134`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L135`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L136`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L137`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L138`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L141`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L142`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L144`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L146`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L147`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L157`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L166`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L182`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L184`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L194`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L203`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L214`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L226`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L228`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L229`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L230`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L231`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L232`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L233`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L234`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L237`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L239`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L241`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L244`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L246`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L248`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L259`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L262`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L263`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L264`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L265`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L266`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L268`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L270`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L271`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L273`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L275`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L276`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L279`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L298`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L299`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L308`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L309`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L310`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L311`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L312`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L313`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L321`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L322`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L331`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L332`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L333`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L334`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L335`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L336`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L386`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L398`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L399`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L401`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L402`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L424`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L425`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L426`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L427`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L428`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L429`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L431`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L439`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L445`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L451`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L452`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L456`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L465`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L466`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L503`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L504`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L506`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L510`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L517`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **use-click-echo** at `L519`
  - Forbidden pattern found: 'print('
  - 💡 *Use click.echo() or rich.print() for CLI output*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L30`
  - Method 'run_ci_check' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L150`
  - Method 'run_baseline_save' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L187`
  - Method 'run_baseline_compare' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L251`
  - Method 'run_baseline_stats' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L282`
  - Method 'run_ci_init' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L292`
  - Method '_init_github_workflow' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L316`
  - Method '_init_azure_pipeline' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L380`
  - Method 'run_hooks_install' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L434`
  - Method 'run_hooks_uninstall' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L459`
  - Method 'run_warnings_list' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/cli/commands/config.py`** (4 violations)

- 🔵 **cli-config-from-env** at `file`
  - Required pattern not found: '(envvar\s*=|os\.environ|getenv)'
  - 💡 *Add envvar parameter: @click.option('--api-key', envvar='API_KEY')*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L177`
  - Method '_get_tier_section' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/cli/commands/conformance.py`** (2 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/cli/commands/conformance_formatters.py`** (4 violations)

- 🔵 **cli-proper-exit-codes** at `file`
  - Required pattern not found: 'sys\.exit\s*\(\s*[012]\s*\)|raise\s+(SystemExit|click\.Abort|typer\.Abort)'
  - 💡 *Use sys.exit(0) for success, sys.exit(1) for errors*
- 🔵 **cli-proper-exit-codes** at `file`
  - Required pattern not found: 'sys\.exit\s*\(\s*[012]\s*\)|raise\s+(SystemExit|click\.Abort|typer\.Abort)'
  - 💡 *Use sys.exit(0) for success, sys.exit(1) for errors*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/cli/commands/context.py`** (4 violations)

- 🔵 **cli-proper-exit-codes** at `file`
  - Required pattern not found: 'sys\.exit\s*\(\s*[012]\s*\)|raise\s+(SystemExit|click\.Abort|typer\.Abort)'
  - 💡 *Use sys.exit(0) for success, sys.exit(1) for errors*
- 🔵 **cli-proper-exit-codes** at `file`
  - Required pattern not found: 'sys\.exit\s*\(\s*[012]\s*\)|raise\s+(SystemExit|click\.Abort|typer\.Abort)'
  - 💡 *Use sys.exit(0) for success, sys.exit(1) for errors*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/cli/commands/contracts.py`** (4 violations)

- 🟡 **max-cyclomatic-complexity** at `L58`
  - Function 'run_contracts_fix' has complexity 18 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L58`
  - Function 'run_contracts_fix' has 58 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/cli/commands/discover.py`** (6 violations)

- 🟡 **max-cyclomatic-complexity** at `L40`
  - Function '_run_single_zone_discovery' has complexity 12 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-cyclomatic-complexity** at `L99`
  - Function '_run_multi_zone_discovery' has complexity 13 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-cyclomatic-complexity** at `L210`
  - Function '_output_multi_zone_summary' has complexity 14 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-cyclomatic-complexity** at `L282`
  - Function '_output_summary' has complexity 16 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/cli/commands/revision.py`** (10 violations)

- 🔵 **cli-proper-exit-codes** at `file`
  - Required pattern not found: 'sys\.exit\s*\(\s*[012]\s*\)|raise\s+(SystemExit|click\.Abort|typer\.Abort)'
  - 💡 *Use sys.exit(0) for success, sys.exit(1) for errors*
- 🔵 **cli-proper-exit-codes** at `file`
  - Required pattern not found: 'sys\.exit\s*\(\s*[012]\s*\)|raise\s+(SystemExit|click\.Abort|typer\.Abort)'
  - 💡 *Use sys.exit(0) for success, sys.exit(1) for errors*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L74`
  - Method 'create_revision_session' returns 'dict | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L123`
  - Method '_build_issues_list' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L144`
  - Method '_build_issue_entry' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L157`
  - Method '_generate_options' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L213`
  - Method '_handle_issue_interactive' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L316`
  - Method '_evaluate_autonomously' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/cli/commands/revision_apply.py`** (9 violations)

- 🔵 **cli-proper-exit-codes** at `file`
  - Required pattern not found: 'sys\.exit\s*\(\s*[012]\s*\)|raise\s+(SystemExit|click\.Abort|typer\.Abort)'
  - 💡 *Use sys.exit(0) for success, sys.exit(1) for errors*
- 🔵 **cli-proper-exit-codes** at `file`
  - Required pattern not found: 'sys\.exit\s*\(\s*[012]\s*\)|raise\s+(SystemExit|click\.Abort|typer\.Abort)'
  - 💡 *Use sys.exit(0) for success, sys.exit(1) for errors*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L71`
  - Method '_build_revision_lists' returns 'tuple', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L99`
  - Method '_build_revision_notes' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L170`
  - Method '_build_apply_instructions' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L197`
  - Method '_execute_apply_revision' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L226`
  - Method '_increment_version' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/cli/commands/spec.py`** (12 violations)

- 🟡 **max-cyclomatic-complexity** at `L251`
  - Function '_extract_locations_from_analysis' has complexity 12 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L334`
  - Function 'run_draft' has 62 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-nesting-depth** at `L251`
  - Function '_extract_locations_from_analysis' has nesting depth 7 (max: 4)
  - 💡 *Use early returns, guard clauses, or extract nested logic*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L73`
  - Method '_load_conversation_history' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L137`
  - Method '_retrieve_context' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L162`
  - Method '_load_optional_file' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L167`
  - Method '_get_code_context' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L251`
  - Method '_extract_locations_from_analysis' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L301`
  - Method '_handle_draft_escalation' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L417`
  - Method '_load_spec_content' returns 'tuple', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/cli/commands/spec_adapt.py`** (12 violations)

- 🟡 **max-cyclomatic-complexity** at `L234`
  - Function 'run_adapt' has complexity 12 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L234`
  - Function 'run_adapt' has 99 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L33`
  - Method '_load_external_spec' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L41`
  - Method '_load_codebase_profile' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L53`
  - Method '_get_existing_spec_ids' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L72`
  - Method '_build_adapt_inputs' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L87`
  - Method '_save_adapted_spec' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L108`
  - Method '_extract_target_locations' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L134`
  - Method '_analyze_placement' returns 'PlacementDecision', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L173`
  - Method '_handle_escalation' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/cli/commands/tdflow.py`** (13 violations)

- 🔵 **cli-proper-exit-codes** at `file`
  - Required pattern not found: 'sys\.exit\s*\(\s*[012]\s*\)|raise\s+(SystemExit|click\.Abort|typer\.Abort)'
  - 💡 *Use sys.exit(0) for success, sys.exit(1) for errors*
- 🔵 **cli-proper-exit-codes** at `file`
  - Required pattern not found: 'sys\.exit\s*\(\s*[012]\s*\)|raise\s+(SystemExit|click\.Abort|typer\.Abort)'
  - 💡 *Use sys.exit(0) for success, sys.exit(1) for errors*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L25`
  - Method '_get_generator' returns 'Optional["GenerationEngine"]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L43`
  - Method 'run_start' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L89`
  - Method 'run_red' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L127`
  - Method 'run_green' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L167`
  - Method 'run_refactor' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L205`
  - Method 'run_verify' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L238`
  - Method 'run_status' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L276`
  - Method 'run_resume' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L290`
  - Method 'run_list' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/cli/commands/verify.py`** (2 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/cli/commands/workspace.py`** (3 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L370`
  - Method '_filter_repos' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/cli/core.py`** (15 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L56`
  - Method '_extract_text_from_content' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L68`
  - Method '_extract_from_messages' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L82`
  - Method '_extract_from_content_blocks' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L94`
  - Method '_try_parse_result_format' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L106`
  - Method '_try_parse_direct_fields' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L115`
  - Method '_parse_claude_json_response' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L141`
  - Method 'call_claude_code' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L196`
  - Method 'call_anthropic_api' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L241`
  - Method '_find_yaml_in_code_blocks' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L257`
  - Method '_is_prose_line' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L263`
  - Method '_extract_yaml_lines' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L282`
  - Method 'extract_yaml_from_response' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L298`
  - Method 'execute_contract' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/cli/helpers.py`** (10 violations)

- 🔵 **cli-proper-exit-codes** at `file`
  - Required pattern not found: 'sys\.exit\s*\(\s*[012]\s*\)|raise\s+(SystemExit|click\.Abort|typer\.Abort)'
  - 💡 *Use sys.exit(0) for success, sys.exit(1) for errors*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L15`
  - Method 'build_contracts_output' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L55`
  - Method '_get_severity_icon' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L62`
  - Method '_print_failed_check' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L72`
  - Method 'print_contracts_text' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L94`
  - Method 'print_banner' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L102`
  - Method 'print_section' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L110`
  - Method 'format_check_result' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/cli/main.py`** (6 violations)

- 🔵 **max-imports** at `L1`
  - File has 38 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **max-imports** at `L1`
  - File has 38 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **max-imports** at `L1`
  - File has 38 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **max-imports** at `L1`
  - File has 38 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/cli/parser.py`** (3 violations)

- 🔵 **cli-proper-exit-codes** at `file`
  - Required pattern not found: 'sys\.exit\s*\(\s*[012]\s*\)|raise\s+(SystemExit|click\.Abort|typer\.Abort)'
  - 💡 *Use sys.exit(0) for success, sys.exit(1) for errors*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/cli/render.py`** (17 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L14`
  - Method '_render_metadata' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L28`
  - Method '_render_overview' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L77`
  - Method '_render_acceptance_criteria' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L97`
  - Method '_render_requirements' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L132`
  - Method '_render_entity' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L182`
  - Method '_render_entities' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L197`
  - Method '_render_interface_response' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L208`
  - Method '_render_single_interface' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L222`
  - Method '_render_interfaces' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L233`
  - Method '_render_workflow' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L262`
  - Method '_render_workflows' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L275`
  - Method '_render_error_handling' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L294`
  - Method '_render_testing_notes' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L323`
  - Method '_render_glossary' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L337`
  - Method 'render_spec_to_markdown' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/analyze_structure.py`** (12 violations)

- 🔵 **single-responsibility-modules** at `L92`
  - Class 'StructureAnalyzer' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L80`
  - Method 'to_dict' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L83`
  - Method 'to_yaml' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L87`
  - Method 'to_json' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L147`
  - Method '_extract_function_calls' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L158`
  - Method '_truncate_docstring' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L183`
  - Method '_extract_function_prefix' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L208`
  - Method 'identify_logical_groups' returns 'list[LogicalGroup]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L229`
  - Method 'suggest_splits' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L249`
  - Method 'analyze_file' returns 'FileAnalysis', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/audit/audit_manager.py`** (29 violations)

- 🟡 **max-function-length** at `L139`
  - Function 'spawn_child_thread' has 51 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L247`
  - Function 'log_llm_interaction' has 104 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-parameter-count** at `L139`
  - Function 'spawn_child_thread' has 9 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🟡 **max-parameter-count** at `L247`
  - Function 'log_llm_interaction' has 17 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🟡 **max-class-size** at `L76`
  - Class 'AuditManager' has 21 methods (max: 20)
  - 💡 *Consider splitting into multiple classes with single responsibilities*
- 🟡 **max-file-lines** at `file`
  - File exceeds line limit (552 lines > 500)
  - 💡 *Consider splitting into smaller files*
- 🟡 **no-god-classes** at `L76`
  - Class 'AuditManager' has 21 methods (max: 15)
  - 💡 *Split large classes using composition or inheritance*
- 🔵 **single-responsibility-modules** at `L76`
  - Class 'AuditManager' has 21 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L106`
  - Method 'create_root_thread' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L139`
  - Method 'spawn_child_thread' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L199`
  - Method 'spawn_parallel_group' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L247`
  - Method 'log_llm_interaction' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L362`
  - Method 'log_human_interaction' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L396`
  - Method 'complete_thread' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L453`
  - Method 'get_thread_info' returns 'ThreadInfo | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L457`
  - Method 'get_thread_tree' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L461`
  - Method 'get_ancestry' returns 'list[ThreadInfo]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L465`
  - Method 'get_transactions' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L470`
  - Method 'get_transaction' returns 'TransactionRecord | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L475`
  - Method 'get_conversation_turns' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L480`
  - Method 'get_conversation_content' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L485`
  - Method 'list_root_threads' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L490`
  - Method 'get_summary' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L527`
  - Method '_get_logger' returns 'TransactionLogger', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L533`
  - Method '_get_archive' returns 'ConversationArchive', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L540`
  - Method '_get_chain' returns 'IntegrityChain', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L547`
  - Method '_generate_thread_id' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/audit/context_frame.py`** (27 violations)

- 🟡 **max-cyclomatic-complexity** at `L313`
  - Function 'to_dict' has complexity 12 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-parameter-count** at `L438`
  - Function 'with_llm_interaction' has 10 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🟡 **max-file-lines** at `file`
  - File exceeds line limit (600 lines > 500)
  - 💡 *Consider splitting into smaller files*
- 🔵 **single-responsibility-modules** at `L370`
  - Class 'ContextFrameBuilder' has 12 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L72`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L96`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L128`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L138`
  - Method 'is_valid' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L170`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L193`
  - Method 'to_markdown' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L242`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L255`
  - Method 'is_valid' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L313`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L362`
  - Method 'is_valid' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L386`
  - Method 'with_type' returns '"ContextFrameBuilder"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L391`
  - Method 'with_stage' returns '"ContextFrameBuilder"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L400`
  - Method 'with_input_context' returns '"ContextFrameBuilder"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L438`
  - Method 'with_llm_interaction' returns '"ContextFrameBuilder"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L466`
  - Method 'with_parsed_artifact' returns '"ContextFrameBuilder"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L513`
  - Method 'with_output_context' returns '"ContextFrameBuilder"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L544`
  - Method 'with_context_delta' returns '"ContextFrameBuilder"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L549`
  - Method 'with_duration' returns '"ContextFrameBuilder"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L554`
  - Method 'with_integrity' returns '"ContextFrameBuilder"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L562`
  - Method 'build' returns 'ContextFrame', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L566`
  - Method '_validate_against_schema' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/audit/conversation_archive.py`** (19 violations)

- 🟡 **max-cyclomatic-complexity** at `L134`
  - Function 'to_markdown' has complexity 11 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L134`
  - Function 'to_markdown' has 54 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L224`
  - Function 'archive_turn' has 63 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-parameter-count** at `L224`
  - Function 'archive_turn' has 14 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🔵 **single-responsibility-modules** at `L199`
  - Class 'ConversationArchive' has 10 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L45`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L97`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L134`
  - Method 'to_markdown' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L224`
  - Method 'archive_turn' returns 'ConversationTurn', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L298`
  - Method 'get_turn' returns 'ConversationTurn | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L307`
  - Method 'get_turn_content' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L314`
  - Method 'list_turns' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L321`
  - Method 'get_summary' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L328`
  - Method 'get_total_tokens' returns 'dict[str, int]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L349`
  - Method '_get_next_sequence' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L364`
  - Method '_update_index' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L400`
  - Method '_dict_to_turn' returns 'ConversationTurn', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/audit/frame_logger.py`** (26 violations)

- 🟡 **max-function-length** at `L104`
  - Function 'log_stage_frame' has 75 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L197`
  - Function 'log_agent_step' has 56 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-parameter-count** at `L104`
  - Function 'log_stage_frame' has 17 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🟡 **max-parameter-count** at `L197`
  - Function 'log_agent_step' has 12 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🟡 **max-file-lines** at `file`
  - File exceeds line limit (571 lines > 500)
  - 💡 *Consider splitting into smaller files*
- 🟡 **no-god-classes** at `L61`
  - Class 'FrameLogger' has 19 methods (max: 15)
  - 💡 *Split large classes using composition or inheritance*
- 🔵 **single-responsibility-modules** at `L61`
  - Class 'FrameLogger' has 19 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L91`
  - Method 'register_schemas' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L100`
  - Method 'get_schema' returns 'dict[str, Any] | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L104`
  - Method 'log_stage_frame' returns 'ContextFrame', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L197`
  - Method 'log_agent_step' returns 'ContextFrame', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L266`
  - Method 'log_human_interaction' returns 'ContextFrame', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L316`
  - Method 'log_spawn' returns 'ContextFrame', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L356`
  - Method 'get_frame' returns 'ContextFrame | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L365`
  - Method 'list_frames' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L372`
  - Method 'get_frame_content' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L379`
  - Method 'get_validation_summary' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L419`
  - Method '_persist_frame' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L452`
  - Method '_resolve_schema' returns 'dict[str, Any] | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L479`
  - Method '_get_required_fields' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L485`
  - Method '_get_next_sequence' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L499`
  - Method '_dict_to_frame' returns 'ContextFrame', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L550`
  - Method '_dict_to_validated_context' returns 'ValidatedContext', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L561`
  - Method '_dict_to_parsed_artifact' returns 'ParsedArtifact', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/audit/integrity_chain.py`** (14 violations)

- 🔵 **single-responsibility-modules** at `L99`
  - Class 'IntegrityChain' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L36`
  - Method 'compute_hash' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L68`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L88`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L126`
  - Method 'append' returns 'ChainBlock', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L157`
  - Method 'get_last_hash' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L176`
  - Method 'get_chain' returns 'list[ChainBlock]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L254`
  - Method 'get_block' returns 'ChainBlock | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L261`
  - Method 'get_proof' returns 'dict[str, Any] | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L294`
  - Method '_append_to_sig' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L299`
  - Method '_append_to_yaml' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L336`
  - Method 'load_transaction' returns 'dict[str, Any] | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/audit/thread_correlator.py`** (29 violations)

- 🟡 **max-cyclomatic-complexity** at `L136`
  - Function 'to_dict' has complexity 11 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L210`
  - Function 'create_thread' has 61 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-parameter-count** at `L210`
  - Function 'create_thread' has 9 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🟡 **max-parameter-count** at `L290`
  - Function 'complete_thread' has 6 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🟡 **max-file-lines** at `file`
  - File exceeds line limit (562 lines > 500)
  - 💡 *Consider splitting into smaller files*
- 🟡 **no-god-classes** at `L181`
  - Class 'ThreadCorrelator' has 19 methods (max: 15)
  - 💡 *Split large classes using composition or inheritance*
- 🔵 **single-responsibility-modules** at `L181`
  - Class 'ThreadCorrelator' has 19 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L78`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L136`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L210`
  - Method 'create_thread' returns 'ThreadInfo', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L282`
  - Method 'start_thread' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L290`
  - Method 'complete_thread' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L326`
  - Method 'get_thread' returns 'ThreadInfo | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L335`
  - Method 'get_children' returns 'list[ThreadInfo]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L348`
  - Method 'get_thread_tree' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L360`
  - Method 'get_parallel_group' returns 'list[ThreadInfo]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L375`
  - Method 'create_parallel_group' returns 'list[ThreadInfo]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L418`
  - Method 'get_ancestry' returns 'list[ThreadInfo]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L436`
  - Method '_save_thread_manifest' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L447`
  - Method '_add_child_to_parent' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L455`
  - Method '_log_spawn' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L467`
  - Method '_build_tree' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L478`
  - Method '_update_index' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L502`
  - Method '_update_lineage_tree' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L514`
  - Method '_load_index' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L526`
  - Method '_save_index' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L534`
  - Method '_dict_to_thread_info' returns 'ThreadInfo', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/audit/transaction_logger.py`** (19 violations)

- 🟡 **max-cyclomatic-complexity** at `L114`
  - Function 'to_dict' has complexity 16 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L114`
  - Function 'to_dict' has 62 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L279`
  - Function 'log_llm_call' has 53 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-parameter-count** at `L279`
  - Function 'log_llm_call' has 13 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🟡 **max-file-lines** at `file`
  - File exceeds line limit (524 lines > 500)
  - 💡 *Consider splitting into smaller files*
- 🔵 **single-responsibility-modules** at `L197`
  - Class 'TransactionLogger' has 11 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L114`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L228`
  - Method 'log_transaction' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L279`
  - Method 'log_llm_call' returns 'TransactionRecord', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L336`
  - Method 'log_spawn' returns 'TransactionRecord', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L366`
  - Method 'log_human_interaction' returns 'TransactionRecord', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L399`
  - Method 'get_transaction' returns 'TransactionRecord | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L408`
  - Method 'list_transactions' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L416`
  - Method 'get_full_llm_content' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L423`
  - Method '_get_next_sequence' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L438`
  - Method '_format_llm_content' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L472`
  - Method '_dict_to_record' returns 'TransactionRecord', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/bridge/conflict_resolver.py`** (12 violations)

- 🟡 **max-nesting-depth** at `L160`
  - Function 'resolve_conflicts' has nesting depth 7 (max: 4)
  - 💡 *Use early returns, guard clauses, or extract nested logic*
- 🔵 **single-responsibility-modules** at `L25`
  - Class 'ConflictResolver' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L56`
  - Method 'load_existing_contracts' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L88`
  - Method 'detect_conflicts' returns 'list[Conflict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L123`
  - Method '_check_overlapping_scope' returns 'Conflict | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L148`
  - Method '_determine_resolution' returns 'ResolutionStrategy', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L160`
  - Method 'resolve_conflicts' returns 'GeneratedContract', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L217`
  - Method '_generate_unique_id' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L228`
  - Method 'get_existing_check_ids' returns 'set[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L232`
  - Method 'get_existing_contract_names' returns 'set[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/bridge/contract_builder.py`** (12 violations)

- 🟡 **max-function-length** at `L71`
  - Function 'build_contract' has 53 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-parameter-count** at `L71`
  - Function 'build_contract' has 6 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🔵 **single-responsibility-modules** at `L43`
  - Class 'ContractBuilder' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L71`
  - Method 'build_contract' returns 'GeneratedContract', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L138`
  - Method '_group_patterns' returns 'dict[str, float]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L147`
  - Method 'write_contract' returns 'Path | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L183`
  - Method '_build_yaml_content' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L236`
  - Method 'preview_contract' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L248`
  - Method 'get_output_path' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L252`
  - Method 'contract_exists' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/bridge/domain.py`** (28 violations)

- 🔵 **single-responsibility-modules** at `L20`
  - Class 'ConfidenceTier' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L171`
  - Class 'GeneratedContract' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L363`
  - Class 'MappingContext' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L28`
  - Method 'from_score' returns '"ConfidenceTier"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L40`
  - Method 'auto_enable' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L45`
  - Method 'should_generate' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L50`
  - Method 'needs_review' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L91`
  - Method 'resolve_id' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L117`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L155`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L186`
  - Method 'enabled_count' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L190`
  - Method 'disabled_count' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L194`
  - Method 'review_required_count' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L197`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L240`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L268`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L290`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L328`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L378`
  - Method 'is_pattern_detected' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L385`
  - Method 'get_pattern_confidence' returns 'float', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L392`
  - Method 'get_pattern_primary' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L399`
  - Method 'get_pattern_metadata' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L406`
  - Method 'get_layer_paths' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L412`
  - Method 'has_layer' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L417`
  - Method 'get_architecture_style' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L422`
  - Method 'has_framework' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/bridge/mappings/architecture.py`** (9 violations)

- 🟡 **max-function-length** at `L49`
  - Function 'get_templates' has 55 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L36`
  - Method 'matches' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L49`
  - Method 'get_templates' returns 'list[CheckTemplate]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L129`
  - Method 'matches' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L140`
  - Method 'get_templates' returns 'list[CheckTemplate]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L190`
  - Method 'matches' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L195`
  - Method 'get_templates' returns 'list[CheckTemplate]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/bridge/mappings/base.py`** (10 violations)

- 🔵 **single-responsibility-modules** at `L24`
  - Class 'PatternMapping' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L40`
  - Method 'matches' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L47`
  - Method 'get_templates' returns 'List[CheckTemplate]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L64`
  - Method 'matches' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L77`
  - Method 'get_templates' returns 'list[CheckTemplate]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L89`
  - Method 'generate' returns 'list[GeneratedCheck]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L119`
  - Method '_template_to_check' returns 'GeneratedCheck | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L163`
  - Method 'get_info' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/bridge/mappings/conventions.py`** (16 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L32`
  - Method 'matches' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L52`
  - Method 'get_templates' returns 'list[CheckTemplate]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L83`
  - Method 'matches' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L98`
  - Method 'get_templates' returns 'list[CheckTemplate]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L130`
  - Method 'matches' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L140`
  - Method 'get_templates' returns 'list[CheckTemplate]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L190`
  - Method 'matches' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L199`
  - Method 'get_templates' returns 'list[CheckTemplate]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L234`
  - Method 'matches' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L245`
  - Method 'get_templates' returns 'list[CheckTemplate]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L278`
  - Method 'matches' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L287`
  - Method 'get_templates' returns 'list[CheckTemplate]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L318`
  - Method 'matches' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L327`
  - Method 'get_templates' returns 'list[CheckTemplate]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/bridge/mappings/cqrs.py`** (7 violations)

- 🟡 **max-function-length** at `L52`
  - Function 'get_templates' has 63 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L36`
  - Method 'matches' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L52`
  - Method 'get_templates' returns 'list[CheckTemplate]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L130`
  - Method 'matches' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L143`
  - Method 'get_templates' returns 'list[CheckTemplate]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/bridge/mappings/registry.py`** (10 violations)

- 🔵 **single-responsibility-modules** at `L19`
  - Class 'MappingRegistry' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L37`
  - Method 'register' returns 'type[PatternMapping]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L52`
  - Method 'get_all_mappings' returns 'list[PatternMapping]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L62`
  - Method 'get_mappings_for_language' returns 'list[PatternMapping]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L71`
  - Method 'get_mappings_for_pattern' returns 'list[PatternMapping]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L77`
  - Method 'get_mapping_info' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L82`
  - Method 'generate_checks' returns 'list[GeneratedCheck]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L115`
  - Method 'clear' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/bridge/mappings/repository.py`** (6 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L34`
  - Method 'matches' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L40`
  - Method 'get_templates' returns 'list[CheckTemplate]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L96`
  - Method 'matches' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L106`
  - Method 'get_templates' returns 'list[CheckTemplate]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/bridge/orchestrator.py`** (17 violations)

- 🟡 **max-cyclomatic-complexity** at `L200`
  - Function '_generate_report' has complexity 14 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L200`
  - Function '_generate_report' has 65 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **single-responsibility-modules** at `L31`
  - Class 'BridgeOrchestrator' has 14 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L84`
  - Method '_verbose' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L89`
  - Method '_filter_zones' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L98`
  - Method '_process_zones' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L110`
  - Method '_write_contracts' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L120`
  - Method 'generate' returns 'tuple[list[GeneratedContract], GenerationReport]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L162`
  - Method '_handle_conflicts' returns 'GeneratedContract', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L171`
  - Method '_generate_zone_contract' returns 'GeneratedContract | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L200`
  - Method '_generate_report' returns 'GenerationReport', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L278`
  - Method 'preview' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L308`
  - Method 'list_mappings' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L325`
  - Method 'refresh' returns 'tuple[list[GeneratedContract], GenerationReport]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L342`
  - Method 'write_report' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/bridge/profile_loader.py`** (18 violations)

- 🔵 **single-responsibility-modules** at `L26`
  - Class 'ProfileLoader' has 15 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L47`
  - Method 'load' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L81`
  - Method 'profile_path' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L91`
  - Method 'profile_hash' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L96`
  - Method 'profile_generated_at' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L102`
  - Method 'is_multi_zone' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L111`
  - Method 'get_zones' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L128`
  - Method 'get_languages' returns 'list[tuple[str, float]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L151`
  - Method 'get_primary_language' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L170`
  - Method 'create_context' returns 'MappingContext', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L193`
  - Method '_create_single_zone_context' returns 'MappingContext', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L221`
  - Method '_create_zone_context' returns 'MappingContext', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L253`
  - Method '_extract_frameworks' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L268`
  - Method '_extract_frameworks_from_patterns' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L277`
  - Method 'get_all_contexts' returns 'list[MappingContext]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L301`
  - Method 'load_profile' returns 'tuple[ProfileLoader, dict[str, Any]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/builtin_checks.py`** (25 violations)

- 🟡 **max-file-lines** at `file`
  - File exceeds line limit (750 lines > 500)
  - 💡 *Consider splitting into smaller files*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L39`
  - Method 'check_todo_comments' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L75`
  - Method 'check_debug_statements' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L135`
  - Method 'check_file_size' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L170`
  - Method 'check_line_length' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L195`
  - Method 'check_trailing_whitespace' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L220`
  - Method 'check_mixed_line_endings' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L252`
  - Method 'check_hardcoded_secrets' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L307`
  - Method 'check_lineage_metadata' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L372`
  - Method '_validate_spec_component' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L388`
  - Method '_validate_spec_file' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L405`
  - Method 'check_spec_integrity' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L428`
  - Method '_check_component_link' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L451`
  - Method 'check_bidirectional_links' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L473`
  - Method '_check_file_references_spec' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L494`
  - Method '_check_file_placement' returns 'dict | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L509`
  - Method 'check_file_structure' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L548`
  - Method 'check_minimal_context_validation' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L608`
  - Method 'check_layer_imports' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L632`
  - Method 'check_constructor_injection' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L657`
  - Method 'check_domain_purity' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L682`
  - Method 'check_circular_imports' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L747`
  - Method 'list_builtin_checks' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/builtin_checks_architecture.py`** (17 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L62`
  - Method 'check_layer_imports' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L97`
  - Method '_check_class_init' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L121`
  - Method '_check_forbidden_instantiations' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L138`
  - Method '_matches_class_pattern' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L143`
  - Method '_get_init_method' returns 'ast.FunctionDef | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L148`
  - Method 'check_constructor_injection' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L186`
  - Method '_is_forbidden_import' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L191`
  - Method '_check_import_purity' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L204`
  - Method '_check_call_purity' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L216`
  - Method 'check_domain_purity' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L241`
  - Method '_is_local_import' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L247`
  - Method '_record_cycle' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L262`
  - Method '_find_cycles' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L286`
  - Method '_build_import_graph' returns 'dict[str, set[str]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L304`
  - Method 'check_circular_imports' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/builtin_checks_architecture_helpers.py`** (12 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L39`
  - Method 'is_stdlib_or_thirdparty' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L45`
  - Method 'get_relative_path' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L53`
  - Method 'parse_source_safe' returns 'ast.Module | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L62`
  - Method 'get_layer_for_path' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L76`
  - Method 'get_layer_for_import' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L88`
  - Method 'extract_import_names' returns 'list[tuple[str, int]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L97`
  - Method 'get_call_string' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L118`
  - Method 'path_to_module' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L129`
  - Method 'is_type_checking_block' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L136`
  - Method 'create_violation' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/cicd/baseline.py`** (18 violations)

- 🔵 **single-responsibility-modules** at `L26`
  - Class 'BaselineManager' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L195`
  - Class 'GitHelper' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L44`
  - Method 'load' returns 'Baseline | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L61`
  - Method 'save' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L74`
  - Method 'create_from_violations' returns 'Baseline', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L94`
  - Method 'update' returns 'tuple[Baseline, int, int]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L141`
  - Method 'compare' returns 'BaselineComparison', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L160`
  - Method 'exists' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L164`
  - Method 'get_stats' returns 'dict | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L204`
  - Method 'get_changed_files' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L228`
  - Method 'get_merge_base' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L251`
  - Method 'get_current_sha' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L265`
  - Method 'get_current_branch' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L279`
  - Method 'is_git_repo' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L292`
  - Method 'get_repo_root' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L306`
  - Method 'file_exists_at_ref' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/cicd/domain.py`** (41 violations)

- 🟡 **max-file-lines** at `file`
  - File exceeds line limit (611 lines > 500)
  - 💡 *Consider splitting into smaller files*
- 🔵 **single-responsibility-modules** at `L220`
  - Class 'Baseline' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L297`
  - Class 'BaselineComparison' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L404`
  - Class 'CIResult' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L501`
  - Class 'CIConfig' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L38`
  - Method 'description' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L72`
  - Method 'hash' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L84`
  - Method 'to_sarif_result' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L138`
  - Method 'to_junit_testcase' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L180`
  - Method 'from_violation' returns '"BaselineEntry"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L193`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L206`
  - Method 'from_dict' returns '"BaselineEntry"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L233`
  - Method 'contains' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L237`
  - Method 'get_entry' returns 'BaselineEntry | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L241`
  - Method 'add' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L250`
  - Method 'remove' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L258`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L269`
  - Method 'from_dict' returns '"Baseline"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L284`
  - Method 'create_empty' returns '"Baseline"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L311`
  - Method 'introduces_violations' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L316`
  - Method 'net_change' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L326`
  - Method 'has_improvements' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L331`
  - Method 'new_errors' returns 'list[CIViolation]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L336`
  - Method 'new_warnings' returns 'list[CIViolation]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L340`
  - Method 'should_fail' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L355`
  - Method 'should_fail_ratchet' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L368`
  - Method 'compare' returns '"BaselineComparison"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L426`
  - Method 'total_violations' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L431`
  - Method 'error_count' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L436`
  - Method 'warning_count' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L441`
  - Method 'info_count' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L446`
  - Method 'is_success' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L450`
  - Method 'get_violations_by_file' returns 'dict[str, list[CIViolation]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L459`
  - Method 'get_violations_by_check' returns 'dict[str, list[CIViolation]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L468`
  - Method 'to_summary_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L530`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L558`
  - Method 'from_dict' returns '"CIConfig"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L589`
  - Method 'for_github_actions' returns '"CIConfig"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L601`
  - Method 'for_azure_devops' returns '"CIConfig"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/cicd/outputs/junit.py`** (7 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L22`
  - Method 'generate_junit' returns 'ET.Element', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L76`
  - Method '_format_testcase_name' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L84`
  - Method '_format_failure_text' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L103`
  - Method 'write_junit' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L122`
  - Method 'generate_junit_string' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/cicd/outputs/markdown.py`** (14 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L20`
  - Method 'generate_markdown' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L60`
  - Method '_generate_summary_table' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L78`
  - Method '_format_net_change' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L87`
  - Method '_format_new_violations_section' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L100`
  - Method '_format_fixed_violations_section' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L116`
  - Method '_format_existing_violations_section' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L131`
  - Method '_generate_comparison_section' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L140`
  - Method '_generate_violations_section' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L173`
  - Method '_format_violation_item' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L196`
  - Method '_generate_footer' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L214`
  - Method 'write_markdown' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L232`
  - Method 'generate_pr_comment' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/cicd/outputs/sarif.py`** (7 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L28`
  - Method 'generate_sarif' returns 'Dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L82`
  - Method '_collect_rules' returns 'List[Dict[str, Any]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L113`
  - Method '_map_severity_to_level' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L123`
  - Method 'write_sarif' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L139`
  - Method 'generate_sarif_for_github' returns 'Dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/cicd/platforms/azure.py`** (3 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L123`
  - Method 'generate_azure_pr_comment_body' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/cicd/platforms/github.py`** (3 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L151`
  - Method 'generate_github_pr_comment_body' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/cicd/runner.py`** (19 violations)

- 🟡 **max-cyclomatic-complexity** at `L382`
  - Function '_determine_exit_code' has complexity 19 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-file-lines** at `file`
  - File exceeds line limit (583 lines > 500)
  - 💡 *Consider splitting into smaller files*
- 🔵 **single-responsibility-modules** at `L38`
  - Class 'CIRunner' has 14 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L456`
  - Class 'CheckCache' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L128`
  - Method '_get_files_to_check' returns 'set[str] | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L154`
  - Method '_filter_contracts' returns 'list[dict[str, Any]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L175`
  - Method '_contract_applies_to_files' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L199`
  - Method '_execute_checks' returns 'list[CIViolation]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L236`
  - Method '_execute_parallel' returns 'list[CIViolation]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L272`
  - Method '_execute_sequential' returns 'list[CIViolation]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L299`
  - Method '_run_single_check' returns 'list[CIViolation]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L359`
  - Method '_get_cache_key' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L378`
  - Method '_compare_baseline' returns 'BaselineComparison', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L382`
  - Method '_determine_exit_code' returns 'ExitCode', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L427`
  - Method '_get_commit_sha' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L542`
  - Method 'clear' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L558`
  - Method 'prune_expired' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/code_chunker.py`** (7 violations)

- 🔵 **single-responsibility-modules** at `L24`
  - Class 'CodeChunker' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L47`
  - Method 'chunk_file' returns 'list[Chunk]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L68`
  - Method '_extract_context' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L109`
  - Method '_chunk_by_structure' returns 'list[Chunk]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L147`
  - Method '_chunk_sliding_window' returns 'list[Chunk]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/command_runner.py`** (3 violations)

- 🔵 **single-responsibility-modules** at `L32`
  - Class 'CommandRunner' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/conformance/domain.py`** (28 violations)

- 🟡 **max-cyclomatic-complexity** at `L170`
  - Function 'compute_test_path' has complexity 23 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L170`
  - Function 'compute_test_path' has 62 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **single-responsibility-modules** at `L113`
  - Class 'Violation' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L286`
  - Class 'Exemption' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L32`
  - Method 'from_contract_severity' returns '"Severity"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L42`
  - Method 'weight' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L86`
  - Method 'matches_file' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L94`
  - Method 'matches_violation_id' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L102`
  - Method 'matches_line' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L137`
  - Method 'generate_id' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L170`
  - Method 'compute_test_path' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L261`
  - Method 'mark_resolved' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L270`
  - Method 'mark_stale' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L274`
  - Method 'mark_exemption_expired' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L279`
  - Method 'reopen' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L302`
  - Method 'is_expired' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L308`
  - Method 'is_active' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L312`
  - Method 'needs_review' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L318`
  - Method 'covers_check' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L322`
  - Method 'covers_violation' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L371`
  - Method 'compliance_rate' returns 'float', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L378`
  - Method 'open_issues' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L397`
  - Method 'has_blockers' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L401`
  - Method 'has_critical' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L405`
  - Method 'is_passing' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L438`
  - Method 'delta_from' returns 'dict[str, int]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/conformance/history_store.py`** (11 violations)

- 🔵 **single-responsibility-modules** at `L18`
  - Class 'HistoryStore' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L30`
  - Method 'ensure_directory' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L37`
  - Method 'save_snapshot' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L62`
  - Method 'get_snapshot' returns 'HistorySnapshot | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L75`
  - Method '_dict_to_snapshot' returns 'HistorySnapshot', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L95`
  - Method 'get_range' returns 'list[HistorySnapshot]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L108`
  - Method 'get_latest' returns 'list[HistorySnapshot]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L133`
  - Method 'prune_old_snapshots' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L154`
  - Method 'get_trend' returns 'dict[str, list]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/conformance/manager.py`** (17 violations)

- 🔵 **single-responsibility-modules** at `L33`
  - Class 'ConformanceManager' has 15 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L55`
  - Method 'is_initialized' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L61`
  - Method 'initialize' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L108`
  - Method 'run_conformance_check' returns 'ConformanceReport', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L154`
  - Method '_create_or_update_violation' returns 'Violation', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L198`
  - Method '_mark_unseen_violations' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L213`
  - Method '_generate_report' returns 'ConformanceReport', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L271`
  - Method 'get_report' returns 'ConformanceReport | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L275`
  - Method 'list_violations' returns 'list[Violation]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L300`
  - Method 'get_violation' returns 'Violation | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L305`
  - Method 'resolve_violation' returns 'Violation | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L321`
  - Method 'prune_violations' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L343`
  - Method 'get_history' returns 'list[HistorySnapshot]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L350`
  - Method 'get_exemptions' returns 'list[Exemption]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L365`
  - Method 'get_summary_stats' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/conformance/stores.py`** (30 violations)

- 🔵 **single-responsibility-modules** at `L79`
  - Class 'ViolationStore' has 14 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L263`
  - Class 'ExemptionRegistry' has 14 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L91`
  - Method 'ensure_directory' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L98`
  - Method 'load_all' returns 'list[Violation]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L114`
  - Method '_load_violation' returns 'Violation | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L123`
  - Method '_dict_to_violation' returns 'Violation', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L149`
  - Method '_violation_to_dict' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L200`
  - Method 'save' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L211`
  - Method 'delete' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L220`
  - Method 'find_by_contract' returns 'list[Violation]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L224`
  - Method 'find_by_status' returns 'list[Violation]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L228`
  - Method 'count_by_status' returns 'dict[ViolationStatus, int]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L235`
  - Method 'count_by_severity' returns 'dict[Severity, int]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L243`
  - Method 'mark_stale' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L274`
  - Method 'ensure_directory' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L281`
  - Method 'load_all' returns 'list[Exemption]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L299`
  - Method '_load_exemption' returns 'Exemption | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L308`
  - Method '_dict_to_exemption' returns 'Exemption', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L343`
  - Method '_exemption_to_dict' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L385`
  - Method 'save' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L396`
  - Method 'delete' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L405`
  - Method 'find_for_violation' returns 'Exemption | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L412`
  - Method 'get_expired' returns 'list[Exemption]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L416`
  - Method 'get_active' returns 'list[Exemption]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L420`
  - Method 'get_needs_review' returns 'list[Exemption]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L424`
  - Method 'update_status' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L440`
  - Method 'save' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L465`
  - Method 'load' returns 'ConformanceReport | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/context/agent_config.py`** (13 violations)

- 🔵 **single-responsibility-modules** at `L163`
  - Class 'AgentConfigLoader' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L66`
  - Method 'model_post_init' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L125`
  - Method 'get_constraint_text' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L131`
  - Method 'get_instructions_text' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L135`
  - Method 'to_context_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L196`
  - Method 'load' returns 'AgentConfig', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L243`
  - Method '_load_file' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L284`
  - Method '_merge' returns 'AgentConfig', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L314`
  - Method '_deep_merge_dict' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L324`
  - Method 'invalidate_cache' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L337`
  - Method 'get_cached_configs' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/context/audit.py`** (16 violations)

- 🟡 **max-parameter-count** at `L93`
  - Function 'log_step' has 6 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🟡 **max-parameter-count** at `L148`
  - Function 'log_task_summary' has 6 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🔵 **single-responsibility-modules** at `L62`
  - Class 'ContextAuditLogger' has 12 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L93`
  - Method 'log_step' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L148`
  - Method 'log_task_summary' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L191`
  - Method 'get_step_audit' returns 'dict[str, Any] | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L198`
  - Method 'get_step_context' returns 'dict[str, Any] | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L205`
  - Method 'get_thinking' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L216`
  - Method 'get_summary' returns 'dict[str, Any] | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L223`
  - Method 'list_steps' returns 'list[int]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L234`
  - Method '_hash_context' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L240`
  - Method '_save_yaml' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L252`
  - Method 'load_task_audit' returns 'Optional["ContextAuditLogger"]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L273`
  - Method 'list_task_audits' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/context/compaction.py`** (29 violations)

- 🟡 **max-class-size** at `L133`
  - Class 'CompactionManager' has 21 methods (max: 20)
  - 💡 *Consider splitting into multiple classes with single responsibilities*
- 🟡 **no-god-classes** at `L133`
  - Class 'CompactionManager' has 21 methods (max: 15)
  - 💡 *Split large classes using composition or inheritance*
- 🔵 **single-responsibility-modules** at `L133`
  - Class 'CompactionManager' has 21 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L51`
  - Method 'summarize' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L85`
  - Method '__lt__' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L122`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L166`
  - Method 'estimate_tokens' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L171`
  - Method 'needs_compaction' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L180`
  - Method 'compact' returns 'tuple[dict[str, Any], CompactionAudit]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L237`
  - Method '_should_preserve' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L245`
  - Method '_navigate_to_section' returns 'tuple[dict | None, str | None]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L257`
  - Method '_create_result_parent' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L268`
  - Method '_apply_truncate' returns 'tuple[Any, bool]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L274`
  - Method '_apply_truncate_middle' returns 'tuple[Any, bool]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L280`
  - Method '_apply_keep_first' returns 'tuple[Any, bool]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L288`
  - Method '_apply_keep_last' returns 'tuple[Any, bool]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L296`
  - Method '_apply_summarize' returns 'tuple[Any, bool]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L307`
  - Method '_summarize_string' returns 'tuple[str, bool]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L316`
  - Method '_summarize_list' returns 'tuple[Any, bool]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L330`
  - Method '_apply_rule' returns 'tuple[dict[str, Any], bool]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L369`
  - Method '_truncate' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L376`
  - Method '_truncate_middle' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L384`
  - Method 'get_section_tokens' returns 'dict[str, int]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L392`
  - Method 'set_summarizer' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L401`
  - Method 'get_summarization_stats' returns 'dict[str, int]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L407`
  - Method 'reset_stats' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L452`
  - Method 'summarize' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/context/fingerprint.py`** (28 violations)

- 🟡 **max-class-size** at `L165`
  - Class 'FingerprintGenerator' has 21 methods (max: 20)
  - 💡 *Consider splitting into multiple classes with single responsibilities*
- 🟡 **no-god-classes** at `L165`
  - Class 'FingerprintGenerator' has 21 methods (max: 15)
  - 💡 *Split large classes using composition or inheritance*
- 🔵 **single-responsibility-modules** at `L165`
  - Class 'FingerprintGenerator' has 21 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L100`
  - Method 'to_context_yaml' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L139`
  - Method 'estimate_tokens' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L143`
  - Method 'with_task_context' returns '"ProjectFingerprint"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L194`
  - Method 'generate' returns 'ProjectFingerprint', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L226`
  - Method 'with_task_context' returns 'ProjectFingerprint', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L240`
  - Method '_compute_content_hash' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L258`
  - Method '_detect_identity' returns 'ProjectIdentity', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L266`
  - Method '_detect_python' returns 'TechnicalProfile | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L289`
  - Method '_detect_python_build_system' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L299`
  - Method '_detect_python_frameworks' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L309`
  - Method '_detect_node' returns 'TechnicalProfile | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L323`
  - Method '_detect_simple_language' returns 'TechnicalProfile | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L342`
  - Method '_detect_technical' returns 'TechnicalProfile', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L353`
  - Method '_detect_architecture' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L363`
  - Method '_detect_import_style' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L371`
  - Method '_detect_docstring_style' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L383`
  - Method '_detect_error_handling' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L391`
  - Method '_detect_patterns' returns 'DetectedPatterns', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L414`
  - Method '_find_first_existing_dir' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L421`
  - Method '_find_config_files' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L431`
  - Method '_find_entry_points' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L449`
  - Method '_detect_structure' returns 'ProjectStructure', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L472`
  - Method 'clear_cache' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/context/templates/__init__.py`** (5 violations)

- 🔵 **default-result-return-types** at `L74`
  - Method 'get_template_for_task' returns 'BaseContextTemplate', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L99`
  - Method 'register_template' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L115`
  - Method 'task_type' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L123`
  - Method 'list_task_types' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L137`
  - Method 'get_template_class' returns 'type[BaseContextTemplate]', expected pattern 'Result|Either|Success|Failure'

**`src/agentforge/core/context/templates/base.py`** (18 violations)

- 🟡 **max-cyclomatic-complexity** at `L287`
  - Function '_get_section_value' has complexity 12 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L213`
  - Function 'build_context_dict' has 63 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-parameter-count** at `L213`
  - Function 'build_context_dict' has 6 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🔵 **single-responsibility-modules** at `L46`
  - Class 'BaseContextTemplate' has 12 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L129`
  - Method 'task_type' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L135`
  - Method 'phases' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L140`
  - Method 'get_tier2_for_phase' returns 'TierDefinition', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L144`
  - Method 'get_phase_mapping' returns 'dict[str, str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L172`
  - Method 'translate_phase' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L189`
  - Method 'get_system_prompt' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L197`
  - Method 'get_all_tiers' returns 'list[TierDefinition]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L205`
  - Method 'get_total_budget' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L213`
  - Method 'build_context_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L287`
  - Method '_get_section_value' returns 'Any | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L328`
  - Method '_truncate_to_budget' returns 'Any', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L345`
  - Method 'estimate_context_tokens' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/context/templates/bridge.py`** (9 violations)

- 🟡 **max-function-length** at `L49`
  - Function 'get_tier2_for_phase' has 83 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **single-responsibility-modules** at `L28`
  - Class 'BridgeTemplate' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L32`
  - Method 'task_type' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L36`
  - Method 'phases' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L39`
  - Method 'get_phase_mapping' returns 'dict[str, str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L49`
  - Method 'get_tier2_for_phase' returns 'TierDefinition', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L134`
  - Method 'get_system_prompt' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/context/templates/code_review.py`** (9 violations)

- 🟡 **max-function-length** at `L49`
  - Function 'get_tier2_for_phase' has 78 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **single-responsibility-modules** at `L28`
  - Class 'CodeReviewTemplate' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L32`
  - Method 'task_type' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L36`
  - Method 'phases' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L39`
  - Method 'get_phase_mapping' returns 'dict[str, str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L49`
  - Method 'get_tier2_for_phase' returns 'TierDefinition', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L129`
  - Method 'get_system_prompt' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/context/templates/discovery.py`** (9 violations)

- 🟡 **max-function-length** at `L49`
  - Function 'get_tier2_for_phase' has 76 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **single-responsibility-modules** at `L28`
  - Class 'DiscoveryTemplate' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L32`
  - Method 'task_type' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L36`
  - Method 'phases' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L39`
  - Method 'get_phase_mapping' returns 'dict[str, str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L49`
  - Method 'get_tier2_for_phase' returns 'TierDefinition', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L127`
  - Method 'get_system_prompt' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/context/templates/fix_violation.py`** (8 violations)

- 🟡 **max-function-length** at `L40`
  - Function 'get_tier2_for_phase' has 100 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **single-responsibility-modules** at `L29`
  - Class 'FixViolationTemplate' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L33`
  - Method 'task_type' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L37`
  - Method 'phases' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L40`
  - Method 'get_tier2_for_phase' returns 'TierDefinition', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L142`
  - Method 'get_system_prompt' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/context/templates/implement_feature.py`** (8 violations)

- 🟡 **max-function-length** at `L43`
  - Function 'get_tier2_for_phase' has 100 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **single-responsibility-modules** at `L32`
  - Class 'ImplementFeatureTemplate' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L36`
  - Method 'task_type' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L40`
  - Method 'phases' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L43`
  - Method 'get_tier2_for_phase' returns 'TierDefinition', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L145`
  - Method 'get_system_prompt' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/context/templates/models.py`** (5 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L56`
  - Method 'get_section' returns 'ContextSection | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L63`
  - Method 'get_required_sections' returns 'list[ContextSection]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L67`
  - Method 'get_section_names' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/context/templates/refactor.py`** (8 violations)

- 🟡 **max-function-length** at `L40`
  - Function 'get_tier2_for_phase' has 106 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **single-responsibility-modules** at `L29`
  - Class 'RefactorTemplate' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L33`
  - Method 'task_type' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L37`
  - Method 'phases' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L40`
  - Method 'get_tier2_for_phase' returns 'TierDefinition', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L148`
  - Method 'get_system_prompt' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/context/templates/write_tests.py`** (8 violations)

- 🟡 **max-function-length** at `L40`
  - Function 'get_tier2_for_phase' has 100 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **single-responsibility-modules** at `L29`
  - Class 'WriteTestsTemplate' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L33`
  - Method 'task_type' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L37`
  - Method 'phases' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L40`
  - Method 'get_tier2_for_phase' returns 'TierDefinition', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L142`
  - Method 'get_system_prompt' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/context_assembler.py`** (16 violations)

- 🔵 **single-responsibility-modules** at `L58`
  - Class 'ContextAssembler' has 15 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L85`
  - Method '_build_layer_patterns' returns 'dict[str, list[str]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L117`
  - Method 'detect_layer' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L134`
  - Method 'detect_language' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L150`
  - Method 'estimate_tokens' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L154`
  - Method '_process_vector_results' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L181`
  - Method '_process_lsp_symbols' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L212`
  - Method '_apply_entry_point_boosts' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L225`
  - Method '_get_file_content' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L251`
  - Method '_build_file_contexts' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L291`
  - Method 'assemble' returns 'CodeContext', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L340`
  - Method '_truncate_content' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L353`
  - Method '_detect_patterns' returns 'list[PatternMatch]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L357`
  - Method 'assemble_from_files' returns 'CodeContext', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/context_assembler_types.py`** (12 violations)

- 🔵 **single-responsibility-modules** at `L89`
  - Class 'CodeContext' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L42`
  - Method 'to_dict' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L62`
  - Method 'to_dict' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L80`
  - Method 'to_dict' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L97`
  - Method 'to_dict' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L108`
  - Method 'to_yaml' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L112`
  - Method '_group_files_by_layer' returns 'dict[str, list["FileContext"]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L122`
  - Method '_format_file_section' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L130`
  - Method '_format_patterns_section' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L142`
  - Method 'to_prompt_text' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/context_patterns.py`** (5 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L63`
  - Method 'check_pattern_def' returns 'PatternMatch', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L85`
  - Method 'check_cqrs_pattern' returns 'PatternMatch', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L101`
  - Method 'detect_patterns' returns 'list[PatternMatch]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/context_retrieval.py`** (13 violations)

- 🔵 **single-responsibility-modules** at `L64`
  - Class 'ContextRetriever' has 14 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L100`
  - Method '_load_config' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L128`
  - Method 'assembler' returns 'ContextAssembler', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L175`
  - Method '_retrieve_lsp_symbols' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L192`
  - Method '_retrieve_vector_results' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L205`
  - Method 'retrieve' returns 'CodeContext', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L247`
  - Method '_extract_keywords' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L274`
  - Method 'get_symbol_context' returns 'CodeContext | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L311`
  - Method 'get_file_context' returns 'FileContext | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L315`
  - Method 'index' returns 'IndexStats', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L331`
  - Method 'check_dependencies' returns 'dict[str, dict[str, Any]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/context_retrieval_cli.py`** (5 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L89`
  - Method 'run_search_command' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L110`
  - Method 'run_symbol_command' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L121`
  - Method 'dispatch_command' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/contract_runner.py`** (13 violations)

- 🔵 **single-responsibility-modules** at `L27`
  - Class 'ContractRunner' has 11 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L38`
  - Method '_load_project_context' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L47`
  - Method 'load_contract' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L56`
  - Method '_build_system_message' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L61`
  - Method '_should_include_section' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L69`
  - Method '_build_user_message' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L79`
  - Method '_substitute_variables' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L88`
  - Method 'assemble_prompt' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L119`
  - Method 'validate_output' returns 'Any | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L137`
  - Method 'save_prompt' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L157`
  - Method 'save_output' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/contract_validator.py`** (4 violations)

- 🔵 **single-responsibility-modules** at `L35`
  - Class 'ContractValidator' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L51`
  - Method 'validate_contract' returns 'ContractValidationReport', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/contract_validator_types.py`** (2 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/contracts.py`** (2 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/contracts/__init__.py`** (4 violations)

- 🔵 **max-imports** at `L1`
  - File has 33 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **max-imports** at `L1`
  - File has 33 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **max-imports** at `L1`
  - File has 33 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **max-imports** at `L1`
  - File has 33 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*

**`src/agentforge/core/contracts/cli.py`** (9 violations)

- 🟡 **max-cyclomatic-complexity** at `L132`
  - Function 'review_command' has complexity 21 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L132`
  - Function 'review_command' has 95 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-nesting-depth** at `L132`
  - Function 'review_command' has nesting depth 5 (max: 4)
  - 💡 *Use early returns, guard clauses, or extract nested logic*
- 🟡 **main-guard-pattern** at `file`
  - Required pattern not found: 'if\s+__name__\s*==\s*['"]__main__['"]'
  - 💡 *Add: if __name__ == '__main__': main()*
- 🔵 **cli-has-version** at `file`
  - Required pattern not found: '@click\.version_option|--version|version_callback'
  - 💡 *Add @click.version_option() to main command*
- 🔵 **cli-config-from-env** at `file`
  - Required pattern not found: '(envvar\s*=|os\.environ|getenv)'
  - 💡 *Add envvar parameter: @click.option('--api-key', envvar='API_KEY')*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L50`
  - Method 'get_registry' returns 'ContractRegistry', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/contracts/draft.py`** (31 violations)

- 🟡 **max-file-lines** at `file`
  - File exceeds line limit (501 lines > 500)
  - 💡 *Consider splitting into smaller files*
- 🔵 **single-responsibility-modules** at `L294`
  - Class 'ContractDraft' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L410`
  - Class 'ApprovedContracts' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L46`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L59`
  - Method 'from_dict' returns '"ValidationRule"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L86`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L98`
  - Method 'from_dict' returns '"EscalationTrigger"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L122`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L132`
  - Method 'from_dict' returns '"QualityGate"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L169`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L183`
  - Method 'from_dict' returns '"StageContract"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L210`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L221`
  - Method 'from_dict' returns '"OpenQuestion"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L242`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L253`
  - Method 'from_dict' returns '"Assumption"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L273`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L283`
  - Method 'from_dict' returns '"Revision"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L327`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L345`
  - Method 'from_dict' returns '"ContractDraft"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L380`
  - Method 'to_yaml' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L385`
  - Method 'from_yaml' returns '"ContractDraft"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L390`
  - Method 'get_stage_contract' returns 'StageContract | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L397`
  - Method 'add_revision' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L430`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L445`
  - Method 'from_dict' returns '"ApprovedContracts"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L468`
  - Method 'to_yaml' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L473`
  - Method 'from_yaml' returns '"ApprovedContracts"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L478`
  - Method 'get_stage_contract' returns 'StageContract | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L486`
  - Method 'from_draft' returns '"ApprovedContracts"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/contracts/drafter.py`** (16 violations)

- 🟡 **max-cyclomatic-complexity** at `L135`
  - Function '_load_system_prompt' has complexity 12 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🔵 **single-responsibility-modules** at `L110`
  - Class 'ContractDrafter' has 12 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L71`
  - Method 'to_prompt_context' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L135`
  - Method '_load_system_prompt' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L175`
  - Method '_get_default_system_prompt' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L204`
  - Method 'draft' returns 'ContractDraft', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L244`
  - Method '_build_user_message' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L281`
  - Method '_parse_response' returns 'ContractDraft', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L307`
  - Method '_extract_yaml' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L318`
  - Method '_build_draft_from_data' returns 'ContractDraft', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L364`
  - Method '_parse_stage_contract' returns 'StageContract', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L382`
  - Method '_create_error_draft' returns 'ContractDraft', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L398`
  - Method '_generate_draft_id' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L403`
  - Method 'refine' returns 'ContractDraft', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/contracts/enforcer.py`** (24 violations)

- 🟡 **max-function-length** at `L255`
  - Function '_validate_schema' has 55 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-nesting-depth** at `L473`
  - Function '_evaluate_trigger_condition' has nesting depth 5 (max: 4)
  - 💡 *Use early returns, guard clauses, or extract nested logic*
- 🟡 **max-file-lines** at `file`
  - File exceeds line limit (644 lines > 500)
  - 💡 *Consider splitting into smaller files*
- 🟡 **no-god-classes** at `L141`
  - Class 'ContractEnforcer' has 20 methods (max: 15)
  - 💡 *Split large classes using composition or inheritance*
- 🔵 **single-responsibility-modules** at `L85`
  - Class 'ValidationResult' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L141`
  - Class 'ContractEnforcer' has 20 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L69`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L95`
  - Method 'error_count' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L100`
  - Method 'warning_count' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L104`
  - Method 'add_violation' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L163`
  - Method '_next_violation_id' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L320`
  - Method '_check_type' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L336`
  - Method '_get_severity' returns 'ViolationSeverity', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L340`
  - Method '_validate_required_field' returns 'Violation | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L356`
  - Method '_validate_type_check' returns 'Violation | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L375`
  - Method '_validate_enum_constraint' returns 'Violation | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L419`
  - Method '_get_field_value' returns 'Any', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L442`
  - Method 'check_escalation_triggers' returns 'list[EscalationCheck]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L473`
  - Method '_evaluate_trigger_condition' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L511`
  - Method '_evaluate_check' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L602`
  - Method '_check_operation_rule' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L615`
  - Method 'get_summary' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/contracts/evolution.py`** (14 violations)

- 🟡 **max-function-length** at `L126`
  - Function 'detect_assumption_violation' has 55 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L314`
  - Function 'apply_evolution' has 54 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **single-responsibility-modules** at `L98`
  - Class 'ContractEvolutionHandler' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L53`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L111`
  - Method '_next_violation_id' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L116`
  - Method '_next_escalation_id' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L121`
  - Method '_next_change_id' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L126`
  - Method 'detect_assumption_violation' returns 'AssumptionViolation | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L193`
  - Method 'escalate_for_redraft' returns 'ContractEscalation', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L222`
  - Method '_generate_proposed_changes' returns 'list[ContractChange]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L276`
  - Method '_generate_escalation_prompt' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L314`
  - Method 'apply_evolution' returns 'ApprovedContracts', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/contracts/operations/loader.py`** (26 violations)

- 🔵 **single-responsibility-modules** at `L122`
  - Class 'OperationContract' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L308`
  - Class 'OperationContractManager' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L39`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L51`
  - Method 'from_dict' returns '"OperationRule"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L73`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L84`
  - Method 'from_dict' returns '"OperationTrigger"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L103`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L112`
  - Method 'from_dict' returns '"OperationGate"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L140`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L152`
  - Method 'from_dict' returns '"OperationContract"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L171`
  - Method 'get_rule' returns 'OperationRule | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L178`
  - Method 'get_rules_by_type' returns 'list[OperationRule]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L182`
  - Method 'get_rules_by_severity' returns 'list[OperationRule]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L187`
  - Method 'get_builtin_contracts_path' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L202`
  - Method 'load_operation_contract' returns 'OperationContract', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L238`
  - Method '_load_unified_format' returns 'OperationContract', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L279`
  - Method 'load_all_operation_contracts' returns 'dict[str, OperationContract]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L324`
  - Method 'get_all_rules' returns 'list[OperationRule]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L331`
  - Method 'get_all_triggers' returns 'list[OperationTrigger]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L338`
  - Method 'get_all_gates' returns 'list[OperationGate]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L345`
  - Method 'get_rules_for_check_type' returns 'list[OperationRule]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L349`
  - Method 'get_error_rules' returns 'list[OperationRule]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L353`
  - Method 'get_blocking_triggers' returns 'list[OperationTrigger]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L357`
  - Method 'validate_contracts' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/contracts/operations/verifier.py`** (30 violations)

- 🔵 **single-responsibility-modules** at `L43`
  - Class 'VerificationReport' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L156`
  - Class 'OperationContractVerifier' has 15 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L37`
  - Method '__str__' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L52`
  - Method 'is_passed' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L57`
  - Method 'error_count' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L61`
  - Method 'warning_count' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L65`
  - Method 'info_count' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L68`
  - Method 'violations_by_file' returns 'dict[str, list[Violation]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L75`
  - Method 'summary' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L101`
  - Method '_has_bool_naming_issue' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L112`
  - Method '_check_bool_variable' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L126`
  - Method '_is_name_too_short' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L133`
  - Method '_is_name_generic' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L138`
  - Method '_create_violation' returns 'Violation', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L173`
  - Method '_init_handlers' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L182`
  - Method 'verify' returns 'VerificationReport', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L205`
  - Method '_run_checks' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L225`
  - Method 'verify_rule' returns 'VerificationReport', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L243`
  - Method '_collect_files' returns 'list[Path]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L255`
  - Method '_get_contracts' returns 'list[OperationContract]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L265`
  - Method '_check_code_metric' returns 'list[Violation]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L290`
  - Method '_results_to_violations' returns 'list[Violation]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L302`
  - Method '_check_safety_pattern' returns 'list[Violation]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L327`
  - Method '_check_naming_convention' returns 'list[Violation]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L340`
  - Method '_check_boolean_naming' returns 'list[Violation]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L372`
  - Method '_check_descriptive_naming' returns 'list[Violation]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L387`
  - Method '_find_naming_issues' returns 'list[Violation]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L428`
  - Method 'verify_operations' returns 'VerificationReport', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/contracts/registry.py`** (19 violations)

- 🟡 **max-cyclomatic-complexity** at `L192`
  - Function 'evolve' has complexity 12 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L192`
  - Function 'evolve' has 53 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-nesting-depth** at `L192`
  - Function 'evolve' has nesting depth 5 (max: 4)
  - 💡 *Use early returns, guard clauses, or extract nested logic*
- 🔵 **single-responsibility-modules** at `L28`
  - Class 'ContractRegistry' has 13 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L57`
  - Method 'register' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L91`
  - Method 'get_for_request' returns 'ApprovedContracts | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L108`
  - Method 'list_approved' returns 'list[dict[str, Any]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L127`
  - Method 'save_draft' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L140`
  - Method 'get_draft' returns 'ContractDraft | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L156`
  - Method 'list_drafts' returns 'list[dict[str, Any]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L177`
  - Method 'delete_draft' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L192`
  - Method 'evolve' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L262`
  - Method '_load_index' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L269`
  - Method '_save_index' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L277`
  - Method '_update_index' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L287`
  - Method 'generate_contract_set_id' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L293`
  - Method 'generate_draft_id' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/contracts/reviewer.py`** (19 violations)

- 🔵 **single-responsibility-modules** at `L106`
  - Class 'ContractReviewer' has 13 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L74`
  - Method 'get_stage_decision' returns 'StageDecision | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L81`
  - Method 'all_stages_approved' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L96`
  - Method 'approve' returns 'ApprovedContracts', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L113`
  - Method 'create_session' returns 'ReviewSession', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L126`
  - Method '_format_header' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L137`
  - Method '_format_stage_summary' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L152`
  - Method '_format_triggers_and_gates' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L165`
  - Method '_format_questions_and_assumptions' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L183`
  - Method 'format_for_display' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L199`
  - Method '_format_requirements_list' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L208`
  - Method '_format_schema_section' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L217`
  - Method '_format_validation_rules_section' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L228`
  - Method 'format_stage_for_review' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L254`
  - Method 'apply_feedback' returns 'ReviewSession', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L282`
  - Method 'finalize' returns 'ApprovedContracts | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L301`
  - Method 'get_summary' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/contracts_ast.py`** (14 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L24`
  - Method 'execute_ast_check' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L62`
  - Method '_get_violations' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L77`
  - Method 'check_cyclomatic_complexity' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L94`
  - Method '_get_node_complexity' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L110`
  - Method '_calculate_complexity' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L119`
  - Method 'visit' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L132`
  - Method 'check_function_length' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L157`
  - Method 'check_nesting_depth' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L174`
  - Method '_calculate_max_nesting' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L191`
  - Method 'check_parameter_count' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L218`
  - Method 'check_class_size' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L238`
  - Method 'check_import_count' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/contracts_execution.py`** (18 violations)

- 🟡 **max-file-lines** at `file`
  - File exceeds line limit (930 lines > 500)
  - 💡 *Consider splitting into smaller files*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L50`
  - Method '_normalize_file_paths' returns 'list[Path]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L57`
  - Method '_get_check_handlers' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L107`
  - Method '_get_files_for_check' returns 'list[Path]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L260`
  - Method '_is_gitignored' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L410`
  - Method '_get_symbol_pattern' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L416`
  - Method '_extract_symbols' returns 'list[tuple]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L518`
  - Method '_build_bases_string' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L531`
  - Method '_extract_class_with_bases' returns 'list[tuple]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L555`
  - Method '_parse_inheritance_list' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L576`
  - Method '_has_interface' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L659`
  - Method 'method_name' returns 'ReturnType', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L667`
  - Method '_get_method_visibility' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L682`
  - Method '_should_include_method' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L693`
  - Method '_extract_methods_with_return_types' returns 'list[tuple]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L722`
  - Method '_is_return_type_excluded' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/contracts_fixers.py`** (23 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L43`
  - Method 'register_fixer' returns 'Callable[[FixerFunc], FixerFunc]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L46`
  - Method 'decorator' returns 'FixerFunc', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L53`
  - Method 'get_fixer' returns 'FixerFunc | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L58`
  - Method 'list_fixers' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L94`
  - Method '_find_bare_asserts' returns 'list[tuple[int, int, str]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L104`
  - Method '_apply_assert_fixes' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L160`
  - Method '_generate_assert_message' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L200`
  - Method '_get_node_repr' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L211`
  - Method '_is_single_line_assert' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L224`
  - Method '_add_message_to_assert' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L251`
  - Method '_is_escaped_quote' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L256`
  - Method '_handle_string_start' returns 'tuple[str, int]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L263`
  - Method '_handle_quote' returns 'tuple[str | None, int]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L274`
  - Method '_update_paren_depth' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L283`
  - Method '_find_char_at_depth_zero' returns 'int | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L325`
  - Method '_find_expression_end' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L331`
  - Method '_has_message_already' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L336`
  - Method '_check_logging_setup' returns 'tuple[bool, bool]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L343`
  - Method '_convert_prints_to_logger' returns 'tuple[list[str], int]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L358`
  - Method '_find_import_insert_position' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L371`
  - Method '_add_logging_header' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/contracts_lsp.py`** (15 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L23`
  - Method 'execute_lsp_query_check' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L75`
  - Method '_run_lsp_query' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L92`
  - Method '_symbol_matches_kind' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L100`
  - Method '_symbol_matches_visibility' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L107`
  - Method '_symbol_matches_name' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L114`
  - Method '_symbol_has_modifiers' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L122`
  - Method '_symbol_excluded_by_modifiers' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L134`
  - Method '_symbol_excluded_by_name' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L141`
  - Method '_symbol_excluded_by_container' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L153`
  - Method '_lsp_query_symbols' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L184`
  - Method '_lsp_query_references' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L190`
  - Method '_lsp_query_diagnostics' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L214`
  - Method '_lsp_query_call_hierarchy' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/contracts_registry.py`** (15 violations)

- 🔵 **single-responsibility-modules** at `L33`
  - Class 'ContractRegistry' has 15 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L54`
  - Method 'discover_contracts' returns 'dict[str, Contract]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L91`
  - Method '_load_contract_file' returns 'Contract | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L134`
  - Method 'resolve_inheritance' returns 'Contract', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L159`
  - Method '_resolve_contract_reference' returns 'Contract | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L174`
  - Method 'load_exemptions' returns 'list[Exemption]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L208`
  - Method '_parse_exemption' returns 'Exemption | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L240`
  - Method 'find_exemption' returns 'Exemption | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L269`
  - Method '_contract_matches_filters' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L281`
  - Method 'get_enabled_contracts' returns 'list[Contract]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L296`
  - Method 'get_applicable_contracts' returns 'list[Contract]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L305`
  - Method 'get_contract' returns 'Contract | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L313`
  - Method 'get_all_contracts_data' returns 'list[dict[str, Any]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/contracts_types.py`** (14 violations)

- 🔵 **single-responsibility-modules** at `L137`
  - Class 'Exemption' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L48`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L58`
  - Method 'from_dict' returns '"EscalationTrigger"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L79`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L87`
  - Method 'from_dict' returns '"QualityGate"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L132`
  - Method 'exempted_count' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L152`
  - Method 'is_expired' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L158`
  - Method 'is_active' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L162`
  - Method 'covers_file' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L171`
  - Method 'covers_line' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L212`
  - Method 'is_abstract' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L220`
  - Method 'all_checks' returns 'list[dict[str, Any]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/discovery/analyzers/interactions.py`** (18 violations)

- 🟡 **max-cyclomatic-complexity** at `L52`
  - Function '_detect_docker_compose' has complexity 13 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-nesting-depth** at `L52`
  - Function '_detect_docker_compose' has nesting depth 5 (max: 4)
  - 💡 *Use early returns, guard clauses, or extract nested logic*
- 🔵 **single-responsibility-modules** at `L24`
  - Class 'InteractionDetector' has 13 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L37`
  - Method 'detect_all' returns 'list[Interaction]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L52`
  - Method '_detect_docker_compose' returns 'list[Interaction]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L117`
  - Method '_map_services_to_zones' returns 'dict[str, str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L154`
  - Method '_detect_shared_schemas' returns 'list[Interaction]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L183`
  - Method '_find_zones_referencing' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L212`
  - Method '_get_zone_files' returns 'list[Path]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L231`
  - Method '_detect_schema_format' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L241`
  - Method '_find_referenced_zone' returns 'tuple[Path, str] | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L250`
  - Method '_get_zone_path' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L254`
  - Method '_detect_shared_packages' returns 'list[Interaction]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L285`
  - Method '_map_projects_to_zones' returns 'dict[Path, str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L299`
  - Method '_get_project_references' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L315`
  - Method 'detect_interactions' returns 'list[Interaction]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/discovery/analyzers/patterns.py`** (17 violations)

- 🟡 **max-cyclomatic-complexity** at `L484`
  - Function '_check_signal' has complexity 43 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-cyclomatic-complexity** at `L654`
  - Function '_detect_frameworks' has complexity 15 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L484`
  - Function '_check_signal' has 88 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-nesting-depth** at `L484`
  - Function '_check_signal' has nesting depth 11 (max: 4)
  - 💡 *Use early returns, guard clauses, or extract nested logic*
- 🟡 **max-nesting-depth** at `L654`
  - Function '_detect_frameworks' has nesting depth 5 (max: 4)
  - 💡 *Use early returns, guard clauses, or extract nested logic*
- 🟡 **max-parameter-count** at `L484`
  - Function '_check_signal' has 8 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🟡 **max-parameter-count** at `L583`
  - Function '_add_match' has 6 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🟡 **max-file-lines** at `file`
  - File exceeds line limit (715 lines > 500)
  - 💡 *Consider splitting into smaller files*
- 🔵 **single-responsibility-modules** at `L398`
  - Class 'PatternAnalyzer' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L444`
  - Method '_analyze_file' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L484`
  - Method '_check_signal' returns 'float', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L583`
  - Method '_add_match' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L602`
  - Method '_aggregate_patterns' returns 'dict[str, PatternDetection]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L654`
  - Method '_detect_frameworks' returns 'dict[str, Detection]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L704`
  - Method 'get_patterns_by_confidence' returns 'list[PatternDetection]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/discovery/analyzers/structure.py`** (19 violations)

- 🟡 **max-cyclomatic-complexity** at `L183`
  - Function '_detect_layer' has complexity 12 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-nesting-depth** at `L183`
  - Function '_detect_layer' has nesting depth 5 (max: 4)
  - 💡 *Use early returns, guard clauses, or extract nested logic*
- 🟡 **max-file-lines** at `file`
  - File exceeds line limit (540 lines > 500)
  - 💡 *Consider splitting into smaller files*
- 🔵 **single-responsibility-modules** at `L89`
  - Class 'StructureAnalyzer' has 15 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L150`
  - Method '_scan_directories' returns 'list[DirectoryInfo]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L183`
  - Method '_detect_layer' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L226`
  - Method '_aggregate_layers' returns 'dict[str, LayerInfo]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L268`
  - Method '_calculate_style_score' returns 'tuple[float, list[str]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L298`
  - Method '_detect_architecture_style' returns 'tuple[str, float, list[str]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L321`
  - Method '_find_entry_points' returns 'list[Path]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L342`
  - Method '_find_pyproject_scripts' returns 'list[Path]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L372`
  - Method '_find_test_directories' returns 'list[Path]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L391`
  - Method '_detect_source_root' returns 'Path | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L419`
  - Method 'get_layer_for_path' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L431`
  - Method '_detect_dotnet_layers' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L490`
  - Method '_find_dotnet_entry_points' returns 'list[Path]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L518`
  - Method '_find_dotnet_test_directories' returns 'list[Path]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/discovery/analyzers/test_linkage.py`** (16 violations)

- 🟡 **max-function-length** at `L36`
  - Function 'analyze' has 53 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-nesting-depth** at `L135`
  - Function '_extract_imports' has nesting depth 5 (max: 4)
  - 💡 *Use early returns, guard clauses, or extract nested logic*
- 🔵 **single-responsibility-modules** at `L24`
  - Class 'TestLinkageAnalyzer' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L36`
  - Method 'analyze' returns 'CoverageGapAnalysis', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L111`
  - Method '_find_test_files' returns 'list[Path]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L123`
  - Method '_find_source_files' returns 'list[Path]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L135`
  - Method '_extract_imports' returns 'set[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L156`
  - Method '_check_import_linkage' returns 'tuple[float, str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L188`
  - Method '_check_naming_convention' returns 'tuple[str | None, float]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L218`
  - Method '_count_test_methods' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L230`
  - Method '_detect_frameworks' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L246`
  - Method '_categorize_tests' returns 'dict[str, int]', expected pattern 'Result|Either|Success|Failure'
- 🟡 **file-structure** at `file`
  - Test file outside tests/ directory
  - 💡 *Move test files to tests/ directory*
- 🟡 **file-structure** at `file`
  - Test file outside tests/ directory
  - 💡 *Move test files to tests/ directory*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/discovery/domain.py`** (20 violations)

- 🟡 **max-file-lines** at `file`
  - File exceeds line limit (511 lines > 500)
  - 💡 *Consider splitting into smaller files*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L41`
  - Method 'from_score' returns '"ConfidenceLevel"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L99`
  - Method 'confidence_level' returns 'ConfidenceLevel', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L102`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L127`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L163`
  - Method 'has_violations' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L167`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L200`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L220`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L260`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L281`
  - Method 'get_test_path' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L288`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L318`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L329`
  - Method 'contains_path' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L355`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L389`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L434`
  - Method 'is_complete' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L473`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/discovery/generators/as_built_spec.py`** (17 violations)

- 🟡 **max-cyclomatic-complexity** at `L296`
  - Function '_classify_class' has complexity 12 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-nesting-depth** at `L323`
  - Function '_match_test_methods' has nesting depth 5 (max: 4)
  - 💡 *Use early returns, guard clauses, or extract nested logic*
- 🔵 **single-responsibility-modules** at `L107`
  - Class 'AsBuiltSpecGenerator' has 11 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L48`
  - Method 'component_id' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L72`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L130`
  - Method '_simplify_path' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L156`
  - Method 'generate_from_test_analysis' returns 'list[AsBuiltSpec]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L192`
  - Method '_generate_spec_for_directory' returns 'AsBuiltSpec | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L226`
  - Method '_analyze_source_file' returns 'DiscoveredComponent | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L259`
  - Method '_extract_entities' returns 'list[DiscoveredEntity]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L296`
  - Method '_classify_class' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L315`
  - Method '_extract_module_docstring' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L323`
  - Method '_match_test_methods' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L351`
  - Method 'save_specs' returns 'list[Path]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L382`
  - Method 'generate_lineage_updates' returns 'dict[str, dict[str, str]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/discovery/generators/lineage_embedder.py`** (13 violations)

- 🟡 **max-cyclomatic-complexity** at `L300`
  - Function '_insert_lineage_block' has complexity 18 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L122`
  - Function 'embed_file' has 68 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-nesting-depth** at `L227`
  - Function '_find_existing_lineage' has nesting depth 5 (max: 4)
  - 💡 *Use early returns, guard clauses, or extract nested logic*
- 🔵 **single-responsibility-modules** at `L50`
  - Class 'LineageEmbedder' has 11 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L207`
  - Method '_build_lineage_block' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L227`
  - Method '_find_existing_lineage' returns 'tuple[bool, int, int]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L262`
  - Method '_is_lineage_line' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L272`
  - Method '_is_lineage_end' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L281`
  - Method '_replace_lineage_block' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L300`
  - Method '_insert_lineage_block' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L358`
  - Method 'summary' returns 'dict[str, int]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/discovery/generators/profile.py`** (13 violations)

- 🟡 **max-parameter-count** at `L46`
  - Function 'generate' has 7 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🔵 **single-responsibility-modules** at `L32`
  - Class 'ProfileGenerator' has 10 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L46`
  - Method 'generate' returns 'CodebaseProfile', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L107`
  - Method '_build_structure_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L128`
  - Method '_build_patterns_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L154`
  - Method '_build_architecture_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L163`
  - Method 'to_yaml' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L171`
  - Method 'save' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L194`
  - Method '_profile_to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L236`
  - Method 'load' returns ''ProfileGenerator'', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L251`
  - Method '_dict_to_profile' returns 'CodebaseProfile', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/discovery/manager.py`** (34 violations)

- 🟡 **max-cyclomatic-complexity** at `L246`
  - Function '_detect_languages' has complexity 12 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-cyclomatic-complexity** at `L600`
  - Function 'discover' has complexity 13 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-cyclomatic-complexity** at `L719`
  - Function '_analyze_zone' has complexity 14 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-cyclomatic-complexity** at `L844`
  - Function '_generate_multi_zone_profile' has complexity 16 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L600`
  - Function 'discover' has 80 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L719`
  - Function '_analyze_zone' has 87 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L844`
  - Function '_generate_multi_zone_profile' has 61 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-nesting-depth** at `L207`
  - Function '_run_phase' has nesting depth 6 (max: 4)
  - 💡 *Use early returns, guard clauses, or extract nested logic*
- 🟡 **max-file-lines** at `file`
  - File exceeds line limit (959 lines > 500)
  - 💡 *Consider splitting into smaller files*
- 🔵 **single-responsibility-modules** at `L84`
  - Class 'DiscoveryManager' has 14 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L546`
  - Class 'MultiZoneDiscoveryManager' has 11 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **max-imports** at `L1`
  - File has 36 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **max-imports** at `L1`
  - File has 36 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **max-imports** at `L1`
  - File has 36 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **max-imports** at `L1`
  - File has 36 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **default-result-return-types** at `L129`
  - Method '_default_phases' returns 'list[DiscoveryPhase]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L139`
  - Method '_execute_phase' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L246`
  - Method '_detect_languages' returns 'list[LanguageInfo]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L360`
  - Method '_map_architecture' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L379`
  - Method '_analyze_tests' returns 'CoverageGapAnalysis', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L409`
  - Method '_has_minimum_results' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L417`
  - Method '_generate_profile' returns 'tuple[CodebaseProfile, Path | None]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L473`
  - Method '_generate_as_built_specs' returns 'tuple[list[Path], int]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L525`
  - Method '_report_progress' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L590`
  - Method '_load_config' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L700`
  - Method 'list_zones' returns 'list[Zone]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L709`
  - Method '_detect_zones' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L719`
  - Method '_analyze_zone' returns 'ZoneProfile', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L828`
  - Method '_detect_interactions' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L844`
  - Method '_generate_multi_zone_profile' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L923`
  - Method '_get_detection_mode' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L953`
  - Method '_report_progress' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/discovery/providers/base.py`** (13 violations)

- 🔵 **single-responsibility-modules** at `L60`
  - Class 'LanguageProvider' has 10 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L74`
  - Method 'language_name' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L80`
  - Method 'file_extensions' returns 'set[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L86`
  - Method 'project_markers' returns 'set[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L91`
  - Method 'detect_project' returns 'dict[str, Any] | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L101`
  - Method 'parse_file' returns 'Any | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L111`
  - Method 'extract_symbols' returns 'list[Symbol]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L116`
  - Method 'get_imports' returns 'list[Import]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L121`
  - Method 'get_dependencies' returns 'list[Dependency]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L125`
  - Method 'get_source_files' returns 'list[Path]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L148`
  - Method 'count_lines' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/discovery/providers/dotnet_provider.py`** (33 violations)

- 🟡 **max-cyclomatic-complexity** at `L104`
  - Function '_parse_csproj' has complexity 19 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-cyclomatic-complexity** at `L304`
  - Function '_extract_symbols_regex' has complexity 15 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-cyclomatic-complexity** at `L493`
  - Function 'detect_layer_from_project_name' has complexity 11 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-cyclomatic-complexity** at `L549`
  - Function 'count_lines' has complexity 11 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L104`
  - Function '_parse_csproj' has 57 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L304`
  - Function '_extract_symbols_regex' has 82 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-nesting-depth** at `L549`
  - Function 'count_lines' has nesting depth 7 (max: 4)
  - 💡 *Use early returns, guard clauses, or extract nested logic*
- 🟡 **max-class-size** at `L19`
  - Class 'DotNetProvider' has 21 methods (max: 20)
  - 💡 *Consider splitting into multiple classes with single responsibilities*
- 🟡 **max-file-lines** at `file`
  - File exceeds line limit (585 lines > 500)
  - 💡 *Consider splitting into smaller files*
- 🟡 **no-god-classes** at `L19`
  - Class 'DotNetProvider' has 21 methods (max: 15)
  - 💡 *Split large classes using composition or inheritance*
- 🔵 **single-responsibility-modules** at `L19`
  - Class 'DotNetProvider' has 21 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L28`
  - Method 'language_name' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L32`
  - Method 'file_extensions' returns 'set[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L36`
  - Method 'project_markers' returns 'set[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L45`
  - Method 'detect_project' returns 'dict[str, Any] | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L65`
  - Method '_parse_solution' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L104`
  - Method '_parse_csproj' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L183`
  - Method '_detect_frameworks_from_package' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L217`
  - Method 'parse_file' returns 'Any | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L224`
  - Method 'extract_symbols' returns 'list[Symbol]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L234`
  - Method '_extract_symbols_lsp' returns 'list[Symbol]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L245`
  - Method '_ensure_lsp' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L266`
  - Method '_convert_lsp_symbols' returns 'list[Symbol]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L304`
  - Method '_extract_symbols_regex' returns 'list[Symbol]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L406`
  - Method '_infer_visibility' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L412`
  - Method 'get_imports' returns 'list[Import]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L458`
  - Method 'get_dependencies' returns 'list[Dependency]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L485`
  - Method 'get_project_references' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L493`
  - Method 'detect_layer_from_project_name' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L527`
  - Method 'get_source_files' returns 'list[Path]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L549`
  - Method 'count_lines' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/discovery/providers/python_provider.py`** (52 violations)

- 🟡 **max-cyclomatic-complexity** at `L477`
  - Function 'suggest_extractions' has complexity 11 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-cyclomatic-complexity** at `L609`
  - Function 'get_violation_context' has complexity 14 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-cyclomatic-complexity** at `L786`
  - Function '_get_parameter_suggestions' has complexity 19 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L786`
  - Function '_get_parameter_suggestions' has 51 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-nesting-depth** at `L477`
  - Function 'suggest_extractions' has nesting depth 6 (max: 4)
  - 💡 *Use early returns, guard clauses, or extract nested logic*
- 🟡 **max-nesting-depth** at `L666`
  - Function '_get_complexity_suggestions' has nesting depth 5 (max: 4)
  - 💡 *Use early returns, guard clauses, or extract nested logic*
- 🟡 **max-nesting-depth** at `L718`
  - Function '_get_length_suggestions' has nesting depth 5 (max: 4)
  - 💡 *Use early returns, guard clauses, or extract nested logic*
- 🟡 **max-class-size** at `L111`
  - Class 'PythonProvider' has 38 methods (max: 20)
  - 💡 *Consider splitting into multiple classes with single responsibilities*
- 🟡 **max-file-lines** at `file`
  - File exceeds line limit (970 lines > 500)
  - 💡 *Consider splitting into smaller files*
- 🟡 **no-god-classes** at `L111`
  - Class 'PythonProvider' has 38 methods (max: 15)
  - 💡 *Split large classes using composition or inheritance*
- 🔵 **single-responsibility-modules** at `L41`
  - Class 'ComplexityVisitor' has 10 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L111`
  - Class 'PythonProvider' has 38 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L115`
  - Method 'language_name' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L119`
  - Method 'file_extensions' returns 'set[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L123`
  - Method 'project_markers' returns 'set[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L126`
  - Method 'detect_project' returns 'dict[str, Any] | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L156`
  - Method '_parse_project_file' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L176`
  - Method '_parse_pyproject_toml' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L206`
  - Method '_parse_setup_py' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L224`
  - Method '_detect_frameworks_from_requirements' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L234`
  - Method '_detect_frameworks_from_deps' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L257`
  - Method 'parse_file' returns 'ast.AST | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L265`
  - Method 'extract_symbols' returns 'list[Symbol]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L281`
  - Method '_process_class_node' returns 'Symbol', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L304`
  - Method '_process_function_node' returns 'Symbol', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L344`
  - Method '_find_parent_class' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L353`
  - Method '_get_visibility' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L360`
  - Method '_get_decorator_name' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L369`
  - Method '_get_attr_name' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L378`
  - Method '_get_annotation_str' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L398`
  - Method 'get_function_node' returns 'ast.AST | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L410`
  - Method 'get_function_source' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L424`
  - Method 'get_function_location' returns 'tuple[int, int] | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L431`
  - Method 'analyze_complexity' returns 'ComplexityMetrics | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L451`
  - Method 'analyze_file_complexity' returns 'dict[str, ComplexityMetrics]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L477`
  - Method 'suggest_extractions' returns 'list[ExtractionSuggestion]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L511`
  - Method '_analyze_loop_extraction' returns 'ExtractionSuggestion | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L532`
  - Method '_analyze_if_extraction' returns 'ExtractionSuggestion | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L562`
  - Method '_analyze_try_extraction' returns 'ExtractionSuggestion | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L582`
  - Method 'get_extractable_ranges' returns 'list[dict[str, Any]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L609`
  - Method 'get_violation_context' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L666`
  - Method '_get_complexity_suggestions' returns 'list[dict[str, Any]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L718`
  - Method '_get_length_suggestions' returns 'list[dict[str, Any]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L750`
  - Method '_get_nesting_suggestions' returns 'list[dict[str, Any]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L786`
  - Method '_get_parameter_suggestions' returns 'list[dict[str, Any]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L857`
  - Method 'get_imports' returns 'list[Import]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L890`
  - Method 'get_dependencies' returns 'list[Dependency]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L913`
  - Method '_parse_pyproject_deps' returns 'list[Dependency]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L944`
  - Method '_parse_requirements_txt' returns 'list[Dependency]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L958`
  - Method '_parse_dep_string' returns 'Dependency | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/discovery/zones/detector.py`** (10 violations)

- 🔵 **single-responsibility-modules** at `L53`
  - Class 'ZoneDetector' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L64`
  - Method 'detect_zones' returns 'list[Zone]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L90`
  - Method '_find_markers' returns 'list[Path]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L100`
  - Method '_is_in_existing_zone' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L104`
  - Method '_create_zone_from_marker' returns 'Zone | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L117`
  - Method '_derive_zone_name' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L126`
  - Method '_derive_zone_path' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L138`
  - Method 'detect_zones' returns 'list[Zone]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/discovery/zones/merger.py`** (8 violations)

- 🔵 **single-responsibility-modules** at `L19`
  - Class 'ZoneMerger' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L36`
  - Method 'discovery_mode' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L40`
  - Method 'merge_zones' returns 'list[Zone]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L59`
  - Method '_merge_hybrid' returns 'list[Zone]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L111`
  - Method '_get_manual_zones' returns 'list[Zone]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L137`
  - Method 'merge_zones' returns 'list[Zone]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/embedding_providers.py`** (19 violations)

- 🔵 **single-responsibility-modules** at `L41`
  - Class 'EmbeddingProvider' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L77`
  - Class 'LocalEmbeddingProvider' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L135`
  - Class 'OpenAIEmbeddingProvider' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L193`
  - Class 'VoyageEmbeddingProvider' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L48`
  - Method 'embed' returns 'np.ndarray', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L61`
  - Method 'is_available' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L67`
  - Method 'requires_api_key' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L72`
  - Method 'install_instructions' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L117`
  - Method 'embed' returns 'np.ndarray', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L127`
  - Method 'is_available' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L165`
  - Method 'embed' returns 'np.ndarray', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L183`
  - Method 'is_available' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L223`
  - Method 'embed' returns 'np.ndarray', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L237`
  - Method 'is_available' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L255`
  - Method 'get_embedding_provider' returns 'EmbeddingProvider', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L313`
  - Method 'list_providers' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L333`
  - Method 'get_available_providers' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/generate/domain.py`** (22 violations)

- 🟡 **max-parameter-count** at `L318`
  - Function 'success_result' has 6 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🔵 **single-responsibility-modules** at `L134`
  - Class 'GeneratedFile' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L175`
  - Class 'GenerationContext' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L264`
  - Class 'GenerationResult' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L115`
  - Method 'total_tokens' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L120`
  - Method 'cost_estimate' returns 'float', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L148`
  - Method 'is_new' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L153`
  - Method 'is_modification' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L158`
  - Method 'line_count' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L162`
  - Method 'diff_summary' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L189`
  - Method 'for_red' returns '"GenerationContext"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L207`
  - Method 'for_green' returns '"GenerationContext"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L227`
  - Method 'for_fix' returns '"GenerationContext"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L245`
  - Method 'for_refactor' returns '"GenerationContext"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L278`
  - Method 'tokens_used' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L283`
  - Method 'prompt_tokens' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L288`
  - Method 'completion_tokens' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L293`
  - Method 'file_count' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L298`
  - Method 'total_lines' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L338`
  - Method 'summary' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/generate/engine.py`** (13 violations)

- 🟡 **max-function-length** at `L76`
  - Function 'generate' has 56 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **single-responsibility-modules** at `L33`
  - Class 'GenerationEngine' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L220`
  - Class 'GenerationSession' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L151`
  - Method '_call_llm' returns 'tuple[str, TokenUsage]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L175`
  - Method '_parse_response' returns 'tuple[list[GeneratedFile], str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L193`
  - Method '_write_files' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L302`
  - Method '_record_result' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L309`
  - Method 'total_tokens_used' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L314`
  - Method 'total_files_generated' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L319`
  - Method 'all_succeeded' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L323`
  - Method 'summary' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/generate/parser.py`** (11 violations)

- 🔵 **single-responsibility-modules** at `L21`
  - Class 'ResponseParser' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L63`
  - Method 'parse' returns 'list[GeneratedFile]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L108`
  - Method '_parse_implicit_paths' returns 'list[GeneratedFile]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L141`
  - Method '_clean_content' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L164`
  - Method '_validate_python_syntax' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L184`
  - Method 'extract_explanation' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L205`
  - Method 'parse_with_explanation' returns 'tuple[list[GeneratedFile], str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L257`
  - Method 'parse' returns 'list[GeneratedFile]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L287`
  - Method 'parse_response' returns 'list[GeneratedFile]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/generate/prompt_builder.py`** (17 violations)

- 🔵 **single-responsibility-modules** at `L22`
  - Class 'PromptBuilder' has 13 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L105`
  - Method 'build' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L131`
  - Method '_build_system_section' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L139`
  - Method '_build_context_section' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L185`
  - Method '_format_specification' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L193`
  - Method '_format_existing_code' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L207`
  - Method '_format_patterns' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L225`
  - Method '_format_examples' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L247`
  - Method '_format_error_context' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L271`
  - Method '_build_instructions_section' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L284`
  - Method '_build_output_section' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L313`
  - Method '_get_component_from_spec' returns 'dict[str, Any] | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L328`
  - Method 'estimate_tokens' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L345`
  - Method 'simple_test_prompt' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L373`
  - Method 'simple_impl_prompt' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/generate/provider.py`** (22 violations)

- 🟡 **max-cyclomatic-complexity** at `L138`
  - Function 'generate' has complexity 11 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L138`
  - Function 'generate' has 61 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **single-responsibility-modules** at `L21`
  - Class 'LLMProvider' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L77`
  - Class 'ClaudeProvider' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L226`
  - Class 'ManualProvider' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L30`
  - Method 'generate' returns 'tuple[str, TokenUsage]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L53`
  - Method 'count_tokens' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L67`
  - Method 'model_name' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L72`
  - Method 'is_available' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L129`
  - Method 'model_name' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L134`
  - Method 'is_available' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L138`
  - Method 'generate' returns 'tuple[str, TokenUsage]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L214`
  - Method 'count_tokens' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L252`
  - Method 'model_name' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L257`
  - Method 'is_available' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L261`
  - Method 'generate' returns 'tuple[str, TokenUsage]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L316`
  - Method 'count_tokens' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L321`
  - Method '_load_dotenv_if_needed' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L334`
  - Method 'get_provider' returns 'LLMProvider', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L362`
  - Method 'get_provider_sync' returns 'LLMProvider', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/generate/writer.py`** (18 violations)

- 🔵 **use-pathlib** at `L241`
  - Forbidden pattern found: 'os.path.exists'
  - 💡 *Use pathlib.Path: path.exists(), path.is_file(), path / 'subdir'*
- 🔵 **single-responsibility-modules** at `L38`
  - Class 'CodeWriter' has 15 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L86`
  - Method 'set_metadata' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L97`
  - Method 'write' returns 'list[Path]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L127`
  - Method '_write_file' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L146`
  - Method '_create_or_modify_file' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L180`
  - Method '_delete_file' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L196`
  - Method '_backup_file' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L221`
  - Method '_atomic_write' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L245`
  - Method '_add_header' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L274`
  - Method 'rollback' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L297`
  - Method '_rollback_operation' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L314`
  - Method 'clear_history' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L318`
  - Method 'cleanup_backups' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L343`
  - Method 'operation_count' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L348`
  - Method 'has_pending_operations' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/__init__.py`** (4 violations)

- 🔵 **max-imports** at `L1`
  - File has 102 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **max-imports** at `L1`
  - File has 102 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **max-imports** at `L1`
  - File has 102 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **max-imports** at `L1`
  - File has 102 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*

**`src/agentforge/core/harness/action_parser.py`** (14 violations)

- 🟡 **max-cyclomatic-complexity** at `L45`
  - Function 'parse' has complexity 13 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-nesting-depth** at `L45`
  - Function 'parse' has nesting depth 6 (max: 4)
  - 💡 *Use early returns, guard clauses, or extract nested logic*
- 🟡 **max-nesting-depth** at `L221`
  - Function 'parse_lenient' has nesting depth 5 (max: 4)
  - 💡 *Use early returns, guard clauses, or extract nested logic*
- 🔵 **single-responsibility-modules** at `L24`
  - Class 'ActionParser' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L45`
  - Method 'parse' returns 'AgentAction', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L99`
  - Method '_extract_thinking' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L104`
  - Method '_extract_action' returns 'tuple[ActionType, str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L131`
  - Method '_infer_action' returns 'tuple[ActionType, str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L167`
  - Method '_parse_tool_calls' returns 'list[ToolCall]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L193`
  - Method '_parse_parameters' returns 'dict[str, str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L204`
  - Method '_extract_element' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L221`
  - Method 'parse_lenient' returns 'AgentAction', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/agent_monitor.py`** (18 violations)

- 🟡 **max-cyclomatic-complexity** at `L114`
  - Function 'detect_loop' has complexity 20 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-cyclomatic-complexity** at `L218`
  - Function 'detect_thrashing' has complexity 12 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-cyclomatic-complexity** at `L296`
  - Function 'get_health' has complexity 23 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L114`
  - Function 'detect_loop' has 53 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L296`
  - Function 'get_health' has 76 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **no-god-classes** at `L42`
  - Class 'AgentMonitor' has 16 methods (max: 15)
  - 💡 *Split large classes using composition or inheritance*
- 🔵 **single-responsibility-modules** at `L42`
  - Class 'AgentMonitor' has 16 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L114`
  - Method 'detect_loop' returns 'LoopDetection | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L182`
  - Method '_extract_keywords' returns 'set[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L188`
  - Method '_get_recent_keywords' returns 'set[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L198`
  - Method 'detect_drift' returns 'float', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L218`
  - Method 'detect_thrashing' returns 'ThrashingDetection | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L263`
  - Method 'get_context_pressure' returns 'float', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L269`
  - Method 'get_progress_score' returns 'float', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L296`
  - Method 'get_health' returns 'AgentHealth', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L397`
  - Method 'get_recent_observations' returns 'list[Observation]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/agent_orchestrator.py`** (22 violations)

- 🟡 **max-function-length** at `L98`
  - Function 'start_session' has 54 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L227`
  - Function 'execute_step' has 65 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L313`
  - Function '_execute_llm_step' has 65 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-parameter-count** at `L45`
  - Function '__init__' has 10 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🟡 **max-parameter-count** at `L98`
  - Function 'start_session' has 6 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🟡 **max-file-lines** at `file`
  - File exceeds line limit (706 lines > 500)
  - 💡 *Consider splitting into smaller files*
- 🟡 **no-god-classes** at `L34`
  - Class 'AgentOrchestrator' has 17 methods (max: 15)
  - 💡 *Split large classes using composition or inheritance*
- 🔵 **single-responsibility-modules** at `L34`
  - Class 'AgentOrchestrator' has 17 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L98`
  - Method 'start_session' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L167`
  - Method '_init_llm_context' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L198`
  - Method 'resume_session' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L435`
  - Method 'pause_session' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L462`
  - Method 'get_status' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L500`
  - Method 'get_available_tools' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L520`
  - Method 'handle_health_check' returns 'RecoveryAttempt | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L562`
  - Method 'handle_escalation' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L600`
  - Method 'complete_session' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L634`
  - Method 'fail_session' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L671`
  - Method 'cleanup' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L686`
  - Method '_create_checkpoint' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/agent_prompt_builder.py`** (12 violations)

- 🔵 **single-responsibility-modules** at `L84`
  - Class 'AgentPromptBuilder' has 10 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L95`
  - Method 'build_system_prompt' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L108`
  - Method 'build_user_prompt' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L135`
  - Method 'build_messages' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L167`
  - Method '_build_tools_section' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L189`
  - Method '_build_task_section' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L197`
  - Method '_build_memory_section' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L204`
  - Method '_build_history_section' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L222`
  - Method '_build_status_section' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L232`
  - Method 'format_tool_results' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/auto_fix_daemon.py`** (12 violations)

- 🔵 **single-responsibility-modules** at `L92`
  - Class 'AutoFixDaemon' has 10 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L35`
  - Method 'to_dict' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L49`
  - Method 'from_dict' returns '"AutoFixConfig"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L79`
  - Method 'to_dict' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L140`
  - Method 'should_attempt_fix' returns 'tuple', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L163`
  - Method 'get_next_violation' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L186`
  - Method 'get_status' returns 'DaemonStatus', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L190`
  - Method 'run_once' returns 'FixAttempt | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L263`
  - Method 'run_batch' returns 'list[FixAttempt]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L335`
  - Method 'create_auto_fix_daemon' returns 'AutoFixDaemon', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/checkpoint_manager.py`** (12 violations)

- 🟡 **max-function-length** at `L36`
  - Function 'create_checkpoint' has 55 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-nesting-depth** at `L182`
  - Function 'delete_checkpoint' has nesting depth 5 (max: 4)
  - 💡 *Use early returns, guard clauses, or extract nested logic*
- 🔵 **single-responsibility-modules** at `L22`
  - Class 'CheckpointManager' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L36`
  - Method 'create_checkpoint' returns 'Checkpoint', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L108`
  - Method 'restore_checkpoint' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L139`
  - Method 'list_checkpoints' returns 'list[Checkpoint]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L166`
  - Method 'get_checkpoint' returns 'Checkpoint | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L182`
  - Method 'delete_checkpoint' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L202`
  - Method 'cleanup_old_checkpoints' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L219`
  - Method '_load_checkpoint' returns 'Checkpoint | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/conformance_tools.py`** (9 violations)

- 🟡 **max-cyclomatic-complexity** at `L243`
  - Function 'run_conformance_check' has complexity 12 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-cyclomatic-complexity** at `L330`
  - Function 'get_check_definition' has complexity 11 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L243`
  - Function 'run_conformance_check' has 69 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **single-responsibility-modules** at `L37`
  - Class 'ConformanceTools' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L57`
  - Method '_get_registry' returns 'ContractRegistry', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L63`
  - Method '_find_check_by_id' returns 'dict[str, Any] | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L396`
  - Method 'get_tool_executors' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/escalation_domain.py`** (2 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/escalation_manager.py`** (16 violations)

- 🟡 **max-parameter-count** at `L49`
  - Function 'create_escalation' has 6 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🔵 **single-responsibility-modules** at `L28`
  - Class 'EscalationManager' has 13 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L49`
  - Method 'create_escalation' returns 'Escalation', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L88`
  - Method 'acknowledge_escalation' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L111`
  - Method 'resolve_escalation' returns 'EscalationResolution', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L151`
  - Method 'get_escalation' returns 'Escalation | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L171`
  - Method 'list_escalations' returns 'list[Escalation]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L209`
  - Method 'get_pending_escalations' returns 'list[Escalation]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L226`
  - Method 'check_timeouts' returns 'list[Escalation]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L246`
  - Method 'cancel_escalation' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L267`
  - Method '_save_escalation' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L275`
  - Method '_save_resolution' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L290`
  - Method '_escalation_to_dict' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L306`
  - Method '_dict_to_escalation' returns 'Escalation', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/escalation_notifier.py`** (11 violations)

- 🟡 **max-nesting-depth** at `L45`
  - Function 'notify' has nesting depth 6 (max: 4)
  - 💡 *Use early returns, guard clauses, or extract nested logic*
- 🔵 **single-responsibility-modules** at `L19`
  - Class 'EscalationNotifier' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L45`
  - Method 'notify' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L75`
  - Method 'notify_cli' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L111`
  - Method 'notify_file' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L142`
  - Method 'notify_webhook' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L170`
  - Method 'format_escalation' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L230`
  - Method 'get_priority_color' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L241`
  - Method '_escalation_to_dict' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/execution_context_store.py`** (11 violations)

- 🔵 **single-responsibility-modules** at `L22`
  - Class 'ExecutionContextStore' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L40`
  - Method '_get_session_dir' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L44`
  - Method 'save_context' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L76`
  - Method 'load_context' returns 'ExecutionContext | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L98`
  - Method 'append_step' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L177`
  - Method 'delete_context' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L204`
  - Method 'list_sessions' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L222`
  - Method 'get_step_count' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L245`
  - Method 'create_execution_store' returns 'ExecutionContextStore', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/fix_violation_workflow.py`** (15 violations)

- 🟡 **max-cyclomatic-complexity** at `L227`
  - Function 'fix_violation' has complexity 19 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-cyclomatic-complexity** at `L339`
  - Function '_determine_phase' has complexity 16 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L227`
  - Function 'fix_violation' has 83 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-nesting-depth** at `L227`
  - Function 'fix_violation' has nesting depth 8 (max: 4)
  - 💡 *Use early returns, guard clauses, or extract nested logic*
- 🟡 **max-nesting-depth** at `L339`
  - Function '_determine_phase' has nesting depth 5 (max: 4)
  - 💡 *Use early returns, guard clauses, or extract nested logic*
- 🔵 **single-responsibility-modules** at `L150`
  - Class 'FixViolationWorkflow' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L53`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L69`
  - Method 'from_dict' returns '"FixAttempt"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L194`
  - Method '_build_tool_list' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L213`
  - Method '_format_step_history' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L227`
  - Method 'fix_violation' returns 'FixAttempt', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L339`
  - Method '_determine_phase' returns 'FixPhase', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L368`
  - Method 'create_fix_workflow' returns 'FixViolationWorkflow', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/git_tools.py`** (5 violations)

- 🔵 **single-responsibility-modules** at `L20`
  - Class 'GitTools' has 10 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L238`
  - Method 'get_pending_commit' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L273`
  - Method 'get_tool_executors' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/llm_executor.py`** (9 violations)

- 🟡 **max-parameter-count** at `L45`
  - Function '__init__' has 6 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🔵 **single-responsibility-modules** at `L34`
  - Class 'LLMExecutor' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L71`
  - Method 'register_tool' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L80`
  - Method 'register_tools' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L138`
  - Method '_call_llm' returns 'tuple[str, int]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L192`
  - Method '_messages_to_prompt' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L311`
  - Method 'create_default_executor' returns 'LLMExecutor', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/llm_executor_domain.py`** (36 violations)

- 🟡 **max-cyclomatic-complexity** at `L56`
  - Function '_infer_category' has complexity 15 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🔵 **single-responsibility-modules** at `L44`
  - Class 'ToolCall' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L97`
  - Class 'ToolResult' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L153`
  - Class 'AgentAction' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L228`
  - Class 'ConversationMessage' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L283`
  - Class 'ExecutionContext' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L357`
  - Class 'StepResult' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L56`
  - Method '_infer_category' returns 'ToolCategory', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L77`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L86`
  - Method 'from_dict' returns '"ToolCall"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L126`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L163`
  - Method 'tool_action' returns '"AgentAction"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L172`
  - Method 'think_action' returns '"AgentAction"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L180`
  - Method 'respond_action' returns '"AgentAction"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L189`
  - Method 'complete_action' returns '"AgentAction"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L198`
  - Method 'escalate_action' returns '"AgentAction"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L205`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L216`
  - Method 'from_dict' returns '"AgentAction"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L238`
  - Method 'user_message' returns '"ConversationMessage"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L243`
  - Method 'assistant_message' returns '"ConversationMessage"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L252`
  - Method 'tool_result_message' returns '"ConversationMessage"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L260`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L271`
  - Method 'from_dict' returns '"ConversationMessage"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L297`
  - Method 'tokens_remaining' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L302`
  - Method 'recent_messages' returns 'list[ConversationMessage]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L306`
  - Method 'add_user_message' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L310`
  - Method 'add_assistant_message' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L320`
  - Method 'add_tool_results' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L326`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L341`
  - Method 'from_dict' returns '"ExecutionContext"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L403`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L437`
  - Method 'total_tokens' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L441`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L449`
  - Method 'from_dict' returns '"TokenUsage"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/memory_domain.py`** (8 violations)

- 🔵 **single-responsibility-modules** at `L26`
  - Class 'MemoryEntry' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L59`
  - Method 'create' returns '"MemoryEntry"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L85`
  - Method 'is_expired' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L97`
  - Method 'timestamp' returns 'datetime', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L101`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L122`
  - Method 'from_dict' returns '"MemoryEntry"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/memory_manager.py`** (5 violations)

- 🔵 **single-responsibility-modules** at `L20`
  - Class 'MemoryManager' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L113`
  - Method 'search' returns 'list[dict[str, Any]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L149`
  - Method 'get_context' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/memory_store.py`** (8 violations)

- 🔵 **single-responsibility-modules** at `L26`
  - Class 'MemoryStore' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L90`
  - Method 'delete' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L108`
  - Method 'list_keys' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L126`
  - Method 'clear_tier' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L139`
  - Method '_load_tier' returns 'dict[str, MemoryEntry]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L170`
  - Method '_save_tier' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/minimal_context/__init__.py`** (4 violations)

- 🔵 **max-imports** at `L1`
  - File has 44 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **max-imports** at `L1`
  - File has 44 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **max-imports** at `L1`
  - File has 44 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **max-imports** at `L1`
  - File has 44 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*

**`src/agentforge/core/harness/minimal_context/adaptive_budget.py`** (13 violations)

- 🟡 **max-cyclomatic-complexity** at `L191`
  - Function '_update_progress' has complexity 13 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🔵 **single-responsibility-modules** at `L30`
  - Class 'AdaptiveBudget' has 10 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L75`
  - Method 'check_continue' returns 'tuple[bool, str, LoopDetection | None]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L128`
  - Method '_check_enhanced_loops' returns 'LoopDetection | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L159`
  - Method '_detect_runaway_legacy' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L181`
  - Method 'get_last_loop_detection' returns 'LoopDetection | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L185`
  - Method 'get_loop_suggestions' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L191`
  - Method '_update_progress' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L230`
  - Method '_parse_violation_count' returns 'int | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L240`
  - Method '_calculate_budget' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L246`
  - Method 'reset' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/minimal_context/context_models.py`** (15 violations)

- 🔵 **single-responsibility-modules** at `L176`
  - Class 'Understanding' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L300`
  - Class 'AgentContext' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L27`
  - Method '_utc_now' returns 'datetime', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L81`
  - Method 'round_confidence' returns 'float', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L189`
  - Method 'get_active_facts' returns 'list[Fact]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L193`
  - Method 'get_by_category' returns 'list[Fact]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L197`
  - Method 'get_high_confidence' returns 'list[Fact]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L201`
  - Method 'compact' returns '"Understanding"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L222`
  - Method 'score_fact' returns 'float', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L318`
  - Method 'estimate_tokens' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L334`
  - Method 'to_yaml' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L377`
  - Method '_format_understanding' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L393`
  - Method '_format_actions' returns 'list[dict[str, str]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/minimal_context/executor.py`** (44 violations)

- 🟡 **max-cyclomatic-complexity** at `L255`
  - Function '_handle_phase_transition' has complexity 17 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-cyclomatic-complexity** at `L595`
  - Function '_validate_response_parameters' has complexity 12 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-cyclomatic-complexity** at `L741`
  - Function 'run_until_complete' has complexity 30 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-cyclomatic-complexity** at `L894`
  - Function 'run_task_native' has complexity 20 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L103`
  - Function '__init__' has 71 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L255`
  - Function '_handle_phase_transition' has 54 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L345`
  - Function 'execute_step' has 92 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L632`
  - Function '_execute_action' has 52 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L741`
  - Function 'run_until_complete' has 127 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L894`
  - Function 'run_task_native' has 107 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-nesting-depth** at `L255`
  - Function '_handle_phase_transition' has nesting depth 5 (max: 4)
  - 💡 *Use early returns, guard clauses, or extract nested logic*
- 🟡 **max-nesting-depth** at `L741`
  - Function 'run_until_complete' has nesting depth 5 (max: 4)
  - 💡 *Use early returns, guard clauses, or extract nested logic*
- 🟡 **max-parameter-count** at `L103`
  - Function '__init__' has 11 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🟡 **max-class-size** at `L80`
  - Class 'MinimalContextExecutor' has 21 methods (max: 20)
  - 💡 *Consider splitting into multiple classes with single responsibilities*
- 🟡 **max-file-lines** at `file`
  - File exceeds line limit (1142 lines > 500)
  - 💡 *Consider splitting into smaller files*
- 🟡 **no-god-classes** at `L80`
  - Class 'MinimalContextExecutor' has 21 methods (max: 15)
  - 💡 *Split large classes using composition or inheritance*
- 🔵 **single-responsibility-modules** at `L80`
  - Class 'MinimalContextExecutor' has 21 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **max-imports** at `L1`
  - File has 40 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **max-imports** at `L1`
  - File has 40 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **max-imports** at `L1`
  - File has 40 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **max-imports** at `L1`
  - File has 40 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **default-result-return-types** at `L196`
  - Method 'register_action' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L202`
  - Method 'register_actions' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L219`
  - Method '_build_phase_context' returns 'PhaseContext', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L255`
  - Method '_handle_phase_transition' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L316`
  - Method '_log_step' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L345`
  - Method 'execute_step' returns 'StepOutcome', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L467`
  - Method '_call_llm' returns 'tuple', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L501`
  - Method '_messages_to_prompt' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L513`
  - Method '_parse_action' returns 'tuple', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L555`
  - Method '_parse_and_validate_yaml' returns 'tuple | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L595`
  - Method '_validate_response_parameters' returns 'tuple[bool, str | None]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L632`
  - Method '_execute_action' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L691`
  - Method '_should_continue' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L706`
  - Method '_extract_and_store_facts' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L741`
  - Method 'run_until_complete' returns 'list[StepOutcome]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L894`
  - Method 'run_task_native' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L1029`
  - Method '_process_native_response' returns 'StepOutcome', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L1080`
  - Method '_update_phase_from_action' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L1100`
  - Method 'get_native_tool_executor' returns 'NativeToolExecutor', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L1105`
  - Method 'create_executor' returns 'MinimalContextExecutor', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L1135`
  - Method 'should_use_native_tools' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/minimal_context/fix_workflow.py`** (60 violations)

- 🟡 **max-cyclomatic-complexity** at `L423`
  - Function '_action_read_file' has complexity 11 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-cyclomatic-complexity** at `L302`
  - Function 'wrapper' has complexity 11 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-cyclomatic-complexity** at `L868`
  - Function 'wrapper' has complexity 14 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L346`
  - Function '_validate_python_file' has 59 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L613`
  - Function '_action_replace_lines' has 56 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L858`
  - Function '_wrap_extract_function' has 54 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L1351`
  - Function 'fix_violation' has 108 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-parameter-count** at `L833`
  - Function '_update_verification_and_context' has 6 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🟡 **max-class-size** at `L116`
  - Class 'MinimalContextFixWorkflow' has 40 methods (max: 20)
  - 💡 *Consider splitting into multiple classes with single responsibilities*
- 🟡 **max-file-lines** at `file`
  - File exceeds line limit (1582 lines > 500)
  - 💡 *Consider splitting into smaller files*
- 🟡 **no-god-classes** at `L116`
  - Class 'MinimalContextFixWorkflow' has 40 methods (max: 15)
  - 💡 *Split large classes using composition or inheritance*
- 🔵 **single-responsibility-modules** at `L116`
  - Class 'MinimalContextFixWorkflow' has 40 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L51`
  - Method '_detect_source_indent' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L59`
  - Method '_adjust_content_indentation' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L75`
  - Method '_validate_replace_params' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L88`
  - Method '_validate_insert_params' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L101`
  - Method '_extract_function_name_from_output' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L190`
  - Method '_build_action_executors' returns 'dict[str, Callable]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L243`
  - Method '_track_modified_file' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L253`
  - Method '_save_file_for_revert' returns 'tuple[str | None, bool]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L262`
  - Method '_revert_file_changes' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L274`
  - Method '_build_test_revert_result' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L296`
  - Method '_with_test_verification' returns 'Callable', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L302`
  - Method 'wrapper' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L346`
  - Method '_validate_python_file' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L423`
  - Method '_action_read_file' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L488`
  - Method '_action_edit_file' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L537`
  - Method '_fuzzy_find_and_replace' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L550`
  - Method 'normalize' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L613`
  - Method '_action_replace_lines' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L689`
  - Method '_detect_insert_indentation' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L700`
  - Method '_process_insert_content' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L715`
  - Method '_action_insert_lines' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L754`
  - Method '_action_write_file' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L801`
  - Method '_check_tests_worsened' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L811`
  - Method '_build_revert_result' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L833`
  - Method '_update_verification_and_context' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L858`
  - Method '_wrap_extract_function' returns 'Callable', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L923`
  - Method '_count_test_failures' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L934`
  - Method '_action_run_check' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L978`
  - Method '_maybe_refresh_context_for_new_function' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L991`
  - Method '_refresh_precomputed_context' returns 'dict[str, Any] | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L1042`
  - Method '_action_run_tests' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L1076`
  - Method '_action_load_context' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L1114`
  - Method '_action_plan_fix' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L1133`
  - Method '_read_source_file' returns 'tuple[str, list[str]] | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L1141`
  - Method '_find_violating_function' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L1152`
  - Method '_add_provider_context' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L1173`
  - Method '_add_extraction_suggestions' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L1193`
  - Method '_add_class_context' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L1211`
  - Method '_add_check_definition' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L1222`
  - Method '_add_file_context' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L1234`
  - Method '_precompute_violation_context' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L1274`
  - Method '_add_python_context' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L1300`
  - Method '_validate_extraction_suggestions' returns 'list[dict[str, Any]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L1351`
  - Method 'fix_violation' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L1490`
  - Method 'resume_task' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L1549`
  - Method 'create_minimal_fix_workflow' returns 'MinimalContextFixWorkflow', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/minimal_context/loop_detector.py`** (18 violations)

- 🟡 **max-cyclomatic-complexity** at `L212`
  - Function '_check_identical' has complexity 11 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-cyclomatic-complexity** at `L288`
  - Function '_check_semantic_loop' has complexity 14 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-cyclomatic-complexity** at `L338`
  - Function '_check_no_progress' has complexity 11 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🔵 **single-responsibility-modules** at `L79`
  - Class 'LoopDetector' has 12 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L65`
  - Method 'matches' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L116`
  - Method 'check' returns 'LoopDetection', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L161`
  - Method '_to_signature' returns 'ActionSignature', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L185`
  - Method '_categorize_action' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L199`
  - Method '_categorize_error' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L212`
  - Method '_check_identical' returns 'LoopDetection', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L248`
  - Method '_check_error_cycle' returns 'LoopDetection', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L288`
  - Method '_check_semantic_loop' returns 'LoopDetection', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L338`
  - Method '_check_no_progress' returns 'LoopDetection', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L388`
  - Method '_suggest_for_identical' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L442`
  - Method 'get_summary' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L464`
  - Method 'reset' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/minimal_context/native_tool_executor.py`** (13 violations)

- 🟡 **max-function-length** at `L112`
  - Function 'execute' has 53 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **single-responsibility-modules** at `L63`
  - Class 'NativeToolExecutor' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L91`
  - Method 'register_action' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L102`
  - Method 'register_actions' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L183`
  - Method '_log_execution' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L199`
  - Method 'get_execution_log' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L203`
  - Method 'clear_execution_log' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L207`
  - Method 'has_action' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L211`
  - Method 'list_actions' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L216`
  - Method 'create_enhanced_handlers' returns 'dict[str, ActionHandler]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L237`
  - Method 'create_fix_violation_handlers' returns 'dict[str, ActionHandler]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/minimal_context/phase_machine.py`** (26 violations)

- 🟡 **max-function-length** at `L150`
  - Function '_setup_default_transitions' has 104 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-file-lines** at `file`
  - File exceeds line limit (502 lines > 500)
  - 💡 *Consider splitting into smaller files*
- 🟡 **no-god-classes** at `L128`
  - Class 'PhaseMachine' has 19 methods (max: 15)
  - 💡 *Split large classes using composition or inheritance*
- 🔵 **single-responsibility-modules** at `L128`
  - Class 'PhaseMachine' has 19 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L90`
  - Method 'has_modifications' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L93`
  - Method 'has_fact_of_type' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L150`
  - Method '_setup_default_transitions' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L274`
  - Method '_setup_default_phase_configs' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L312`
  - Method 'add_transition' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L318`
  - Method 'configure_phase' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L323`
  - Method 'current_phase' returns 'Phase', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L327`
  - Method 'steps_in_phase' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L331`
  - Method 'phase_history' returns 'list[Phase]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L334`
  - Method 'can_transition' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L346`
  - Method 'get_available_transitions' returns 'list[Transition]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L351`
  - Method 'transition' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L384`
  - Method 'advance_step' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L388`
  - Method 'validate_state' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L434`
  - Method '_find_forward_transition' returns 'Phase | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L448`
  - Method 'should_auto_transition' returns 'Phase | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L469`
  - Method 'get_phase_info' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L480`
  - Method 'to_state' returns 'PhaseState', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L489`
  - Method 'from_state' returns '"PhaseMachine"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L497`
  - Method 'reset' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/minimal_context/state_store.py`** (34 violations)

- 🟡 **max-parameter-count** at `L211`
  - Function 'create_task' has 6 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🟡 **max-parameter-count** at `L385`
  - Function 'record_action' has 8 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🟡 **max-file-lines** at `file`
  - File exceeds line limit (544 lines > 500)
  - 💡 *Consider splitting into smaller files*
- 🟡 **no-god-classes** at `L196`
  - Class 'TaskStateStore' has 18 methods (max: 15)
  - 💡 *Split large classes using composition or inheritance*
- 🔵 **single-responsibility-modules** at `L131`
  - Class 'TaskState' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L196`
  - Class 'TaskStateStore' has 18 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L52`
  - Method '_utc_now' returns 'datetime', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L70`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L84`
  - Method 'from_dict' returns '"ActionRecord"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L108`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L119`
  - Method 'from_dict' returns '"VerificationStatus"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L154`
  - Method 'to_task_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L165`
  - Method 'to_state_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L178`
  - Method 'get_phase_machine' returns '"PhaseMachine"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L191`
  - Method 'set_phase_machine' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L208`
  - Method '_task_dir' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L211`
  - Method 'create_task' returns 'TaskState', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L269`
  - Method 'load' returns 'TaskState | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L318`
  - Method '_migrate_state' returns 'tuple[dict[str, Any], bool]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L355`
  - Method '_save_state' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L362`
  - Method 'update_phase' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L369`
  - Method 'update_phase_machine' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L376`
  - Method 'increment_step' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L385`
  - Method 'record_action' returns 'ActionRecord', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L439`
  - Method 'get_recent_actions' returns 'list[ActionRecord]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L453`
  - Method 'update_verification' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L474`
  - Method 'update_context_data' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L481`
  - Method 'set_error' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L489`
  - Method 'save_artifact' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L507`
  - Method 'load_artifact' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L519`
  - Method 'list_tasks' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L536`
  - Method 'delete_task' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/minimal_context/step_outcome.py`** (5 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L49`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L75`
  - Method 'is_terminal' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L79`
  - Method 'is_error' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/minimal_context/template_context_builder.py`** (22 violations)

- 🟡 **max-cyclomatic-complexity** at `L325`
  - Function '_get_precomputed' has complexity 11 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-cyclomatic-complexity** at `L362`
  - Function '_get_domain_context' has complexity 11 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-cyclomatic-complexity** at `L404`
  - Function '_format_user_message' has complexity 11 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-nesting-depth** at `L325`
  - Function '_get_precomputed' has nesting depth 5 (max: 4)
  - 💡 *Use early returns, guard clauses, or extract nested logic*
- 🟡 **max-file-lines** at `file`
  - File exceeds line limit (521 lines > 500)
  - 💡 *Consider splitting into smaller files*
- 🔵 **single-responsibility-modules** at `L68`
  - Class 'TemplateContextBuilder' has 15 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L116`
  - Method 'build' returns 'TemplateStepContext', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L188`
  - Method 'build_messages' returns 'list[dict[str, str]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L205`
  - Method 'get_token_breakdown' returns 'dict[str, int]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L219`
  - Method '_get_phase_name' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L232`
  - Method '_get_standard_phase' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L257`
  - Method '_build_task_spec' returns 'TaskSpec', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L267`
  - Method '_build_state_spec' returns 'StateSpec', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L325`
  - Method '_get_precomputed' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L362`
  - Method '_get_domain_context' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L404`
  - Method '_format_user_message' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L450`
  - Method '_format_available_actions' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L489`
  - Method '_format_directive' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L500`
  - Method '_calculate_token_breakdown' returns 'dict[str, int]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L518`
  - Method 'phases' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/minimal_context/tool_handlers/__init__.py`** (13 violations)

- 🔵 **default-result-return-types** at `L63`
  - Method 'create_standard_handlers' returns 'dict[str, ActionHandler]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L101`
  - Method 'create_fix_violation_handlers' returns 'dict[str, ActionHandler]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L124`
  - Method 'create_minimal_handlers' returns 'dict[str, ActionHandler]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L174`
  - Method 'register' returns '"ToolHandlerRegistry"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L188`
  - Method 'register_all' returns '"ToolHandlerRegistry"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L203`
  - Method 'add_file_handlers' returns '"ToolHandlerRegistry"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L216`
  - Method 'add_search_handlers' returns '"ToolHandlerRegistry"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L227`
  - Method 'add_verify_handlers' returns '"ToolHandlerRegistry"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L238`
  - Method 'add_terminal_handlers' returns '"ToolHandlerRegistry"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L251`
  - Method 'add_all' returns '"ToolHandlerRegistry"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L260`
  - Method 'get_handlers' returns 'dict[str, ActionHandler]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L264`
  - Method 'has_handler' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L268`
  - Method 'list_handlers' returns 'list', expected pattern 'Result|Either|Success|Failure'

**`src/agentforge/core/harness/minimal_context/tool_handlers/constants.py`** (2 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/minimal_context/tool_handlers/file_handlers.py`** (21 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L31`
  - Method '_detect_line_indent' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L38`
  - Method '_detect_content_indent' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L46`
  - Method '_adjust_lines_indentation' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L62`
  - Method '_process_insert_content' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L80`
  - Method '_validate_edit_params' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L93`
  - Method '_validate_replace_params' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L106`
  - Method '_validate_insert_params' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L119`
  - Method '_validate_line_range' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L129`
  - Method '_validate_line_number' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L139`
  - Method 'create_read_file_handler' returns 'ActionHandler', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L151`
  - Method 'handler' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L193`
  - Method 'create_write_file_handler' returns 'ActionHandler', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L205`
  - Method 'handler' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L242`
  - Method 'create_edit_file_handler' returns 'ActionHandler', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L257`
  - Method 'handler' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L323`
  - Method 'create_replace_lines_handler' returns 'ActionHandler', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L337`
  - Method 'handler' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L387`
  - Method 'create_insert_lines_handler' returns 'ActionHandler', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L401`
  - Method 'handler' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/minimal_context/tool_handlers/search_handlers.py`** (23 violations)

- 🟡 **max-cyclomatic-complexity** at `L186`
  - Function 'handler' has complexity 13 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L172`
  - Function 'create_load_context_handler' has 68 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L186`
  - Function 'handler' has 57 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-nesting-depth** at `L172`
  - Function 'create_load_context_handler' has nesting depth 5 (max: 4)
  - 💡 *Use early returns, guard clauses, or extract nested logic*
- 🟡 **max-nesting-depth** at `L186`
  - Function 'handler' has nesting depth 5 (max: 4)
  - 💡 *Use early returns, guard clauses, or extract nested logic*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L50`
  - Method '_should_exclude' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L59`
  - Method '_get_search_files' returns 'list[Path]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L70`
  - Method '_search_file' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L86`
  - Method '_format_search_results' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L98`
  - Method '_regex_search' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L118`
  - Method '_semantic_search' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L148`
  - Method 'create_search_code_handler' returns 'ActionHandler', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L152`
  - Method 'handler' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L172`
  - Method 'create_load_context_handler' returns 'ActionHandler', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L186`
  - Method 'handler' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L265`
  - Method '_get_relative_path' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L273`
  - Method '_find_same_dir_files' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L285`
  - Method '_find_test_files' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L304`
  - Method '_find_import_files' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L324`
  - Method 'create_find_related_handler' returns 'ActionHandler', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L328`
  - Method 'handler' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/minimal_context/tool_handlers/terminal_handlers.py`** (16 violations)

- 🟡 **max-cyclomatic-complexity** at `L103`
  - Function 'handler' has complexity 11 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L88`
  - Function 'create_cannot_fix_handler' has 85 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L103`
  - Function 'handler' has 57 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L28`
  - Method 'create_complete_handler' returns 'ActionHandler', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L38`
  - Method 'handler' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L59`
  - Method 'create_escalate_handler' returns 'ActionHandler', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L69`
  - Method 'handler' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L88`
  - Method 'create_cannot_fix_handler' returns 'ActionHandler', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L103`
  - Method 'handler' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L178`
  - Method '_update_violation_status' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L204`
  - Method 'create_request_help_handler' returns 'ActionHandler', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L219`
  - Method 'handler' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L274`
  - Method 'create_plan_fix_handler' returns 'ActionHandler', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L289`
  - Method 'handler' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/minimal_context/tool_handlers/types.py`** (11 violations)

- 🟡 **max-nesting-depth** at `L33`
  - Function 'validate_path_security' has nesting depth 5 (max: 4)
  - 💡 *Use early returns, guard clauses, or extract nested logic*
- 🔵 **single-responsibility-modules** at `L104`
  - Class 'HandlerContext' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L13`
  - Method 'handler' returns 'str

Handlers return result strings (not exceptions) so the LLM can understand
and potentially recover from errors.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

# Type alias for action handlers
ActionHandler = Callable[[dict[str, Any]], str]


class PathValidationError(Exception)', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L33`
  - Method 'validate_path_security' returns 'tuple[Path, str | None]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L112`
  - Method 'violation_id' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L117`
  - Method 'task_id' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L122`
  - Method 'files_examined' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L127`
  - Method 'attempted_approaches' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L132`
  - Method 'understanding' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/minimal_context/tool_handlers/verify_handlers.py`** (21 violations)

- 🟡 **max-cyclomatic-complexity** at `L50`
  - Function 'handler' has complexity 19 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-cyclomatic-complexity** at `L385`
  - Function 'handler' has complexity 11 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L35`
  - Function 'create_run_check_handler' has 82 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L146`
  - Function 'create_run_check_handler_v2' has 89 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L268`
  - Function 'create_run_tests_handler' has 75 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L370`
  - Function 'create_validate_python_handler' has 70 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L385`
  - Function 'handler' has 58 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L35`
  - Method 'create_run_check_handler' returns 'ActionHandler', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L50`
  - Method 'handler' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L113`
  - Method '_run_check_fallback' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L146`
  - Method 'create_run_check_handler_v2' returns 'ActionHandler', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L160`
  - Method 'handler' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L181`
  - Method '_check_violation_resolved' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L243`
  - Method '_run_general_check' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L268`
  - Method 'create_run_tests_handler' returns 'ActionHandler', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L282`
  - Method 'handler' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L330`
  - Method '_run_pytest_fallback' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L370`
  - Method 'create_validate_python_handler' returns 'ActionHandler', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L385`
  - Method 'handler' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/minimal_context/understanding.py`** (25 violations)

- 🟡 **max-file-lines** at `file`
  - File exceeds line limit (511 lines > 500)
  - 💡 *Consider splitting into smaller files*
- 🔵 **single-responsibility-modules** at `L272`
  - Class 'UnderstandingExtractor' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L384`
  - Class 'FactStore' has 12 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L58`
  - Method 'add_rule' returns '"ExtractionRuleSet"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L62`
  - Method 'extract' returns 'list[Fact]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L101`
  - Method '_build_conformance_rules' returns 'ExtractionRuleSet', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L156`
  - Method '_build_test_rules' returns 'ExtractionRuleSet', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L196`
  - Method '_build_edit_rules' returns 'ExtractionRuleSet', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L225`
  - Method '_build_extract_function_rules' returns 'ExtractionRuleSet', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L302`
  - Method 'register_rule_set' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L306`
  - Method 'extract' returns 'list[Fact]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L355`
  - Method '_llm_extract' returns 'list[Fact]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L401`
  - Method 'add' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L424`
  - Method 'add_many' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L429`
  - Method 'get_active' returns 'list[Fact]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L433`
  - Method 'get_by_category' returns 'list[Fact]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L437`
  - Method 'get_recent' returns 'list[Fact]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L442`
  - Method '_should_supersede' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L460`
  - Method '_compact' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L481`
  - Method '_score_fact' returns 'float', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L495`
  - Method 'to_understanding' returns 'Understanding', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L502`
  - Method 'clear' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L507`
  - Method 'from_understanding' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/minimal_context/working_memory.py`** (32 violations)

- 🟡 **max-parameter-count** at `L118`
  - Function 'add' has 6 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🟡 **max-parameter-count** at `L395`
  - Function 'add_fact' has 7 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🟡 **max-class-size** at `L74`
  - Class 'WorkingMemoryManager' has 21 methods (max: 20)
  - 💡 *Consider splitting into multiple classes with single responsibilities*
- 🟡 **max-file-lines** at `file`
  - File exceeds line limit (569 lines > 500)
  - 💡 *Consider splitting into smaller files*
- 🟡 **no-god-classes** at `L74`
  - Class 'WorkingMemoryManager' has 21 methods (max: 15)
  - 💡 *Split large classes using composition or inheritance*
- 🔵 **single-responsibility-modules** at `L74`
  - Class 'WorkingMemoryManager' has 21 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L28`
  - Method '_utc_now' returns 'datetime', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L44`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L56`
  - Method 'from_dict' returns '"WorkingMemoryItem"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L67`
  - Method 'is_expired' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L95`
  - Method '_load' returns 'list[WorkingMemoryItem]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L106`
  - Method '_save' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L118`
  - Method 'add' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L159`
  - Method 'add_action_result' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L186`
  - Method 'load_context' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L210`
  - Method 'get_items' returns 'list[WorkingMemoryItem]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L230`
  - Method 'get_by_type' returns 'list[WorkingMemoryItem]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L239`
  - Method 'get_action_results' returns 'list[dict[str, Any]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L273`
  - Method 'get_loaded_context' returns 'dict[str, str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L289`
  - Method 'remove' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L308`
  - Method 'clear' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L326`
  - Method '_evict_if_needed' returns 'list[WorkingMemoryItem]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L355`
  - Method 'pin' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L373`
  - Method 'unpin' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L395`
  - Method 'add_fact' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L437`
  - Method 'add_facts_from_list' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L456`
  - Method 'get_facts' returns 'list[dict[str, Any]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L509`
  - Method 'get_high_confidence_facts' returns 'list[dict[str, Any]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L529`
  - Method 'get_facts_for_context' returns 'dict[str, list[str]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L557`
  - Method 'clear_facts' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/monitor_domain.py`** (2 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/orchestrator_domain.py`** (2 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/python_tools.py`** (6 violations)

- 🟡 **max-cyclomatic-complexity** at `L70`
  - Function 'analyze_function' has complexity 17 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L70`
  - Function 'analyze_function' has 65 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **single-responsibility-modules** at `L37`
  - Class 'PythonTools' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L266`
  - Method 'get_tool_executors' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/recovery_domain.py`** (2 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/recovery_executor.py`** (16 violations)

- 🟡 **max-function-length** at `L133`
  - Function 'execute_action' has 60 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-nesting-depth** at `L133`
  - Function 'execute_action' has nesting depth 8 (max: 4)
  - 💡 *Use early returns, guard clauses, or extract nested logic*
- 🔵 **single-responsibility-modules** at `L22`
  - Class 'RecoveryExecutor' has 12 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L74`
  - Method 'execute_recovery' returns 'RecoveryAttempt', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L133`
  - Method 'execute_action' returns 'RecoveryAttempt', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L195`
  - Method 'checkpoint' returns 'RecoveryAttempt', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L227`
  - Method 'rollback' returns 'RecoveryAttempt', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L269`
  - Method 'summarize_context' returns 'RecoveryAttempt', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L327`
  - Method 'reset_state' returns 'RecoveryAttempt', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L356`
  - Method 'escalate' returns 'RecoveryAttempt', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L381`
  - Method 'get_recovery_history' returns 'list[RecoveryAttempt]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L397`
  - Method 'register_policy' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L403`
  - Method 'get_policy_for_issue' returns 'RecoveryPolicy | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L412`
  - Method '_check_cooldown' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/refactoring_tools.py`** (7 violations)

- 🟡 **max-cyclomatic-complexity** at `L130`
  - Function 'simplify_conditional' has complexity 16 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L50`
  - Function 'extract_function' has 63 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L130`
  - Function 'simplify_conditional' has 100 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **single-responsibility-modules** at `L23`
  - Class 'RefactoringTools' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L266`
  - Method 'get_tool_executors' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/rollback_manager.py`** (10 violations)

- 🔵 **single-responsibility-modules** at `L49`
  - Class 'RollbackManager' has 11 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L29`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L39`
  - Method 'from_dict' returns '"BackupManifest"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L65`
  - Method 'create_backup' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L117`
  - Method 'get_current_backup' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L121`
  - Method 'list_backups' returns 'list[BackupManifest]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L226`
  - Method 'cleanup_old_backups' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L328`
  - Method 'get_tool_executors' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/session_domain.py`** (14 violations)

- 🔵 **single-responsibility-modules** at `L30`
  - Class 'TokenBudget' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L95`
  - Class 'SessionContext' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L41`
  - Method 'tokens_remaining' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L46`
  - Method 'utilization_percent' returns 'float', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L53`
  - Method 'is_warning' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L57`
  - Method 'can_continue' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L61`
  - Method 'record_usage' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L65`
  - Method 'extend' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L115`
  - Method 'create' returns '"SessionContext"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L150`
  - Method 'add_artifact' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L174`
  - Method 'get_artifacts' returns 'list[SessionArtifact]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L188`
  - Method 'add_history' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/session_manager.py`** (20 violations)

- 🟡 **no-god-classes** at `L36`
  - Class 'SessionManager' has 17 methods (max: 15)
  - 💡 *Split large classes using composition or inheritance*
- 🔵 **single-responsibility-modules** at `L36`
  - Class 'SessionManager' has 17 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L62`
  - Method 'current_session' returns 'SessionContext | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L66`
  - Method 'create' returns 'SessionContext', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L103`
  - Method 'load' returns 'SessionContext | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L118`
  - Method 'save' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L131`
  - Method 'pause' returns 'SessionContext', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L148`
  - Method 'resume' returns 'SessionContext', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L165`
  - Method 'complete' returns 'SessionContext', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L183`
  - Method 'abort' returns 'SessionContext', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L203`
  - Method 'advance_phase' returns 'SessionContext', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L232`
  - Method 'checkpoint_session' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L246`
  - Method 'record_tokens' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L264`
  - Method 'extend_budget' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L281`
  - Method 'add_artifact' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L295`
  - Method 'cleanup_old_sessions' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L333`
  - Method '_require_session' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L338`
  - Method '_transition_to' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/session_store.py`** (12 violations)

- 🔵 **use-pathlib** at `L89`
  - Forbidden pattern found: 'os.path.exists'
  - 💡 *Use pathlib.Path: path.exists(), path.is_file(), path / 'subdir'*
- 🔵 **single-responsibility-modules** at `L32`
  - Class 'SessionStore' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L50`
  - Method 'ensure_directory' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L57`
  - Method 'save' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L95`
  - Method 'load' returns 'SessionContext | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L118`
  - Method 'exists' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L131`
  - Method 'list_sessions' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L147`
  - Method 'delete' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L165`
  - Method '_serialize' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L208`
  - Method '_deserialize' returns 'SessionContext', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/test_runner_tools.py`** (6 violations)

- 🔵 **single-responsibility-modules** at `L15`
  - Class 'RunnerTools' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L181`
  - Method 'get_tool_executors' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🟡 **file-structure** at `file`
  - Test file outside tests/ directory
  - 💡 *Move test files to tests/ directory*
- 🟡 **file-structure** at `file`
  - Test file outside tests/ directory
  - 💡 *Move test files to tests/ directory*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/tool_domain.py`** (8 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L28`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L40`
  - Method 'from_dict' returns ''ToolDefinition'', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L61`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L73`
  - Method 'from_dict' returns ''ToolProfile'', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L91`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L100`
  - Method 'from_dict' returns ''DomainTools'', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/tool_executor_bridge.py`** (7 violations)

- 🔵 **single-responsibility-modules** at `L25`
  - Class 'ToolExecutorBridge' has 12 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L41`
  - Method 'register_custom_tool' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L50`
  - Method 'get_default_executors' returns 'dict[str, ToolExecutor]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L279`
  - Method '_resolve_path' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L287`
  - Method 'create_tool_bridge' returns 'ToolExecutorBridge', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/tool_registry.py`** (14 violations)

- 🔵 **single-responsibility-modules** at `L23`
  - Class 'ToolRegistry' has 12 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L35`
  - Method 'register_tool' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L41`
  - Method 'register_profile' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L46`
  - Method 'register_domain_tools' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L56`
  - Method 'get_tool' returns 'ToolDefinition | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L60`
  - Method 'get_profile' returns 'ToolProfile | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L65`
  - Method 'list_tools' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L69`
  - Method 'list_profiles' returns 'list[ToolProfile]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L73`
  - Method 'get_base_tools' returns 'list[ToolDefinition]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L77`
  - Method 'get_domain_tools' returns 'DomainTools | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L81`
  - Method 'load_from_yaml' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L110`
  - Method 'save_to_yaml' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/tool_selector.py`** (10 violations)

- 🟡 **max-cyclomatic-complexity** at `L25`
  - Function 'get_tools' has complexity 12 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-cyclomatic-complexity** at `L69`
  - Function 'detect_domain' has complexity 16 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-nesting-depth** at `L25`
  - Function 'get_tools' has nesting depth 5 (max: 4)
  - 💡 *Use early returns, guard clauses, or extract nested logic*
- 🔵 **single-responsibility-modules** at `L17`
  - Class 'ToolSelector' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L25`
  - Method 'get_tools' returns 'list[ToolDefinition]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L69`
  - Method 'detect_domain' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L120`
  - Method 'get_tool_names' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L125`
  - Method 'validate_tool_access' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/harness/violation_tools.py`** (9 violations)

- 🟡 **max-cyclomatic-complexity** at `L135`
  - Function 'list_violations' has complexity 14 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L135`
  - Function 'list_violations' has 60 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **single-responsibility-modules** at `L77`
  - Class 'ViolationTools' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L38`
  - Method 'to_summary' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L47`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L62`
  - Method 'from_dict' returns '"ViolationInfo"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L272`
  - Method 'get_tool_executors' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/init.py`** (8 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L20`
  - Method 'get_package_resource_path' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L40`
  - Method 'initialize_project' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L99`
  - Method '_copy_defaults' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L120`
  - Method '_create_repo_yaml' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L147`
  - Method 'is_initialized' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L160`
  - Method 'get_agentforge_dir' returns 'Path | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/lineage/metadata.py`** (8 violations)

- 🟡 **max-cyclomatic-complexity** at `L99`
  - Function 'parse_lineage_from_file' has complexity 11 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-parameter-count** at `L164`
  - Function 'generate_lineage_header' has 9 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L46`
  - Method 'to_header_comments' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L99`
  - Method 'parse_lineage_from_file' returns 'LineageMetadata | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L164`
  - Method 'generate_lineage_header' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L206`
  - Method 'get_test_path_from_lineage' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/llm/__init__.py`** (4 violations)

- 🔵 **max-imports** at `L1`
  - File has 31 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **max-imports** at `L1`
  - File has 31 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **max-imports** at `L1`
  - File has 31 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **max-imports** at `L1`
  - File has 31 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*

**`src/agentforge/core/llm/client.py`** (12 violations)

- 🟡 **max-nesting-depth** at `L136`
  - Function '_build_request_params' has nesting depth 5 (max: 4)
  - 💡 *Use early returns, guard clauses, or extract nested logic*
- 🟡 **max-parameter-count** at `L95`
  - Function 'complete' has 6 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🟡 **max-parameter-count** at `L136`
  - Function '_build_request_params' has 6 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🔵 **single-responsibility-modules** at `L46`
  - Class 'AnthropicLLMClient' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L95`
  - Method 'complete' returns 'LLMResponse', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L136`
  - Method '_build_request_params' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L177`
  - Method '_parse_response' returns 'LLMResponse', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L222`
  - Method '_map_stop_reason' returns 'StopReason', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L232`
  - Method 'get_usage_stats' returns 'dict[str, int]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L241`
  - Method 'reset_usage_stats' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/llm/factory.py`** (11 violations)

- 🔵 **single-responsibility-modules** at `L59`
  - Class 'LLMClientFactory' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L81`
  - Method 'create' returns 'LLMClient', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L133`
  - Method '_create_real_client' returns 'LLMClient', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L148`
  - Method '_create_simulated_client' returns 'SimulatedLLMClient', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L166`
  - Method '_create_playback_client' returns 'SimulatedLLMClient', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L186`
  - Method '_create_recording_client' returns 'LLMClient', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L216`
  - Method 'create_for_testing' returns 'SimulatedLLMClient', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L272`
  - Method 'get_current_mode' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L277`
  - Method 'is_simulated' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/llm/interface.py`** (16 violations)

- 🟡 **max-parameter-count** at `L188`
  - Function 'complete' has 6 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🟡 **max-parameter-count** at `L229`
  - Function 'complete_with_tools' has 6 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🔵 **single-responsibility-modules** at `L162`
  - Class 'LLMClient' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L48`
  - Method '__repr__' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L66`
  - Method 'to_message_content' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L100`
  - Method 'has_tool_calls' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L105`
  - Method 'total_tokens' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L109`
  - Method 'get_first_tool_call' returns 'ToolCall | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L128`
  - Method 'to_api_format' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L152`
  - Method 'to_api_format' returns 'dict[str, Any] | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L188`
  - Method 'complete' returns 'LLMResponse', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L214`
  - Method 'get_usage_stats' returns 'dict[str, int]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L225`
  - Method 'reset_usage_stats' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L229`
  - Method 'complete_with_tools' returns 'LLMResponse', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/llm/recording.py`** (13 violations)

- 🟡 **max-parameter-count** at `L98`
  - Function 'complete' has 6 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🟡 **max-parameter-count** at `L141`
  - Function '_record_exchange' has 7 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🔵 **single-responsibility-modules** at `L52`
  - Class 'RecordingLLMClient' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L98`
  - Method 'complete' returns 'LLMResponse', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L141`
  - Method '_record_exchange' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L178`
  - Method '_preview_message' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L187`
  - Method 'save' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L214`
  - Method 'get_usage_stats' returns 'dict[str, int]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L218`
  - Method 'reset_usage_stats' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L222`
  - Method 'get_recording' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L226`
  - Method 'clear_recording' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/llm/simulated.py`** (25 violations)

- 🟡 **max-parameter-count** at `L393`
  - Function 'complete' has 6 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🟡 **max-file-lines** at `file`
  - File exceeds line limit (503 lines > 500)
  - 💡 *Consider splitting into smaller files*
- 🔵 **single-responsibility-modules** at `L128`
  - Class 'ScriptedResponseStrategy' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L216`
  - Class 'PatternMatchingStrategy' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L333`
  - Class 'SimulatedLLMClient' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L64`
  - Method 'to_llm_response' returns 'LLMResponse', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L102`
  - Method 'get_response' returns 'SimulatedResponse', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L123`
  - Method 'reset' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L176`
  - Method 'get_response' returns 'SimulatedResponse', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L206`
  - Method 'reset' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L211`
  - Method 'remaining_responses' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L243`
  - Method 'add_pattern' returns '"PatternMatchingStrategy"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L261`
  - Method 'set_default' returns '"PatternMatchingStrategy"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L266`
  - Method 'get_response' returns 'SimulatedResponse', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L310`
  - Method 'get_response' returns 'SimulatedResponse', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L328`
  - Method 'reset' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L393`
  - Method 'complete' returns 'LLMResponse', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L439`
  - Method 'get_usage_stats' returns 'dict[str, int]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L448`
  - Method 'reset_usage_stats' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L454`
  - Method 'get_call_history' returns 'list[dict[str, Any]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L458`
  - Method 'clear_history' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L462`
  - Method 'reset' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L470`
  - Method 'create_simple_client' returns 'SimulatedLLMClient', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/llm/tools.py`** (8 violations)

- 🟡 **max-file-lines** at `file`
  - File exceeds line limit (819 lines > 500)
  - 💡 *Consider splitting into smaller files*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L725`
  - Method 'get_tools_for_task' returns 'list[ToolDefinition]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L754`
  - Method 'get_tool_by_name' returns 'ToolDefinition', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L773`
  - Method 'list_task_types' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L783`
  - Method 'list_all_tools' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L793`
  - Method 'get_tools_by_category' returns 'list[ToolDefinition]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/lsp_adapter.py`** (13 violations)

- 🔵 **single-responsibility-modules** at `L56`
  - Class 'LSPAdapter' has 15 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L77`
  - Method 'initialize' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L100`
  - Method '_get_initialize_params' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L170`
  - Method 'get_symbols' returns 'list[Symbol]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L189`
  - Method '_parse_document_symbols' returns 'list[Symbol]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L227`
  - Method '_uri_to_path' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L233`
  - Method 'get_workspace_symbols' returns 'list[Symbol]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L260`
  - Method 'get_definition' returns 'Location | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L295`
  - Method 'get_references' returns 'list[Location]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L326`
  - Method 'get_hover' returns 'HoverInfo | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L361`
  - Method 'get_diagnostics' returns 'list[Diagnostic]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/lsp_adapter_cli.py`** (2 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/lsp_adapters.py`** (15 violations)

- 🔵 **use-pathlib** at `L96`
  - Forbidden pattern found: 'os.path.isfile'
  - 💡 *Use pathlib.Path: path.exists(), path.is_file(), path / 'subdir'*
- 🔵 **single-responsibility-modules** at `L47`
  - Class 'OmniSharpAdapter' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L32`
  - Method '_get_initialization_options' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L36`
  - Method 'find_solution_or_project' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L63`
  - Method 'SERVER_COMMAND' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L71`
  - Method '_get_initialization_options' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L83`
  - Method 'find_solution_or_project' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L94`
  - Method 'is_available' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L131`
  - Method '_is_dotnet_project' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L136`
  - Method '_is_python_project' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L143`
  - Method '_is_typescript_project' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L148`
  - Method '_get_csharp_adapter' returns 'LSPAdapter', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L155`
  - Method 'get_adapter_for_project' returns 'LSPAdapter', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/lsp_client.py`** (8 violations)

- 🔵 **single-responsibility-modules** at `L67`
  - Class 'LSPClient' has 12 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L156`
  - Method '_parse_diagnostic' returns 'Diagnostic', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L182`
  - Method 'send_request' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L238`
  - Method 'get_diagnostics' returns 'list[Diagnostic]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L242`
  - Method '_path_to_uri' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L249`
  - Method '_uri_to_path' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/lsp_types.py`** (4 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L24`
  - Method 'to_1based' returns ''Location'', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L69`
  - Method 'to_string' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/output_validator.py`** (10 violations)

- 🔵 **single-responsibility-modules** at `L22`
  - Class 'OutputValidator' has 12 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L34`
  - Method 'validate' returns 'ContractValidationReport', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L140`
  - Method '_get_field_value' returns 'Any', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L155`
  - Method '_check_regex' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L173`
  - Method '_check_field_equals' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L187`
  - Method '_check_conditional' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L199`
  - Method '_check_count_min' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L210`
  - Method '_eval_simple_condition' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/pipeline/__init__.py`** (4 violations)

- 🔵 **max-imports** at `L1`
  - File has 65 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **max-imports** at `L1`
  - File has 65 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **max-imports** at `L1`
  - File has 65 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **max-imports** at `L1`
  - File has 65 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*

**`src/agentforge/core/pipeline/artifacts.py`** (2 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/pipeline/config.py`** (12 violations)

- 🔵 **single-responsibility-modules** at `L117`
  - Class 'ConfigurationLoader' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L93`
  - Method 'expand_env_vars' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L170`
  - Method 'load_settings' returns 'GlobalSettings', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L204`
  - Method 'load_pipeline_template' returns 'PipelineTemplate', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L222`
  - Method '_load_template_file' returns 'PipelineTemplate', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L249`
  - Method '_create_default_template' returns 'PipelineTemplate', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L261`
  - Method 'load_stage_config' returns 'StageConfig', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L286`
  - Method 'list_available_pipelines' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L296`
  - Method 'create_default_config' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L345`
  - Method 'load' returns 'PipelineConfig', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/pipeline/config_validator.py`** (5 violations)

- 🟡 **max-function-length** at `L45`
  - Function 'validate_template' has 56 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L45`
  - Method 'validate_template' returns 'list[ValidationError]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L115`
  - Method 'validate_settings' returns 'list[ValidationError]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/pipeline/controller.py`** (25 violations)

- 🟡 **max-cyclomatic-complexity** at `L569`
  - Function '_run' has complexity 13 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-cyclomatic-complexity** at `L681`
  - Function '_execute_stage' has complexity 12 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L681`
  - Function '_execute_stage' has 59 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-parameter-count** at `L139`
  - Function '__init__' has 6 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🟡 **max-class-size** at `L132`
  - Class 'PipelineController' has 21 methods (max: 20)
  - 💡 *Consider splitting into multiple classes with single responsibilities*
- 🟡 **max-file-lines** at `file`
  - File exceeds line limit (789 lines > 500)
  - 💡 *Consider splitting into smaller files*
- 🟡 **no-god-classes** at `L132`
  - Class 'PipelineController' has 21 methods (max: 15)
  - 💡 *Split large classes using composition or inheritance*
- 🔵 **single-responsibility-modules** at `L132`
  - Class 'PipelineController' has 21 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L287`
  - Method 'approve' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L331`
  - Method 'reject' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L367`
  - Method 'abort' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L404`
  - Method 'pause' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L431`
  - Method 'list_pipelines' returns 'list[PipelineState]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L448`
  - Method 'provide_feedback' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L470`
  - Method 'get_status' returns 'PipelineState', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L489`
  - Method '_create' returns 'PipelineState', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L506`
  - Method '_load_or_raise' returns 'PipelineState', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L513`
  - Method '_get_contract_enforcer' returns 'ContractEnforcer | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L569`
  - Method '_run' returns 'PipelineState', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L630`
  - Method '_validate_input_with_contracts' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L645`
  - Method '_validate_output_with_contracts' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L754`
  - Method '_get_next_stage' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L766`
  - Method '_handle_escalation' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/pipeline/discovery_integration.py`** (19 violations)

- 🔵 **single-responsibility-modules** at `L37`
  - Class 'DiscoveredContext' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L68`
  - Method 'get_test_path_for_source' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L73`
  - Method 'has_test_for_source' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L77`
  - Method 'get_language_for_file' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L93`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L112`
  - Method '_extract_languages' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L124`
  - Method '_extract_structure' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L137`
  - Method '_extract_test_info' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L150`
  - Method '_extract_dependencies' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L159`
  - Method 'extract_context_from_profile' returns 'DiscoveredContext', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L179`
  - Method 'get_contracts_for_language' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L223`
  - Method 'create_pipeline_context_from_discovery' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L263`
  - Method 'validate_stage_output_for_language' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L294`
  - Method '_validate_red_output_for_language' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L324`
  - Method '_validate_green_output_for_language' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L368`
  - Method '_find_test_in_dirs' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L377`
  - Method 'resolve_test_path' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/pipeline/escalation.py`** (15 violations)

- 🔵 **single-responsibility-modules** at `L111`
  - Class 'EscalationHandler' has 11 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L68`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L85`
  - Method 'from_dict' returns '"Escalation"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L106`
  - Method 'generate_escalation_id' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L129`
  - Method '_get_escalation_path' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L133`
  - Method 'create' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L158`
  - Method 'resolve' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L185`
  - Method 'reject' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L229`
  - Method 'get_pending' returns 'list[Escalation]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L250`
  - Method 'get_for_pipeline' returns 'list[Escalation]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L270`
  - Method '_load_from_file' returns 'Escalation | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L280`
  - Method 'delete' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L297`
  - Method 'cleanup_resolved' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/pipeline/llm_stage_executor.py`** (12 violations)

- 🔵 **single-responsibility-modules** at `L35`
  - Class 'LLMStageExecutor' has 11 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L119`
  - Method 'get_system_prompt' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L135`
  - Method 'get_user_message' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L150`
  - Method 'parse_response' returns 'dict[str, Any] | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L170`
  - Method '_run_with_llm' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L238`
  - Method 'extract_yaml_from_response' returns 'dict | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L271`
  - Method 'extract_json_from_response' returns 'dict | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L306`
  - Method 'validate_input' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L314`
  - Method 'validate_output' returns '"OutputValidation"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L344`
  - Method 'parse_response' returns 'dict[str, Any] | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/pipeline/registry.py`** (13 violations)

- 🔵 **single-responsibility-modules** at `L37`
  - Class 'StageExecutorRegistry' has 10 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L51`
  - Method 'get_instance' returns '"StageExecutorRegistry"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L58`
  - Method 'reset_instance' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L62`
  - Method 'register' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L88`
  - Method 'register_class' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L126`
  - Method 'list_stages' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L135`
  - Method 'has_stage' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L147`
  - Method 'unregister' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L163`
  - Method 'clear' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L169`
  - Method 'get_registry' returns 'StageExecutorRegistry', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L198`
  - Method 'decorator' returns 'type[StageExecutor]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/pipeline/schemas.py`** (9 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L39`
  - Method 'string_enum' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L367`
  - Method 'get_input_schema' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L383`
  - Method 'get_output_schema' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L388`
  - Method 'get_next_stages' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L393`
  - Method 'validate_transition' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L398`
  - Method 'get_required_artifacts_for_stage' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L404`
  - Method 'get_produced_artifacts_by_stage' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/pipeline/stage_executor.py`** (14 violations)

- 🔵 **single-responsibility-modules** at `L56`
  - Class 'StageResult' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L130`
  - Class 'StageExecutor' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L46`
  - Method 'get_artifact' returns 'Any', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L50`
  - Method 'has_artifact' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L117`
  - Method 'is_success' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L121`
  - Method 'is_failed' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L125`
  - Method 'needs_escalation' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L150`
  - Method 'validate_input' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L168`
  - Method 'get_required_inputs' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L179`
  - Method 'get_output_schema' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L191`
  - Method 'stage_name' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L218`
  - Method 'stage_name' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/pipeline/stages/__init__.py`** (3 violations)

- 🔵 **default-result-return-types** at `L72`
  - Method 'register_design_stages' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L88`
  - Method 'register_tdd_stages' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L101`
  - Method 'register_delivery_stages' returns 'None', expected pattern 'Result|Either|Success|Failure'

**`src/agentforge/core/pipeline/stages/analyze.py`** (10 violations)

- 🔵 **single-responsibility-modules** at `L29`
  - Class 'AnalyzeExecutor' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L226`
  - Method 'get_system_prompt' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L230`
  - Method 'get_user_message' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L257`
  - Method 'parse_response' returns 'dict[str, Any] | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L296`
  - Method '_parse_text_response' returns 'dict[str, Any] | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L334`
  - Method 'validate_output' returns 'OutputValidation', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L357`
  - Method 'get_required_inputs' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L362`
  - Method 'create_analyze_executor' returns 'AnalyzeExecutor', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/pipeline/stages/clarify.py`** (10 violations)

- 🔵 **single-responsibility-modules** at `L27`
  - Class 'ClarifyExecutor' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L144`
  - Method 'get_system_prompt' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L148`
  - Method 'get_user_message' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L188`
  - Method 'parse_response' returns 'dict[str, Any] | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L215`
  - Method '_create_passthrough_artifact' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L257`
  - Method 'validate_output' returns 'OutputValidation', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L282`
  - Method 'get_required_inputs' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L287`
  - Method 'create_clarify_executor' returns 'ClarifyExecutor', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/pipeline/stages/deliver.py`** (12 violations)

- 🔵 **single-responsibility-modules** at `L30`
  - Class 'DeliverPhaseExecutor' has 14 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L219`
  - Method '_generate_commit_message' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L254`
  - Method '_generate_summary' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L278`
  - Method '_stage_files' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L305`
  - Method '_create_commit' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L332`
  - Method '_create_branch' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L350`
  - Method '_create_pull_request' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L386`
  - Method '_generate_patch' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L400`
  - Method 'validate_output' returns 'OutputValidation', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L432`
  - Method 'create_deliver_executor' returns 'DeliverPhaseExecutor', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/pipeline/stages/green.py`** (24 violations)

- 🟡 **max-cyclomatic-complexity** at `L227`
  - Function 'execute' has complexity 13 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L227`
  - Function 'execute' has 69 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L409`
  - Function '_register_implementation_tools' has 65 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-file-lines** at `file`
  - File exceeds line limit (620 lines > 500)
  - 💡 *Consider splitting into smaller files*
- 🔵 **single-responsibility-modules** at `L34`
  - Class 'GreenPhaseExecutor' has 15 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L200`
  - Method '_validate_path' returns '"Path"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L334`
  - Method '_format_test_files' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L344`
  - Method '_format_components' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L355`
  - Method '_build_user_message' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L377`
  - Method '_build_iteration_message' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L409`
  - Method '_register_implementation_tools' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L419`
  - Method 'read_file_handler' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L431`
  - Method 'write_file_handler' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L444`
  - Method 'edit_file_handler' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L465`
  - Method 'run_tests_handler' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L484`
  - Method 'complete_handler' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L535`
  - Method '_parse_pytest_output' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L562`
  - Method '_check_completion' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L572`
  - Method '_extract_completion_data' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L580`
  - Method '_extract_written_files' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L593`
  - Method 'validate_output' returns 'OutputValidation', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L617`
  - Method 'create_green_executor' returns 'GreenPhaseExecutor', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/pipeline/stages/intake.py`** (9 violations)

- 🔵 **single-responsibility-modules** at `L28`
  - Class 'IntakeExecutor' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L122`
  - Method 'get_system_prompt' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L126`
  - Method 'get_user_message' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L146`
  - Method 'parse_response' returns 'dict[str, Any] | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L186`
  - Method 'validate_output' returns 'OutputValidation', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L219`
  - Method 'get_required_inputs' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L224`
  - Method 'create_intake_executor' returns 'IntakeExecutor', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/pipeline/stages/red.py`** (16 violations)

- 🔵 **single-responsibility-modules** at `L33`
  - Class 'RedPhaseExecutor' has 14 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L156`
  - Method 'get_system_prompt' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L160`
  - Method '_format_component' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L175`
  - Method '_format_test_case' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L185`
  - Method '_format_acceptance_criteria' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L196`
  - Method 'get_user_message' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L215`
  - Method 'parse_response' returns 'dict[str, Any] | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L237`
  - Method '_extract_file_blocks' returns 'list[dict[str, str]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L258`
  - Method '_write_test_files' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L284`
  - Method '_run_tests' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L331`
  - Method '_parse_pytest_output' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L355`
  - Method '_validate_red_results' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L401`
  - Method 'validate_output' returns 'OutputValidation', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L427`
  - Method 'create_red_executor' returns 'RedPhaseExecutor', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/pipeline/stages/refactor.py`** (10 violations)

- 🔵 **single-responsibility-modules** at `L24`
  - Class 'RefactorPhaseExecutor' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L164`
  - Method '_run_tests' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L190`
  - Method '_run_conformance' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L249`
  - Method '_build_task' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L272`
  - Method '_create_passthrough_artifact' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L303`
  - Method '_build_artifact' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L336`
  - Method 'validate_output' returns 'OutputValidation', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L366`
  - Method 'create_refactor_executor' returns 'RefactorPhaseExecutor', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/pipeline/stages/spec.py`** (13 violations)

- 🟡 **max-cyclomatic-complexity** at `L298`
  - Function 'validate_output' has complexity 13 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🔵 **single-responsibility-modules** at `L32`
  - Class 'SpecExecutor' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L139`
  - Method 'method_name' returns 'bool"
          description', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L165`
  - Method 'method' returns 'return_type"

data_models', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L208`
  - Method 'get_system_prompt' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L212`
  - Method 'get_user_message' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L271`
  - Method 'parse_response' returns 'dict[str, Any] | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L298`
  - Method 'validate_output' returns 'OutputValidation', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L344`
  - Method 'finalize' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L364`
  - Method 'get_required_inputs' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L369`
  - Method 'create_spec_executor' returns 'SpecExecutor', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/pipeline/state.py`** (20 violations)

- 🔵 **single-responsibility-modules** at `L49`
  - Class 'StageState' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L134`
  - Class 'PipelineState' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L64`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L76`
  - Method 'from_dict' returns '"StageState"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L95`
  - Method 'mark_running' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L100`
  - Method 'mark_completed' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L107`
  - Method 'mark_failed' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L113`
  - Method 'mark_skipped' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L121`
  - Method 'generate_pipeline_id' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L159`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L179`
  - Method 'from_dict' returns '"PipelineState"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L200`
  - Method 'touch' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L204`
  - Method 'get_next_stage' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L219`
  - Method 'get_stage' returns 'StageState', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L225`
  - Method 'collect_artifacts' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L234`
  - Method 'is_terminal' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L242`
  - Method 'can_resume' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L259`
  - Method 'create_pipeline_state' returns 'PipelineState', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/pipeline/state_store.py`** (39 violations)

- 🟡 **max-class-size** at `L175`
  - Class 'PipelineStateStore' has 26 methods (max: 20)
  - 💡 *Consider splitting into multiple classes with single responsibilities*
- 🟡 **max-file-lines** at `file`
  - File exceeds line limit (640 lines > 500)
  - 💡 *Consider splitting into smaller files*
- 🟡 **no-god-classes** at `L175`
  - Class 'PipelineStateStore' has 26 methods (max: 15)
  - 💡 *Split large classes using composition or inheritance*
- 🔵 **single-responsibility-modules** at `L41`
  - Class 'DeferredWriteManager' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L175`
  - Class 'PipelineStateStore' has 26 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L86`
  - Method 'schedule_write' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L102`
  - Method 'flush' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L121`
  - Method 'flush_blocking' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L127`
  - Method '_worker_loop' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L145`
  - Method '_process_pending' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L161`
  - Method 'shutdown' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L169`
  - Method 'pending_count' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L232`
  - Method '_ensure_dirs' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L237`
  - Method '_get_active_path' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L241`
  - Method '_get_completed_path' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L245`
  - Method '_get_lock_path' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L250`
  - Method 'transaction' returns 'Generator[None, None, None]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L283`
  - Method 'save' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L316`
  - Method 'save_deferred' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L357`
  - Method 'flush' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L378`
  - Method 'flush_all_blocking' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L389`
  - Method 'pending_writes' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L396`
  - Method 'deferred_mode' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L400`
  - Method 'load' returns 'PipelineState | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L425`
  - Method '_load_from_file' returns 'PipelineState | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L438`
  - Method '_quarantine_corrupted' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L447`
  - Method 'list_active' returns 'list[PipelineState]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L464`
  - Method 'list_completed' returns 'list[PipelineState]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L484`
  - Method 'delete' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L513`
  - Method 'archive' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L533`
  - Method '_write_yaml' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L542`
  - Method '_read_yaml' returns 'dict[str, Any] | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L554`
  - Method '_update_index' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L568`
  - Method '_remove_from_index' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L575`
  - Method 'get_by_status' returns 'list[PipelineState]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L588`
  - Method 'list' returns 'list[PipelineState]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L618`
  - Method 'cleanup_old_completed' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/pipeline/types.py`** (2 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/pipeline/validator.py`** (13 violations)

- 🔵 **single-responsibility-modules** at `L47`
  - Class 'ArtifactValidator' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L54`
  - Method 'validate' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L88`
  - Method '_validate_type' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L130`
  - Method 'validate_required' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L153`
  - Method 'validate_types' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L183`
  - Method 'validate_and_raise' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L220`
  - Method 'validate_stage_input' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L239`
  - Method 'validate_stage_output' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L259`
  - Method 'validate_transition' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L298`
  - Method 'validate_stage_output_for_language' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L325`
  - Method 'validate_artifacts' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/pyright_runner.py`** (4 violations)

- 🔵 **single-responsibility-modules** at `L45`
  - Class 'PyrightRunner' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L63`
  - Method '_verify_pyright_installed' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/refactoring/base.py`** (4 violations)

- 🔵 **single-responsibility-modules** at `L62`
  - Class 'RefactoringProvider' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L136`
  - Method 'supports_file' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/refactoring/registry.py`** (4 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L28`
  - Method 'get_refactoring_provider' returns 'RefactoringProvider | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L51`
  - Method 'supports_file' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/refactoring/rope_provider.py`** (11 violations)

- 🟡 **max-cyclomatic-complexity** at `L156`
  - Function 'extract_function' has complexity 12 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L89`
  - Function 'can_extract_function' has 53 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L156`
  - Function 'extract_function' has 77 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-nesting-depth** at `L89`
  - Function 'can_extract_function' has nesting depth 5 (max: 4)
  - 💡 *Use early returns, guard clauses, or extract nested logic*
- 🟡 **max-nesting-depth** at `L156`
  - Function 'extract_function' has nesting depth 6 (max: 4)
  - 💡 *Use early returns, guard clauses, or extract nested logic*
- 🔵 **single-responsibility-modules** at `L26`
  - Class 'RopeRefactoringProvider' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L43`
  - Method '_get_project' returns 'Project', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L67`
  - Method '_lines_to_offset' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L75`
  - Method '_get_line_range_offsets' returns 'tuple[int, int]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/spec/placement.py`** (16 violations)

- 🟡 **max-cyclomatic-complexity** at `L242`
  - Function 'analyze' has complexity 13 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L242`
  - Function 'analyze' has 94 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **single-responsibility-modules** at `L111`
  - Class 'SpecPlacementAnalyzer' has 10 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L57`
  - Method 'from_yaml' returns ''SpecInfo'', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L102`
  - Method '__str__' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L133`
  - Method 'load_specs' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L164`
  - Method '_ensure_loaded' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L169`
  - Method 'get_spec_ids' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L174`
  - Method 'get_spec' returns 'SpecInfo | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L179`
  - Method 'find_covering_specs' returns 'list[SpecInfo]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L210`
  - Method '_extract_module_from_location' returns 'tuple[str, str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L242`
  - Method 'analyze' returns 'PlacementDecision', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L359`
  - Method 'suggest_component_id' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L382`
  - Method 'validate_unique_component_id' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/tdflow/domain.py`** (12 violations)

- 🔵 **single-responsibility-modules** at `L161`
  - Class 'TDFlowSession' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L99`
  - Method 'all_passed' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L104`
  - Method 'all_failed' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L134`
  - Method 'to_dict' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L186`
  - Method 'get_component' returns 'ComponentProgress | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L193`
  - Method 'get_next_pending' returns 'ComponentProgress | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L200`
  - Method 'get_current_component' returns 'ComponentProgress | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L206`
  - Method 'all_verified' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L210`
  - Method 'add_history' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L228`
  - Method 'get_progress_summary' returns 'dict[str, int]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/tdflow/orchestrator.py`** (14 violations)

- 🟡 **max-cyclomatic-complexity** at `L257`
  - Function 'verify' has complexity 14 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L257`
  - Function 'verify' has 69 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **single-responsibility-modules** at `L38`
  - Class 'TDFlowOrchestrator' has 13 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L67`
  - Method 'generator' returns 'Optional["GenerationEngine"]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L72`
  - Method 'generator' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L77`
  - Method 'session' returns 'TDFlowSession | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L84`
  - Method 'runner' returns 'TestRunner', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L96`
  - Method 'start' returns 'TDFlowSession', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L257`
  - Method 'verify' returns 'VerificationReport', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L344`
  - Method 'resume' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L359`
  - Method 'get_status' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L388`
  - Method '_get_component' returns 'ComponentProgress | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/tdflow/phases/green.py`** (13 violations)

- 🟡 **max-function-length** at `L78`
  - Function 'execute' has 66 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L272`
  - Function '_generate_csharp_impl' has 69 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L357`
  - Function '_generate_python_impl' has 64 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **single-responsibility-modules** at `L43`
  - Class 'GreenPhaseExecutor' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L168`
  - Method '_load_component_spec' returns 'dict[str, Any] | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L192`
  - Method '_generate_implementation' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L224`
  - Method '_generate_impl_with_llm' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L272`
  - Method '_generate_csharp_impl' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L357`
  - Method '_generate_python_impl' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L440`
  - Method '_get_impl_path' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L475`
  - Method '_to_snake_case' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/tdflow/phases/red.py`** (14 violations)

- 🟡 **max-function-length** at `L67`
  - Function 'execute' has 79 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L259`
  - Function '_generate_csharp_tests' has 89 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L375`
  - Function '_generate_python_tests' has 74 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-file-lines** at `file`
  - File exceeds line limit (547 lines > 500)
  - 💡 *Consider splitting into smaller files*
- 🔵 **single-responsibility-modules** at `L36`
  - Class 'RedPhaseExecutor' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L165`
  - Method '_load_component_spec' returns 'dict[str, Any] | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L189`
  - Method '_generate_tests' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L219`
  - Method '_generate_tests_with_llm' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L259`
  - Method '_generate_csharp_tests' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L375`
  - Method '_generate_python_tests' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L494`
  - Method '_get_test_path' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L526`
  - Method '_to_snake_case' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/tdflow/phases/refactor.py`** (7 violations)

- 🟡 **max-function-length** at `L46`
  - Function 'execute' has 98 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **single-responsibility-modules** at `L22`
  - Class 'RefactorPhaseExecutor' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L176`
  - Method '_run_conformance_check' returns 'list[dict[str, Any]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L198`
  - Method '_is_clean' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L224`
  - Method '_refactor_implementation' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/tdflow/phases/verify.py`** (11 violations)

- 🟡 **max-function-length** at `L49`
  - Function 'execute' has 65 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **single-responsibility-modules** at `L25`
  - Class 'VerifyPhaseExecutor' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L135`
  - Method 'verify_all' returns 'list[VerificationReport]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L151`
  - Method '_run_conformance_check' returns 'list[dict[str, Any]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L172`
  - Method '_build_traceability' returns 'list[dict[str, str]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L205`
  - Method '_load_component_spec' returns 'dict[str, Any] | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L229`
  - Method '_get_report_path' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L243`
  - Method '_save_report' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L262`
  - Method '_load_report' returns 'VerificationReport', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/tdflow/runners/base.py`** (8 violations)

- 🔵 **single-responsibility-modules** at `L21`
  - Class 'TestRunner' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L51`
  - Method 'get_coverage' returns 'float', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L61`
  - Method 'discover_tests' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L71`
  - Method 'build' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L81`
  - Method 'detect' returns '"TestRunner"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L116`
  - Method 'for_framework' returns '"TestRunner"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/tdflow/runners/dotnet.py`** (7 violations)

- 🟡 **no-http-without-https** at `L83`
  - Forbidden pattern found: 'http://'
  - 💡 *Use HTTPS for all external connections*
- 🔵 **single-responsibility-modules** at `L22`
  - Class 'DotNetTestRunner' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L163`
  - Method 'get_coverage' returns 'float', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L193`
  - Method 'discover_tests' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L219`
  - Method 'build' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/tdflow/runners/pytest_runner.py`** (6 violations)

- 🔵 **single-responsibility-modules** at `L17`
  - Class 'PytestRunner' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L157`
  - Method 'get_coverage' returns 'float', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L186`
  - Method 'discover_tests' returns 'list[str]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L210`
  - Method 'build' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/tdflow/session.py`** (15 violations)

- 🔵 **single-responsibility-modules** at `L31`
  - Class 'SessionManager' has 13 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L52`
  - Method 'create' returns 'TDFlowSession', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L95`
  - Method '_extract_components' returns 'list[ComponentProgress]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L117`
  - Method 'load' returns 'TDFlowSession | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L137`
  - Method 'save' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L154`
  - Method 'get_latest' returns 'TDFlowSession | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L166`
  - Method 'list_sessions' returns 'list[dict[str, Any]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L188`
  - Method '_serialize' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L213`
  - Method '_serialize_component' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L226`
  - Method '_serialize_history' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L236`
  - Method '_deserialize' returns 'TDFlowSession', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L266`
  - Method '_deserialize_component' returns 'ComponentProgress', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L293`
  - Method '_deserialize_history' returns 'SessionHistory', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/validate_schema.py`** (4 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L26`
  - Method 'load_yaml_or_json' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L41`
  - Method 'validate' returns 'tuple[bool, list[str]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/vector_search.py`** (13 violations)

- 🔵 **single-responsibility-modules** at `L44`
  - Class 'VectorSearch' has 15 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L93`
  - Method 'index_dir' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L100`
  - Method 'index_file' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L105`
  - Method 'metadata_file' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L109`
  - Method '_get_files' returns 'list[Path]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L127`
  - Method '_detect_language' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L136`
  - Method '_try_load_cache' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L155`
  - Method '_chunk_files' returns 'list[Chunk]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L193`
  - Method 'index' returns 'IndexStats', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L240`
  - Method '_load_index' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L293`
  - Method 'is_indexed' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/vector_types.py`** (8 violations)

- 🔵 **single-responsibility-modules** at `L15`
  - Class 'Chunk' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L24`
  - Method 'to_embedding_text' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L33`
  - Method 'token_estimate' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L37`
  - Method 'to_dict' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L49`
  - Method 'from_dict' returns '"Chunk"', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L71`
  - Method 'to_dict' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/verification_ast.py`** (10 violations)

- 🔵 **single-responsibility-modules** at `L21`
  - Class 'ASTChecker' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L27`
  - Method 'check_metric' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L53`
  - Method '_check_function_length' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L74`
  - Method '_check_nesting_depth' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L106`
  - Method '_check_parameter_count' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L137`
  - Method '_check_class_size' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L161`
  - Method '_check_import_count' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L181`
  - Method '_check_complexity_with_radon' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/verification_checks.py`** (10 violations)

- 🟡 **max-cyclomatic-complexity** at `L48`
  - Function '_run_command_check' has complexity 14 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🔵 **single-responsibility-modules** at `L35`
  - Class 'CheckRunner' has 15 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L42`
  - Method '_substitute_variables' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L77`
  - Method '_collect_files_for_check' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L96`
  - Method '_search_patterns_in_file' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L179`
  - Method '_find_forbidden_import_violations' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L235`
  - Method '_load_custom_function' returns 'Callable', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L401`
  - Method '_collect_ast_violations' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/verification_contracts_check.py`** (6 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L13`
  - Method 'get_contract_results' returns 'tuple[list | None, str | None]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L30`
  - Method 'build_contract_errors' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L44`
  - Method 'aggregate_contract_stats' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L54`
  - Method 'build_contract_message' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/verification_reports.py`** (10 violations)

- 🔵 **single-responsibility-modules** at `L22`
  - Class 'ReportGenerator' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L25`
  - Method 'generate_report' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L34`
  - Method '_format_errors_section' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L44`
  - Method '_format_check_result' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L66`
  - Method '_generate_text_report' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L95`
  - Method '_build_report_data' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L132`
  - Method '_generate_yaml_report' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L137`
  - Method '_generate_json_report' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/verification_runner.py`** (14 violations)

- 🔵 **single-responsibility-modules** at `L58`
  - Class 'VerificationRunner' has 15 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L80`
  - Method 'pyright_runner' returns 'PyrightRunner', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L87`
  - Method 'command_runner' returns 'CommandRunner', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L94`
  - Method 'ast_checker' returns 'ASTChecker', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L104`
  - Method '_substitute_variables' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L121`
  - Method 'get_checks_for_profile' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L137`
  - Method 'get_checks_by_ids' returns 'list[dict]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L142`
  - Method 'run_profile' returns 'VerificationReport', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L150`
  - Method 'run_checks' returns 'VerificationReport', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L166`
  - Method '_check_deps_met' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L178`
  - Method '_run_checks' returns 'VerificationReport', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L210`
  - Method '_get_check_handlers' returns 'dict[str, Callable]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/verification_types.py`** (5 violations)

- 🔵 **single-responsibility-modules** at `L61`
  - Class 'VerificationReport' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L52`
  - Method 'passed' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L56`
  - Method 'is_blocking_failure' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/workspace.py`** (16 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L43`
  - Method 'resolve_workspace_path' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L50`
  - Method 'discover_workspace' returns 'WorkspaceContext', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L118`
  - Method '_load_repos_into_context' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L132`
  - Method '_detect_current_repo' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L146`
  - Method '_load_workspace' returns 'WorkspaceContext', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L169`
  - Method 'init_workspace' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L200`
  - Method 'add_repo_to_workspace' returns 'RepoConfig', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L244`
  - Method 'remove_repo_from_workspace' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L266`
  - Method 'create_repo_link' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L323`
  - Method 'validate_workspace' returns 'tuple', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L352`
  - Method 'format_workspace_status' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L385`
  - Method 'init_single_repo' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L413`
  - Method 'init_global_config' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L442`
  - Method 'unlink_repo' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/workspace_config.py`** (19 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L66`
  - Method 'is_workspace_mode' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L71`
  - Method 'is_single_repo_mode' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L80`
  - Method 'find_upward' returns 'Path | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L92`
  - Method 'expand_path' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L101`
  - Method 'load_yaml_file' returns 'dict | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L111`
  - Method 'load_contracts_from_dir' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L125`
  - Method 'deep_merge' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L135`
  - Method 'merge_configs' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L158`
  - Method 'merge_contracts' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L175`
  - Method '_load_global_config' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L186`
  - Method '_load_repo_config' returns 'Path | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L207`
  - Method '_try_workspace_from_config' returns 'Path | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L225`
  - Method '_resolve_workspace_path' returns 'Path | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L248`
  - Method '_load_workspace_config' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L270`
  - Method '_merge_effective_config' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L292`
  - Method 'discover_config' returns 'ConfigContext', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L361`
  - Method 'format_config_status' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`src/agentforge/core/workspace_types.py`** (15 violations)

- 🔵 **single-responsibility-modules** at `L92`
  - Class 'WorkspaceContext' has 10 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L59`
  - Method 'from_dict' returns ''RepoConfig'', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L72`
  - Method 'to_dict' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L112`
  - Method 'is_workspace_mode' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L117`
  - Method 'workspace_name' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L124`
  - Method 'workspace_description' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L131`
  - Method 'workspace_version' returns 'str | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L138`
  - Method 'workspace_dir' returns 'Path | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L144`
  - Method 'get_repo' returns 'RepoConfig | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L148`
  - Method 'get_repo_path' returns 'Path | None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L152`
  - Method 'get_repos_by_tag' returns 'list[RepoConfig]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L156`
  - Method 'get_repos_by_type' returns 'list[RepoConfig]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L160`
  - Method 'get_repos_by_language' returns 'list[RepoConfig]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @test_path: tests/path/to/test.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/conftest.py`** (18 violations)

- 🔵 **default-result-return-types** at `L47`
  - Method 'sample_python_file' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L52`
  - Method 'greet' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L59`
  - Method 'add' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L63`
  - Method 'divide' returns 'float', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L73`
  - Method 'sample_python_with_errors' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L78`
  - Method 'add' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L81`
  - Method 'greet' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L88`
  - Method 'sample_long_function' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L100`
  - Method 'sample_deeply_nested' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L116`
  - Method 'sample_clean_architecture' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L137`
  - Method 'create_user' returns 'User', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L150`
  - Method 'save' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L158`
  - Method 'sample_layer_violation' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L181`
  - Method 'correctness_config' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L230`
  - Method 'empty_config' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L283`
  - Method '_count' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L322`
  - Method 'context_retriever_config' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L389`
  - Method '_create' returns 'Path', expected pattern 'Result|Either|Success|Failure'

**`tests/integration/cli/conftest.py`** (1 violations)

- 🔵 **cli-proper-exit-codes** at `file`
  - Required pattern not found: 'sys\.exit\s*\(\s*[012]\s*\)|raise\s+(SystemExit|click\.Abort|typer\.Abort)'
  - 💡 *Use sys.exit(0) for success, sys.exit(1) for errors*

**`tests/integration/cli/test_pipeline_cli_integration.py`** (10 violations)

- 🟡 **max-cyclomatic-complexity** at `L27`
  - Function 'test_cli_has_all_pipeline_commands' has complexity 12 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🔵 **single-responsibility-modules** at `L24`
  - Class 'TestCLICommandIntegration' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L448`
  - Class 'TestCLIErrorHandling' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **max-imports** at `L1`
  - File has 36 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **max-imports** at `L1`
  - File has 36 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **max-imports** at `L1`
  - File has 36 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **cli-proper-exit-codes** at `file`
  - Required pattern not found: 'sys\.exit\s*\(\s*[012]\s*\)|raise\s+(SystemExit|click\.Abort|typer\.Abort)'
  - 💡 *Use sys.exit(0) for success, sys.exit(1) for errors*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **max-imports** at `L1`
  - File has 36 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/integration/context/test_context_v2_integration.py`** (11 violations)

- 🟡 **max-cyclomatic-complexity** at `L197`
  - Function 'test_audit_captures_full_workflow' has complexity 14 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L44`
  - Function 'realistic_project' has 67 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **single-responsibility-modules** at `L40`
  - Class 'TestFullContextStack' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L307`
  - Class 'TestContextReproducibility' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L43`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L310`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L363`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🟡 **no-assert-true-false** at `L73`
  - Forbidden pattern found: 'assert True'
  - 💡 *Use specific assertions: assert result == expected*
- 🟡 **no-assert-true-false** at `L73`
  - Forbidden pattern found: 'assert True'
  - 💡 *Use specific assertions: assert result == expected*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/integration/harness/test_harness_workflow.py`** (27 violations)

- 🔵 **single-responsibility-modules** at `L55`
  - Class 'TestSessionLifecycle' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L130`
  - Class 'TestMemoryIntegration' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L244`
  - Class 'TestMonitorAndRecovery' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L310`
  - Class 'TestOrchestratorIntegration' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L419`
  - Class 'TestExecutionContextPersistence' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **max-imports** at `L1`
  - File has 34 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **max-imports** at `L1`
  - File has 34 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **max-imports** at `L1`
  - File has 34 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **fixtures-in-conftest** at `L58`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L64`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L133`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L138`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L190`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L247`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L252`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L256`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L313`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L318`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L349`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L422`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L427`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L486`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L491`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L528`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **max-imports** at `L1`
  - File has 34 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/integration/pipeline/stages/conftest.py`** (6 violations)

- 🟡 **max-function-length** at `L113`
  - Function 'sample_spec_for_tdd' has 60 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **default-result-return-types** at `L51`
  - Method 'login' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L55`
  - Method 'logout' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L84`
  - Method 'get_response' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L357`
  - Method 'add' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L361`
  - Method 'subtract' returns 'int', expected pattern 'Result|Either|Success|Failure'

**`tests/integration/pipeline/stages/test_design_pipeline.py`** (6 violations)

- 🟡 **max-cyclomatic-complexity** at `L280`
  - Function 'test_full_design_pipeline_with_mocked_llm' has complexity 14 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-function-length** at `L214`
  - Function 'test_spec_generates_test_cases' has 57 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L280`
  - Function 'test_full_design_pipeline_with_mocked_llm' has 100 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **single-responsibility-modules** at `L26`
  - Class 'TestDesignPipelineFlow' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/integration/pipeline/stages/test_refactor_deliver_pipeline.py`** (3 violations)

- 🔵 **single-responsibility-modules** at `L13`
  - Class 'TestRefactorIntegration' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/integration/pipeline/stages/test_tdd_pipeline.py`** (5 violations)

- 🟡 **max-function-length** at `L208`
  - Function 'test_green_produces_implementation' has 66 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L241`
  - Method 'add' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L244`
  - Method 'subtract' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/integration/pipeline/test_config_integration.py`** (4 violations)

- 🟡 **max-cyclomatic-complexity** at `L16`
  - Function 'test_full_config_hierarchy' has complexity 12 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🔵 **prefer-pytest-raises** at `L361`
  - Forbidden pattern found: 'try:
            settings = loader.load_settings()
            # If it doesn't raise, should have loaded defaults
            assert settings.project_name == "", "Expected settings.project_name to equal ''"
        except Exception as e:
            # If it raises, should be a clear error
            assert "yaml" in str(e).lower() or "parse" in str(e).lower(), "Assertion failed"

    def test_missing_directory_handled(self, tmp_path):
        """Missing config directory is handled gracefully."""
        from agentforge.core.pipeline.config import ConfigurationLoader

        # Don't create any directories
        loader = ConfigurationLoader(tmp_path)

        # Should fall back to defaults
        settings = loader.load_settings()
        assert settings.project_name == "", "Expected settings.project_name to equal ''"
        assert settings.language == "python", "Expected settings.language to equal 'python'"

        # Listing pipelines should still work
        pipelines = loader.list_available_pipelines()
        assert'
  - 💡 *Use: with pytest.raises(ExceptionType):*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/integration/pipeline/test_pipeline_execution.py`** (2 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/integration/tool_handlers/test_context_injection.py`** (7 violations)

- 🔵 **single-responsibility-modules** at `L27`
  - Class 'TestContextInjection' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L143`
  - Class 'TestExecutorWithHandlers' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L30`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L146`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L154`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/integration/workflows/conftest.py`** (13 violations)

- 🟡 **max-function-length** at `L25`
  - Function 'project_with_violation' has 128 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L189`
  - Function 'project_with_generated_file' has 79 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🟡 **max-function-length** at `L288`
  - Function 'simulated_fix_workflow_responses' has 82 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **default-result-return-types** at `L25`
  - Method 'project_with_violation' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L63`
  - Method 'process_data' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L106`
  - Method 'simple_helper' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L189`
  - Method 'project_with_generated_file' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L219`
  - Method 'validate_type' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L288`
  - Method 'simulated_fix_workflow_responses' returns 'list[dict[str, Any]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L322`
  - Method '_handle_parse' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L381`
  - Method 'simulated_cannot_fix_responses' returns 'list[dict[str, Any]]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L418`
  - Method 'simulated_llm_client' returns 'SimulatedLLMClient', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L437`
  - Method 'simulated_escalation_client' returns 'SimulatedLLMClient', expected pattern 'Result|Either|Success|Failure'

**`tests/integration/workflows/test_fix_violation_workflow.py`** (8 violations)

- 🟡 **max-cyclomatic-complexity** at `L262`
  - Function 'test_read_search_edit_sequence' has complexity 12 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🔵 **single-responsibility-modules** at `L32`
  - Class 'TestToolHandlerIntegration' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L393`
  - Class 'TestEdgeCases' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L96`
  - Method 'simple_helper' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L110`
  - Method 'process_data' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L165`
  - Method '_validate_mode' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/test_python_checks.py`** (5 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L29`
  - Method 'add' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L42`
  - Method 'add' returns 'int', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L171`
  - Method 'greet' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/audit/test_audit_manager.py`** (5 violations)

- 🟡 **max-function-length** at `L320`
  - Function 'test_full_workflow' has 51 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **single-responsibility-modules** at `L13`
  - Class 'TestAuditManagerThreads' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L224`
  - Class 'TestAuditManagerQueries' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/audit/test_context_frame.py`** (2 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/audit/test_conversation_archive.py`** (4 violations)

- 🔵 **single-responsibility-modules** at `L51`
  - Class 'TestConversationTurn' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L136`
  - Class 'TestConversationArchive' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/audit/test_frame_logger.py`** (4 violations)

- 🟡 **max-function-length** at `L268`
  - Function 'test_complete_pipeline_flow' has 51 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **single-responsibility-modules** at `L17`
  - Class 'TestFrameLogger' has 12 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/audit/test_integrity_chain.py`** (4 violations)

- 🔵 **single-responsibility-modules** at `L18`
  - Class 'TestComputeHash' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L66`
  - Class 'TestIntegrityChain' has 12 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/audit/test_thread_correlator.py`** (3 violations)

- 🔵 **single-responsibility-modules** at `L17`
  - Class 'TestThreadCorrelator' has 10 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/audit/test_transaction_logger.py`** (3 violations)

- 🔵 **single-responsibility-modules** at `L18`
  - Class 'TestTransactionLogger' has 12 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/cli/conftest.py`** (1 violations)

- 🔵 **cli-proper-exit-codes** at `file`
  - Required pattern not found: 'sys\.exit\s*\(\s*[012]\s*\)|raise\s+(SystemExit|click\.Abort|typer\.Abort)'
  - 💡 *Use sys.exit(0) for success, sys.exit(1) for errors*

**`tests/unit/cli/test_pipeline_commands.py`** (15 violations)

- 🔵 **single-responsibility-modules** at `L38`
  - Class 'TestStartCommand' has 13 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L170`
  - Class 'TestDesignCommand' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L233`
  - Class 'TestImplementCommand' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L329`
  - Class 'TestStatusCommand' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L424`
  - Class 'TestResumeCommand' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L470`
  - Class 'TestApproveCommand' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L517`
  - Class 'TestRejectCommand' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L565`
  - Class 'TestAbortCommand' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L643`
  - Class 'TestPipelinesCommand' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L750`
  - Class 'TestArtifactsCommand' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L892`
  - Class 'TestPipelineProgressDisplay' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L26`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **cli-proper-exit-codes** at `file`
  - Required pattern not found: 'sys\.exit\s*\(\s*[012]\s*\)|raise\s+(SystemExit|click\.Abort|typer\.Abort)'
  - 💡 *Use sys.exit(0) for success, sys.exit(1) for errors*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/cli/test_spec_adapt.py`** (3 violations)

- 🔵 **cli-proper-exit-codes** at `file`
  - Required pattern not found: 'sys\.exit\s*\(\s*[012]\s*\)|raise\s+(SystemExit|click\.Abort|typer\.Abort)'
  - 💡 *Use sys.exit(0) for success, sys.exit(1) for errors*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/context/test_agent_config.py`** (7 violations)

- 🔵 **single-responsibility-modules** at `L23`
  - Class 'TestAgentPreferences' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L120`
  - Class 'TestAgentConfig' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L178`
  - Class 'TestAgentConfigLoader' has 11 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L181`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L191`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/context/test_audit.py`** (14 violations)

- 🔵 **single-responsibility-modules** at `L18`
  - Class 'TestContextAuditLogger' has 14 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L204`
  - Class 'TestRetrieval' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L281`
  - Class 'TestClassMethods' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L344`
  - Class 'TestEdgeCases' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L21`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L29`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L34`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L43`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L207`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L215`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L284`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L347`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/context/test_compaction.py`** (15 violations)

- 🔵 **single-responsibility-modules** at `L21`
  - Class 'TestCompactionManager' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L118`
  - Class 'TestCompactionStrategies' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L343`
  - Class 'TestSummarizeStrategy' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L24`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L29`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L121`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L368`
  - Method 'summarize' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L391`
  - Method 'summarize' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L413`
  - Method 'summarize' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L436`
  - Method 'summarize' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L449`
  - Method 'summarize' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L476`
  - Method 'summarize' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L499`
  - Method 'summarize' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/context/test_fingerprint.py`** (6 violations)

- 🔵 **single-responsibility-modules** at `L24`
  - Class 'TestProjectFingerprint' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L150`
  - Class 'TestFingerprintGenerator' has 18 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L153`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L161`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/context/test_templates.py`** (21 violations)

- 🔵 **single-responsibility-modules** at `L30`
  - Class 'TestTemplateRegistry' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L95`
  - Class 'TestFixViolationTemplate' has 11 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L199`
  - Class 'TestImplementFeatureTemplate' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L270`
  - Class 'TestBaseContextTemplate' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L454`
  - Class 'TestWriteTestsTemplate' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L525`
  - Class 'TestDiscoveryTemplate' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L582`
  - Class 'TestBridgeTemplate' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L641`
  - Class 'TestCodeReviewTemplate' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L711`
  - Class 'TestRefactorTemplate' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L792`
  - Class 'TestAllTemplatesRegistered' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L835`
  - Class 'TestPhaseMappings' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L98`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L202`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L457`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L528`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L585`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L644`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L714`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L72`
  - Method 'task_type' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/contracts/test_cli.py`** (6 violations)

- 🔵 **single-responsibility-modules** at `L64`
  - Class 'TestListCommand' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L111`
  - Class 'TestShowCommand' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L26`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L32`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/contracts/test_draft.py`** (4 violations)

- 🔵 **single-responsibility-modules** at `L210`
  - Class 'TestContractDraft' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L342`
  - Class 'TestApprovedContracts' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/contracts/test_drafter.py`** (7 violations)

- 🟡 **max-function-length** at `L76`
  - Function 'mock_llm_response_yaml' has 57 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **single-responsibility-modules** at `L72`
  - Class 'TestContractDrafter' has 15 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L75`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L140`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L297`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/contracts/test_enforcer.py`** (7 violations)

- 🟡 **max-function-length** at `L28`
  - Function 'sample_contracts' has 52 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **single-responsibility-modules** at `L115`
  - Class 'TestValidationResult' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L171`
  - Class 'TestContractEnforcer' has 15 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L27`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L174`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/contracts/test_evolution.py`** (6 violations)

- 🔵 **single-responsibility-modules** at `L115`
  - Class 'TestContractEvolutionHandler' has 10 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L262`
  - Class 'TestEvolutionViolationTypes' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L23`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L118`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/contracts/test_operations.py`** (14 violations)

- 🟡 **max-cyclomatic-complexity** at `L357`
  - Function 'test_load_builtin_contracts' has complexity 12 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-cyclomatic-complexity** at `L511`
  - Function 'test_code_generation_contract' has complexity 11 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🟡 **max-cyclomatic-complexity** at `L608`
  - Function 'test_design_patterns_contract' has complexity 32 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🔵 **single-responsibility-modules** at `L146`
  - Class 'TestOperationContract' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L260`
  - Class 'TestLoadOperationContract' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L327`
  - Class 'TestLoadAllOperationContracts' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L394`
  - Class 'TestOperationContractManager' has 10 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L476`
  - Class 'TestBuiltinContracts' has 15 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L263`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L330`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L397`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L479`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/contracts/test_registry.py`** (5 violations)

- 🔵 **single-responsibility-modules** at `L24`
  - Class 'TestContractRegistry' has 19 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L27`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L32`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/contracts/test_reviewer.py`** (8 violations)

- 🟡 **max-function-length** at `L29`
  - Function 'sample_draft' has 65 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **single-responsibility-modules** at `L122`
  - Class 'TestReviewFeedback' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L202`
  - Class 'TestContractReviewer' has 12 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L28`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L205`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L340`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/core/discovery/test_domain.py`** (8 violations)

- 🔵 **single-responsibility-modules** at `L44`
  - Class 'TestConfidenceLevel' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L72`
  - Class 'TestDetection' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L204`
  - Class 'TestCoverageGapAnalysis' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L268`
  - Class 'TestZone' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L382`
  - Class 'TestCodebaseProfile' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L385`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/core/discovery/test_zone_detector.py`** (8 violations)

- 🔵 **single-responsibility-modules** at `L49`
  - Class 'TestZoneDetector' has 16 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L241`
  - Class 'TestDeriveZoneName' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L278`
  - Class 'TestDeriveZonePath' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L52`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L244`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L281`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/core/lineage/test_metadata.py`** (3 violations)

- 🔵 **single-responsibility-modules** at `L22`
  - Class 'TestLineageMetadata' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L95`
  - Class 'TestParseLineageFromFile' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L272`
  - Class 'TestGetTestPathFromLineage' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*

**`tests/unit/core/spec/test_init.py`** (2 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/core/spec/test_placement.py`** (4 violations)

- 🔵 **single-responsibility-modules** at `L124`
  - Class 'TestSpecPlacementAnalyzer' has 10 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L127`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/core/test_contract_runner.py`** (10 violations)

- 🔵 **single-responsibility-modules** at `L201`
  - Class 'TestShouldIncludeSection' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L307`
  - Class 'TestSubstituteVariables' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L361`
  - Class 'TestAssemblePrompt' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L204`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L259`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L310`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L364`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L436`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/core/test_verification_contracts_check.py`** (3 violations)

- 🔵 **single-responsibility-modules** at `L22`
  - Class 'TestBuildContractErrors' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/core/test_verification_reports.py`** (15 violations)

- 🔵 **single-responsibility-modules** at `L26`
  - Class 'TestReportGenerator' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L83`
  - Class 'TestGenerateReport' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L156`
  - Class 'TestFormatCheckResult' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L261`
  - Class 'TestFormatErrorsSection' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L29`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L34`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L46`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L61`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L86`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L90`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L159`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L264`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L312`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/test_action_parser.py`** (10 violations)

- 🔵 **single-responsibility-modules** at `L17`
  - Class 'TestActionParserBasic' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L134`
  - Class 'TestActionParserEdgeCases' has 11 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L252`
  - Class 'TestActionParserLenient' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L313`
  - Class 'TestExtractElement' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L20`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L137`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L255`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L316`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/test_agent_monitor.py`** (7 violations)

- 🔵 **single-responsibility-modules** at `L55`
  - Class 'TestAgentMonitorObservations' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L142`
  - Class 'TestAgentMonitorLoopDetection' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L291`
  - Class 'TestAgentMonitorContextAndProgress' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L357`
  - Class 'TestAgentMonitorHealthAssessment' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L444`
  - Class 'TestAgentMonitorHistoryManagement' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/test_agent_orchestrator.py`** (24 violations)

- 🟡 **max-parameter-count** at `L42`
  - Function 'create_mock_session' has 6 parameters (max: 5)
  - 💡 *Group related parameters into a dataclass or use **kwargs*
- 🔵 **single-responsibility-modules** at `L132`
  - Class 'TestStartSession' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L209`
  - Class 'TestResumeSession' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L255`
  - Class 'TestExecuteStep' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L321`
  - Class 'TestRunUntilComplete' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L383`
  - Class 'TestPauseSession' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L429`
  - Class 'TestGetStatus' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L505`
  - Class 'TestGetAvailableTools' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L135`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L212`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L258`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L324`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L386`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L432`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L508`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L557`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L617`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L673`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L729`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L767`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L794`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L42`
  - Method 'create_mock_session' returns 'Mock', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/test_agent_prompt_builder.py`** (11 violations)

- 🔵 **single-responsibility-modules** at `L18`
  - Class 'TestAgentPromptBuilder' has 10 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L111`
  - Class 'TestToolsSection' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L137`
  - Class 'TestHistorySection' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L173`
  - Class 'TestFormatToolResults' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L21`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L25`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L114`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L140`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L176`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/test_checkpoint_manager.py`** (11 violations)

- 🔵 **single-responsibility-modules** at `L60`
  - Class 'TestCreateCheckpoint' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L157`
  - Class 'TestRestoreCheckpoint' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L236`
  - Class 'TestListCheckpoints' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L324`
  - Class 'TestDeleteCheckpoint' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L63`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L160`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L239`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L296`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L327`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/test_enhanced_context.py`** (19 violations)

- 🟡 **max-cyclomatic-complexity** at `L1760`
  - Function 'test_migrate_v1_to_v2' has complexity 11 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🔵 **single-responsibility-modules** at `L49`
  - Class 'TestFact' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L266`
  - Class 'TestFactStore' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L358`
  - Class 'TestLoopDetector' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L482`
  - Class 'TestPhaseMachine' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L738`
  - Class 'TestWorkingMemoryFactStorage' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L924`
  - Class 'TestAdaptiveBudgetEnhancedLoopDetection' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L1117`
  - Class 'TestPhaseMachineIntegration' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L1332`
  - Class 'TestTemplateContextBuilderIntegration' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L1489`
  - Class 'TestUnifiedArchitecture' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L1604`
  - Class 'TestResponseValidation' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L1731`
  - Class 'TestSchemaVersioning' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L1891`
  - Class 'TestFactCompaction' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **max-imports** at `L1`
  - File has 99 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **max-imports** at `L1`
  - File has 99 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **max-imports** at `L1`
  - File has 99 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **max-imports** at `L1`
  - File has 99 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/test_escalation_domain.py`** (5 violations)

- 🟡 **max-cyclomatic-complexity** at `L109`
  - Function 'test_escalation_creation_with_required_fields' has complexity 12 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🔵 **single-responsibility-modules** at `L106`
  - Class 'TestEscalation' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L254`
  - Class 'TestEscalationRule' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/test_escalation_manager.py`** (15 violations)

- 🔵 **single-responsibility-modules** at `L33`
  - Class 'TestEscalationManagerInit' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L75`
  - Class 'TestCreateEscalation' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L144`
  - Class 'TestAcknowledgeEscalation' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L196`
  - Class 'TestResolveEscalation' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L314`
  - Class 'TestListEscalations' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L480`
  - Class 'TestCancelEscalation' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L78`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L147`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L199`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L283`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L317`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L388`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L483`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/test_escalation_notifier.py`** (12 violations)

- 🔵 **single-responsibility-modules** at `L61`
  - Class 'TestNotify' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L112`
  - Class 'TestNotifyCli' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L162`
  - Class 'TestNotifyFile' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L227`
  - Class 'TestNotifyWebhook' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L302`
  - Class 'TestFormatEscalation' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L64`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L115`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L165`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L230`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L305`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/test_execution_context_store.py`** (7 violations)

- 🔵 **single-responsibility-modules** at `L28`
  - Class 'TestExecutionContextStore' has 11 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L182`
  - Class 'TestSerializationRoundTrip' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L31`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L37`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L42`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/test_executor.py`** (8 violations)

- 🔵 **single-responsibility-modules** at `L33`
  - Class 'TestMinimalContextExecutor' has 11 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L248`
  - Class 'TestNativeToolIntegration' has 11 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L36`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L171`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L204`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L251`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/test_executor_edge_cases.py`** (12 violations)

- 🔵 **single-responsibility-modules** at `L32`
  - Class 'TestExecutorErrorHandling' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L201`
  - Class 'TestParseActionEdgeCases' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L296`
  - Class 'TestAdaptiveBudgetEdgeCases' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L386`
  - Class 'TestNativeToolEdgeCases' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L532`
  - Class 'TestPhaseTransitionEdgeCases' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L35`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L204`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L389`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L480`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L535`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/test_llm_executor.py`** (7 violations)

- 🔵 **single-responsibility-modules** at `L76`
  - Class 'TestExecuteStep' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L199`
  - Class 'TestToolExecution' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L256`
  - Class 'TestRunUntilComplete' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L79`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L93`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/test_llm_executor_domain.py`** (6 violations)

- 🔵 **single-responsibility-modules** at `L48`
  - Class 'TestToolCall' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L121`
  - Class 'TestAgentAction' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L197`
  - Class 'TestExecutionContext' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L264`
  - Class 'TestStepResult' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/test_memory_domain.py`** (7 violations)

- 🔵 **single-responsibility-modules** at `L19`
  - Class 'TestMemoryTier' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L44`
  - Class 'TestMemoryEntryCreate' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L88`
  - Class 'TestMemoryEntryIsExpired' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L133`
  - Class 'TestMemoryEntryToDict' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L189`
  - Class 'TestMemoryEntryFromDict' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/test_memory_manager.py`** (3 violations)

- 🔵 **single-responsibility-modules** at `L48`
  - Class 'TestMemoryManagerGet' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/test_memory_store.py`** (8 violations)

- 🔵 **single-responsibility-modules** at `L52`
  - Class 'TestMemoryStoreGet' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L99`
  - Class 'TestMemoryStoreSet' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L144`
  - Class 'TestMemoryStoreDelete' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L183`
  - Class 'TestMemoryStoreListKeys' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L267`
  - Class 'TestMemoryStoreLoadTier' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L333`
  - Class 'TestMemoryStoreSaveTier' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/test_minimal_context.py`** (2 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/test_monitor_domain.py`** (2 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/test_native_tool_executor.py`** (4 violations)

- 🔵 **single-responsibility-modules** at `L25`
  - Class 'TestNativeToolExecutor' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L140`
  - Class 'TestExecutionLogging' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/test_orchestrator_domain.py`** (5 violations)

- 🔵 **single-responsibility-modules** at `L62`
  - Class 'TestAgentTask' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L131`
  - Class 'TestExecutionResult' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L199`
  - Class 'TestOrchestratorConfig' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/test_recovery_domain.py`** (5 violations)

- 🔵 **single-responsibility-modules** at `L73`
  - Class 'TestCheckpoint' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L143`
  - Class 'TestRecoveryAttempt' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L200`
  - Class 'TestRecoveryPolicy' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/test_recovery_executor.py`** (4 violations)

- 🔵 **single-responsibility-modules** at `L68`
  - Class 'TestExecuteRecovery' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L516`
  - Class 'TestPolicyManagement' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/test_selfhosting_tools.py`** (14 violations)

- 🔵 **single-responsibility-modules** at `L71`
  - Class 'TestViolationTools' has 10 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L193`
  - Class 'TestGitTools' has 14 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L375`
  - Class 'TestRunnerTools' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L464`
  - Class 'TestConformanceTools' has 13 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L74`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L196`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L378`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L467`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🟡 **no-assert-true-false** at `L389`
  - Forbidden pattern found: 'assert True'
  - 💡 *Use specific assertions: assert result == expected*
- 🟡 **no-assert-true-false** at `L400`
  - Forbidden pattern found: 'assert False'
  - 💡 *Use specific assertions: assert result == expected*
- 🟡 **no-assert-true-false** at `L389`
  - Forbidden pattern found: 'assert True'
  - 💡 *Use specific assertions: assert result == expected*
- 🟡 **no-assert-true-false** at `L400`
  - Forbidden pattern found: 'assert False'
  - 💡 *Use specific assertions: assert result == expected*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/test_session_domain.py`** (5 violations)

- 🔵 **single-responsibility-modules** at `L11`
  - Class 'TestSessionState' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L35`
  - Class 'TestTokenBudget' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L142`
  - Class 'TestSessionContext' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/test_session_manager.py`** (22 violations)

- 🔵 **single-responsibility-modules** at `L21`
  - Class 'TestSessionManagerCreation' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L78`
  - Class 'TestSessionManagerStateTransitions' has 11 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L174`
  - Class 'TestSessionManagerPhaseAdvancement' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L226`
  - Class 'TestSessionManagerTokenBudget' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L297`
  - Class 'TestSessionManagerCheckpointing' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L335`
  - Class 'TestSessionManagerCleanup' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L24`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L31`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L81`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L87`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L177`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L183`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L229`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L235`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L272`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L278`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L300`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L306`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L338`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L344`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/test_session_store.py`** (6 violations)

- 🔵 **single-responsibility-modules** at `L15`
  - Class 'TestSessionStore' has 18 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L18`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L25`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L31`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/test_template_context_builder.py`** (16 violations)

- 🔵 **single-responsibility-modules** at `L64`
  - Class 'TestTemplateContextBuilder' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L176`
  - Class 'TestTemplateContextBuilderPhaseTranslation' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L289`
  - Class 'TestTemplateContextBuilderDifferentTaskTypes' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L377`
  - Class 'TestTemplateContextBuilderTokenTracking' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L67`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L90`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L95`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L179`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L193`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L292`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L306`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L380`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L390`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L29`
  - Method 'get_required_context_for_task_type' returns 'dict[str, Any]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/test_tool_domain.py`** (4 violations)

- 🔵 **single-responsibility-modules** at `L11`
  - Class 'TestToolDefinition' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L107`
  - Class 'TestToolProfile' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/test_tool_executor_bridge.py`** (23 violations)

- 🔵 **single-responsibility-modules** at `L16`
  - Class 'TestToolExecutorBridge' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L65`
  - Class 'TestReadFile' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L112`
  - Class 'TestWriteFile' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L155`
  - Class 'TestEditFile' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L202`
  - Class 'TestGlob' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L240`
  - Class 'TestBash' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L277`
  - Class 'TestListFiles' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L19`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L25`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L68`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L73`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L115`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L120`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L158`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L163`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L205`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L210`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L243`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L248`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L280`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L285`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/test_tool_registry.py`** (3 violations)

- 🔵 **single-responsibility-modules** at `L22`
  - Class 'TestToolRegistry' has 14 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/test_tool_selector.py`** (3 violations)

- 🔵 **single-responsibility-modules** at `L23`
  - Class 'TestToolSelector' has 14 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/tool_handlers/test_constants.py`** (3 violations)

- 🔵 **single-responsibility-modules** at `L14`
  - Class 'TestToolHandlerConstants' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/tool_handlers/test_file_handlers.py`** (7 violations)

- 🔵 **single-responsibility-modules** at `L37`
  - Class 'TestReadFileHandler' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L88`
  - Class 'TestWriteFileHandler' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L130`
  - Class 'TestEditFileHandler' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L21`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L29`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/tool_handlers/test_registry.py`** (6 violations)

- 🔵 **single-responsibility-modules** at `L28`
  - Class 'TestCreateStandardHandlers' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L109`
  - Class 'TestCreateMinimalHandlers' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L142`
  - Class 'TestToolHandlerRegistry' has 12 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L20`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/tool_handlers/test_search_handlers.py`** (6 violations)

- 🔵 **single-responsibility-modules** at `L50`
  - Class 'TestSearchCodeHandler' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L118`
  - Class 'TestLoadContextHandler' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L167`
  - Class 'TestFindRelatedHandler' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L19`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/tool_handlers/test_terminal_handlers.py`** (7 violations)

- 🔵 **single-responsibility-modules** at `L32`
  - Class 'TestCompleteHandler' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L117`
  - Class 'TestCannotFixHandler' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L179`
  - Class 'TestRequestHelpHandler' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L229`
  - Class 'TestPlanFixHandler' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L22`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/tool_handlers/test_types.py`** (5 violations)

- 🔵 **single-responsibility-modules** at `L18`
  - Class 'TestValidatePathSecurity' has 10 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **prefer-pytest-raises** at `L92`
  - Forbidden pattern found: 'try:
            symlink.symlink_to(outside_dir)
        except OSError:
            pytest.skip("Cannot create symlinks on this platform")

        resolved, error = validate_path_security("escape/secret.txt", tmp_path)

        assert error is not None, "Expected error is not None"
        assert "escapes project directory" in error, "Expected 'escapes project directory' in error"

    def test_absolute_path_outside_allowed(self, tmp_path):
        """Absolute path outside base directory is allowed (explicit paths trusted).

        Note: Absolute paths are trusted since the caller explicitly provided
        them. The security protection is primarily for relative paths that
        could use .. to escape the project directory.
        """
        # /etc/passwd exists on most Unix systems
        resolved, error = validate_path_security("/etc/passwd", tmp_path)

        # Allowed but file may not exist on all systems
        # If file exists, no error; if not, "not found" error
        if resolved.exists():
            assert error is None, "Expected error is None"
        else:
            assert error is not None, "Expected error is not None"
            assert "not found" in error.lower(), "Expected 'not found' in error.lower()"

    def test_path_with_valid_dots(self, tmp_path):
        """Path with .. that stays inside is allowed."""
        (tmp_path / "src").mkdir()
        (tmp_path / "lib").mkdir()
        test_file = tmp_path / "lib" / "module.py"
        test_file.write_text("# test")

        resolved, error = validate_path_security("src/../lib/module.py", tmp_path)

        assert error is None, "Expected error is None"
        assert resolved == test_file, "Expected resolved to equal test_file"


class TestActionHandler:
    """Tests for ActionHandler type."""

    def test_handler_is_callable_type(self):
        """ActionHandler is a callable type."""
        from typing import Any

        # ActionHandler should accept Dict[str, Any] and return str
        def my_handler(params: dict[str, Any]) -> str:
            return "result"

        # This is a type check - the function should be compatible
        handler: ActionHandler = my_handler
        assert callable(handler), "Expected callable() to be truthy"
        assert'
  - 💡 *Use: with pytest.raises(ExceptionType):*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L141`
  - Method 'my_handler' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/harness/tool_handlers/test_verify_handlers.py`** (5 violations)

- 🔵 **single-responsibility-modules** at `L149`
  - Class 'TestValidatePythonHandler' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L19`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L46`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/llm/test_client.py`** (3 violations)

- 🔵 **cli-tests-use-runner** at `file`
  - Required pattern not found: '(CliRunner|invoke\s*\()'
  - 💡 *Use CliRunner for testing: from click.testing import CliRunner*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/llm/test_factory.py`** (4 violations)

- 🔵 **single-responsibility-modules** at `L36`
  - Class 'TestLLMClientFactorySimulated' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L215`
  - Class 'TestLLMClientFactoryHelpers' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/llm/test_interface.py`** (4 violations)

- 🔵 **single-responsibility-modules** at `L85`
  - Class 'TestLLMResponse' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L187`
  - Class 'TestThinkingConfig' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/llm/test_recording.py`** (2 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/llm/test_simulated.py`** (6 violations)

- 🔵 **single-responsibility-modules** at `L25`
  - Class 'TestSimulatedResponse' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L84`
  - Class 'TestScriptedResponseStrategy' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L204`
  - Class 'TestPatternMatchingStrategy' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L256`
  - Class 'TestSimulatedLLMClient' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/llm/test_tools.py`** (7 violations)

- 🔵 **single-responsibility-modules** at `L45`
  - Class 'TestToolDefinitions' has 10 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L135`
  - Class 'TestToolCollections' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L183`
  - Class 'TestGetToolsForTask' has 10 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L294`
  - Class 'TestGetToolsByCategory' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L328`
  - Class 'TestListFunctions' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/pipeline/conftest.py`** (3 violations)

- 🔵 **single-responsibility-modules** at `L80`
  - Class 'TestExecutor' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **default-result-return-types** at `L96`
  - Method 'get_required_inputs' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L100`
  - Method 'stage_name' returns 'str', expected pattern 'Result|Either|Success|Failure'

**`tests/unit/pipeline/stages/conftest.py`** (1 violations)

- 🟡 **max-function-length** at `L177`
  - Function 'sample_spec_artifact' has 78 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*

**`tests/unit/pipeline/stages/test_analyze.py`** (3 violations)

- 🔵 **single-responsibility-modules** at `L13`
  - Class 'TestAnalyzeExecutor' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/pipeline/stages/test_clarify.py`** (3 violations)

- 🔵 **single-responsibility-modules** at `L13`
  - Class 'TestClarifyExecutor' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/pipeline/stages/test_deliver.py`** (13 violations)

- 🔵 **single-responsibility-modules** at `L14`
  - Class 'TestDeliveryMode' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L42`
  - Class 'TestDeliverPhaseExecutor' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L76`
  - Class 'TestDeliverPhaseConfiguration' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L115`
  - Class 'TestDeliverPhaseDeliveryModes' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L238`
  - Class 'TestDeliverPhaseCommitDelivery' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L390`
  - Class 'TestDeliverPhasePRDelivery' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L601`
  - Class 'TestDeliverPhaseSummaryGeneration' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **max-imports** at `L1`
  - File has 71 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **max-imports** at `L1`
  - File has 71 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **max-imports** at `L1`
  - File has 71 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **max-imports** at `L1`
  - File has 71 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/pipeline/stages/test_green.py`** (5 violations)

- 🔵 **single-responsibility-modules** at `L14`
  - Class 'TestGreenPhaseExecutor' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L59`
  - Class 'TestGreenPhaseTools' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L167`
  - Class 'TestGreenPhaseCompletion' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/pipeline/stages/test_intake.py`** (3 violations)

- 🔵 **single-responsibility-modules** at `L13`
  - Class 'TestIntakeExecutor' has 11 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/pipeline/stages/test_red.py`** (9 violations)

- 🔵 **single-responsibility-modules** at `L14`
  - Class 'TestRedPhaseExecutor' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L190`
  - Class 'TestFileBlockExtraction' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L267`
  - Class 'TestPytestOutputParsing' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🟡 **no-assert-true-false** at `L95`
  - Forbidden pattern found: 'assert True'
  - 💡 *Use specific assertions: assert result == expected*
- 🟡 **no-assert-true-false** at `L202`
  - Forbidden pattern found: 'assert True'
  - 💡 *Use specific assertions: assert result == expected*
- 🟡 **no-assert-true-false** at `L95`
  - Forbidden pattern found: 'assert True'
  - 💡 *Use specific assertions: assert result == expected*
- 🟡 **no-assert-true-false** at `L202`
  - Forbidden pattern found: 'assert True'
  - 💡 *Use specific assertions: assert result == expected*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/pipeline/stages/test_refactor.py`** (8 violations)

- 🔵 **single-responsibility-modules** at `L13`
  - Class 'TestRefactorPhaseExecutor' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L127`
  - Class 'TestRefactorPhaseExecution' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **max-imports** at `L1`
  - File has 40 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **max-imports** at `L1`
  - File has 40 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **max-imports** at `L1`
  - File has 40 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **max-imports** at `L1`
  - File has 40 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/pipeline/stages/test_spec.py`** (4 violations)

- 🔵 **single-responsibility-modules** at `L13`
  - Class 'TestSpecExecutor' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L81`
  - Method 'login' returns 'bool"
          description', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/pipeline/stages/test_stages_init.py`** (2 violations)

- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/pipeline/test_artifacts.py`** (4 violations)

- 🔵 **single-responsibility-modules** at `L223`
  - Class 'TestRedArtifact' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L283`
  - Class 'TestGreenArtifact' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/pipeline/test_config.py`** (10 violations)

- 🔵 **single-responsibility-modules** at `L125`
  - Class 'TestConfigurationLoader' has 12 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L348`
  - Class 'TestBuiltInTemplates' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L401`
  - Class 'TestExpandEnvVars' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L438`
  - Class 'TestPipelineTemplateLoader' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **max-imports** at `L1`
  - File has 37 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **max-imports** at `L1`
  - File has 37 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **max-imports** at `L1`
  - File has 37 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **max-imports** at `L1`
  - File has 37 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/pipeline/test_config_validator.py`** (8 violations)

- 🔵 **single-responsibility-modules** at `L36`
  - Class 'TestConfigValidator' has 13 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L263`
  - Class 'TestConfigValidatorIntegration' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **max-imports** at `L1`
  - File has 35 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **max-imports** at `L1`
  - File has 35 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **max-imports** at `L1`
  - File has 35 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **max-imports** at `L1`
  - File has 35 imports (max: 30)
  - 💡 *Consider splitting module or consolidating imports*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/pipeline/test_controller.py`** (4 violations)

- 🔵 **single-responsibility-modules** at `L24`
  - Class 'TestPipelineController' has 20 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L470`
  - Class 'TestContractEnforcement' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/pipeline/test_discovery_integration.py`** (5 violations)

- 🔵 **single-responsibility-modules** at `L84`
  - Class 'TestDiscoveredContext' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L153`
  - Class 'TestExtractContextFromProfile' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L239`
  - Class 'TestGetContractsForLanguage' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/pipeline/test_escalation.py`** (5 violations)

- 🔵 **single-responsibility-modules** at `L93`
  - Class 'TestEscalationHandler' has 13 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L96`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L100`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/pipeline/test_llm_stage_executor.py`** (3 violations)

- 🔵 **single-responsibility-modules** at `L13`
  - Class 'TestLLMStageExecutor' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/pipeline/test_module_exports.py`** (3 violations)

- 🔵 **single-responsibility-modules** at `L9`
  - Class 'TestModuleExports' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/pipeline/test_registry.py`** (3 violations)

- 🔵 **single-responsibility-modules** at `L21`
  - Class 'TestStageExecutorRegistry' has 11 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/pipeline/test_stage_executor.py`** (4 violations)

- 🔵 **single-responsibility-modules** at `L44`
  - Class 'TestStageResult' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L98`
  - Class 'TestStageExecutor' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/pipeline/test_state.py`** (5 violations)

- 🔵 **single-responsibility-modules** at `L45`
  - Class 'TestStageState' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L110`
  - Class 'TestPipelineState' has 10 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🟡 **no-sleep-in-tests** at `L244`
  - Forbidden pattern found: 'time.sleep('
  - 💡 *Use pytest-timeout, mocking, or async waiting instead*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/pipeline/test_state_machine_properties.py`** (4 violations)

- 🟡 **max-cyclomatic-complexity** at `L302`
  - Function 'test_to_dict_from_dict_roundtrip' has complexity 11 (max: 10)
  - 💡 *Break complex functions into smaller, focused helper functions*
- 🔵 **single-responsibility-modules** at `L167`
  - Class 'TestTimestampInvariant' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/pipeline/test_state_store.py`** (7 violations)

- 🔵 **single-responsibility-modules** at `L20`
  - Class 'TestPipelineStateStore' has 15 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L224`
  - Class 'TestStateStoreList' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **prefer-pytest-raises** at `L197`
  - Forbidden pattern found: 'try:
                # Retry load if we hit a race condition with concurrent write
                for _attempt in range(3):
                    loaded = store.load(state.pipeline_id)
                    if loaded is not None:
                        break
                    time.sleep(0.01)

                if loaded is not None:
                    loaded.config[f"update_{n}"] = n
                    store.save(loaded)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=update_state, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, "Expected len(errors) to equal 0"

        # State should have some updates (order depends on timing)
        final = store.load(state.pipeline_id)
        assert final is not None, "Expected final is not None"


class TestStateStoreList:
    """Tests for unified list() method - Phase 6 API Integration."""

    def test_list_all_pipelines(self, state_store, temp_project):
        """list() returns all pipelines when no filter."""
        # Create pipelines with various statuses
        for i, status in enumerate([
            PipelineStatus.PENDING,
            PipelineStatus.RUNNING,
            PipelineStatus.COMPLETED,
            PipelineStatus.FAILED,
        ]):
            state = create_pipeline_state(f"req{i}", temp_project)
            state.status = status
            state_store.save(state)

        all_pipelines = state_store.list()
        assert len(all_pipelines) == 4, "Expected len(all_pipelines) to equal 4"

    def test_list_filtered_by_status(self, state_store, temp_project):
        """list(status=...) filters correctly."""
        state1 = create_pipeline_state("req1", temp_project)
        state2 = create_pipeline_state("req2", temp_project)
        state3 = create_pipeline_state("req3", temp_project)

        state1.status = PipelineStatus.RUNNING
        state2.status = PipelineStatus.RUNNING
        state3.status = PipelineStatus.COMPLETED

        state_store.save(state1)
        state_store.save(state2)
        state_store.save(state3)

        running = state_store.list(status=PipelineStatus.RUNNING)
        assert len(running) == 2, "Expected len(running) to equal 2"

        completed = state_store.list(status=PipelineStatus.COMPLETED)
        assert len(completed) == 1, "Expected len(completed) to equal 1"

    def test_list_respects_limit(self, state_store, temp_project):
        """list(limit=N) returns at most N results."""
        for i in range(10):
            state = create_pipeline_state(f"req{i}", temp_project)
            state_store.save(state)

        limited = state_store.list(limit=5)
        assert len(limited) == 5, "Expected len(limited) to equal 5"

    def test_list_ordered_by_date_newest_first(self, state_store, temp_project):
        """list() returns results ordered by created_at descending."""
        import time

        states = []
        for i in range(3):
            state = create_pipeline_state(f"req{i}", temp_project)
            state_store.save(state)
            states.append(state)
            time.sleep(0.01)  # Ensure different timestamps

        result = state_store.list()

        # Newest (last created) should be first
        assert result[0].pipeline_id == states[2].pipeline_id, "Expected result[0].pipeline_id to equal states[2].pipeline_id"
        assert result[2].pipeline_id == states[0].pipeline_id, "Expected result[2].pipeline_id to equal states[0].pipeline_id"

    def test_list_empty_store(self, state_store):
        """list() returns empty list when no pipelines."""
        result = state_store.list()
        assert result == [], "Expected result to equal []"

    def test_list_with_status_and_limit(self, state_store, temp_project):
        """list() combines status filter and limit."""
        for i in range(10):
            state = create_pipeline_state(f"req{i}", temp_project)
            state.status = PipelineStatus.RUNNING if i < 7 else PipelineStatus.COMPLETED
            state_store.save(state)

        running = state_store.list(status=PipelineStatus.RUNNING, limit=3)
        assert len(running) == 3, "Expected len(running) to equal 3"
        for s in running:
            assert'
  - 💡 *Use: with pytest.raises(ExceptionType):*
- 🟡 **no-sleep-in-tests** at `L203`
  - Forbidden pattern found: 'time.sleep('
  - 💡 *Use pytest-timeout, mocking, or async waiting instead*
- 🟡 **no-sleep-in-tests** at `L281`
  - Forbidden pattern found: 'time.sleep('
  - 💡 *Use pytest-timeout, mocking, or async waiting instead*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/pipeline/test_types.py`** (3 violations)

- 🔵 **single-responsibility-modules** at `L18`
  - Class 'TestTypeAliasExports' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/pipeline/test_validator.py`** (17 violations)

- 🔵 **single-responsibility-modules** at `L16`
  - Class 'TestArtifactValidator' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L135`
  - Class 'TestValidateRequired' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L170`
  - Class 'TestValidateTypes' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L278`
  - Class 'TestStageInputValidation' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L340`
  - Class 'TestStageOutputValidation' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L384`
  - Class 'TestTransitionValidation' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L437`
  - Class 'TestLanguageSpecificValidation' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L19`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L138`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L173`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L219`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L281`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L343`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L387`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L440`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/tools/bridge/test_contract_builder.py`** (6 violations)

- 🔵 **single-responsibility-modules** at `L15`
  - Class 'TestContractBuilder' has 10 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L18`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L23`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L186`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/tools/bridge/test_domain.py`** (5 violations)

- 🟡 **max-function-length** at `L220`
  - Function 'test_enabled_disabled_counts' has 54 lines (max: 50)
  - 💡 *Extract logic into helper functions or use composition*
- 🔵 **single-responsibility-modules** at `L18`
  - Class 'TestConfidenceTier' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L92`
  - Class 'TestMappingContext' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/tools/bridge/test_profile_loader.py`** (6 violations)

- 🔵 **single-responsibility-modules** at `L14`
  - Class 'TestProfileLoader' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L129`
  - Class 'TestProfileLoaderEdgeCases' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L17`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L51`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/tools/bridge/test_registry.py`** (5 violations)

- 🔵 **single-responsibility-modules** at `L15`
  - Class 'TestMappingRegistry' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L117`
  - Method 'matches' returns 'bool', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L120`
  - Method 'get_templates' returns 'list[CheckTemplate]', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/tools/cicd/test_baseline.py`** (7 violations)

- 🔵 **single-responsibility-modules** at `L17`
  - Class 'TestBaselineManager' has 15 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L158`
  - Class 'TestGitHelper' has 11 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L20`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L25`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L31`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/tools/cicd/test_domain.py`** (12 violations)

- 🔵 **single-responsibility-modules** at `L46`
  - Class 'TestCIViolation' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L146`
  - Class 'TestBaseline' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L212`
  - Class 'TestBaselineComparison' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L298`
  - Class 'TestCIResult' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L375`
  - Class 'TestCIConfig' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L49`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L149`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L154`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L215`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L301`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/tools/cicd/test_outputs.py`** (8 violations)

- 🔵 **single-responsibility-modules** at `L98`
  - Class 'TestSarifOutput' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L175`
  - Class 'TestJunitOutput' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L238`
  - Class 'TestMarkdownOutput' has 11 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L35`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L60`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L78`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/tools/cicd/test_runner.py`** (10 violations)

- 🔵 **single-responsibility-modules** at `L19`
  - Class 'TestCheckCache' has 10 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L115`
  - Class 'TestCIRunner' has 19 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L22`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L27`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L32`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L118`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L124`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L144`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/tools/conformance/test_domain.py`** (13 violations)

- 🔵 **single-responsibility-modules** at `L26`
  - Class 'TestSeverity' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L58`
  - Class 'TestViolationId' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L97`
  - Class 'TestViolation' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L154`
  - Class 'TestExemptionScope' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L204`
  - Class 'TestExemption' has 16 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L328`
  - Class 'TestConformanceSummary' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L361`
  - Class 'TestConformanceReport' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L100`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L207`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L364`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L415`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/tools/conformance/test_manager.py`** (10 violations)

- 🔵 **single-responsibility-modules** at `L54`
  - Class 'TestConformanceManagerInitialize' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L113`
  - Class 'TestConformanceCheck' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L416`
  - Class 'TestListViolations' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L116`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L331`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L419`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L507`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L25`
  - Method '_make_violation' returns 'Violation', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/tools/conformance/test_stores.py`** (12 violations)

- 🔵 **single-responsibility-modules** at `L33`
  - Class 'TestAtomicFileWriter' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L77`
  - Class 'TestViolationStore' has 10 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L230`
  - Class 'TestExemptionRegistry' has 10 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L394`
  - Class 'TestHistoryStore' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L80`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L85`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L233`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L238`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L397`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L402`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/tools/generate/test_domain.py`** (6 violations)

- 🔵 **single-responsibility-modules** at `L91`
  - Class 'TestAPIError' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L165`
  - Class 'TestGeneratedFile' has 10 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L228`
  - Class 'TestGenerationContext' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L291`
  - Class 'TestGenerationResult' has 10 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/tools/generate/test_engine.py`** (11 violations)

- 🔵 **single-responsibility-modules** at `L77`
  - Class 'TestGenerationEngineBasic' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L143`
  - Class 'TestGenerationEngineErrors' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L220`
  - Class 'TestGenerationSession' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L34`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L55`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L63`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L80`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L223`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L422`
  - Method 'greet' returns 'str', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/tools/generate/test_parser.py`** (17 violations)

- 🔵 **single-responsibility-modules** at `L27`
  - Class 'TestResponseParserBasic' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L95`
  - Class 'TestResponseParserContentCleaning' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L147`
  - Class 'TestResponseParserSyntaxValidation' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L195`
  - Class 'TestResponseParserImplicitPaths' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L242`
  - Class 'TestResponseParserExplanation' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L295`
  - Class 'TestMultiLanguageParser' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L389`
  - Class 'TestEdgeCases' has 10 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L30`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L98`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L150`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L154`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L198`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L245`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L298`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L392`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/tools/generate/test_prompt_builder.py`** (21 violations)

- 🔵 **single-responsibility-modules** at `L21`
  - Class 'TestPromptBuilder' has 15 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L146`
  - Class 'TestPromptBuilderExistingCode' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L187`
  - Class 'TestPromptBuilderPatterns' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L223`
  - Class 'TestPromptBuilderExamples' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L261`
  - Class 'TestPromptBuilderErrorContext' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L24`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L29`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L149`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L153`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L190`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L194`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L226`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L230`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L264`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L268`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L319`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L361`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🟡 **no-assert-true-false** at `L293`
  - Forbidden pattern found: 'assert False'
  - 💡 *Use specific assertions: assert result == expected*
- 🟡 **no-assert-true-false** at `L293`
  - Forbidden pattern found: 'assert False'
  - 💡 *Use specific assertions: assert result == expected*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/tools/generate/test_provider.py`** (5 violations)

- 🔵 **single-responsibility-modules** at `L27`
  - Class 'TestClaudeProvider' has 11 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L176`
  - Class 'TestManualProvider' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L268`
  - Class 'TestGetProvider' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/tools/generate/test_writer.py`** (16 violations)

- 🔵 **single-responsibility-modules** at `L19`
  - Class 'TestCodeWriterBasic' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L118`
  - Class 'TestCodeWriterRollback' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L196`
  - Class 'TestCodeWriterHeader' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L268`
  - Class 'TestCodeWriterAtomicWrites' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L394`
  - Class 'TestCodeWriterCleanup' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L22`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L76`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L121`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L199`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L271`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L279`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L320`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L363`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L397`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/tools/tdflow/runners/test_dotnet.py`** (6 violations)

- 🔵 **single-responsibility-modules** at `L17`
  - Class 'TestDotNetTestRunner' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L20`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L35`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L36`
  - Method 'runner' returns 'DotNetTestRunner', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/tools/tdflow/runners/test_pytest_runner.py`** (7 violations)

- 🔵 **single-responsibility-modules** at `L11`
  - Class 'TestPytestRunner' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L109`
  - Class 'TestTestRunnerDetection' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L14`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L28`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L29`
  - Method 'runner' returns 'PytestRunner', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/tools/tdflow/test_domain.py`** (6 violations)

- 🔵 **single-responsibility-modules** at `L44`
  - Class 'TestRunResult' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L109`
  - Class 'TestTDFlowSession' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L112`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L113`
  - Method 'session' returns 'TDFlowSession', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/tools/tdflow/test_orchestrator.py`** (11 violations)

- 🔵 **single-responsibility-modules** at `L25`
  - Class 'TestTDFlowOrchestrator' has 11 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L177`
  - Class 'TestOrchestratorComponentSelection' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L28`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L34`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L51`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L180`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L35`
  - Method 'spec_file' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L52`
  - Method 'orchestrator' returns 'TDFlowOrchestrator', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L181`
  - Method 'session_with_components' returns 'TDFlowSession', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/tools/tdflow/test_session.py`** (9 violations)

- 🔵 **single-responsibility-modules** at `L20`
  - Class 'TestSessionManager' has 10 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🟡 **no-sleep-in-tests** at `L110`
  - Forbidden pattern found: 'time.sleep('
  - 💡 *Use pytest-timeout, mocking, or async waiting instead*
- 🔵 **fixtures-in-conftest** at `L23`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L29`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L48`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L30`
  - Method 'spec_file' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L49`
  - Method 'manager' returns 'SessionManager', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/tools/test_builtin_checks_architecture.py`** (58 violations)

- 🔵 **single-responsibility-modules** at `L87`
  - Class 'TestCheckLayerImports' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L295`
  - Class 'TestCheckConstructorInjection' has 8 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L464`
  - Class 'TestCheckDomainPurity' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L613`
  - Class 'TestCheckCircularImports' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L769`
  - Class 'TestEdgeCases' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🟡 **no-real-network-calls** at `L475`
  - Forbidden pattern found: 'requests.get('
  - 💡 *Use responses, httpretty, or pytest-mock to mock network calls*
- 🟡 **no-real-network-calls** at `L896`
  - Forbidden pattern found: 'requests.get('
  - 💡 *Use responses, httpretty, or pytest-mock to mock network calls*
- 🟡 **unit-tests-isolated** at `L487`
  - Forbidden pattern found: 'sqlite3'
  - 💡 *Mock database connections in unit tests*
- 🟡 **unit-tests-isolated** at `L491`
  - Forbidden pattern found: 'sqlite3'
  - 💡 *Mock database connections in unit tests*
- 🟡 **unit-tests-isolated** at `L504`
  - Forbidden pattern found: 'sqlite3'
  - 💡 *Mock database connections in unit tests*
- 🔵 **fixtures-in-conftest** at `L37`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L56`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L77`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L298`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **no-hardcoded-test-data-paths** at `L897`
  - Forbidden pattern found: 'open("'
  - 💡 *Use tmp_path fixture or Path(__file__).parent for test data*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L38`
  - Method 'layer_detection' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L57`
  - Method 'layer_rules' returns 'dict', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L78`
  - Method 'temp_project' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L90`
  - Method 'test_domain_importing_infrastructure_fails' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L117`
  - Method 'test_domain_importing_application_fails' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L141`
  - Method 'test_application_importing_domain_passes' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L152`
  - Method 'get_user' returns 'User', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L167`
  - Method 'test_stdlib_imports_pass' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L196`
  - Method 'test_import_form_detected' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L220`
  - Method 'test_qualified_import_detected' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L244`
  - Method 'test_no_layer_match_ignored' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L268`
  - Method 'test_syntax_error_gracefully_handled' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L299`
  - Method 'class_patterns' returns 'list', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L303`
  - Method 'test_service_with_no_init_fails' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L324`
  - Method 'test_service_with_no_params_fails' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L348`
  - Method 'test_service_with_injected_deps_passes' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L371`
  - Method 'test_non_service_class_ignored' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L393`
  - Method 'test_direct_instantiation_in_init_fails' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L419`
  - Method 'test_handler_class_checked' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L439`
  - Method 'test_check_for_init_params_disabled' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L467`
  - Method 'test_importing_requests_fails' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L487`
  - Method 'test_importing_sqlite3_fails' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L506`
  - Method 'test_calling_open_fails' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L524`
  - Method 'test_calling_subprocess_fails' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L542`
  - Method 'test_pure_business_logic_passes' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L554`
  - Method 'total' returns 'Decimal', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L560`
  - Method 'apply_discount' returns 'Decimal', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L571`
  - Method 'test_from_import_detected' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L589`
  - Method 'test_custom_forbidden_imports' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L616`
  - Method 'test_simple_cycle_detected' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L645`
  - Method 'test_three_way_cycle_detected' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L662`
  - Method 'test_type_checking_imports_ignored' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L697`
  - Method 'test_no_cycles_passes' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L730`
  - Method 'test_max_depth_limits_detection' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L747`
  - Method 'test_syntax_error_gracefully_handled' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L772`
  - Method 'test_empty_file_list' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L805`
  - Method 'test_nonexistent_file' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L818`
  - Method 'test_empty_file' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L829`
  - Method 'test_unicode_content' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L845`
  - Method 'test_relative_path_handling' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L881`
  - Method 'test_complete_architecture_validation' returns 'None', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/tools/test_context_assembler.py`** (6 violations)

- 🔵 **single-responsibility-modules** at `L45`
  - Class 'TestLayerDetection' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L111`
  - Class 'TestLanguageDetection' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L322`
  - Class 'TestAssemblyMethods' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L395`
  - Class 'TestProcessingMethods' has 12 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/tools/test_context_retrieval.py`** (5 violations)

- 🔵 **single-responsibility-modules** at `L17`
  - Class 'TestContextRetrieverInit' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L127`
  - Class 'TestContextRetrieverRetrieve' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L251`
  - Class 'TestKeywordExtraction' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/tools/test_contracts_execution_naming.py`** (11 violations)

- 🔵 **single-responsibility-modules** at `L22`
  - Class 'TestExtractSymbols' has 9 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L112`
  - Class 'TestExtractClassWithBases' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L154`
  - Class 'TestParseInheritanceList' has 4 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L179`
  - Class 'TestNamingCheck' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L258`
  - Class 'TestAstInterfaceCheck' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **fixtures-in-conftest** at `L182`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **fixtures-in-conftest** at `L261`
  - Forbidden pattern found: '@pytest.fixture'
  - 💡 *Move shared fixtures to conftest.py*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **default-result-return-types** at `L183`
  - Method 'temp_cs_file' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **default-result-return-types** at `L262`
  - Method 'temp_command_file' returns 'Path', expected pattern 'Result|Either|Success|Failure'
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/tools/test_verification_checks.py`** (7 violations)

- 🔵 **single-responsibility-modules** at `L18`
  - Class 'TestCommandCheck' has 7 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L158`
  - Class 'TestRegexCheck' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L249`
  - Class 'TestFileExistsCheck' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L395`
  - Class 'TestCustomCheck' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L483`
  - Class 'TestASTCheck' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`tests/unit/tools/test_verification_runner.py`** (6 violations)

- 🔵 **single-responsibility-modules** at `L18`
  - Class 'TestVerificationRunnerInit' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L83`
  - Class 'TestVariableSubstitution' has 6 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L131`
  - Class 'TestProfileManagement' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **single-responsibility-modules** at `L335`
  - Class 'TestRunCheck' has 5 methods (max: 3)
  - 💡 *Split modules with too many classes into focused single-class modules*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*
- 🔵 **require-lineage-metadata-python** at `L1`
  - File missing lineage metadata (no audit trail)
  - 💡 *Add lineage header to file:
# @spec_file: .agentforge/specs/your-spec-v1.yaml
# @spec_id: your-spec-v1
# @component_id: component-name
# @impl_path: path/to/implementation.py
Or regenerate file through TDFLOW to get proper lineage.*

**`workflows/spec_workflow.yaml`** (2 violations)

- 🔵 **file-structure** at `file`
  - Spec-like file outside .agentforge/specs/
  - 💡 *Move spec files to .agentforge/specs/*
- 🔵 **file-structure** at `file`
  - Spec-like file outside .agentforge/specs/
  - 💡 *Move spec files to .agentforge/specs/*

</details>

---
*Generated at 2026-01-03 20:22:54 UTC*
*Commit: `914daaad`*