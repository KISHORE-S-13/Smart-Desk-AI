import os
import sys
import json
import unittest
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app import app
from database import db
from models import User, Ticket, TicketHistory

class TestDeleteTicketFeature(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Login as employee
        res_emp = self.client.post("/api/login", json={
            "email": "employee@smartdesk.ai",
            "password": "Employee@123"
        })
        self.emp_token = res_emp.get_json()["token"]
        self.emp_user_id = res_emp.get_json()["user"]["id"]

        # Login as admin
        res_adm = self.client.post("/api/login", json={
            "email": "admin@smartdesk.ai",
            "password": "Admin@123"
        })
        self.adm_token = res_adm.get_json()["token"]
        self.adm_user_id = res_adm.get_json()["user"]["id"]

        # Ensure a second employee exists for cross-user permission testing
        self.emp2 = User.query.filter_by(email="employee2@smartdesk.ai").first()
        if not self.emp2:
            self.emp2 = User(
                name="David Miller",
                email="employee2@smartdesk.ai",
                role="employee",
                department="Marketing"
            )
            self.emp2.set_password("Emp2@123")
            db.session.add(self.emp2)
            db.session.commit()

        res_emp2 = self.client.post("/api/login", json={
            "email": "employee2@smartdesk.ai",
            "password": "Emp2@123"
        })
        self.emp2_token = res_emp2.get_json()["token"]
        self.emp2_user_id = res_emp2.get_json()["user"]["id"]

    def tearDown(self):
        self.app_context.pop()

    def test_01_employee_can_delete_own_open_ticket(self):
        """Employee can successfully soft-delete their own open incident request."""
        # Create ticket as employee 1
        res = self.client.post("/api/tickets", json={
            "title": "Mouse cursor lagging after update",
            "description": "Optical mouse cursor skips frames when plugged into docking station.",
            "impact": "Low",
            "urgency": "Low"
        }, headers={"Authorization": f"Bearer {self.emp_token}"})
        self.assertEqual(res.status_code, 201)
        ticket_id = res.get_json()["ticket"]["id"]

        # Employee 1 deletes own open ticket
        del_res = self.client.delete(f"/api/tickets/{ticket_id}", headers={
            "Authorization": f"Bearer {self.emp_token}"
        })
        self.assertEqual(del_res.status_code, 200)
        del_data = del_res.get_json()
        self.assertTrue(del_data.get("is_deleted"))

        # Verify soft-deletion in DB: ticket is marked is_deleted=True
        t = db.session.get(Ticket, ticket_id)
        self.assertIsNotNone(t)
        self.assertTrue(t.is_deleted)

        # Verify audit history logged
        history = TicketHistory.query.filter_by(ticket_id=ticket_id, action="DELETED").first()
        self.assertIsNotNone(history)
        self.assertIn("soft-deleted by Alex Rivera", history.details)

    def test_02_employee_cannot_delete_other_employees_ticket(self):
        """Employee cannot delete an incident request belonging to another employee."""
        # Create ticket as Employee 2
        res = self.client.post("/api/tickets", json={
            "title": "Marketing shared drive read-only error",
            "description": "Cannot save campaign assets to shared network storage folder.",
            "impact": "Medium",
            "urgency": "Medium"
        }, headers={"Authorization": f"Bearer {self.emp2_token}"})
        self.assertEqual(res.status_code, 201)
        ticket_id = res.get_json()["ticket"]["id"]

        # Employee 1 attempts to delete Employee 2's ticket
        del_res = self.client.delete(f"/api/tickets/{ticket_id}", headers={
            "Authorization": f"Bearer {self.emp_token}"
        })
        self.assertEqual(del_res.status_code, 403)
        self.assertIn("own", del_res.get_json()["error"].lower())

        # Verify ticket was NOT soft-deleted
        t = db.session.get(Ticket, ticket_id)
        self.assertFalse(t.is_deleted)

    def test_03_employee_cannot_delete_resolved_or_closed_ticket(self):
        """Employee cannot delete an incident request that is Resolved or Closed."""
        # Create ticket as Employee 1
        res = self.client.post("/api/tickets", json={
            "title": "Teams camera glitch on video calls",
            "description": "External USB camera video freezes after 5 minutes.",
            "impact": "Medium",
            "urgency": "Low"
        }, headers={"Authorization": f"Bearer {self.emp_token}"})
        self.assertEqual(res.status_code, 201)
        ticket_id = res.get_json()["ticket"]["id"]

        # Admin resolves the ticket
        up_res = self.client.patch(f"/api/tickets/{ticket_id}", json={
            "status": "Resolved",
            "resolution_notes": "Updated USB composite device drivers."
        }, headers={"Authorization": f"Bearer {self.adm_token}"})
        self.assertEqual(up_res.status_code, 200)

        # Employee 1 attempts to delete the now Resolved ticket
        del_res = self.client.delete(f"/api/tickets/{ticket_id}", headers={
            "Authorization": f"Bearer {self.emp_token}"
        })
        self.assertEqual(del_res.status_code, 403)
        self.assertIn("resolved or closed", del_res.get_json()["error"].lower())

        # Verify ticket was NOT soft-deleted
        t = db.session.get(Ticket, ticket_id)
        self.assertFalse(t.is_deleted)

    def test_04_admin_can_delete_any_ticket_regardless_of_status(self):
        """Admin can delete any employee's incident request, including Resolved tickets."""
        # Create ticket as Employee 2
        res = self.client.post("/api/tickets", json={
            "title": "Need second monitor HDMI adapter",
            "description": "Requesting an HDMI to USB-C dongle for workstation.",
            "impact": "Low",
            "urgency": "Low"
        }, headers={"Authorization": f"Bearer {self.emp2_token}"})
        self.assertEqual(res.status_code, 201)
        ticket_id = res.get_json()["ticket"]["id"]

        # Admin closes it first
        self.client.patch(f"/api/tickets/{ticket_id}", json={
            "status": "Closed"
        }, headers={"Authorization": f"Bearer {self.adm_token}"})

        # Admin deletes Employee 2's Closed ticket
        del_res = self.client.delete(f"/api/tickets/{ticket_id}", headers={
            "Authorization": f"Bearer {self.adm_token}"
        })
        self.assertEqual(del_res.status_code, 200)
        self.assertTrue(del_res.get_json().get("is_deleted"))

        # Verify soft-deletion
        t = db.session.get(Ticket, ticket_id)
        self.assertTrue(t.is_deleted)

        # Verify audit history record
        history = TicketHistory.query.filter_by(ticket_id=ticket_id, action="DELETED").first()
        self.assertIsNotNone(history)
        self.assertIn("Sarah Chen", history.details)

    def test_05_deleted_tickets_disappear_from_lists_and_stats(self):
        """Deleted tickets are omitted from GET /api/tickets, GET /api/tickets/<id>, PATCH and dashboard stats."""
        # Check initial stats
        stats_before = self.client.get("/api/dashboard/stats", headers={
            "Authorization": f"Bearer {self.adm_token}"
        }).get_json()["metrics"]["total_tickets"]

        # Create ticket
        res = self.client.post("/api/tickets", json={
            "title": "Temporary test ticket for exclusion check",
            "description": "This ticket will be deleted to test exclusion filters.",
            "impact": "Low",
            "urgency": "Low"
        }, headers={"Authorization": f"Bearer {self.emp_token}"})
        ticket_id = res.get_json()["ticket"]["id"]

        # Stats should increment by 1
        stats_mid = self.client.get("/api/dashboard/stats", headers={
            "Authorization": f"Bearer {self.adm_token}"
        }).get_json()["metrics"]["total_tickets"]
        self.assertEqual(stats_mid, stats_before + 1)

        # Delete the ticket
        self.client.delete(f"/api/tickets/{ticket_id}", headers={
            "Authorization": f"Bearer {self.emp_token}"
        })

        # 1. Ticket list excludes it
        list_res = self.client.get("/api/tickets", headers={
            "Authorization": f"Bearer {self.emp_token}"
        })
        listed_ids = [t["id"] for t in list_res.get_json()["tickets"]]
        self.assertNotIn(ticket_id, listed_ids)

        # 2. Direct GET returns 404
        get_res = self.client.get(f"/api/tickets/{ticket_id}", headers={
            "Authorization": f"Bearer {self.emp_token}"
        })
        self.assertEqual(get_res.status_code, 404)

        # 3. Direct PATCH returns 404
        patch_res = self.client.patch(f"/api/tickets/{ticket_id}", json={
            "status": "In Progress"
        }, headers={"Authorization": f"Bearer {self.adm_token}"})
        self.assertEqual(patch_res.status_code, 404)

        # 4. Repeated DELETE returns 404
        re_del = self.client.delete(f"/api/tickets/{ticket_id}", headers={
            "Authorization": f"Bearer {self.emp_token}"
        })
        self.assertEqual(re_del.status_code, 404)

        # 5. Dashboard stats decrement back to before
        stats_after = self.client.get("/api/dashboard/stats", headers={
            "Authorization": f"Bearer {self.adm_token}"
        }).get_json()["metrics"]["total_tickets"]
        self.assertEqual(stats_after, stats_before)

if __name__ == "__main__":
    unittest.main()