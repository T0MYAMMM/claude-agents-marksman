# Continuous-documentation prompt (append below a project's main prompt)

For a **new project under active development**, paste the fenced block below **underneath your
main prompt** (the main prompt holds the project requirements, the agent's TODOs, etc.). This
addendum makes the building agent document the project **continuously, from the very first
commit**, into the orchestration bookshelf — instead of one big pass at the end. It reuses the
same project across sessions (no duplicates) and follows the document-project procedure rules.

The machine must be on the Tailscale tailnet to reach the API.

---

```
## Continuous documentation directive (in addition to building this project)

As you build this project, you ALSO maintain living documentation of it in the orchestration
system's "bookshelf" — a Google Drive library with 6 categories: overview, architecture,
guides, tutorials, reference, rules. Document every meaningful update FROM THE BEGINNING; do
not defer docs to the end. Keep them in sync with the code as it evolves.

API base URL: https://edts025131.iguana-wezen.ts.net/api/v1
Parent Google Drive folder: 1s2uz-M0R9otOKQpaNZ9X6KFhuUwTqJ0_

### A. One-time bootstrap (first run only — then reuse)
Maintain a gitignored state file `./.orchestration/state.json` so you reuse the SAME project
on every session (never create a duplicate project).
- If `.orchestration/state.json` exists: load {agent_id, api_key, project_id}. Open a fresh
  session: POST /agents/checkin {agent_id, project_id} (header X-Agent-Key) → session_id.
- If it does NOT exist, bootstrap once:
  1. Derive <PROJECT_NAME> from the repo (package.json / pyproject "name", or folder name).
  2. POST /agents {"name":"docs-agent"} → {id, api_key}              (api_key shown once)
  3. POST /projects {"name":"<PROJECT_NAME>","gdrive_folder_id":"1s2uz-M0R9otOKQpaNZ9X6KFhuUwTqJ0_","description":"<one-liner>"} → project_id
  4. POST /projects/<project_id>/bookshelf                            (creates the 6 subfolders)
  5. POST /agents/checkin {agent_id, project_id} (X-Agent-Key)        → session_id
  6. Write {agent_id, api_key, project_id} to `./.orchestration/state.json` and add
     `.orchestration/` to .gitignore.

### B. Read the rules once
Fetch the authoritative guide and obey it (categories, Markdown standards, completeness,
reliability rules):
  GET https://edts025131.iguana-wezen.ts.net/api/v1/artifacts/1P70ppp3IEDo255BhKkMu57oStBWS-db8

### C. When to document (cadence — document as you go, not in a batch)
After EACH meaningful unit of work, create or UPDATE the relevant book(s):
- New/changed feature      → a `guides` how-to and/or `reference` book; update `overview`.
- New module/script/CLI/endpoint → a `reference` book (one per item).
- Architectural decision or new component → update `architecture` (record the decision; add or
  revise a Mermaid diagram).
- A feature becomes usable end-to-end → a `tutorials` walkthrough.
- A convention/constraint you adopt → a `rules` book.
- Project vision/status changes → update `overview`.
Treat docs like tests: part of "done" for each change, not an afterthought.

### D. How to write and submit (follows the document-project procedure)
- Markdown standards: YAML frontmatter (type, category, title, version, source_path), strict
  ATX headers, fenced code blocks WITH a language, Mermaid for diagrams, relative cross-links.
- Submit/refresh a book (idempotent — re-posting the same file_name UPDATES it in place):
    POST /sessions/<session_id>/document  (header X-Agent-Key: <api_key>)
      {"agent_id":"<agent_id>","category":"<one of the 6>","file_name":"<stable-name>.md",
       "content":"<full markdown>","commit_message":"<what changed>"}
  Use a STABLE file_name per topic (e.g. `auth-module.md`) so updates replace, not duplicate.
- To edit content directly: PATCH /artifacts/<file_id> {"content":"<md>"}.
- To remove an obsolete/duplicate/wrong book: DELETE /artifacts/<file_id>.

### E. Mandatory reliability rules (these prevent corruption)
1. ISOLATED SCRATCH ONLY — if you stage Markdown on disk, use a PRIVATE per-run dir
   (`./.docs-scratch-<pid>/`), never a shared path; give each parallel sub-agent its own.
2. IDEMPOTENT UPLOADS — re-posting the same (category, file_name) replaces in place; on a
   5xx/timeout just retry the same POST (it never duplicates).
3. VERIFY EVERY UPLOAD — after each POST /document, GET /artifacts/<file_id> and confirm the
   content is non-empty and correct.
4. SELF-CORRECT — fix your own mess with PATCH (overwrite) or DELETE (remove). Never leave an
   empty, duplicate, or mis-categorized book on the shelf.

### F. Keep it honest and current
- When code changes, update the matching book in the same commit/turn (same file_name).
- Periodically GET /projects/<project_id>/library and confirm every script/feature/module has
  a current book and no category is stale. Close gaps immediately.
- View the shelf at https://edts025131.iguana-wezen.ts.net:8443 → this project → Bookshelf.
```

---

Result: the project's bookshelf grows alongside the code — overview/architecture/guides/
tutorials/reference/rules stay current from day one — and because uploads are idempotent on a
stable `file_name`, re-documenting a changed module simply refreshes its book.
