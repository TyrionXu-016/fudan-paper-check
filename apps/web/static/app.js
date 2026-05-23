const STATUS_PROGRESS = {
  queued: 10,
  converting: 30,
  parsing: 50,
  checking: 75,
  done: 100,
  failed: 100,
};

const STATUS_LABEL = {
  queued: "排队中",
  converting: "PDF 转换中",
  parsing: "文档解析中",
  checking: "执行检查",
  done: "已完成",
  failed: "失败",
};

let currentJobId = null;
let pollTimer = null;
let latestReport = null;

const el = (id) => document.getElementById(id);

async function checkHealth() {
  const pill = el("apiStatus");
  try {
    const res = await fetch("/health");
    if (!res.ok) throw new Error("bad status");
    pill.textContent = "服务在线";
    pill.classList.add("ok");
  } catch {
    pill.textContent = "服务不可用";
    pill.classList.add("bad");
  }
}

function showJobPanel(job) {
  el("jobEmpty").classList.add("hidden");
  el("jobPanel").classList.remove("hidden");
  el("jobId").textContent = job.job_id;
  el("jobJournal").textContent = job.journal_profile || "—";
  el("jobUpdated").textContent = job.updated_at || "—";

  const status = job.status;
  const badge = el("jobStatus");
  badge.textContent = STATUS_LABEL[status] || status;
  badge.className = `badge ${status}`;

  const progress = STATUS_PROGRESS[status] ?? 0;
  el("progressFill").style.width = `${progress}%`;
  el("progressText").textContent =
    status === "failed"
      ? job.error || "任务失败"
      : status === "done"
        ? "检查完成，报告已生成"
        : `${STATUS_LABEL[status] || status}…`;
}

function renderSummary(report) {
  const grid = el("summaryGrid");
  const s = report.summary;
  grid.innerHTML = `
    <div class="summary-item"><strong>${report.paper_title || "—"}</strong><span>论文标题</span></div>
    <div class="summary-item error"><strong>${s.errors}</strong><span>错误</span></div>
    <div class="summary-item warning"><strong>${s.warnings}</strong><span>警告</span></div>
    <div class="summary-item info"><strong>${s.infos}</strong><span>提示</span></div>
  `;

  const q = report.parse_quality;
  const warnings = (q.fusion_warnings || []).map((w) => `<li>${escapeHtml(w)}</li>`).join("");
  el("qualityBox").innerHTML = `
    <strong>解析质量</strong><br />
    融合得分 ${q.fusion_score} · Maker ${q.maker_score} · MinerU ${q.mineru_score}
    ${q.degraded ? " · <em>已启用降级模式</em>" : ""}
    ${warnings ? `<ul>${warnings}</ul>` : ""}
  `;
}

function renderIssues(issues) {
  const list = el("issuesList");
  if (!issues.length) {
    list.innerHTML = '<div class="empty">未发现问题</div>';
    return;
  }

  list.innerHTML = issues
    .map((issue) => {
      const loc = [issue.section, issue.line ? `L${issue.line}` : ""]
        .filter(Boolean)
        .join(" · ");
      return `
        <article class="issue ${issue.severity}">
          <div class="issue-head">
            <code>${escapeHtml(issue.code)}</code>
            <span>${escapeHtml(issue.category)} · ${escapeHtml(issue.severity)}</span>
          </div>
          <p>${escapeHtml(issue.message)}</p>
          ${issue.suggestion ? `<small>建议：${escapeHtml(issue.suggestion)}</small>` : ""}
          ${issue.evidence ? `<small>证据：${escapeHtml(issue.evidence)}</small>` : ""}
          ${loc ? `<small>位置：${escapeHtml(loc)}</small>` : ""}
        </article>
      `;
    })
    .join("");
}

function showReport(report) {
  latestReport = report;
  el("reportEmpty").classList.add("hidden");
  el("reportPanel").classList.remove("hidden");
  el("reportActions").classList.remove("hidden");
  renderSummary(report);
  renderIssues(report.issues || []);
}

async function fetchReport(jobId) {
  const res = await fetch(`/v1/papers/${jobId}/report`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function pollJob(jobId) {
  clearInterval(pollTimer);
  pollTimer = setInterval(async () => {
    try {
      const res = await fetch(`/v1/papers/${jobId}`);
      if (!res.ok) throw new Error("job not found");
      const job = await res.json();
      showJobPanel(job);

      if (job.status === "done") {
        clearInterval(pollTimer);
        const report = await fetchReport(jobId);
        showReport(report);
        el("submitBtn").disabled = false;
      } else if (job.status === "failed") {
        clearInterval(pollTimer);
        el("submitBtn").disabled = false;
      }
    } catch (err) {
      clearInterval(pollTimer);
      el("progressText").textContent = `轮询失败：${err.message}`;
      el("submitBtn").disabled = false;
    }
  }, 1200);
}

el("uploadForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const mainFile = el("mainFile").files[0];
  if (!mainFile) return;

  el("submitBtn").disabled = true;
  el("reportEmpty").classList.remove("hidden");
  el("reportPanel").classList.add("hidden");
  el("reportActions").classList.add("hidden");

  const formData = new FormData();
  formData.append("file", mainFile);
  formData.append("journal_profile", el("journalProfile").value);
  const mineru = el("mineruFile").files[0];
  if (mineru) formData.append("mineru_file", mineru);

  try {
    const res = await fetch("/v1/papers", { method: "POST", body: formData });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    currentJobId = data.job_id;
    showJobPanel({ job_id: data.job_id, status: data.status, journal_profile: el("journalProfile").value });
    await pollJob(currentJobId);
  } catch (err) {
    el("progressText").textContent = `上传失败：${err.message}`;
    el("submitBtn").disabled = false;
  }
});

el("copyJsonBtn").addEventListener("click", async () => {
  if (!latestReport) return;
  await navigator.clipboard.writeText(JSON.stringify(latestReport, null, 2));
  el("copyJsonBtn").textContent = "已复制";
  setTimeout(() => { el("copyJsonBtn").textContent = "复制 JSON"; }, 1500);
});

el("downloadMdBtn").addEventListener("click", () => {
  if (!currentJobId) return;
  window.open(`/v1/papers/${currentJobId}/report.md`, "_blank");
});

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

checkHealth();
