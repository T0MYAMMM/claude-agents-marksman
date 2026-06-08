"""Read contracts for the dashboard metrics overview endpoint."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class Totals(BaseModel):
    """System-wide row counts surfaced on the dashboard."""

    projects: int
    sessions: int
    agents: int
    commits: int
    documents: int


class StateCount(BaseModel):
    """Count of sessions in a single state."""

    state: str
    count: int


class StatusCount(BaseModel):
    """Count of agents in a single connectivity status."""

    status: str
    count: int


class TypeCount(BaseModel):
    """Count of commits of a single type."""

    type: str
    count: int


class ActivityPoint(BaseModel):
    """Commit volume for a single calendar day (zero-filled)."""

    date: str
    commits: int


class RecentSession(BaseModel):
    """A lightweight session summary for the recent-activity list."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    project_id: str
    state: str
    progress_pct: int
    started_at: datetime


class OverviewStats(BaseModel):
    """Aggregated dashboard metrics across the whole system."""

    totals: Totals
    sessions_by_state: list[StateCount]
    agents_by_status: list[StatusCount]
    commits_by_type: list[TypeCount]
    activity: list[ActivityPoint]
    recent_sessions: list[RecentSession]
