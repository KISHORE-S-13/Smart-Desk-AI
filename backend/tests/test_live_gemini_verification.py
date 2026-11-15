import urllib.request
import json
import time
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

def run_live_verification():
    base_url = "http://127.0.0.1:5000/api"

    print("=================================================================")
    print("PHASE 1: Inspect Health & Concurrency Telemetry BEFORE Call")
    print("=================================================================")
    with urllib.request.urlopen(f"{base_url}/health") as r:
        h_before = json.loads(r.read().decode())
        print(f"Service Status: {h_before['status']}")
        print(f"Database: {h_before['database']}")
        print(f"Configured Model: {h_before['ai']['gemini_model']}")
        print("Telemetry Before:")
        print(json.dumps(h_before["ai"]["concurrency_monitoring"], indent=2))

    print("\n=================================================================")
    print("PHASE 2: Authenticate Employee")
    print("=================================================================")
    login_data = json.dumps({"email": "employee@smartdesk.ai", "password": "Employee@123"}).encode()
    req = urllib.request.Request(f"{base_url}/login", data=login_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        emp_token = json.loads(r.read().decode())["token"]
        print("Authenticated successfully as employee.")

    print("\n=================================================================")
    print("PHASE 3: Live Gemini Analysis of Network Troubleshooting Prompt")
    print("=================================================================")
    prompt_payload = {
        "title": "My office Wi-Fi keeps disconnecting every 10 minutes",
        "description": "The Wi-Fi signal drops and reconnects automatically on my corporate laptop while working in conference room B.",
        "impact": "Medium",
        "urgency": "Medium"
    }

    t0 = time.time()
    req_analyze = urllib.request.Request(f"{base_url}/ai/analyze", data=json.dumps(prompt_payload).encode(), headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {emp_token}"
    })
    with urllib.request.urlopen(req_analyze) as r:
        response_data = json.loads(r.read().decode())
        elapsed_time = time.time() - t0

    analysis = response_data.get("analysis", {})
    print(f"Response Received in: {elapsed_time:.2f} seconds")
    print(f"Analysis Source: {analysis.get('analysis_source')}")
    print(f"Detected Ticket Type: {analysis.get('ticket_type')}")
    print(f"Detected Category: {analysis.get('category')}")
    print(f"Calculated Priority: {analysis.get('priority')}")
    print(f"Priority Reason: {analysis.get('reason_for_priority')}")
    print(f"Assigned Support Team: {analysis.get('assigned_support_team')}")
    print(f"Recommended Steps Count: {len(analysis.get('recommended_troubleshooting_steps', []))}")
    for idx, step in enumerate(analysis.get("recommended_troubleshooting_steps", []), 1):
        print(f"  Step {idx}: {step}")
    print(f"Suggested Response: {analysis.get('suggested_response_to_employee')}")

    # Confirm genuine Gemini generation
    assert analysis.get("analysis_source") == "gemini", f"FAILED: Expected analysis_source='gemini', got {analysis.get('analysis_source')}"
    print("\n>> VERIFICATION: Successfully confirmed genuine Gemini AI generation (analysis_source='gemini')!")

    print("\n=================================================================")
    print("PHASE 4: Inspect Health & Concurrency Telemetry AFTER Call")
    print("=================================================================")
    with urllib.request.urlopen(f"{base_url}/health") as r:
        h_after = json.loads(r.read().decode())
        telemetry_after = h_after["ai"]["concurrency_monitoring"]
        print("Telemetry After:")
        print(json.dumps(telemetry_after, indent=2))
        assert telemetry_after["completed"] >= 1, "Completed counter did not increment!"
        assert telemetry_after["active_workers"] == 0, "Active workers should be 0 after completion!"
        print(">> TELEMETRY VERIFICATION: Completed requests incremented; active workers cleanly reset to 0.")

    print("\n=================================================================")
    print("PHASE 5: Separately Verify Fallback Engine Still Works When Gemini Unavailable")
    print("=================================================================")
    from services.ai_service import rule_based_fallback
    fallback_res = rule_based_fallback(
        title="VPN client gateway error 412",
        description="Cannot connect to network gateway during service maintenance.",
        impact="Medium",
        urgency="Medium"
    )
    print(f"Fallback Analysis Source: {fallback_res.get('analysis_source')}")
    print(f"Fallback Category: {fallback_res.get('category')}")
    print(f"Fallback Priority: {fallback_res.get('priority')}")
    print(f"Fallback Team: {fallback_res.get('assigned_support_team')}")
    print(f"Fallback Steps Count: {len(fallback_res.get('recommended_troubleshooting_steps', []))}")
    assert fallback_res.get("analysis_source") == "rule_based_fallback", "Fallback source mismatch!"
    print(">> FALLBACK VERIFICATION: Deterministic fallback engine is operational and verified.")

    print("\n=================================================================")
    print("ALL LIVE GEMINI & FALLBACK VERIFICATION TESTS PASSED (100%)")
    print("=================================================================\n")

if __name__ == "__main__":
    run_live_verification()
