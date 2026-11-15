from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
import json

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(30), nullable=False, default="employee")  # "employee" | "admin"
    department = db.Column(db.String(100), default="General")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tickets_created = db.relationship("Ticket", backref="creator", foreign_keys="Ticket.created_by_user_id", lazy=True)
    tickets_assigned = db.relationship("Ticket", backref="assignee", foreign_keys="Ticket.assigned_to_user_id", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "department": self.department,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Ticket(db.Model):
    __tablename__ = "tickets"

    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    ticket_type = db.Column(db.String(50), default="Incident")  # "Incident" | "Service Request"
    category = db.Column(db.String(50), default="Other")       # Network, Hardware, Software, Email, Access Management, Other
    impact = db.Column(db.String(20), default="Medium")        # Low, Medium, High
    urgency = db.Column(db.String(20), default="Medium")       # Low, Medium, High
    priority = db.Column(db.String(20), default="Medium")      # Low, Medium, High, Critical
    priority_reason = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), default="New", index=True) # New, Triaged, Assigned, In Progress, Resolved, Closed
    assigned_team = db.Column(db.String(100), default="Service Desk")
    assigned_to_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    
    # Gemini AI Analysis Fields
    analysis_source = db.Column(db.String(40), default="gemini") # "gemini" | "rule_based_fallback"
    recommended_steps = db.Column(db.Text, nullable=True)        # JSON string of steps
    suggested_response = db.Column(db.Text, nullable=True)
    resolution_notes = db.Column(db.Text, nullable=True)

    # Soft deletion flag
    is_deleted = db.Column(db.Boolean, default=False, nullable=False, index=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

    history = db.relationship("TicketHistory", backref="ticket", cascade="all, delete-orphan", lazy=True, order_by="TicketHistory.created_at.desc()")

    def to_dict(self, include_history=False):
        steps = []
        if self.recommended_steps:
            try:
                steps = json.loads(self.recommended_steps)
            except Exception:
                steps = [self.recommended_steps]

        data = {
            "id": self.id,
            "ticket_number": self.ticket_number,
            "title": self.title,
            "description": self.description,
            "ticket_type": self.ticket_type,
            "category": self.category,
            "impact": self.impact,
            "urgency": self.urgency,
            "priority": self.priority,
            "priority_reason": self.priority_reason,
            "status": self.status,
            "assigned_team": self.assigned_team,
            "assigned_to_user_id": self.assigned_to_user_id,
            "created_by_user_id": self.created_by_user_id,
            "creator_name": self.creator.name if self.creator else "Unknown",
            "creator_email": self.creator.email if self.creator else None,
            "analysis_source": self.analysis_source,
            "is_deleted": bool(self.is_deleted),
            "recommended_steps": steps,
            "suggested_response": self.suggested_response,
            "resolution_notes": self.resolution_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }
        if include_history:
            data["history"] = [h.to_dict() for h in self.history]
        return data


class TicketHistory(db.Model):
    __tablename__ = "ticket_history"

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(50), nullable=False) # e.g. CREATED, AI_ANALYSIS, STATUS_CHANGED, ASSIGNED, RESOLVED, NOTE_ADDED
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", foreign_keys=[user_id], lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "ticket_id": self.ticket_id,
            "action": self.action,
            "details": self.details,
            "user_name": self.user.name if self.user else "System",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class KnowledgeArticle(db.Model):
    __tablename__ = "knowledge_articles"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(50), nullable=False) # VPN, Wi-Fi, Password Reset, Email, Software Installation, General
    content = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(255), default="")
    source = db.Column(db.String(50), default="system_seed") # "system_seed" | "uploaded_pdf"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "content": self.content,
            "tags": [t.strip() for t in self.tags.split(",") if t.strip()] if self.tags else [],
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
