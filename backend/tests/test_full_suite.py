import os
import sys
import json
import unittest
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app import app
from database import db
from models import User, Ticket, KnowledgeArticle
from services.ai_service import rule_based_fallback, analyze_ticket_with_gemini

class TestSmartDeskFullSuite(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_01_employee_login(self):
        print("\n[Test 1] Testing Employee Login...")
        res = self.client.post("/api/login", json={
            "email": "employee@smartdesk.ai",
            "password": "Employee@123"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("token", data)
        self.assertEqual(data["user"]["role"], "employee")
        print(" -> PASSED: Employee login succeeded, JWT generated.")

    def test_02_admin_login(self):
        print("\n[Test 2] Testing Admin Login...")
        res = self.client.post("/api/login", json={
            "email": "admin@smartdesk.ai",
            "password": "Admin@123"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("token", data)
        self.assertEqual(data["user"]["role"], "admin")
        print(" -> PASSED: Admin login succeeded, JWT generated.")

    def test_03_and_04_gemini_classification_and_ticket_creation(self):
        print("\n[Test 3 & 4] Testing Gemini AI Classification & Ticket Creation...")
        login_res = self.client.post("/api/login", json={
            "email": "employee@smartdesk.ai",
            "password": "Employee@123"
        })
        token = login_res.get_json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Submit ticket
        ticket_payload = {
            "title": "Cannot connect to Cisco AnyConnect VPN from home",
            "description": "I get error 'Gateway not reachable' repeatedly while trying to connect to Chicago VPN gateway.",
            "impact": "High",
            "urgency": "High"
        }
        res = self.client.post("/api/tickets", json=ticket_payload, headers=headers)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertIn("ticket", data)
        ticket = data["ticket"]
        self.assertIn(ticket["category"], ["Network", "Other"])
        self.assertIn(ticket["priority"], ["Low", "Medium", "High", "Critical"])
        self.assertIn("recommended_steps", ticket)
        self.assertGreater(len(ticket["recommended_steps"]), 0)
        print(f" -> PASSED: Ticket created ID={ticket['id']}, Number={ticket['ticket_number']}, Category={ticket['category']}, Priority={ticket['priority']}, Source={ticket['analysis_source']}")

    def test_05_fallback_classification(self):
        print("\n[Test 5] Testing Deterministic Rule-Based Fallback...")
        fallback_res = rule_based_fallback(
            title="Outlook mailbox is full and cannot send emails",
            description="My quota exceeded 50GB and outgoing emails bounce with error 550.",
            impact="Medium",
            urgency="High"
        )
        self.assertEqual(fallback_res["category"], "Email")
        self.assertEqual(fallback_res["analysis_source"], "rule_based_fallback")
        self.assertIn(fallback_res["priority"], ["High", "Medium"])
        print(f" -> PASSED: Fallback classified category as {fallback_res['category']} with team {fallback_res['assigned_support_team']}.")

    def test_06_ticket_persistence(self):
        print("\n[Test 6] Testing Ticket Database Persistence...")
        login_res = self.client.post("/api/login", json={
            "email": "employee@smartdesk.ai",
            "password": "Employee@123"
        })
        token = login_res.get_json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        res = self.client.get("/api/tickets", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertGreater(data["total"], 0)
        print(f" -> PASSED: Tickets retrieved from database. Total tickets found for user: {data['total']}")

    def test_07_and_08_ticket_assignment_and_status_update(self):
        print("\n[Test 7 & 8] Testing Ticket Assignment & Status Updates (Admin)...")
        # Login as Admin
        admin_login = self.client.post("/api/login", json={
            "email": "admin@smartdesk.ai",
            "password": "Admin@123"
        })
        admin_token = admin_login.get_json()["token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Fetch first ticket
        list_res = self.client.get("/api/tickets", headers=admin_headers)
        tickets = list_res.get_json()["tickets"]
        self.assertGreater(len(tickets), 0)
        target_ticket = tickets[0]

        # Patch ticket: Assign team and change status to In Progress
        patch_res = self.client.patch(
            f"/api/tickets/{target_ticket['id']}",
            json={
                "status": "In Progress",
                "assigned_team": "Network Operations",
                "resolution_notes": "Engineer dispatched to check VPN gateway routing."
            },
            headers=admin_headers
        )
        self.assertEqual(patch_res.status_code, 200)
        updated = patch_res.get_json()["ticket"]
        self.assertEqual(updated["status"], "In Progress")
        self.assertEqual(updated["assigned_team"], "Network Operations")
        self.assertEqual(len(updated["history"]), 2) # CREATED + UPDATED
        print(f" -> PASSED: Ticket {updated['ticket_number']} updated to 'In Progress' and assigned to Network Operations.")

    def test_09_knowledge_assistant(self):
        print("\n[Test 9] Testing Generative AI Knowledge Assistant (RAG)...")
        login_res = self.client.post("/api/login", json={
            "email": "employee@smartdesk.ai",
            "password": "Employee@123"
        })
        token = login_res.get_json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        res = self.client.post("/api/ai/chat", json={
            "message": "How do I fix GlobalProtect VPN gateway unreachable error?"
        }, headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("answer", data)
        self.assertGreater(len(data["answer"]), 20)
        print(f" -> PASSED: Knowledge assistant responded using source: {data['source_type']}.")
        print("Sample answer snippet:", data["answer"][:150], "...")

    def test_10_dashboard_analytics(self):
        print("\n[Test 10] Testing Admin Dashboard Analytics...")
        admin_login = self.client.post("/api/login", json={
            "email": "admin@smartdesk.ai",
            "password": "Admin@123"
        })
        admin_token = admin_login.get_json()["token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        res = self.client.get("/api/dashboard/stats", headers=admin_headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("metrics", data)
        self.assertIn("by_category", data)
        self.assertIn("by_status", data)
        self.assertIn("team_workload", data)
        print(f" -> PASSED: Dashboard metrics received. Total={data['metrics']['total_tickets']}, Open={data['metrics']['open_tickets']}.")

if __name__ == "__main__":
    unittest.main()
