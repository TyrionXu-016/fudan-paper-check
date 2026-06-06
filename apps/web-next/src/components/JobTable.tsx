import type { JobListItem } from "@/lib/types";

const STATUS_LABEL: Record<string, string> = {
  queued: "排队中",
  converting: "转换中",
  parsing: "解析中",
  checking: "检查中",
  done: "已完成",
  failed: "失败",
};

const STATUS_CLASS: Record<string, string> = {
  done: "badge badge-passed",
  failed: "badge badge-failed",
  checking: "badge badge-issues",
  parsing: "badge badge-progress",
  converting: "badge badge-progress",
  queued: "badge badge-neutral",
};

export function JobTable({ jobs }: { jobs: JobListItem[] }) {
  if (!jobs.length) {
    return (
      <div className="card-surface border border-dashed border-ink/15 p-12 text-center text-ink-muted">
        暂无历史任务，去上传第一篇论文吧。
      </div>
    );
  }

  return (
    <div className="card-surface overflow-hidden">
      <table className="issue-table">
        <thead>
          <tr>
            <th>论文</th>
            <th>文件</th>
            <th>状态</th>
            <th>结果</th>
            <th>更新时间</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <tr key={job.job_id} className="issue-row--info">
              <td>
                <a href={`/jobs/${job.job_id}`} className="font-medium text-vermillion hover:underline">
                  {job.paper_title || "（处理中）"}
                </a>
              </td>
              <td className="text-ink-muted">{job.filename || "—"}</td>
              <td>
                <span className={STATUS_CLASS[job.status] ?? "badge badge-neutral"}>
                  {STATUS_LABEL[job.status] || job.status}
                </span>
              </td>
              <td className="text-ink-muted">
                {job.summary
                  ? `${job.summary.errors} 错 / ${job.summary.warnings} 警 / ${job.summary.infos} 提示`
                  : "—"}
              </td>
              <td className="font-[family-name:var(--font-sans)] text-xs text-ink-faint">
                {job.updated_at ? new Date(job.updated_at).toLocaleString("zh-CN") : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
