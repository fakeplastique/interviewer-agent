"use client";
import { useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import { useAuth } from "@/lib/auth";

const FEATURES = [
  {
    icon: "🤖",
    title: "AI Interviewer",
    desc: "Claude Sonnet powered questions tailored to your topic and experience level.",
  },
  {
    icon: "⚡",
    title: "Real-time Feedback",
    desc: "Instant scoring and constructive feedback after every answer via WebSocket.",
  },
  {
    icon: "📊",
    title: "Detailed Reports",
    desc: "Full performance report with overall score and improvement tips at the end.",
  },
  {
    icon: "🎯",
    title: "Custom Topics",
    desc: "Python, System Design, Algorithms, React — any topic you need to practice.",
  },
  {
    icon: "🏆",
    title: "Level-based",
    desc: "Junior, Middle, Senior — get questions appropriate for your target role.",
  },
  {
    icon: "☁️",
    title: "Kafka-powered",
    desc: "Event-driven async architecture ensures smooth, scalable sessions.",
  },
];

const TOPICS = ["Python", "JavaScript", "System Design", "Algorithms", "React", "Go", "SQL", "DevOps"];

export default function HomePage() {
  const { user } = useAuth();
  const router = useRouter();

  return (
    <>
      <Navbar />

      {/* ── Hero ─────────────────────────────────────────────────────────── */}
      <section style={{ position: "relative", overflow: "hidden", padding: "100px 0 80px" }}>
        <div className="hero-bg" />
        <div className="container" style={{ textAlign: "center", position: "relative" }}>
          <div
            style={{
              display: "inline-flex", alignItems: "center", gap: "8px",
              padding: "6px 16px", borderRadius: "999px",
              background: "rgba(99,102,241,0.12)", border: "1px solid rgba(99,102,241,0.25)",
              fontSize: "0.8rem", color: "var(--accent-light)",
              marginBottom: "28px", fontWeight: 600,
            }}
          >
            <span style={{ width: 8, height: 8, borderRadius: "50%", background: "var(--green)", display: "inline-block" }} />
            Powered by Claude Sonnet + LangGraph
          </div>

          <h1 style={{ marginBottom: "24px" }}>
            Ace Your Next<br />
            <span className="gradient-text">Technical Interview</span>
          </h1>

          <p style={{ fontSize: "1.2rem", maxWidth: 560, margin: "0 auto 40px", color: "var(--text-secondary)" }}>
            Practice with an AI interviewer that adapts to your level, gives real-time feedback, and prepares you for the real thing.
          </p>

          <div style={{ display: "flex", gap: "12px", justifyContent: "center", flexWrap: "wrap" }}>
            {user ? (
              <button className="btn btn-primary animate-glow" onClick={() => router.push("/dashboard")} style={{ padding: "14px 32px", fontSize: "1rem" }}>
                Go to Dashboard →
              </button>
            ) : (
              <>
                <button className="btn btn-primary animate-glow" onClick={() => router.push("/auth?tab=register")} style={{ padding: "14px 32px", fontSize: "1rem" }}>
                  Start Practicing Free →
                </button>
                <button className="btn btn-secondary" onClick={() => router.push("/auth")} style={{ padding: "14px 32px", fontSize: "1rem" }}>
                  Sign In
                </button>
              </>
            )}
          </div>

          {/* Topic chips */}
          <div style={{ marginTop: "48px", display: "flex", gap: "8px", justifyContent: "center", flexWrap: "wrap" }}>
            {TOPICS.map((t) => (
              <span
                key={t}
                style={{
                  padding: "6px 14px", borderRadius: "999px",
                  background: "var(--bg-card)", border: "1px solid var(--border)",
                  fontSize: "0.8rem", color: "var(--text-secondary)",
                }}
              >
                {t}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features ──────────────────────────────────────────────────────── */}
      <section className="section" style={{ background: "var(--bg-secondary)" }}>
        <div className="container">
          <h2 style={{ textAlign: "center", marginBottom: "12px" }}>Everything you need to prepare</h2>
          <p style={{ textAlign: "center", marginBottom: "48px", color: "var(--text-secondary)" }}>
            A full-stack AI interview platform built with modern tech
          </p>

          <div className="grid-3">
            {FEATURES.map((f) => (
              <div key={f.title} className="card" style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                <span style={{ fontSize: "2rem" }}>{f.icon}</span>
                <h3>{f.title}</h3>
                <p style={{ fontSize: "0.9rem" }}>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ───────────────────────────────────────────────────────────── */}
      <section className="section">
        <div className="container" style={{ textAlign: "center" }}>
          <div
            style={{
              background: "linear-gradient(135deg, rgba(99,102,241,0.1) 0%, rgba(167,139,250,0.08) 100%)",
              border: "1px solid rgba(99,102,241,0.2)",
              borderRadius: "var(--radius-xl)",
              padding: "60px 40px",
            }}
          >
            <h2 style={{ marginBottom: "16px" }}>Ready to ace your interview?</h2>
            <p style={{ marginBottom: "32px" }}>Join and start practicing in under 30 seconds.</p>
            <button
              className="btn btn-primary"
              onClick={() => router.push(user ? "/dashboard" : "/auth?tab=register")}
              style={{ padding: "14px 36px", fontSize: "1rem" }}
            >
              {user ? "Open Dashboard" : "Create Free Account"}
            </button>
          </div>
        </div>
      </section>
    </>
  );
}
