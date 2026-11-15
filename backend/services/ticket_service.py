from datetime import datetime
import json
from database import db
from models import Ticket, TicketHistory, User
from services.ai_service import analyze_ticket_with_gemini

VALID_STATUSES = ["New", "Triaged", "Assigned", "In Progress", "Resolved", "Closed"]

def generate_ticket_number():
    """Generates sequential, enterprise-formatted ticket IDs like SMART-1001."""
    last_ticket = Ticket.query.order_by(Ticket.id.desc()).first()
    if last_ticket:
        next_num = last_ticket.id + 1001
    else:
        next_num = 1001
    return f"SMART-{next_num}"

def create_ticket(title, description, impact, urgency, created_by_user_id, pre_analysis=None):
    """
    Creates a new ticket, executes AI analysis, auto-assigns team, and logs audit history.
    Enforces ITIL priority guardrails on stored ticket.
    """
    from services.ai_service import apply_itil_priority_guardrail

    if pre_analysis:
        analysis = pre_analysis
    else:
        analysis = analyze_ticket_with_gemini(title, description, impact, urgency)

    # Re-verify and enforce ITIL guardrail on final ticket creation
    guarded_priority, guarded_reason = apply_itil_priority_guardrail(
        title=title,
        description=description,
        impact=impact,
        urgency=urgency,
        candidate_priority=analysis.get("priority", "Medium"),
        reason=analysis.get("reason_for_priority", "")
    )
    analysis["priority"] = guarded_priority
    analysis["reason_for_priority"] = guarded_reason

    ticket_number = generate_ticket_number()
    rec_steps_json = json.dumps(analysis.get("recommended_troubleshooting_steps", []))

    ticket = Ticket(
        ticket_number=ticket_number,
        title=title.strip(),
        description=description.strip(),
        ticket_type=analysis.get("ticket_type", "Incident"),
        category=analysis.get("category", "Other"),
        impact=impact or "Medium",
        urgency=urgency or "Medium",
        priority=analysis.get("priority", "Medium"),
        priority_reason=analysis.get("reason_for_priority", ""),
        status="Triaged" if analysis.get("analysis_source") == "gemini" else "New",
        assigned_team=analysis.get("assigned_support_team", "Service Desk Tier 1"),
        created_by_user_id=created_by_user_id,
        analysis_source=analysis.get("analysis_source", "gemini"),
        recommended_steps=rec_steps_json,
        suggested_response=analysis.get("suggested_response_to_employee", ""),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.session.add(ticket)
    db.session.flush() # Populate ticket.id

    # Create audit history record
    history = TicketHistory(
        ticket_id=ticket.id,
        user_id=created_by_user_id,
        action="CREATED",
        details=f"Ticket created. AI Classification: {ticket.category} | Priority: {ticket.priority} | Team: {ticket.assigned_team} (Source: {ticket.analysis_source})"
    )
    db.session.add(history)
    db.session.commit()

    return ticket

def update_ticket(ticket_id, user, data):
    """
    Updates ticket status, team assignment, or resolution notes with audit history.
    Enforces role permissions and human-in-the-loop review.
    """
    ticket = db.session.get(Ticket, ticket_id)
    if not ticket or ticket.is_deleted:
        return None, "Ticket not found"

    # Permission check: employees can only cancel/close their own tickets or view
    if user.role != "admin" and ticket.created_by_user_id != user.id:
        return None, "Unauthorized access to this ticket"

    changes = []

    if "status" in data:
        new_status = data["status"]
        if new_status not in VALID_STATUSES:
            return None, f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}"
        if new_status != ticket.status:
            old_status = ticket.status
            ticket.status = new_status
            if new_status in ["Resolved", "Closed"] and not ticket.resolved_at:
                ticket.resolved_at = datetime.utcnow()
            changes.append(f"Status changed from '{old_status}' to '{new_status}'")

    if user.role == "admin":
        if "assigned_team" in data and data["assigned_team"] != ticket.assigned_team:
            old_team = ticket.assigned_team
            ticket.assigned_team = data["assigned_team"]
            changes.append(f"Assigned team updated from '{old_team}' to '{ticket.assigned_team}'")

        if "assigned_to_user_id" in data:
            ticket.assigned_to_user_id = data["assigned_to_user_id"]
            changes.append(f"Assignee updated to User ID #{ticket.assigned_to_user_id}")

        if "priority" in data and data["priority"] in ["Low", "Medium", "High", "Critical"]:
            if data["priority"] != ticket.priority:
                old_p = ticket.priority
                ticket.priority = data["priority"]
                changes.append(f"Priority modified from '{old_p}' to '{ticket.priority}' (Admin Override)")

        if "resolution_notes" in data:
            ticket.resolution_notes = data["resolution_notes"]
            changes.append("Resolution notes updated by admin")

    ticket.updated_at = datetime.utcnow()

    if changes:
        history = TicketHistory(
            ticket_id=ticket.id,
            user_id=user.id,
            action="UPDATED",
            details="; ".join(changes)
        )
        db.session.add(history)

    db.session.commit()
    return ticket, None

def delete_ticket(ticket_id, user):
    """
    Soft-deletes an incident request.
    Enforces:
    1. Employees can only delete their own incident requests.
    2. Employees cannot delete resolved or closed requests.
    3. Admin can delete any request regardless of status.
    4. Sets is_deleted=True, logs audit history, and preserves records.
    """
    ticket = db.session.get(Ticket, ticket_id)
    if not ticket or ticket.is_deleted:
        return None, "Ticket not found", 404

    # Role-based authorization
    if user.role != "admin":
        # Check ownership
        if ticket.created_by_user_id != user.id:
            return None, "Access denied: You can only delete your own incident requests.", 403

        # Check status: cannot delete resolved or closed requests
        if ticket.status in ["Resolved", "Closed"]:
            return None, "Cannot delete ticket: Resolved or closed incident requests cannot be deleted.", 403

    # Soft delete
    ticket.is_deleted = True
    ticket.updated_at = datetime.utcnow()

    # Log audit history
    history = TicketHistory(
        ticket_id=ticket.id,
        user_id=user.id,
        action="DELETED",
        details=f"Ticket soft-deleted by {user.name} ({user.role.capitalize()})."
    )
    db.session.add(history)
    db.session.commit()

    return ticket, None, 200
