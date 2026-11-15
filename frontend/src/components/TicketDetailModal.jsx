import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { ticketApi } from "../services/api";
import StatusBadge from "./StatusBadge";
import PriorityBadge from "./PriorityBadge";
import {
  X,
  Sparkles,
  Cpu,
  Clock,
  User,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  History,
  Send,
  MessageSquareQuote,
  Trash2
} from "lucide-react";

const SUPPORT_TEAMS = [
  "Network Operations",
  "Workplace Tech Support",
  "Application Support",
  "Enterprise Messaging & Collaboration",
  "Identity & Access Management (IAM)",
  "Service Desk Tier 1"
];

const STATUS_OPTIONS = ["New", "Triaged", "Assigned", "In Progress", "Resolved", "Closed"];

export default function TicketDetailModal({ ticket, onClose, onTicketUpdated, onTicketDeleted }) {
  const { user, isAdmin } = useAuth();
  const [status, setStatus] = useState(ticket?.status || "New");
  const [assignedTeam, setAssignedTeam] = useState(ticket?.assigned_team || "Service Desk Tier 1");
  const [resolutionNotes, setResolutionNotes] = useState(ticket?.resolution_notes || "");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  if (!ticket) return null;

  // Employees can delete only their own non-resolved/non-closed tickets; Admins can delete any ticket
  const canDelete = isAdmin || (user?.id === ticket.created_by_user_id && ticket.status !== "Resolved" && ticket.status !== "Closed");

  const handleDelete = async () => {
    const confirmed = window.confirm("Are you sure you want to delete this request?");
    if (!confirmed) return;

    setIsDeleting(true);
    setErrorMsg("");
    setSuccessMsg("");

    try {
      await ticketApi.delete(ticket.id);
      if (onTicketDeleted) {
        onTicketDeleted(ticket.id);
      }
      onClose();
    } catch (err) {
      setErrorMsg(err.response?.data?.error || "Failed to delete ticket.");
      setIsDeleting(false);
    }
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMsg("");
    setSuccessMsg("");

    try {
      const payload = {
        status,
        ...(isAdmin && {
          assigned_team: assignedTeam,
          resolution_notes: resolutionNotes
        })
      };
      const res = await ticketApi.update(ticket.id, payload);
      setSuccessMsg("Ticket updated successfully!");
      if (onTicketUpdated) {
        onTicketUpdated(res.data.ticket);
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.error || "Failed to update ticket.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-container ticket-detail-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-header-left">
            <span className="ticket-modal-number">{ticket.ticket_number}</span>
            <StatusBadge status={ticket.status} />
            <PriorityBadge priority={ticket.priority} />
            <span className="badge-ticket-type">{ticket.ticket_type}</span>
          </div>
          <button className="btn-close-modal" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          {errorMsg && <div className="alert-banner alert-error">{errorMsg}</div>}
          {successMsg && <div className="alert-banner alert-success">{successMsg}</div>}

          <div className="ticket-detail-grid">
            {/* Left Column: Details & AI Panel */}
            <div className="ticket-main-col">
              <h2 className="ticket-detail-title">{ticket.title}</h2>

              <div className="ticket-meta-strip">
                <div className="meta-item">
                  <User size={14} />
                  <span>Requester: <strong>{ticket.creator_name}</strong></span>
                </div>
                <div className="meta-item">
                  <Clock size={14} />
                  <span>Created: {new Date(ticket.created_at).toLocaleString()}</span>
                </div>
                <div className="meta-item">
                  <ShieldCheck size={14} />
                  <span>Assigned Team: <strong>{ticket.assigned_team}</strong></span>
                </div>
              </div>

              <div className="ticket-section">
                <h4 className="section-label">Incident Description</h4>
                <div className="ticket-description-box">
                  {ticket.description}
                </div>
              </div>

              {/* Gemini AI Intelligence Box */}
              <div className="ai-analysis-card">
                <div className="ai-card-header">
                  <div className="ai-card-title">
                    <Sparkles size={18} className="ai-sparkle-icon" />
                    <span>Gemini AI Intelligent Triage</span>
                  </div>
                  <span className={`engine-badge ${ticket.analysis_source === "gemini" ? "engine-gemini" : "engine-fallback"}`}>
                    <Cpu size={12} />
                    {ticket.analysis_source === "gemini" ? "Gemini 3.8 Flash" : "Fallback Engine"}
                  </span>
                </div>

                <div className="ai-card-content">
                  <div className="ai-stat-row">
                    <div>
                      <span className="ai-field-label">Detected Category</span>
                      <span className="ai-field-value">{ticket.category}</span>
                    </div>
                    <div>
                      <span className="ai-field-label">Calculated Priority</span>
                      <span className="ai-field-value">{ticket.priority}</span>
                    </div>
                  </div>

                  <div className="ai-reason-box">
                    <strong>Priority Justification:</strong> {ticket.priority_reason || "Assessed according to enterprise business impact guidelines."}
                  </div>

                  {ticket.recommended_steps && ticket.recommended_steps.length > 0 && (
                    <div className="ai-steps-section">
                      <h5 className="ai-steps-heading">
                        <CheckCircle2 size={16} />
                        Recommended Troubleshooting Checklist
                      </h5>
                      <ul className="ai-steps-list">
                        {ticket.recommended_steps.map((step, idx) => (
                          <li key={idx} className="ai-step-item">
                            <span className="step-idx">{idx + 1}</span>
                            <span>{step}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {ticket.suggested_response && (
                    <div className="ai-suggested-response-box">
                      <div className="suggested-resp-header">
                        <MessageSquareQuote size={15} />
                        <span>AI Drafted Response for Employee</span>
                      </div>
                      <p>{ticket.suggested_response}</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Resolution Notes Display (if resolved) */}
              {ticket.resolution_notes && (
                <div className="ticket-section resolution-notes-display">
                  <h4 className="section-label">Engineer Resolution Notes</h4>
                  <div className="notes-box">{ticket.resolution_notes}</div>
                </div>
              )}
            </div>

            {/* Right Column: Workflow Actions & History */}
            <div className="ticket-actions-col">
              <div className="action-card">
                <h3 className="action-card-title">Service Workflow Actions</h3>
                <form onSubmit={handleUpdate}>
                  <div className="form-group">
                    <label className="form-label">Lifecycle Status</label>
                    <select
                      className="form-select"
                      value={status}
                      onChange={(e) => setStatus(e.target.value)}
                    >
                      {STATUS_OPTIONS.map((st) => (
                        <option key={st} value={st}>{st}</option>
                      ))}
                    </select>
                  </div>

                  {isAdmin && (
                    <>
                      <div className="form-group">
                        <label className="form-label">Assign Support Team</label>
                        <select
                          className="form-select"
                          value={assignedTeam}
                          onChange={(e) => setAssignedTeam(e.target.value)}
                        >
                          {SUPPORT_TEAMS.map((team) => (
                            <option key={team} value={team}>{team}</option>
                          ))}
                        </select>
                      </div>

                      <div className="form-group">
                        <label className="form-label">Engineer Resolution Notes</label>
                        <textarea
                          className="form-textarea"
                          rows={4}
                          placeholder="Document root cause, diagnostic findings, or actions taken..."
                          value={resolutionNotes}
                          onChange={(e) => setResolutionNotes(e.target.value)}
                        ></textarea>
                      </div>
                    </>
                  )}

                  <button
                    type="submit"
                    className="btn-primary btn-block"
                    disabled={isSubmitting || isDeleting}
                  >
                    {isSubmitting ? "Updating..." : "Commit Workflow Action"}
                  </button>
                  <small className="human-approval-hint">
                    Human-in-the-loop review ensures actions and notes are verified.
                  </small>
                </form>

                {canDelete && (
                  <div className="delete-action-section">
                    <button
                      type="button"
                      className="btn-danger btn-block"
                      onClick={handleDelete}
                      disabled={isSubmitting || isDeleting}
                    >
                      <Trash2 size={15} />
                      {isDeleting ? "Deleting..." : "Delete Incident Request"}
                    </button>
                  </div>
                )}
              </div>

              {/* Audit History Timeline */}
              <div className="action-card history-card">
                <h3 className="action-card-title">
                  <History size={16} />
                  Audit History
                </h3>
                <div className="history-timeline">
                  {ticket.history && ticket.history.length > 0 ? (
                    ticket.history.map((h, i) => (
                      <div key={i} className="timeline-item">
                        <div className="timeline-marker"></div>
                        <div className="timeline-content">
                          <div className="timeline-header">
                            <span className="timeline-actor">{h.user_name}</span>
                            <span className="timeline-time">
                              {new Date(h.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                          </div>
                          <div className="timeline-action">{h.action}</div>
                          <div className="timeline-details">{h.details}</div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="empty-text">No prior history logged.</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
