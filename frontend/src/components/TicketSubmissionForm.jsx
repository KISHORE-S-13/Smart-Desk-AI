import React, { useState, useEffect, useRef } from "react";
import { ticketApi, aiApi } from "../services/api";
import {
  Sparkles,
  Send,
  AlertCircle,
  CheckCircle2,
  Cpu,
  RefreshCw,
  Zap,
  RotateCcw
} from "lucide-react";

export default function TicketSubmissionForm({
  onTicketCreated,
  onCancel,
  isEmbedded = false
}) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [impact, setImpact] = useState("Medium");
  const [urgency, setUrgency] = useState("Medium");

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [aiPreview, setAiPreview] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [fallbackNotice, setFallbackNotice] = useState("");
  const [successNotice, setSuccessNotice] = useState("");

  const timerRef = useRef(null);
  const abortControllerRef = useRef(null);
  const submissionLockRef = useRef(false);

  // Timer effect for analysis
  useEffect(() => {
    if (isAnalyzing) {
      setElapsedSeconds(0);
      timerRef.current = setInterval(() => {
        setElapsedSeconds((prev) => {
          if (prev >= 30) {
            clearInterval(timerRef.current);
            return 30;
          }
          return prev + 1;
        });
      }, 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isAnalyzing]);

  // Clean up abort controller on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const handleAIAnalyzePreview = async () => {
    if (!title.trim()) {
      setErrorMsg("Please enter an issue title before triggering AI analysis.");
      return;
    }
    setErrorMsg("");
    setFallbackNotice("");
    setIsAnalyzing(true);

    abortControllerRef.current = new AbortController();

    try {
      const res = await aiApi.analyze({
        title: title.trim(),
        description: description.trim(),
        impact,
        urgency
      });

      const analysis = res.data.analysis;
      setAiPreview(analysis);

      if (analysis.analysis_source === "rule_based_fallback") {
        setFallbackNotice(
          "Automatic rule-based classification was applied (Gemini response took over 30s or experienced a temporary service spike)."
        );
      }
    } catch (err) {
      if (err.name === "CanceledError" || err.code === "ERR_CANCELED") {
        console.log("Analysis preview cancelled by user.");
      } else {
        setErrorMsg(
          err.response?.data?.error ||
          "Gemini connection timed out or is temporarily unavailable. You can still submit the ticket directly."
        );
      }
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleCancelAnalysis = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setIsAnalyzing(false);
    setErrorMsg("AI analysis cancelled. You can submit directly or re-run analysis.");
  };

  const handleResetForm = () => {
    setTitle("");
    setDescription("");
    setImpact("Medium");
    setUrgency("Medium");
    setAiPreview(null);
    setErrorMsg("");
    setFallbackNotice("");
    setSuccessNotice("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (submissionLockRef.current || isSubmitting) {
      return; // Prevent duplicate rapid clicks
    }

    if (!title.trim() || !description.trim()) {
      setErrorMsg("Both Title and Description are required to submit.");
      return;
    }

    // Cancel in-flight preview request if user chooses to submit immediately
    if (isAnalyzing && abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsAnalyzing(false);
    }

    submissionLockRef.current = true;
    setIsSubmitting(true);
    setErrorMsg("");
    setSuccessNotice("");

    try {
      const payload = {
        title: title.trim(),
        description: description.trim(),
        impact,
        urgency,
        pre_analysis: aiPreview
      };

      const res = await ticketApi.create(payload);
      const ticket = res.data.ticket;

      if (res.data.duplicate_prevented) {
        alert(`Duplicate prevented: Ticket ${ticket.ticket_number} for this issue was already registered.`);
      }

      setSuccessNotice(`Ticket ${ticket.ticket_number} created successfully and added to In Progress & Ongoing!`);
      handleResetForm();

      if (onTicketCreated) {
        onTicketCreated(ticket);
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.error || "Failed to submit ticket. Please check network connection.");
    } finally {
      setIsSubmitting(false);
      submissionLockRef.current = false;
    }
  };

  return (
    <form onSubmit={handleSubmit} className={`modal-body-form ${isEmbedded ? "submission-form-embedded" : ""}`}>
      {successNotice && (
        <div className="alert-banner alert-success mb-3">
          <CheckCircle2 size={16} />
          <span>{successNotice}</span>
        </div>
      )}

      {errorMsg && (
        <div className="alert-banner alert-error mb-3">
          <AlertCircle size={16} />
          <span>{errorMsg}</span>
        </div>
      )}

      {fallbackNotice && (
        <div className="alert-banner alert-warning mb-3">
          <Zap size={16} />
          <span>{fallbackNotice}</span>
        </div>
      )}

      <div className="form-group">
        <label className="form-label">
          Issue Title <span className="req">*</span>
        </label>
        <input
          type="text"
          className="form-input"
          placeholder="e.g. My office VPN is not connecting or Outlook disconnected"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
          disabled={isSubmitting}
        />
      </div>

      <div className="form-row-2">
        <div className="form-group">
          <label className="form-label">Impact (Optional)</label>
          <select
            className="form-select"
            value={impact}
            onChange={(e) => setImpact(e.target.value)}
            disabled={isSubmitting}
          >
            <option value="Low">Low - Affects only me / minor inconvenience</option>
            <option value="Medium">Medium - Standard operational disruption</option>
            <option value="High">High - Critical work blocked / multiple users</option>
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Urgency (Optional)</label>
          <select
            className="form-select"
            value={urgency}
            onChange={(e) => setUrgency(e.target.value)}
            disabled={isSubmitting}
          >
            <option value="Low">Low - Can wait 2-3 business days</option>
            <option value="Medium">Medium - Normal business response (24 hrs)</option>
            <option value="High">High - Immediate attention needed</option>
          </select>
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">
          Detailed Description <span className="req">*</span>
        </label>
        <textarea
          className="form-textarea"
          rows={4}
          placeholder="Provide exact error messages, affected device, steps already tried..."
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          required
          disabled={isSubmitting}
        ></textarea>
      </div>

      {/* AI Pre-Analysis & Triage Section */}
      <div className="ai-preview-section">
        <div className="ai-preview-header">
          {!isAnalyzing ? (
            <button
              type="button"
              className="btn-ai-preview"
              onClick={handleAIAnalyzePreview}
              disabled={!title.trim() || isSubmitting}
            >
              <Sparkles size={16} />
              <span>{aiPreview ? "Re-Run AI Triage" : "AI Triage Preview (Gemini)"}</span>
            </button>
          ) : (
            <div className="analyzing-status-pill">
              <RefreshCw size={14} className="spin-icon" />
              <span>Analyzing with Gemini ({elapsedSeconds}s / 30s max)...</span>
              <button
                type="button"
                className="btn-cancel-inline"
                onClick={handleCancelAnalysis}
              >
                Cancel
              </button>
            </div>
          )}

          <span className="ai-preview-hint">
            {isAnalyzing
              ? "Evaluating ITIL category, priority, and self-help steps (30s timeout active)."
              : "Preview AI classification and recommended steps before ticket dispatch."}
          </span>
        </div>

        {/* In-Flight Analysis Progress Bar */}
        {isAnalyzing && (
          <div className="analysis-progress-container">
            <div
              className="analysis-progress-bar"
              style={{ width: `${Math.min((elapsedSeconds / 30) * 100, 100)}%` }}
            ></div>
          </div>
        )}

        {/* AI Preview Result Card */}
        {aiPreview && (
          <div className="ai-preview-card">
            <div className="ai-preview-card-top">
              <div className="ai-preview-badges">
                <span className="badge-preview-cat">{aiPreview.category}</span>
                <span className={`badge-preview-pri pri-${aiPreview.priority?.toLowerCase()}`}>
                  Priority: {aiPreview.priority}
                </span>
                <span className="badge-preview-team">{aiPreview.assigned_support_team}</span>
              </div>
              <span
                className={`engine-badge-mini ${
                  aiPreview.analysis_source === "gemini" ? "engine-gemini" : "engine-fallback"
                }`}
              >
                <Cpu size={12} />
                {aiPreview.analysis_source === "gemini" ? "Gemini 3.8 Flash" : "Fallback Engine"}
              </span>
            </div>

            <p className="ai-preview-reason">
              <strong>Priority Reason:</strong> {aiPreview.reason_for_priority}
            </p>

            {aiPreview.recommended_troubleshooting_steps?.length > 0 && (
              <div className="preview-steps-box">
                <span className="preview-steps-title">
                  <CheckCircle2 size={14} /> Try these steps first:
                </span>
                <ul className="preview-steps-list">
                  {aiPreview.recommended_troubleshooting_steps.map((st, i) => (
                    <li key={i}>{st}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>

      <div className={isEmbedded ? "embedded-form-actions" : "modal-footer"}>
        {isEmbedded ? (
          <>
            <button
              type="button"
              className="btn-secondary"
              onClick={handleResetForm}
              disabled={isSubmitting}
            >
              <RotateCcw size={15} /> Clear Form
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={isSubmitting}
            >
              <Send size={16} />
              <span>{isSubmitting ? "Submitting Incident..." : "Submit Incident"}</span>
            </button>
          </>
        ) : (
          <>
            <button
              type="button"
              className="btn-secondary"
              onClick={onCancel}
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={isSubmitting}
            >
              <Send size={16} />
              <span>{isSubmitting ? "Submitting Ticket..." : "Submit Incident"}</span>
            </button>
          </>
        )}
      </div>
    </form>
  );
}