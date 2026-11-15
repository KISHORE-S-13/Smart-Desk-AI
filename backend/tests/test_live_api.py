import urllib.request
import json
import time

def run_integration_tests():
    base_url = "http://127.0.0.1:5000/api"
    proxy_url = "http://127.0.0.1:5173/api"

    print("\n--- [Step 1] Testing Direct Backend Health Check ---")
    with urllib.request.urlopen(f"{base_url}/health") as response:
        health_data = json.loads(response.read().decode())
        print(f"Status: {health_data.get('status')}")
        print(f"Database: {health_data.get('database')}")
        print(f"Gemini Configured: {health_data.get('ai', {}).get('gemini_configured')}")

    print("\n--- [Step 2] Testing Vite Dev Server & Proxy Health Check ---")
    with urllib.request.urlopen(f"{proxy_url}/health") as response:
        proxy_data = json.loads(response.read().decode())
        print(f"Proxy Response: {proxy_data.get('status')}")

    print("\n--- [Step 3] Testing Employee Login ---")
    login_payload = json.dumps({"email": "employee@smartdesk.ai", "password": "Employee@123"}).encode()
    req = urllib.request.Request(f"{base_url}/login", data=login_payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as response:
        emp_res = json.loads(response.read().decode())
        emp_token = emp_res["token"]
        print(f"Authenticated as: {emp_res['user']['name']} ({emp_res['user']['role']})")

    print("\n--- [Step 4] Testing Employee Ticket Creation with Live Gemini Analysis ---")
    ticket_payload = json.dumps({
        "title": "My office VPN is not connecting",
        "description": "When attempting to connect to the corporate VPN gateway from my remote office, the client times out with error 412.",
        "impact": "High",
        "urgency": "Medium"
    }).encode()
    req = urllib.request.Request(f"{base_url}/tickets", data=ticket_payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {emp_token}"
    })
    with urllib.request.urlopen(req) as response:
        t_res = json.loads(response.read().decode())
        ticket = t_res["ticket"]
        ticket_id = ticket["id"]
        ticket_num = ticket["ticket_number"]
        print(f"Ticket Created: {ticket_num}")
        print(f"Category: {ticket['category']}")
        print(f"Priority: {ticket['priority']}")
        print(f"Engine: {ticket['analysis_source']}")
        print(f"Assigned Support Team: {ticket['assigned_team']}")
        print(f"Suggested Response: {ticket.get('suggested_response')[:120]}...")

    print("\n--- [Step 5] Testing Admin Login ---")
    admin_login_payload = json.dumps({"email": "admin@smartdesk.ai", "password": "Admin@123"}).encode()
    req = urllib.request.Request(f"{base_url}/login", data=admin_login_payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as response:
        adm_res = json.loads(response.read().decode())
        adm_token = adm_res["token"]
        print(f"Authenticated as: {adm_res['user']['name']} ({adm_res['user']['role']})")

    print("\n--- [Step 6] Testing Admin Ticket Update & Resolution ---")
    patch_payload = json.dumps({
        "status": "Resolved",
        "assigned_team": "Network Operations",
        "resolution_notes": "Reset IPsec tunnel on Chicago edge gateway and cleared routing table entry. Confirmed operational with user."
    }).encode()
    req = urllib.request.Request(f"{base_url}/tickets/{ticket_id}", data=patch_payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {adm_token}"
    }, method="PATCH")
    with urllib.request.urlopen(req) as response:
        up_res = json.loads(response.read().decode())
        up_ticket = up_res["ticket"]
        print(f"Ticket Status Updated: {up_ticket['status']}")
        print(f"Assigned Team: {up_ticket['assigned_team']}")
        print(f"Resolution Notes: {up_ticket['resolution_notes']}")
        print(f"Audit History Entries: {len(up_ticket['history'])}")

    print("\n--- [Step 7] Testing Admin Operations Dashboard Metrics ---")
    req = urllib.request.Request(f"{base_url}/dashboard/stats", headers={"Authorization": f"Bearer {adm_token}"})
    with urllib.request.urlopen(req) as response:
        stats_res = json.loads(response.read().decode())
        metrics = stats_res["metrics"]
        print(f"Total Tickets: {metrics['total_tickets']}")
        print(f"Open Tickets: {metrics['open_tickets']}")
        print(f"Resolved Tickets: {metrics['resolved_tickets']}")
        print(f"Critical/High Tickets: {metrics['critical_and_high']}")
        print(f"Categories Breakdown: {stats_res['by_category']}")

    print("\n--- [Step 8] Testing Knowledge Assistant Chatbot (RAG) ---")
    chat_payload = json.dumps({
        "message": "My office VPN is not connecting. What should I check?"
    }).encode()
    req = urllib.request.Request(f"{base_url}/ai/chat", data=chat_payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {emp_token}"
    })
    with urllib.request.urlopen(req) as response:
        chat_res = json.loads(response.read().decode())
        print(f"Chatbot Engine: {chat_res.get('source_type')}")
        print(f"Retrieved Sources: {[s['title'] for s in chat_res.get('sources', [])]}")
        print(f"Answer Preview: {chat_res['answer'][:150]}...")

    print("\n=======================================================")
    print("SUCCESS: ALL END-TO-END LIVE API & FRONTEND TESTS PASSED!")
    print("=======================================================\n")

if __name__ == "__main__":
    run_integration_tests()
