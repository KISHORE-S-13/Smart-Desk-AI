import React, { useEffect, useState } from "react";
import { dashboardApi } from "../services/api";
import StatusBadge from "./StatusBadge";
import PriorityBadge from "./PriorityBadge";
import {
  Ticket,
  Clock,
  CheckCircle,
  AlertOctagon,
  Users,
  FolderTree,
  ArrowUpRight,
  TrendingUp,
  RefreshCw
} from "lucide-react";

export default function AdminOverview({ onSelectTicket, onNavigateSection }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchStats = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await dashboardApi.getStats();
      setStats(res.data);
    } catch (err) {
      setError("Failed to fetch dashboard metrics.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="dashboard-loading-state">
        <RefreshCw className="spin-icon" size={24} />
        <p>Loading enterprise operations intelligence...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert-banner alert-error">
        {error}
        <button onClick={fetchStats} className="btn-secondary btn-sm ml-4">Retry</button>
      </div>
    );
  }

  const { metrics, by_category = {}, by_priority = {}, team_workload = {}, recent_incidents = [] } = stats || {};

  return (
    <div className="admin-overview-view">
      <div className="view-header">
        <div>
          <h1 className="view-title">Executive Operations Overview</h1>
          <p className="view-subtitle">Real-time IT service delivery health and GenAI workload routing</p>
        </div>
        <button className="btn-secondary" onClick={fetchStats}>
          <RefreshCw size={14} /> Refresh Metrics
        </button>
      </div>

      {/* KPI Cards Row */}
      <div className="kpi-cards-grid">
        <div className="kpi-card card-total">
          <div className="kpi-icon-wrap">
            <Ticket size={24} />
          </div>
          <div className="kpi-body">
            <span className="kpi-label">Total Lifecycle Tickets</span>
            <span className="kpi-value">{metrics?.total_tickets ?? 0}</span>
          </div>
        </div>

        <div
          className={`kpi-card card-open ${onNavigateSection ? "clickable-kpi" : ""}`}
          onClick={() => onNavigateSection && onNavigateSection("in_progress")}
          title="Click to view In Progress & Ongoing tickets"
        >
          <div className="kpi-icon-wrap">
            <Clock size={24} />
          </div>
          <div className="kpi-body">
            <span className="kpi-label">Active / In-Flight</span>
            <span className="kpi-value">{metrics?.open_tickets ?? 0}</span>
          </div>
        </div>

        <div
          className={`kpi-card card-resolved ${onNavigateSection ? "clickable-kpi" : ""}`}
          onClick={() => onNavigateSection && onNavigateSection("completed")}
          title="Click to view Completed & Resolved tickets"
        >
          <div className="kpi-icon-wrap">
            <CheckCircle size={24} />
          </div>
          <div className="kpi-body">
            <span className="kpi-label">Resolved & Closed</span>
            <span className="kpi-value">{metrics?.resolved_tickets ?? 0}</span>
          </div>
        </div>

        <div className="kpi-card card-critical">
          <div className="kpi-icon-wrap">
            <AlertOctagon size={24} />
          </div>
          <div className="kpi-body">
            <span className="kpi-label">Critical / High Priority</span>
            <span className="kpi-value">{metrics?.critical_and_high ?? 0}</span>
          </div>
        </div>
      </div>

      {/* Analytics Breakdown Grid */}
      <div className="analytics-split-grid">
        {/* Category Breakdown */}
        <div className="analytics-card">
          <div className="card-header-clean">
            <div className="card-title-wrap">
              <FolderTree size={18} />
              <h3>Tickets by Category</h3>
            </div>
          </div>
          <div className="category-bars-list">
            {Object.keys(by_category).length === 0 ? (
              <p className="empty-subtext">No category telemetry yet.</p>
            ) : (
              Object.entries(by_category).map(([cat, count]) => {
                const total = metrics?.total_tickets || 1;
                const pct = Math.round((count / total) * 100);
                return (
                  <div key={cat} className="bar-item">
                    <div className="bar-label-row">
                      <span className="bar-name">{cat}</span>
                      <span className="bar-count">{count} ({pct}%)</span>
                    </div>
                    <div className="bar-track">
                      <div className="bar-fill" style={{ width: `${pct}%` }}></div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Support Team Workload */}
        <div className="analytics-card">
          <div className="card-header-clean">
            <div className="card-title-wrap">
              <Users size={18} />
              <h3>Support Team Workload Allocation</h3>
            </div>
          </div>
          <div className="team-workload-list">
            {Object.keys(team_workload).length === 0 ? (
              <p className="empty-subtext">No team assignments yet.</p>
            ) : (
              Object.entries(team_workload).map(([team, count]) => {
                const total = metrics?.total_tickets || 1;
                const pct = Math.round((count / total) * 100);
                return (
                  <div key={team} className="team-workload-item">
                    <div className="team-info">
                      <span className="team-name">{team}</span>
                      <span className="team-tickets-badge">{count} tickets</span>
                    </div>
                    <div className="bar-track">
                      <div className="bar-fill team-fill" style={{ width: `${pct}%` }}></div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* Recent Incidents Table */}
      <div className="analytics-card full-width">
        <div className="card-header-clean">
          <div className="card-title-wrap">
            <TrendingUp size={18} />
            <h3>Recent IT Incidents</h3>
          </div>
          <span className="header-hint">Click on any incident row to review and execute triage</span>
        </div>

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
                <th>Reported By</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {recent_incidents.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center py-6">No incidents recorded yet.</td>
                </tr>
              ) : (
                recent_incidents.map((t) => (
                  <tr key={t.id} onClick={() => onSelectTicket(t)} className="clickable-row">
                    <td className="font-semibold text-primary">{t.ticket_number}</td>
                    <td className="ticket-table-title">{t.title}</td>
                    <td><span className="cat-chip">{t.category}</span></td>
                    <td><PriorityBadge priority={t.priority} /></td>
                    <td><StatusBadge status={t.status} /></td>
                    <td className="text-sm">{t.assigned_team}</td>
                    <td className="text-sm">{t.creator_name}</td>
                    <td>
                      <button className="btn-view-table">
                        Review <ArrowUpRight size={14} />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
