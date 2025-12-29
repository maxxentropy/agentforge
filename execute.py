#!/usr/bin/env python3
"""
AgentForge Executor
===================

Run contracts via Claude Code CLI (subscription) or Anthropic API.

DEFAULT: Uses Claude Code CLI (your subscription, no extra cost)

Usage:
    python execute.py intake --request "Add discount codes to orders"
    
With API instead (pay-per-token):
    export ANTHROPIC_API_KEY=your_key
    python execute.py intake --request "Add discount codes" --use-api
"""

import os
import sys
import yaml
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from run_contract import ContractRunner


def call_claude_code(system: str, user: str) -> str:
    """
    Call Claude Code CLI (uses your subscription, no API credits needed).
    
    This is the DEFAULT execution method.
    Uses --output-format json and --append-system-prompt for structured output.
    """
    import tempfile
    import json as json_module
    
    # The main prompt content
    full_prompt = f"""{system}

---

{user}"""
    
    # Write prompt to temp file (handles large prompts better)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(full_prompt)
        temp_path = f.name
    
    # System prompt enforcement for YAML-only output with readable formatting
    yaml_enforcement = """CRITICAL: You are in YAML-only output mode.

OUTPUT RULES:
- Output ONLY valid YAML, nothing else
- NO prose, NO explanations, NO markdown code blocks
- NO text before or after the YAML
- Do NOT use ``` markers
- The response must be directly parseable by a YAML parser

YAML FORMATTING FOR READABILITY:
- Use literal block style (|) for multiline strings, NOT quoted strings with \\n
- Use proper indentation (2 spaces)
- Keep lines under 100 characters where possible
- Use folded style (>) for long single paragraphs if needed

EXAMPLE - BAD (hard to read):
  description: "This is a long description\\nthat spans multiple lines\\nand is hard to read"

EXAMPLE - GOOD (readable):
  description: |
    This is a long description
    that spans multiple lines
    and is easy to read"""
    
    try:
        # Call claude CLI with:
        # --output-format json: Get structured response wrapper
        # --append-system-prompt: Enforce YAML-only output
        result = subprocess.run(
            [
                'claude', '-p', f'@{temp_path}',
                '--output-format', 'json',
                '--append-system-prompt', yaml_enforcement
            ],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes for complex prompts
            env={**os.environ, 'NO_COLOR': '1'}  # Disable color codes in output
        )
        
        if result.returncode != 0:
            print(f"Claude Code error (exit {result.returncode}):")
            print(result.stderr or result.stdout)
            sys.exit(1)
        
        # Parse the JSON wrapper to get the actual response
        try:
            json_response = json_module.loads(result.stdout)
            
            # Debug: print structure if needed
            # print(f"DEBUG: JSON keys: {json_response.keys() if isinstance(json_response, dict) else 'not a dict'}")
            
            # Handle different response structures
            if isinstance(json_response, dict):
                # Try result.content[0].text (newer format)
                if 'result' in json_response:
                    result_obj = json_response['result']
                    if isinstance(result_obj, dict):
                        content = result_obj.get('content', [])
                        if content and len(content) > 0:
                            first_content = content[0]
                            if isinstance(first_content, dict):
                                return first_content.get('text', str(first_content))
                            return str(first_content)
                    elif isinstance(result_obj, str):
                        # result is directly a string
                        return result_obj
                
                # Try messages array (conversation format)
                if 'messages' in json_response:
                    for msg in reversed(json_response['messages']):
                        if isinstance(msg, dict) and msg.get('role') == 'assistant':
                            content = msg.get('content', [])
                            if isinstance(content, str):
                                return content
                            if isinstance(content, list):
                                for block in content:
                                    if isinstance(block, dict) and block.get('type') == 'text':
                                        return block.get('text', '')
                                    elif isinstance(block, str):
                                        return block
                
                # Try direct text field
                if 'text' in json_response:
                    return json_response['text']
                
                # Try content directly
                if 'content' in json_response:
                    content = json_response['content']
                    if isinstance(content, str):
                        return content
                    if isinstance(content, list) and len(content) > 0:
                        first = content[0]
                        if isinstance(first, dict):
                            return first.get('text', str(first))
                        return str(first)
            
            # If json_response is a string, return it
            if isinstance(json_response, str):
                return json_response
            
            # Last fallback - return raw stdout
            return result.stdout
            
        except json_module.JSONDecodeError:
            # If not JSON, return raw output
            return result.stdout
        
    except FileNotFoundError:
        print("=" * 60)
        print("ERROR: 'claude' command not found")
        print("=" * 60)
        print()
        print("Claude Code CLI is not installed or not in PATH.")
        print()
        print("Options:")
        print("  1. Install Claude Code: npm install -g @anthropic-ai/claude-code")
        print("     (Requires Node.js and Claude Pro/Team subscription)")
        print()
        print("  2. Use API mode instead:")
        print("     export ANTHROPIC_API_KEY=your_key")
        print("     python execute.py intake --request '...' --use-api")
        print()
        sys.exit(1)
        
    except subprocess.TimeoutExpired:
        print("Error: Claude Code timed out after 5 minutes")
        sys.exit(1)
        
    finally:
        try:
            os.unlink(temp_path)
        except OSError:
            pass


def call_anthropic_api(system: str, user: str, max_tokens: int = 4096, temperature: float = 0.0) -> str:
    """
    Call Anthropic API directly (pay-per-token).
    
    Use with --use-api flag.
    """
    try:
        import anthropic
    except ImportError:
        print("Error: anthropic package not installed")
        print("Run: pip install anthropic")
        sys.exit(1)
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print()
        print("Get your API key from: https://console.anthropic.com/")
        print()
        print("Or use Claude Code CLI instead (uses subscription):")
        print("  python execute.py intake --request '...'  # no --use-api flag")
        sys.exit(1)
    
    client = anthropic.Anthropic(api_key=api_key)
    
    print("  Calling Anthropic API...")
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[
            {"role": "user", "content": user}
        ]
    )
    
    return response.content[0].text


def extract_yaml_from_response(response: str) -> str:
    """Extract YAML content from a response that may include markdown or prose."""
    import re
    
    # Try to find YAML in code blocks first
    yaml_block_pattern = r'```ya?ml?\s*\n(.*?)```'
    matches = re.findall(yaml_block_pattern, response, re.DOTALL | re.IGNORECASE)
    
    if matches:
        # Return the last YAML block (most likely to be the actual output)
        return matches[-1].strip()
    
    # Try to find any code block
    code_block_pattern = r'```\s*\n(.*?)```'
    matches = re.findall(code_block_pattern, response, re.DOTALL)
    
    if matches:
        # Check if any block looks like YAML
        for match in reversed(matches):
            if ':' in match and not match.strip().startswith('{'):
                return match.strip()
    
    # No code blocks - try to find YAML-like content
    lines = response.split('\n')
    yaml_lines = []
    in_yaml = False
    
    for line in lines:
        # YAML typically starts with a key: value or list item
        if re.match(r'^[a-z_]+:', line) or re.match(r'^- ', line):
            in_yaml = True
        
        if in_yaml:
            # Stop if we hit obvious prose
            if line.startswith('**') or line.startswith('Looking at') or line.startswith('Let me'):
                if yaml_lines:
                    break
                continue
            yaml_lines.append(line)
    
    if yaml_lines:
        return '\n'.join(yaml_lines).strip()
    
    # Last resort: return as-is
    return response.strip()


def execute_contract(contract_id: str, inputs: dict, use_api: bool = False) -> dict:
    """Execute a contract and return parsed output."""
    runner = ContractRunner()
    contract = runner.load_contract(contract_id)
    
    prompt_data = runner.assemble_prompt(contract, inputs)
    
    system = prompt_data['prompt']['system']
    user = prompt_data['prompt']['user']
    max_tokens = prompt_data['execution'].get('max_tokens', 4096)
    temperature = prompt_data['execution'].get('temperature', 0.0)
    
    print(f"  Contract: {contract_id}")
    
    if use_api:
        print("  Mode: Anthropic API (pay-per-token)")
        response = call_anthropic_api(system, user, max_tokens, temperature)
    else:
        print("  Mode: Claude Code CLI (subscription)")
        response = call_claude_code(system, user)
    
    # Extract YAML from response
    yaml_content = extract_yaml_from_response(response)
    
    # Parse YAML response
    try:
        parsed = yaml.safe_load(yaml_content)
        if parsed is None:
            raise yaml.YAMLError("Empty YAML")
        return parsed
        
    except yaml.YAMLError as e:
        print(f"\nWarning: Could not parse response as YAML")
        print(f"Error: {e}")
        print("\nExtracted content:")
        print("-" * 40)
        print(yaml_content[:500])
        if len(yaml_content) > 500:
            print(f"... ({len(yaml_content) - 500} more characters)")
        print("-" * 40)
        print("\nRaw response:")
        print("-" * 40)
        print(response[:500])
        print("-" * 40)
        return {"_raw": response, "_parse_error": str(e)}


def run_intake(args):
    """Execute INTAKE contract."""
    print()
    print("=" * 60)
    print("INTAKE")
    print("=" * 60)
    
    inputs = {
        'raw_request': args.request,
        'priority': args.priority or 'medium',
    }
    
    result = execute_contract('spec.intake.v1', inputs, args.use_api)
    
    # Save output
    output_path = Path('outputs/intake_record.yaml')
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w') as f:
        yaml.dump(result, f, default_flow_style=False, sort_keys=False)
    
    print(f"\n✅ Saved to: {output_path}")
    print()
    print("-" * 60)
    print("RESULT")
    print("-" * 60)
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))
    
    # Show next step
    if result.get('detected_scope') == 'unclear' or result.get('initial_questions'):
        questions = result.get('initial_questions', [])
        blocking = [q for q in questions if q.get('priority') == 'blocking']
        
        if blocking:
            print("-" * 60)
            print("BLOCKING QUESTIONS (answer before proceeding)")
            print("-" * 60)
            for i, q in enumerate(blocking, 1):
                print(f"  {i}. {q.get('question', 'N/A')}")
            print()
            print("Next: python execute.py clarify")


def run_clarify(args):
    """Execute CLARIFY contract."""
    print()
    print("=" * 60)
    print("CLARIFY")
    print("=" * 60)
    
    # Load intake record
    intake_path = Path(args.intake_file)
    if not intake_path.exists():
        print(f"Error: {intake_path} not found")
        print("Run intake first: python execute.py intake --request '...'")
        sys.exit(1)
    
    with open(intake_path) as f:
        intake_record = yaml.safe_load(f)
    
    # Load history if exists
    history = []
    history_path = Path('outputs/conversation_history.yaml')
    if history_path.exists():
        with open(history_path) as f:
            history = yaml.safe_load(f) or []
    
    # Add answer to history if provided
    if args.answer:
        history.append({
            'question': 'Previous question',
            'answer': args.answer,
            'timestamp': datetime.now().isoformat()
        })
        with open(history_path, 'w') as f:
            yaml.dump(history, f, default_flow_style=False)
    
    inputs = {
        'intake_record': intake_record,
        'conversation_history': history,
    }
    
    result = execute_contract('spec.clarify.v1', inputs, args.use_api)
    
    print()
    print("-" * 60)
    print("RESULT")
    print("-" * 60)
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))
    
    mode = result.get('mode', 'unknown')
    
    if mode == 'question':
        question = result.get('question', {})
        print("-" * 60)
        print("QUESTION FOR YOU")
        print("-" * 60)
        print(f"\n  {question.get('text', 'No question')}\n")
        print("Run with your answer:")
        print(f"  python execute.py clarify --answer \"your answer here\"")
        
    elif mode == 'complete':
        output_path = Path('outputs/clarification_log.yaml')
        with open(output_path, 'w') as f:
            yaml.dump(result.get('clarification_log', result), f, default_flow_style=False)
        
        print(f"\n✅ Clarification complete! Saved to: {output_path}")
        print()
        print("Next: python execute.py analyze")


def run_analyze(args):
    """Execute ANALYZE contract."""
    print()
    print("=" * 60)
    print("ANALYZE")
    print("=" * 60)

    # Load required files
    intake_path = Path(args.intake_file)
    clarify_path = Path(args.clarification_file)

    if not intake_path.exists():
        print(f"Error: {intake_path} not found")
        sys.exit(1)
    if not clarify_path.exists():
        print(f"Error: {clarify_path} not found")
        sys.exit(1)

    with open(intake_path) as f:
        intake_record = yaml.safe_load(f)
    with open(clarify_path) as f:
        clarification_log = yaml.safe_load(f)

    # Load architecture if exists
    arch_path = Path('config/architecture.yaml')
    architecture_rules = ""
    if arch_path.exists():
        with open(arch_path) as f:
            architecture_rules = f.read()

    # Get code context if project path provided
    code_context = args.code_context or "No code context provided."

    if args.project_path:
        print(f"\n  Retrieving context from: {args.project_path}")
        try:
            sys.path.insert(0, str(Path(__file__).parent / 'tools'))
            from context_retrieval import ContextRetriever

            retriever = ContextRetriever(args.project_path)

            # Build query from intake record
            query_parts = [
                intake_record.get('detected_intent', ''),
                intake_record.get('detected_scope', ''),
                intake_record.get('original_request', ''),
            ]
            query = ' '.join(part for part in query_parts if part)

            context = retriever.retrieve(query, budget_tokens=6000)

            print(f"  Found {len(context.files)} relevant files")
            print(f"  Found {len(context.symbols)} relevant symbols")
            print(f"  Total tokens: {context.total_tokens}")

            # Format for LLM consumption
            code_context = context.to_prompt_text()

            retriever.shutdown()

        except ImportError as e:
            print(f"  Warning: Context retrieval not available: {e}")
        except Exception as e:
            print(f"  Warning: Context retrieval failed: {e}")

    inputs = {
        'intake_record': intake_record,
        'clarification_log': clarification_log,
        'architecture_rules': architecture_rules or "No architecture rules configured.",
        'code_context': code_context,
    }

    result = execute_contract('spec.analyze.v1', inputs, args.use_api)
    
    output_path = Path('outputs/analysis_report.yaml')
    with open(output_path, 'w') as f:
        yaml.dump(result, f, default_flow_style=False, sort_keys=False)
    
    print(f"\n✅ Saved to: {output_path}")
    print()
    print("-" * 60)
    print("RESULT")
    print("-" * 60)
    print(yaml.dump(result, default_flow_style=False, sort_keys=False)[:2000])
    print()
    print("Next: python execute.py draft")


def run_draft(args):
    """Execute DRAFT contract."""
    print()
    print("=" * 60)
    print("DRAFT")
    print("=" * 60)
    
    # Load required files
    with open(args.intake_file) as f:
        intake_record = yaml.safe_load(f)
    with open(args.clarification_file) as f:
        clarification_log = yaml.safe_load(f)
    with open(args.analysis_file) as f:
        analysis_report = yaml.safe_load(f)
    
    inputs = {
        'intake_record': intake_record,
        'clarification_log': clarification_log,
        'analysis_report': analysis_report,
    }
    
    result = execute_contract('spec.draft.v1', inputs, args.use_api)
    
    # Draft output is now YAML (specification.schema.yaml)
    output_path = Path('outputs/specification.yaml')
    
    if isinstance(result, dict) and '_raw' not in result:
        # Successfully parsed as YAML - save it
        with open(output_path, 'w') as f:
            yaml.dump(result, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
        print(f"\n✅ Specification saved to: {output_path}")
        print()
        print("-" * 60)
        print("SUMMARY")
        print("-" * 60)
        
        # Show summary
        metadata = result.get('metadata', {})
        print(f"  Feature: {metadata.get('feature_name', 'Unknown')}")
        print(f"  Version: {metadata.get('version', '1.0')}")
        print(f"  Status: {metadata.get('status', 'draft')}")
        
        reqs = result.get('requirements', {})
        fr_count = len(reqs.get('functional', []))
        nfr_count = len(reqs.get('non_functional', []))
        entity_count = len(result.get('entities', []))
        
        print(f"  Functional Requirements: {fr_count}")
        print(f"  Non-Functional Requirements: {nfr_count}")
        print(f"  Entities: {entity_count}")
        
        print()
        print("Validate schema: python tools/validate_schema.py schemas/specification.schema.yaml outputs/specification.yaml")
        print("Render to markdown: python execute.py render-spec")
        print("Next step: python execute.py validate")
        
    else:
        # Couldn't parse as YAML - save raw and warn
        raw_path = Path('outputs/specification_raw.txt')
        raw_content = result.get('_raw', str(result)) if isinstance(result, dict) else str(result)
        with open(raw_path, 'w') as f:
            f.write(raw_content)
        
        print(f"\n⚠️  Could not parse output as YAML")
        print(f"   Raw output saved to: {raw_path}")
        print(f"   Error: {result.get('_parse_error', 'Unknown')}")
        print()
        print("Try re-running the draft step.")


def run_validate(args):
    """Execute VALIDATE contract."""
    print()
    print("=" * 60)
    print("VALIDATE")
    print("=" * 60)
    
    spec_path = Path(args.spec_file)
    if not spec_path.exists():
        print(f"Error: {spec_path} not found")
        print("Run 'python execute.py draft' first")
        sys.exit(1)
    
    # Load specification - handle both YAML and markdown
    with open(spec_path) as f:
        spec_content = f.read()
    
    # If YAML, also load as structured data for better validation
    specification_data = None
    if spec_path.suffix in ['.yaml', '.yml']:
        try:
            specification_data = yaml.safe_load(spec_content)
            print(f"  Spec format: YAML (structured)")
        except yaml.YAMLError:
            print(f"  Spec format: YAML (parse failed, using raw)")
    else:
        print(f"  Spec format: Markdown")
    
    with open(args.analysis_file) as f:
        analysis_report = yaml.safe_load(f)
    
    arch_path = Path('config/architecture.yaml')
    architecture_rules = ""
    if arch_path.exists():
        with open(arch_path) as f:
            architecture_rules = f.read()
    
    # Pass both raw content and structured data if available
    inputs = {
        'specification': spec_content,
        'specification_data': specification_data,  # Structured YAML if available
        'analysis_report': analysis_report,
        'architecture_rules': architecture_rules,
    }
    
    result = execute_contract('spec.validate.v1', inputs, args.use_api)
    
    output_path = Path('outputs/validation_report.yaml')
    with open(output_path, 'w') as f:
        yaml.dump(result, f, default_flow_style=False, sort_keys=False)
    
    print(f"\n✅ Saved to: {output_path}")
    print()
    print("-" * 60)
    print("RESULT")
    print("-" * 60)
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))
    
    verdict = result.get('overall_verdict', 'unknown')
    print("-" * 60)
    print(f"VERDICT: {verdict.upper()}")
    print("-" * 60)
    
    if verdict == 'approved':
        print("\n✅ Specification approved! Ready for implementation.")
    elif verdict == 'approved_with_notes':
        print("\n✅ Specification approved with conditions.")
        print("   Address approval_conditions before implementation, or run:")
        print("   python execute.py revise")
    elif verdict == 'needs_revision':
        print("\n⚠️  Specification needs revision. Run:")
        print("   python execute.py revise")
        print("   Then re-validate: python execute.py validate")
    else:
        print("\n❌ Specification rejected. Major rework needed.")
        print("   Run: python execute.py revise")


def run_revise(args):
    """
    Revision workflow with session management.
    
    Modes:
      - Interactive (default): Human makes decisions one by one
      - Autonomous (--auto): Agent makes decisions, flags uncertain ones
      - Continue (--continue): Resume paused session
      - Apply (--apply): Apply all decisions to spec
      - Status (--status): Show session status
    """
    
    if args.status:
        return show_revision_status(args)
    
    if args.apply:
        return apply_revision_session(args)
    
    if args.resume:
        return continue_revision_session(args)
    
    # Start new session or continue existing
    session_path = Path('outputs/revision_session.yaml')
    
    if session_path.exists() and not args.force:
        print()
        print("⚠️  Existing revision session found.")
        print()
        with open(session_path) as f:
            session = yaml.safe_load(f)
        print(f"  Status: {session.get('status', 'unknown')}")
        print(f"  Issues: {session.get('summary', {}).get('total_issues', '?')}")
        print(f"  Resolved: {session.get('summary', {}).get('resolved', '?')}")
        print()
        print("Options:")
        print("  python execute.py revise --continue   # Resume session")
        print("  python execute.py revise --status     # View details")
        print("  python execute.py revise --apply      # Apply decisions")
        print("  python execute.py revise --force      # Start fresh")
        return
    
    # Create new session
    session = create_revision_session(args)
    
    if session is None:
        return
    
    # Save initial session
    save_revision_session(session)
    
    if args.auto:
        # Autonomous mode
        run_autonomous_revision(session, args)
    else:
        # Interactive mode
        run_interactive_revision(session, args)


def create_revision_session(args) -> dict:
    """Create a new revision session from validation report."""
    print()
    print("=" * 60)
    print("REVISE - Creating Session")
    print("=" * 60)
    
    # Load specification
    spec_path = Path(args.spec_file)
    if not spec_path.exists():
        print(f"Error: {spec_path} not found")
        return None
    
    with open(spec_path) as f:
        specification = yaml.safe_load(f)
    
    # Load validation report
    validation_path = Path(args.validation_file)
    if not validation_path.exists():
        print(f"Error: {validation_path} not found")
        print("Run 'python execute.py validate' first")
        return None
    
    with open(validation_path) as f:
        validation_report = yaml.safe_load(f)
    
    verdict = validation_report.get('overall_verdict', 'unknown')
    blocking = validation_report.get('blocking_issues', [])
    warnings = validation_report.get('warnings', [])
    conditions = validation_report.get('approval_conditions', [])
    improvements = validation_report.get('revision_guidance', {}).get('recommended_improvements', [])
    
    # Build issues list
    issues = []
    
    for item in blocking:
        issue = build_issue_entry(item, 'BLOCKING', 'issue_id')
        issues.append(issue)
    
    for item in warnings:
        issue = build_issue_entry(item, 'WARNING', 'warning_id')
        issues.append(issue)
    
    for i, cond in enumerate(conditions):
        issue = {
            'id': f'COND-{i+1}',
            'type': 'CONDITION',
            'location': 'Approval Conditions',
            'description': cond if isinstance(cond, str) else str(cond),
            'recommendation': '',
            'options': generate_default_options(cond if isinstance(cond, str) else str(cond)),
            'decision': None,
        }
        issues.append(issue)
    
    if not issues:
        print("\n✅ No issues to address! Specification is clean.")
        return None
    
    # Create session
    from datetime import datetime
    import uuid
    
    session = {
        'session_id': str(uuid.uuid4())[:8],
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'updated_at': datetime.utcnow().isoformat() + 'Z',
        'spec_file': str(spec_path),
        'spec_version': specification.get('metadata', {}).get('version', '1.0'),
        'validation_file': str(validation_path),
        'validation_verdict': verdict,
        'mode': 'autonomous' if args.auto else 'interactive',
        'status': 'in_progress',
        'issues': issues,
        'summary': {
            'total_issues': len(issues),
            'resolved': 0,
            'deferred': 0,
            'pending_human': 0,
        },
        'apply_log': [],
    }
    
    print(f"\n  Session ID: {session['session_id']}")
    print(f"  Previous verdict: {verdict}")
    print(f"  Total issues: {len(issues)}")
    print(f"  Mode: {'Autonomous' if args.auto else 'Interactive'}")
    
    return session


def build_issue_entry(item: dict, issue_type: str, id_field: str) -> dict:
    """Build a structured issue entry with options."""
    issue_id = item.get(id_field, item.get('id', f'{issue_type[0]}?'))
    description = item.get('description', '')
    recommendation = item.get('recommendation', '')
    
    return {
        'id': issue_id,
        'type': issue_type,
        'location': item.get('location', 'Unknown'),
        'description': description,
        'recommendation': recommendation,
        'options': generate_options_from_recommendation(recommendation, description),
        'decision': None,
    }


def generate_options_from_recommendation(recommendation: str, description: str) -> list:
    """Generate structured options from a recommendation."""
    options = []
    
    if not recommendation:
        options.append({
            'id': '1',
            'label': 'Apply fix based on description',
            'resolution': f'Fix: {description[:100]}',
            'confidence': None,
            'rationale': 'Default fix option',
        })
    else:
        import re
        
        # Extract specific values (numbers with optional units)
        value_matches = re.findall(r'\b(\$?[\d,]+(?:\.\d+)?(?:ms|s|%)?)\b', recommendation)
        
        # Look for "e.g.," suggestions
        eg_matches = re.findall(r'e\.g\.,?\s*["\']?([^"\'.,]+)["\']?', recommendation, re.IGNORECASE)
        
        # Look for "Add X" or "Use X" patterns
        action_matches = re.findall(r'(?:Add|Use|Set|Change|Include)\s+([^.,]+)', recommendation, re.IGNORECASE)
        
        seen = set()
        
        # Create options from values (for bounds, limits, etc.)
        if value_matches and ('bound' in recommendation.lower() or 'limit' in recommendation.lower()):
            for val in value_matches[:3]:
                if val not in seen:
                    seen.add(val)
                    options.append({
                        'id': str(len(options) + 1),
                        'label': f'Set limit/bound to {val}',
                        'resolution': f'Add constraint: <= {val}',
                        'confidence': None,
                        'rationale': f'Value from recommendation',
                    })
        
        # Create options from action matches
        for action in action_matches[:2]:
            action = action.strip()
            if action and len(action) > 5 and action.lower() not in seen:
                seen.add(action.lower())
                options.append({
                    'id': str(len(options) + 1),
                    'label': action[:60] + ('...' if len(action) > 60 else ''),
                    'resolution': action,
                    'confidence': None,
                    'rationale': 'Action from recommendation',
                })
        
        # If still no options, use full recommendation
        if not options:
            options.append({
                'id': '1',
                'label': 'Apply recommendation as stated',
                'resolution': recommendation[:200],
                'confidence': None,
                'rationale': 'Direct from validation',
            })
    
    # Always add skip and custom options
    options.append({
        'id': 'skip',
        'label': 'Skip - defer to implementation kickoff',
        'resolution': 'Deferred to implementation',
        'confidence': None,
        'rationale': 'Defer decision',
    })
    
    options.append({
        'id': 'custom',
        'label': 'Custom resolution...',
        'resolution': None,
        'confidence': None,
        'rationale': 'User-provided resolution',
    })
    
    return options


def generate_default_options(description: str) -> list:
    """Generate default options for conditions without recommendations."""
    return [
        {
            'id': '1',
            'label': 'Address as stated',
            'resolution': description[:200],
            'confidence': None,
            'rationale': 'Direct resolution',
        },
        {
            'id': 'skip',
            'label': 'Skip - defer to implementation kickoff',
            'resolution': 'Deferred to implementation',
            'confidence': None,
            'rationale': 'Defer decision',
        },
        {
            'id': 'custom',
            'label': 'Custom resolution...',
            'resolution': None,
            'confidence': None,
            'rationale': 'User-provided resolution',
        },
    ]


def save_revision_session(session: dict):
    """Save revision session to YAML file."""
    from datetime import datetime
    session['updated_at'] = datetime.utcnow().isoformat() + 'Z'
    
    # Update summary
    resolved = sum(1 for i in session['issues'] if i.get('decision') and i['decision'].get('selected_option') not in [None, 'skip'])
    deferred = sum(1 for i in session['issues'] if i.get('decision') and i['decision'].get('selected_option') == 'skip')
    pending = sum(1 for i in session['issues'] if i.get('decision') and i['decision'].get('requires_human'))
    
    session['summary'] = {
        'total_issues': len(session['issues']),
        'resolved': resolved,
        'deferred': deferred,
        'pending_human': pending,
    }
    
    session_path = Path('outputs/revision_session.yaml')
    with open(session_path, 'w') as f:
        yaml.dump(session, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def run_interactive_revision(session: dict, args):
    """Interactive mode - human makes decisions."""
    print()
    print("-" * 60)
    print("INTERACTIVE MODE")
    print("-" * 60)
    print("You will decide how to resolve each issue.")
    print("Type 'q' at any prompt to save and quit.")
    print()
    
    issues = session['issues']
    
    for idx, issue in enumerate(issues):
        if issue.get('decision') and not issue['decision'].get('requires_human'):
            # Already decided
            continue
        
        print()
        print(f"Issue {idx + 1} of {len(issues)}: {issue['id']} [{issue['type']}]")
        print("━" * 60)
        print()
        print(f"Location: {issue['location']}")
        print()
        print("Problem:")
        for line in issue['description'].strip().split('\n'):
            print(f"  {line}")
        print()
        
        if issue.get('recommendation'):
            print("Recommendation:")
            for line in issue['recommendation'].strip().split('\n'):
                print(f"  {line}")
            print()
        
        # Show options
        options = issue['options']
        print("Options:")
        for opt in options:
            print(f"  [{opt['id']}] {opt['label']}")
        print()
        
        # Get user choice
        while True:
            try:
                choice = input("Your choice (or 'q' to save & quit): ").strip()
                
                if choice.lower() == 'q':
                    save_revision_session(session)
                    print(f"\n✅ Session saved. Resume with: python execute.py revise --continue")
                    return
                
                # Find matching option
                selected = next((o for o in options if o['id'] == choice), None)
                if selected:
                    break
                
                print(f"Invalid choice. Enter one of: {', '.join(o['id'] for o in options)}")
                
            except (EOFError, KeyboardInterrupt):
                save_revision_session(session)
                print(f"\n✅ Session saved. Resume with: python execute.py revise --continue")
                return
        
        # Handle custom option
        resolution = selected['resolution']
        if selected['id'] == 'custom':
            print()
            print("Enter your custom resolution (press Enter twice to finish):")
            custom_lines = []
            while True:
                try:
                    line = input()
                    if line == '' and custom_lines and custom_lines[-1] == '':
                        custom_lines.pop()
                        break
                    custom_lines.append(line)
                except EOFError:
                    break
            resolution = '\n'.join(custom_lines).strip()
        
        # Get rationale
        print()
        rationale = input("Brief rationale (optional, press Enter to skip): ").strip()
        
        # Record decision
        from datetime import datetime
        issue['decision'] = {
            'selected_option': selected['id'],
            'decided_by': 'human',
            'rationale': rationale or f"Selected: {selected['label']}",
            'custom_resolution': resolution if selected['id'] == 'custom' else None,
            'requires_human': False,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
        }
        
        print(f"\n  ✓ Recorded: {selected['label']}")
        save_revision_session(session)
    
    # All done
    session['status'] = 'ready_to_apply'
    save_revision_session(session)
    
    print_session_summary(session)
    print()
    print("All issues addressed! Apply with:")
    print("  python execute.py revise --apply")


def run_autonomous_revision(session: dict, args):
    """Autonomous mode - agent makes decisions."""
    print()
    print("-" * 60)
    print("AUTONOMOUS MODE")
    print("-" * 60)
    print("Agent will evaluate each issue and make decisions.")
    print("Uncertain decisions will be flagged for human review.")
    print()
    
    issues = session['issues']
    
    for idx, issue in enumerate(issues):
        if issue.get('decision'):
            continue
        
        print(f"\nEvaluating {idx + 1}/{len(issues)}: {issue['id']}...", end=' ', flush=True)
        
        decision = evaluate_issue_autonomously(issue, session, args.use_api)
        issue['decision'] = decision
        
        if decision.get('requires_human'):
            print(f"⚠️  FLAGGED FOR HUMAN")
            session['mode'] = 'paused_for_human'
        elif decision.get('selected_option') == 'skip':
            print(f"→ Deferred")
        else:
            print(f"✓ {decision.get('selected_option')}: {decision.get('rationale', '')[:40]}...")
        
        save_revision_session(session)
    
    # Check if any need human review
    pending_human = [i for i in issues if i.get('decision', {}).get('requires_human')]
    
    if pending_human:
        session['status'] = 'pending_human'
        session['mode'] = 'paused_for_human'
        save_revision_session(session)
        
        print()
        print("=" * 60)
        print("HUMAN REVIEW REQUIRED")
        print("=" * 60)
        print(f"\n{len(pending_human)} issue(s) flagged for human review:\n")
        
        for issue in pending_human:
            print(f"  • {issue['id']}: {issue['decision'].get('human_prompt', 'Needs review')[:60]}")
        
        print()
        print("Review and decide with:")
        print("  python execute.py revise --continue")
    else:
        session['status'] = 'ready_to_apply'
        save_revision_session(session)
        
        print_session_summary(session)
        print()
        print("All issues resolved autonomously! Apply with:")
        print("  python execute.py revise --apply")


def evaluate_issue_autonomously(issue: dict, session: dict, use_api: bool) -> dict:
    """Use agent to evaluate a single issue and make decision."""
    
    # Format options for prompt
    options_text = "\n".join([
        f"- id: \"{opt['id']}\"\n  label: \"{opt['label']}\"\n  resolution: \"{opt.get('resolution', 'custom')}\"" 
        for opt in issue['options']
    ])
    
    system = """You are an Autonomous Revision Agent evaluating specification issues.

# Decision Rules

Make autonomous decisions (requires_human: false) when:
- Clear technical fix (bounds, constraints, formatting)
- Obvious best option from context
- Standard validation issue

Flag for human (requires_human: true) when:
- Architectural decision
- Business logic ambiguity
- Trade-offs with no clear winner
- Requires domain expertise

# Output Format

Output ONLY valid YAML:
```yaml
selected_option: "option_id"
decided_by: agent
rationale: "Why this option (20+ chars)"
confidence: high|medium|low
requires_human: true|false
human_prompt: "If requires_human, explain why"
```"""

    user = f"""# Issue to Evaluate

ID: {issue['id']}
Type: {issue['type']}
Location: {issue['location']}

Problem:
{issue['description']}

Recommendation:
{issue.get('recommendation', 'None provided')}

# Available Options

{options_text}

# Task

Decide which option to select. Output YAML only."""

    try:
        if use_api:
            response = call_anthropic_api(system, user, max_tokens=300, temperature=0.0)
        else:
            response = call_claude_code(system, user)
        
        yaml_content = extract_yaml_from_response(response)
        decision = yaml.safe_load(yaml_content)
        
        if decision:
            from datetime import datetime
            decision['timestamp'] = datetime.utcnow().isoformat() + 'Z'
            decision['decided_by'] = 'agent'
            return decision
            
    except Exception as e:
        print(f"[Error: {e}]", end=' ')
    
    # Fallback - flag for human
    from datetime import datetime
    return {
        'selected_option': None,
        'decided_by': 'agent',
        'rationale': 'Failed to evaluate autonomously',
        'confidence': 'low',
        'requires_human': True,
        'human_prompt': 'Agent could not evaluate this issue. Please review.',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
    }


def continue_revision_session(args):
    """Continue a paused revision session."""
    print()
    print("=" * 60)
    print("REVISE - Continue Session")
    print("=" * 60)
    
    session_path = Path('outputs/revision_session.yaml')
    if not session_path.exists():
        print("\nNo revision session found. Start with:")
        print("  python execute.py revise")
        return
    
    with open(session_path) as f:
        session = yaml.safe_load(f)
    
    print(f"\n  Session ID: {session['session_id']}")
    print(f"  Status: {session['status']}")
    print_session_summary(session)
    
    # Find issues needing human input
    pending = [i for i in session['issues'] if 
               not i.get('decision') or 
               i['decision'].get('requires_human')]
    
    if not pending:
        session['status'] = 'ready_to_apply'
        save_revision_session(session)
        print("\nAll issues resolved! Apply with:")
        print("  python execute.py revise --apply")
        return
    
    print(f"\n{len(pending)} issue(s) need your input:\n")
    
    session['mode'] = 'interactive'
    
    for idx, issue in enumerate(pending):
        print()
        print(f"Issue {idx + 1} of {len(pending)}: {issue['id']} [{issue['type']}]")
        print("━" * 60)
        
        # Show agent's concern if flagged
        if issue.get('decision', {}).get('requires_human'):
            print()
            print("⚠️  Agent flagged this for human review:")
            print(f"   {issue['decision'].get('human_prompt', 'Needs review')}")
        
        print()
        print(f"Location: {issue['location']}")
        print()
        print("Problem:")
        for line in issue['description'].strip().split('\n'):
            print(f"  {line}")
        print()
        
        if issue.get('recommendation'):
            print("Recommendation:")
            for line in issue['recommendation'].strip().split('\n'):
                print(f"  {line}")
            print()
        
        # Show options
        options = issue['options']
        print("Options:")
        for opt in options:
            print(f"  [{opt['id']}] {opt['label']}")
        print()
        
        # Get user choice
        while True:
            try:
                choice = input("Your choice (or 'q' to save & quit): ").strip()
                
                if choice.lower() == 'q':
                    save_revision_session(session)
                    print(f"\n✅ Session saved. Resume with: python execute.py revise --continue")
                    return
                
                selected = next((o for o in options if o['id'] == choice), None)
                if selected:
                    break
                
                print(f"Invalid choice. Enter one of: {', '.join(o['id'] for o in options)}")
                
            except (EOFError, KeyboardInterrupt):
                save_revision_session(session)
                print(f"\n✅ Session saved. Resume with: python execute.py revise --continue")
                return
        
        # Handle custom
        resolution = selected['resolution']
        if selected['id'] == 'custom':
            print()
            print("Enter your custom resolution:")
            resolution = input().strip()
        
        # Get rationale
        print()
        rationale = input("Brief rationale (optional): ").strip()
        
        # Update decision
        from datetime import datetime
        issue['decision'] = {
            'selected_option': selected['id'],
            'decided_by': 'human',
            'rationale': rationale or f"Selected: {selected['label']}",
            'custom_resolution': resolution if selected['id'] == 'custom' else None,
            'requires_human': False,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
        }
        
        print(f"\n  ✓ Recorded: {selected['label']}")
        save_revision_session(session)
    
    session['status'] = 'ready_to_apply'
    save_revision_session(session)
    
    print_session_summary(session)
    print()
    print("All issues addressed! Apply with:")
    print("  python execute.py revise --apply")


def show_revision_status(args):
    """Show current revision session status."""
    print()
    print("=" * 60)
    print("REVISION SESSION STATUS")
    print("=" * 60)
    
    session_path = Path('outputs/revision_session.yaml')
    if not session_path.exists():
        print("\nNo active revision session.")
        print("Start with: python execute.py revise")
        return
    
    with open(session_path) as f:
        session = yaml.safe_load(f)
    
    print(f"\n  Session ID: {session['session_id']}")
    print(f"  Created: {session['created_at']}")
    print(f"  Updated: {session['updated_at']}")
    print(f"  Status: {session['status']}")
    print(f"  Mode: {session['mode']}")
    print(f"  Spec: {session['spec_file']} v{session['spec_version']}")
    print(f"  Verdict: {session['validation_verdict']}")
    
    print_session_summary(session)
    
    print("\n  Issues:")
    for issue in session['issues']:
        decision = issue.get('decision', {})
        if decision.get('requires_human'):
            status = "⚠️  NEEDS HUMAN"
        elif decision.get('selected_option') == 'skip':
            status = "→ Deferred"
        elif decision.get('selected_option'):
            status = f"✓ {decision['selected_option']} ({decision.get('decided_by', '?')})"
        else:
            status = "○ Pending"
        
        print(f"    {issue['id']} [{issue['type']}]: {status}")
    
    print()
    print("Commands:")
    if session['status'] == 'pending_human':
        print("  python execute.py revise --continue  # Resolve flagged issues")
    elif session['status'] == 'ready_to_apply':
        print("  python execute.py revise --apply     # Apply to specification")
    elif session['status'] == 'in_progress':
        print("  python execute.py revise --continue  # Continue session")
    print("  python execute.py revise --force      # Start fresh session")


def print_session_summary(session: dict):
    """Print session summary."""
    summary = session.get('summary', {})
    print()
    print(f"  Summary:")
    print(f"    Total: {summary.get('total_issues', '?')}")
    print(f"    Resolved: {summary.get('resolved', 0)}")
    print(f"    Deferred: {summary.get('deferred', 0)}")
    print(f"    Pending human: {summary.get('pending_human', 0)}")


def apply_revision_session(args):
    """Apply all decisions from revision session to specification."""
    print()
    print("=" * 60)
    print("REVISE - Apply Decisions")
    print("=" * 60)
    
    session_path = Path('outputs/revision_session.yaml')
    if not session_path.exists():
        print("\nNo revision session found. Start with:")
        print("  python execute.py revise")
        return
    
    with open(session_path) as f:
        session = yaml.safe_load(f)
    
    # Check status
    if session['status'] not in ['ready_to_apply', 'in_progress']:
        if session['status'] == 'pending_human':
            print("\n⚠️  Some issues need human review first.")
            print("Run: python execute.py revise --continue")
            return
        elif session['status'] == 'applied':
            print("\n✅ Session already applied.")
            return
    
    # Check for unresolved issues
    unresolved = [i for i in session['issues'] if not i.get('decision') or i['decision'].get('requires_human')]
    if unresolved:
        print(f"\n⚠️  {len(unresolved)} issue(s) still need decisions.")
        print("Run: python execute.py revise --continue")
        return
    
    print_session_summary(session)
    
    # Build revision instructions from decisions
    to_apply = []
    to_defer = []
    
    for issue in session['issues']:
        decision = issue['decision']
        if decision['selected_option'] == 'skip':
            to_defer.append({
                'issue_id': issue['id'],
                'reason': decision.get('rationale', 'Deferred'),
            })
        else:
            resolution = decision.get('custom_resolution') or next(
                (o['resolution'] for o in issue['options'] if o['id'] == decision['selected_option']),
                decision.get('rationale', '')
            )
            to_apply.append({
                'issue_id': issue['id'],
                'location': issue['location'],
                'resolution': resolution,
                'decided_by': decision['decided_by'],
                'rationale': decision.get('rationale', ''),
            })
    
    print(f"\n  Will apply {len(to_apply)} change(s), defer {len(to_defer)}.")
    
    if not to_apply:
        print("\n✅ No changes to apply (all deferred).")
        session['status'] = 'applied'
        save_revision_session(session)
        return
    
    # Confirm
    print()
    confirm = input("Apply these changes to specification? (y/n): ").strip().lower()
    if confirm != 'y':
        print("\nAborted. Session preserved.")
        return
    
    # Load specification
    spec_path = Path(session['spec_file'])
    with open(spec_path) as f:
        specification = yaml.safe_load(f)
    
    # Build instructions for Claude
    revision_text = build_apply_instructions(to_apply, to_defer)
    
    print()
    print("-" * 60)
    print("APPLYING CHANGES")
    print("-" * 60)
    print("  Mode:", "Claude Code CLI (subscription)" if not args.use_api else "Anthropic API")
    
    result = execute_apply_revision(
        yaml.dump(specification, default_flow_style=False, sort_keys=False),
        revision_text,
        args.use_api
    )
    
    if isinstance(result, dict) and '_raw' not in result:
        # Success - backup and save
        import shutil
        backup_path = spec_path.with_suffix('.yaml.bak')
        shutil.copy(spec_path, backup_path)
        print(f"\n  Backed up: {backup_path}")
        
        # Add revision notes
        result['_revision_notes'] = {
            'revision_version': increment_version(session['spec_version']),
            'session_id': session['session_id'],
            'previous_verdict': session['validation_verdict'],
            'issues_addressed': [
                {'id': r['issue_id'], 'action': r['resolution'][:50], 'decided_by': r['decided_by']}
                for r in to_apply
            ],
            'issues_deferred': [
                {'id': d['issue_id'], 'reason': d['reason']}
                for d in to_defer
            ],
        }
        
        with open(spec_path, 'w') as f:
            yaml.dump(result, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
        # Update session
        from datetime import datetime
        session['status'] = 'applied'
        session['apply_log'].append({
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'action': 'applied',
            'changes': len(to_apply),
            'deferred': len(to_defer),
        })
        save_revision_session(session)
        
        print(f"\n✅ Specification updated: {spec_path}")
        print()
        print("-" * 60)
        print("NEXT STEPS")
        print("-" * 60)
        print("  1. Review changes:")
        print(f"     diff {backup_path} {spec_path}")
        print("  2. Re-validate:")
        print("     python execute.py validate")
        
    else:
        print("\n❌ Failed to apply changes.")
        print("   Session preserved. Try again or apply manually.")


def build_apply_instructions(to_apply: list, to_defer: list) -> str:
    """Build instructions for applying revisions."""
    lines = [
        "# Revision Instructions",
        "",
        "Apply these specific changes to the specification:",
        "",
    ]
    
    for r in to_apply:
        lines.append(f"## {r['issue_id']} at {r['location']}")
        lines.append(f"Resolution: {r['resolution']}")
        lines.append(f"Rationale: {r['rationale']}")
        lines.append("")
    
    if to_defer:
        lines.append("## Deferred (no changes):")
        for d in to_defer:
            lines.append(f"- {d['issue_id']}: {d['reason']}")
        lines.append("")
    
    lines.extend([
        "# Rules",
        "- Apply ONLY the changes listed",
        "- Preserve all other content",
        "- Use literal blocks (|) for multiline",
        "- Output complete YAML starting with 'metadata:'",
    ])
    
    return '\n'.join(lines)


def execute_apply_revision(spec_yaml: str, instructions: str, use_api: bool) -> dict:
    """Execute the revision application."""
    system = """Apply the requested changes to the specification.
Output the complete revised specification as valid YAML.
Start with "metadata:" - no preamble or explanation."""

    user = f"""# Current Specification

```yaml
{spec_yaml}
```

{instructions}

Output the complete revised YAML specification:"""

    if use_api:
        response = call_anthropic_api(system, user, max_tokens=12000, temperature=0.0)
    else:
        response = call_claude_code(system, user)
    
    yaml_content = extract_yaml_from_response(response)
    
    try:
        return yaml.safe_load(yaml_content)
    except yaml.YAMLError:
        return {"_raw": response}


def increment_version(version: str) -> str:
    """Increment patch version."""
    parts = version.split('.')
    if len(parts) >= 2:
        parts[-1] = str(int(parts[-1]) + 1)
    return '.'.join(parts)


def run_context(args):
    """
    Test context retrieval system.

    Retrieves relevant code context using LSP and/or vector search.
    Useful for testing and debugging context retrieval before running analyze.
    """
    print()
    print("=" * 60)
    print("CONTEXT RETRIEVAL")
    print("=" * 60)

    sys.path.insert(0, str(Path(__file__).parent / 'tools'))

    try:
        from context_retrieval import ContextRetriever
    except ImportError as e:
        print(f"\nError: Could not import context_retrieval: {e}")
        sys.exit(1)

    print(f"\n  Project: {args.project}")

    provider = getattr(args, 'provider', None)
    retriever = ContextRetriever(args.project, provider=provider)

    try:
        # Check dependencies if requested
        if args.check:
            print("\nChecking components...")
            status = retriever.check_dependencies()

            print("\n  LSP (Language Server Protocol):")
            lsp = status["lsp"]
            if lsp["available"]:
                print(f"    Status: Available")
                print(f"    Server: {lsp.get('server', 'unknown')}")
            else:
                print(f"    Status: Not available")
                if lsp.get("error"):
                    print(f"    Error: {lsp['error']}")
                if lsp.get("install_instructions"):
                    print(f"    Install: {lsp['install_instructions']}")

            print("\n  Embedding Providers:")
            try:
                from embedding_providers import list_providers, get_available_providers
                providers = list_providers()
                available = get_available_providers()
                current = available[0] if available else None

                for p in providers:
                    mark = "✓" if p["available"] else "✗"
                    default = " (current)" if p["name"] == current else ""
                    api_note = "" if not p["requires_api_key"] else " (needs API key)"
                    print(f"    {mark} {p['name']}{api_note}{default}")
                    if not p["available"] and p["install_instructions"]:
                        print(f"      Install: {p['install_instructions']}")
            except ImportError:
                print("    Could not load embedding providers")

            print("\n  Vector Search:")
            vec = status["vector"]
            if vec["available"]:
                print(f"    Status: Available")
                print(f"    Indexed: {'Yes' if vec.get('indexed') else 'No'}")
            else:
                print(f"    Status: Not available")
                if vec.get("error"):
                    print(f"    Error: {vec['error']}")
                print("    Install: pip install sentence-transformers faiss-cpu")
            return

        # Build index if requested
        if args.index:
            print("\nBuilding vector index...")
            stats = retriever.index(force_rebuild=args.force)
            print(f"  Files indexed: {stats.file_count}")
            print(f"  Chunks created: {stats.chunk_count}")
            print(f"  Duration: {stats.duration_ms}ms")
            if stats.errors:
                print(f"  Errors: {len(stats.errors)}")

        # Search if query provided
        if args.query:
            print(f"\n  Query: {args.query}")
            print(f"  Budget: {args.budget} tokens")
            print()
            print("-" * 60)
            print("Searching...")
            print("-" * 60)

            context = retriever.retrieve(
                args.query,
                budget_tokens=args.budget,
                use_lsp=not args.no_lsp,
                use_vector=not args.no_vector,
            )

            print(f"\n  Found {len(context.files)} files")
            print(f"  Found {len(context.symbols)} symbols")
            print(f"  Total tokens: {context.total_tokens}")
            print()
            print("-" * 60)
            print("RESULTS")
            print("-" * 60)

            if args.format == 'yaml':
                print(context.to_yaml())
            elif args.format == 'json':
                import json
                print(json.dumps(context.to_dict(), indent=2))
            else:
                print(context.to_prompt_text())

            # Save output
            output_dir = Path('outputs')
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / 'context_retrieval.yaml'

            with open(output_path, 'w') as f:
                f.write(context.to_yaml())

            print(f"\nSaved to: {output_path}")

        elif not args.check and not args.index:
            print("\nNo action specified. Use --query, --check, or --index")
            print("  python execute.py context -p /path/to/project --check")
            print("  python execute.py context -p /path/to/project --index")
            print("  python execute.py context -p /path/to/project -q 'order processing'")

    finally:
        retriever.shutdown()


def run_verify(args):
    """
    Run deterministic verification checks.

    Replaces LLM-based validation with actual verification:
    - Does the code compile? (dotnet build)
    - Do tests pass? (dotnet test)
    - Do architecture rules hold? (regex/import checks)

    This is the core "Correctness is Upstream" philosophy in action.
    """
    print()
    print("=" * 60)
    print("VERIFY - Deterministic Correctness Checks")
    print("=" * 60)

    # Import verification runner
    try:
        sys.path.insert(0, str(Path(__file__).parent / 'tools'))
        from verification_runner import VerificationRunner, CheckStatus
    except ImportError as e:
        print(f"\nError: Could not import verification_runner: {e}")
        print("Ensure tools/verification_runner.py exists.")
        sys.exit(1)

    # Set up runner
    project_root = Path(args.project_root) if args.project_root else Path.cwd()
    config_path = Path(args.config) if args.config else None

    runner = VerificationRunner(
        config_path=config_path,
        project_root=project_root
    )

    # Set context variables
    context = {
        'project_root': str(project_root),
    }

    if args.project:
        context['project_path'] = args.project

    runner.set_context(**context)

    print(f"\n  Project Root: {project_root}")
    if args.project:
        print(f"  Project File: {args.project}")
    print(f"  Config: {runner.config_path}")

    # Determine what to run
    if args.profile:
        print(f"  Profile: {args.profile}")
        print()
        print("-" * 60)
        print(f"Running '{args.profile}' profile...")
        print("-" * 60)

        try:
            report = runner.run_profile(args.profile)
        except ValueError as e:
            print(f"\nError: {e}")
            available = list(runner.config.get('profiles', {}).keys())
            print(f"Available profiles: {', '.join(available)}")
            sys.exit(1)

    elif args.checks:
        check_ids = [c.strip() for c in args.checks.split(',')]
        print(f"  Checks: {', '.join(check_ids)}")
        print()
        print("-" * 60)
        print(f"Running {len(check_ids)} check(s)...")
        print("-" * 60)

        report = runner.run_checks(check_ids=check_ids)
    else:
        # Default to quick profile if available, else all checks
        profiles = runner.config.get('profiles', {})
        if 'quick' in profiles:
            print("  Profile: quick (default)")
            print()
            print("-" * 60)
            print("Running 'quick' profile...")
            print("-" * 60)
            report = runner.run_profile('quick')
        else:
            print("  Running: all checks")
            print()
            print("-" * 60)
            print("Running all checks...")
            print("-" * 60)
            report = runner.run_checks(all_checks=True)

    # Print results
    output = runner.generate_report(report, format='text')
    print(output)

    # Save report
    output_dir = Path('outputs')
    output_dir.mkdir(exist_ok=True)

    if args.format == 'yaml':
        report_content = runner.generate_report(report, format='yaml')
        report_path = output_dir / 'verification_report.yaml'
    elif args.format == 'json':
        report_content = runner.generate_report(report, format='json')
        report_path = output_dir / 'verification_report.json'
    else:
        report_content = runner.generate_report(report, format='yaml')
        report_path = output_dir / 'verification_report.yaml'

    with open(report_path, 'w') as f:
        f.write(report_content)

    print(f"\nReport saved to: {report_path}")

    # Summary and next steps
    print()
    print("-" * 60)
    if report.is_valid:
        print("RESULT: PASS")
        print("-" * 60)
        print("\nAll blocking checks passed!")

        if report.required_failures > 0:
            print(f"\nNote: {report.required_failures} required check(s) failed (non-blocking).")
            print("Consider addressing these before proceeding.")

        if report.advisory_warnings > 0:
            print(f"\nAdvisory: {report.advisory_warnings} warning(s) - review recommended.")

    else:
        print("RESULT: FAIL")
        print("-" * 60)
        print(f"\n{report.blocking_failures} blocking check(s) failed!")
        print("\nBlocking failures must be fixed before proceeding:")

        for result in report.results:
            if result.is_blocking_failure:
                print(f"\n  {result.check_id}: {result.check_name}")
                print(f"    {result.message}")
                if result.fix_suggestion:
                    print(f"    Fix: {result.fix_suggestion}")
                if result.errors:
                    for err in result.errors[:3]:
                        if isinstance(err, dict):
                            file_info = err.get('file', '')
                            line_info = err.get('line', '')
                            msg = err.get('message', err.get('match', ''))
                            if file_info:
                                print(f"      - {file_info}:{line_info}: {msg[:60]}")
                            else:
                                print(f"      - {msg[:80]}")

        print()
        print("Fix the issues and re-run:")
        print("  python execute.py verify")

    # Exit code
    if not report.is_valid:
        sys.exit(1)
    elif args.strict and (report.required_failures > 0 or report.advisory_warnings > 0):
        print("\n--strict mode: Failing due to non-blocking issues.")
        sys.exit(1)


# =============================================================================
# WORKSPACE COMMANDS
# =============================================================================

def run_workspace(args):
    """
    Workspace management commands.

    Workspaces provide multi-repository context for code intelligence and
    verification. They define relationships between repos that form a logical
    product or system.
    """
    # Subcommand dispatch is handled by subparsers
    pass


def run_workspace_init(args):
    """Initialize a new workspace or single-repo config."""
    print()
    print("=" * 60)
    if getattr(args, 'single_repo', False):
        print("WORKSPACE INIT (Single-Repo Mode)")
    else:
        print("WORKSPACE INIT")
    print("=" * 60)

    sys.path.insert(0, str(Path(__file__).parent / 'tools'))

    try:
        from workspace import init_workspace, init_single_repo
    except ImportError as e:
        print(f"\nError: Could not import workspace module: {e}")
        sys.exit(1)

    if getattr(args, 'single_repo', False):
        # Single-repo mode - no workspace, just repo config
        if not getattr(args, 'language', None):
            print("\n❌ Error: --language is required for --single-repo mode")
            sys.exit(1)

        repo_dir = Path(args.path) if args.path else Path.cwd()

        print(f"\n  Location: {repo_dir}")
        print(f"  Name: {args.name}")
        print(f"  Language: {args.language}")
        print(f"  Type: {getattr(args, 'type', 'service') or 'service'}")

        try:
            result = init_single_repo(
                repo_dir,
                name=args.name,
                language=args.language,
                repo_type=getattr(args, 'type', 'service') or 'service',
                force=args.force,
            )

            print(f"\n✅ Single-repo config initialized: {result}")
            print()
            print("Created:")
            print(f"  .agentforge/")
            print(f"  ├── repo.yaml")
            print(f"  ├── contracts/")
            print(f"  └── specs/")
            print()
            print("Next steps:")
            print("  1. Add contracts to .agentforge/contracts/")
            print("  2. Run verification: python execute.py verify")

        except Exception as e:
            print(f"\n❌ Failed to initialize: {e}")
            sys.exit(1)
    else:
        # Full workspace mode
        workspace_dir = Path(args.path) if args.path else Path.cwd()

        print(f"\n  Location: {workspace_dir}")
        print(f"  Name: {args.name}")

        if args.description:
            print(f"  Description: {args.description}")

        try:
            result = init_workspace(
                workspace_dir,
                name=args.name,
                description=args.description,
                force=args.force,
            )

            print(f"\n✅ Workspace initialized: {result}")
            print()
            print("Next steps:")
            print("  1. Add repositories:")
            print(f"     python execute.py workspace add-repo --name api --path ../my-api --type service --lang csharp")
            print("  2. Validate workspace:")
            print("     python execute.py workspace validate")

        except Exception as e:
            print(f"\n❌ Failed to initialize workspace: {e}")
            sys.exit(1)


def run_workspace_status(args):
    """Show workspace status and configuration."""
    print()
    print("=" * 60)
    print("WORKSPACE STATUS")
    print("=" * 60)

    sys.path.insert(0, str(Path(__file__).parent / 'tools'))

    try:
        from workspace import discover_workspace, format_workspace_status
    except ImportError as e:
        print(f"\nError: Could not import workspace module: {e}")
        sys.exit(1)

    # Discover workspace
    workspace_arg = args.workspace if args.workspace else None
    ctx = discover_workspace(workspace_arg=workspace_arg)

    if not ctx.is_workspace_mode:
        print("\n❌ No workspace found.")
        print()
        print("Discovery searched:")
        print("  1. --workspace flag")
        print("  2. AGENTFORGE_WORKSPACE env var")
        print("  3. repo.yaml in current directory")
        print("  4. workspace.yaml in current directory")
        print("  5. agentforge/workspace.yaml subdirectory")
        print()
        print("Initialize with:")
        print("  python execute.py workspace init --name my-workspace")
        sys.exit(1)

    print(f"\n  Workspace: {ctx.workspace_name}")
    print(f"  Root: {ctx.workspace_dir}")
    print(f"  Config: {ctx.workspace_path}")

    if ctx.workspace_description:
        print(f"  Description: {ctx.workspace_description}")

    if ctx.workspace_version:
        print(f"  Version: {ctx.workspace_version}")

    print()
    print("-" * 60)
    print(f"REPOSITORIES ({len(ctx.repos)})")
    print("-" * 60)

    for repo in ctx.repos.values():
        # Check if repo path exists
        status = "✓" if repo.is_available else "✗ NOT FOUND"

        print(f"\n  {repo.name} [{status}]")
        print(f"    Path: {repo.path}")
        print(f"    Type: {repo.type}")
        print(f"    Language: {repo.language}")

        if repo.framework:
            print(f"    Framework: {repo.framework}")
        if repo.lsp:
            print(f"    LSP: {repo.lsp}")
        if repo.layers:
            print(f"    Layers: {', '.join(repo.layers)}")
        if repo.tags:
            print(f"    Tags: {', '.join(repo.tags)}")

    # Show paths if configured
    paths = ctx.workspace_config.get('paths', {})
    if paths:
        print()
        print("-" * 60)
        print("PATHS")
        print("-" * 60)
        for key, path in paths.items():
            full_path = ctx.workspace_dir / path
            exists = full_path.exists()
            status = "✓" if exists else "✗"
            print(f"  {key}: {path} [{status}]")

    # Show defaults if configured
    defaults = ctx.workspace_config.get('defaults', {})
    if defaults:
        print()
        print("-" * 60)
        print("DEFAULTS")
        print("-" * 60)

        context_defaults = defaults.get('context', {})
        if context_defaults:
            print("  Context:")
            print(f"    Budget tokens: {context_defaults.get('budget_tokens', 6000)}")
            provider = context_defaults.get('embedding_provider')
            print(f"    Embedding provider: {provider or 'auto'}")

        verify_defaults = defaults.get('verification', {})
        if verify_defaults:
            print("  Verification:")
            print(f"    Fail fast: {verify_defaults.get('fail_fast', True)}")
            print(f"    Profiles: {', '.join(verify_defaults.get('profiles', ['quick']))}")


def run_workspace_add_repo(args):
    """Add a repository to the workspace."""
    print()
    print("=" * 60)
    print("WORKSPACE ADD-REPO")
    print("=" * 60)

    sys.path.insert(0, str(Path(__file__).parent / 'tools'))

    try:
        from workspace import discover_workspace, add_repo_to_workspace
    except ImportError as e:
        print(f"\nError: Could not import workspace module: {e}")
        sys.exit(1)

    # Discover workspace
    workspace_arg = args.workspace if args.workspace else None
    ctx = discover_workspace(workspace_arg=workspace_arg)

    if not ctx.is_workspace_mode:
        print("\n❌ No workspace found. Initialize first:")
        print("  python execute.py workspace init --name my-workspace")
        sys.exit(1)

    print(f"\n  Workspace: {ctx.workspace_name}")
    print(f"  Adding repo: {args.name}")
    print(f"    Path: {args.path}")
    print(f"    Type: {args.type}")
    print(f"    Language: {args.language}")

    layers = args.layers.split(',') if args.layers else None
    tags = args.tags.split(',') if args.tags else None

    if args.framework:
        print(f"    Framework: {args.framework}")
    if args.lsp:
        print(f"    LSP: {args.lsp}")
    if layers:
        print(f"    Layers: {', '.join(layers)}")
    if tags:
        print(f"    Tags: {', '.join(tags)}")

    try:
        result = add_repo_to_workspace(
            ctx,
            name=args.name,
            path=args.path,
            repo_type=args.type,
            language=args.language,
            framework=args.framework,
            lsp=args.lsp,
            layers=layers,
            tags=tags,
        )
        print(f"\n✅ Repository added: {args.name}")
        print(f"   Updated: {ctx.workspace_path}")
    except Exception as e:
        print(f"\n❌ Failed to add repository: {e}")
        sys.exit(1)


def run_workspace_remove_repo(args):
    """Remove a repository from the workspace."""
    print()
    print("=" * 60)
    print("WORKSPACE REMOVE-REPO")
    print("=" * 60)

    sys.path.insert(0, str(Path(__file__).parent / 'tools'))

    try:
        from workspace import discover_workspace, remove_repo_from_workspace
    except ImportError as e:
        print(f"\nError: Could not import workspace module: {e}")
        sys.exit(1)

    # Discover workspace
    workspace_arg = args.workspace if args.workspace else None
    ctx = discover_workspace(workspace_arg=workspace_arg)

    if not ctx.is_workspace_mode:
        print("\n❌ No workspace found.")
        sys.exit(1)

    print(f"\n  Workspace: {ctx.workspace_name}")
    print(f"  Removing repo: {args.name}")

    # Check if repo exists
    if args.name not in ctx.repos:
        print(f"\n❌ Repository '{args.name}' not found in workspace.")
        print("Available repos:", ', '.join(ctx.repos.keys()))
        sys.exit(1)

    # Remove repo
    removed = remove_repo_from_workspace(ctx, args.name)
    if removed:
        print(f"\n✅ Repository removed: {args.name}")
    else:
        print(f"\n❌ Failed to remove repository: {args.name}")


def run_workspace_link(args):
    """Link a repository to a workspace."""
    print()
    print("=" * 60)
    print("WORKSPACE LINK")
    print("=" * 60)

    sys.path.insert(0, str(Path(__file__).parent / 'tools'))

    try:
        from workspace import create_repo_link
    except ImportError as e:
        print(f"\nError: Could not import workspace module: {e}")
        sys.exit(1)

    repo_dir = Path(args.repo).resolve() if args.repo else Path.cwd().resolve()
    workspace_path = Path(args.workspace).resolve()

    if not workspace_path.exists():
        print(f"\n❌ Workspace not found: {workspace_path}")
        sys.exit(1)

    print(f"\n  Repository: {repo_dir}")
    print(f"  Linking to: {workspace_path}")

    # Use workspace.py function to create the link
    try:
        repo_name = repo_dir.name.lower().replace('_', '-').replace(' ', '-')
        repo_yaml_path = create_repo_link(repo_dir, workspace_path, repo_name)

        print(f"\n✅ Linked repository to workspace")
        print(f"   Created: {repo_yaml_path}")
    except Exception as e:
        print(f"\n❌ Failed to link repository: {e}")
        sys.exit(1)


def run_workspace_validate(args):
    """Validate workspace configuration."""
    print()
    print("=" * 60)
    print("WORKSPACE VALIDATE")
    print("=" * 60)

    sys.path.insert(0, str(Path(__file__).parent / 'tools'))

    try:
        from workspace import discover_workspace, validate_workspace
    except ImportError as e:
        print(f"\nError: Could not import workspace module: {e}")
        sys.exit(1)

    # Discover workspace
    workspace_arg = args.workspace if args.workspace else None
    ctx = discover_workspace(workspace_arg=workspace_arg)

    if not ctx.is_workspace_mode:
        print("\n❌ No workspace found.")
        sys.exit(1)

    print(f"\n  Workspace: {ctx.workspace_name}")
    print(f"  Config: {ctx.workspace_path}")
    print()
    print("-" * 60)
    print("VALIDATION")
    print("-" * 60)

    errors, warnings = validate_workspace(ctx)

    if not errors:
        print("\n✅ Workspace configuration is valid!")
    else:
        print("\n❌ Workspace has configuration errors:")
        for error in errors:
            print(f"   • {error}")

    if warnings:
        print("\n⚠️  Warnings:")
        for warning in warnings:
            print(f"   • {warning}")

    if errors:
        sys.exit(1)


def run_workspace_list_repos(args):
    """List repositories in workspace."""
    print()
    print("=" * 60)
    print("WORKSPACE LIST-REPOS")
    print("=" * 60)

    sys.path.insert(0, str(Path(__file__).parent / 'tools'))

    try:
        from workspace import discover_workspace
    except ImportError as e:
        print(f"\nError: Could not import workspace module: {e}")
        sys.exit(1)

    # Discover workspace
    workspace_arg = args.workspace if args.workspace else None
    ctx = discover_workspace(workspace_arg=workspace_arg)

    if not ctx.is_workspace_mode:
        print("\n❌ No workspace found.")
        sys.exit(1)

    print(f"\n  Workspace: {ctx.workspace_name}")
    print()

    # Filter repos - ctx.repos is a dict, so convert to list of values
    repos = list(ctx.repos.values())

    if args.type:
        repos = [r for r in repos if r.type == args.type]

    if args.language:
        repos = [r for r in repos if r.language == args.language]

    if args.tag:
        repos = [r for r in repos if args.tag in (r.tags or [])]

    if args.format == 'json':
        import json
        output = [
            {
                'name': r.name,
                'path': r.path,
                'type': r.type,
                'language': r.language,
                'framework': r.framework,
                'tags': r.tags,
            }
            for r in repos
        ]
        print(json.dumps(output, indent=2))
    elif args.format == 'yaml':
        output = [
            {
                'name': r.name,
                'path': r.path,
                'type': r.type,
                'language': r.language,
                'framework': r.framework,
                'tags': r.tags,
            }
            for r in repos
        ]
        print(yaml.dump(output, default_flow_style=False))
    else:
        # Table format
        print(f"{'NAME':<20} {'TYPE':<12} {'LANGUAGE':<12} {'PATH'}")
        print("-" * 70)
        for repo in repos:
            print(f"{repo.name:<20} {repo.type:<12} {repo.language:<12} {repo.path}")

    print()
    print(f"Total: {len(repos)} repository(ies)")


def run_workspace_unlink(args):
    """Unlink current repo from workspace (convert to single-repo mode)."""
    print()
    print("=" * 60)
    print("WORKSPACE UNLINK")
    print("=" * 60)

    sys.path.insert(0, str(Path(__file__).parent / 'tools'))

    try:
        from workspace import unlink_repo
    except ImportError as e:
        print(f"\nError: Could not import workspace module: {e}")
        sys.exit(1)

    repo_dir = Path.cwd()
    print(f"\n  Repository: {repo_dir}")

    try:
        unlinked = unlink_repo(repo_dir)
        if unlinked:
            print("\n✅ Repository unlinked from workspace")
            print("   Now in single-repo mode (workspace_ref: null)")
        else:
            print("\n⚠️  Repository is already in single-repo mode")
    except Exception as e:
        print(f"\n❌ Failed to unlink: {e}")
        sys.exit(1)


# =============================================================================
# CONFIG COMMANDS
# =============================================================================

def run_config(args):
    """Configuration management commands."""
    # Subcommand dispatch is handled by subparsers
    pass


def run_config_init_global(args):
    """Initialize global config at ~/.agentforge/"""
    print()
    print("=" * 60)
    print("CONFIG INIT-GLOBAL")
    print("=" * 60)

    sys.path.insert(0, str(Path(__file__).parent / 'tools'))

    try:
        from workspace import init_global_config
    except ImportError as e:
        print(f"\nError: Could not import workspace module: {e}")
        sys.exit(1)

    print(f"\n  Location: ~/.agentforge/")

    try:
        result = init_global_config(force=getattr(args, 'force', False))

        print(f"\n✅ Global config initialized: {result}")
        print()
        print("Created:")
        print("  ~/.agentforge/")
        print("  ├── config.yaml")
        print("  ├── contracts/")
        print("  └── workspaces/")
        print()
        print("Edit config.yaml to set your default preferences.")

    except Exception as e:
        print(f"\n❌ Failed to initialize: {e}")
        sys.exit(1)


def run_config_show(args):
    """Show configuration at specified tier or effective."""
    print()
    print("=" * 60)
    print("CONFIG SHOW")
    print("=" * 60)

    sys.path.insert(0, str(Path(__file__).parent / 'tools'))

    try:
        from workspace import discover_config, format_config_status
    except ImportError as e:
        print(f"\nError: Could not import workspace module: {e}")
        sys.exit(1)

    ctx = discover_config()

    tier = getattr(args, 'tier', None)

    if tier == 'global':
        print("\nGlobal Configuration (~/.agentforge/config.yaml):")
        print("-" * 50)
        if ctx.global_config:
            print(yaml.dump(ctx.global_config, default_flow_style=False))
        else:
            print("Not configured. Run: python execute.py config init-global")
    elif tier == 'workspace':
        print("\nWorkspace Configuration:")
        print("-" * 50)
        if ctx.workspace_config:
            defaults = ctx.workspace_config.get('defaults', {})
            if defaults:
                print(yaml.dump(defaults, default_flow_style=False))
            else:
                print("No defaults configured in workspace")
        else:
            print("No workspace found")
    elif tier == 'repo':
        print("\nRepository Configuration:")
        print("-" * 50)
        if ctx.repo_config:
            overrides = ctx.repo_config.get('overrides', {})
            if overrides:
                print(yaml.dump(overrides, default_flow_style=False))
            else:
                print("No overrides configured in repo")
        else:
            print("No repo config found")
    else:
        # Show full status
        print(format_config_status(ctx))


def run_config_set(args):
    """Set a configuration value."""
    print()
    print("=" * 60)
    print("CONFIG SET")
    print("=" * 60)

    sys.path.insert(0, str(Path(__file__).parent / 'tools'))

    try:
        from workspace import load_yaml_file
    except ImportError as e:
        print(f"\nError: Could not import workspace module: {e}")
        sys.exit(1)

    key = args.key
    value = args.value

    # Determine which config file to update
    if getattr(args, 'set_global', False):
        config_path = Path.home() / '.agentforge' / 'config.yaml'
        tier = 'global'
    elif getattr(args, 'set_workspace', False):
        # Find workspace.yaml
        from workspace import find_upward
        ws_yaml = find_upward('workspace.yaml') or find_upward('agentforge/workspace.yaml')
        if not ws_yaml:
            print("\n❌ No workspace found")
            sys.exit(1)
        config_path = ws_yaml
        tier = 'workspace'
    else:
        # Default to repo
        config_path = Path.cwd() / '.agentforge' / 'repo.yaml'
        tier = 'repo'

    if not config_path.exists():
        print(f"\n❌ Config file not found: {config_path}")
        sys.exit(1)

    print(f"\n  Tier: {tier}")
    print(f"  File: {config_path}")
    print(f"  Key: {key}")
    print(f"  Value: {value}")

    # Load config
    with open(config_path) as f:
        config = yaml.safe_load(f) or {}

    # Parse value (try to convert to appropriate type)
    try:
        if value.lower() == 'true':
            parsed_value = True
        elif value.lower() == 'false':
            parsed_value = False
        elif value.lower() == 'null' or value.lower() == 'none':
            parsed_value = None
        elif value.isdigit():
            parsed_value = int(value)
        else:
            try:
                parsed_value = float(value)
            except ValueError:
                parsed_value = value
    except AttributeError:
        parsed_value = value

    # Navigate to key (dot notation)
    keys = key.split('.')
    target = config

    # For repo.yaml, settings go under 'overrides'
    if tier == 'repo' and keys[0] != 'overrides':
        if 'overrides' not in config:
            config['overrides'] = {}
        target = config['overrides']
    elif tier == 'workspace' and keys[0] != 'defaults':
        if 'defaults' not in config:
            config['defaults'] = {}
        target = config['defaults']
    elif tier == 'global' and keys[0] != 'defaults':
        if 'defaults' not in config:
            config['defaults'] = {}
        target = config['defaults']

    # Navigate/create nested structure
    for k in keys[:-1]:
        if k not in target:
            target[k] = {}
        target = target[k]

    # Set value
    target[keys[-1]] = parsed_value

    # Write back
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print(f"\n✅ Configuration updated")


# ==============================================================================
# CONTRACT HANDLERS
# ==============================================================================

def run_contracts(args):
    """Fallback for contracts without subcommand."""
    pass  # Handled in main()


def run_contracts_list(args):
    """List all contracts."""
    print()
    print("=" * 60)
    print("CONTRACTS LIST")
    print("=" * 60)

    sys.path.insert(0, str(Path(__file__).parent / 'tools'))

    try:
        from contracts import ContractRegistry
    except ImportError as e:
        print(f"\nError: Could not import contracts module: {e}")
        sys.exit(1)

    # Create registry from current directory
    repo_root = Path.cwd()
    registry = ContractRegistry(repo_root)
    contracts = registry.discover_contracts()

    # Apply filters
    filtered = []
    for name, contract in contracts.items():
        # Filter by tier
        if args.tier and contract.tier != args.tier:
            continue

        # Filter by language
        if args.language:
            languages = contract.applies_to.get('languages', [])
            if args.language not in languages and languages:
                continue

        # Filter by type
        if args.type and contract.type != args.type:
            continue

        # Filter by tag
        if args.tag:
            if args.tag not in contract.tags:
                continue

        filtered.append(contract)

    if not filtered:
        print("\n  No contracts found matching filters")
        return

    if args.format == 'table':
        print(f"\n  Found {len(filtered)} contracts:\n")
        print(f"  {'Name':<30} {'Type':<15} {'Tier':<10} {'Checks':<8} {'Enabled'}")
        print(f"  {'-' * 30} {'-' * 15} {'-' * 10} {'-' * 8} {'-' * 7}")
        for c in sorted(filtered, key=lambda x: (x.tier, x.name)):
            check_count = len(c.checks)
            enabled = '✓' if c.enabled else '✗'
            print(f"  {c.name:<30} {c.type:<15} {c.tier:<10} {check_count:<8} {enabled}")
    elif args.format == 'yaml':
        output = {'contracts': []}
        for c in filtered:
            output['contracts'].append({
                'name': c.name,
                'type': c.type,
                'tier': c.tier,
                'enabled': c.enabled,
                'checks': len(c.checks),
                'tags': c.tags
            })
        print(yaml.dump(output, default_flow_style=False))
    elif args.format == 'json':
        import json
        output = {'contracts': []}
        for c in filtered:
            output['contracts'].append({
                'name': c.name,
                'type': c.type,
                'tier': c.tier,
                'enabled': c.enabled,
                'checks': len(c.checks),
                'tags': c.tags
            })
        print(json.dumps(output, indent=2))


def run_contracts_show(args):
    """Show contract details."""
    print()
    print("=" * 60)
    print("CONTRACT DETAILS")
    print("=" * 60)

    sys.path.insert(0, str(Path(__file__).parent / 'tools'))

    try:
        from contracts import ContractRegistry
    except ImportError as e:
        print(f"\nError: Could not import contracts module: {e}")
        sys.exit(1)

    repo_root = Path.cwd()
    registry = ContractRegistry(repo_root)
    contract = registry.get_contract(args.name)

    if not contract:
        print(f"\n❌ Contract not found: {args.name}")
        sys.exit(1)

    if args.format == 'yaml':
        output = {
            'name': contract.name,
            'type': contract.type,
            'description': contract.description,
            'version': contract.version,
            'tier': contract.tier,
            'enabled': contract.enabled,
            'extends': contract.extends,
            'applies_to': contract.applies_to,
            'tags': contract.tags,
            'checks': contract.all_checks()
        }
        print(yaml.dump(output, default_flow_style=False))
    elif args.format == 'json':
        import json
        output = {
            'name': contract.name,
            'type': contract.type,
            'description': contract.description,
            'version': contract.version,
            'tier': contract.tier,
            'enabled': contract.enabled,
            'extends': contract.extends,
            'applies_to': contract.applies_to,
            'tags': contract.tags,
            'checks': contract.all_checks()
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"\n  Contract: {contract.name}")
        print(f"  Type: {contract.type}")
        print(f"  Version: {contract.version}")
        print(f"  Tier: {contract.tier}")
        print(f"  Enabled: {contract.enabled}")
        if contract.description:
            print(f"  Description: {contract.description[:80]}...")
        if contract.extends:
            print(f"  Extends: {', '.join(contract.extends)}")
        print(f"\n  Checks ({len(contract.all_checks())}):")
        for check in contract.all_checks():
            status = '✓' if check.get('enabled', True) else '✗'
            print(f"    {status} {check.get('id')}: {check.get('name')} [{check.get('type')}]")


def run_contracts_check(args):
    """Run contract checks."""
    print()
    print("=" * 60)
    print("CONTRACT CHECK")
    print("=" * 60)

    sys.path.insert(0, str(Path(__file__).parent / 'tools'))

    try:
        from contracts import ContractRegistry, run_contract, run_all_contracts
    except ImportError as e:
        print(f"\nError: Could not import contracts module: {e}")
        sys.exit(1)

    repo_root = Path.cwd()

    # Get file paths if specified
    file_paths = None
    if args.files:
        file_paths = [Path(f.strip()) for f in args.files.split(',')]

    # Run checks
    if args.contract:
        # Run specific contract
        registry = ContractRegistry(repo_root)
        contract = registry.get_contract(args.contract)
        if not contract:
            print(f"\n❌ Contract not found: {args.contract}")
            sys.exit(1)
        results = [run_contract(contract, repo_root, registry, file_paths)]
    else:
        # Run all applicable contracts
        results = run_all_contracts(
            repo_root,
            language=args.language,
            repo_type=args.repo_type,
            file_paths=file_paths
        )

    # Calculate summary
    total_errors = sum(len(r.errors) for r in results)
    total_warnings = sum(len(r.warnings) for r in results)
    total_exempted = sum(r.exempted_count for r in results)
    all_passed = all(r.passed for r in results)

    if args.format == 'text':
        print(f"\n  Ran {len(results)} contracts\n")

        for result in results:
            status = '✓' if result.passed else '✗'
            print(f"  {status} {result.contract_name} ({result.contract_type})")

            for check_result in result.check_results:
                if not check_result.passed:
                    severity_icon = '❌' if check_result.severity == 'error' else '⚠️' if check_result.severity == 'warning' else 'ℹ️'
                    if check_result.exempted:
                        severity_icon = '🔓'
                    location = f"{check_result.file_path}:{check_result.line_number}" if check_result.file_path else ""
                    print(f"      {severity_icon} {check_result.check_name}: {check_result.message}")
                    if location:
                        print(f"         at {location}")
                    if check_result.fix_hint:
                        print(f"         fix: {check_result.fix_hint}")

        print(f"\n  Summary:")
        print(f"    Errors: {total_errors}")
        print(f"    Warnings: {total_warnings}")
        print(f"    Exempted: {total_exempted}")

    elif args.format == 'yaml':
        output = {
            'summary': {
                'passed': all_passed,
                'contracts_checked': len(results),
                'errors': total_errors,
                'warnings': total_warnings,
                'exempted': total_exempted
            },
            'results': []
        }
        for result in results:
            output['results'].append({
                'contract': result.contract_name,
                'type': result.contract_type,
                'passed': result.passed,
                'violations': [
                    {
                        'check_id': r.check_id,
                        'check_name': r.check_name,
                        'severity': r.severity,
                        'message': r.message,
                        'file': r.file_path,
                        'line': r.line_number,
                        'exempted': r.exempted,
                        'exemption_id': r.exemption_id
                    }
                    for r in result.check_results if not r.passed
                ]
            })
        print(yaml.dump(output, default_flow_style=False))

    elif args.format == 'json':
        import json
        output = {
            'summary': {
                'passed': all_passed,
                'contracts_checked': len(results),
                'errors': total_errors,
                'warnings': total_warnings,
                'exempted': total_exempted
            },
            'results': []
        }
        for result in results:
            output['results'].append({
                'contract': result.contract_name,
                'type': result.contract_type,
                'passed': result.passed,
                'violations': [
                    {
                        'check_id': r.check_id,
                        'check_name': r.check_name,
                        'severity': r.severity,
                        'message': r.message,
                        'file': r.file_path,
                        'line': r.line_number,
                        'exempted': r.exempted,
                        'exemption_id': r.exemption_id
                    }
                    for r in result.check_results if not r.passed
                ]
            })
        print(json.dumps(output, indent=2))

    # Exit with error code if failed
    if not all_passed:
        if args.strict or total_errors > 0:
            sys.exit(1)


def run_contracts_init(args):
    """Initialize contract for repo."""
    print()
    print("=" * 60)
    print("CONTRACT INIT")
    print("=" * 60)

    repo_root = Path.cwd()
    contracts_dir = repo_root / 'contracts'
    contracts_dir.mkdir(exist_ok=True)

    # Determine contract name
    name = args.name or repo_root.name.replace('-', '_').replace(' ', '_').lower()

    contract_path = contracts_dir / f'{name}.contract.yaml'

    if contract_path.exists():
        print(f"\n❌ Contract already exists: {contract_path}")
        sys.exit(1)

    # Build contract content
    extends = args.extends or '_base'

    contract = {
        'schema_version': '1.0',
        'contract': {
            'name': name,
            'type': args.type,
            'description': f'Contract for {name} repository',
            'version': '1.0.0',
            'enabled': True,
            'extends': extends
        },
        'checks': []
    }

    with open(contract_path, 'w') as f:
        yaml.dump(contract, f, default_flow_style=False, sort_keys=False)

    print(f"\n✅ Created contract: {contract_path}")
    print(f"   Extends: {extends}")
    print(f"\n   Next steps:")
    print(f"   1. Edit {contract_path} to add checks")
    print(f"   2. Run 'python execute.py contracts check' to verify")


def run_contracts_validate(args):
    """Validate contract files."""
    print()
    print("=" * 60)
    print("CONTRACT VALIDATE")
    print("=" * 60)

    # TODO: Implement schema validation using the contract schema
    # For now, just check if contracts can be loaded

    sys.path.insert(0, str(Path(__file__).parent / 'tools'))

    try:
        from contracts import ContractRegistry
    except ImportError as e:
        print(f"\nError: Could not import contracts module: {e}")
        sys.exit(1)

    repo_root = Path.cwd()

    if args.file:
        # Validate specific file
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"\n❌ File not found: {file_path}")
            sys.exit(1)

        try:
            with open(file_path) as f:
                data = yaml.safe_load(f)
            if 'contract' not in data:
                print(f"\n❌ Invalid contract: missing 'contract' key")
                sys.exit(1)
            print(f"\n✅ Contract valid: {file_path}")
        except Exception as e:
            print(f"\n❌ Failed to validate: {e}")
            sys.exit(1)
    else:
        # Validate all contracts
        registry = ContractRegistry(repo_root)
        contracts = registry.discover_contracts()
        print(f"\n  Validated {len(contracts)} contracts")
        for name, contract in contracts.items():
            print(f"    ✓ {name} ({contract.tier})")


# ==============================================================================
# EXEMPTION HANDLERS
# ==============================================================================

def run_exemptions(args):
    """Fallback for exemptions without subcommand."""
    pass  # Handled in main()


def run_exemptions_list(args):
    """List all exemptions."""
    print()
    print("=" * 60)
    print("EXEMPTIONS LIST")
    print("=" * 60)

    sys.path.insert(0, str(Path(__file__).parent / 'tools'))

    try:
        from contracts import ContractRegistry
    except ImportError as e:
        print(f"\nError: Could not import contracts module: {e}")
        sys.exit(1)

    repo_root = Path.cwd()
    registry = ContractRegistry(repo_root)
    exemptions = registry.load_exemptions()

    # Apply filters
    filtered = []
    for ex in exemptions:
        if args.contract and ex.contract != args.contract:
            continue

        if args.status != 'all':
            if args.status == 'active' and not ex.is_active():
                continue
            if args.status == 'expired' and not ex.is_expired():
                continue
            if args.status == 'resolved' and ex.status != 'resolved':
                continue

        filtered.append(ex)

    if not filtered:
        print("\n  No exemptions found matching filters")
        return

    if args.format == 'table':
        print(f"\n  Found {len(filtered)} exemptions:\n")
        print(f"  {'ID':<25} {'Contract':<20} {'Check':<20} {'Status':<10} {'Expires'}")
        print(f"  {'-' * 25} {'-' * 20} {'-' * 20} {'-' * 10} {'-' * 12}")
        for ex in filtered:
            status = 'active' if ex.is_active() else 'expired' if ex.is_expired() else ex.status
            expires = str(ex.expires) if ex.expires else '-'
            checks_str = ex.checks[0] if len(ex.checks) == 1 else f"{ex.checks[0]}+{len(ex.checks)-1}"
            print(f"  {ex.id:<25} {ex.contract:<20} {checks_str:<20} {status:<10} {expires}")

    elif args.format == 'yaml':
        output = {'exemptions': []}
        for ex in filtered:
            output['exemptions'].append({
                'id': ex.id,
                'contract': ex.contract,
                'checks': ex.checks,
                'reason': ex.reason,
                'approved_by': ex.approved_by,
                'expires': str(ex.expires) if ex.expires else None,
                'status': ex.status,
                'is_active': ex.is_active()
            })
        print(yaml.dump(output, default_flow_style=False))

    elif args.format == 'json':
        import json
        output = {'exemptions': []}
        for ex in filtered:
            output['exemptions'].append({
                'id': ex.id,
                'contract': ex.contract,
                'checks': ex.checks,
                'reason': ex.reason,
                'approved_by': ex.approved_by,
                'expires': str(ex.expires) if ex.expires else None,
                'status': ex.status,
                'is_active': ex.is_active()
            })
        print(json.dumps(output, indent=2))


def run_exemptions_add(args):
    """Add a new exemption."""
    print()
    print("=" * 60)
    print("ADD EXEMPTION")
    print("=" * 60)

    from datetime import date

    repo_root = Path.cwd()
    exemptions_dir = repo_root / 'exemptions'
    exemptions_dir.mkdir(exist_ok=True)

    # Create exemption file if needed
    exemptions_file = exemptions_dir / 'exemptions.yaml'

    if exemptions_file.exists():
        with open(exemptions_file) as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {'schema_version': '1.0', 'exemptions': []}

    if 'exemptions' not in data:
        data['exemptions'] = []

    # Generate exemption ID
    exemption_id = f"{args.contract.replace(' ', '-').lower()}-{args.check}-{date.today().isoformat()}"

    # Parse scope
    scope = {}
    if args.files:
        scope['files'] = [f.strip() for f in args.files.split(',')]
    else:
        scope['global'] = True

    # Create exemption
    exemption = {
        'id': exemption_id,
        'contract': args.contract,
        'check': args.check,
        'reason': args.reason,
        'approved_by': args.approved_by,
        'approved_date': date.today().isoformat(),
        'scope': scope,
        'status': 'active'
    }

    if args.expires:
        exemption['expires'] = args.expires

    if args.ticket:
        exemption['ticket'] = args.ticket

    data['exemptions'].append(exemption)

    # Write back
    with open(exemptions_file, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    print(f"\n✅ Added exemption: {exemption_id}")
    print(f"   Contract: {args.contract}")
    print(f"   Check: {args.check}")
    print(f"   File: {exemptions_file}")


def run_exemptions_audit(args):
    """Audit exemptions."""
    print()
    print("=" * 60)
    print("EXEMPTION AUDIT")
    print("=" * 60)

    sys.path.insert(0, str(Path(__file__).parent / 'tools'))

    try:
        from contracts import ContractRegistry
    except ImportError as e:
        print(f"\nError: Could not import contracts module: {e}")
        sys.exit(1)

    repo_root = Path.cwd()
    registry = ContractRegistry(repo_root)
    exemptions = registry.load_exemptions()

    # Categorize
    active = [e for e in exemptions if e.is_active()]
    expired = [e for e in exemptions if e.is_expired()]
    no_expiry = [e for e in active if e.expires is None]

    print(f"\n  Exemption Audit Summary:")
    print(f"  {'─' * 40}")
    print(f"  Total exemptions: {len(exemptions)}")
    print(f"  Active: {len(active)}")
    print(f"  Expired: {len(expired)}")
    print(f"  Without expiration: {len(no_expiry)}")

    if args.show_expired and expired:
        print(f"\n  Expired Exemptions:")
        for ex in expired:
            print(f"    ⏰ {ex.id} (expired {ex.expires})")
            print(f"       Contract: {ex.contract}, Check: {ex.checks[0]}")

    if no_expiry:
        print(f"\n  ⚠️  Exemptions without expiration date:")
        for ex in no_expiry:
            print(f"    {ex.id}")
            print(f"       Contract: {ex.contract}, Check: {ex.checks[0]}")

    if expired:
        print(f"\n  Recommendation: Review and remove expired exemptions")


def run_render_spec(args):
    """Render YAML specification to Markdown for human consumption."""
    print()
    print("=" * 60)
    print("RENDER SPECIFICATION")
    print("=" * 60)
    
    spec_path = Path(args.spec_file)
    if not spec_path.exists():
        print(f"Error: {spec_path} not found")
        print("Run 'python execute.py draft' first")
        sys.exit(1)
    
    with open(spec_path) as f:
        spec = yaml.safe_load(f)
    
    # Build markdown document
    lines = []
    
    # Metadata header
    meta = spec.get('metadata', {})
    lines.append(f"# {meta.get('feature_name', 'Specification')}")
    lines.append("")
    lines.append(f"**Version:** {meta.get('version', '1.0')}")
    lines.append(f"**Status:** {meta.get('status', 'draft')}")
    lines.append(f"**Date:** {meta.get('created_date', 'N/A')}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Overview
    overview = spec.get('overview', {})
    lines.append("## 1. Overview")
    lines.append("")
    lines.append("### 1.1 Purpose")
    lines.append("")
    lines.append(overview.get('purpose', '').strip())
    lines.append("")
    
    if overview.get('background'):
        lines.append("### 1.2 Background")
        lines.append("")
        lines.append(overview.get('background', '').strip())
        lines.append("")
    
    lines.append("### 1.3 Scope")
    lines.append("")
    scope = overview.get('scope', {})
    if scope.get('includes'):
        lines.append("**In Scope:**")
        for item in scope.get('includes', []):
            lines.append(f"- {item}")
        lines.append("")
    if scope.get('excludes'):
        lines.append("**Out of Scope:**")
        for item in scope.get('excludes', []):
            lines.append(f"- {item}")
        lines.append("")
    
    if overview.get('assumptions'):
        lines.append("### 1.4 Assumptions")
        lines.append("")
        for item in overview.get('assumptions', []):
            lines.append(f"- {item}")
        lines.append("")
    
    if overview.get('constraints'):
        lines.append("### 1.5 Constraints")
        lines.append("")
        for item in overview.get('constraints', []):
            lines.append(f"- {item}")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # Requirements
    reqs = spec.get('requirements', {})
    lines.append("## 2. Requirements")
    lines.append("")
    
    lines.append("### 2.1 Functional Requirements")
    lines.append("")
    for req in reqs.get('functional', []):
        lines.append(f"**{req.get('id')}: {req.get('title')}**")
        lines.append("")
        lines.append(f"*Priority:* {req.get('priority', 'must').upper()}")
        lines.append("")
        lines.append(req.get('description', '').strip())
        lines.append("")
        if req.get('rationale'):
            lines.append(f"*Rationale:* {req.get('rationale')}")
            lines.append("")
        
        if req.get('acceptance_criteria'):
            lines.append("*Acceptance Criteria:*")
            lines.append("")
            lines.append("```gherkin")
            for ac in req.get('acceptance_criteria', []):
                lines.append(f"Scenario: {ac.get('id')}")
                lines.append(f"  Given {ac.get('given')}")
                lines.append(f"  When {ac.get('when')}")
                lines.append(f"  Then {ac.get('then')}")
                if ac.get('and_then'):
                    for at in ac.get('and_then', []):
                        lines.append(f"  And {at}")
                lines.append("")
            lines.append("```")
            lines.append("")
    
    if reqs.get('non_functional'):
        lines.append("### 2.2 Non-Functional Requirements")
        lines.append("")
        for req in reqs.get('non_functional', []):
            lines.append(f"**{req.get('id')}: {req.get('title')}**")
            lines.append("")
            lines.append(req.get('description', '').strip())
            lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # Entities
    entities = spec.get('entities', [])
    if entities:
        lines.append("## 3. Data Model")
        lines.append("")
        lines.append("### 3.1 Entities")
        lines.append("")
        
        for entity in entities:
            lines.append(f"#### {entity.get('name')}")
            lines.append("")
            lines.append(f"**Layer:** {entity.get('layer')} | **Type:** {entity.get('type')}")
            lines.append("")
            if entity.get('description'):
                lines.append(entity.get('description', '').strip())
                lines.append("")
            
            if entity.get('properties'):
                lines.append("**Properties:**")
                lines.append("")
                lines.append("| Property | Type | Nullable | Constraints | Description |")
                lines.append("|----------|------|----------|-------------|-------------|")
                for prop in entity.get('properties', []):
                    constraints = ', '.join(prop.get('constraints', [])) or '-'
                    lines.append(f"| {prop.get('name')} | {prop.get('type')} | {prop.get('nullable', False)} | {constraints} | {prop.get('description', '-')} |")
                lines.append("")
            
            if entity.get('methods'):
                lines.append("**Methods:**")
                lines.append("")
                for method in entity.get('methods', []):
                    params = ', '.join([f"{p.get('name')}: {p.get('type')}" for p in method.get('parameters', [])])
                    lines.append(f"- `{method.get('name')}({params}) -> {method.get('returns')}`: {method.get('description', '')}")
                lines.append("")
            
            if entity.get('invariants'):
                lines.append("**Invariants:**")
                lines.append("")
                for inv in entity.get('invariants', []):
                    lines.append(f"- {inv}")
                lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # Interfaces
    interfaces = spec.get('interfaces', [])
    if interfaces:
        lines.append("## 4. Interfaces")
        lines.append("")
        for iface in interfaces:
            lines.append(f"#### {iface.get('name')}")
            lines.append("")
            lines.append(f"**Type:** {iface.get('type')} | **Path:** `{iface.get('path')}`")
            lines.append("")
            
            if iface.get('request'):
                req = iface.get('request', {})
                lines.append(f"**Request Body:** `{req.get('body', 'N/A')}`")
                lines.append("")
            
            if iface.get('response'):
                resp = iface.get('response', {})
                lines.append(f"**Success Response:** `{resp.get('success', 'N/A')}`")
                lines.append("")
                if resp.get('error_codes'):
                    lines.append("**Error Codes:**")
                    for err in resp.get('error_codes', []):
                        lines.append(f"- `{err}`")
                    lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # Workflows
    workflows = spec.get('workflows', [])
    if workflows:
        lines.append("## 5. Workflows")
        lines.append("")
        for wf in workflows:
            lines.append(f"### {wf.get('name')}")
            lines.append("")
            if wf.get('description'):
                lines.append(wf.get('description'))
                lines.append("")
            lines.append(f"**Trigger:** {wf.get('trigger')}")
            lines.append("")
            
            if wf.get('steps'):
                lines.append("**Steps:**")
                lines.append("")
                for step in wf.get('steps', []):
                    lines.append(f"{step.get('step')}. **{step.get('actor', 'System')}:** {step.get('action')}")
                    if step.get('alternatives'):
                        for alt in step.get('alternatives', []):
                            lines.append(f"   - *Alternative:* {alt}")
                lines.append("")
            
            lines.append(f"**Success:** {wf.get('success_outcome', 'N/A')}")
            lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # Error Handling
    errors = spec.get('error_handling', [])
    if errors:
        lines.append("## 6. Error Handling")
        lines.append("")
        lines.append("| Error Code | Condition | Response | User Message |")
        lines.append("|------------|-----------|----------|--------------|")
        for err in errors:
            lines.append(f"| {err.get('error_code')} | {err.get('condition')} | {err.get('response')} | {err.get('user_message', '-')} |")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # Testing Notes
    testing = spec.get('testing_notes', {})
    if testing:
        lines.append("## 7. Testing Notes")
        lines.append("")
        if testing.get('unit_test_focus'):
            lines.append("### Unit Test Focus")
            lines.append("")
            for item in testing.get('unit_test_focus', []):
                lines.append(f"- {item}")
            lines.append("")
        if testing.get('integration_test_scenarios'):
            lines.append("### Integration Test Scenarios")
            lines.append("")
            for item in testing.get('integration_test_scenarios', []):
                lines.append(f"- {item}")
            lines.append("")
        if testing.get('edge_cases'):
            lines.append("### Edge Cases")
            lines.append("")
            for item in testing.get('edge_cases', []):
                lines.append(f"- {item}")
            lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # Glossary
    glossary = spec.get('glossary', [])
    if glossary:
        lines.append("## Glossary")
        lines.append("")
        lines.append("| Term | Definition |")
        lines.append("|------|------------|")
        for item in glossary:
            lines.append(f"| {item.get('term')} | {item.get('definition')} |")
        lines.append("")
    
    # Write output
    output_path = Path(args.output)
    markdown = '\n'.join(lines)
    
    with open(output_path, 'w') as f:
        f.write(markdown)
    
    print(f"\n✅ Rendered to: {output_path}")
    print(f"   Source: {spec_path}")
    print(f"   Lines: {len(lines)}")


def main():
    parser = argparse.ArgumentParser(
        description='Execute AgentForge contracts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Execution Modes:
  DEFAULT: Claude Code CLI (uses your subscription, no extra cost)
  --use-api: Anthropic API (pay-per-token, requires ANTHROPIC_API_KEY)

Workflow:
  intake → clarify → analyze → draft → validate
                                          ↓
                                    [if issues]
                                          ↓
                                       revise → validate → [repeat until approved]
                                          ↓
                                       verify  ← Deterministic correctness checks
                                          ↓
                                     APPROVED (code compiles, tests pass)

Revision Modes:
  Interactive (default):  Human decides each issue
  Autonomous (--auto):    Agent decides, flags uncertain for human

Verification Profiles:
  quick:        Fast sanity checks (compile, no secrets)
  ci:           Standard CI/CD checks (compile, test, architecture)
  full:         Complete verification suite
  architecture: Architecture and design rules only
  precommit:    Fast pre-commit hook checks

Examples:
  # Main workflow
  python execute.py intake --request "Add discount codes to orders"
  python execute.py clarify --answer "One code per order"
  python execute.py analyze
  python execute.py draft
  python execute.py validate

  # Interactive revision (default)
  python execute.py revise

  # Autonomous revision (agent decides)
  python execute.py revise --auto

  # Session management
  python execute.py revise --status      # View session
  python execute.py revise --continue    # Resume session
  python execute.py revise --apply       # Apply decisions
  python execute.py revise --force       # Start fresh

  # Context retrieval (code intelligence)
  python execute.py context -p ~/projects/MyApp --check      # Check components
  python execute.py context -p ~/projects/MyApp --index      # Build vector index
  python execute.py context -p ~/projects/MyApp -q "order processing"

  # Deterministic verification (replaces LLM judgment)
  python execute.py verify                           # Quick profile
  python execute.py verify --profile ci             # CI checks
  python execute.py verify --project MyApp.csproj   # With project path
  python execute.py verify --checks compile_check,test_check

  # Utilities
  python execute.py render-spec          # YAML → Markdown

  # Workspace management (multi-repo support)
  python execute.py workspace init --name my-project
  python execute.py workspace init --single-repo --name my-tool --lang python  # Single-repo mode
  python execute.py workspace add-repo --name api --path ../api --type service --lang csharp
  python execute.py workspace status
  python execute.py workspace list-repos --type service
  python execute.py workspace validate
  python execute.py workspace unlink   # Convert to single-repo

  # Configuration management (three-tier)
  python execute.py config init-global          # Initialize ~/.agentforge/
  python execute.py config show                  # Show all tiers
  python execute.py config show --tier global   # Show only global
  python execute.py config set context.budget_tokens 8000 --global

  # Contract management (code correctness rules)
  python execute.py contracts list                          # List all contracts
  python execute.py contracts list --tier builtin          # Show builtin contracts
  python execute.py contracts show _patterns-csharp        # Show contract details
  python execute.py contracts check                        # Run all contract checks
  python execute.py contracts check --contract my-rules    # Run specific contract
  python execute.py contracts init --extends _patterns-csharp  # Create repo contract

  # Exemption management (documented intentional violations)
  python execute.py exemptions list                        # List exemptions
  python execute.py exemptions list --status expired       # Show expired
  python execute.py exemptions add -c my-contract -k check-id -r "Legacy code" -a @me
  python execute.py exemptions audit                       # Audit exemptions
"""
    )
    
    parser.add_argument('--use-api', action='store_true',
                        help='Use Anthropic API instead of Claude Code CLI')
    
    subparsers = parser.add_subparsers(dest='command', help='Command')
    
    # INTAKE
    intake_parser = subparsers.add_parser('intake', help='Run INTAKE')
    intake_parser.add_argument('--request', '-r', required=True, help='Feature request')
    intake_parser.add_argument('--priority', '-p', choices=['critical', 'high', 'medium', 'low'])
    intake_parser.set_defaults(func=run_intake)
    
    # CLARIFY
    clarify_parser = subparsers.add_parser('clarify', help='Run CLARIFY')
    clarify_parser.add_argument('--intake-file', default='outputs/intake_record.yaml')
    clarify_parser.add_argument('--answer', '-a', help='Answer to previous question')
    clarify_parser.set_defaults(func=run_clarify)
    
    # ANALYZE
    analyze_parser = subparsers.add_parser('analyze', help='Run ANALYZE')
    analyze_parser.add_argument('--intake-file', default='outputs/intake_record.yaml')
    analyze_parser.add_argument('--clarification-file', default='outputs/clarification_log.yaml')
    analyze_parser.add_argument('--code-context', help='Code context to include (manual)')
    analyze_parser.add_argument('--project-path', help='Project path for automatic context retrieval')
    analyze_parser.set_defaults(func=run_analyze)
    
    # DRAFT
    draft_parser = subparsers.add_parser('draft', help='Run DRAFT')
    draft_parser.add_argument('--intake-file', default='outputs/intake_record.yaml')
    draft_parser.add_argument('--clarification-file', default='outputs/clarification_log.yaml')
    draft_parser.add_argument('--analysis-file', default='outputs/analysis_report.yaml')
    draft_parser.set_defaults(func=run_draft)
    
    # VALIDATE
    validate_parser = subparsers.add_parser('validate', help='Run VALIDATE')
    validate_parser.add_argument('--spec-file', default='outputs/specification.yaml')
    validate_parser.add_argument('--analysis-file', default='outputs/analysis_report.yaml')
    validate_parser.set_defaults(func=run_validate)
    
    # REVISE
    revise_parser = subparsers.add_parser('revise', help='Fix issues from validation')
    revise_parser.add_argument('--spec-file', default='outputs/specification.yaml')
    revise_parser.add_argument('--validation-file', default='outputs/validation_report.yaml')
    revise_parser.add_argument('--auto', action='store_true',
                               help='Autonomous mode - agent makes decisions')
    revise_parser.add_argument('--continue', '--resume', dest='resume', action='store_true',
                               help='Continue paused session')
    revise_parser.add_argument('--apply', action='store_true',
                               help='Apply all decisions to specification')
    revise_parser.add_argument('--status', action='store_true',
                               help='Show revision session status')
    revise_parser.add_argument('--force', action='store_true',
                               help='Start fresh session (discard existing)')
    revise_parser.set_defaults(func=run_revise)
    
    # CONTEXT (test context retrieval)
    context_parser = subparsers.add_parser('context', help='Test context retrieval')
    context_parser.add_argument('--project', '-p', required=True, help='Project root path')
    context_parser.add_argument('--query', '-q', help='Search query')
    context_parser.add_argument('--budget', '-b', type=int, default=6000, help='Token budget')
    context_parser.add_argument('--check', action='store_true', help='Check available components')
    context_parser.add_argument('--index', action='store_true', help='Build/rebuild vector index')
    context_parser.add_argument('--force', action='store_true', help='Force rebuild index')
    context_parser.add_argument('--provider', choices=['local', 'openai', 'voyage'],
                                help='Embedding provider (default: auto-select)')
    context_parser.add_argument('--no-lsp', action='store_true', help='Disable LSP')
    context_parser.add_argument('--no-vector', action='store_true', help='Disable vector search')
    context_parser.add_argument('--format', '-f', choices=['text', 'yaml', 'json'], default='text',
                                help='Output format')
    context_parser.set_defaults(func=run_context)

    # VERIFY (deterministic correctness checks)
    verify_parser = subparsers.add_parser('verify', help='Run deterministic correctness checks')
    verify_parser.add_argument('--profile', '-p',
                               choices=['quick', 'ci', 'full', 'architecture', 'precommit'],
                               help='Check profile to run')
    verify_parser.add_argument('--checks', '-c',
                               help='Comma-separated list of check IDs')
    verify_parser.add_argument('--project',
                               help='Path to project file (e.g., MyApp.csproj)')
    verify_parser.add_argument('--project-root',
                               help='Project root directory')
    verify_parser.add_argument('--config',
                               help='Path to correctness.yaml config')
    verify_parser.add_argument('--format', '-f',
                               choices=['text', 'yaml', 'json'],
                               default='yaml',
                               help='Report output format')
    verify_parser.add_argument('--strict', action='store_true',
                               help='Fail on advisory warnings too')
    verify_parser.set_defaults(func=run_verify)

    # RENDER-SPEC
    render_parser = subparsers.add_parser('render-spec', help='Render YAML spec to Markdown')
    render_parser.add_argument('--spec-file', default='outputs/specification.yaml')
    render_parser.add_argument('--output', '-o', default='outputs/specification.md')
    render_parser.set_defaults(func=run_render_spec)

    # WORKSPACE
    workspace_parser = subparsers.add_parser('workspace', help='Workspace management')
    workspace_parser.add_argument('--workspace', '-w',
                                   help='Path to workspace.yaml (or use AGENTFORGE_WORKSPACE env)')
    workspace_subparsers = workspace_parser.add_subparsers(dest='workspace_command',
                                                            help='Workspace subcommand')

    # workspace init
    ws_init_parser = workspace_subparsers.add_parser('init', help='Initialize a new workspace or single-repo config')
    ws_init_parser.add_argument('--name', '-n', required=True,
                                help='Workspace/repo name (lowercase, alphanumeric, hyphens)')
    ws_init_parser.add_argument('--path', '-p',
                                help='Directory for workspace.yaml (default: current)')
    ws_init_parser.add_argument('--description', '-d',
                                help='Workspace description')
    ws_init_parser.add_argument('--single-repo', action='store_true',
                                help='Initialize for single-repo mode (no workspace)')
    ws_init_parser.add_argument('--language', '--lang', '-l',
                                choices=['csharp', 'typescript', 'python', 'java', 'go', 'rust'],
                                help='Primary language (required for --single-repo)')
    ws_init_parser.add_argument('--type', '-t',
                                choices=['service', 'library', 'application', 'meta', 'tool'],
                                default='service',
                                help='Repository type (for --single-repo)')
    ws_init_parser.add_argument('--force', action='store_true',
                                help='Overwrite existing config')
    ws_init_parser.set_defaults(func=run_workspace_init)

    # workspace status
    ws_status_parser = workspace_subparsers.add_parser('status', help='Show workspace status')
    ws_status_parser.add_argument('--repo', '-r',
                                  help='Start discovery from this repo directory')
    ws_status_parser.set_defaults(func=run_workspace_status)

    # workspace add-repo
    ws_add_parser = workspace_subparsers.add_parser('add-repo', help='Add a repository to workspace')
    ws_add_parser.add_argument('--name', '-n', required=True,
                               help='Repository name (lowercase, alphanumeric, hyphens)')
    ws_add_parser.add_argument('--path', '-p', required=True,
                               help='Relative path to repository root')
    ws_add_parser.add_argument('--type', '-t', required=True,
                               choices=['service', 'library', 'application', 'meta'],
                               help='Repository type')
    ws_add_parser.add_argument('--language', '--lang', '-l', required=True,
                               choices=['csharp', 'typescript', 'python', 'java', 'go', 'rust', 'yaml'],
                               help='Primary programming language')
    ws_add_parser.add_argument('--framework', '-f',
                               help='Framework (e.g., aspnetcore, express, django)')
    ws_add_parser.add_argument('--lsp',
                               choices=['omnisharp', 'csharp-ls', 'typescript-language-server', 'pyright'],
                               help='LSP server to use')
    ws_add_parser.add_argument('--layers',
                               help='Comma-separated architecture layers')
    ws_add_parser.add_argument('--tags',
                               help='Comma-separated tags')
    ws_add_parser.set_defaults(func=run_workspace_add_repo)

    # workspace remove-repo
    ws_remove_parser = workspace_subparsers.add_parser('remove-repo', help='Remove a repository')
    ws_remove_parser.add_argument('--name', '-n', required=True,
                                  help='Repository name to remove')
    ws_remove_parser.set_defaults(func=run_workspace_remove_repo)

    # workspace link
    ws_link_parser = workspace_subparsers.add_parser('link',
                                                      help='Link a repo to a workspace')
    ws_link_parser.add_argument('--workspace', '-w', required=True,
                                help='Path to workspace.yaml')
    ws_link_parser.add_argument('--repo', '-r',
                                help='Repository directory (default: current)')
    ws_link_parser.set_defaults(func=run_workspace_link)

    # workspace validate
    ws_validate_parser = workspace_subparsers.add_parser('validate',
                                                          help='Validate workspace configuration')
    ws_validate_parser.set_defaults(func=run_workspace_validate)

    # workspace list-repos
    ws_list_parser = workspace_subparsers.add_parser('list-repos', help='List repositories')
    ws_list_parser.add_argument('--type', '-t',
                                choices=['service', 'library', 'application', 'meta'],
                                help='Filter by type')
    ws_list_parser.add_argument('--language', '--lang', '-l',
                                help='Filter by language')
    ws_list_parser.add_argument('--tag',
                                help='Filter by tag')
    ws_list_parser.add_argument('--format', '-f',
                                choices=['table', 'json', 'yaml'],
                                default='table',
                                help='Output format')
    ws_list_parser.set_defaults(func=run_workspace_list_repos)

    # workspace unlink
    ws_unlink_parser = workspace_subparsers.add_parser('unlink',
                                                        help='Unlink repo from workspace (convert to single-repo)')
    ws_unlink_parser.set_defaults(func=run_workspace_unlink)

    workspace_parser.set_defaults(func=run_workspace)

    # CONFIG
    config_parser = subparsers.add_parser('config', help='Configuration management')
    config_subparsers = config_parser.add_subparsers(dest='config_command',
                                                      help='Config subcommand')

    # config init-global
    cfg_init_parser = config_subparsers.add_parser('init-global',
                                                    help='Initialize global config at ~/.agentforge/')
    cfg_init_parser.add_argument('--force', action='store_true',
                                  help='Overwrite existing config')
    cfg_init_parser.set_defaults(func=run_config_init_global)

    # config show
    cfg_show_parser = config_subparsers.add_parser('show', help='Show configuration')
    cfg_show_parser.add_argument('--tier',
                                  choices=['global', 'workspace', 'repo', 'effective'],
                                  help='Show specific tier (default: show all)')
    cfg_show_parser.set_defaults(func=run_config_show)

    # config set
    cfg_set_parser = config_subparsers.add_parser('set', help='Set a configuration value')
    cfg_set_parser.add_argument('key', help='Config key (dot notation, e.g., context.budget_tokens)')
    cfg_set_parser.add_argument('value', help='Value to set')
    cfg_set_parser.add_argument('--global', dest='set_global', action='store_true',
                                 help='Set in global config')
    cfg_set_parser.add_argument('--workspace', dest='set_workspace', action='store_true',
                                 help='Set in workspace config')
    cfg_set_parser.add_argument('--repo', dest='set_repo', action='store_true',
                                 help='Set in repo config (default)')
    cfg_set_parser.set_defaults(func=run_config_set)

    config_parser.set_defaults(func=run_config)

    # CONTRACTS
    contracts_parser = subparsers.add_parser('contracts', help='Contract management')
    contracts_subparsers = contracts_parser.add_subparsers(dest='contracts_command',
                                                           help='Contracts subcommand')

    # contracts list
    ct_list_parser = contracts_subparsers.add_parser('list', help='List all contracts')
    ct_list_parser.add_argument('--language', '--lang', '-l',
                                help='Filter by language')
    ct_list_parser.add_argument('--type', '-t',
                                help='Filter by contract type')
    ct_list_parser.add_argument('--tag',
                                help='Filter by tag')
    ct_list_parser.add_argument('--tier',
                                choices=['builtin', 'global', 'workspace', 'repo'],
                                help='Filter by tier')
    ct_list_parser.add_argument('--format', '-f',
                                choices=['table', 'json', 'yaml'],
                                default='table',
                                help='Output format')
    ct_list_parser.set_defaults(func=run_contracts_list)

    # contracts show
    ct_show_parser = contracts_subparsers.add_parser('show', help='Show contract details')
    ct_show_parser.add_argument('name', help='Contract name')
    ct_show_parser.add_argument('--format', '-f',
                                choices=['yaml', 'json', 'text'],
                                default='yaml',
                                help='Output format')
    ct_show_parser.set_defaults(func=run_contracts_show)

    # contracts check
    ct_check_parser = contracts_subparsers.add_parser('check', help='Run contract checks')
    ct_check_parser.add_argument('--contract', '-c',
                                 help='Run specific contract (default: all applicable)')
    ct_check_parser.add_argument('--check', '-k',
                                 help='Run specific check ID')
    ct_check_parser.add_argument('--language', '--lang', '-l',
                                 help='Filter by language')
    ct_check_parser.add_argument('--repo-type', '-t',
                                 help='Repository type (service, library, etc.)')
    ct_check_parser.add_argument('--files', '-F',
                                 help='Comma-separated file paths to check')
    ct_check_parser.add_argument('--format', '-f',
                                 choices=['text', 'yaml', 'json'],
                                 default='text',
                                 help='Output format')
    ct_check_parser.add_argument('--strict', action='store_true',
                                 help='Fail on warnings too (not just errors)')
    ct_check_parser.set_defaults(func=run_contracts_check)

    # contracts init
    ct_init_parser = contracts_subparsers.add_parser('init', help='Initialize contract for repo')
    ct_init_parser.add_argument('--extends', '-e',
                                help='Parent contract to extend (e.g., _patterns-csharp)')
    ct_init_parser.add_argument('--name', '-n',
                                help='Contract name (default: repo-specific)')
    ct_init_parser.add_argument('--type', '-t',
                                choices=['architecture', 'patterns', 'naming', 'testing',
                                         'documentation', 'security', 'api', 'custom'],
                                default='patterns',
                                help='Contract type')
    ct_init_parser.set_defaults(func=run_contracts_init)

    # contracts validate
    ct_validate_parser = contracts_subparsers.add_parser('validate',
                                                          help='Validate contract files')
    ct_validate_parser.add_argument('--file', '-f',
                                    help='Specific contract file to validate')
    ct_validate_parser.set_defaults(func=run_contracts_validate)

    contracts_parser.set_defaults(func=run_contracts)

    # EXEMPTIONS
    exemptions_parser = subparsers.add_parser('exemptions', help='Exemption management')
    exemptions_subparsers = exemptions_parser.add_subparsers(dest='exemptions_command',
                                                             help='Exemptions subcommand')

    # exemptions list
    ex_list_parser = exemptions_subparsers.add_parser('list', help='List all exemptions')
    ex_list_parser.add_argument('--contract', '-c',
                                help='Filter by contract')
    ex_list_parser.add_argument('--status',
                                choices=['active', 'expired', 'resolved', 'all'],
                                default='active',
                                help='Filter by status')
    ex_list_parser.add_argument('--format', '-f',
                                choices=['table', 'json', 'yaml'],
                                default='table',
                                help='Output format')
    ex_list_parser.set_defaults(func=run_exemptions_list)

    # exemptions add
    ex_add_parser = exemptions_subparsers.add_parser('add', help='Add a new exemption')
    ex_add_parser.add_argument('--contract', '-c', required=True,
                               help='Contract name')
    ex_add_parser.add_argument('--check', '-k', required=True,
                               help='Check ID to exempt')
    ex_add_parser.add_argument('--reason', '-r', required=True,
                               help='Reason for exemption')
    ex_add_parser.add_argument('--approved-by', '-a', required=True,
                               help='Who approved (e.g., @username)')
    ex_add_parser.add_argument('--files', '-F',
                               help='Comma-separated file patterns to exempt')
    ex_add_parser.add_argument('--expires', '-e',
                               help='Expiration date (YYYY-MM-DD)')
    ex_add_parser.add_argument('--ticket', '-t',
                               help='Tracking ticket (e.g., AB#1234)')
    ex_add_parser.set_defaults(func=run_exemptions_add)

    # exemptions audit
    ex_audit_parser = exemptions_subparsers.add_parser('audit', help='Audit exemptions')
    ex_audit_parser.add_argument('--show-expired', action='store_true',
                                 help='Include expired exemptions')
    ex_audit_parser.add_argument('--show-unused', action='store_true',
                                 help='Find exemptions that no longer match violations')
    ex_audit_parser.add_argument('--format', '-f',
                                 choices=['text', 'yaml', 'json'],
                                 default='text',
                                 help='Output format')
    ex_audit_parser.set_defaults(func=run_exemptions_audit)

    exemptions_parser.set_defaults(func=run_exemptions)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    # Handle workspace without subcommand
    if args.command == 'workspace' and (not hasattr(args, 'workspace_command') or args.workspace_command is None):
        workspace_parser.print_help()
        sys.exit(1)

    # Handle config without subcommand
    if args.command == 'config' and (not hasattr(args, 'config_command') or args.config_command is None):
        config_parser.print_help()
        sys.exit(1)

    # Handle contracts without subcommand
    if args.command == 'contracts' and (not hasattr(args, 'contracts_command') or args.contracts_command is None):
        contracts_parser.print_help()
        sys.exit(1)

    # Handle exemptions without subcommand
    if args.command == 'exemptions' and (not hasattr(args, 'exemptions_command') or args.exemptions_command is None):
        exemptions_parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == '__main__':
    main()
