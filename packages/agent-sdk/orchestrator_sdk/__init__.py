"""Lightweight client SDK for the AI Agent Orchestration API.

Stdlib-only (urllib) so agents pull in no extra dependencies. Exposes an AdminClient
(operator actions: register/revoke agents, create projects, inject feedback, approve)
and an AgentClient (the operational protocol: check-in, plan, refine, report, complete).
"""

from orchestrator_sdk.client import AdminClient, AgentClient, OrchestratorError
from orchestrator_sdk.protocol import markdown_document, stage_payload

__all__ = [
    "AdminClient",
    "AgentClient",
    "OrchestratorError",
    "markdown_document",
    "stage_payload",
]
