import React from "react";
import { useAuth } from "../context/AuthContext";
import {
  Sparkles,
  LayoutDashboard,
  Ticket,
  PlusCircle,
  BookOpen,
  Bot
} from "lucide-react";

export default function Sidebar({
  activeTab,
  setActiveTab,
  onOpenCreateTicket,
  onOpenTickets,
  onOpenChatbot
}) {
  const { isAdmin } = useAuth();

  return (
    <aside className="enterprise-sidebar">
      {/* 1. SmartDesk AI Logo fixed at the top */}
      <div className="sidebar-brand-header">
        <div className="brand-logo-container">
          <Sparkles className="brand-icon" size={22} />
        </div>
        <div className="brand-text">
          <span className="brand-title">
            SmartDesk <span className="brand-highlight">AI</span>
          </span>
          <span className="brand-subtitle">Unified Service Management</span>
        </div>
      </div>

      {/* 2. Scrollable Navigation Area */}
      <div className="sidebar-nav-scroll-area">
        <div className="sidebar-section-title">MAIN WORKSPACE</div>
        <nav className="sidebar-nav">
          {isAdmin ? (
            <>
              <button
                className={`sidebar-nav-item ${activeTab === "overview" ? "active" : ""}`}
                onClick={() => setActiveTab("overview")}
              >
                <LayoutDashboard size={18} />
                <span>Operations Overview</span>
              </button>
              <button
                className={`sidebar-nav-item ${activeTab === "tickets" ? "active" : ""}`}
                onClick={onOpenTickets || (() => setActiveTab("tickets"))}
              >
                <Ticket size={18} />
                <span>Incident Dashboard</span>
              </button>
              <button
                className="sidebar-nav-item btn-create-nav"
                onClick={onOpenCreateTicket}
              >
                <PlusCircle size={18} />
                <span>Submit Ticket</span>
              </button>
              <button
                className={`sidebar-nav-item ${activeTab === "knowledge" ? "active" : ""}`}
                onClick={() => setActiveTab("knowledge")}
              >
                <BookOpen size={18} />
                <span>Knowledge Base & PDF</span>
              </button>
            </>
          ) : (
            <>
              <button
                className={`sidebar-nav-item ${activeTab === "my-tickets" ? "active" : ""}`}
                onClick={onOpenTickets || (() => setActiveTab("my-tickets"))}
              >
                <Ticket size={18} />
                <span>Incident Dashboard</span>
              </button>
              <button
                className="sidebar-nav-item btn-create-nav"
                onClick={onOpenCreateTicket}
              >
                <PlusCircle size={18} />
                <span>Submit Ticket</span>
              </button>
              <button
                className={`sidebar-nav-item ${activeTab === "knowledge" ? "active" : ""}`}
                onClick={() => setActiveTab("knowledge")}
              >
                <BookOpen size={18} />
                <span>Self-Help Guides</span>
              </button>
            </>
          )}

          <div className="sidebar-divider"></div>
          <div className="sidebar-section-title">AI COPILOT</div>

          <button
            className="sidebar-nav-item ai-assistant-highlight"
            onClick={onOpenChatbot}
          >
            <Bot size={18} />
            <span>Ask Knowledge Assistant</span>
            <span className="copilot-pill">RAG</span>
          </button>
        </nav>
      </div>

      {/* 3. Anchored Footer at bottom */}
      <div className="sidebar-footer">
        <div className="sidebar-system-info">
          <div className="info-row">
            <span className="dot-green"></span>
            <span>USM Engine Online</span>
          </div>
          <small>SmartDesk AI v2.4 (Enterprise)</small>
        </div>
      </div>
    </aside>
  );
}