import time
import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from services.ai_service import analyze_ticket_with_gemini, rule_based_fallback
import services.ai_service as ai_module

def run_tests():
    print("\n=======================================================")
    print("TEST 1: Verify ThreadPoolExecutor Timeout Returns Promptly")
    print("=======================================================")

    # Mock _call_gemini_raw with an 8-second slow worker to simulate a hung API call
    orig_call = ai_module._call_gemini_raw

    def simulated_slow_gemini(client, model, prompt):
        time.sleep(8)
        return orig_call(client, model, prompt)

    ai_module._call_gemini_raw = simulated_slow_gemini

    # Warm up client initialization
    ai_module.get_genai_client()

    t0 = time.time()
    res = analyze_ticket_with_gemini(
        title="My office VPN is not connecting",
        description="Gateway unreachable error 412",
        impact="Medium",
        urgency="Medium",
        timeout_seconds=2  # 2-second test timeout
    )
    elapsed = time.time() - t0

    print(f"Elapsed Time: {elapsed:.2f} seconds (Target Timeout: 2.0s)")
    print(f"Returned Source: {res['analysis_source']}")
    print(f"Returned Category: {res['category']}")
    print(f"Returned Priority: {res['priority']}")
    print(f"Returned Reason: {res['reason_for_priority']}")

    # Restore original call
    ai_module._call_gemini_raw = orig_call

    # Assert that execution did NOT wait for the 8s worker and returned promptly within ~2s
    assert elapsed < 3.0, f"FAILED: Function took {elapsed:.2f}s instead of returning promptly on 2s timeout!"
    assert res["analysis_source"] == "rule_based_fallback", "FAILED: Did not return rule-based fallback!"
    print(">> TEST 1 PASSED: Timeout returned immediately without waiting for worker!")

    print("\n=======================================================")
    print("TEST 2: Verify Medium Impact + Medium Urgency Priority")
    print("=======================================================")

    # Case A: Medium Impact + Medium Urgency + Important client meeting
    res_client = rule_based_fallback(
        title="My office VPN is not connecting",
        description="I have an important client meeting in 30 minutes and need access to presentation deck.",
        impact="Medium",
        urgency="Medium"
    )
    print("Case A (Medium Impact / Urgency + Client Meeting):")
    print(f"  Priority: {res_client['priority']}")
    print(f"  Reason: {res_client['reason_for_priority']}")
    assert res_client["priority"] != "Critical", "FAILED: Priority must NOT be Critical!"
    assert res_client["priority"] == "High", f"FAILED: Expected High for urgent client meeting, got {res_client['priority']}"
    print("  >> Case A PASSED: Scaled to High, NOT Critical.")

    # Case B: Standard Medium Impact + Medium Urgency without meeting
    res_std = rule_based_fallback(
        title="My office VPN is not connecting",
        description="Cannot reach internal staging server, will try again after lunch.",
        impact="Medium",
        urgency="Medium"
    )
    print("\nCase B (Standard Medium Impact / Urgency):")
    print(f"  Priority: {res_std['priority']}")
    print(f"  Reason: {res_std['reason_for_priority']}")
    assert res_std["priority"] == "Medium", f"FAILED: Expected Medium, got {res_std['priority']}"
    print("  >> Case B PASSED: Correctly assigned Medium priority.")

    # Case C: Low Impact + Low Urgency
    res_low = rule_based_fallback(
        title="VPN icon display is slightly offset",
        description="Just a cosmetic question about tray icon.",
        impact="Low",
        urgency="Low"
    )
    print("\nCase C (Low Impact / Urgency):")
    print(f"  Priority: {res_low['priority']}")
    assert res_low["priority"] == "Low", f"FAILED: Expected Low, got {res_low['priority']}"
    print("  >> Case C PASSED: Correctly assigned Low priority.")

    # Case D: High Impact + High Urgency (Enterprise-wide)
    res_crit = rule_based_fallback(
        title="Enterprise VPN Gateway Down",
        description="Entire Chicago datacenter VPN gateway unresponsive, all remote workers disconnected.",
        impact="High",
        urgency="High"
    )
    print("\nCase D (Enterprise High Impact + High Urgency):")
    print(f"  Priority: {res_crit['priority']}")
    assert res_crit["priority"] == "Critical", f"FAILED: Expected Critical, got {res_crit['priority']}"
    print("  >> Case D PASSED: Critical reserved for high impact + high urgency.")

    print("\n=======================================================")
    print("ALL TIMEOUT & PRIORITY VERIFICATION TESTS PASSED (100%)")
    print("=======================================================\n")

if __name__ == "__main__":
    run_tests()
