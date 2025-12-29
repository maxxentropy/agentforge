# Configuration Files

Machine-verifiable configuration for AgentForge.

## Config Files

| File | Schema | Purpose |
|------|--------|---------|
| `execution.yaml` | `schemas/execution.schema.yaml` | Execution mode settings |
| `context_retrieval.yaml` | `schemas/context_retrieval.schema.yaml` | Code retrieval settings |
| `architecture.yaml` | `schemas/architecture.schema.yaml` | Project architecture rules |

## Validation

```bash
# Validate execution config
python tools/validate_schema.py schemas/execution.schema.yaml config/execution.yaml

# Validate architecture rules
python tools/validate_schema.py schemas/architecture.schema.yaml config/architecture.yaml

# Validate context retrieval
python tools/validate_schema.py schemas/context_retrieval.schema.yaml config/context_retrieval.yaml
```

## Customization

### execution.yaml

Configure how prompts are executed:

```yaml
default_mode: human_in_loop  # or api_sequential, api_parallel

human_in_loop:
  prompt_output_dir: "outputs/prompts"
  
api_sequential:
  model: "claude-sonnet-4-20250514"
  requests_per_minute: 50
```

### architecture.yaml

Define your project's rules (the "physics"):

```yaml
layers:
  domain:
    path: "src/Domain"
    allowed_dependencies: []  # Domain has no dependencies
    
  application:
    path: "src/Application"
    allowed_dependencies: [domain]

dependency_rules:
  - id: "ARCH-001"
    rule: "Domain cannot reference Infrastructure"
    from_layer: domain
    to_layer: infrastructure
    allowed: false
    severity: blocking
```

### context_retrieval.yaml

Configure code retrieval:

```yaml
lsp:
  servers:
    csharp:
      enabled: true
      
vector:
  enabled: true
  chunking:
    strategy: "ast_aware"
```

## Sample vs Production

The included configs are samples. For your project:

1. Copy `config/architecture.yaml` to your project
2. Modify layers, rules, patterns for your architecture
3. Validate: `python tools/validate_schema.py schemas/architecture.schema.yaml your_architecture.yaml`
