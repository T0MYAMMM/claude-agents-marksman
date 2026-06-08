"""End-to-end example exercising every feature of the orchestration system.

Drives a complete agent lifecycle against a live deployment and leaves the dashboard
populated with a real project, session, commit timeline, and Drive-backed artifacts:

    register agent → create project → check in → submit plan → human feedback →
    re-check-in (sees feedback) → refine → approve → stage reports → complete →
    read commit timeline → fetch artifact content → (optional) revoke agent

Usage:
    python examples/full_workflow.py \
        --base-url https://<node>.<tailnet>.ts.net/api/v1 \
        --folder-id 1s2uz-M0R9otOKQpaNZ9X6KFhuUwTqJ0_ \
        [--revoke] [--cleanup]

The base URL defaults to localhost for non-tailnet runs.
"""

import argparse
import sys
from pathlib import Path

# Make the SDK importable without installation.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "packages" / "agent-sdk"))

from orchestrator_sdk import (  # noqa: E402
    AdminClient,
    AgentClient,
    OrchestratorError,
    markdown_document,
    stage_payload,
)

DEFAULT_FOLDER = "1s2uz-M0R9otOKQpaNZ9X6KFhuUwTqJ0_"


def step(n: int, title: str) -> None:
    print(f"\n\033[1;36m[{n}]\033[0m {title}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base-url", default="http://127.0.0.1:8000/api/v1")
    ap.add_argument("--folder-id", default=DEFAULT_FOLDER, help="Google Drive folder for artifacts")
    ap.add_argument("--revoke", action="store_true", help="Revoke the demo agent at the end")
    ap.add_argument("--cleanup", action="store_true", help="Delete the demo project at the end")
    args = ap.parse_args()

    admin = AdminClient(args.base_url)

    step(1, "Register an agent (operator action)")
    reg = admin.register_agent("demo-agent", tailscale_node="demo.tailnet.ts.net")
    agent_id, api_key = reg["id"], reg["api_key"]
    print(f"    agent_id={agent_id}  api_key={api_key[:8]}… (shown once)")
    agent = AgentClient(args.base_url, agent_id, api_key)

    step(2, "Create a project")
    project = admin.create_project(
        "Checkout Service Revamp",
        gdrive_folder_id=args.folder_id,
        description="Demo project created by examples/full_workflow.py",
    )
    pid = project["id"]
    print(f"    project_id={pid}  drive_folder={args.folder_id}")

    step(3, "Agent checks in (INIT)")
    ck = agent.check_in(pid)
    sid = ck["session_id"]
    print(f"    session_id={sid}  state={ck['state']}")

    step(4, "Agent uploads a PLAN (→ Google Drive, → WAITING_FOR_HUMAN)")
    plan_md = markdown_document(
        "Checkout Service Revamp — Plan",
        {"type": "plan", "session": sid, "author": "demo-agent"},
        "## Stages\n\n1. Extract payment gateway\n2. Add idempotency keys\n3. Migrate tests",
    )
    pl = agent.submit_plan(sid, "plan.md", plan_md, "Initial plan")
    print(f"    commit={pl['commit_id']}  drive_file={pl['gdrive_file_id']}  state={pl['session_state']}")

    step(5, "Human injects feedback (→ REFINING)")
    fb = admin.submit_feedback(sid, "Split stage 2: separate idempotency from retries.")
    print(f"    feedback={fb['id']}  resolved={fb['resolved']}")

    step(6, "Agent re-checks-in and sees the pending feedback")
    ck2 = agent.check_in(pid)
    for item in ck2["context"]["pending_feedback"]:
        print(f"    ↳ pending: {item['comment']}")

    step(7, "Agent uploads a REVISION (resolves feedback, → WAITING_FOR_HUMAN)")
    rev_md = markdown_document(
        "Checkout Service Revamp — Plan v2",
        {"type": "plan", "revision": 2, "session": sid},
        "## Stages\n\n1. Extract payment gateway\n2a. Add idempotency keys\n2b. Add retry policy\n3. Migrate tests",
    )
    rv = agent.refine(sid, "plan-v2.md", rev_md, "Revise: split stage 2 per feedback")
    print(f"    commit={rv['commit_id']}  drive_file={rv['gdrive_file_id']}")

    step(8, "Human approves the plan (→ EXECUTING)")
    ap_ = admin.approve(sid)
    print(f"    state={ap_['session_state']}")

    step(9, "Agent reports stage progress")
    for i, (name, pct, tasks, blockers) in enumerate(
        [
            ("Extract payment gateway", 33, ["Carved out PaymentGateway interface"], []),
            ("Idempotency + retries", 66, ["Added idempotency keys", "Added retry policy"],
             [{"severity": "low", "detail": "Waiting on staging creds"}]),
        ],
        start=1,
    ):
        r = agent.report_stage(
            sid,
            stage_payload(
                index=i, name=name, of_total=3, progress_pct=pct,
                completed_tasks=tasks, blockers=blockers,
                commit_message=f"Stage {i}: {name}",
            ),
        )
        print(f"    stage {i} → progress={r['progress_pct']}%  next={r['next_action']}")

    step(10, "Agent uploads the final artifact (COMPLETION → COMPLETED)")
    final_md = markdown_document(
        "Checkout Service Revamp — Completion Report",
        {"type": "completion", "session": sid},
        "All stages complete. Payment gateway extracted, idempotency + retries shipped, tests migrated.",
    )
    done = agent.complete(sid, "completion-report.md", final_md, "Deploy complete")
    print(f"    commit={done['commit_id']}  drive_file={done['gdrive_file_id']}  state={done['session_state']}")

    step(11, "Read the commit timeline (newest first)")
    commits = admin.list_commits(sid)["items"]
    for c in commits:
        print(f"    {c['type']:<13} {c['message']}")

    step(12, "Fetch artifact content back from Google Drive")
    content = admin.get_artifact(done["gdrive_file_id"])["content"]
    print("    --- completion-report.md ---")
    for line in content.splitlines()[:6]:
        print(f"    {line}")

    if args.revoke:
        step(13, "Revoke the agent, then prove its key no longer works")
        admin.revoke_agent(agent_id)
        try:
            agent.check_in(pid)
            print("    UNEXPECTED: check-in succeeded after revocation")
        except OrchestratorError as exc:
            print(f"    ✓ check-in rejected after revocation (HTTP {exc.status})")

    if args.cleanup:
        admin.delete_project(pid)
        print("\n    cleaned up demo project")
    else:
        host = args.base_url.split("/api/")[0]
        print("\n\033[1;32mDone.\033[0m View it on the dashboard:")
        print(f"    project : {host.replace(':8000','').rstrip('/')}  (or :8443 over the tailnet)")
        print(f"    session : .../sessions/{sid}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except OrchestratorError as exc:
        print(f"\n\033[1;31mAPI error\033[0m {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
