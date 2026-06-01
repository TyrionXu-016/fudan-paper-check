"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Navbar } from "@/components/Navbar";
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
    return <div className="flex min-h-screen items-center justify-center text-stone-500">加载中…</div>;
  }

  const alreadyReviewed = Boolean(review?.advisor_decision && review.reviewed_at);

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,#faf7f0,#f4f1ea)]">
      <Navbar />
      <main className="mx-auto max-w-3xl px-6 py-8">
        <Link href={`/mse/projects/${projectId}`} className="text-sm text-teal-700 hover:underline">
          ← 返回项目
        </Link>
        <h2 className="mt-4 text-2xl font-semibold text-stone-900">创新性审查</h2>
        {project && (
          <p className="mt-1 text-sm text-stone-500">
            {project.title} · {projectStatusLabel(project.status)}
          </p>
        )}

        {!review ? (
          <div className="mt-8 rounded-2xl bg-amber-50 p-6 text-sm text-amber-900">
            尚无 LLM 预审结果。请确认最新轮次已通过格式门禁并完成分析。
          </div>
        ) : (
          <div className="mt-8 space-y-6">
            {review.novelty_score != null && (
              <div className="rounded-2xl bg-white p-5 ring-1 ring-stone-200/80">
                <p className="text-xs text-stone-500">创新性参考分（0–1）</p>
                <p className="text-3xl font-semibold text-teal-800">
                  {(review.novelty_score * 100).toFixed(0)}%
                </p>
              </div>
            )}

            <Section title="预审摘要">
              <p className="whitespace-pre-wrap text-sm leading-7 text-stone-700">{review.llm_summary}</p>
            </Section>

            <Section title="与领域对比">
              <p className="text-sm leading-7 text-stone-700">{review.comparison_notes}</p>
            </Section>

            {review.strengths && review.strengths.length > 0 && (
              <Section title="优势">
                <ul className="list-inside list-disc text-sm text-stone-700">
                  {review.strengths.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              </Section>
            )}

            {review.weaknesses && review.weaknesses.length > 0 && (
              <Section title="不足">
                <ul className="list-inside list-disc text-sm text-stone-700">
                  {review.weaknesses.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              </Section>
            )}

            {review.suggested_questions && review.suggested_questions.length > 0 && (
              <Section title="建议追问">
                <ul className="list-inside list-decimal text-sm text-stone-700">
                  {review.suggested_questions.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              </Section>
            )}
          </div>
        )}

        {alreadyReviewed ? (
          <div className="mt-8 rounded-2xl bg-emerald-50 p-6 text-sm text-emerald-900">
            已于 {review?.reviewed_at?.slice(0, 19)} 提交终审结论：
            {review?.advisor_decision === "approve"
              ? "通过"
              : review?.advisor_decision === "revise"
                ? "需修改"
                : "不予通过"}
            {review?.advisor_comment && (
              <p className="mt-2 text-stone-700">评语：{review.advisor_comment}</p>
            )}
          </div>
        ) : (
          review && (
            <form onSubmit={handleSubmit} className="mt-8 space-y-4 rounded-2xl bg-white p-6 ring-1 ring-stone-200/80">
              <h3 className="font-medium text-stone-900">导师终审</h3>
              <fieldset className="space-y-2">
                {DECISIONS.map((d) => (
                  <label
                    key={d.value}
                    className={`flex cursor-pointer gap-3 rounded-xl border p-4 ${
                      decision === d.value ? "border-teal-600 bg-teal-50" : "border-stone-200"
                    }`}
                  >
                    <input
                      type="radio"
                      name="decision"
                      value={d.value}
                      checked={decision === d.value}
                      onChange={() => setDecision(d.value)}
                    />
                    <span>
                      <span className="font-medium text-stone-900">{d.label}</span>
                      <span className="block text-xs text-stone-500">{d.desc}</span>
                    </span>
                  </label>
                ))}
              </fieldset>
              <label className="block text-sm">
                评语（可选）
                <textarea
                  className="mt-1 w-full rounded-lg border border-stone-300 px-3 py-2"
                  rows={4}
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="给学生的终审意见…"
                />
              </label>
              {error && <p className="text-sm text-red-600">{error}</p>}
              <button
                type="submit"
                disabled={submitting}
                className="w-full rounded-full bg-teal-700 py-2.5 text-white disabled:opacity-50"
              >
                {submitting ? "提交中…" : "提交终审结论"}
              </button>
            </form>
          )
        )}
      </main>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-2xl bg-white p-5 ring-1 ring-stone-200/80">
      <h3 className="mb-3 text-sm font-medium text-stone-500">{title}</h3>
      {children}
    </section>
  );
}
