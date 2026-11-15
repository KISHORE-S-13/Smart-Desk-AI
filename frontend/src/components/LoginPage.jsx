import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import {
  Sparkles,
  Shield,
  User,
  Lock,
  Mail,
  ArrowRight,
  AlertCircle,
  Eye,
  EyeOff,
  ShieldCheck,
  RefreshCw
} from "lucide-react";

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [activeDemoRole, setActiveDemoRole] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      setError("Please enter both email and password.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await login(email, password);
    } catch (err) {
      setError(err.response?.data?.error || "Login failed. Check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  const handleQuickDemoLogin = async (demoEmail, demoPass, role) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setActiveDemoRole(role);
    setLoading(true);
    setError("");
    try {
      await login(demoEmail, demoPass);
    } catch (err) {
      setError(err.response?.data?.error || "Demo login failed.");
    } finally {
      setLoading(false);
      setActiveDemoRole(null);
    }
  };

  return (
    <div className="login-page-wrapper">
      {/* Futuristic Background Ambient Glow Orbs */}
      <div className="login-ambient-orb login-ambient-orb-1" />
      <div className="login-ambient-orb login-ambient-orb-2" />
      <div className="login-ambient-orb login-ambient-orb-3" />

      {/* Cyber Grid Pattern Background */}
      <div className="login-cyber-grid" />

      {/* Subtle Floating Tech Particles */}
      <div className="login-particles-layer">
        <span className="particle particle-1" />
        <span className="particle particle-2" />
        <span className="particle particle-3" />
        <span className="particle particle-4" />
        <span className="particle particle-5" />
      </div>

      <div className="login-card-container">
        {/* Brand header */}
        <div className="login-header">
          <div className="login-logo-wrap">
            <div className="logo-glow-ring" />
            <Sparkles size={28} className="logo-sparkle-icon" />
          </div>

          <div className="login-badge-row">
            <span className="ai-status-pill">
              <span className="pulse-dot" />
              <span>USM Core v2.4 • Generative AI</span>
            </span>
          </div>

          <h1 className="login-title">
            SmartDesk <span className="ai-gradient-text">AI</span>
          </h1>
          <p className="login-subtitle">
            Generative AI Powered Unified Service Management
          </p>
        </div>

        {error && (
          <div className="alert-banner alert-error">
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        {/* Standard Form */}
        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label className="form-label">Corporate Email</label>
            <div className="input-icon-wrap">
              <Mail size={16} className="input-icon" />
              <input
                type="email"
                className="form-input with-icon"
                placeholder="name@smartdesk.ai"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <div className="input-icon-wrap">
              <Lock size={16} className="input-icon" />
              <input
                type={showPassword ? "text" : "password"}
                className="form-input with-icon with-password-toggle"
                placeholder="Enter password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <button
                type="button"
                className="password-toggle-btn"
                onClick={() => setShowPassword(!showPassword)}
                tabIndex="-1"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            className="btn-primary btn-block btn-login"
            disabled={loading}
          >
            {loading ? (
              <>
                <RefreshCw size={16} className="spin-icon" />
                <span>Authenticating Identity...</span>
              </>
            ) : (
              <>
                <span>Sign In to Portal</span>
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </form>

        {/* 1-Click Demo Accounts */}
        <div className="demo-accounts-section">
          <div className="demo-accounts-title">
            <span className="title-divider-line" />
            <span className="title-text">Or Instant Demo Access</span>
            <span className="title-divider-line" />
          </div>

          <div className="demo-buttons-grid">
            <button
              type="button"
              className={`demo-card-btn demo-card-employee ${activeDemoRole === "employee" ? "active" : ""}`}
              onClick={() => handleQuickDemoLogin("employee@smartdesk.ai", "Employee@123", "employee")}
              disabled={loading}
            >
              <div className="demo-btn-icon icon-employee">
                <User size={18} />
              </div>
              <div className="demo-btn-text">
                <div className="demo-card-topline">
                  <strong>Alex Rivera</strong>
                  <span className="demo-role-badge badge-employee">EMPLOYEE</span>
                </div>
                <small>employee@smartdesk.ai • Engineering</small>
              </div>
              <div className="demo-card-action">
                <span className="action-pill">Log In →</span>
              </div>
            </button>

            <button
              type="button"
              className={`demo-card-btn demo-card-admin ${activeDemoRole === "admin" ? "active" : ""}`}
              onClick={() => handleQuickDemoLogin("admin@smartdesk.ai", "Admin@123", "admin")}
              disabled={loading}
            >
              <div className="demo-btn-icon icon-admin">
                <Shield size={18} />
              </div>
              <div className="demo-btn-text">
                <div className="demo-card-topline">
                  <strong>Sarah Chen</strong>
                  <span className="demo-role-badge badge-admin">IT ADMIN</span>
                </div>
                <small>admin@smartdesk.ai • IT Operations</small>
              </div>
              <div className="demo-card-action">
                <span className="action-pill action-pill-admin">Log In →</span>
              </div>
            </button>
          </div>
        </div>

        {/* Demo Authentication Limitations Notice */}
        <div className="auth-limitations-notice">
          <ShieldCheck size={16} className="notice-icon" />
          <span>
            <strong>Demo Architecture Notice:</strong> Uses local password hashing (Werkzeug PBKDF2) and stateless JWT tokens. Enterprise SSO (SAML 2.0 / Okta / Azure AD) integration is recommended for production deployment.
          </span>
        </div>
      </div>
    </div>
  );
}
