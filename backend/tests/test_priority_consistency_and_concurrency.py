import urllib.request
import json
import time

def run_regression_tests():
    base_url = "http://127.0.0.1:5000/api"

    print("\n=======================================================")
    print("STEP 1: Authenticate as Employee")
    print("=======================================================")
    login_data = json.dumps({"email": "employee@smartdesk.ai", "password": "Employee@123"}).encode()
    req = urllib.request.Request(f"{base_url}/login", data=login_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        token = json.loads(r.read().decode())["token"]
        print("Employee JWT token acquired.")

    print("\n=======================================================")
    print("STEP 2: Test Individual Client Meeting (Medium/Medium) -> High, NEVER Critical")
    print("=======================================================")
    # 2a. Preview endpoint
    meeting_payload = {
        "title": "My office VPN is not connecting",
        "description": "I have an important client meeting in 30 minutes and need to connect to present slides.",
        "impact": "Medium",
        "urgency": "Medium"
    }
    req_preview = urllib.request.Request(f"{base_url}/ai/analyze", data=json.dumps(meeting_payload).encode(), headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    })
    with urllib.request.urlopen(req_preview) as r:
        preview_res = json.loads(r.read().decode())["analysis"]
        print(f"Preview Analysis Result:")
        print(f"  Source: {preview_res['analysis_source']}")
        print(f"  Category: {preview_res['category']}")
        print(f"  Priority: {preview_res['priority']}")
        print(f"  Reason: {preview_res['reason_for_priority']}")
        assert preview_res["priority"] == "High", f"FAILED: Expected High for client meeting, got {preview_res['priority']}"
        assert preview_res["priority"] != "Critical", "FAILED: Individual client meeting must NEVER be Critical!"
        print("  >> PREVIEW PASSED: Priority is High (never Critical).")

    # 2b. Final Ticket Creation
    req_create = urllib.request.Request(f"{base_url}/tickets", data=json.dumps(meeting_payload).encode(), headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    })
    with urllib.request.urlopen(req_create) as r:
        ticket_res = json.loads(r.read().decode())["ticket"]
        print(f"\nStored Ticket Creation Result:")
        print(f"  Ticket Number: {ticket_res['ticket_number']}")
        print(f"  Category: {ticket_res['category']}")
        print(f"  Impact: {ticket_res['impact']} | Urgency: {ticket_res['urgency']}")
        print(f"  Stored Priority: {ticket_res['priority']}")
        print(f"  Stored Reason: {ticket_res['priority_reason']}")
        assert ticket_res["priority"] == "High", f"FAILED: Stored priority must be High, got {ticket_res['priority']}"
        assert ticket_res["priority"] != "Critical", "FAILED: Stored ticket must NEVER be Critical for single-user meeting!"
        print("  >> TICKET CREATION PASSED: Stored priority is High.")

    print("\n=======================================================")
    print("STEP 3: Test Enterprise-Wide Outage (High/High) -> Critical")
    print("=======================================================")
    enterprise_payload = {
        "title": "Entire Corporate VPN Gateway Down",
        "description": "Global datacenter VPN infrastructure failure. All employees and remote workers disconnected across company.",
        "impact": "High",
        "urgency": "High"
    }
    # 3a. Preview
    req_ent_prev = urllib.request.Request(f"{base_url}/ai/analyze", data=json.dumps(enterprise_payload).encode(), headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    })
    with urllib.request.urlopen(req_ent_prev) as r:
        ent_prev = json.loads(r.read().decode())["analysis"]
        print(f"Enterprise Outage Preview:")
        print(f"  Priority: {ent_prev['priority']}")
        print(f"  Reason: {ent_prev['reason_for_priority']}")
        assert ent_prev["priority"] == "Critical", f"FAILED: Expected Critical for enterprise outage, got {ent_prev['priority']}"
        print("  >> ENTERPRISE PREVIEW PASSED: Priority is Critical.")

    # 3b. Create Ticket
    req_ent_create = urllib.request.Request(f"{base_url}/tickets", data=json.dumps(enterprise_payload).encode(), headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    })
    with urllib.request.urlopen(req_ent_create) as r:
        ent_ticket = json.loads(r.read().decode())["ticket"]
        print(f"\nEnterprise Stored Ticket:")
        print(f"  Ticket Number: {ent_ticket['ticket_number']}")
        print(f"  Priority: {ent_ticket['priority']}")
        assert ent_ticket["priority"] == "Critical", f"FAILED: Expected Critical, got {ent_ticket['priority']}"
        print("  >> ENTERPRISE TICKET CREATION PASSED: Correctly stored as Critical.")

    print("\n=======================================================")
    print("STEP 4: Test Standard Single-User Issue (Medium/Medium, No Meeting) -> Medium")
    print("=======================================================")
    std_payload = {
        "title": "VPN connection logs review request",
        "description": "Need assistance reviewing my local connection logs when convenient.",
        "impact": "Medium",
        "urgency": "Medium"
    }
    req_std = urllib.request.Request(f"{base_url}/tickets", data=json.dumps(std_payload).encode(), headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    })
    with urllib.request.urlopen(req_std) as r:
        std_ticket = json.loads(r.read().decode())["ticket"]
        print(f"Standard Ticket Stored Priority: {std_ticket['priority']}")
        assert std_ticket["priority"] == "Medium", f"FAILED: Expected Medium, got {std_ticket['priority']}"
        print("  >> STANDARD ISSUE PASSED: Priority is Medium.")

    print("\n=======================================================")
    print("STEP 5: Verify Admin Dashboard Metrics & Health Concurrency Monitoring")
    print("=======================================================")
    # Login as admin
    admin_login_data = json.dumps({"email": "admin@smartdesk.ai", "password": "Admin@123"}).encode()
    req_adm = urllib.request.Request(f"{base_url}/login", data=admin_login_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req_adm) as r:
        adm_token = json.loads(r.read().decode())["token"]

    # Dashboard stats
    req_stats = urllib.request.Request(f"{base_url}/dashboard/stats", headers={"Authorization": f"Bearer {adm_token}"})
    with urllib.request.urlopen(req_stats) as r:
        stats = json.loads(r.read().decode())
        print("Dashboard Metrics:")
        print("  Total Tickets:", stats["metrics"]["total_tickets"])
        print("  Critical Tickets:", stats["metrics"]["critical_tickets"])
        print("  High Priority Tickets:", stats["metrics"]["high_priority_tickets"])
        print("  By Priority Breakdown:", stats["by_priority"])

    # Health telemetry
    with urllib.request.urlopen(f"{base_url}/health") as r:
        health_data = json.loads(r.read().decode())
        ai_info = health_data["ai"]
        telemetry = ai_info["concurrency_monitoring"]
        print("\nAI Health & Concurrency Monitoring:")
        print(f"  Active Workers: {telemetry['active_workers']} / {telemetry['max_concurrency']}")
        print(f"  Total Requests: {telemetry['total_requests']}")
        print(f"  Completed: {telemetry['completed']}")
        print(f"  Timeouts: {telemetry['timeouts']}")
        print(f"  Fallbacks: {telemetry['fallbacks']}")
        print(f"  Concurrency Sheds: {telemetry['concurrency_sheds']}")
        assert telemetry["active_workers"] <= telemetry["max_concurrency"], "Active workers exceeded cap!"
        print("  >> CONCURRENCY MONITORING PASSED: Bounded within safe concurrency limits.")

    print("\n=======================================================")
    print("ALL REGRESSION & ITIL PRIORITY CONSISTENCY TESTS PASSED (100%)")
    print("=======================================================\n")

if __name__ == "__main__":
    run_regression_tests()
