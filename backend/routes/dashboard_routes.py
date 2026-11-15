from flask import Blueprint, jsonify
from sqlalchemy import func
from models import Ticket
from services.auth_service import token_required

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard/stats", methods=["GET"])
@token_required()
def get_dashboard_stats(current_user):
    # Exclude soft-deleted tickets from all metrics
    active_query = Ticket.query.filter_by(is_deleted=False)
    
    # Non-admins only see metrics for their own tickets
    user_filter_id = None
    if current_user.role != "admin":
        user_filter_id = current_user.id
        active_query = active_query.filter_by(created_by_user_id=current_user.id)
        
    total_tickets = active_query.count()
    open_tickets = active_query.filter(Ticket.status.in_(["New", "Triaged", "Assigned", "In Progress"])).count()
    resolved_tickets = active_query.filter(Ticket.status.in_(["Resolved", "Closed"])).count()
    critical_tickets = active_query.filter_by(priority="Critical").count()
    high_priority_tickets = active_query.filter_by(priority="High").count()
    
    # Category breakdown
    category_counts = db_session_group_counts(Ticket.category, user_id=user_filter_id)
    
    # Priority breakdown
    priority_counts = db_session_group_counts(Ticket.priority, user_id=user_filter_id)

    # Status breakdown
    status_counts = db_session_group_counts(Ticket.status, user_id=user_filter_id)

    # Support team workload
    team_counts = db_session_group_counts(Ticket.assigned_team, user_id=user_filter_id)

    # Recent incidents (excluding soft-deleted)
    recent_tickets = (
        active_query.order_by(Ticket.created_at.desc())
        .limit(6)
        .all()
    )

    return jsonify({
        "metrics": {
            "total_tickets": total_tickets,
            "open_tickets": open_tickets,
            "resolved_tickets": resolved_tickets,
            "critical_tickets": critical_tickets,
            "high_priority_tickets": high_priority_tickets,
            "critical_and_high": critical_tickets + high_priority_tickets,
        },
        "by_category": category_counts,
        "by_priority": priority_counts,
        "by_status": status_counts,
        "team_workload": team_counts,
        "recent_incidents": [t.to_dict() for t in recent_tickets]
    }), 200


def db_session_group_counts(column, user_id=None):
    from database import db
    query = (
        db.session.query(column, func.count(Ticket.id))
        .filter(Ticket.is_deleted == False)
    )
    if user_id is not None:
        query = query.filter(Ticket.created_by_user_id == user_id)
    results = query.group_by(column).all()
    return {str(val or "Unassigned"): count for val, count in results}
