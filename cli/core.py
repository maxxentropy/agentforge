"""
Core utilities for CLI command execution.

Contains shared functions used across multiple command modules:
- API calling (Claude Code CLI and Anthropic API)
- YAML parsing and extraction
- Contract execution
"""

import os
import sys
import yaml
import subprocess
import tempfile
import json as json_module
import re
from pathlib import Path
from typing import Any

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from run_contract import ContractRunner


# YAML enforcement prompt for Claude CLI
YAML_ENFORCEMENT_PROMPT = """CRITICAL: You are in YAML-only output mode.

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


def _extract_text_from_content(content: Any) -> str | None:
    """Extract text from various content formats."""
    if isinstance(content, str):
        return content
    if isinstance(content, list) and len(content) > 0:
        first = content[0]
        if isinstance(first, dict):
            return first.get('text', str(first))
        return str(first)
    return None


def _extract_from_messages(messages: list) -> str | None:
    """Extract text from messages array (conversation format)."""
    for msg in reversed(messages):
        if not isinstance(msg, dict) or msg.get('role') != 'assistant':
            continue
        content = msg.get('content', [])
        if isinstance(content, str):
            return content
        text = _extract_from_content_blocks(content)
        if text:
            return text
    return None


def _extract_from_content_blocks(content: list) -> str | None:
    """Extract text from content blocks array."""
    if not isinstance(content, list):
        return None
    for block in content:
        if isinstance(block, str):
            return block
        if isinstance(block, dict) and block.get('type') == 'text':
            return block.get('text', '')
    return None


def _parse_claude_json_response(json_response: Any, raw_stdout: str) -> str:
    """Parse Claude CLI JSON response to extract text content."""
    if isinstance(json_response, str):
        return json_response
    if not isinstance(json_response, dict):
        return raw_stdout

    # Try result.content[0].text (newer format)
    if 'result' in json_response:
        result_obj = json_response['result']
        if isinstance(result_obj, str):
            return result_obj
        if isinstance(result_obj, dict):
            text = _extract_text_from_content(result_obj.get('content', []))
            if text:
                return text

    # Try messages array (conversation format)
    if 'messages' in json_response:
        text = _extract_from_messages(json_response['messages'])
        if text:
            return text

    # Try direct text or content fields
    if 'text' in json_response:
        return json_response['text']
    if 'content' in json_response:
        text = _extract_text_from_content(json_response['content'])
        if text:
            return text

    return raw_stdout


def call_claude_code(system: str, user: str) -> str:
    """
    Call Claude Code CLI (uses your subscription, no API credits needed).

    This is the DEFAULT execution method.
    Uses --output-format json and --append-system-prompt for structured output.
    """
    full_prompt = f"{system}\n\n---\n\n{user}"

    # Write prompt to temp file (handles large prompts better)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(full_prompt)
        temp_path = f.name

    try:
        result = subprocess.run(
            [
                'claude', '-p', f'@{temp_path}',
                '--output-format', 'json',
                '--append-system-prompt', YAML_ENFORCEMENT_PROMPT
            ],
            capture_output=True,
            text=True,
            timeout=300,
            env={**os.environ, 'NO_COLOR': '1'}
        )

        if result.returncode != 0:
            print(f"Claude Code error (exit {result.returncode}):")
            print(result.stderr or result.stdout)
            sys.exit(1)

        # Parse JSON response
        try:
            json_response = json_module.loads(result.stdout)
            return _parse_claude_json_response(json_response, result.stdout)
        except json_module.JSONDecodeError:
            return result.stdout

    except FileNotFoundError:
        print("=" * 60)
        print("ERROR: 'claude' command not found")
        print("=" * 60)
        print("\nClaude Code CLI is not installed or not in PATH.\n")
        print("Options:")
        print("  1. Install Claude Code: npm install -g @anthropic-ai/claude-code")
        print("     (Requires Node.js and Claude Pro/Team subscription)\n")
        print("  2. Use API mode instead:")
        print("     export ANTHROPIC_API_KEY=your_key")
        print("     python execute.py intake --request '...' --use-api\n")
        sys.exit(1)

    except subprocess.TimeoutExpired:
        print("Error: Claude Code timed out after 5 minutes")
        sys.exit(1)

    finally:
        try:
            Path(temp_path).unlink()
        except OSError:
            pass


def call_anthropic_api(
    system: str,
    user: str,
    max_tokens: int = 4096,
    temperature: float = 0.0
) -> str:
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


def _find_yaml_in_code_blocks(response: str) -> str | None:
    """Find YAML content in markdown code blocks."""
    # Try explicit YAML blocks first
    yaml_pattern = r'```ya?ml?\s*\n(.*?)```'
    matches = re.findall(yaml_pattern, response, re.DOTALL | re.IGNORECASE)
    if matches:
        return matches[-1].strip()

    # Try any code block that looks like YAML
    code_pattern = r'```\s*\n(.*?)```'
    for match in reversed(re.findall(code_pattern, response, re.DOTALL)):
        if ':' in match and not match.strip().startswith('{'):
            return match.strip()
    return None


def _is_prose_line(line: str) -> bool:
    """Check if a line is prose rather than YAML."""
    prose_starts = ('**', 'Looking at', 'Let me', 'Here is', 'The ')
    return line.startswith(prose_starts)


def _extract_yaml_lines(response: str) -> str | None:
    """Extract YAML-like lines from raw response."""
    yaml_lines = []
    in_yaml = False

    for line in response.split('\n'):
        if re.match(r'^[a-z_]+:', line) or re.match(r'^- ', line):
            in_yaml = True
        if not in_yaml:
            continue
        if _is_prose_line(line):
            if yaml_lines:
                break
            continue
        yaml_lines.append(line)

    return '\n'.join(yaml_lines).strip() if yaml_lines else None


def extract_yaml_from_response(response: str) -> str:
    """Extract YAML content from a response that may include markdown or prose."""
    # Try code blocks first
    result = _find_yaml_in_code_blocks(response)
    if result:
        return result

    # Try extracting YAML-like lines
    result = _extract_yaml_lines(response)
    if result:
        return result

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
