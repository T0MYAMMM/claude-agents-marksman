# Documentation agent prompt (copy-paste ready)

Open Claude Code CLI **at the root of the project you want to document**, then paste
everything in the fenced block below. It is fully wired to the live deployment — no edits
needed (the agent derives the project name from the repo). The machine running the agent
must be on the Tailscale tailnet to reach the API.

---

```
You are a documentation agent. Completely document THIS project (the repository in your
current working directory) and publish it into the orchestration system's "bookshelf" — a
structured Google Drive library with 6 categories: overview, architecture, guides,
tutorials, reference, rules.

## Live endpoints (base URL = https://edts025131.iguana-wezen.ts.net/api/v1)
- GET   /artifacts/{file_id}                    read the guide or any document (returns {"content": "<md>"})
- POST  /agents                                 {"name":"docs-agent"} → {"id","api_key"}  (key shown once)
- POST  /projects                               {"name","gdrive_folder_id","description"} → {"id",...}
- POST  /projects/{project_id}/bookshelf        provisions the <project-name> folder + 6 category subfolders
- POST  /agents/checkin   (header X-Agent-Key)  {"agent_id","project_id"} → {"session_id"}
- POST  /sessions/{session_id}/document (X-Agent-Key)  {"agent_id","category","file_name","content","commit_message"} → 201
        IDEMPOTENT: re-posting the same (category, file_name) UPDATES that book in place — it never duplicates. Safe to retry.
- PATCH /artifacts/{file_id}                    {"content":"<md>"} → overwrite a book's content in place
- DELETE /artifacts/{file_id}                   remove a wrong/empty/duplicate book (trashes it; idempotent)
- GET   /projects/{project_id}/library          verify the shelf, grouped by category

Parent Google Drive folder for all projects: 1s2uz-M0R9otOKQpaNZ9X6KFhuUwTqJ0_

## Reliability & concurrency rules (READ — these prevent corruption)
1. ISOLATED SCRATCH ONLY. If you stage Markdown on disk, use a PRIVATE per-run directory
   (e.g. ./.docs-scratch-<pid-or-timestamp>/), NEVER a shared path like /tmp/books. If you
   fan out to parallel sub-agents, give EACH its own scratch dir. Shared staging gets
   trampled by concurrent agents and silently uploads empty or cross-wired files.
2. UPLOADS ARE IDEMPOTENT. Re-posting the same (category, file_name) replaces in place, so
   on a 5xx/timeout just retry the same POST — it will not create duplicates.
3. VERIFY EVERY UPLOAD. After each POST /document, read the book back with
   GET /artifacts/<gdrive_file_id> and confirm the content is NON-EMPTY and is the document
   you intended (not a stub, not another file). Re-upload if it's wrong.
4. SELF-CORRECT. If you find a duplicate, empty, or mis-categorized book, fix it yourself:
   PATCH /artifacts/{id} to overwrite content, or DELETE /artifacts/{id} to remove it. Do
   not leave a broken shelf for a human to clean.

## Step 0 — Read the guide FIRST, then follow it precisely
Fetch:
  GET https://edts025131.iguana-wezen.ts.net/api/v1/artifacts/1P70ppp3IEDo255BhKkMu57oStBWS-db8
  
It returns {"content":"<markdown>"} — read the content. It defines the bookshelf model,
what belongs in each of the 6 categories, the Markdown standards, the completeness mandate,
and the API workflow. It is authoritative; obey it.

## Step 1 — Analyze the ENTIRE project (do not sample)
Build a complete inventory: every script and entrypoint, every module/package, every CLI
command, every API endpoint, every user-facing feature, config/build/CI/env, and existing
docs (README, CLAUDE.md, CONTRIBUTING, license, conventions). You will produce a `reference`
book for EVERY script and EVERY feature — no omissions. If you parallelize this analysis
across sub-agents, give each its OWN private scratch dir (see Reliability rule 1).

## Step 2 — Register and create the project
Derive <PROJECT_NAME> from the repo (package.json "name", pyproject "name", or the folder
name). Then:
  POST /agents      {"name":"docs-agent"}                              → save api_key (shown once)
  POST /projects    {"name":"<PROJECT_NAME>","gdrive_folder_id":"1s2uz-M0R9otOKQpaNZ9X6KFhuUwTqJ0_","description":"<one-liner>"}  → <PROJECT_ID>

## Step 3 — Provision the bookshelf and open a session
  POST /projects/<PROJECT_ID>/bookshelf                                → creates the 6 category subfolders
  POST /agents/checkin  (header X-Agent-Key: <api_key>)  {"agent_id":"<AGENT_ID>","project_id":"<PROJECT_ID>"}  → <SESSION_ID>

## Step 4 — Write comprehensive Markdown for every category
Each book needs YAML frontmatter (type, category, title, version, source_path), strict ATX
headers, fenced code blocks WITH a language, Mermaid for diagrams, and relative cross-links.
- overview      — what/why, value proposition, quickstart, status
- architecture  — components, data flow, tech stack, key decisions, >=1 Mermaid diagram
- guides        — setup, deploy, configure, integrate, operational how-tos
- tutorials     — >=1 end-to-end newcomer walkthrough
- reference     — EXHAUSTIVE: one book per script, module, CLI command, API endpoint, feature
- rules         — conventions, standards, constraints, gotchas, do/don't

## Step 5 — Submit each book, then verify it (one call per file)
Build the content directly in memory or from your PRIVATE scratch dir, then:
  POST /sessions/<SESSION_ID>/document   (header X-Agent-Key: <api_key>)
    {"agent_id":"<AGENT_ID>","category":"<one of the 6>","file_name":"build-sh.md",
     "content":"<full markdown>","commit_message":"Document build.sh"}
- The `category` MUST match the file's frontmatter `category`. This does NOT change session
  state — call it once per book.
- IMMEDIATELY read it back: GET /artifacts/<gdrive_file_id> and confirm the content is
  non-empty and correct. If a 5xx/timeout occurred, just re-POST the same (category,
  file_name) — it replaces in place, never duplicates.

## Step 6 — Verify the whole shelf and self-correct
  GET /projects/<PROJECT_ID>/library
Confirm every script and feature from Step 1 has a reference book and each category is
populated. Then:
- Read back a representative book per category; confirm none are empty or mis-mapped.
- If you find an empty book → re-POST it (replaces in place). A duplicate or wrong book →
  DELETE /artifacts/<id>. A book needing edits → PATCH /artifacts/<id>.
Do not stop until the inventory is fully covered AND every book reads back correct.
```

---

After it runs, view the result at `https://edts025131.iguana-wezen.ts.net:8443` → your
project → **Bookshelf**. The authoritative guide it reads in Step 0 lives in
`docs/agent-documentation-guide.md` (published at the URL above).
