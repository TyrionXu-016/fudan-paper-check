const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API_TIMEOUT_MS = Number(process.env.NEXT_PUBLIC_API_TIMEOUT_MS ?? "15000");
const SERVICE_UNAVAILABLE_MESSAGE = "后端服务暂不可用，请稍后重试。";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function apiErrorFromFetchError(err: unknown): ApiError {
  if (err instanceof ApiError) return err;
  if (err instanceof DOMException && err.name === "AbortError") {
    return new ApiError(0, SERVICE_UNAVAILABLE_MESSAGE);
  }
  if (err instanceof TypeError) {
    return new ApiError(0, SERVICE_UNAVAILABLE_MESSAGE);
  }
  return new ApiError(0, SERVICE_UNAVAILABLE_MESSAGE);
}

async function fetchWithTimeout(input: string, init: RequestInit = {}): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), API_TIMEOUT_MS);
  const onAbort = () => controller.abort();
  init.signal?.addEventListener("abort", onAbort, { once: true });
  try {
    return await fetch(input, { ...init, signal: controller.signal });
  } catch (err) {
    throw apiErrorFromFetchError(err);
  } finally {
    clearTimeout(timeout);
    init.signal?.removeEventListener("abort", onAbort);
  }
}

function parseApiErrorMessage(text: string): string {
  if (!text) return "";
  try {
    const body = JSON.parse(text) as { message?: unknown; detail?: unknown };
    if (typeof body.message === "string" && body.message.trim()) return body.message;
    if (typeof body.detail === "string" && body.detail.trim()) return body.detail;
  } catch {
    return text;
  }
  return text;
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null,
): Promise<T> {
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetchWithTimeout(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const text = await res.text();
    throw new ApiError(res.status, parseApiErrorMessage(text) || res.statusText);
  }
  if (res.status === 204) return undefined as T;
  const contentType = res.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) return res.json();
  return (await res.text()) as T;
}

export const api = {
  baseUrl: API_BASE,
  login: (email: string, password: string) =>
    request<{ access_token: string; user: import("./types").User }>(
      "/v1/auth/login",
      { method: "POST", body: JSON.stringify({ email, password }) },
    ),
  register: (email: string, password: string, name: string, role?: string) =>
    request<{ access_token: string; user: import("./types").User }>(
      "/v1/auth/register",
      { method: "POST", body: JSON.stringify({ email, password, name, role: role ?? "advisor" }) },
    ),
  me: (token: string) =>
    request<import("./types").User>("/v1/auth/me", {}, token),
  listJobs: (token: string) =>
    request<import("./types").JobListItem[]>("/v1/papers", {}, token),
  getJob: (token: string, jobId: string) =>
    request<import("./types").JobListItem & { error?: string }>(
      `/v1/papers/${jobId}`,
      {},
      token,
    ),
  getReport: (token: string, jobId: string) =>
    request<import("./types").CheckReport>(
      `/v1/papers/${jobId}/report`,
      {},
      token,
    ),
  upload: (
    token: string,
    file: File,
    journalProfile: string,
    mineruFile?: File | null,
  ) => {
    const form = new FormData();
    form.append("file", file);
    form.append("journal_profile", journalProfile);
    if (mineruFile) form.append("mineru_file", mineruFile);
    return request<{ job_id: string; status: string }>(
      "/v1/papers",
      { method: "POST", body: form },
      token,
    );
  },
  reportMarkdownUrl: (jobId: string) => `${API_BASE}/v1/papers/${jobId}/report.md`,
  mseDashboard: (token: string) =>
    request<import("./types").MseDashboardResponse>("/v1/mse/dashboard", {}, token),
  createMseProject: (
    token: string,
    body: {
      title: string;
      student_email?: string;
      advisor_email?: string;
      auto_notify_student?: boolean;
    },
  ) =>
    request<import("./types").MseProject>(
      "/v1/mse/projects",
      { method: "POST", body: JSON.stringify(body) },
      token,
    ),
  listMseProjects: (token: string) =>
    request<import("./types").MseProject[]>("/v1/mse/projects", {}, token),
  getMseProject: (token: string, projectId: string) =>
    request<import("./types").MseProject>(`/v1/mse/projects/${projectId}`, {}, token),
  listMseRounds: (token: string, projectId: string) =>
    request<import("./types").MseSubmissionRound[]>(
      `/v1/mse/projects/${projectId}/rounds`,
      {},
      token,
    ),
  getMseRoundReport: (token: string, projectId: string, roundNumber: number) =>
    request<import("./types").MseRoundReport>(
      `/v1/mse/projects/${projectId}/rounds/${roundNumber}/report`,
      {},
      token,
    ),
  submitMsePaperViaInvite: (inviteToken: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<{ round_id: string; round_number: number; job_id: string }>(
      `/v1/mse/invites/${encodeURIComponent(inviteToken)}/submissions`,
      { method: "POST", body: form },
    );
  },
  submitMsePaper: (token: string, projectId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<{ round_id: string; round_number: number; job_id: string }>(
      `/v1/mse/projects/${projectId}/submissions`,
      { method: "POST", body: form },
      token,
    );
  },
  releaseMseRound: (token: string, projectId: string, roundNumber: number) =>
    request<import("./types").MseRoundReport>(
      `/v1/mse/projects/${projectId}/rounds/${roundNumber}/release`,
      { method: "POST", body: JSON.stringify({}) },
      token,
    ),
  dismissMseIssue: (
    token: string,
    projectId: string,
    roundNumber: number,
    fingerprint: string,
    reason?: string,
  ) =>
    request<{ status: string }>(
      `/v1/mse/projects/${projectId}/rounds/${roundNumber}/issues/${encodeURIComponent(fingerprint)}/dismiss`,
      { method: "POST", body: JSON.stringify({ reason: reason ?? "" }) },
      token,
    ),
  retryMseRound: (token: string, projectId: string, roundNumber: number) =>
    request<{ status: string; round_id: string }>(
      `/v1/mse/projects/${projectId}/rounds/${roundNumber}/retry`,
      { method: "POST", body: JSON.stringify({}) },
      token,
    ),
  uploadMseRules: (token: string, projectId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<import("./types").MseProject>(
      `/v1/mse/projects/${projectId}/rules`,
      { method: "POST", body: form },
      token,
    );
  },
  uploadMseDefaultRules: (token: string, projectId: string) =>
    request<import("./types").MseProject>(
      `/v1/mse/projects/${projectId}/rules/default`,
      { method: "POST", body: JSON.stringify({}) },
      token,
    ),
  getInnovationReview: (token: string, projectId: string) =>
    request<import("./types").InnovationReview>(
      `/v1/mse/projects/${projectId}/innovation-review`,
      {},
      token,
    ),
  submitInnovationReview: (
    token: string,
    projectId: string,
    body: { advisor_comment: string; advisor_decision: "approve" | "revise" | "reject" },
  ) =>
    request<import("./types").InnovationReview>(
      `/v1/mse/projects/${projectId}/innovation-review`,
      { method: "POST", body: JSON.stringify(body) },
      token,
    ),
  getInviteInfo: (inviteToken: string) =>
    request<import("./types").InviteInfo>(`/v1/mse/invites/${encodeURIComponent(inviteToken)}`),
  acceptInvite: (token: string, inviteToken: string) =>
    request<import("./types").MseProject>(
      `/v1/mse/invites/${encodeURIComponent(inviteToken)}/accept`,
      { method: "POST", body: JSON.stringify({}) },
      token,
    ),
  inviteMember: (token: string, projectId: string, email?: string) =>
    request<{ invite_url: string; token: string }>(
      `/v1/mse/projects/${projectId}/invite`,
      { method: "POST", body: JSON.stringify({ email, send_email: false }) },
      token,
    ),
  downloadMseRoundExport: async (
    token: string,
    projectId: string,
    roundNumber: number,
    format: "md" | "pdf",
  ) => {
    const res = await fetchWithTimeout(
      `${API_BASE}/v1/mse/projects/${projectId}/rounds/${roundNumber}/export.${format}`,
      { headers: { Authorization: `Bearer ${token}` } },
    );
    if (!res.ok) {
      throw new ApiError(res.status, await res.text());
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `round-${roundNumber}.${format}`;
    a.click();
    URL.revokeObjectURL(url);
  },
};
