# @spec_file: .agentforge/specs/core-v1.yaml
# @spec_id: core-v1
# @component_id: core-verification-contracts-check

"""
Tests for verification contracts check helpers.

Tests the helper functions for running contract-based verification checks.
"""

from unittest.mock import Mock

import pytest

from agentforge.core.verification_contracts_check import (
    aggregate_contract_stats,
    build_contract_errors,
    build_contract_message,
)


class TestBuildContractErrors:
    """Tests for build_contract_errors function."""

    def test_build_errors_from_failed_checks(self):
        """Should extract errors from failed check results."""
        # Create mock result with failed checks
        check_result = Mock()
        check_result.passed = False
        check_result.exempted = False
        check_result.check_id = "check-001"
        check_result.severity = "error"
        check_result.message = "Something failed"
        check_result.file_path = "src/example.py"
        check_result.line_number = 42

        contract_result = Mock()
        contract_result.contract_name = "test-contract"
        contract_result.check_results = [check_result]

        errors = build_contract_errors([contract_result])

        assert len(errors) == 1
        assert errors[0]["contract"] == "test-contract"
        assert errors[0]["check"] == "check-001"
        assert errors[0]["severity"] == "error"
        assert errors[0]["message"] == "Something failed"
        assert errors[0]["file"] == "src/example.py"
        assert errors[0]["line"] == 42

    def test_build_errors_ignores_passed_checks(self):
        """Should not include passed checks in errors."""
        check_result = Mock()
        check_result.passed = True
        check_result.exempted = False

        contract_result = Mock()
        contract_result.check_results = [check_result]

        errors = build_contract_errors([contract_result])

        assert len(errors) == 0

    def test_build_errors_ignores_exempted_checks(self):
        """Should not include exempted checks in errors."""
        check_result = Mock()
        check_result.passed = False
        check_result.exempted = True

        contract_result = Mock()
        contract_result.check_results = [check_result]

        errors = build_contract_errors([contract_result])

        assert len(errors) == 0

    def test_build_errors_multiple_results(self):
        """Should handle multiple contract results."""
        check1 = Mock(passed=False, exempted=False, check_id="c1",
                      severity="error", message="Error 1", file_path="a.py", line_number=1)
        check2 = Mock(passed=False, exempted=False, check_id="c2",
                      severity="warning", message="Error 2", file_path="b.py", line_number=2)
        check3 = Mock(passed=True, exempted=False)  # Should be ignored

        result1 = Mock(contract_name="contract1", check_results=[check1])
        result2 = Mock(contract_name="contract2", check_results=[check2, check3])

        errors = build_contract_errors([result1, result2])

        assert len(errors) == 2
        assert errors[0]["check"] == "c1"
        assert errors[1]["check"] == "c2"

    def test_build_errors_empty_results(self):
        """Should handle empty results list."""
        errors = build_contract_errors([])

        assert errors == []


class TestAggregateContractStats:
    """Tests for aggregate_contract_stats function."""

    def test_aggregate_all_passed(self):
        """Should aggregate stats when all contracts pass."""
        result = Mock()
        result.errors = []
        result.warnings = []
        result.exempted_count = 0
        result.passed = True

        stats = aggregate_contract_stats([result])

        assert stats["errors"] == 0
        assert stats["warnings"] == 0
        assert stats["exempted"] == 0
        assert stats["all_passed"] is True

    def test_aggregate_with_failures(self):
        """Should aggregate stats with failures."""
        result1 = Mock(errors=["e1", "e2"], warnings=["w1"], exempted_count=1, passed=False)
        result2 = Mock(errors=["e3"], warnings=[], exempted_count=2, passed=True)

        stats = aggregate_contract_stats([result1, result2])

        assert stats["errors"] == 3
        assert stats["warnings"] == 1
        assert stats["exempted"] == 3
        assert stats["all_passed"] is False

    def test_aggregate_empty_results(self):
        """Should handle empty results list."""
        stats = aggregate_contract_stats([])

        assert stats["errors"] == 0
        assert stats["warnings"] == 0
        assert stats["exempted"] == 0
        assert stats["all_passed"] is True  # vacuously true


class TestBuildContractMessage:
    """Tests for build_contract_message function."""

    def test_build_message_no_exemptions(self):
        """Should build message without exemption count when zero."""
        results = [Mock(), Mock()]
        stats = {"errors": 2, "warnings": 1, "exempted": 0}

        message = build_contract_message(results, stats)

        assert "Ran 2 contracts" in message
        assert "2 errors" in message
        assert "1 warnings" in message
        assert "exempted" not in message

    def test_build_message_with_exemptions(self):
        """Should include exemption count when non-zero."""
        results = [Mock()]
        stats = {"errors": 0, "warnings": 0, "exempted": 5}

        message = build_contract_message(results, stats)

        assert "5 exempted" in message

    def test_build_message_no_results(self):
        """Should handle zero contracts."""
        results = []
        stats = {"errors": 0, "warnings": 0, "exempted": 0}

        message = build_contract_message(results, stats)

        assert "Ran 0 contracts" in message


class TestGetContractResults:
    """Tests for get_contract_results function.

    Note: These tests require the external 'contracts' module which is loaded
    dynamically inside the function. We skip these tests when the module is
    not available.
    """

    @pytest.mark.skip(reason="Requires external 'contracts' module")
    def test_get_results_contract_not_found(self, tmp_path):
        """Should return error when contract not found."""
        pass

    @pytest.mark.skip(reason="Requires external 'contracts' module")
    def test_get_results_with_specific_contract(self, tmp_path):
        """Should run specific contract when name provided."""
        pass

    @pytest.mark.skip(reason="Requires external 'contracts' module")
    def test_get_results_run_all_contracts(self, tmp_path):
        """Should run all contracts when no specific contract named."""
        pass
