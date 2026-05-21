"use client";
import { useEffect, useRef, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import ReactMarkdown from "react-markdown";
import Navbar from "@/components/Navbar";
import CharacterPanel from "@/components/CharacterPanel";
import { useAuth } from "@/lib/auth";
import { interviewApi, Interview, Question } from "@/lib/api";
import type { SpeechContext } from "@/components/CharacterPanel";
import { createInterviewSocket, WSMessage } from "@/lib/ws";

interface ChatMessage {
  id: string;
  role: "ai" | "user" | "feedback";
  content: string;
  score?: number;
  questionId?: string;
}

export default function InterviewPage() {
  const { id } = useParams<{ id: string }>();
  const { token } = useAuth();
  const router = useRouter();

  const [interview, setInterview] = useState<Interview | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [answer, setAnswer] = useState("");
  const [currentQuestionId, setCurrentQuestionId] = useState<string | null>(null);
  const [progress, setProgress] = useState({ current: 0, total: 5 });
  const [submitting, setSubmitting] = useState(false);
  const [connecting, setConnecting] = useState(true);
  const [completed, setCompleted] = useState(false);

  // Character state
  const [speechContext, setSpeechContext] = useState<SpeechContext | null>(null);
  const [contextKey, setContextKey] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const chatRef = useRef<HTMLDivElement>(null);
  const currentQuestionTextRef = useRef<string>("");
  const lastAnswerRef = useRef<string>("");

  const addMessage = (msg: ChatMessage) => {
    setMessages((prev) => [...prev, msg]);
    setTimeout(() => chatRef.current?.scrollTo({ top: chatRef.current.scrollHeight, behavior: "smooth" }), 50);
  };

  const handleWsMessage = useCallback((msg: WSMessage) => {
    if (msg.type === "question") {
      setCurrentQuestionId(msg.question_id || null);
      setProgress({ current: msg.index || 0, total: msg.total || 5 });
      currentQuestionTextRef.current = msg.text || "";
      addMessage({
        id: `q-${msg.question_id}`,
        role: "ai",
        content: msg.text || "",
        questionId: msg.question_id,
      });
      setSubmitting(false);
    } else if (msg.type === "feedback") {
      addMessage({
        id: `f-${msg.question_id}`,
        role: "feedback",
        content: msg.feedback || "",
        score: msg.score,
      });
      if (msg.feedback) {
        setSpeechContext({
          question: currentQuestionTextRef.current,
          answer: lastAnswerRef.current,
          feedback: msg.feedback,
          score: msg.score ?? 5,
        });
        setContextKey((k) => k + 1);
      }
    } else if (msg.type === "completed") {
      setCompleted(true);
      addMessage({
        id: "completed",
        role: "ai",
        content: "🎉 Interview complete! Preparing your detailed report...",
      });
      setTimeout(() => router.push(`/results/${id}`), 3000);
    }
  }, [id, router, token]);

  useEffect(() => {
    if (!token || !id) { router.push("/auth"); return; }

    interviewApi.get(id, token).then((iv) => {
      setInterview(iv);
      iv.questions.forEach((q: Question) => {
        addMessage({ id: `q-${q.id}`, role: "ai", content: q.text, questionId: q.id });
        if (q.answer) addMessage({ id: `a-${q.id}`, role: "user", content: q.answer });
        if (q.feedback) addMessage({ id: `f-${q.id}`, role: "feedback", content: q.feedback, score: q.score ?? undefined });
      });
      const lastUnanswered = iv.questions.find((q: Question) => !q.answer);
      if (lastUnanswered) {
        setCurrentQuestionId(lastUnanswered.id);
        currentQuestionTextRef.current = lastUnanswered.text;
      }
      setProgress({ current: iv.questions.length, total: 5 });
    }).catch(console.error);

    wsRef.current = createInterviewSocket(id, token, handleWsMessage, () => setConnecting(false));
    wsRef.current.onopen = () => setConnecting(false);

    return () => wsRef.current?.close();
  }, [id, token, router, handleWsMessage]);

  const submitAnswer = async () => {
    if (!answer.trim() || !currentQuestionId || !token || submitting) return;
    const text = answer.trim();
    lastAnswerRef.current = text;
    setAnswer("");
    setSubmitting(true);
    addMessage({ id: `user-${Date.now()}`, role: "user", content: text });
    try {
      await interviewApi.submitAnswer(id, currentQuestionId, text, token);
      setCurrentQuestionId(null);
    } catch (e) {
      console.error(e);
      setSubmitting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) submitAnswer();
  };

  return (
    <>
      <Navbar />
      <div style={{ maxWidth: 1100, margin: "0 auto", padding: "24px", height: "calc(100vh - 70px)", display: "flex", flexDirection: "column" }}>

        {/* Header */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "20px", flexWrap: "wrap", gap: "12px" }}>
          <div>
            <h2 style={{ marginBottom: "4px" }}>
              {interview?.topic || "Interview"} <span className={`badge badge-${interview?.level}`}>{interview?.level}</span>
            </h2>
            <p style={{ fontSize: "0.875rem" }}>
              {connecting ? (
                <span style={{ color: "var(--yellow)" }}>⚡ Connecting...</span>
              ) : completed ? (
                <span style={{ color: "var(--green)" }}>✅ Completed</span>
              ) : (
                <span style={{ color: "var(--green)" }}>🟢 Live</span>
              )}
            </p>
          </div>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "6px" }}>
              Question {Math.min(progress.current, progress.total)} of {progress.total}
            </div>
            <div className="progress-track" style={{ width: 200 }}>
              <div className="progress-fill" style={{ width: `${(Math.min(progress.current, progress.total) / progress.total) * 100}%` }} />
            </div>
          </div>
        </div>

        {/* Main row: chat + character */}
        <div style={{ flex: 1, display: "flex", gap: 16, overflow: "hidden" }}>

          {/* Left: chat + input */}
          <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
            <div
              ref={chatRef}
              style={{
                flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: "16px",
                padding: "20px", background: "var(--bg-secondary)", borderRadius: "var(--radius-lg)",
                border: "1px solid var(--border)", marginBottom: "16px",
              }}
            >
              {messages.length === 0 && (
                <div style={{ textAlign: "center", color: "var(--text-muted)", paddingTop: "40px" }}>
                  <div style={{ fontSize: "3rem", marginBottom: "12px" }}>🤖</div>
                  <p>Waiting for the interview to start...</p>
                </div>
              )}

              {messages.map((msg) => (
                <div
                  key={msg.id}
                  style={{ display: "flex", flexDirection: "column", alignItems: msg.role === "user" ? "flex-end" : "flex-start" }}
                >
                  {msg.role !== "user" && (
                    <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "4px", paddingLeft: "4px" }}>
                      {msg.role === "feedback" ? "📊 Feedback" : "🤖 AI Interviewer"}
                    </span>
                  )}
                  <div className={`bubble bubble-${msg.role === "user" ? "user" : msg.role === "feedback" ? "feedback" : "ai"}`}>
                    {msg.role === "feedback" && msg.score !== undefined && (
                      <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
                        <span style={{ fontWeight: 700, fontSize: "1.1rem", color: msg.score >= 7 ? "var(--green)" : msg.score >= 4 ? "var(--yellow)" : "var(--red)" }}>
                          {msg.score}/10
                        </span>
                        <div className="progress-track" style={{ flex: 1 }}>
                          <div className="progress-fill" style={{ width: `${(msg.score / 10) * 100}%`, background: msg.score >= 7 ? "var(--green)" : msg.score >= 4 ? "var(--yellow)" : "var(--red)" }} />
                        </div>
                      </div>
                    )}
                    {msg.role === "user" ? (
                      <span style={{ fontSize: "0.95rem" }}>{msg.content}</span>
                    ) : (
                      <div className="md-content" style={{ fontSize: "0.95rem" }}>
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {submitting && (
                <div style={{ display: "flex", alignItems: "center", gap: "8px", paddingLeft: "4px" }}>
                  <div className="spinner" />
                  <span style={{ color: "var(--text-muted)", fontSize: "0.875rem" }}>AI is thinking...</span>
                </div>
              )}
            </div>

            {!completed && (
              <div style={{ display: "flex", gap: "12px", alignItems: "flex-end" }}>
                <div style={{ flex: 1 }}>
                  <textarea
                    className="input"
                    rows={3}
                    placeholder={currentQuestionId ? "Type your answer... (Ctrl+Enter to submit)" : "Waiting for the next question..."}
                    value={answer}
                    onChange={(e) => setAnswer(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={!currentQuestionId || submitting}
                    style={{ resize: "none", lineHeight: 1.5 }}
                  />
                </div>
                <button
                  className="btn btn-primary"
                  onClick={submitAnswer}
                  disabled={!answer.trim() || !currentQuestionId || submitting}
                  style={{ padding: "14px 20px", alignSelf: "flex-end" }}
                >
                  Send →
                </button>
              </div>
            )}
          </div>

          {/* Right: character */}
          <CharacterPanel
            context={speechContext}
            contextKey={contextKey}
            isThinking={submitting}
            token={token || ""}
          />
        </div>
      </div>
    </>
  );
}
