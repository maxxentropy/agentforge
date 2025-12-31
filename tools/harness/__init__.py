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
from tools.harness.session_domain import (
    SessionState,
    TokenBudget,
    SessionArtifact,
    SessionHistory,
    SessionContext,
)
from tools.harness.session_store import SessionStore
from tools.harness.session_manager import (
    SessionManager,
    SessionAlreadyActive,
    NoActiveSession,
    InvalidStateTransition,
)

# Phase 2: Memory System
from tools.harness.memory_domain import (
    MemoryTier,
    MemoryEntry,
)
from tools.harness.memory_store import (
    MemoryStore,
    MemoryWriteError,
)
from tools.harness.memory_manager import MemoryManager

# Phase 3: Tool Selection
from tools.harness.tool_domain import (
    ToolDefinition,
    ToolProfile,
    DomainTools,
)
from tools.harness.tool_registry import (
    ToolRegistry,
    DuplicateToolError,
)
from tools.harness.tool_selector import ToolSelector

# Phase 4: Agent Monitor
from tools.harness.monitor_domain import (
    ObservationType,
    Observation,
    HealthStatus,
    Recommendation,
    LoopDetection,
    ThrashingDetection,
    AgentHealth,
)
from tools.harness.agent_monitor import AgentMonitor, MonitorConfig

# Phase 5: Recovery System
from tools.harness.recovery_domain import (
    RecoveryAction,
    RecoveryResult,
    Checkpoint,
    RecoveryAttempt,
    RecoveryPolicy,
)
from tools.harness.checkpoint_manager import CheckpointManager
from tools.harness.recovery_executor import RecoveryExecutor

# Phase 6: Human Escalation
from tools.harness.escalation_domain import (
    EscalationPriority,
    EscalationStatus,
    EscalationChannel,
    ResolutionType,
    Escalation,
    EscalationResolution,
    EscalationRule,
)
from tools.harness.escalation_manager import EscalationManager
from tools.harness.escalation_notifier import EscalationNotifier

# Phase 7: Orchestrator
from tools.harness.orchestrator_domain import (
    OrchestratorState,
    ExecutionMode,
    AgentTask,
    ExecutionResult,
    OrchestratorConfig,
)
from tools.harness.agent_orchestrator import AgentOrchestrator

# Phase 8: LLM Executor
from tools.harness.llm_executor_domain import (
    ActionType,
    ToolCategory,
    ToolCall,
    ToolResult,
    AgentAction,
    ConversationMessage,
    ExecutionContext,
    StepResult,
    TokenUsage,
    LLMExecutorError,
    ActionParseError,
    ToolExecutionError,
)
from tools.harness.llm_executor import LLMExecutor, create_default_executor
from tools.harness.action_parser import ActionParser
from tools.harness.agent_prompt_builder import AgentPromptBuilder
from tools.harness.tool_executor_bridge import ToolExecutorBridge, create_tool_bridge
from tools.harness.execution_context_store import (
    ExecutionContextStore,
    create_execution_store,
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
]
