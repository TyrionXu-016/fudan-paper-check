export type User = {
  id: string;
  email: string;
  name: string;
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
  code: string;
  category: string;
  severity: "error" | "warning" | "info";
  section?: string | null;
  line?: number | null;
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
