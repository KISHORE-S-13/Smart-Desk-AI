import React, { useState, useRef, useEffect } from "react";
import { aiApi } from "../services/api";
import {
  X,
  Bot,
  Send,
  Sparkles,
  BookOpen,
  User,
  ShieldCheck,
  RefreshCw
} from "lucide-react";

const SUGGESTED_QUERIES = [
  "How do I fix GlobalProtect VPN gateway unreachable error?",
  "What is the corporate password policy and lockout time?",
  "How to connect to Corp-Secure Wi-Fi on Windows?",
  "Outlook is disconnected and won't sync my emails",
  "How can I install VS Code without admin privileges?"
];

export default function ChatbotDrawer({ isOpen, onClose }) {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hello! I am the **SmartDesk AI Knowledge Assistant**. Ask me any IT support questions regarding company VPN, Wi-Fi, Outlook, passwords, or software installations. I will answer based strictly on verified corporate IT policies.",
      source_type: "system",
      sources: []
    }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  if (!isOpen) return null;

  const handleSend = async (queryText) => {
    const text = queryText || input;
    if (!text.trim() || loading) return;

    const userMsg = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await aiApi.chat(text, messages);
      const botMsg = {
        role: "assistant",
        content: res.data.answer,
        source_type: res.data.source_type,
        sources: res.data.sources || []
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "I am currently unable to retrieve knowledge documents. Please try again in a few moments or submit a support ticket.",
          source_type: "error",
          sources: []
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div className="drawer-container chatbot-drawer" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <div className="drawer-header-brand">
            <div className="bot-avatar-header">
              <Bot size={20} />
            </div>
            <div>
              <h3 className="drawer-title">IT Knowledge Assistant</h3>
              <div className="drawer-status">
                <span className="dot-green"></span>
                <span>RAG Grounded • Gemini 3.8 Flash</span>
              </div>
            </div>
          </div>
          <button className="btn-close-drawer" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {/* Quick query chips */}
        <div className="chat-chips-container">
          <span className="chips-label">Frequently Asked:</span>
          <div className="chips-scroll">
            {SUGGESTED_QUERIES.map((q, idx) => (
              <button
                key={idx}
                className="chip-btn"
                onClick={() => handleSend(q)}
                disabled={loading}
              >
                {q}
              </button>
            ))}
          </div>
        </div>

        {/* Messages scroll area */}
        <div className="chat-messages-area">
          {messages.map((m, i) => (
            <div key={i} className={`chat-message-row msg-${m.role}`}>
              <div className="msg-avatar">
                {m.role === "assistant" ? <Sparkles size={16} /> : <User size={16} />}
              </div>
              <div className="msg-bubble">
                <div className="msg-content markdown-body">
                  {m.content.split("\n").map((line, li) => (
                    <p key={li}>{line}</p>
                  ))}
                </div>

                {m.sources && m.sources.length > 0 && (
                  <div className="msg-sources">
                    <span className="sources-label">
                      <BookOpen size={12} /> Grounded Sources:
                    </span>
                    <div className="sources-tags">
                      {m.sources.map((s) => (
                        <span key={s.id} className="source-tag">
                          {s.title}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {m.source_type && m.source_type !== "system" && (
                  <div className="msg-meta-source">
                    Engine: {m.source_type === "gemini_rag" ? "Gemini RAG" : "SmartDesk Knowledge Base"}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="chat-message-row msg-assistant">
              <div className="msg-avatar">
                <Sparkles size={16} />
              </div>
              <div className="msg-bubble typing-bubble">
                <span className="typing-dot"></span>
                <span className="typing-dot"></span>
                <span className="typing-dot"></span>
                <span className="typing-text">Consulting IT Knowledge Base...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input box */}
        <div className="chat-input-bar">
          <input
            type="text"
            className="chat-input-field"
            placeholder="Type your IT support question (e.g. VPN issues, password reset)..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
          />
          <button
            className="btn-chat-send"
            onClick={() => handleSend()}
            disabled={!input.trim() || loading}
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
