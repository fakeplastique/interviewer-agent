"use client";
import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import { useAuth } from "@/lib/auth";
import { interviewApi, Interview } from "@/lib/api";

const TOPICS = ["Python", "JavaScript", "TypeScript", "Go", "Rust", "Java", "System Design", "Algorithms", "React", "SQL", "DevOps", "Docker"];
const LEVELS = ["junior", "middle", "senior"] as const;

function StatusBadge({ status }: { status: Interview["status"] }) {
  const labels = { pending: "Pending", active: "Active", completed: "Completed", failed: "Failed" };
  return <span className={`badge badge-${status}`}>{labels[status]}</span>;
}

function LevelBadge({ level }: { level: Interview["level"] }) {
  return <span className={`badge badge-${level}`}>{level}</span>;
}

function ScoreCircle({ score }: { score?: number }) {
  if (score === undefined || score === null) return <span style={{ color: "var(--text-muted)", fontSize: "0.875rem" }}>—</span>;
  const color = score >= 70 ? "var(--green)" : score >= 40 ? "var(--yellow)" : "var(--red)";
  const radius = 44;
  const circ = 2 * Math.PI * radius;
  const fill = (score / 100) * circ;
  return (
    <div className="score-ring">
      <svg width="120" height="120" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r={radius} fill="none" stroke="var(--bg-secondary)" strokeWidth="8" />
        <circle cx="60" cy="60" r={radius} fill="none" stroke={color} strokeWidth="8"
          strokeDasharray={`${fill} ${circ - fill}`} strokeLinecap="round" />
      </svg>
      <span className="score-ring-value" style={{ color }}>{Math.round(score)}</span>
    </div>
  );
}

export default function DashboardPage() {
  const { token, user } = useAuth();
  const router = useRouter();
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [topic, setTopic] = useState("Python");
  const [level, setLevel] = useState<typeof LEVELS[number]>("middle");

  const loadInterviews = useCallback(async () => {
    if (!token) return;
    try {
      const data = await interviewApi.list(token);
      setInterviews(data);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }, [token]);

  useEffect(() => {
    if (!token) { router.push("/auth"); return; }
    loadInterviews();
  }, [token, router, loadInterviews]);

  const createAndStart = async () => {
    if (!token) return;
    setCreating(true);
    try {
      const iv = await interviewApi.create(topic, level, token);
      await interviewApi.start(iv.id, token);
      router.push(`/interview/${iv.id}`);
    } catch (e) {
      console.error(e);
    } finally {
      setCreating(false);
      setShowModal(false);
    }
  };

  const deleteInterview = async (id: string) => {
    if (!token || !confirm("Delete this interview?")) return;
    await interviewApi.delete(id, token);
    setInterviews((prev) => prev.filter((i) => i.id !== id));
  };

  const stats = {
    total: interviews.length,
    completed: interviews.filter((i) => i.status === "completed").length,
    avgScore: interviews.filter((i) => i.score !== null && i.score !== undefined).length
      ? Math.round(interviews.reduce((acc, i) => acc + (i.score || 0), 0) / interviews.filter((i) => i.score !== undefined && i.score !== null).length)
      : null,
  };

  return (
    <>
      <Navbar />
      <div className="container" style={{ padding: "40px 24px" }}>
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "32px", flexWrap: "wrap", gap: "16px" }}>
          <div>
            <h1 style={{ fontSize: "2rem", marginBottom: "4px" }}>Dashboard</h1>
            <p>Welcome back, {user?.full_name || user?.email}</p>
          </div>
          <button className="btn btn-primary" onClick={() => setShowModal(true)}>
            + New Interview
          </button>
        </div>

        {/* Stats */}
        <div className="grid-3" style={{ marginBottom: "32px" }}>
          {[
            { label: "Total Sessions", value: stats.total, icon: "🎯" },
            { label: "Completed", value: stats.completed, icon: "✅" },
            { label: "Avg Score", value: stats.avgScore !== null ? `${stats.avgScore}/100` : "—", icon: "📊" },
          ].map((s) => (
            <div key={s.label} className="card" style={{ display: "flex", alignItems: "center", gap: "16px" }}>
              <span style={{ fontSize: "2rem" }}>{s.icon}</span>
              <div>
                <div style={{ fontSize: "1.5rem", fontWeight: 700 }}>{s.value}</div>
                <div style={{ color: "var(--text-muted)", fontSize: "0.875rem" }}>{s.label}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Interview list */}
        <h2 style={{ marginBottom: "20px" }}>Interview History</h2>

        {loading ? (
          <div style={{ display: "flex", justifyContent: "center", padding: "60px" }}>
            <div className="spinner" style={{ width: 40, height: 40 }} />
          </div>
        ) : interviews.length === 0 ? (
          <div className="empty-state card">
            <div style={{ fontSize: "3rem", marginBottom: "12px" }}>🤖</div>
            <h3 style={{ color: "var(--text-secondary)", marginBottom: "8px" }}>No interviews yet</h3>
            <p>Start your first AI mock interview to begin practicing.</p>
            <button className="btn btn-primary" onClick={() => setShowModal(true)} style={{ marginTop: "20px" }}>
              Start First Interview
            </button>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {interviews.map((iv) => (
              <div
                key={iv.id}
                className="card"
                style={{ display: "flex", alignItems: "center", gap: "20px", flexWrap: "wrap" }}
              >
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px", flexWrap: "wrap" }}>
                    <span style={{ fontWeight: 600, fontSize: "1.05rem" }}>{iv.topic}</span>
                    <LevelBadge level={iv.level} />
                    <StatusBadge status={iv.status} />
                  </div>
                  <div style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>
                    {new Date(iv.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit" })}
                    {" · "}{iv.questions.length} question{iv.questions.length !== 1 ? "s" : ""}
                  </div>
                </div>

                {iv.status === "completed" && <ScoreCircle score={iv.score ?? undefined} />}

                <div style={{ display: "flex", gap: "8px" }}>
                  {iv.status === "active" && (
                    <Link href={`/interview/${iv.id}`} className="btn btn-primary" style={{ padding: "8px 16px" }}>
                      Resume →
                    </Link>
                  )}
                  {iv.status === "completed" && (
                    <Link href={`/results/${iv.id}`} className="btn btn-secondary" style={{ padding: "8px 16px" }}>
                      View Report
                    </Link>
                  )}
                  <button className="btn btn-danger" style={{ padding: "8px 12px" }} onClick={() => deleteInterview(iv.id)}>
                    🗑
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* New Interview Modal */}
      {showModal && (
        <div
          style={{
            position: "fixed", inset: 0, zIndex: 200,
            background: "rgba(0,0,0,0.7)", backdropFilter: "blur(8px)",
            display: "flex", alignItems: "center", justifyContent: "center", padding: "24px",
          }}
          onClick={(e) => e.target === e.currentTarget && setShowModal(false)}
        >
          <div className="card animate-fade-in" style={{ width: "100%", maxWidth: 480 }}>
            <h2 style={{ marginBottom: "24px" }}>New Interview</h2>

            <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
              <div>
                <label className="label">Topic</label>
                <select className="input select" value={topic} onChange={(e) => setTopic(e.target.value)}>
                  {TOPICS.map((t) => <option key={t}>{t}</option>)}
                </select>
              </div>
              <div>
                <label className="label">Experience Level</label>
                <div style={{ display: "flex", gap: "8px" }}>
                  {LEVELS.map((l) => (
                    <button
                      key={l}
                      onClick={() => setLevel(l)}
                      style={{
                        flex: 1, padding: "10px", border: "1px solid",
                        borderColor: level === l ? "var(--accent)" : "var(--border)",
                        borderRadius: "var(--radius-sm)", cursor: "pointer",
                        background: level === l ? "rgba(99,102,241,0.1)" : "var(--bg-secondary)",
                        color: level === l ? "var(--accent-light)" : "var(--text-secondary)",
                        fontWeight: 600, fontSize: "0.875rem", fontFamily: "inherit",
                        textTransform: "capitalize", transition: "all 0.2s",
                      }}
                    >
                      {l}
                    </button>
                  ))}
                </div>
              </div>

              <div style={{ display: "flex", gap: "10px", marginTop: "8px" }}>
                <button className="btn btn-secondary" style={{ flex: 1 }} onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button className="btn btn-primary" style={{ flex: 1, justifyContent: "center" }} onClick={createAndStart} disabled={creating}>
                  {creating ? <span className="spinner" /> : "Start Interview →"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
