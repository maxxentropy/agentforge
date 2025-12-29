"""
Contract management commands.

Handles contract listing, checking, initialization, validation, and
exemption management.
"""

import sys
import json
import yaml
from pathlib import Path
from datetime import date


def _ensure_contracts_tools():
    """Add tools directory to path for contracts imports."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'tools'))


# =============================================================================
# CONTRACT COMMANDS
# =============================================================================

def run_contracts(args):
    """Fallback for contracts without subcommand."""
    pass


def run_contracts_list(args):
    """List all contracts."""
    print()
    print("=" * 60)
    print("CONTRACTS LIST")
    print("=" * 60)

    _ensure_contracts_tools()

    try:
        from contracts import ContractRegistry
    except ImportError as e:
        print(f"\nError: Could not import contracts module: {e}")
        sys.exit(1)

    repo_root = Path.cwd()
    registry = ContractRegistry(repo_root)
    contracts = registry.discover_contracts()

    filtered = _filter_contracts(contracts, args)

    if not filtered:
        print("\n  No contracts found matching filters")
        return

    _output_contracts(filtered, args.format)


def _filter_contracts(contracts: dict, args) -> list:
    """Filter contracts by tier, language, type, tag."""
    filtered = []
    for name, contract in contracts.items():
        if args.tier and contract.tier != args.tier:
            continue
        if args.language:
            languages = contract.applies_to.get('languages', [])
            if args.language not in languages and languages:
                continue
        if args.type and contract.type != args.type:
            continue
        if args.tag and args.tag not in contract.tags:
            continue
        filtered.append(contract)
    return filtered


def _output_contracts(filtered: list, fmt: str):
    """Output contracts in specified format."""
    if fmt == 'table':
        print(f"\n  Found {len(filtered)} contracts:\n")
        print(f"  {'Name':<30} {'Type':<15} {'Tier':<10} {'Checks':<8} {'Enabled'}")
        print(f"  {'-' * 30} {'-' * 15} {'-' * 10} {'-' * 8} {'-' * 7}")
        for c in sorted(filtered, key=lambda x: (x.tier, x.name)):
            enabled = '✓' if c.enabled else '✗'
            print(f"  {c.name:<30} {c.type:<15} {c.tier:<10} {len(c.checks):<8} {enabled}")
    elif fmt == 'yaml':
        output = {'contracts': [{'name': c.name, 'type': c.type, 'tier': c.tier, 'enabled': c.enabled, 'checks': len(c.checks), 'tags': c.tags} for c in filtered]}
        print(yaml.dump(output, default_flow_style=False))
    elif fmt == 'json':
        output = {'contracts': [{'name': c.name, 'type': c.type, 'tier': c.tier, 'enabled': c.enabled, 'checks': len(c.checks), 'tags': c.tags} for c in filtered]}
        print(json.dumps(output, indent=2))


def run_contracts_show(args):
    """Show contract details."""
    print()
    print("=" * 60)
    print("CONTRACT DETAILS")
    print("=" * 60)

    _ensure_contracts_tools()

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

    _output_contract_details(contract, args.format)


def _output_contract_details(contract, fmt: str):
    """Output contract details in specified format."""
    output = {
        'name': contract.name, 'type': contract.type, 'description': contract.description,
        'version': contract.version, 'tier': contract.tier, 'enabled': contract.enabled,
        'extends': contract.extends, 'applies_to': contract.applies_to, 'tags': contract.tags,
        'checks': contract.all_checks()
    }
    if fmt == 'yaml':
        print(yaml.dump(output, default_flow_style=False))
    elif fmt == 'json':
        print(json.dumps(output, indent=2))
    else:
        print(f"\n  Contract: {contract.name}")
        print(f"  Type: {contract.type}\n  Version: {contract.version}\n  Tier: {contract.tier}\n  Enabled: {contract.enabled}")
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

    _ensure_contracts_tools()

    try:
        from contracts import ContractRegistry, run_contract, run_all_contracts
    except ImportError as e:
        print(f"\nError: Could not import contracts module: {e}")
        sys.exit(1)

    repo_root = Path.cwd()
    file_paths = [Path(f.strip()) for f in args.files.split(',')] if args.files else None

    if args.contract:
        registry = ContractRegistry(repo_root)
        contract = registry.get_contract(args.contract)
        if not contract:
            print(f"\n❌ Contract not found: {args.contract}")
            sys.exit(1)
        results = [run_contract(contract, repo_root, registry, file_paths)]
    else:
        results = run_all_contracts(repo_root, language=args.language, repo_type=args.repo_type, file_paths=file_paths)

    total_errors = sum(len(r.errors) for r in results)
    total_warnings = sum(len(r.warnings) for r in results)
    total_exempted = sum(r.exempted_count for r in results)
    all_passed = all(r.passed for r in results)

    _output_check_results(results, all_passed, total_errors, total_warnings, total_exempted, args.format)

    if not all_passed and (args.strict or total_errors > 0):
        sys.exit(1)


def _output_check_results(results, all_passed, total_errors, total_warnings, total_exempted, fmt):
    """Output check results in specified format."""
    if fmt == 'text':
        _print_contracts_text(results, total_errors, total_warnings, total_exempted)
    else:
        output = _build_contracts_output(results, all_passed, total_errors, total_warnings, total_exempted)
        if fmt == 'yaml':
            print(yaml.dump(output, default_flow_style=False))
        elif fmt == 'json':
            print(json.dumps(output, indent=2))


def _build_contracts_output(results, all_passed, total_errors, total_warnings, total_exempted):
    """Build structured output dict for contract results."""
    output = {'summary': {'passed': all_passed, 'contracts_checked': len(results), 'errors': total_errors, 'warnings': total_warnings, 'exempted': total_exempted}, 'results': []}
    for result in results:
        output['results'].append({
            'contract': result.contract_name, 'type': result.contract_type, 'passed': result.passed,
            'violations': [{'check_id': r.check_id, 'check_name': r.check_name, 'severity': r.severity, 'message': r.message, 'file': r.file_path, 'line': r.line_number, 'exempted': r.exempted, 'exemption_id': r.exemption_id} for r in result.check_results if not r.passed]
        })
    return output


def _print_contracts_text(results, total_errors, total_warnings, total_exempted):
    """Print contract results in text format."""
    print(f"\n  Ran {len(results)} contracts\n")
    for result in results:
        status = '✓' if result.passed else '✗'
        print(f"  {status} {result.contract_name} ({result.contract_type})")
        for check_result in result.check_results:
            if not check_result.passed:
                icon = '🔓' if check_result.exempted else '❌' if check_result.severity == 'error' else '⚠️' if check_result.severity == 'warning' else 'ℹ️'
                location = f"{check_result.file_path}:{check_result.line_number}" if check_result.file_path else ""
                print(f"      {icon} {check_result.check_name}: {check_result.message}")
                if location:
                    print(f"         at {location}")
                if check_result.fix_hint:
                    print(f"         fix: {check_result.fix_hint}")
    print(f"\n  Summary:\n    Errors: {total_errors}\n    Warnings: {total_warnings}\n    Exempted: {total_exempted}")


def run_contracts_init(args):
    """Initialize contract for repo."""
    print()
    print("=" * 60)
    print("CONTRACT INIT")
    print("=" * 60)

    repo_root = Path.cwd()
    contracts_dir = repo_root / 'contracts'
    contracts_dir.mkdir(exist_ok=True)

    name = args.name or repo_root.name.replace('-', '_').replace(' ', '_').lower()
    contract_path = contracts_dir / f'{name}.contract.yaml'

    if contract_path.exists():
        print(f"\n❌ Contract already exists: {contract_path}")
        sys.exit(1)

    extends = args.extends or '_base'
    contract = {
        'schema_version': '1.0',
        'contract': {'name': name, 'type': args.type, 'description': f'Contract for {name} repository', 'version': '1.0.0', 'enabled': True, 'extends': extends},
        'checks': []
    }

    with open(contract_path, 'w') as f:
        yaml.dump(contract, f, default_flow_style=False, sort_keys=False)

    print(f"\n✅ Created contract: {contract_path}")
    print(f"   Extends: {extends}")
    print(f"\n   Next steps:\n   1. Edit {contract_path} to add checks\n   2. Run 'python execute.py contracts check' to verify")


def run_contracts_validate(args):
    """Validate contract files."""
    print()
    print("=" * 60)
    print("CONTRACT VALIDATE")
    print("=" * 60)

    _ensure_contracts_tools()

    try:
        from contracts import ContractRegistry
    except ImportError as e:
        print(f"\nError: Could not import contracts module: {e}")
        sys.exit(1)

    repo_root = Path.cwd()

    if args.file:
        _validate_single_contract(args.file)
    else:
        registry = ContractRegistry(repo_root)
        contracts = registry.discover_contracts()
        print(f"\n  Validated {len(contracts)} contracts")
        for name, contract in contracts.items():
            print(f"    ✓ {name} ({contract.tier})")


def _validate_single_contract(file_path: str):
    """Validate a single contract file."""
    path = Path(file_path)
    if not path.exists():
        print(f"\n❌ File not found: {path}")
        sys.exit(1)
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
        if 'contract' not in data:
            print(f"\n❌ Invalid contract: missing 'contract' key")
            sys.exit(1)
        print(f"\n✅ Contract valid: {path}")
    except Exception as e:
        print(f"\n❌ Failed to validate: {e}")
        sys.exit(1)


# =============================================================================
# EXEMPTION COMMANDS
# =============================================================================

def run_exemptions(args):
    """Fallback for exemptions without subcommand."""
    pass


def run_exemptions_list(args):
    """List all exemptions."""
    print()
    print("=" * 60)
    print("EXEMPTIONS LIST")
    print("=" * 60)

    _ensure_contracts_tools()

    try:
        from contracts import ContractRegistry
    except ImportError as e:
        print(f"\nError: Could not import contracts module: {e}")
        sys.exit(1)

    repo_root = Path.cwd()
    registry = ContractRegistry(repo_root)
    exemptions = registry.load_exemptions()

    filtered = _filter_exemptions(exemptions, args)

    if not filtered:
        print("\n  No exemptions found matching filters")
        return

    _output_exemptions(filtered, args.format)


def _filter_exemptions(exemptions, args) -> list:
    """Filter exemptions by contract and status."""
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
    return filtered


def _output_exemptions(filtered, fmt: str):
    """Output exemptions in specified format."""
    if fmt == 'table':
        print(f"\n  Found {len(filtered)} exemptions:\n")
        print(f"  {'ID':<25} {'Contract':<20} {'Check':<20} {'Status':<10} {'Expires'}")
        print(f"  {'-' * 25} {'-' * 20} {'-' * 20} {'-' * 10} {'-' * 12}")
        for ex in filtered:
            status = 'active' if ex.is_active() else 'expired' if ex.is_expired() else ex.status
            expires = str(ex.expires) if ex.expires else '-'
            checks_str = ex.checks[0] if len(ex.checks) == 1 else f"{ex.checks[0]}+{len(ex.checks)-1}"
            print(f"  {ex.id:<25} {ex.contract:<20} {checks_str:<20} {status:<10} {expires}")
    else:
        output = {'exemptions': [{'id': ex.id, 'contract': ex.contract, 'checks': ex.checks, 'reason': ex.reason, 'approved_by': ex.approved_by, 'expires': str(ex.expires) if ex.expires else None, 'status': ex.status, 'is_active': ex.is_active()} for ex in filtered]}
        if fmt == 'yaml':
            print(yaml.dump(output, default_flow_style=False))
        elif fmt == 'json':
            print(json.dumps(output, indent=2))


def run_exemptions_add(args):
    """Add a new exemption."""
    print()
    print("=" * 60)
    print("ADD EXEMPTION")
    print("=" * 60)

    repo_root = Path.cwd()
    exemptions_dir = repo_root / 'exemptions'
    exemptions_dir.mkdir(exist_ok=True)

    exemptions_file = exemptions_dir / 'exemptions.yaml'
    if exemptions_file.exists():
        with open(exemptions_file) as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {'schema_version': '1.0', 'exemptions': []}

    if 'exemptions' not in data:
        data['exemptions'] = []

    exemption_id = f"{args.contract.replace(' ', '-').lower()}-{args.check}-{date.today().isoformat()}"
    scope = {'files': [f.strip() for f in args.files.split(',')]} if args.files else {'global': True}

    exemption = {'id': exemption_id, 'contract': args.contract, 'check': args.check, 'reason': args.reason, 'approved_by': args.approved_by, 'approved_date': date.today().isoformat(), 'scope': scope, 'status': 'active'}
    if args.expires:
        exemption['expires'] = args.expires
    if args.ticket:
        exemption['ticket'] = args.ticket

    data['exemptions'].append(exemption)

    with open(exemptions_file, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    print(f"\n✅ Added exemption: {exemption_id}")
    print(f"   Contract: {args.contract}\n   Check: {args.check}\n   File: {exemptions_file}")


def run_exemptions_audit(args):
    """Audit exemptions."""
    print()
    print("=" * 60)
    print("EXEMPTION AUDIT")
    print("=" * 60)

    _ensure_contracts_tools()

    try:
        from contracts import ContractRegistry
    except ImportError as e:
        print(f"\nError: Could not import contracts module: {e}")
        sys.exit(1)

    repo_root = Path.cwd()
    registry = ContractRegistry(repo_root)
    exemptions = registry.load_exemptions()

    active = [e for e in exemptions if e.is_active()]
    expired = [e for e in exemptions if e.is_expired()]
    no_expiry = [e for e in active if e.expires is None]

    print(f"\n  Exemption Audit Summary:")
    print(f"  {'─' * 40}")
    print(f"  Total exemptions: {len(exemptions)}\n  Active: {len(active)}\n  Expired: {len(expired)}\n  Without expiration: {len(no_expiry)}")

    if args.show_expired and expired:
        print(f"\n  Expired Exemptions:")
        for ex in expired:
            print(f"    ⏰ {ex.id} (expired {ex.expires})")
            print(f"       Contract: {ex.contract}, Check: {ex.checks[0]}")

    if no_expiry:
        print(f"\n  ⚠️  Exemptions without expiration date:")
        for ex in no_expiry:
            print(f"    {ex.id}\n       Contract: {ex.contract}, Check: {ex.checks[0]}")

    if expired:
        print(f"\n  Recommendation: Review and remove expired exemptions")
