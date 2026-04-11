"use client";
import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth";

function AuthForm() {
  const searchParams = useSearchParams();
  const [tab, setTab] = useState<"login" | "register">(
    searchParams.get("tab") === "register" ? "register" : "login"
  );
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login, register, user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (user) router.push("/dashboard");
  }, [user, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (tab === "login") {
        await login(email, password);
      } else {
        await register(email, password, fullName);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center",
        padding: "24px", background: "var(--bg-primary)",
      }}
    >
      <div className="hero-bg" style={{ position: "fixed" }} />

      <div
        className="card animate-fade-in"
        style={{ width: "100%", maxWidth: 440, position: "relative" }}
      >
        <div style={{ textAlign: "center", marginBottom: "32px" }}>
          <h1 style={{ fontSize: "1.75rem", marginBottom: "8px" }}>
            <span className="gradient-text">MockAI</span>
          </h1>
          <p>{tab === "login" ? "Welcome back" : "Create your account"}</p>
        </div>

        {/* Tab switcher */}
        <div
          style={{
            display: "flex", gap: "4px", padding: "4px",
            background: "var(--bg-secondary)", borderRadius: "var(--radius-sm)",
            marginBottom: "28px",
          }}
        >
          {(["login", "register"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              style={{
                flex: 1, padding: "8px", border: "none", cursor: "pointer",
                borderRadius: "6px", fontWeight: 600, fontSize: "0.875rem", fontFamily: "inherit",
                background: tab === t ? "var(--bg-card)" : "transparent",
                color: tab === t ? "var(--text-primary)" : "var(--text-muted)",
                transition: "all 0.2s",
              }}
            >
              {t === "login" ? "Sign In" : "Register"}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {tab === "register" && (
            <div>
              <label className="label">Full Name</label>
              <input
                className="input"
                type="text"
                placeholder="John Doe"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />
            </div>
          )}
          <div>
            <label className="label">Email</label>
            <input
              className="input"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="label">Password</label>
            <input
              className="input"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
            />
          </div>

          {error && (
            <div
              style={{
                padding: "12px 16px", borderRadius: "var(--radius-sm)",
                background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)",
                color: "var(--red)", fontSize: "0.875rem",
              }}
            >
              {error}
            </div>
          )}

          <button className="btn btn-primary" type="submit" disabled={loading} style={{ marginTop: "4px", justifyContent: "center" }}>
            {loading ? <span className="spinner" /> : tab === "login" ? "Sign In →" : "Create Account →"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default function AuthPage() {
  return (
    <Suspense>
      <AuthForm />
    </Suspense>
  );
}
