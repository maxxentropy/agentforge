"""Contract management commands - listing, checking, validation, exemptions."""
import sys, json, click, yaml
from pathlib import Path
from datetime import date


def _ensure_contracts_tools():
    """Add tools directory to path for contracts imports."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'tools'))


def run_contracts(args):
    """Fallback for contracts without subcommand."""
    pass


def run_contracts_list(args):
    """List all contracts."""
    click.echo()
    click.echo("=" * 60)
    click.echo("CONTRACTS LIST")
    click.echo("=" * 60)

    _ensure_contracts_tools()

    try:
        from contracts import ContractRegistry
    except ImportError as e:
        click.echo(f"\nError: Could not import contracts module: {e}")
        sys.exit(1)

    repo_root = Path.cwd()
    registry = ContractRegistry(repo_root)
    contracts = registry.discover_contracts()

    filtered = _filter_contracts(contracts, args)

    if not filtered:
        click.echo("\n  No contracts found matching filters")
        return

    _output_contracts(filtered, args.format)


def _contract_matches_filter(contract, args) -> bool:
    """Check if a contract matches the filter criteria."""
    if args.tier and contract.tier != args.tier:
        return False
    if args.language:
        languages = contract.applies_to.get('languages', [])
        if args.language not in languages and languages:
            return False
    if args.type and contract.type != args.type:
        return False
    if args.tag and args.tag not in contract.tags:
        return False
    return True


def _filter_contracts(contracts: dict, args) -> list:
    """Filter contracts by tier, language, type, tag."""
    return [c for c in contracts.values() if _contract_matches_filter(c, args)]


def _output_contracts(filtered: list, fmt: str):
    """Output contracts in specified format."""
    if fmt == 'table':
        click.echo(f"\n  Found {len(filtered)} contracts:\n")
        click.echo(f"  {'Name':<30} {'Type':<15} {'Tier':<10} {'Checks':<8} {'Enabled'}")
        click.echo(f"  {'-' * 30} {'-' * 15} {'-' * 10} {'-' * 8} {'-' * 7}")
        for c in sorted(filtered, key=lambda x: (x.tier, x.name)):
            enabled = 'Y' if c.enabled else 'N'
            click.echo(f"  {c.name:<30} {c.type:<15} {c.tier:<10} {len(c.checks):<8} {enabled}")
    elif fmt == 'yaml':
        output = {'contracts': [{'name': c.name, 'type': c.type, 'tier': c.tier, 'enabled': c.enabled, 'checks': len(c.checks), 'tags': c.tags} for c in filtered]}
        click.echo(yaml.dump(output, default_flow_style=False))
    elif fmt == 'json':
        output = {'contracts': [{'name': c.name, 'type': c.type, 'tier': c.tier, 'enabled': c.enabled, 'checks': len(c.checks), 'tags': c.tags} for c in filtered]}
        click.echo(json.dumps(output, indent=2))


def run_contracts_show(args):
    """Show contract details."""
    click.echo()
    click.echo("=" * 60)
    click.echo("CONTRACT DETAILS")
    click.echo("=" * 60)

    _ensure_contracts_tools()

    try:
        from contracts import ContractRegistry
    except ImportError as e:
        click.echo(f"\nError: Could not import contracts module: {e}")
        sys.exit(1)

    repo_root = Path.cwd()
    registry = ContractRegistry(repo_root)
    contract = registry.get_contract(args.name)

    if not contract:
        click.echo(f"\nContract not found: {args.name}")
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
        click.echo(yaml.dump(output, default_flow_style=False))
    elif fmt == 'json':
        click.echo(json.dumps(output, indent=2))
    else:
        click.echo(f"\n  Contract: {contract.name}")
        click.echo(f"  Type: {contract.type}\n  Version: {contract.version}\n  Tier: {contract.tier}\n  Enabled: {contract.enabled}")
        if contract.description:
            click.echo(f"  Description: {contract.description[:80]}...")
        if contract.extends:
            click.echo(f"  Extends: {', '.join(contract.extends)}")
        click.echo(f"\n  Checks ({len(contract.all_checks())}):")
        for check in contract.all_checks():
            status = 'Y' if check.get('enabled', True) else 'N'
            click.echo(f"    [{status}] {check.get('id')}: {check.get('name')} [{check.get('type')}]")


def _get_contract_results(args, repo_root, file_paths):
    """Get contract results based on args. Returns list of results."""
    from contracts import ContractRegistry, run_contract, run_all_contracts

    if args.contract:
        registry = ContractRegistry(repo_root)
        contract = registry.get_contract(args.contract)
        if not contract:
            click.echo(f"\nContract not found: {args.contract}")
            sys.exit(1)
        return [run_contract(contract, repo_root, registry, file_paths)]

    return run_all_contracts(
        repo_root, language=args.language, repo_type=args.repo_type, file_paths=file_paths
    )


def _calculate_contract_totals(results):
    """Calculate aggregate totals from contract results."""
    return {
        "errors": sum(len(r.errors) for r in results),
        "warnings": sum(len(r.warnings) for r in results),
        "exempted": sum(r.exempted_count for r in results),
        "all_passed": all(r.passed for r in results),
    }


def run_contracts_check(args):
    """Run contract checks."""
    click.echo()
    click.echo("=" * 60)
    click.echo("CONTRACT CHECK")
    click.echo("=" * 60)

    _ensure_contracts_tools()

    try:
        repo_root = Path.cwd()
        file_paths = [(repo_root / f.strip()).resolve() for f in args.files.split(',')] if args.files else None
        results = _get_contract_results(args, repo_root, file_paths)
    except ImportError as e:
        click.echo(f"\nError: Could not import contracts module: {e}")
        sys.exit(1)

    totals = _calculate_contract_totals(results)

    _output_check_results(results, totals, args.format)

    if not totals["all_passed"] and (args.strict or totals["errors"] > 0):
        sys.exit(1)


def _output_check_results(results, totals, fmt):
    """Output check results in specified format."""
    if fmt == 'text':
        _print_contracts_text(results, totals['errors'], totals['warnings'], totals['exempted'])
    else:
        output = _build_contracts_output(results, totals)
        if fmt == 'yaml':
            click.echo(yaml.dump(output, default_flow_style=False))
        elif fmt == 'json':
            click.echo(json.dumps(output, indent=2))


def _build_contracts_output(results, totals):
    """Build structured output dict for contract results."""
    output = {
        'summary': {
            'passed': totals['all_passed'],
            'contracts_checked': len(results),
            'errors': totals['errors'],
            'warnings': totals['warnings'],
            'exempted': totals['exempted']
        },
        'results': []
    }
    for result in results:
        output['results'].append({
            'contract': result.contract_name, 'type': result.contract_type, 'passed': result.passed,
            'violations': [{'check_id': r.check_id, 'check_name': r.check_name, 'severity': r.severity, 'message': r.message, 'file': r.file_path, 'line': r.line_number, 'exempted': r.exempted, 'exemption_id': r.exemption_id} for r in result.check_results if not r.passed]
        })
    return output


def _get_check_icon(check_result) -> str:
    """Get icon for check result based on status and severity."""
    if check_result.exempted:
        return '[EX]'
    severity_icons = {'error': '[ERR]', 'warning': '[WRN]'}
    return severity_icons.get(check_result.severity, '[INF]')


def _print_check_failure(check_result):
    """Print a failed check result."""
    icon = _get_check_icon(check_result)
    click.echo(f"      {icon} {check_result.check_name}: {check_result.message}")
    if check_result.file_path:
        click.echo(f"         at {check_result.file_path}:{check_result.line_number}")
    if check_result.fix_hint:
        click.echo(f"         fix: {check_result.fix_hint}")


def _print_contracts_text(results, total_errors, total_warnings, total_exempted):
    """Print contract results in text format."""
    click.echo(f"\n  Ran {len(results)} contracts\n")
    for result in results:
        status = '[OK]' if result.passed else '[FAIL]'
        click.echo(f"  {status} {result.contract_name} ({result.contract_type})")
        for check_result in result.check_results:
            if not check_result.passed:
                _print_check_failure(check_result)
    click.echo(f"\n  Summary:\n    Errors: {total_errors}\n    Warnings: {total_warnings}\n    Exempted: {total_exempted}")


def run_contracts_init(args):
    """Initialize contract for repo."""
    click.echo()
    click.echo("=" * 60)
    click.echo("CONTRACT INIT")
    click.echo("=" * 60)

    repo_root = Path.cwd()
    contracts_dir = repo_root / 'contracts'
    contracts_dir.mkdir(exist_ok=True)

    name = args.name or repo_root.name.replace('-', '_').replace(' ', '_').lower()
    contract_path = contracts_dir / f'{name}.contract.yaml'

    if contract_path.exists():
        click.echo(f"\nContract already exists: {contract_path}")
        sys.exit(1)

    extends = args.extends or '_base'
    contract = {
        'schema_version': '1.0',
        'contract': {'name': name, 'type': args.type, 'description': f'Contract for {name} repository', 'version': '1.0.0', 'enabled': True, 'extends': extends},
        'checks': []
    }

    with open(contract_path, 'w') as f:
        yaml.dump(contract, f, default_flow_style=False, sort_keys=False)

    click.echo(f"\nCreated contract: {contract_path}")
    click.echo(f"   Extends: {extends}")
    click.echo(f"\n   Next steps:\n   1. Edit {contract_path} to add checks\n   2. Run 'python execute.py contracts check' to verify")


def run_contracts_validate(args):
    """Validate contract files."""
    click.echo()
    click.echo("=" * 60)
    click.echo("CONTRACT VALIDATE")
    click.echo("=" * 60)

    _ensure_contracts_tools()

    try:
        from contracts import ContractRegistry
    except ImportError as e:
        click.echo(f"\nError: Could not import contracts module: {e}")
        sys.exit(1)

    repo_root = Path.cwd()

    if args.file:
        _validate_single_contract(args.file)
    else:
        registry = ContractRegistry(repo_root)
        contracts = registry.discover_contracts()
        click.echo(f"\n  Validated {len(contracts)} contracts")
        for name, contract in contracts.items():
            click.echo(f"    [OK] {name} ({contract.tier})")


def _validate_single_contract(file_path: str):
    """Validate a single contract file."""
    path = Path(file_path)
    if not path.exists():
        click.echo(f"\nFile not found: {path}")
        sys.exit(1)
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
        if 'contract' not in data:
            click.echo(f"\nInvalid contract: missing 'contract' key")
            sys.exit(1)
        click.echo(f"\nContract valid: {path}")
    except Exception as e:
        click.echo(f"\nFailed to validate: {e}")
        sys.exit(1)


# --- EXEMPTION COMMANDS ---

def run_exemptions(args):
    """Fallback for exemptions without subcommand."""
    pass


def run_exemptions_list(args):
    """List all exemptions."""
    click.echo()
    click.echo("=" * 60)
    click.echo("EXEMPTIONS LIST")
    click.echo("=" * 60)

    _ensure_contracts_tools()

    try:
        from contracts import ContractRegistry
    except ImportError as e:
        click.echo(f"\nError: Could not import contracts module: {e}")
        sys.exit(1)

    repo_root = Path.cwd()
    registry = ContractRegistry(repo_root)
    exemptions = registry.load_exemptions()

    filtered = _filter_exemptions(exemptions, args)

    if not filtered:
        click.echo("\n  No exemptions found matching filters")
        return

    _output_exemptions(filtered, args.format)


def _exemption_matches_status(ex, status: str) -> bool:
    """Check if exemption matches status filter."""
    if status == 'all':
        return True
    if status == 'active':
        return ex.is_active()
    if status == 'expired':
        return ex.is_expired()
    if status == 'resolved':
        return ex.status == 'resolved'
    return True


def _filter_exemptions(exemptions, args) -> list:
    """Filter exemptions by contract and status."""
    return [ex for ex in exemptions
            if (not args.contract or ex.contract == args.contract)
            and _exemption_matches_status(ex, args.status)]


def _get_exemption_status(ex) -> str:
    """Get display status for exemption."""
    if ex.is_active():
        return 'active'
    if ex.is_expired():
        return 'expired'
    return ex.status


def _exemption_to_dict(ex) -> dict:
    """Convert exemption to dictionary for output."""
    return {
        'id': ex.id, 'contract': ex.contract, 'checks': ex.checks,
        'reason': ex.reason, 'approved_by': ex.approved_by,
        'expires': str(ex.expires) if ex.expires else None,
        'status': ex.status, 'is_active': ex.is_active()
    }


def _output_exemptions(filtered, fmt: str):
    """Output exemptions in specified format."""
    if fmt == 'table':
        click.echo(f"\n  Found {len(filtered)} exemptions:\n")
        click.echo(f"  {'ID':<25} {'Contract':<20} {'Check':<20} {'Status':<10} {'Expires'}")
        click.echo(f"  {'-' * 25} {'-' * 20} {'-' * 20} {'-' * 10} {'-' * 12}")
        for ex in filtered:
            checks_str = ex.checks[0] if len(ex.checks) == 1 else f"{ex.checks[0]}+{len(ex.checks)-1}"
            expires = str(ex.expires) if ex.expires else '-'
            click.echo(f"  {ex.id:<25} {ex.contract:<20} {checks_str:<20} {_get_exemption_status(ex):<10} {expires}")
    else:
        output = {'exemptions': [_exemption_to_dict(ex) for ex in filtered]}
        if fmt == 'yaml':
            click.echo(yaml.dump(output, default_flow_style=False))
        elif fmt == 'json':
            click.echo(json.dumps(output, indent=2))


def run_exemptions_add(args):
    """Add a new exemption."""
    click.echo()
    click.echo("=" * 60)
    click.echo("ADD EXEMPTION")
    click.echo("=" * 60)

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

    click.echo(f"\nAdded exemption: {exemption_id}")
    click.echo(f"   Contract: {args.contract}\n   Check: {args.check}\n   File: {exemptions_file}")


def _categorize_exemptions(exemptions) -> tuple:
    """Categorize exemptions by status."""
    active = [e for e in exemptions if e.is_active()]
    expired = [e for e in exemptions if e.is_expired()]
    no_expiry = [e for e in active if e.expires is None]
    return active, expired, no_expiry


def _print_audit_details(expired, no_expiry, show_expired: bool):
    """Print detailed audit findings."""
    if show_expired and expired:
        click.echo(f"\n  Expired Exemptions:")
        for ex in expired:
            click.echo(f"    [EXP] {ex.id} (expired {ex.expires})")
            click.echo(f"       Contract: {ex.contract}, Check: {ex.checks[0]}")

    if no_expiry:
        click.echo(f"\n  Exemptions without expiration date:")
        for ex in no_expiry:
            click.echo(f"    {ex.id}\n       Contract: {ex.contract}, Check: {ex.checks[0]}")

    if expired:
        click.echo(f"\n  Recommendation: Review and remove expired exemptions")


def run_exemptions_audit(args):
    """Audit exemptions."""
    click.echo()
    click.echo("=" * 60)
    click.echo("EXEMPTION AUDIT")
    click.echo("=" * 60)

    _ensure_contracts_tools()

    try:
        from contracts import ContractRegistry
    except ImportError as e:
        click.echo(f"\nError: Could not import contracts module: {e}")
        sys.exit(1)

    registry = ContractRegistry(Path.cwd())
    exemptions = registry.load_exemptions()
    active, expired, no_expiry = _categorize_exemptions(exemptions)

    click.echo(f"\n  Exemption Audit Summary:")
    click.echo(f"  {'─' * 40}")
    click.echo(f"  Total exemptions: {len(exemptions)}\n  Active: {len(active)}\n  Expired: {len(expired)}\n  Without expiration: {len(no_expiry)}")

    _print_audit_details(expired, no_expiry, args.show_expired)
