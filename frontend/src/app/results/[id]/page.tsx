"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import { useAuth } from "@/lib/auth";
import { interviewApi, Interview, Question } from "@/lib/api";

function ScoreRing({ score, size = 160 }: { score: number; size?: number }) {
  const r = (size / 2) - 12;
  const circ = 2 * Math.PI * r;
  const fill = (score / 100) * circ;
  const color = score >= 70 ? "#10b981" : score >= 40 ? "#f59e0b" : "#ef4444";
  return (
    <div style={{ position: "relative", width: size, height: size, display: "flex", alignItems: "center", justifyContent: "center" }}>
      <svg width={size} height={size} style={{ position: "absolute", transform: "rotate(-90deg)" }}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--bg-secondary)" strokeWidth="10" />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth="10"
          strokeDasharray={`${fill} ${circ - fill}`} strokeLinecap="round"
          style={{ transition: "stroke-dasharray 1s ease" }} />
      </svg>
      <div style={{ textAlign: "center" }}>
        <div style={{ fontSize: "2.5rem", fontWeight: 800, color }}>{Math.round(score)}</div>
        <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>/ 100</div>
      </div>
    </div>
  );
}

function QuestionCard({ q, index }: { q: Question; index: number }) {
  const [open, setOpen] = useState(index === 0);
  const color = (q.score || 0) >= 7 ? "var(--green)" : (q.score || 0) >= 4 ? "var(--yellow)" : "var(--red)";

  return (
    <div className="card" style={{ overflow: "hidden" }}>
      <div
        onClick={() => setOpen(!open)}
        style={{ display: "flex", justifyContent: "space-between", alignItems: "center", cursor: "pointer" }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <span style={{
            width: 28, height: 28, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center",
            background: "var(--bg-secondary)", fontSize: "0.8rem", fontWeight: 700, color: "var(--text-muted)", flexShrink: 0,
          }}>{index + 1}</span>
          <span style={{ fontWeight: 500, fontSize: "0.95rem" }}>{q.text}</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "12px", flexShrink: 0 }}>
          {q.score !== null && q.score !== undefined && (
            <span style={{ fontWeight: 700, color, fontSize: "0.95rem" }}>{q.score}/10</span>
          )}
          <span style={{ color: "var(--text-muted)", transition: "transform 0.2s", transform: open ? "rotate(180deg)" : "none" }}>▾</span>
        </div>
      </div>

      {open && (
        <div style={{ marginTop: "20px", display: "flex", flexDirection: "column", gap: "16px", paddingTop: "16px", borderTop: "1px solid var(--border)" }}>
          <div>
            <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "8px" }}>Your Answer</div>
            <div style={{ padding: "12px 16px", background: "var(--bg-secondary)", borderRadius: "var(--radius-sm)", fontSize: "0.9rem", color: "var(--text-secondary)" }}>
              {q.answer || <em style={{ color: "var(--text-muted)" }}>No answer provided</em>}
            </div>
          </div>
          {q.feedback && (
            <div>
              <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "8px" }}>AI Feedback</div>
              <div style={{ padding: "12px 16px", background: "rgba(16,185,129,0.06)", border: "1px solid rgba(16,185,129,0.15)", borderRadius: "var(--radius-sm)", fontSize: "0.9rem", color: "var(--text-secondary)" }}>
                {q.feedback}
              </div>
            </div>
          )}
          {q.score !== null && q.score !== undefined && (
            <div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "6px" }}>Score</div>
              <div className="progress-track" style={{ height: 8 }}>
                <div className="progress-fill" style={{
                  width: `${(q.score / 10) * 100}%`,
                  background: color,
                  transition: "width 1s ease",
                }} />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function ResultsPage() {
  const { id } = useParams<{ id: string }>();
  const { token } = useAuth();
  const router = useRouter();
  const [interview, setInterview] = useState<Interview | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) { router.push("/auth"); return; }
    interviewApi.get(id, token)
      .then(setInterview)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id, token, router]);

  if (loading) {
    return (
      <>
        <Navbar />
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "60vh" }}>
          <div className="spinner" style={{ width: 48, height: 48 }} />
        </div>
      </>
    );
  }

  if (!interview) {
    return (
      <>
        <Navbar />
        <div className="empty-state container" style={{ paddingTop: "80px" }}>
          <h2>Interview not found</h2>
          <Link href="/dashboard" className="btn btn-primary" style={{ marginTop: "20px" }}>← Back to Dashboard</Link>
        </div>
      </>
    );
  }

  const levelColor = interview.level === "senior" ? "var(--accent-light)" : interview.level === "middle" ? "var(--yellow)" : "var(--cyan)";

  return (
    <>
      <Navbar />
      <div className="container" style={{ padding: "40px 24px", maxWidth: 860 }}>
        {/* Back nav */}
        <Link href="/dashboard" style={{ color: "var(--text-muted)", textDecoration: "none", fontSize: "0.875rem", display: "inline-flex", alignItems: "center", gap: "4px", marginBottom: "32px" }}>
          ← Dashboard
        </Link>

        {/* Hero card */}
        <div
          className="card"
          style={{
            background: "linear-gradient(135deg, rgba(99,102,241,0.08) 0%, rgba(167,139,250,0.05) 100%)",
            border: "1px solid rgba(99,102,241,0.2)",
            display: "flex", flexWrap: "wrap", gap: "32px", alignItems: "center",
            marginBottom: "32px",
          }}
        >
          <div style={{ flex: 1, minWidth: 200 }}>
            <div style={{ display: "flex", gap: "8px", alignItems: "center", marginBottom: "12px" }}>
              <span className={`badge badge-${interview.level}`}>{interview.level}</span>
              <span className="badge badge-completed">Completed</span>
            </div>
            <h1 style={{ fontSize: "2rem", marginBottom: "8px" }}>{interview.topic}</h1>
            <p style={{ marginBottom: "4px" }}>
              {interview.questions.length} questions · {new Date(interview.created_at).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}
            </p>
            {interview.report && (
              <p style={{ marginTop: "16px", lineHeight: 1.6, borderLeft: "3px solid var(--accent)", paddingLeft: "12px" }}>
                {interview.report}
              </p>
            )}
          </div>
          {interview.score !== null && interview.score !== undefined && (
            <ScoreRing score={interview.score} />
          )}
        </div>

        {/* Per-question breakdown */}
        <h2 style={{ marginBottom: "20px" }}>Question Breakdown</h2>
        <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginBottom: "32px" }}>
          {interview.questions.map((q, i) => (
            <QuestionCard key={q.id} q={q} index={i} />
          ))}
        </div>

        {/* Actions */}
        <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
          <Link href="/dashboard" className="btn btn-secondary">← Back to Dashboard</Link>
          <button
            className="btn btn-primary"
            onClick={() => router.push("/dashboard")}
          >
            Start New Interview
          </button>
        </div>
      </div>
    </>
  );
}
