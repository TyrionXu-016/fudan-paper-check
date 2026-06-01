export type User = {
  id: string;
  email: string;
  name: string;
  role?: string;
};

export type JobStatus =
  | "queued"
  | "converting"
  | "parsing"
  | "checking"
  | "done"
  | "failed";

export type JobListItem = {
  job_id: string;
  status: JobStatus;
  journal_profile: string;
  filename?: string | null;
  paper_title?: string | null;
  summary?: {
    errors: number;
    warnings: number;
    infos: number;
  } | null;
  created_at: string;
  updated_at: string;
};

export type Issue = {
  id?: string;
  code: string;
  category: string;
  severity: "error" | "warning" | "info";
  section?: string | null;
  line?: number | null;
  page?: number | null;
  page_line?: string | null;
  rule_ref?: string | null;
  revision_hint?: string | null;
  original_text?: string | null;
  suggested_text?: string | null;
  message: string;
  suggestion?: string;
  evidence?: string;
};

export type CheckReport = {
  job_id: string;
  paper_title: string;
  parse_quality: {
    fusion_score: number;
    maker_score: number;
    mineru_score: number;
    fusion_warnings: string[];
    degraded: boolean;
  };
  summary: { errors: number; warnings: number; infos: number };
  issues: Issue[];
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
  user: User;
};

export type MseDashboardTodo = {
  type: string;
  project_id: string;
  title: string;
  round_number?: number | null;
  urgency?: string;
};

export type MseDashboardActivity = {
  at: string;
  event: string;
  project_id: string;
  summary: string;
};

export type MseDashboardResponse = {
  advisor?: {
    role: "advisor";
    stats: {
      total_projects: number;
      active: number;
      pending_release: number;
      awaiting_advisor: number;
      parse_failed: number;
      completed: number;
    };
    todos: MseDashboardTodo[];
    activity: MseDashboardActivity[];
  };
  student?: {
    role: "student";
    stats: {
      my_projects: number;
      in_revision: number;
      awaiting_advisor: number;
      completed: number;
    };
    action_required: MseDashboardTodo[];
    recent: MseDashboardActivity[];
  };
};

export type MseProject = {
  id: string;
  title: string;
  initiator_role: string;
  advisor_id?: string | null;
  advisor_email?: string | null;
  student_id?: string | null;
  student_email?: string | null;
  rule_base_ids?: string[];
  status: string;
  current_round: number;
  auto_notify_student: boolean;
  created_at?: string;
  updated_at?: string;
};

export type MseSubmissionRound = {
  id: string;
  project_id: string;
  round_number: number;
  job_id: string;
  review_status: string;
  issue_count: number;
  error_count: number;
  warning_count: number;
  gate_passed?: boolean | null;
  gate_reason?: string;
  submitted_at?: string;
  analyzed_at?: string | null;
  released_at?: string | null;
};

export type RoundIssueDiff = {
  base_round: number;
  current_round: number;
  fixed: Issue[];
  new: Issue[];
  persistent: Issue[];
  dismissed: Issue[];
};

export type MseRoundReport = {
  project_id: string;
  round_number: number;
  round_id: string;
  review_status: string;
  released: boolean;
  gate?: {
    round_id: string;
    passed: boolean;
    reason: string;
    notify_target: string;
  } | null;
  diff?: RoundIssueDiff | null;
  report?: CheckReport | null;
  innovation_preview?: InnovationReview | null;
};

export type InviteInfo = {
  token: string;
  project_id: string;
  project_title: string;
  target_role: string;
  target_email: string;
  expires_at: string;
  used: boolean;
  expired: boolean;
};

export type InnovationReview = {
  id: string;
  project_id: string;
  round_id: string;
  llm_summary: string;
  novelty_score?: number | null;
  comparison_notes: string;
  strengths?: string[];
  weaknesses?: string[];
  suggested_questions?: string[];
  advisor_comment?: string;
  advisor_decision?: "approve" | "revise" | "reject" | null;
  reviewed_at?: string | null;
  created_at?: string;
};
