class OrchestratorError(Exception):
    """Base exception for orchestrator errors."""


class ToolNotFoundError(OrchestratorError):
    """Raised when a tool is not registered."""


class ToolExecutionError(OrchestratorError):
    """Raised when a tool fails during execution."""


class LLMError(OrchestratorError):
    """Raised when LLM interaction fails."""
