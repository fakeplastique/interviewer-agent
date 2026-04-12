"use client";
import Link from "next/link";
import { useAuth } from "@/lib/auth";

export default function Navbar() {
  const { user, logout } = useAuth();

  return (
    <nav className="navbar">
      <div className="container navbar-inner">
        <Link href="/" className="navbar-brand">
          <span className="gradient-text">MockAI</span>
        </Link>

        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          {user ? (
            <>
              <span style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>
                {user.full_name || user.email}
              </span>
              <Link href="/dashboard" className="btn btn-secondary" style={{ padding: "8px 16px" }}>
                Dashboard
              </Link>
              <button className="btn btn-secondary" style={{ padding: "8px 16px" }} onClick={logout}>
                Logout
              </button>
            </>
          ) : (
            <>
              <Link href="/auth" className="btn btn-secondary" style={{ padding: "8px 16px" }}>
                Sign In
              </Link>
              <Link href="/auth?tab=register" className="btn btn-primary" style={{ padding: "8px 16px" }}>
                Get Started
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
