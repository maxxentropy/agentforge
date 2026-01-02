"""
Agent Harness - Autonomous Agent Framework Layer
=================================================

Provides infrastructure for running autonomous agents with:
- Session management and state persistence
- 4-tier memory hierarchy
- Phase-appropriate tool selection
- Pathology detection and recovery strategies
- Human escalation and oversight
- LLM execution with tool integration

Components:
    session: Session Manager (Phase 1)
    memory: Memory System (Phase 2)
    tools: Tool Selector (Phase 3)
    monitor: Agent Monitor (Phase 4)
    recovery: Recovery Strategies (Phase 5)
    escalation: Human Escalation (Phase 6)
    orchestrator: Agent Orchestrator (Phase 7)
    llm: LLM Executor (Phase 8)
"""

# Phase 1: Session Management
from agentforge.core.harness.action_parser import ActionParser
from agentforge.core.harness.agent_monitor import AgentMonitor, MonitorConfig
from agentforge.core.harness.agent_orchestrator import AgentOrchestrator
from agentforge.core.harness.agent_prompt_builder import AgentPromptBuilder
from agentforge.core.harness.auto_fix_daemon import (
    AutoFixConfig,
    AutoFixDaemon,
    DaemonStatus,
    create_auto_fix_daemon,
)
from agentforge.core.harness.checkpoint_manager import CheckpointManager
from agentforge.core.harness.conformance_tools import (
    CONFORMANCE_TOOL_DEFINITIONS,
    ConformanceTools,
)

# Phase 6: Human Escalation
from agentforge.core.harness.escalation_domain import (
    Escalation,
    EscalationChannel,
    EscalationPriority,
    EscalationResolution,
    EscalationRule,
    EscalationStatus,
    ResolutionType,
)
from agentforge.core.harness.escalation_manager import EscalationManager
from agentforge.core.harness.escalation_notifier import EscalationNotifier
from agentforge.core.harness.execution_context_store import (
    ExecutionContextStore,
    create_execution_store,
)
from agentforge.core.harness.fix_violation_workflow import (
    FixAttempt,
    FixPhase,
    FixViolationWorkflow,
    create_fix_workflow,
)
from agentforge.core.harness.git_tools import (
    GIT_TOOL_DEFINITIONS,
    GitTools,
)
from agentforge.core.harness.llm_executor import LLMExecutor, create_default_executor

# Phase 8: LLM Executor
from agentforge.core.harness.llm_executor_domain import (
    ActionParseError,
    ActionType,
    AgentAction,
    ConversationMessage,
    ExecutionContext,
    LLMExecutorError,
    StepResult,
    TokenUsage,
    ToolCall,
    ToolCategory,
    ToolExecutionError,
    ToolResult,
)

# Phase 2: Memory System
from agentforge.core.harness.memory_domain import (
    MemoryEntry,
    MemoryTier,
)
from agentforge.core.harness.memory_manager import MemoryManager
from agentforge.core.harness.memory_store import (
    MemoryStore,
    MemoryWriteError,
)

# Minimal Context Architecture
from agentforge.core.harness.minimal_context import (
    AdaptiveBudget,
    MinimalContextExecutor,
    MinimalContextFixWorkflow,
    Phase,
    StepOutcome,
    TaskState,
    TaskStateStore,
    WorkingMemoryItem,
    WorkingMemoryManager,
    create_minimal_fix_workflow,
)

# Phase 4: Agent Monitor
from agentforge.core.harness.monitor_domain import (
    AgentHealth,
    HealthStatus,
    LoopDetection,
    Observation,
    ObservationType,
    Recommendation,
    ThrashingDetection,
)

# Phase 7: Orchestrator
from agentforge.core.harness.orchestrator_domain import (
    AgentTask,
    ExecutionMode,
    ExecutionResult,
    OrchestratorConfig,
    OrchestratorState,
)

# Phase 5: Recovery System
from agentforge.core.harness.recovery_domain import (
    Checkpoint,
    RecoveryAction,
    RecoveryAttempt,
    RecoveryPolicy,
    RecoveryResult,
)
from agentforge.core.harness.recovery_executor import RecoveryExecutor
from agentforge.core.harness.rollback_manager import (
    ROLLBACK_TOOL_DEFINITIONS,
    BackupManifest,
    RollbackManager,
)
from agentforge.core.harness.session_domain import (
    SessionArtifact,
    SessionContext,
    SessionHistory,
    SessionState,
    TokenBudget,
)
from agentforge.core.harness.session_manager import (
    InvalidStateTransition,
    NoActiveSession,
    SessionAlreadyActive,
    SessionManager,
)
from agentforge.core.harness.session_store import SessionStore
from agentforge.core.harness.test_runner_tools import (
    TEST_TOOL_DEFINITIONS,
    TestRunnerTools,
)

# Phase 3: Tool Selection
from agentforge.core.harness.tool_domain import (
    DomainTools,
    ToolDefinition,
    ToolProfile,
)
from agentforge.core.harness.tool_executor_bridge import ToolExecutorBridge, create_tool_bridge
from agentforge.core.harness.tool_registry import (
    DuplicateToolError,
    ToolRegistry,
)
from agentforge.core.harness.tool_selector import ToolSelector

# Self-Hosting (Phase 9)
from agentforge.core.harness.violation_tools import (
    VIOLATION_TOOL_DEFINITIONS,
    ViolationInfo,
    ViolationTools,
)

__all__ = [
    # Session Management
    "SessionState",
    "TokenBudget",
    "SessionArtifact",
    "SessionHistory",
    "SessionContext",
    "SessionStore",
    "SessionManager",
    "SessionAlreadyActive",
    "NoActiveSession",
    "InvalidStateTransition",
    # Memory System
    "MemoryTier",
    "MemoryEntry",
    "MemoryStore",
    "MemoryWriteError",
    "MemoryManager",
    # Tool Selection
    "ToolDefinition",
    "ToolProfile",
    "DomainTools",
    "ToolRegistry",
    "DuplicateToolError",
    "ToolSelector",
    # Agent Monitor
    "ObservationType",
    "Observation",
    "HealthStatus",
    "Recommendation",
    "LoopDetection",
    "ThrashingDetection",
    "AgentHealth",
    "MonitorConfig",
    "AgentMonitor",
    # Recovery System
    "RecoveryAction",
    "RecoveryResult",
    "Checkpoint",
    "RecoveryAttempt",
    "RecoveryPolicy",
    "CheckpointManager",
    "RecoveryExecutor",
    # Human Escalation
    "EscalationPriority",
    "EscalationStatus",
    "EscalationChannel",
    "ResolutionType",
    "Escalation",
    "EscalationResolution",
    "EscalationRule",
    "EscalationManager",
    "EscalationNotifier",
    # Orchestrator
    "OrchestratorState",
    "ExecutionMode",
    "AgentTask",
    "ExecutionResult",
    "OrchestratorConfig",
    "AgentOrchestrator",
    # LLM Executor
    "ActionType",
    "ToolCategory",
    "ToolCall",
    "ToolResult",
    "AgentAction",
    "ConversationMessage",
    "ExecutionContext",
    "StepResult",
    "TokenUsage",
    "LLMExecutorError",
    "ActionParseError",
    "ToolExecutionError",
    "LLMExecutor",
    "create_default_executor",
    "ActionParser",
    "AgentPromptBuilder",
    "ToolExecutorBridge",
    "create_tool_bridge",
    "ExecutionContextStore",
    "create_execution_store",
    # Self-Hosting
    "ViolationTools",
    "ViolationInfo",
    "VIOLATION_TOOL_DEFINITIONS",
    "ConformanceTools",
    "CONFORMANCE_TOOL_DEFINITIONS",
    "GitTools",
    "GIT_TOOL_DEFINITIONS",
    "TestRunnerTools",
    "TEST_TOOL_DEFINITIONS",
    "FixViolationWorkflow",
    "FixPhase",
    "FixAttempt",
    "create_fix_workflow",
    "AutoFixDaemon",
    "AutoFixConfig",
    "DaemonStatus",
    "create_auto_fix_daemon",
    "RollbackManager",
    "BackupManifest",
    "ROLLBACK_TOOL_DEFINITIONS",
    # Minimal Context Architecture
    "TaskStateStore",
    "TaskState",
    "Phase",
    "WorkingMemoryManager",
    "WorkingMemoryItem",
    "MinimalContextExecutor",
    "StepOutcome",
    "AdaptiveBudget",
    "MinimalContextFixWorkflow",
    "create_minimal_fix_workflow",
]
