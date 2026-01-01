#!/usr/bin/env python3
# @spec_file: specs/minimal-context-architecture/08-testing.yaml
# @spec_id: mutation-testing-v1
# @component_id: mutation-test-runner

"""
Mutation Testing Runner for Critical Paths
==========================================

Runs mutation testing on critical code paths to verify test coverage quality.

Installation:
    pip install mutmut

Usage:
    python tools/run_mutation_tests.py [--quick] [--module MODULE]

Options:
    --quick     Run on a subset of critical paths (faster)
    --module    Target a specific module for mutation testing
    --report    Generate HTML report after testing

Example:
    # Full mutation test run (slow but comprehensive)
    python tools/run_mutation_tests.py

    # Quick run on core modules only
    python tools/run_mutation_tests.py --quick

    # Test specific module
    python tools/run_mutation_tests.py --module adaptive_budget
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Critical paths that should have strong mutation coverage
CRITICAL_PATHS = {
    "step_outcome": "src/agentforge/core/harness/minimal_context/step_outcome.py",
    "adaptive_budget": "src/agentforge/core/harness/minimal_context/adaptive_budget.py",
    "loop_detector": "src/agentforge/core/harness/minimal_context/loop_detector.py",
    "phase_machine": "src/agentforge/core/harness/minimal_context/phase_machine.py",
    "state_store": "src/agentforge/core/harness/minimal_context/state_store.py",
    "compaction": "src/agentforge/core/context/compaction.py",
    "audit": "src/agentforge/core/context/audit.py",
}

# Quick paths for faster iteration
QUICK_PATHS = {
    "step_outcome": CRITICAL_PATHS["step_outcome"],
    "adaptive_budget": CRITICAL_PATHS["adaptive_budget"],
    "loop_detector": CRITICAL_PATHS["loop_detector"],
}

# Test directories that cover the critical paths
TEST_DIRS = {
    "step_outcome": "tests/unit/harness/test_executor.py tests/unit/harness/test_executor_edge_cases.py",
    "adaptive_budget": "tests/unit/harness/test_executor.py tests/unit/harness/test_executor_edge_cases.py",
    "loop_detector": "tests/unit/harness/test_loop_detector.py",
    "phase_machine": "tests/unit/harness/test_phase_machine.py",
    "state_store": "tests/unit/harness/test_state_store.py",
    "compaction": "tests/unit/context/test_compaction.py",
    "audit": "tests/unit/context/test_audit.py",
}


def check_mutmut_installed() -> bool:
    """Check if mutmut is installed."""
    try:
        subprocess.run(
            ["mutmut", "--version"],
            capture_output=True,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def run_mutation_test(module: str, path: str, tests: str) -> int:
    """
    Run mutation testing on a specific module.

    Returns:
        Exit code from mutmut
    """
    print(f"\n{'='*60}")
    print(f"Mutation testing: {module}")
    print(f"Path: {path}")
    print(f"Tests: {tests}")
    print(f"{'='*60}\n")

    cmd = [
        "mutmut",
        "run",
        "--paths-to-mutate", path,
        "--tests-dir", tests.split()[0].rsplit("/", 1)[0],  # Get test directory
        "--runner", f"python -m pytest -x -q {tests}",
    ]

    result = subprocess.run(cmd)
    return result.returncode


def show_results() -> None:
    """Show mutation testing results."""
    print("\n" + "="*60)
    print("Mutation Testing Results")
    print("="*60 + "\n")

    subprocess.run(["mutmut", "results"])


def generate_report() -> None:
    """Generate HTML report."""
    print("\nGenerating HTML report...")
    subprocess.run(["mutmut", "html"])
    print("Report generated: html/index.html")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run mutation testing on critical paths"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run on subset of critical paths (faster)"
    )
    parser.add_argument(
        "--module",
        type=str,
        choices=list(CRITICAL_PATHS.keys()),
        help="Target specific module"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate HTML report after testing"
    )
    parser.add_argument(
        "--results-only",
        action="store_true",
        help="Show results from previous run"
    )

    args = parser.parse_args()

    # Check mutmut installation
    if not check_mutmut_installed():
        print("ERROR: mutmut is not installed.")
        print("Install with: pip install mutmut")
        return 1

    # Just show results?
    if args.results_only:
        show_results()
        return 0

    # Determine which paths to test
    if args.module:
        paths = {args.module: CRITICAL_PATHS[args.module]}
    elif args.quick:
        paths = QUICK_PATHS
    else:
        paths = CRITICAL_PATHS

    # Run mutation tests
    failed = []
    for module, path in paths.items():
        tests = TEST_DIRS.get(module, "tests/unit/")
        exit_code = run_mutation_test(module, path, tests)
        if exit_code != 0:
            failed.append(module)

    # Show results
    show_results()

    # Generate report if requested
    if args.report:
        generate_report()

    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    print(f"Modules tested: {len(paths)}")
    if failed:
        print(f"Modules with surviving mutants: {', '.join(failed)}")
        print("\nTo improve mutation coverage:")
        print("1. Run: mutmut show <id> to see surviving mutants")
        print("2. Add tests that would catch the mutated behavior")
        print("3. Re-run mutation tests to verify coverage")
    else:
        print("All mutations killed! ✓")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
