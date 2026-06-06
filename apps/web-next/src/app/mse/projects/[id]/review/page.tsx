"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { AppShell, LoadingScreen } from "@/components/ui/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { api } from "@/lib/api";
import { projectStatusLabel } from "@/lib/mse";
import { useAuth } from "@/lib/auth";
import type { InnovationReview, MseProject } from "@/lib/types";

const DECISIONS = [
  { value: "approve" as const, label: "通过", desc: "论文达到要求，辅导完成" },
  { value: "revise" as const, label: "需修改", desc: "退回学生继续改稿" },
  { value: "reject" as const, label: "不予通过", desc: "创新性或质量未达标" },
];

export default function MseInnovationReviewPage() {
  const params = useParams();
  const projectId = params.id as string;
  const { user, token, loading } = useAuth();
  const router = useRouter();
  const [project, setProject] = useState<MseProject | null>(null);
  const [review, setReview] = useState<InnovationReview | null>(null);
  const [comment, setComment] = useState("");
  const [decision, setDecision] = useState<"approve" | "revise" | "reject">("approve");
  const [fetching, setFetching] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!token) return;
    const p = await api.getMseProject(token, projectId);
    setProject(p);
    try {
      const r = await api.getInnovationReview(token, projectId);
      setReview(r);
      if (r.advisor_comment) setComment(r.advisor_comment);
      if (r.advisor_decision) setDecision(r.advisor_decision);
    } catch {
      setReview(null);
    }
  }, [token, projectId]);

  useEffect(() => {
    if (loading) return;
    if (!token) {
      router.replace("/login");
      return;
    }
    if ((user?.role ?? "advisor") !== "advisor") {
      router.replace(`/mse/projects/${projectId}`);
      return;
    }
    load()
      .catch((e) => setError(e instanceof Error ? e.message : "加载失败"))
      .finally(() => setFetching(false));
  }, [loading, token, user, router, projectId, load]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!token) return;
    setSubmitting(true);
    setError("");
    try {
      const updated = await api.submitInnovationReview(token, projectId, {
        advisor_comment: comment,
        advisor_decision: decision,
      });
      setReview(updated);
      router.push(`/mse/projects/${projectId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "提交失败");
    } finally {
      setSubmitting(false);
    }
  }

  if (fetching) {
    return <LoadingScreen />;
  }

  const alreadyReviewed = Boolean(review?.advisor_decision && review.reviewed_at);

  return (
    <AppShell width="narrow">
      <PageHeader
        eyebrow="终审"
        title="创新性审查"
        description={
          project
            ? `${project.title} · ${projectStatusLabel(project.status)}`
            : undefined
        }
        backHref={`/mse/projects/${projectId}`}
        backLabel="项目"
      />

      {!review ? (
        <div className="alert alert-warn">尚无 LLM 预审结果。请确认最新轮次已通过格式门禁并完成分析。</div>
      ) : (
        <div className="space-y-6">
          {review.novelty_score != null && (
            <div className="card-surface p-6">
              <p className="ui-label">创新性参考</p>
              <p className="stat-value mt-2 text-vermillion">
                {(review.novelty_score * 100).toFixed(0)}%
              </p>
            </div>
          )}

          <ReviewSection title="预审摘要">
            <p className="whitespace-pre-wrap text-sm leading-7 text-ink-muted">{review.llm_summary}</p>
          </ReviewSection>

          <ReviewSection title="与领域对比">
            <p className="text-sm leading-7 text-ink-muted">{review.comparison_notes}</p>
          </ReviewSection>

          {review.strengths && review.strengths.length > 0 && (
            <ReviewSection title="优势">
              <ul className="list-inside list-disc text-sm text-ink-muted">
                {review.strengths.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </ReviewSection>
          )}

          {review.weaknesses && review.weaknesses.length > 0 && (
            <ReviewSection title="不足">
              <ul className="list-inside list-disc text-sm text-ink-muted">
                {review.weaknesses.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </ReviewSection>
          )}

          {review.suggested_questions && review.suggested_questions.length > 0 && (
            <ReviewSection title="建议追问">
              <ul className="list-inside list-decimal text-sm text-ink-muted">
                {review.suggested_questions.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </ReviewSection>
          )}
        </div>
      )}

      {alreadyReviewed ? (
        <div className="alert alert-info mt-8">
          已于 {review?.reviewed_at?.slice(0, 19)} 提交终审结论：
          {review?.advisor_decision === "approve"
            ? "通过"
            : review?.advisor_decision === "revise"
              ? "需修改"
              : "不予通过"}
          {review?.advisor_comment && (
            <p className="mt-2 text-ink-muted">评语：{review.advisor_comment}</p>
          )}
        </div>
      ) : (
        review && (
          <form onSubmit={handleSubmit} className="card-surface mt-8 space-y-5 p-6">
            <h3 className="display-title text-lg">导师终审</h3>
            <fieldset className="space-y-3">
              {DECISIONS.map((d) => (
                <label
                  key={d.value}
                  className={`flex cursor-pointer gap-3 rounded-xl border p-4 transition-colors ${
                    decision === d.value
                      ? "border-vermillion/40 bg-paper-deep"
                      : "border-ink/10 hover:border-ink/20"
                  }`}
                >
                  <input
                    type="radio"
                    name="decision"
                    value={d.value}
                    checked={decision === d.value}
                    onChange={() => setDecision(d.value)}
                    className="mt-1"
                  />
                  <span>
                    <span className="font-medium text-ink">{d.label}</span>
                    <span className="mt-0.5 block font-[family-name:var(--font-sans)] text-xs text-ink-faint">
                      {d.desc}
                    </span>
                  </span>
                </label>
              ))}
            </fieldset>
            <label className="block font-[family-name:var(--font-sans)] text-sm text-ink-muted">
              评语（可选）
              <textarea
                className="input-field min-h-[6rem] resize-y"
                rows={4}
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="给学生的终审意见…"
              />
            </label>
            {error && <p className="text-sm text-vermillion">{error}</p>}
            <button type="submit" disabled={submitting} className="btn btn-primary w-full py-3">
              {submitting ? "提交中…" : "提交终审结论"}
            </button>
          </form>
        )
      )}
    </AppShell>
  );
}

function ReviewSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="card-surface p-5">
      <h3 className="ui-label mb-3">{title}</h3>
      {children}
    </section>
  );
}
