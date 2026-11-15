import React, { useState, useEffect } from "react";
import { ticketApi } from "../services/api";
import { useAuth } from "../context/AuthContext";
import StatusBadge from "./StatusBadge";
import PriorityBadge from "./PriorityBadge";
import TicketSubmissionForm from "./TicketSubmissionForm";
import {
  Search,
  Filter,
  PlusCircle,
  RefreshCw,
  ArrowUpRight,
  Sparkles,
  Cpu,
  Trash2,
  Clock,
  CheckCircle2,
  CheckCircle,
  Layers,
  FileText,
  User,
  MessageSquareQuote
} from "lucide-react";

const CATEGORIES = ["All", "Network", "Hardware", "Software", "Email", "Access Management", "Other"];
const PRIORITIES = ["All", "Critical", "High", "Medium", "Low"];

export default function TicketList({
  onSelectTicket,
  onOpenCreateTicket,
  initialSection = "in_progress"
}) {
  const { user, isAdmin } = useAuth();
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeSection, setActiveSection] = useState(initialSection); // "submit" | "in_progress" | "completed" | "all"
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("All");
  const [priorityFilter, setPriorityFilter] = useState("All");
  const [notification, setNotification] = useState("");

  const fetchTickets = async () => {
    setLoading(true);
    try {
      const params = {};
      if (search.trim()) params.search = search.trim();
      if (categoryFilter !== "All") params.category = categoryFilter;
      if (priorityFilter !== "All") params.priority = priorityFilter;

      const res = await ticketApi.list(params);
      setTickets(res.data.tickets || []);
    } catch {
      setTickets([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTickets();
  }, [categoryFilter, priorityFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchTickets();
  };

  const handleTicketCreatedFromForm = (newTicket) => {
    setNotification(`Incident request ${newTicket.ticket_number} created successfully and added to In Progress & Ongoing!`);
    setTimeout(() => setNotification(""), 6000);
    fetchTickets();
    // Automatically switch to In Progress & Ongoing
    setActiveSection("in_progress");
  };

  const canDeleteTicket = (t) => {
    if (isAdmin) return true;
    if (t.created_by_user_id === user?.id) {
      return t.status !== "Resolved" && t.status !== "Closed";
    }
    return false;
  };

  const handleDelete = async (e, t) => {
    e.stopPropagation();
    const confirmed = window.confirm("Are you sure you want to delete this request?");
    if (!confirmed) return;

    try {
      await ticketApi.delete(t.id);
      setNotification(`Incident request ${t.ticket_number} deleted successfully.`);
      setTimeout(() => setNotification(""), 4000);
      fetchTickets();
    } catch (err) {
      alert(err.response?.data?.error || "Failed to delete ticket.");
    }
  };

  // Filter into the two operational sections (excluding soft-deleted, already done by backend)
  const inProgressStatuses = ["New", "Triaged", "Assigned", "In Progress"];
  const completedStatuses = ["Resolved", "Closed"];

  const inProgressTickets = tickets.filter((t) => inProgressStatuses.includes(t.status));
  const completedTickets = tickets.filter((t) => completedStatuses.includes(t.status));

  return (
    <div className="ticket-list-view dashboard-three-sections">
      {/* Header Banner */}
      <div className="view-header">
        <div>
          <h1 className="view-title">
            {isAdmin ? "Enterprise Operations & Ticket Management" : "Employee IT Incident Dashboard"}
          </h1>
          <p className="view-subtitle">
            {isAdmin
              ? "Oversee, assign, and resolve multi-tier enterprise support incidents across all departments."
              : "Submit new service requests, track active ongoing resolutions, and inspect completed incident logs."}
          </p>
        </div>

        <div className="view-header-actions">
          <button
            className={`btn-primary ${activeSection === "submit" ? "btn-active-highlight" : ""}`}
            onClick={() => setActiveSection("submit")}
          >
            <PlusCircle size={16} /> Submit New Ticket
          </button>
          <button className="btn-secondary" onClick={fetchTickets} title="Refresh Live State">
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </div>

      {notification && (
        <div className="alert-banner alert-success mb-4">
          <CheckCircle2 size={16} />
          <span>{notification}</span>
        </div>
      )}

      {/* KPI Section Metric Cards */}
      <div className="kpi-cards-grid three-section-kpis">
        <div
          className={`kpi-card card-open clickable-kpi ${activeSection === "in_progress" ? "kpi-active-ring" : ""}`}
          onClick={() => setActiveSection("in_progress")}
          title="View In Progress & Ongoing tickets"
        >
          <div className="kpi-icon-wrap">
            <Clock size={24} />
          </div>
          <div className="kpi-body">
            <span className="kpi-label">In Progress & Ongoing</span>
            <div className="kpi-val-row">
              <span className="kpi-value">{inProgressTickets.length}</span>
              <span className="kpi-subtag">New • Triaged • Assigned • In Progress</span>
            </div>
          </div>
        </div>

        <div
          className={`kpi-card card-resolved clickable-kpi ${activeSection === "completed" ? "kpi-active-ring" : ""}`}
          onClick={() => setActiveSection("completed")}
          title="View Completed & Resolved tickets"
        >
          <div className="kpi-icon-wrap">
            <CheckCircle size={24} />
          </div>
          <div className="kpi-body">
            <span className="kpi-label">Completed Tickets</span>
            <div className="kpi-val-row">
              <span className="kpi-value">{completedTickets.length}</span>
              <span className="kpi-subtag">Resolved & Closed with Notes</span>
            </div>
          </div>
        </div>

        <div
          className={`kpi-card card-total clickable-kpi ${activeSection === "submit" ? "kpi-active-ring" : ""}`}
          onClick={() => setActiveSection("submit")}
          title="Open Ticket Submission Form"
        >
          <div className="kpi-icon-wrap">
            <PlusCircle size={24} />
          </div>
          <div className="kpi-body">
            <span className="kpi-label">Submit Ticket</span>
            <div className="kpi-val-row">
              <span className="kpi-value text-blue">+</span>
              <span className="kpi-subtag">Instant Gemini AI Triage</span>
            </div>
          </div>
        </div>
      </div>

      {/* Section Switcher Tabs */}
      <div className="dashboard-section-tabs-bar">
        <div className="section-tabs-group">
          <button
            className={`section-tab-btn ${activeSection === "in_progress" ? "active" : ""}`}
            onClick={() => setActiveSection("in_progress")}
          >
            <Clock size={16} />
            <span>In Progress & Ongoing</span>
            <span className="section-tab-badge badge-ongoing">{inProgressTickets.length}</span>
          </button>

          <button
            className={`section-tab-btn ${activeSection === "completed" ? "active" : ""}`}
            onClick={() => setActiveSection("completed")}
          >
            <CheckCircle2 size={16} />
            <span>Completed Tickets</span>
            <span className="section-tab-badge badge-completed">{completedTickets.length}</span>
          </button>

          <button
            className={`section-tab-btn ${activeSection === "submit" ? "active" : ""}`}
            onClick={() => setActiveSection("submit")}
          >
            <PlusCircle size={16} />
            <span>Submit Ticket</span>
          </button>

          <button
            className={`section-tab-btn tab-all-sections ${activeSection === "all" ? "active" : ""}`}
            onClick={() => setActiveSection("all")}
          >
            <Layers size={16} />
            <span>All Sections</span>
          </button>
        </div>

        {/* Global Filter Toolbar for Ticket Tables */}
        {activeSection !== "submit" && (
          <div className="section-filter-inline">
            <form onSubmit={handleSearchSubmit} className="search-form-compact">
              <Search size={14} className="search-icon" />
              <input
                type="text"
                className="search-input-compact"
                placeholder="Filter by ID, title, or keywords..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </form>

            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="filter-select-compact"
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>{c === "All" ? "All Categories" : c}</option>
              ))}
            </select>

            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="filter-select-compact"
            >
              {PRIORITIES.map((p) => (
                <option key={p} value={p}>{p === "All" ? "All Priorities" : p}</option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* ============================================================== */}
      {/* SECTION 1: SUBMIT TICKET FORM */}
      {/* ============================================================== */}
      {(activeSection === "submit" || activeSection === "all") && (
        <div className="dashboard-section-block section-submit-block">
          <div className="section-block-header">
            <div className="section-title-wrap">
              <PlusCircle size={18} className="text-primary" />
              <h3>1. Submit Ticket</h3>
              <span className="section-pill-tag">Self-Service AI Intake</span>
            </div>
            <p className="section-desc">
              Describe your IT issue below. Gemini AI assesses category, business urgency, and ITIL priority in real-time.
              Upon submission, your ticket automatically routes into <strong>In Progress & Ongoing</strong>.
            </p>
          </div>

          <div className="submit-form-card">
            <TicketSubmissionForm
              isEmbedded={true}
              onTicketCreated={handleTicketCreatedFromForm}
            />
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* SECTION 2: IN PROGRESS & ONGOING */}
      {/* ============================================================== */}
      {(activeSection === "in_progress" || activeSection === "all") && (
        <div className="dashboard-section-block section-ongoing-block">
          <div className="section-block-header">
            <div className="section-title-wrap">
              <Clock size={18} className="text-amber-500" />
              <h3>2. In Progress & Ongoing</h3>
              <span className="section-pill-tag tag-warning">
                {inProgressTickets.length} Active {inProgressTickets.length === 1 ? "Incident" : "Incidents"}
              </span>
            </div>
            <p className="section-desc">
              {isAdmin
                ? "Displaying all active employee incidents currently in New, Triaged, Assigned, or In Progress status. Click any row to assign or update."
                : "Displaying your active incidents undergoing diagnosis or resolution. Click any row to review current status and AI troubleshooting."}
            </p>
          </div>

          <div className="analytics-card no-padding">
            {loading ? (
              <div className="dashboard-loading-state">
                <RefreshCw className="spin-icon" size={20} />
                <p>Loading active ongoing incidents...</p>
              </div>
            ) : inProgressTickets.length === 0 ? (
              <div className="empty-state-card">
                <CheckCircle2 size={32} className="text-emerald-500" />
                <h4>No In Progress Incidents</h4>
                <p>
                  {isAdmin
                    ? "There are currently no active unresolved tickets across departments."
                    : "You currently have no open or ongoing IT requests."}
                </p>
                <button className="btn-primary mt-3" onClick={() => setActiveSection("submit")}>
                  <PlusCircle size={15} /> Submit an Incident
                </button>
              </div>
            ) : (
              <div className="table-responsive">
                <table className="enterprise-table">
                  <thead>
                    <tr>
                      <th>Ticket ID</th>
                      <th>Title</th>
                      <th>Category</th>
                      <th>Priority</th>
                      <th>Status</th>
                      <th>Assigned Team</th>
                      {isAdmin && <th>Reported By</th>}
                      <th>AI Engine</th>
                      <th>Created</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {inProgressTickets.map((t) => (
                      <tr key={t.id} onClick={() => onSelectTicket(t)} className="clickable-row">
                        <td className="font-semibold text-primary">{t.ticket_number}</td>
                        <td className="ticket-table-title">{t.title}</td>
                        <td><span className="cat-chip">{t.category}</span></td>
                        <td><PriorityBadge priority={t.priority} /></td>
                        <td><StatusBadge status={t.status} /></td>
                        <td className="text-sm">{t.assigned_team}</td>
                        {isAdmin && <td className="text-sm text-slate-600">{t.creator_name}</td>}
                        <td>
                          <span className={`engine-badge-mini ${t.analysis_source === "gemini" ? "engine-gemini" : "engine-fallback"}`}>
                            <Cpu size={11} />
                            {t.analysis_source === "gemini" ? "Gemini" : "Fallback"}
                          </span>
                        </td>
                        <td className="text-sm text-slate-500">
                          {new Date(t.created_at).toLocaleDateString()}
                        </td>
                        <td onClick={(e) => e.stopPropagation()}>
                          <div className="table-actions-cell">
                            <button
                              className="btn-view-table"
                              onClick={() => onSelectTicket(t)}
                            >
                              {isAdmin ? "Manage" : "Details"} <ArrowUpRight size={13} />
                            </button>
                            {canDeleteTicket(t) && (
                              <button
                                className="btn-delete-table"
                                title="Delete request"
                                onClick={(e) => handleDelete(e, t)}
                              >
                                <Trash2 size={13} /> Delete
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* SECTION 3: COMPLETED TICKETS */}
      {/* ============================================================== */}
      {(activeSection === "completed" || activeSection === "all") && (
        <div className="dashboard-section-block section-completed-block">
          <div className="section-block-header">
            <div className="section-title-wrap">
              <CheckCircle2 size={18} className="text-emerald-500" />
              <h3>3. Completed Tickets</h3>
              <span className="section-pill-tag tag-success">
                {completedTickets.length} Resolved / Closed
              </span>
            </div>
            <p className="section-desc">
              {isAdmin
                ? "Displaying all completed incidents with status Resolved or Closed. Inspect resolution notes and service delivery history."
                : "Displaying your resolved and closed incidents. Review technician resolution notes and confirmed fixes."}
            </p>
          </div>

          <div className="analytics-card no-padding">
            {loading ? (
              <div className="dashboard-loading-state">
                <RefreshCw className="spin-icon" size={20} />
                <p>Loading completed tickets...</p>
              </div>
            ) : completedTickets.length === 0 ? (
              <div className="empty-state-card">
                <FileText size={32} className="text-slate-400" />
                <h4>No Completed Tickets Yet</h4>
                <p>Tickets moved to Resolved or Closed status will automatically appear here with resolution notes.</p>
              </div>
            ) : (
              <div className="table-responsive">
                <table className="enterprise-table">
                  <thead>
                    <tr>
                      <th>Ticket ID</th>
                      <th>Title</th>
                      <th>Category</th>
                      <th>Priority</th>
                      <th>Status</th>
                      <th>Resolution Notes & Root Cause</th>
                      {isAdmin && <th>Reported By</th>}
                      <th>Completed Date</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {completedTickets.map((t) => (
                      <tr key={t.id} onClick={() => onSelectTicket(t)} className="clickable-row">
                        <td className="font-semibold text-primary">{t.ticket_number}</td>
                        <td className="ticket-table-title">{t.title}</td>
                        <td><span className="cat-chip">{t.category}</span></td>
                        <td><PriorityBadge priority={t.priority} /></td>
                        <td><StatusBadge status={t.status} /></td>
                        <td className="resolution-notes-cell">
                          {t.resolution_notes ? (
                            <div className="resolution-notes-snippet" title={t.resolution_notes}>
                              <MessageSquareQuote size={13} className="text-emerald-600 inline-icon" />
                              <span>{t.resolution_notes}</span>
                            </div>
                          ) : (
                            <span className="text-slate-400 text-xs italic">No notes recorded</span>
                          )}
                        </td>
                        {isAdmin && <td className="text-sm text-slate-600">{t.creator_name}</td>}
                        <td className="text-sm text-slate-500">
                          {t.resolved_at
                            ? new Date(t.resolved_at).toLocaleDateString()
                            : new Date(t.updated_at || t.created_at).toLocaleDateString()}
                        </td>
                        <td onClick={(e) => e.stopPropagation()}>
                          <div className="table-actions-cell">
                            <button
                              className="btn-view-table"
                              onClick={() => onSelectTicket(t)}
                            >
                              Inspect <ArrowUpRight size={13} />
                            </button>
                            {canDeleteTicket(t) && (
                              <button
                                className="btn-delete-table"
                                title="Delete request"
                                onClick={(e) => handleDelete(e, t)}
                              >
                                <Trash2 size={13} /> Delete
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}