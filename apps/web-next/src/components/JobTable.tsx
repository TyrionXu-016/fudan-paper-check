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
  done: "bg-emerald-100 text-emerald-800",
  failed: "bg-red-100 text-red-800",
  checking: "bg-amber-100 text-amber-800",
  parsing: "bg-amber-100 text-amber-800",
  converting: "bg-amber-100 text-amber-800",
  queued: "bg-stone-100 text-stone-700",
};

export function JobTable({ jobs }: { jobs: JobListItem[] }) {
  if (!jobs.length) {
    return (
      <div className="rounded-2xl border border-dashed border-stone-300 bg-white p-10 text-center text-stone-500">
        暂无历史任务，去上传第一篇论文吧。
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm">
      <table className="min-w-full text-left text-sm">
        <thead className="bg-stone-50 text-stone-500">
          <tr>
            <th className="px-4 py-3 font-medium">论文</th>
            <th className="px-4 py-3 font-medium">文件</th>
            <th className="px-4 py-3 font-medium">状态</th>
            <th className="px-4 py-3 font-medium">结果</th>
            <th className="px-4 py-3 font-medium">更新时间</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <tr key={job.job_id} className="border-t border-stone-100 hover:bg-stone-50">
              <td className="px-4 py-3">
                <a href={`/jobs/${job.job_id}`} className="font-medium text-teal-700 hover:underline">
                  {job.paper_title || "（处理中）"}
                </a>
              </td>
              <td className="px-4 py-3 text-stone-600">{job.filename || "—"}</td>
              <td className="px-4 py-3">
                <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${STATUS_CLASS[job.status]}`}>
                  {STATUS_LABEL[job.status] || job.status}
                </span>
              </td>
              <td className="px-4 py-3 text-stone-600">
                {job.summary
                  ? `${job.summary.errors} 错 / ${job.summary.warnings} 警 / ${job.summary.infos} 提示`
                  : "—"}
              </td>
              <td className="px-4 py-3 text-stone-500">
                {job.updated_at ? new Date(job.updated_at).toLocaleString("zh-CN") : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
