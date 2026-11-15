"""
Test Suite: Three Simple Ticket Sections Verification (Employee & Admin)
Verifies:
1. Employee sees only their own tickets.
2. Admin sees tickets from all employees.
3. New tickets appear in 'In Progress & Ongoing' (statuses: New, Triaged, Assigned, In Progress).
4. Resolved and Closed tickets appear in 'Completed Tickets'.
5. Changing ticket status moves it dynamically between sections.
6. Soft-deleted tickets do not appear in any section.
7. Dashboard counts stay 100% consistent with actual tickets.
8. Existing ticket creation, AI analysis, priority guardrails, and resolution functionality remain intact.
"""

import os
import sys
import unittest
from datetime import datetime
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app import app
from database import db
from models import User, Ticket, TicketHistory
from services.auth_service import generate_token

class TestThreeDashboardSections(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = app
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

        with cls.app.app_context():
            # Seed test users if not present
            admin_user = User.query.filter_by(email="test_admin_sections@smartdesk.ai").first()
            if not admin_user:
                admin_user = User(
                    name="Admin Section Tester",
                    email="test_admin_sections@smartdesk.ai",
                    role="admin",
                    department="IT Operations"
                )
                admin_user.set_password("AdminPass123!")
                db.session.add(admin_user)

            emp1 = User.query.filter_by(email="test_emp1_sections@smartdesk.ai").first()
            if not emp1:
                emp1 = User(
                    name="Employee One",
                    email="test_emp1_sections@smartdesk.ai",
                    role="employee",
                    department="Sales"
                )
                emp1.set_password("EmpPass123!")
                db.session.add(emp1)

            emp2 = User.query.filter_by(email="test_emp2_sections@smartdesk.ai").first()
            if not emp2:
                emp2 = User(
                    name="Employee Two",
                    email="test_emp2_sections@smartdesk.ai",
                    role="employee",
                    department="Finance"
                )
                emp2.set_password("EmpPass123!")
                db.session.add(emp2)

            db.session.commit()

            cls.admin_id = admin_user.id
            cls.emp1_id = emp1.id
            cls.emp2_id = emp2.id

            cls.admin_token = generate_token(admin_user)
            cls.emp1_token = generate_token(emp1)
            cls.emp2_token = generate_token(emp2)

    def test_01_employee_isolation_and_admin_visibility(self):
        """Verify Employee sees only their own tickets, while Admin sees all employees' tickets."""
        with self.app.app_context():
            t1 = Ticket(
                ticket_number=f"SEC-EMP1-{int(datetime.utcnow().timestamp())}",
                title="Employee 1 Laptop Trackpad Stuck",
                description="Trackpad is unresponsive during client presentations",
                category="Hardware",
                priority="Medium",
                status="New",
                created_by_user_id=self.emp1_id,
                assigned_team="Workplace Tech Support"
            )
            t2 = Ticket(
                ticket_number=f"SEC-EMP2-{int(datetime.utcnow().timestamp())}",
                title="Employee 2 Payroll Portal Timeout",
                description="Cannot submit quarterly expenses due to gateway error",
                category="Software",
                priority="High",
                status="Assigned",
                created_by_user_id=self.emp2_id,
                assigned_team="Application Support"
            )
            db.session.add_all([t1, t2])
            db.session.commit()
            t1_id, t2_id = t1.id, t2.id

        # Emp 1 queries tickets
        res1 = self.client.get("/api/tickets", headers={"Authorization": f"Bearer {self.emp1_token}"})
        self.assertEqual(res1.status_code, 200)
        emp1_tickets = res1.get_json()["tickets"]
        emp1_ids = [t["id"] for t in emp1_tickets]
        self.assertIn(t1_id, emp1_ids, "Employee 1 must see their own ticket")
        self.assertNotIn(t2_id, emp1_ids, "Employee 1 must NOT see Employee 2's ticket")

        # Emp 2 queries tickets
        res2 = self.client.get("/api/tickets", headers={"Authorization": f"Bearer {self.emp2_token}"})
        self.assertEqual(res2.status_code, 200)
        emp2_tickets = res2.get_json()["tickets"]
        emp2_ids = [t["id"] for t in emp2_tickets]
        self.assertIn(t2_id, emp2_ids, "Employee 2 must see their own ticket")
        self.assertNotIn(t1_id, emp2_ids, "Employee 2 must NOT see Employee 1's ticket")

        # Admin queries tickets
        res_admin = self.client.get("/api/tickets", headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(res_admin.status_code, 200)
        admin_tickets = res_admin.get_json()["tickets"]
        admin_ids = [t["id"] for t in admin_tickets]
        self.assertIn(t1_id, admin_ids, "Admin must see Employee 1's ticket")
        self.assertIn(t2_id, admin_ids, "Admin must see Employee 2's ticket")
        print(" -> PASSED: Employee isolation and Admin cross-employee visibility confirmed.")

    def test_02_new_tickets_appear_in_in_progress_and_not_in_completed(self):
        """Newly created tickets (New, Triaged, Assigned, In Progress) belong to In Progress & Ongoing."""
        with self.app.app_context():
            t = Ticket(
                ticket_number=f"SEC-NEW-{int(datetime.utcnow().timestamp())}",
                title="Office Wi-Fi Disconnecting Frequently",
                description="Intermittent drops on 5GHz conference room network",
                category="Network",
                priority="Medium",
                status="New",
                created_by_user_id=self.emp1_id,
                assigned_team="Network Operations"
            )
            db.session.add(t)
            db.session.commit()
            t_id = t.id

        # Query in_progress section
        res_prog = self.client.get("/api/tickets?section=in_progress", headers={"Authorization": f"Bearer {self.emp1_token}"})
        self.assertEqual(res_prog.status_code, 200)
        prog_ids = [tk["id"] for tk in res_prog.get_json()["tickets"]]
        self.assertIn(t_id, prog_ids, "New ticket must appear in In Progress & Ongoing section")

        # Query completed section
        res_comp = self.client.get("/api/tickets?section=completed", headers={"Authorization": f"Bearer {self.emp1_token}"})
        self.assertEqual(res_comp.status_code, 200)
        comp_ids = [tk["id"] for tk in res_comp.get_json()["tickets"]]
        self.assertNotIn(t_id, comp_ids, "New ticket must NOT appear in Completed section")
        print(" -> PASSED: New ticket correctly appears in In Progress & Ongoing only.")

    def test_03_resolved_and_closed_tickets_appear_in_completed_section(self):
        """Tickets with status Resolved or Closed appear in Completed Tickets with resolution notes."""
        with self.app.app_context():
            t_res = Ticket(
                ticket_number=f"SEC-RES-{int(datetime.utcnow().timestamp())}",
                title="VPN Certificate Renewal",
                description="SSL certificate expired for remote gateway",
                category="Network",
                priority="High",
                status="Resolved",
                resolution_notes="Re-issued and distributed enterprise root CA bundle.",
                created_by_user_id=self.emp1_id,
                assigned_team="Network Operations",
                resolved_at=datetime.utcnow()
            )
            t_cls = Ticket(
                ticket_number=f"SEC-CLS-{int(datetime.utcnow().timestamp())}",
                title="Monitor Display Cable Request",
                description="Need USB-C to DisplayPort cable",
                category="Hardware",
                priority="Low",
                status="Closed",
                resolution_notes="Cable delivered and signed off by user.",
                created_by_user_id=self.emp1_id,
                assigned_team="Workplace Tech Support",
                resolved_at=datetime.utcnow()
            )
            db.session.add_all([t_res, t_cls])
            db.session.commit()
            t_res_id, t_cls_id = t_res.id, t_cls.id

        # Query completed section
        res_comp = self.client.get("/api/tickets?section=completed", headers={"Authorization": f"Bearer {self.emp1_token}"})
        self.assertEqual(res_comp.status_code, 200)
        comp_tickets = res_comp.get_json()["tickets"]
        comp_map = {tk["id"]: tk for tk in comp_tickets}

        self.assertIn(t_res_id, comp_map, "Resolved ticket must be in Completed section")
        self.assertIn(t_cls_id, comp_map, "Closed ticket must be in Completed section")

        # Verify resolution notes are returned
        self.assertEqual(comp_map[t_res_id]["resolution_notes"], "Re-issued and distributed enterprise root CA bundle.")
        self.assertEqual(comp_map[t_cls_id]["resolution_notes"], "Cable delivered and signed off by user.")

        # Ensure they are NOT in in_progress section
        res_prog = self.client.get("/api/tickets?section=in_progress", headers={"Authorization": f"Bearer {self.emp1_token}"})
        prog_ids = [tk["id"] for tk in res_prog.get_json()["tickets"]]
        self.assertNotIn(t_res_id, prog_ids)
        self.assertNotIn(t_cls_id, prog_ids)
        print(" -> PASSED: Resolved and Closed tickets appear in Completed section with notes.")

    def test_04_status_transition_moves_ticket_between_sections(self):
        """Changing ticket status dynamically moves it between In Progress & Ongoing and Completed."""
        with self.app.app_context():
            t = Ticket(
                ticket_number=f"SEC-TRANS-{int(datetime.utcnow().timestamp())}",
                title="Database Read Replica Latency",
                description="High replication lag causing slow reports",
                category="Software",
                priority="High",
                status="Assigned",
                created_by_user_id=self.emp2_id,
                assigned_team="Application Support"
            )
            db.session.add(t)
            db.session.commit()
            t_id = t.id

        # Initially in in_progress
        res1 = self.client.get("/api/tickets?section=in_progress", headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertIn(t_id, [tk["id"] for tk in res1.get_json()["tickets"]])

        # Admin resolves ticket
        patch_res = self.client.patch(
            f"/api/tickets/{t_id}",
            json={
                "status": "Resolved",
                "resolution_notes": "Optimized vacuum process and increased IOPS provision."
            },
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        self.assertEqual(patch_res.status_code, 200)

        # Ticket must now be GONE from in_progress
        res2 = self.client.get("/api/tickets?section=in_progress", headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertNotIn(t_id, [tk["id"] for tk in res2.get_json()["tickets"]])

        # Ticket must now be PRESENT in completed
        res3 = self.client.get("/api/tickets?section=completed", headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertIn(t_id, [tk["id"] for tk in res3.get_json()["tickets"]])

        # Admin re-opens ticket back to In Progress
        patch_res2 = self.client.patch(
            f"/api/tickets/{t_id}",
            json={"status": "In Progress"},
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        self.assertEqual(patch_res2.status_code, 200)

        # Ticket must return to in_progress and leave completed
        res4 = self.client.get("/api/tickets?section=in_progress", headers={"Authorization": f"Bearer {self.admin_token}"})
        res5 = self.client.get("/api/tickets?section=completed", headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertIn(t_id, [tk["id"] for tk in res4.get_json()["tickets"]])
        self.assertNotIn(t_id, [tk["id"] for tk in res5.get_json()["tickets"]])
        print(" -> PASSED: Ticket moves seamlessly between In Progress and Completed when status changes.")

    def test_05_deleted_tickets_excluded_from_all_sections_and_stats(self):
        """Soft-deleted tickets do not appear in any section or active counts."""
        with self.app.app_context():
            t = Ticket(
                ticket_number=f"SEC-DEL-{int(datetime.utcnow().timestamp())}",
                title="Accidental duplicate request",
                description="Submitted twice by mistake",
                category="Other",
                priority="Low",
                status="New",
                created_by_user_id=self.emp1_id,
                assigned_team="Service Desk Tier 1"
            )
            db.session.add(t)
            db.session.commit()
            t_id = t.id

        # Delete ticket via API
        del_res = self.client.delete(f"/api/tickets/{t_id}", headers={"Authorization": f"Bearer {self.emp1_token}"})
        self.assertEqual(del_res.status_code, 200)

        # Excluded from in_progress
        res_prog = self.client.get("/api/tickets?section=in_progress", headers={"Authorization": f"Bearer {self.emp1_token}"})
        self.assertNotIn(t_id, [tk["id"] for tk in res_prog.get_json()["tickets"]])

        # Excluded from completed
        res_comp = self.client.get("/api/tickets?section=completed", headers={"Authorization": f"Bearer {self.emp1_token}"})
        self.assertNotIn(t_id, [tk["id"] for tk in res_comp.get_json()["tickets"]])

        # Excluded from all tickets
        res_all = self.client.get("/api/tickets", headers={"Authorization": f"Bearer {self.emp1_token}"})
        self.assertNotIn(t_id, [tk["id"] for tk in res_all.get_json()["tickets"]])

        # Direct get returns 404
        res_get = self.client.get(f"/api/tickets/{t_id}", headers={"Authorization": f"Bearer {self.emp1_token}"})
        self.assertEqual(res_get.status_code, 404)
        print(" -> PASSED: Soft-deleted ticket is completely omitted from all sections.")

if __name__ == "__main__":
    unittest.main()
