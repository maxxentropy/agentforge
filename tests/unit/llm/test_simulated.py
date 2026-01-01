# @spec_file: .agentforge/specs/core-llm-v1.yaml
# @spec_id: core-llm-v1
# @component_id: llm-simulated-tests

"""
Tests for simulated LLM client and response strategies.
"""

import pytest
import tempfile
from pathlib import Path

import yaml

from agentforge.core.llm.interface import StopReason, ToolDefinition
from agentforge.core.llm.simulated import (
    PatternMatchingStrategy,
    ScriptedResponseStrategy,
    SequentialStrategy,
    SimulatedLLMClient,
    SimulatedResponse,
    create_simple_client,
)


class TestSimulatedResponse:
    """Tests for SimulatedResponse dataclass."""

    def test_default_values(self):
        """SimulatedResponse should have sensible defaults."""
        response = SimulatedResponse()

        assert response.content == ""
        assert response.tool_calls == []
        assert response.thinking is None
        assert response.stop_reason == "end_turn"

    def test_with_tool_calls(self):
        """SimulatedResponse should store tool calls."""
        response = SimulatedResponse(
            tool_calls=[
                {"name": "read_file", "input": {"path": "test.py"}},
            ],
        )

        assert len(response.tool_calls) == 1
        assert response.tool_calls[0]["name"] == "read_file"

    def test_to_llm_response_text_only(self):
        """to_llm_response should convert text response."""
        sim = SimulatedResponse(content="Hello", stop_reason="end_turn")
        response = sim.to_llm_response(call_index=0)

        assert response.content == "Hello"
        assert response.stop_reason == StopReason.END_TURN
        assert response.tool_calls == []

    def test_to_llm_response_with_tools(self):
        """to_llm_response should convert tool calls."""
        sim = SimulatedResponse(
            content="",
            tool_calls=[
                {"name": "write_file", "input": {"path": "x.py", "content": "test"}},
            ],
        )
        response = sim.to_llm_response(call_index=1)

        assert response.stop_reason == StopReason.TOOL_USE
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].name == "write_file"
        assert response.tool_calls[0].input["path"] == "x.py"
        assert response.tool_calls[0].id == "sim_1_0"

    def test_to_llm_response_with_thinking(self):
        """to_llm_response should include thinking content."""
        sim = SimulatedResponse(
            content="Done",
            thinking="Let me analyze this...",
        )
        response = sim.to_llm_response()

        assert response.thinking == "Let me analyze this..."


class TestScriptedResponseStrategy:
    """Tests for ScriptedResponseStrategy."""

    def test_from_script_data(self):
        """Strategy should load from script dict."""
        script = {
            "responses": [
                {"content": "First response"},
                {"content": "Second response"},
            ],
        }
        strategy = ScriptedResponseStrategy(script_data=script)

        r1 = strategy.get_response("", [], [], {})
        r2 = strategy.get_response("", [], [], {})

        assert r1.content == "First response"
        assert r2.content == "Second response"

    def test_from_yaml_file(self):
        """Strategy should load from YAML file."""
        script = {
            "metadata": {"name": "Test Script"},
            "responses": [
                {"tool_calls": [{"name": "test", "input": {}}]},
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(script, f)
            f.flush()

            strategy = ScriptedResponseStrategy(script_path=Path(f.name))
            response = strategy.get_response("", [], [], {})

            assert len(response.tool_calls) == 1
            assert response.tool_calls[0]["name"] == "test"

    def test_exhausted_script(self):
        """Strategy should return completion when script exhausted."""
        strategy = ScriptedResponseStrategy(script_data={"responses": []})

        response = strategy.get_response("", [], [], {})

        assert "complete" in [tc["name"] for tc in response.tool_calls]

    def test_reset(self):
        """reset should replay script from beginning."""
        strategy = ScriptedResponseStrategy(
            script_data={
                "responses": [
                    {"content": "First"},
                    {"content": "Second"},
                ],
            }
        )

        strategy.get_response("", [], [], {})
        strategy.get_response("", [], [], {})
        strategy.reset()

        response = strategy.get_response("", [], [], {})
        assert response.content == "First"

    def test_remaining_responses(self):
        """remaining_responses should track progress."""
        strategy = ScriptedResponseStrategy(
            script_data={
                "responses": [
                    {"content": "1"},
                    {"content": "2"},
                    {"content": "3"},
                ],
            }
        )

        assert strategy.remaining_responses == 3
        strategy.get_response("", [], [], {})
        assert strategy.remaining_responses == 2


class TestSequentialStrategy:
    """Tests for SequentialStrategy."""

    def test_returns_in_order(self):
        """Strategy should return responses in sequence."""
        responses = [
            SimulatedResponse(content="First"),
            SimulatedResponse(content="Second"),
            SimulatedResponse(content="Third"),
        ]
        strategy = SequentialStrategy(responses)

        assert strategy.get_response("", [], [], {}).content == "First"
        assert strategy.get_response("", [], [], {}).content == "Second"
        assert strategy.get_response("", [], [], {}).content == "Third"

    def test_exhausted_sequence(self):
        """Strategy should complete when sequence exhausted."""
        strategy = SequentialStrategy([
            SimulatedResponse(content="Only one"),
        ])

        strategy.get_response("", [], [], {})  # Consume the one
        response = strategy.get_response("", [], [], {})

        assert "complete" in [tc["name"] for tc in response.tool_calls]

    def test_reset(self):
        """reset should replay from beginning."""
        strategy = SequentialStrategy([
            SimulatedResponse(content="First"),
        ])

        strategy.get_response("", [], [], {})
        strategy.reset()

        assert strategy.get_response("", [], [], {}).content == "First"


class TestPatternMatchingStrategy:
    """Tests for PatternMatchingStrategy."""

    def test_matches_pattern(self):
        """Strategy should return response when pattern matches."""
        strategy = PatternMatchingStrategy()
        strategy.add_pattern(
            lambda ctx: "error" in str(ctx.get("messages", [])).lower(),
            SimulatedResponse(content="Error detected!"),
        )

        response = strategy.get_response(
            system="",
            messages=[{"role": "user", "content": "There is an error"}],
            tools=[],
            context={},
        )

        assert response.content == "Error detected!"

    def test_default_when_no_match(self):
        """Strategy should use default when no patterns match."""
        strategy = PatternMatchingStrategy()
        strategy.add_pattern(
            lambda ctx: False,  # Never matches
            SimulatedResponse(content="Matched"),
        )

        response = strategy.get_response("", [], [], {})

        assert "escalate" in [tc["name"] for tc in response.tool_calls]

    def test_custom_default(self):
        """set_default should override default response."""
        strategy = PatternMatchingStrategy()
        strategy.set_default(SimulatedResponse(content="Custom default"))

        response = strategy.get_response("", [], [], {})

        assert response.content == "Custom default"

    def test_chaining(self):
        """Methods should support chaining."""
        strategy = (
            PatternMatchingStrategy()
            .add_pattern(lambda _: False, SimulatedResponse())
            .set_default(SimulatedResponse(content="Chained"))
        )

        assert strategy.get_response("", [], [], {}).content == "Chained"


class TestSimulatedLLMClient:
    """Tests for SimulatedLLMClient."""

    def test_basic_complete(self):
        """Client should return simulated response."""
        client = SimulatedLLMClient(
            default_response=SimulatedResponse(content="Default response"),
        )

        response = client.complete(
            system="Test system",
            messages=[{"role": "user", "content": "Hello"}],
        )

        assert response.content == "Default response"

    def test_with_strategy(self):
        """Client should use strategy for responses."""
        strategy = SequentialStrategy([
            SimulatedResponse(content="From strategy"),
        ])
        client = SimulatedLLMClient(strategy=strategy)

        response = client.complete(system="", messages=[])

        assert response.content == "From strategy"

    def test_usage_tracking(self):
        """Client should track usage statistics."""
        client = SimulatedLLMClient()

        client.complete(system="", messages=[])
        client.complete(system="", messages=[])

        stats = client.get_usage_stats()
        assert stats["call_count"] == 2
        assert stats["total_input_tokens"] == 200  # 100 per call

    def test_call_history(self):
        """Client should record call history."""
        client = SimulatedLLMClient()

        client.complete(
            system="Test prompt",
            messages=[{"role": "user", "content": "Hello"}],
            tools=[ToolDefinition("test", "A test tool", {})],
        )

        history = client.get_call_history()
        assert len(history) == 1
        assert history[0]["system"] == "Test prompt"
        assert history[0]["tools"] == ["test"]

    def test_reset(self):
        """reset should clear all state."""
        strategy = SequentialStrategy([
            SimulatedResponse(content="First"),
            SimulatedResponse(content="Second"),
        ])
        client = SimulatedLLMClient(strategy=strategy)

        client.complete(system="", messages=[])
        client.reset()

        assert client.get_usage_stats()["call_count"] == 0
        assert client.get_call_history() == []
        assert client.complete(system="", messages=[]).content == "First"

    def test_no_strategy_uses_default(self):
        """Client without strategy should use default response."""
        client = SimulatedLLMClient()

        response = client.complete(system="", messages=[])

        assert "no strategy configured" in response.content.lower()


class TestCreateSimpleClient:
    """Tests for create_simple_client helper function."""

    def test_creates_working_client(self):
        """Helper should create functional client."""
        client = create_simple_client([
            {"content": "Response 1"},
            {"tool_calls": [{"name": "test", "input": {}}]},
        ])

        r1 = client.complete(system="", messages=[])
        r2 = client.complete(system="", messages=[])

        assert r1.content == "Response 1"
        assert r2.tool_calls[0].name == "test"

    def test_with_thinking(self):
        """Helper should support thinking field."""
        client = create_simple_client([
            {"content": "Done", "thinking": "Let me think..."},
        ])

        response = client.complete(system="", messages=[])

        assert response.thinking == "Let me think..."
