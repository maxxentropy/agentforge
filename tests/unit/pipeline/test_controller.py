# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_file: .agentforge/specs/core-pipeline-v1.yaml
# @spec_id: core-pipeline-v1
# @spec_id: core-pipeline-v1
# @component_id: pipeline-controller

"""Tests for PipelineController."""

import pytest

from agentforge.core.pipeline import (
    PassthroughExecutor,
    PipelineController,
    PipelineNotFoundError,
    PipelineResult,
    PipelineStateError,
    PipelineStatus,
    StageExecutor,
    StageResult,
    StageStatus,
)


class TestPipelineController:
    """Tests for PipelineController core functionality."""

    def test_execute_creates_and_runs(self, controller):
        """execute() creates and runs pipeline to completion."""
        result = controller.execute("Test request")

        assert result.success is True, "Expected result.success is True"
        assert result.pipeline_id.startswith("PL-"), "Expected result.pipeline_id.startswith() to be truthy"
        assert len(result.stages_completed) > 0, "Expected len(result.stages_completed) > 0"

    def test_execute_with_template(self, controller):
        """execute() respects template parameter."""
        result = controller.execute("Test request", template="design")

        assert result.success is True, "Expected result.success is True"
        state = controller.get_status(result.pipeline_id)
        assert state.template == "design", "Expected state.template to equal 'design'"

    def test_execute_with_config(self, controller):
        """execute() passes config to pipeline."""
        result = controller.execute(
            "Test request",
            config={"supervised": True, "custom_key": "value"}
        )

        assert result.success is True, "Expected result.success is True"
        state = controller.get_status(result.pipeline_id)
        assert state.config.get("custom_key") == "value", "Expected state.config.get('custom_key') to equal 'value'"

    def test_execute_single_stage(self, temp_project, fresh_registry):
        """execute() runs through stages."""
        # Template "test" requires: ["analyze", "red"]
        fresh_registry.register("analyze", lambda: PassthroughExecutor("analyze"))
        fresh_registry.register("red", lambda: PassthroughExecutor("red"))

        controller = PipelineController(
            project_path=temp_project,
            registry=fresh_registry,
        )

        result = controller.execute("Test", template="test")

        assert result.success is True, "Expected result.success is True"
        state = controller.get_status(result.pipeline_id)
        assert state.status == PipelineStatus.COMPLETED, "Expected state.status to equal PipelineStatus.COMPLETED"

    def test_execute_multi_stage(self, controller):
        """execute() runs through multiple stages in order."""
        result = controller.execute("Multi-stage test")

        assert result.success is True, "Expected result.success is True"
        state = controller.get_status(result.pipeline_id)
        assert state.status == PipelineStatus.COMPLETED, "Expected state.status to equal PipelineStatus.COMPLETED"

        for stage_name in state.stage_order:
            stage = state.stages[stage_name]
            assert stage.status == StageStatus.COMPLETED, "Expected stage.status to equal StageStatus.COMPLETED"

    def test_execute_with_failure(self, temp_project, fresh_registry):
        """execute() stops on stage failure."""

        class FailingExecutor(StageExecutor):
            def execute(self, context):
                return StageResult.failed("Intentional failure")

        fresh_registry.register("intake", lambda: PassthroughExecutor("intake"))
        fresh_registry.register("clarify", FailingExecutor)

        controller = PipelineController(
            project_path=temp_project,
            registry=fresh_registry,
        )

        result = controller.execute("Test", template="design")

        assert result.success is False, "Expected result.success is False"
        assert result.error == "Intentional failure", "Expected result.error to equal 'Intentional failure'"
        state = controller.get_status(result.pipeline_id)
        assert state.status == PipelineStatus.FAILED, "Expected state.status to equal PipelineStatus.FAILED"

    def test_execute_with_escalation(self, temp_project, fresh_registry):
        """execute() pauses on escalation."""

        class EscalatingExecutor(StageExecutor):
            def execute(self, context):
                return StageResult.escalate(
                    escalation_type="approval_required",
                    message="Please approve",
                )

        fresh_registry.register("intake", EscalatingExecutor)
        fresh_registry.register("clarify", lambda: PassthroughExecutor("clarify"))
        fresh_registry.register("analyze", lambda: PassthroughExecutor("analyze"))
        fresh_registry.register("spec", lambda: PassthroughExecutor("spec"))

        controller = PipelineController(
            project_path=temp_project,
            registry=fresh_registry,
        )

        result = controller.execute("Test", template="design")

        assert result.success is False, "Expected result.success is False"# Not complete yet
        state = controller.get_status(result.pipeline_id)
        assert state.status == PipelineStatus.WAITING_APPROVAL, "Expected state.status to equal PipelineStatus.WAITING_APPR..."

        pending = controller.escalation_handler.get_pending(state.pipeline_id)
        assert len(pending) == 1, "Expected len(pending) to equal 1"

    def test_pause_and_resume(self, temp_project, full_registry):
        """pause() and resume() work correctly."""
        controller = PipelineController(temp_project, registry=full_registry)

        # Create a pipeline and set it to running
        result = controller.execute("Test", template="design")
        controller.get_status(result.pipeline_id)

        # Can't pause completed
        paused = controller.pause(result.pipeline_id)
        assert paused is False, "Expected paused is False"

    def test_resume_paused_pipeline(self, temp_project, full_registry):
        """resume() continues paused pipeline."""
        controller = PipelineController(temp_project, registry=full_registry)

        # Create and pause manually
        state = controller._create("Test", "design", {})
        state.status = PipelineStatus.PAUSED
        state.current_stage = "clarify"
        state.stages["intake"].mark_completed({"done": True})
        controller.state_store.save(state)

        result = controller.resume(state.pipeline_id)

        assert result.success is True, "Expected result.success is True"
        state = controller.get_status(result.pipeline_id)
        assert state.status == PipelineStatus.COMPLETED, "Expected state.status to equal PipelineStatus.COMPLETED"

    def test_resume_with_pending_escalation(self, temp_project, fresh_registry):
        """resume() fails if there are pending escalations."""

        class EscalatingExecutor(StageExecutor):
            def execute(self, context):
                return StageResult.escalate(
                    escalation_type="approval_required",
                    message="Approve first",
                )

        fresh_registry.register("intake", EscalatingExecutor)
        fresh_registry.register("clarify", lambda: PassthroughExecutor())
        fresh_registry.register("analyze", lambda: PassthroughExecutor())
        fresh_registry.register("spec", lambda: PassthroughExecutor())

        controller = PipelineController(temp_project, registry=fresh_registry)

        result = controller.execute("Test", template="design")
        state = controller.get_status(result.pipeline_id)
        assert state.status == PipelineStatus.WAITING_APPROVAL, "Expected state.status to equal PipelineStatus.WAITING_APPR..."

        with pytest.raises(PipelineStateError) as exc_info:
            controller.resume(state.pipeline_id)

        assert "pending escalations" in str(exc_info.value).lower(), "Expected 'pending escalations' in str(exc_info.value).lower()"

    def test_approve_escalation(self, temp_project, fresh_registry):
        """approve() resolves escalation and continues."""
        call_count = [0]

        class EscalatingOnce(StageExecutor):
            def execute(self, context):
                call_count[0] += 1
                if call_count[0] == 1:
                    return StageResult.escalate(
                        escalation_type="approval_required",
                        message="Approve first",
                    )
                return StageResult.success()

        fresh_registry.register("intake", EscalatingOnce)
        fresh_registry.register("clarify", lambda: PassthroughExecutor())
        fresh_registry.register("analyze", lambda: PassthroughExecutor())
        fresh_registry.register("spec", lambda: PassthroughExecutor())

        controller = PipelineController(temp_project, registry=fresh_registry)

        result = controller.execute("Test", template="design")
        state = controller.get_status(result.pipeline_id)
        assert state.status == PipelineStatus.WAITING_APPROVAL, "Expected state.status to equal PipelineStatus.WAITING_APPR..."

        success = controller.approve(state.pipeline_id)
        assert success is True, "Expected success is True"

        state = controller.get_status(state.pipeline_id)
        assert state.status == PipelineStatus.COMPLETED, "Expected state.status to equal PipelineStatus.COMPLETED"

    def test_reject_escalation(self, temp_project, fresh_registry):
        """reject() aborts the pipeline."""

        class EscalatingExecutor(StageExecutor):
            def execute(self, context):
                return StageResult.escalate(
                    escalation_type="approval_required",
                    message="Approve first",
                )

        fresh_registry.register("intake", EscalatingExecutor)
        fresh_registry.register("clarify", lambda: PassthroughExecutor())
        fresh_registry.register("analyze", lambda: PassthroughExecutor())
        fresh_registry.register("spec", lambda: PassthroughExecutor())

        controller = PipelineController(temp_project, registry=fresh_registry)

        result = controller.execute("Test", template="design")

        success = controller.reject(result.pipeline_id, "Not approved")
        assert success is True, "Expected success is True"

        state = controller.get_status(result.pipeline_id)
        assert state.status == PipelineStatus.ABORTED, "Expected state.status to equal PipelineStatus.ABORTED"

    def test_abort_pipeline(self, temp_project, full_registry):
        """abort() stops a running pipeline."""
        controller = PipelineController(temp_project, registry=full_registry)

        state = controller._create("Test", "implement", {})
        state.status = PipelineStatus.RUNNING
        state.current_stage = "clarify"
        state.stages["clarify"].mark_running()
        controller.state_store.save(state)

        success = controller.abort(state.pipeline_id, "User cancelled")
        assert success is True, "Expected success is True"

        state = controller.get_status(state.pipeline_id)
        assert state.status == PipelineStatus.ABORTED, "Expected state.status to equal PipelineStatus.ABORTED"
        assert state.stages["clarify"].status == StageStatus.FAILED, "Expected state.stages['clarify'].status to equal StageStatus.FAILED"
        assert "User cancelled" in state.stages["clarify"].error, "Expected 'User cancelled' in state.stages['clarify'].error"

    def test_abort_already_terminal(self, controller):
        """abort() returns False for terminal pipeline."""
        result = controller.execute("Test")

        success = controller.abort(result.pipeline_id)
        assert success is False, "Expected success is False"

    def test_get_status(self, controller):
        """get_status() returns current pipeline state."""
        result = controller.execute("Test")
        loaded = controller.get_status(result.pipeline_id)

        assert loaded.pipeline_id == result.pipeline_id, "Expected loaded.pipeline_id to equal result.pipeline_id"
        assert loaded.status == PipelineStatus.COMPLETED, "Expected loaded.status to equal PipelineStatus.COMPLETED"

    def test_get_status_not_found(self, controller):
        """get_status() raises error for unknown pipeline."""
        with pytest.raises(PipelineNotFoundError):
            controller.get_status("PL-99999999-nonexist")

    def test_stage_executor_not_found(self, temp_project, fresh_registry):
        """execute() handles missing stage executor."""
        fresh_registry.register("intake", lambda: PassthroughExecutor())

        controller = PipelineController(temp_project, registry=fresh_registry)

        result = controller.execute("Test", template="design")

        assert result.success is False, "Expected result.success is False"
        state = controller.get_status(result.pipeline_id)
        assert state.status == PipelineStatus.FAILED, "Expected state.status to equal PipelineStatus.FAILED"
        assert "not registered" in state.stages["clarify"].error.lower(), "Expected 'not registered' in state.stages['clarify'].err..."

    def test_stage_next_override(self, temp_project, fresh_registry):
        """Stage can override next stage."""

        class SkipToSpec(StageExecutor):
            def execute(self, context):
                return StageResult.success(next_stage="spec")

        fresh_registry.register("intake", SkipToSpec)
        fresh_registry.register("clarify", lambda: PassthroughExecutor())
        fresh_registry.register("analyze", lambda: PassthroughExecutor())
        fresh_registry.register("spec", lambda: PassthroughExecutor())

        controller = PipelineController(temp_project, registry=fresh_registry)

        result = controller.execute("Test", template="design")

        state = controller.get_status(result.pipeline_id)
        assert state.stages["intake"].status == StageStatus.COMPLETED, "Expected state.stages['intake'].status to equal StageStatus.COMPLETED"
        assert state.stages["clarify"].status == StageStatus.PENDING, "Expected state.stages['clarify'].status to equal StageStatus.PENDING"
        assert state.stages["analyze"].status == StageStatus.PENDING, "Expected state.stages['analyze'].status to equal StageStatus.PENDING"
        assert state.stages["spec"].status == StageStatus.COMPLETED, "Expected state.stages['spec'].status to equal StageStatus.COMPLETED"

    def test_artifacts_flow_between_stages(self, temp_project, fresh_registry):
        """Artifacts from earlier stages flow to later stages."""
        received_artifacts = []

        class ArtifactProducer(StageExecutor):
            def execute(self, context):
                return StageResult.success({"produced_by": "producer"})

        class ArtifactConsumer(StageExecutor):
            def execute(self, context):
                received_artifacts.append(dict(context.input_artifacts))
                return StageResult.success()

        fresh_registry.register("intake", ArtifactProducer)
        fresh_registry.register("clarify", ArtifactConsumer)
        fresh_registry.register("analyze", lambda: PassthroughExecutor())
        fresh_registry.register("spec", lambda: PassthroughExecutor())

        controller = PipelineController(temp_project, registry=fresh_registry)
        controller.execute("Test", template="design")

        assert len(received_artifacts) == 1, "Expected len(received_artifacts) to equal 1"
        assert received_artifacts[0]["produced_by"] == "producer", "Expected received_artifacts[0]['prod... to equal 'producer'"

    def test_input_validation_failure(self, temp_project, fresh_registry):
        """Stage fails if input validation fails."""

        class ValidatingExecutor(StageExecutor):
            def execute(self, context):
                return StageResult.success()

            def get_required_inputs(self):
                return ["required_artifact"]

        fresh_registry.register("intake", lambda: PassthroughExecutor())
        fresh_registry.register("clarify", ValidatingExecutor)
        fresh_registry.register("analyze", lambda: PassthroughExecutor())
        fresh_registry.register("spec", lambda: PassthroughExecutor())

        controller = PipelineController(temp_project, registry=fresh_registry)

        result = controller.execute("Test", template="design")

        state = controller.get_status(result.pipeline_id)
        assert state.status == PipelineStatus.FAILED, "Expected state.status to equal PipelineStatus.FAILED"
        assert "required_artifact" in state.stages["clarify"].error, "Expected 'required_artifact' in state.stages['clarify'].error"


class TestPipelineResult:
    """Tests for PipelineResult dataclass."""

    def test_result_success_attributes(self):
        """PipelineResult has all success attributes."""
        result = PipelineResult(
            success=True,
            pipeline_id="PL-123",
            stages_completed=["intake", "clarify"],
            current_stage=None,
            deliverable={"output": "value"},
            error=None,
            total_duration_seconds=1.5,
        )

        assert result.success is True, "Expected result.success is True"
        assert result.pipeline_id == "PL-123", "Expected result.pipeline_id to equal 'PL-123'"
        assert result.stages_completed == ["intake", "clarify"], "Expected result.stages_completed to equal ['intake', 'clarify']"
        assert result.deliverable == {"output": "value"}, "Expected result.deliverable to equal {'output': 'value'}"
        assert result.error is None, "Expected result.error is None"

    def test_result_failure_attributes(self):
        """PipelineResult has error on failure."""
        result = PipelineResult(
            success=False,
            pipeline_id="PL-123",
            error="Something went wrong",
            total_duration_seconds=0.5,
        )

        assert result.success is False, "Expected result.success is False"
        assert result.error == "Something went wrong", "Expected result.error to equal 'Something went wrong'"


class TestControllerListPipelines:
    """Tests for list_pipelines()."""

    def test_list_all_pipelines(self, controller):
        """list_pipelines() returns all pipelines."""
        controller.execute("Request 1")
        controller.execute("Request 2")
        controller.execute("Request 3")

        pipelines = controller.list_pipelines()
        assert len(pipelines) >= 3, "Expected len(pipelines) >= 3"

    def test_list_filtered_by_status(self, temp_project, fresh_registry):
        """list_pipelines(status=...) filters correctly."""

        class FailingExecutor(StageExecutor):
            def execute(self, context):
                return StageResult.failed("fail")

        fresh_registry.register("intake", lambda: PassthroughExecutor())
        fresh_registry.register("clarify", FailingExecutor)
        fresh_registry.register("analyze", lambda: PassthroughExecutor())
        fresh_registry.register("spec", lambda: PassthroughExecutor())

        controller = PipelineController(temp_project, registry=fresh_registry)

        controller.execute("Will complete", template="test")  # test template has no clarify
        controller.execute("Will fail", template="design")

        # Register all stages for the test template result to complete
        from agentforge.core.pipeline import get_registry
        get_registry().register("red", lambda: PassthroughExecutor())

        failed = controller.list_pipelines(status=PipelineStatus.FAILED)
        # At least one should be failed
        assert any(p.status == PipelineStatus.FAILED for p in failed), "Expected any() to be truthy"

    def test_list_respects_limit(self, controller):
        """list_pipelines(limit=N) returns at most N results."""
        for i in range(10):
            controller.execute(f"Request {i}")

        limited = controller.list_pipelines(limit=5)
        assert len(limited) == 5, "Expected len(limited) to equal 5"


class TestControllerProvideFeedback:
    """Tests for provide_feedback()."""

    def test_provide_feedback_stores(self, controller):
        """provide_feedback() stores in pipeline state."""
        result = controller.execute("Test")

        controller.provide_feedback(result.pipeline_id, "This looks good")

        state = controller.get_status(result.pipeline_id)
        assert state.config.get("feedback") == "This looks good", "Expected state.config.get('feedback') to equal 'This looks good'"

    def test_provide_feedback_appends(self, controller):
        """provide_feedback() maintains history."""
        result = controller.execute("Test")

        controller.provide_feedback(result.pipeline_id, "First feedback")
        controller.provide_feedback(result.pipeline_id, "Second feedback")

        state = controller.get_status(result.pipeline_id)
        assert state.config.get("feedback") == "Second feedback", "Expected state.config.get('feedback') to equal 'Second feedback'"
        assert state.config.get("feedback_history") == ["First feedback", "Second feedback"], "Expected state.config.get('feedback_... to equal ['First feedback', 'Second ..."


class TestContractEnforcement:
    """Tests for contract enforcement integration."""

    def test_controller_has_operation_manager(self, controller):
        """Controller initializes with operation contract manager."""
        assert controller.operation_manager is not None, "Expected controller.operation_manager is not None"

    def test_controller_has_contract_registry(self, controller):
        """Controller initializes with contract registry."""
        assert controller.contract_registry is not None, "Expected controller.contract_registry is not None"

    def test_get_contract_enforcer_with_no_contracts(self, controller):
        """_get_contract_enforcer returns minimal enforcer for operation contracts."""
        from agentforge.core.pipeline import create_pipeline_state

        state = create_pipeline_state(
            request="Test request",
            project_path=controller.project_path,
            template="implement",
        )

        enforcer = controller._get_contract_enforcer(state)

        # Should return an enforcer even without task contracts
        # (for operation contract enforcement)
        assert enforcer is not None, "Expected enforcer is not None"
        assert enforcer.contracts.contract_set_id == "operation-only", "Expected enforcer.contracts.contract... to equal 'operation-only'"

    def test_enforcer_disabled_via_config(self, temp_project, full_registry):
        """Contract enforcement can be disabled via config."""
        from agentforge.core.pipeline import create_pipeline_state

        controller = PipelineController(
            project_path=temp_project,
            registry=full_registry,
        )

        state = create_pipeline_state(
            request="Test",
            project_path=temp_project,
            template="implement",
            config={"enforce_operation_contracts": False},
        )

        enforcer = controller._get_contract_enforcer(state)
        assert enforcer is None, "Expected enforcer is None"

    def test_operation_contracts_loaded(self, controller):
        """Operation contract manager loads built-in contracts."""
        rules = controller.operation_manager.get_all_rules()

        # Should have loaded tool-usage, git-operations, safety-rules
        assert len(rules) > 0, "Expected len(rules) > 0"

        # Check for a known rule
        rule_ids = [r.rule_id for r in rules]
        assert "read-before-edit" in rule_ids, "Expected 'read-before-edit' in rule_ids"

    def test_lsp_preference_rules_loaded(self, controller):
        """LSP preference rules are loaded from tool-usage contract."""
        rules = controller.operation_manager.get_all_rules()
        rule_ids = [r.rule_id for r in rules]

        # Check for LSP rules we added
        assert "lsp-for-definitions" in rule_ids, "Expected 'lsp-for-definitions' in rule_ids"
        assert "lsp-for-references" in rule_ids, "Expected 'lsp-for-references' in rule_ids"
        assert "lsp-for-symbols" in rule_ids, "Expected 'lsp-for-symbols' in rule_ids"

    def test_enforce_contracts_config_flag(self, temp_project, full_registry):
        """enforce_contracts config flag controls contract validation."""
        controller = PipelineController(
            project_path=temp_project,
            registry=full_registry,
        )

        # Run with contract enforcement disabled
        result = controller.execute(
            "Test request",
            config={"enforce_contracts": False}
        )

        # Should still succeed - contracts not enforced
        assert result.success is True, "Expected result.success is True"

    def test_execute_with_contract_enforcement(self, controller):
        """Pipeline executes successfully with contract enforcement enabled."""
        result = controller.execute(
            "Test request",
            config={"enforce_contracts": True}
        )

        assert result.success is True, "Expected result.success is True"


class TestContractEscalationTriggers:
    """Tests for contract-triggered escalations."""

    def test_escalation_trigger_from_contract(self, temp_project, fresh_registry):
        """Contract escalation triggers can pause pipeline."""
        from agentforge.core.contracts.draft import (
            ApprovedContracts,
            EscalationTrigger,
            StageContract,
        )
        from agentforge.core.contracts.registry import ContractRegistry

        # Register stages
        fresh_registry.register("intake", lambda: PassthroughExecutor("intake"))
        fresh_registry.register("clarify", lambda: PassthroughExecutor("clarify"))
        fresh_registry.register("analyze", lambda: PassthroughExecutor("analyze"))
        fresh_registry.register("spec", lambda: PassthroughExecutor("spec"))

        # Create a contract with an escalation trigger
        contracts = ApprovedContracts(
            contract_set_id="TEST-CONTRACT-001",
            draft_id="DRAFT-TEST",
            request_id="REQ-TEST",
            stage_contracts=[
                StageContract(stage_name="intake"),
                StageContract(stage_name="clarify"),
            ],
            escalation_triggers=[
                EscalationTrigger(
                    trigger_id="test-trigger",
                    condition="Confidence below 0.5",
                    severity="blocking",
                    prompt="Low confidence - please review",
                    rationale="Test trigger",
                ),
            ],
        )

        # Register the contract
        registry = ContractRegistry(temp_project)
        registry.register(contracts)

        controller = PipelineController(
            project_path=temp_project,
            registry=fresh_registry,
        )

        # Execute with contract reference
        result = controller.execute(
            "Test request",
            template="design",
            config={
                "request_id": "REQ-TEST",
                "enforce_contracts": True,
            }
        )

        # Pipeline should complete (trigger condition not met)
        # since confidence is not explicitly low
        assert result.success is True, "Expected result.success is True"
