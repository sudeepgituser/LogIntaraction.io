import React, { useState, useRef, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { sendMessage, userMessageAdded } from "../store/chatSlice";
import "./ChatInterface.css";

export default function ChatInterface({ hcpId, hcpName }) {
  const dispatch = useDispatch();
  const { messages, status, sessionId } = useSelector((s) => s.chat);
  const [input, setInput] = useState("");
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const handleSend = (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    dispatch(userMessageAdded(input));
    dispatch(sendMessage({ session_id: sessionId, message: input, hcp_id: hcpId, created_by: "demo_rep" }));
    setInput("");
  };

  return (
    <div className="chat-interface">
      <p className="chat-interface__hint">
        Talking about <strong>{hcpName || "an HCP"}</strong>. Describe the visit/call naturally
        &mdash; e.g. "Just left Dr. Mehta's clinic, discussed Drug A efficacy data, dropped 10
        samples, she wants updated pediatric dosing info by next week."
      </p>

      <div className="chat-window" ref={scrollRef}>
        {messages.length === 0 && (
          <div className="chat-empty">No messages yet &mdash; start by describing your visit.</div>
        )}
        {messages.map((m, idx) => (
          <div key={idx} className={`chat-bubble chat-bubble--${m.role}`}>
            <div className="chat-bubble__label">{m.role === "user" ? "You" : "AI Agent"}</div>
            <div className="chat-bubble__content">{m.content}</div>
            {m.toolCalls && m.toolCalls.length > 0 && (
              <div className="tool-trace">
                {m.toolCalls.map((t, i) => (
                  <span key={i} className="tool-chip" title={t.output}>
                    ⚙ {t.tool}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
        {status === "sending" && (
          <div className="chat-bubble chat-bubble--assistant chat-bubble--pending">
            <div className="chat-bubble__label">AI Agent</div>
            <div className="chat-bubble__content">Thinking &amp; calling tools&hellip;</div>
          </div>
        )}
      </div>

      <form className="chat-input-row" onSubmit={handleSend}>
        <input
          type="text"
          placeholder="Describe your interaction..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button className="btn-primary" type="submit" disabled={status === "sending"}>
          Send
        </button>
      </form>
    </div>
  );
}
