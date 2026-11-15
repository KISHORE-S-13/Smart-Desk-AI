import React from "react";

const statusConfig = {
  New: { bg: "bg-blue-50 text-blue-700 border-blue-200", dot: "bg-blue-500" },
  Triaged: { bg: "bg-indigo-50 text-indigo-700 border-indigo-200", dot: "bg-indigo-500" },
  Assigned: { bg: "bg-purple-50 text-purple-700 border-purple-200", dot: "bg-purple-500" },
  "In Progress": { bg: "bg-amber-50 text-amber-700 border-amber-200", dot: "bg-amber-500" },
  Resolved: { bg: "bg-emerald-50 text-emerald-700 border-emerald-200", dot: "bg-emerald-500" },
  Closed: { bg: "bg-slate-100 text-slate-700 border-slate-200", dot: "bg-slate-500" },
};

export default function StatusBadge({ status }) {
  const current = statusConfig[status] || statusConfig.New;

  return (
    <span className={`status-badge status-${status?.toLowerCase().replace(/\s+/g, "-")}`}>
      <span className="status-dot"></span>
      {status || "New"}
    </span>
  );
}
