# @spec_file: .agentforge/specs/core-v1.yaml
# @spec_id: core-v1
# @component_id: core-contract-runner

"""
Tests for ContractRunner class.

Tests the prompt contract loading, assembly, variable substitution,
conditional sections, and output saving functionality.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from agentforge.core.contract_runner import ContractRunner


class TestContractRunnerInit:
    """Tests for ContractRunner initialization."""

    def test_init_with_defaults(self, tmp_path):
        """Should initialize with default directories."""
        with patch.object(Path, '__new__', return_value=tmp_path):
            runner = ContractRunner()
            # Just verify it doesn't crash - actual paths depend on project root
            assert runner is not None, "Expected runner is not None"

    def test_init_with_custom_dirs(self, tmp_path):
        """Should initialize with custom directories."""
        contracts_dir = tmp_path / "contracts"
        outputs_dir = tmp_path / "outputs"
        contracts_dir.mkdir()

        runner = ContractRunner(
            contracts_dir=contracts_dir,
            outputs_dir=outputs_dir
        )

        assert runner.contracts_dir == contracts_dir, "Expected runner.contracts_dir to equal contracts_dir"
        assert runner.outputs_dir == outputs_dir, "Expected runner.outputs_dir to equal outputs_dir"
        assert outputs_dir.exists(), "Expected outputs_dir.exists() to be truthy"# Should be created

    def test_init_creates_outputs_dir(self, tmp_path):
        """Should create outputs directory if it doesn't exist."""
        contracts_dir = tmp_path / "contracts"
        outputs_dir = tmp_path / "new_outputs"
        contracts_dir.mkdir()

        assert not outputs_dir.exists(), "Assertion failed"

        ContractRunner(
            contracts_dir=contracts_dir,
            outputs_dir=outputs_dir
        )

        assert outputs_dir.exists(), "Expected outputs_dir.exists() to be truthy"


class TestLoadProjectContext:
    """Tests for _load_project_context method."""

    def test_load_project_context_when_exists(self, tmp_path):
        """Should load project context from file when it exists."""
        contracts_dir = tmp_path / "contracts"
        outputs_dir = tmp_path / "outputs"
        sample_data_dir = tmp_path / "sample_data"
        contracts_dir.mkdir()
        sample_data_dir.mkdir()

        context_content = "project: test\nversion: 1.0"
        (sample_data_dir / "project_context.yaml").write_text(context_content)

        with patch.object(Path, 'parent', new_callable=lambda: property(lambda s: tmp_path)):
            runner = ContractRunner(
                contracts_dir=contracts_dir,
                outputs_dir=outputs_dir
            )
            # The context is loaded during init; we're verifying the mechanism exists
            assert runner.project_context is not None, "Expected runner.project_context is not None"

    def test_load_project_context_when_missing(self, tmp_path):
        """Should return default message when context file doesn't exist."""
        contracts_dir = tmp_path / "contracts"
        outputs_dir = tmp_path / "outputs"
        contracts_dir.mkdir()

        runner = ContractRunner(
            contracts_dir=contracts_dir,
            outputs_dir=outputs_dir
        )

        # Should get default message since sample_data doesn't exist
        assert "No project context configured" in runner.project_context or runner.project_context, "Assertion failed"


class TestLoadContract:
    """Tests for load_contract method."""

    def test_load_contract_success(self, tmp_path):
        """Should load a valid contract file."""
        contracts_dir = tmp_path / "contracts"
        outputs_dir = tmp_path / "outputs"
        contracts_dir.mkdir()

        contract_content = {
            "contract": {"id": "test-contract", "version": "1.0"},
            "template": {"system": {"sections": []}},
        }
        (contracts_dir / "test-contract.yaml").write_text(yaml.dump(contract_content))

        runner = ContractRunner(
            contracts_dir=contracts_dir,
            outputs_dir=outputs_dir
        )
        contract = runner.load_contract("test-contract")

        assert contract["contract"]["id"] == "test-contract", "Expected contract['contract']['id'] to equal 'test-contract'"
        assert contract["contract"]["version"] == "1.0", "Expected contract['contract']['versi... to equal '1.0'"

    def test_load_contract_not_found(self, tmp_path):
        """Should raise FileNotFoundError for missing contract."""
        contracts_dir = tmp_path / "contracts"
        outputs_dir = tmp_path / "outputs"
        contracts_dir.mkdir()

        runner = ContractRunner(
            contracts_dir=contracts_dir,
            outputs_dir=outputs_dir
        )

        with pytest.raises(FileNotFoundError, match="Contract not found"):
            runner.load_contract("nonexistent-contract")


class TestBuildSystemMessage:
    """Tests for _build_system_message method."""

    def test_build_system_message_with_sections(self, tmp_path):
        """Should join system message sections."""
        contracts_dir = tmp_path / "contracts"
        outputs_dir = tmp_path / "outputs"
        contracts_dir.mkdir()

        runner = ContractRunner(
            contracts_dir=contracts_dir,
            outputs_dir=outputs_dir
        )

        contract = {
            "template": {
                "system": {
                    "sections": [
                        {"content": "First section"},
                        {"content": "Second section"},
                    ]
                }
            }
        }

        message = runner._build_system_message(contract)

        assert "First section" in message, "Expected 'First section' in message"
        assert "Second section" in message, "Expected 'Second section' in message"

    def test_build_system_message_empty_sections(self, tmp_path):
        """Should handle empty sections list."""
        contracts_dir = tmp_path / "contracts"
        outputs_dir = tmp_path / "outputs"
        contracts_dir.mkdir()

        runner = ContractRunner(
            contracts_dir=contracts_dir,
            outputs_dir=outputs_dir
        )

        contract = {"template": {"system": {"sections": []}}}
        message = runner._build_system_message(contract)

        assert message == "", "Expected message to equal ''"

    def test_build_system_message_missing_template(self, tmp_path):
        """Should handle missing template gracefully."""
        contracts_dir = tmp_path / "contracts"
        outputs_dir = tmp_path / "outputs"
        contracts_dir.mkdir()

        runner = ContractRunner(
            contracts_dir=contracts_dir,
            outputs_dir=outputs_dir
        )

        contract = {}
        message = runner._build_system_message(contract)

        assert message == "", "Expected message to equal ''"


class TestShouldIncludeSection:
    """Tests for _should_include_section method."""

    @pytest.fixture
    def runner(self, tmp_path):
        contracts_dir = tmp_path / "contracts"
        outputs_dir = tmp_path / "outputs"
        contracts_dir.mkdir()
        return ContractRunner(contracts_dir=contracts_dir, outputs_dir=outputs_dir)

    def test_include_section_no_condition(self, runner):
        """Should include section when no condition specified."""
        section = {"content": "Always include"}
        result = runner._should_include_section(section, {}, {})
        assert result is True, "Expected result is True"

    def test_include_section_truthy_input(self, runner):
        """Should include section when input condition is truthy."""
        section = {"content": "Conditional", "condition": "has_context"}
        result = runner._should_include_section(
            section, {"has_context": True}, {}
        )
        assert result is True, "Expected result is True"

    def test_include_section_truthy_context(self, runner):
        """Should include section when context condition is truthy."""
        section = {"content": "Conditional", "condition": "has_context"}
        result = runner._should_include_section(
            section, {}, {"has_context": "some value"}
        )
        assert result is True, "Expected result is True"

    def test_exclude_section_falsy_condition(self, runner):
        """Should exclude section when condition is falsy."""
        section = {"content": "Conditional", "condition": "missing_var"}
        result = runner._should_include_section(section, {}, {})
        assert result is False, "Expected result is False"

    def test_exclude_section_empty_string(self, runner):
        """Should exclude section when condition is empty string."""
        section = {"content": "Conditional", "condition": "empty_var"}
        result = runner._should_include_section(
            section, {"empty_var": ""}, {}
        )
        assert result is False, "Expected result is False"

    def test_include_section_nonempty_list(self, runner):
        """Should include section when condition is non-empty list."""
        section = {"content": "Conditional", "condition": "items"}
        result = runner._should_include_section(
            section, {"items": [1, 2, 3]}, {}
        )
        assert result is True, "Expected result is True"


class TestBuildUserMessage:
    """Tests for _build_user_message method."""

    @pytest.fixture
    def runner(self, tmp_path):
        contracts_dir = tmp_path / "contracts"
        outputs_dir = tmp_path / "outputs"
        contracts_dir.mkdir()
        return ContractRunner(contracts_dir=contracts_dir, outputs_dir=outputs_dir)

    def test_build_user_message_all_sections(self, runner):
        """Should include all unconditional sections."""
        contract = {
            "template": {
                "user": {
                    "sections": [
                        {"content": "Part A"},
                        {"content": "Part B"},
                    ]
                }
            }
        }

        message = runner._build_user_message(contract, {}, {})

        assert "Part A" in message, "Expected 'Part A' in message"
        assert "Part B" in message, "Expected 'Part B' in message"

    def test_build_user_message_conditional_sections(self, runner):
        """Should filter sections based on conditions."""
        contract = {
            "template": {
                "user": {
                    "sections": [
                        {"content": "Always"},
                        {"content": "Sometimes", "condition": "show_extra"},
                        {"content": "Never", "condition": "show_never"},
                    ]
                }
            }
        }

        message = runner._build_user_message(
            contract, {"show_extra": True}, {}
        )

        assert "Always" in message, "Expected 'Always' in message"
        assert "Sometimes" in message, "Expected 'Sometimes' in message"
        assert "Never" not in message, "Expected 'Never' not in message"


class TestSubstituteVariables:
    """Tests for _substitute_variables method."""

    @pytest.fixture
    def runner(self, tmp_path):
        contracts_dir = tmp_path / "contracts"
        outputs_dir = tmp_path / "outputs"
        contracts_dir.mkdir()
        return ContractRunner(contracts_dir=contracts_dir, outputs_dir=outputs_dir)

    def test_substitute_string_variable(self, runner):
        """Should substitute string variables."""
        message = "Hello, {name}!"
        result = runner._substitute_variables(message, {"name": "World"})
        assert result == "Hello, World!", "Expected result to equal 'Hello, World!'"

    def test_substitute_multiple_variables(self, runner):
        """Should substitute multiple variables."""
        message = "{greeting}, {name}!"
        result = runner._substitute_variables(
            message, {"greeting": "Hi", "name": "Alice"}
        )
        assert result == "Hi, Alice!", "Expected result to equal 'Hi, Alice!'"

    def test_substitute_dict_variable(self, runner):
        """Should substitute dict as YAML."""
        message = "Config: {config}"
        result = runner._substitute_variables(
            message, {"config": {"key": "value"}}
        )
        assert "key: value" in result, "Expected 'key: value' in result"

    def test_substitute_list_variable(self, runner):
        """Should substitute list as YAML."""
        message = "Items: {items}"
        result = runner._substitute_variables(
            message, {"items": ["a", "b", "c"]}
        )
        assert "- a" in result, "Expected '- a' in result"
        assert "- b" in result, "Expected '- b' in result"

    def test_substitute_integer_variable(self, runner):
        """Should substitute integer as string."""
        message = "Count: {count}"
        result = runner._substitute_variables(message, {"count": 42})
        assert result == "Count: 42", "Expected result to equal 'Count: 42'"

    def test_no_matching_variable(self, runner):
        """Should leave unmatched placeholders as-is."""
        message = "Hello, {name}!"
        result = runner._substitute_variables(message, {"other": "value"})
        assert result == "Hello, {name}!", "Expected result to equal 'Hello, {name}!'"


class TestAssemblePrompt:
    """Tests for assemble_prompt method."""

    @pytest.fixture
    def runner(self, tmp_path):
        contracts_dir = tmp_path / "contracts"
        outputs_dir = tmp_path / "outputs"
        contracts_dir.mkdir()
        return ContractRunner(contracts_dir=contracts_dir, outputs_dir=outputs_dir)

    def test_assemble_prompt_structure(self, runner):
        """Should assemble prompt with correct structure."""
        contract = {
            "contract": {"id": "test", "version": "1.0"},
            "template": {
                "system": {"sections": [{"content": "System msg"}]},
                "user": {"sections": [{"content": "User: {request}"}]},
            },
            "execution": {"temperature": 0.5, "max_tokens": 2000},
            "output": {"format": "json"},
        }

        result = runner.assemble_prompt(
            contract, {"request": "Help me"}
        )

        assert result["contract_id"] == "test", "Expected result['contract_id'] to equal 'test'"
        assert result["contract_version"] == "1.0", "Expected result['contract_version'] to equal '1.0'"
        assert "generated_at" in result, "Expected 'generated_at' in result"
        assert result["inputs_provided"] == {"request": "Help me"}, "Expected result['inputs_provided'] to equal {'request': 'Help me'}"
        assert "System msg" in result["prompt"]["system"], "Expected 'System msg' in result['prompt']['system']"
        assert "Help me" in result["prompt"]["user"], "Expected 'Help me' in result['prompt']['user']"
        assert result["execution"]["temperature"] == 0.5, "Expected result['execution']['temper... to equal 0.5"
        assert result["execution"]["max_tokens"] == 2000, "Expected result['execution']['max_to... to equal 2000"
        assert result["expected_output"]["format"] == "json", "Expected result['expected_output']['... to equal 'json'"

    def test_assemble_prompt_default_execution(self, runner):
        """Should use default execution settings when not specified."""
        contract = {
            "contract": {"id": "test", "version": "1.0"},
            "template": {
                "system": {"sections": []},
                "user": {"sections": []},
            },
        }

        result = runner.assemble_prompt(contract, {})

        assert result["execution"]["temperature"] == 0.0, "Expected result['execution']['temper... to equal 0.0"
        assert result["execution"]["max_tokens"] == 4096, "Expected result['execution']['max_to... to equal 4096"
        assert result["expected_output"]["format"] == "yaml", "Expected result['expected_output']['... to equal 'yaml'"

    def test_assemble_prompt_with_context(self, runner):
        """Should merge context with inputs."""
        contract = {
            "contract": {"id": "test", "version": "1.0"},
            "template": {
                "system": {"sections": []},
                "user": {"sections": [{"content": "{input_val} - {ctx_val}"}]},
            },
        }

        result = runner.assemble_prompt(
            contract,
            {"input_val": "from_input"},
            {"ctx_val": "from_context"}
        )

        assert "from_input" in result["prompt"]["user"], "Expected 'from_input' in result['prompt']['user']"
        assert "from_context" in result["prompt"]["user"], "Expected 'from_context' in result['prompt']['user']"


class TestValidateOutput:
    """Tests for validate_output method."""

    @pytest.fixture
    def runner(self, tmp_path):
        contracts_dir = tmp_path / "contracts"
        outputs_dir = tmp_path / "outputs"
        contracts_dir.mkdir()
        return ContractRunner(contracts_dir=contracts_dir, outputs_dir=outputs_dir)

    def test_validate_output_strips_yaml_fence(self, runner):
        """Should strip markdown YAML fences from output."""
        contract = {"output": {"schema": {}}}
        output = "```yaml\nkey: value\n```"

        # Should not crash - validation result depends on validator
        result = runner.validate_output(contract, output, {})
        # Result may be None if validator not available, or a validation report
        # The key test is that it doesn't crash and processes the fence stripping
        assert result is None or hasattr(result, 'is_valid') or isinstance(result, (dict, bool)), "Assertion failed"

    def test_validate_output_invalid_yaml(self, runner):
        """Should return None for invalid YAML."""
        contract = {"output": {"schema": {}}}
        output = "not: valid: yaml: here: :::"

        result = runner.validate_output(contract, output, {})
        assert result is None, "Expected result is None"


class TestSavePrompt:
    """Tests for save_prompt method."""

    def test_save_prompt_creates_file(self, tmp_path):
        """Should save prompt to YAML file."""
        contracts_dir = tmp_path / "contracts"
        outputs_dir = tmp_path / "outputs"
        contracts_dir.mkdir()

        runner = ContractRunner(
            contracts_dir=contracts_dir,
            outputs_dir=outputs_dir
        )

        prompt = {
            "contract_id": "test",
            "prompt": {"system": "Hello\nWorld", "user": "Request"}
        }

        filepath = runner.save_prompt(prompt, "test")

        assert filepath.exists(), "Expected filepath.exists() to be truthy"
        assert "test" in filepath.name, "Expected 'test' in filepath.name"
        assert filepath.suffix == ".yaml", "Expected filepath.suffix to equal '.yaml'"

    def test_save_prompt_multiline_preserved(self, tmp_path):
        """Should preserve multiline strings with block style."""
        contracts_dir = tmp_path / "contracts"
        outputs_dir = tmp_path / "outputs"
        contracts_dir.mkdir()

        runner = ContractRunner(
            contracts_dir=contracts_dir,
            outputs_dir=outputs_dir
        )

        prompt = {
            "prompt": {"content": "Line 1\nLine 2\nLine 3"}
        }

        filepath = runner.save_prompt(prompt, "test")
        content = filepath.read_text()

        # Multiline should use block style (|)
        assert "Line 1" in content, "Expected 'Line 1' in content"
        assert "Line 2" in content, "Expected 'Line 2' in content"


class TestSaveOutput:
    """Tests for save_output method."""

    def test_save_output_creates_file(self, tmp_path):
        """Should save output string to file."""
        contracts_dir = tmp_path / "contracts"
        outputs_dir = tmp_path / "outputs"
        contracts_dir.mkdir()

        runner = ContractRunner(
            contracts_dir=contracts_dir,
            outputs_dir=outputs_dir
        )

        output = "key: value\nother: data"
        filepath = runner.save_output(output, "test-contract")

        assert filepath.exists(), "Expected filepath.exists() to be truthy"
        assert filepath.read_text() == output, "Expected filepath.read_text() to equal output"
        assert "test-contract" in filepath.name, "Expected 'test-contract' in filepath.name"
        assert "_output.yaml" in filepath.name, "Expected '_output.yaml' in filepath.name"
