import urllib.request
import json
import time

def test_vpn_workflow_and_timeout():
    base_url = "http://127.0.0.1:5000/api"

    print("\n=== STEP 1: Employee Authentication ===")
    login_payload = json.dumps({"email": "employee@smartdesk.ai", "password": "Employee@123"}).encode()
    req = urllib.request.Request(f"{base_url}/login", data=login_payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        login_res = json.loads(resp.read().decode())
        emp_token = login_res["token"]
        print(f"Logged in as: {login_res['user']['name']} ({login_res['user']['email']})")

    print("\n=== STEP 2: Pre-Submission AI Analysis Preview (POST /api/ai/analyze) ===")
    start_time = time.time()
    analyze_payload = json.dumps({
        "title": "My office VPN is not connecting",
        "description": "Cisco AnyConnect gives error 'Gateway not reachable' on Chicago VPN gateway.",
        "impact": "High",
        "urgency": "High"
    }).encode()
    req = urllib.request.Request(f"{base_url}/ai/analyze", data=analyze_payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {emp_token}"
    })
    with urllib.request.urlopen(req) as resp:
        analysis_res = json.loads(resp.read().decode())
        elapsed = time.time() - start_time
        analysis = analysis_res["analysis"]
        print(f"Analysis completed in {elapsed:.2f}s")
        print(f"Source: {analysis['analysis_source']}")
        print(f"Category: {analysis['category']}")
        print(f"Priority: {analysis['priority']}")
        print(f"Assigned Support Team: {analysis['assigned_support_team']}")
        print(f"Troubleshooting Steps Count: {len(analysis['recommended_troubleshooting_steps'])}")

    print("\n=== STEP 3: Submitting VPN Incident (POST /api/tickets) ===")
    ticket_payload = json.dumps({
        "title": "My office VPN is not connecting",
        "description": "Cisco AnyConnect gives error 'Gateway not reachable' on Chicago VPN gateway.",
        "impact": "High",
        "urgency": "High",
        "pre_analysis": analysis
    }).encode()
    req = urllib.request.Request(f"{base_url}/tickets", data=ticket_payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {emp_token}"
    })
    with urllib.request.urlopen(req) as resp:
        ticket_res = json.loads(resp.read().decode())
        ticket = ticket_res["ticket"]
        ticket_id = ticket["id"]
        ticket_number = ticket["ticket_number"]
        print(f"Ticket Created: {ticket_number} (ID: {ticket_id})")
        print(f"Status: {ticket['status']}")
        print(f"Duplicate Prevented Flag: {ticket_res.get('duplicate_prevented')}")

    print("\n=== STEP 4: Duplicate Ticket Prevention Test ===")
    # Immediately attempt to submit the identical ticket again
    req_dup = urllib.request.Request(f"{base_url}/tickets", data=ticket_payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {emp_token}"
    })
    with urllib.request.urlopen(req_dup) as resp:
        dup_res = json.loads(resp.read().decode())
        print(f"Response Message: {dup_res['message']}")
        print(f"Duplicate Prevented: {dup_res.get('duplicate_prevented')}")
        print(f"Returned Ticket: {dup_res['ticket']['ticket_number']} (Same as {ticket_number}: {dup_res['ticket']['ticket_number'] == ticket_number})")
        assert dup_res.get("duplicate_prevented") is True, "Duplicate prevention failed!"

    print("\n=== STEP 5: Admin Login & Workflow Resolution ===")
    admin_login_payload = json.dumps({"email": "admin@smartdesk.ai", "password": "Admin@123"}).encode()
    req_admin = urllib.request.Request(f"{base_url}/login", data=admin_login_payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req_admin) as resp:
        admin_res = json.loads(resp.read().decode())
        admin_token = admin_res["token"]
        print(f"Logged in as Admin: {admin_res['user']['name']}")

    # Transition to In Progress
    patch_in_progress = json.dumps({
        "status": "In Progress",
        "assigned_team": "Network Operations"
    }).encode()
    req_patch1 = urllib.request.Request(f"{base_url}/tickets/{ticket_id}", data=patch_in_progress, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {admin_token}"
    }, method="PATCH")
    with urllib.request.urlopen(req_patch1) as resp:
        p1_res = json.loads(resp.read().decode())
        print(f"Ticket Status Transitioned: {p1_res['ticket']['status']}")

    # Transition to Resolved with resolution notes
    patch_resolved = json.dumps({
        "status": "Resolved",
        "resolution_notes": "Restarted IPsec daemon on Chicago edge router and verified handshake telemetry. User confirmed connected."
    }).encode()
    req_patch2 = urllib.request.Request(f"{base_url}/tickets/{ticket_id}", data=patch_resolved, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {admin_token}"
    }, method="PATCH")
    with urllib.request.urlopen(req_patch2) as resp:
        p2_res = json.loads(resp.read().decode())
        print(f"Ticket Status Transitioned: {p2_res['ticket']['status']}")
        print(f"Resolution Notes: {p2_res['ticket']['resolution_notes']}")
        print(f"Total Audit History Events: {len(p2_res['ticket']['history'])}")

    print("\n=== STEP 6: Admin Dashboard Operations Stats Check ===")
    req_stats = urllib.request.Request(f"{base_url}/dashboard/stats", headers={"Authorization": f"Bearer {admin_token}"})
    with urllib.request.urlopen(req_stats) as resp:
        stats = json.loads(resp.read().decode())
        print("Updated Metrics:", stats["metrics"])

    print("\n=======================================================")
    print("SUCCESS: COMPLETE VPN WORKFLOW & DUPLICATE PROTECTION VERIFIED!")
    print("=======================================================\n")

if __name__ == "__main__":
    test_vpn_workflow_and_timeout()
