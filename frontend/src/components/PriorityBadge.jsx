import React from "react";

export default function PriorityBadge({ priority }) {
  const p = priority?.toLowerCase() || "medium";
  return (
    <span className={`priority-badge priority-${p}`}>
      {priority || "Medium"}
    </span>
  );
}
