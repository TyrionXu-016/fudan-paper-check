const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
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

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const text = await res.text();
    throw new ApiError(res.status, text || res.statusText);
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
  register: (email: string, password: string, name: string) =>
    request<{ access_token: string; user: import("./types").User }>(
      "/v1/auth/register",
      { method: "POST", body: JSON.stringify({ email, password, name }) },
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
};
