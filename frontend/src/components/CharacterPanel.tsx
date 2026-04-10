"use client";
import { useEffect, useRef, useState } from "react";
import Lottie, { LottieRefCurrentProps } from "lottie-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function stripMarkdown(text: string): string {
  return text
    .replace(/#{1,6}\s+/g, "")          // headings
    .replace(/\*\*(.+?)\*\*/g, "$1")    // bold
    .replace(/\*(.+?)\*/g, "$1")        // italic
    .replace(/_(.+?)_/g, "$1")          // italic underscore
    .replace(/`{1,3}[^`]*`{1,3}/g, "") // inline & block code
    .replace(/^\s*[-*+]\s+/gm, "")     // unordered list bullets
    .replace(/^\s*\d+\.\s+/gm, "")     // ordered list numbers
    .replace(/\[(.+?)\]\(.+?\)/g, "$1") // links → label only
    .replace(/^\s*>\s+/gm, "")          // blockquotes
    .replace(/\n{2,}/g, " ")            // collapse multiple newlines
    .trim();
}

export interface SpeechContext {
  question: string;
  answer: string;
  feedback: string;
  score: number;
}

interface Props {
  context?: SpeechContext | null;
  contextKey?: number;
  isThinking?: boolean;
  token: string;
  onLangChange?: (lang: "pl" | "ua") => void;
  lottieFile?: string;
}

type State = "idle" | "speaking" | "thinking";

const SENTENCE_RE = /^([\s\S]*?[.!?…])\s*/;

export default function CharacterPanel({
  context, contextKey, isThinking, token, onLangChange, lottieFile = "/buddy.json",
}: Props) {
  const [state, setState] = useState<State>("idle");
  const [currentSentence, setCurrentSentence] = useState<string | null>(null);
  const [lang, setLang] = useState<"pl" | "ua">("pl");
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [animData, setAnimData] = useState<any>(null);

  const lottieRef = useRef<LottieRefCurrentProps>(null);
  const isThinkingRef = useRef(isThinking);
  useEffect(() => { isThinkingRef.current = isThinking; }, [isThinking]);

  // ordered queue: TTS blobs fetched in parallel, played in order
  const sentenceQueueRef = useRef<{ text: string; blobPromise: Promise<Blob | null> }[]>([]);
  const playingRef = useRef(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const switchLang = (l: "pl" | "ua") => { setLang(l); onLangChange?.(l); };

  // Load Lottie JSON
  useEffect(() => {
    fetch(lottieFile).then((r) => r.json()).then(setAnimData).catch(() => {});
  }, [lottieFile]);

  // Adjust animation speed per state
  useEffect(() => {
    const speeds: Record<State, number> = { idle: 0.6, thinking: 1, speaking: 2 };
    lottieRef.current?.setSpeed(speeds[state]);
  }, [state]);

  // Sync thinking when not speaking
  useEffect(() => {
    if (state === "speaking") return;
    setState(isThinking ? "thinking" : "idle");
  }, [isThinking]); // eslint-disable-line react-hooks/exhaustive-deps

  function stopAll() {
    abortRef.current?.abort();
    if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; }
    sentenceQueueRef.current = [];
    playingRef.current = false;
  }

  async function fetchTTSBlob(text: string, signal: AbortSignal): Promise<Blob | null> {
    try {
      const res = await fetch(`${API_BASE}/api/v1/tts/speak`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ text }),
        signal,
      });
      if (!res.ok) return null;
      return res.blob();
    } catch {
      return null;
    }
  }

  async function playNext() {
    if (sentenceQueueRef.current.length === 0) {
      playingRef.current = false;
      setState(isThinkingRef.current ? "thinking" : "idle");
      setTimeout(() => setCurrentSentence(null), 1500);
      return;
    }

    playingRef.current = true;
    const { text, blobPromise } = sentenceQueueRef.current.shift()!;
    setCurrentSentence(text);

    const blob = await blobPromise;
    if (!blob) { playNext(); return; }

    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audioRef.current = audio;
    audio.onplay  = () => setState("speaking");
    audio.onended = () => { URL.revokeObjectURL(url); audioRef.current = null; playNext(); };
    audio.onerror = () => { URL.revokeObjectURL(url); playNext(); };
    audio.play().catch(() => playNext());
  }

  function enqueueSentence(text: string, signal: AbortSignal) {
    const clean = stripMarkdown(text);
    const blobPromise = fetchTTSBlob(clean, signal);
    sentenceQueueRef.current.push({ text: clean, blobPromise });
    if (!playingRef.current) playNext();
  }

  // SSE stream + sentence splitting when contextKey changes
  useEffect(() => {
    if (!context || !token) return;

    stopAll();
    setState(isThinkingRef.current ? "thinking" : "idle");
    setCurrentSentence(null);

    const abort = new AbortController();
    abortRef.current = abort;

    (async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/character/react/stream`, {
          method: "POST",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
          body: JSON.stringify({ ...context, lang }),
          signal: abort.signal,
        });

        if (!res.ok || !res.body) return;

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        enqueueSentence("Hahahahaha!!!!", abort.signal);

        let rawBuf = "";
        let sentenceBuf = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          rawBuf += decoder.decode(value, { stream: true });
          const lines = rawBuf.split("\n");
          rawBuf = lines.pop() ?? "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const payload = line.slice(6).trim();
            if (payload === "[DONE]") break;

            try {
              const { token: tok } = JSON.parse(payload);
              sentenceBuf += tok;

              // flush complete sentences eagerly
              let m = SENTENCE_RE.exec(sentenceBuf);
              while (m) {
                enqueueSentence(m[1], abort.signal);
                sentenceBuf = sentenceBuf.slice(m[0].length);
                m = SENTENCE_RE.exec(sentenceBuf);
              }
            } catch { /* malformed SSE chunk */ }
          }
        }

        // flush remainder
        if (sentenceBuf.trim()) enqueueSentence(sentenceBuf.trim(), abort.signal);
      } catch (e: unknown) {
        if (e instanceof Error && e.name !== "AbortError") {
          setState(isThinkingRef.current ? "thinking" : "idle");
        }
      }
    })();

    return () => abort.abort();
  }, [contextKey]); // eslint-disable-line react-hooks/exhaustive-deps

  const statusColor =
    state === "speaking" ? "var(--green)" :
    state === "thinking"  ? "var(--yellow)" : "var(--text-muted)";
  const statusLabel =
    state === "speaking" ? "🔊 Speaking..." :
    state === "thinking"  ? "⏳ Evaluating..." : "● Ready";

  return (
    <div style={{
      width: 240, flexShrink: 0, display: "flex", flexDirection: "column",
      alignItems: "center", padding: "20px 16px",
      background: "var(--bg-secondary)", border: "1px solid var(--border)",
      borderRadius: "var(--radius-lg)",
    }}>
      <div style={{ fontWeight: 700, fontSize: "1rem", marginBottom: 4 }}>Buddy</div>
      <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: 10 }}>AI Coach</div>

      {/* Language toggle */}
      <div style={{ display: "flex", gap: 4, marginBottom: 14 }}>
        {(["pl", "ua"] as const).map((l) => (
          <button key={l} onClick={() => switchLang(l)} style={{
            padding: "3px 10px", borderRadius: 999, fontSize: "0.72rem", fontWeight: 600,
            cursor: "pointer", border: "1px solid", textTransform: "uppercase",
            borderColor: lang === l ? "var(--accent)" : "var(--border)",
            background:   lang === l ? "rgba(99,102,241,0.15)" : "transparent",
            color:        lang === l ? "var(--accent-light)" : "var(--text-muted)",
            transition: "all 0.15s",
          }}>{l}</button>
        ))}
      </div>

      {/* Speech bubble — current sentence only */}
      <div style={{ minHeight: 72, width: "100%", marginBottom: 12, display: "flex", alignItems: "center", justifyContent: "center" }}>
        {currentSentence && (
          <div style={{
            background: "var(--bg-card)", border: "1px solid var(--border)",
            borderRadius: "var(--radius-md)", padding: "10px 14px",
            fontSize: "0.82rem", lineHeight: 1.5, color: "var(--text-primary)",
            position: "relative", animation: "bubblePop 0.25s ease forwards",
          }}>
            {currentSentence}
            <span style={{
              position: "absolute", bottom: -8, left: "50%", transform: "translateX(-50%)",
              width: 0, height: 0,
              borderLeft: "8px solid transparent", borderRight: "8px solid transparent",
              borderTop: "8px solid var(--border)",
            }} />
          </div>
        )}
      </div>

      {/* Lottie character */}
      <div style={{
        width: 160, height: 160,
        border: `2px solid ${state === "speaking" ? "var(--green)" : "var(--border)"}`,
        borderRadius: "50%", overflow: "hidden", transition: "border-color 0.3s",
      }}>
        {animData ? (
          <Lottie lottieRef={lottieRef} animationData={animData} loop autoplay style={{ width: "100%", height: "100%" }} />
        ) : (
          <div style={{ width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "3rem" }}>🤖</div>
        )}
      </div>

      <div style={{ marginTop: 14, fontSize: "0.78rem", color: statusColor, transition: "color 0.3s", fontWeight: 500 }}>
        {statusLabel}
      </div>
    </div>
  );
}
