"""HTTP clients for the orchestration API (stdlib urllib, no third-party deps)."""

import json
import urllib.error
import urllib.request
from typing import Any


class OrchestratorError(RuntimeError):
    """Raised when the API returns a non-2xx response."""

    def __init__(self, status: int, body: str) -> None:
        super().__init__(f"HTTP {status}: {body}")
        self.status = status
        self.body = body


def _request(
    method: str, url: str, *, body: dict | None = None, headers: dict | None = None
) -> Any:
    """Perform a JSON request and return the decoded response (or None for 204)."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url, data=data, method=method, headers={"Content-Type": "application/json", **(headers or {})}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        raise OrchestratorError(exc.code, exc.read().decode(errors="replace")) from exc


class AdminClient:
    """Operator/human-facing actions (over the trusted network; no agent key)."""

    def __init__(self, base_url: str) -> None:
        self.base = base_url.rstrip("/")

    # --- agent lifecycle ---
    def register_agent(self, name: str, tailscale_node: str | None = None) -> dict:
        """Register an agent; the response contains the one-time api_key."""
        return _request(
            "POST", f"{self.base}/agents", body={"name": name, "tailscale_node": tailscale_node}
        )

    def revoke_agent(self, agent_id: str) -> None:
        """Revoke an agent's key."""
        _request("DELETE", f"{self.base}/agents/{agent_id}")

    def list_agents(self) -> list[dict]:
        return _request("GET", f"{self.base}/agents")

    # --- projects ---
    def create_project(self, name: str, gdrive_folder_id: str, description: str | None = None) -> dict:
        return _request(
            "POST",
            f"{self.base}/projects",
            body={"name": name, "gdrive_folder_id": gdrive_folder_id, "description": description},
        )

    def delete_project(self, project_id: str) -> None:
        _request("DELETE", f"{self.base}/projects/{project_id}")

    def provision_bookshelf(self, project_id: str) -> dict:
        """Provision the project's bookshelf folder + 6 category subfolders.

        Creates the `<project-name>` folder under the project's parent Drive folder
        plus the overview/architecture/guides/tutorials/reference/rules subfolders.
        Returns the project including `bookshelf_folder_id`.
        """
        return _request("POST", f"{self.base}/projects/{project_id}/bookshelf")

    def list_library(self, project_id: str) -> dict:
        """Return the project's library: sections, each with its documents."""
        return _request("GET", f"{self.base}/projects/{project_id}/library")

    # --- human review actions ---
    def submit_feedback(self, session_id: str, comment: str) -> dict:
        return _request(
            "POST", f"{self.base}/sessions/{session_id}/feedback", body={"comment": comment}
        )

    def approve(self, session_id: str) -> dict:
        return _request("POST", f"{self.base}/sessions/{session_id}/approve")

    # --- reads ---
    def list_commits(self, session_id: str) -> dict:
        return _request("GET", f"{self.base}/sessions/{session_id}/commits")

    def get_artifact(self, gdrive_file_id: str) -> dict:
        return _request("GET", f"{self.base}/artifacts/{gdrive_file_id}")


class AgentClient:
    """The agent operational protocol. Authenticates with the agent API key."""

    def __init__(self, base_url: str, agent_id: str, api_key: str) -> None:
        self.base = base_url.rstrip("/")
        self.agent_id = agent_id
        self._headers = {"X-Agent-Key": api_key}

    def check_in(self, project_id: str) -> dict:
        """Step 1 INIT: returns session context including any pending feedback."""
        return _request(
            "POST",
            f"{self.base}/agents/checkin",
            body={"agent_id": self.agent_id, "project_id": project_id},
            headers=self._headers,
        )

    def submit_plan(self, session_id: str, file_name: str, content: str, message: str) -> dict:
        """Step 2 PLANNING: upload the initial plan."""
        return self._artifact(session_id, "plan", file_name, content, message)

    def refine(self, session_id: str, file_name: str, content: str, message: str) -> dict:
        """Step 3 REFINEMENT: upload a revised plan, resolving open feedback."""
        return self._artifact(session_id, "refine", file_name, content, message)

    def complete(self, session_id: str, file_name: str, content: str, message: str) -> dict:
        """Step 5 COMPLETION: upload the final artifact and close the session."""
        return self._artifact(session_id, "complete", file_name, content, message)

    def document(
        self, session_id: str, category: str, file_name: str, content: str, message: str
    ) -> dict:
        """Upload one Markdown book into a bookshelf category.

        `category` must be one of overview|architecture|guides|tutorials|reference|rules.
        Uploads the Markdown into that category's Drive subfolder and records a DOC
        commit. Does NOT change session state, so call it repeatedly per file.
        """
        body = {
            "agent_id": self.agent_id,
            "category": category,
            "file_name": file_name,
            "content": content,
            "commit_message": message,
        }
        return _request(
            "POST", f"{self.base}/sessions/{session_id}/document", body=body, headers=self._headers
        )

    def report_stage(self, session_id: str, payload: dict) -> dict:
        """Step 4 REPORTING: post a stage report (build via protocol.stage_payload)."""
        body = {"session_id": session_id, "agent_id": self.agent_id, **payload}
        return _request(
            "POST", f"{self.base}/webhooks/stage-report", body=body, headers=self._headers
        )

    def _artifact(self, session_id: str, action: str, file_name: str, content: str, message: str) -> dict:
        body = {
            "agent_id": self.agent_id,
            "file_name": file_name,
            "content": content,
            "commit_message": message,
        }
        return _request(
            "POST", f"{self.base}/sessions/{session_id}/{action}", body=body, headers=self._headers
        )
