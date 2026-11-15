import React from "react";
import { useAuth } from "../context/AuthContext";
import { Sparkles, Bot, LogOut, Shield, User as UserIcon } from "lucide-react";

export default function Navbar({ onOpenChatbot }) {
  const { user, logout, isAdmin } = useAuth();

  return (
    <header className="enterprise-navbar">
      <div className="navbar-left">
        <div className="navbar-brand mobile-brand">
          <div className="brand-logo-container">
            <Sparkles className="brand-icon" size={20} />
          </div>
          <div className="brand-text">
            <span className="brand-title">
              SmartDesk <span className="brand-highlight">AI</span>
            </span>
          </div>
        </div>
        <div className="navbar-desktop-context">
          <span className="context-dot-live"></span>
          <span className="navbar-context-label">Enterprise USM Console</span>
        </div>
      </div>

      <div className="navbar-center">
        <div className="model-indicator-badge">
          <span className="live-pulse"></span>
          <span>Gemini 3.8 Flash Active</span>
        </div>
      </div>

      <div className="navbar-actions">
        <button
          className="btn-assistant-toggle"
          onClick={onOpenChatbot}
          title="Open IT Knowledge Assistant"
        >
          <Bot size={18} />
          <span>AI Support Bot</span>
        </button>

        <div className="user-profile-widget">
          <div className="user-avatar">
            {isAdmin ? <Shield size={16} /> : <UserIcon size={16} />}
          </div>
          <div className="user-meta">
            <span className="user-name">{user?.name}</span>
            <span className="user-role-tag">{isAdmin ? "IT Administrator" : user?.department || "Employee"}</span>
          </div>
          <button className="btn-logout" onClick={logout} title="Sign Out">
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </header>
  );
}