// TypeScript mirrors of the backend Pydantic contracts.

export type SessionState =
  | "INIT"
  | "PLANNING"
  | "WAITING_FOR_HUMAN"
  | "REFINING"
  | "EXECUTING"
  | "COMPLETED"
  | "FAILED"
  | "TERMINATED";

export type CommitType =
  | "PLAN"
  | "REVISION"
  | "STAGE_REPORT"
  | "COMPLETION"
  | "DOC";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  reply: string;
  revised_markdown: string | null;
}

export interface Project {
  id: string;
  name: string;
  description: string | null;
  gdrive_folder_id: string;
  created_at: string;
  updated_at: string;
}

export interface SessionSummary {
  id: string;
  project_id: string;
  title: string;
  state: SessionState;
  progress_pct: number;
  started_at: string;
  ended_at: string | null;
}

export interface Commit {
  id: string;
  session_id: string;
  agent_id: string;
  type: CommitType;
  message: string;
  parent_commit_id: string | null;
  gdrive_ref_id: string | null;
  payload: Record<string, unknown> | null;
  created_at: string;
}

export interface CommitPage {
  items: Commit[];
  next_cursor: string | null;
}

export interface Feedback {
  id: string;
  session_id: string;
  commit_id: string | null;
  comment: string;
  resolved: boolean;
  created_at: string;
}

// --- Bookshelf / Library -----------------------------------------------------

export type BookCategory =
  | "overview"
  | "architecture"
  | "guides"
  | "tutorials"
  | "reference"
  | "rules";

/** A single document on a shelf (maps to /artifacts/[fileId]). */
export interface Document {
  gdrive_file_id: string;
  file_name: string;
  category: BookCategory;
  web_view_link: string | null;
  created_at: string;
}

/** Alias used by the bookshelf UI ("book" reads better than "document"). */
export type Book = Document;

/** One category's documents, as returned by the library endpoint. */
export interface CategorySection {
  category: BookCategory;
  documents: Document[];
}

/** Backend contract: GET /projects/{id}/library */
export interface Library {
  project_id: string;
  bookshelf_folder_id: string | null;
  sections: CategorySection[];
}

// --- Overview / Stats --------------------------------------------------------

export interface OverviewTotals {
  projects: number;
  sessions: number;
  agents: number;
  commits: number;
  documents: number;
}

export interface SessionsByState {
  state: string;
  count: number;
}

export interface AgentsByStatus {
  status: string;
  count: number;
}

export interface CommitsByType {
  type: string;
  count: number;
}

export interface ActivityPoint {
  date: string;
  commits: number;
}

/** A lightweight session row for the dashboard recent-activity list. */
export interface RecentSession {
  id: string;
  title: string;
  project_id: string;
  state: SessionState;
  progress_pct: number;
  started_at: string;
}

/** Backend contract: GET /stats/overview */
export interface OverviewStats {
  totals: OverviewTotals;
  sessions_by_state: SessionsByState[];
  agents_by_status: AgentsByStatus[];
  commits_by_type: CommitsByType[];
  activity: ActivityPoint[];
  recent_sessions: RecentSession[];
}
