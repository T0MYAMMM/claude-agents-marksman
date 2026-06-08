"""Unit tests for the version-control engine and session state machine."""

import pytest

from app.models.agent import Agent
from app.models.enums import CommitType, SessionState
from app.models.project import Project
from app.models.session import Session
from app.services.session_state import InvalidTransitionError, assert_transition
from app.services.version_control import record_commit


@pytest.mark.asyncio
async def test_record_commit_chains_to_parent(db_session) -> None:
    """The second commit on a session links back to the first."""
    agent = Agent(name="a", api_key_hash="h")
    project = Project(name="p", gdrive_folder_id="f")
    db_session.add_all([agent, project])
    await db_session.flush()
    session = Session(project_id=project.id, agent_id=agent.id, title="t")
    db_session.add(session)
    await db_session.flush()

    first = await record_commit(
        db_session,
        session_id=session.id,
        agent_id=agent.id,
        commit_type=CommitType.PLAN,
        message="plan",
    )
    second = await record_commit(
        db_session,
        session_id=session.id,
        agent_id=agent.id,
        commit_type=CommitType.STAGE_REPORT,
        message="stage 1",
    )
    assert first.parent_commit_id is None
    assert second.parent_commit_id == first.id


def test_legal_transition() -> None:
    """INIT -> PLANNING is allowed."""
    assert_transition(SessionState.INIT, SessionState.PLANNING)


def test_illegal_transition_raises() -> None:
    """COMPLETED is terminal; any transition out of it is rejected."""
    with pytest.raises(InvalidTransitionError):
        assert_transition(SessionState.COMPLETED, SessionState.EXECUTING)
