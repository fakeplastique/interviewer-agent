// WebSocket client for real-time interview messages

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

export type WSMessageType = "question" | "feedback" | "completed" | "error" | "ping";

export interface WSMessage {
  type: WSMessageType;
  interview_id?: string;
  question_id?: string;
  text?: string;
  index?: number;
  total?: number;
  score?: number;
  feedback?: string;
  overall_score?: number;
  report?: string;
}

export function createInterviewSocket(
  interviewId: string,
  token: string,
  onMessage: (msg: WSMessage) => void,
  onClose?: () => void
): WebSocket {
  const ws = new WebSocket(
    `${WS_BASE}/ws/interviews/${interviewId}?token=${encodeURIComponent(token)}`
  );

  ws.onmessage = (event) => {
    try {
      const data: WSMessage = JSON.parse(event.data);
      if (data.type !== "ping") onMessage(data);
    } catch (e) {
      console.error("WS parse error", e);
    }
  };

  ws.onerror = (err) => console.error("WS error", err);
  ws.onclose = () => onClose?.();

  return ws;
}
