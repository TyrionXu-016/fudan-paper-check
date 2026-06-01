import type { Issue } from "./types";

export async function issueFingerprint(issue: Issue): Promise<string> {
  const page = issue.page ?? issue.line ?? 0;
  const ruleRef = issue.rule_ref ?? "";
  const msg = (issue.message ?? "").slice(0, 50);
  const key = `${ruleRef}|${issue.section ?? ""}|${page}|${msg}`;
  const data = new TextEncoder().encode(key);
  const hash = await crypto.subtle.digest("SHA-256", data);
  const hex = Array.from(new Uint8Array(hash))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
  return hex.slice(0, 16);
}

const PROJECT_STATUS: Record<string, string> = {
  draft: "草稿",
  pending_member: "待绑定成员",
  active: "进行中",
  analyzing: "分析中",
  awaiting_advisor: "待导师终审",
  completed: "已完成",
  archived: "已归档",
};

const REVIEW_STATUS: Record<string, string> = {
  pending: "待处理",
  parsing: "解析中",
  parse_failed: "解析失败",
  analyzing: "分析中",
  analysis_failed: "分析失败",
  pending_release: "待导师发布",
  issues_found: "发现问题",
  passed: "已通过",
  failed: "失败",
};

export function projectStatusLabel(status: string): string {
  return PROJECT_STATUS[status] ?? status;
}

export function reviewStatusLabel(status: string): string {
  return REVIEW_STATUS[status] ?? status;
}

export function reviewStatusClass(status: string): string {
  if (status === "passed") return "bg-emerald-100 text-emerald-800";
  if (status === "pending_release") return "bg-violet-100 text-violet-800";
  if (status.endsWith("failed")) return "bg-red-100 text-red-800";
  if (status === "issues_found") return "bg-amber-100 text-amber-800";
  if (status === "parsing" || status === "analyzing") return "bg-blue-100 text-blue-800";
  return "bg-stone-100 text-stone-700";
}
