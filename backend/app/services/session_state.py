"""Session state-machine transitions.

Centralises the legal transitions so routers never set `state` ad hoc. Mirrors the
operational protocol: INIT -> PLANNING -> WAITING_FOR_HUMAN -> (REFINING ->
WAITING_FOR_HUMAN)* -> EXECUTING -> COMPLETED, with FAILED/TERMINATED reachable from
any active state.
"""

from app.models.enums import SessionState

# EXECUTING is reachable only from WAITING_FOR_HUMAN: a reviewer must approve the plan
# (the /approve endpoint) before the agent executes. Stage reports therefore require an
# already-approved (EXECUTING) session and keep it EXECUTING.
_ALLOWED: dict[SessionState, set[SessionState]] = {
    SessionState.INIT: {SessionState.PLANNING, SessionState.TERMINATED},
    SessionState.PLANNING: {SessionState.WAITING_FOR_HUMAN, SessionState.FAILED},
    SessionState.WAITING_FOR_HUMAN: {
        SessionState.REFINING,
        SessionState.EXECUTING,
        SessionState.TERMINATED,
    },
    SessionState.REFINING: {SessionState.WAITING_FOR_HUMAN, SessionState.FAILED},
    SessionState.EXECUTING: {
        SessionState.EXECUTING,  # stage reports keep it EXECUTING
        SessionState.WAITING_FOR_HUMAN,  # mid-execution feedback pause
        SessionState.COMPLETED,
        SessionState.FAILED,
    },
    SessionState.COMPLETED: set(),
    SessionState.FAILED: set(),
    SessionState.TERMINATED: set(),
}


class InvalidTransitionError(ValueError):
    """Raised when an illegal state transition is attempted."""


def assert_transition(current: SessionState, target: SessionState) -> None:
    """Raise InvalidTransitionError if moving from `current` to `target` is not allowed."""
    if target not in _ALLOWED.get(current, set()):
        raise InvalidTransitionError(
            f"Illegal session transition: {current.value} -> {target.value}"
        )
