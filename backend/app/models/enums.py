"""Enumerations shared across models and API schemas."""

import enum


class SessionState(enum.StrEnum):
    """Lifecycle state of an agent session (mirrors the operational protocol)."""

    INIT = "INIT"
    PLANNING = "PLANNING"
    WAITING_FOR_HUMAN = "WAITING_FOR_HUMAN"
    REFINING = "REFINING"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TERMINATED = "TERMINATED"


class CommitType(enum.StrEnum):
    """Kind of artifact/event a commit records."""

    PLAN = "PLAN"
    REVISION = "REVISION"
    STAGE_REPORT = "STAGE_REPORT"
    COMPLETION = "COMPLETION"
    DOC = "DOC"  # documentation commits (bookshelf library)


class DocCategory(enum.StrEnum):
    """Category folders for the project bookshelf (documentation library)."""

    OVERVIEW = "overview"
    ARCHITECTURE = "architecture"
    GUIDES = "guides"
    TUTORIALS = "tutorials"
    REFERENCE = "reference"
    RULES = "rules"


class AgentStatus(enum.StrEnum):
    """Connectivity state of a registered agent."""

    ONLINE = "ONLINE"
    IDLE = "IDLE"
    OFFLINE = "OFFLINE"
    ERROR = "ERROR"
    REVOKED = "REVOKED"  # key revoked; the agent can no longer authenticate
