from flask import Blueprint, request, jsonify
from models import Ticket
from services.auth_service import token_required
from services.ticket_service import create_ticket, update_ticket, delete_ticket

ticket_bp = Blueprint("tickets", __name__)

@ticket_bp.route("/tickets", methods=["POST"])
@token_required()
def handle_create_ticket(current_user):
    from datetime import datetime, timedelta
    data = request.get_json() or {}
    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    impact = data.get("impact", "Medium")
    urgency = data.get("urgency", "Medium")
    pre_analysis = data.get("pre_analysis")

    if not title or not description:
        return jsonify({"error": "Title and description are required"}), 400

    # Enterprise Duplicate Prevention: check if identical ticket was submitted within last 60s
    recent_cutoff = datetime.utcnow() - timedelta(seconds=60)
    existing_duplicate = Ticket.query.filter(
        Ticket.created_by_user_id == current_user.id,
        Ticket.title == title,
        Ticket.description == description,
        Ticket.created_at >= recent_cutoff
    ).order_by(Ticket.created_at.desc()).first()

    if existing_duplicate:
        return jsonify({
            "message": "Duplicate ticket prevented: Identical incident already registered.",
            "ticket": existing_duplicate.to_dict(include_history=True),
            "duplicate_prevented": True
        }), 200

    try:
        ticket = create_ticket(
            title=title,
            description=description,
            impact=impact,
            urgency=urgency,
            created_by_user_id=current_user.id,
            pre_analysis=pre_analysis
        )
        return jsonify({
            "message": "Ticket created successfully",
            "ticket": ticket.to_dict(include_history=True),
            "duplicate_prevented": False
        }), 201
    except Exception as e:
        return jsonify({"error": f"Failed to create ticket: {str(e)}"}), 500


@ticket_bp.route("/tickets", methods=["GET"])
@token_required()
def handle_list_tickets(current_user):
    # Exclude soft-deleted tickets
    query = Ticket.query.filter_by(is_deleted=False)

    # Role-based restriction: employees can only view tickets they created
    if current_user.role != "admin":
        query = query.filter_by(created_by_user_id=current_user.id)

    # Support section-based filtering: in_progress vs completed
    section_filter = request.args.get("section")
    if section_filter == "in_progress":
        query = query.filter(Ticket.status.in_(["New", "Triaged", "Assigned", "In Progress"]))
    elif section_filter == "completed":
        query = query.filter(Ticket.status.in_(["Resolved", "Closed"]))

    status_filter = request.args.get("status")
    if status_filter and status_filter != "All":
        statuses = [s.strip() for s in status_filter.split(",") if s.strip()]
        if len(statuses) == 1:
            query = query.filter_by(status=statuses[0])
        elif len(statuses) > 1:
            query = query.filter(Ticket.status.in_(statuses))

    category_filter = request.args.get("category")
    if category_filter and category_filter != "All":
        query = query.filter_by(category=category_filter)

    priority_filter = request.args.get("priority")
    if priority_filter and priority_filter != "All":
        query = query.filter_by(priority=priority_filter)

    team_filter = request.args.get("assigned_team")
    if team_filter:
        query = query.filter_by(assigned_team=team_filter)

    search = request.args.get("search", "").strip()
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Ticket.ticket_number.ilike(search_pattern)) |
            (Ticket.title.ilike(search_pattern)) |
            (Ticket.description.ilike(search_pattern))
        )

    tickets = query.order_by(Ticket.created_at.desc()).all()
    return jsonify({
        "total": len(tickets),
        "tickets": [t.to_dict(include_history=False) for t in tickets]
    }), 200


@ticket_bp.route("/tickets/<int:ticket_id>", methods=["GET"])
@token_required()
def handle_get_ticket(current_user, ticket_id):
    from database import db
    ticket = db.session.get(Ticket, ticket_id)
    if not ticket or ticket.is_deleted:
        return jsonify({"error": "Ticket not found"}), 404

    # Enforce permission: employees can only see their own tickets
    if current_user.role != "admin" and ticket.created_by_user_id != current_user.id:
        return jsonify({"error": "Access denied"}), 403

    return jsonify({"ticket": ticket.to_dict(include_history=True)}), 200


@ticket_bp.route("/tickets/<int:ticket_id>", methods=["PATCH"])
@token_required()
def handle_update_ticket(current_user, ticket_id):
    data = request.get_json() or {}
    ticket, error = update_ticket(ticket_id, current_user, data)
    if error:
        status_code = 404 if "not found" in error.lower() else (403 if "unauthorized" in error.lower() else 400)
        return jsonify({"error": error}), status_code

    return jsonify({
        "message": "Ticket updated successfully",
        "ticket": ticket.to_dict(include_history=True)
    }), 200


@ticket_bp.route("/tickets/<int:ticket_id>", methods=["DELETE"])
@token_required()
def handle_delete_ticket(current_user, ticket_id):
    ticket, error, status_code = delete_ticket(ticket_id, current_user)
    if error:
        return jsonify({"error": error}), status_code

    return jsonify({
        "message": "Incident request deleted successfully",
        "ticket_id": ticket_id,
        "is_deleted": True
    }), 200
