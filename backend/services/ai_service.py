import os
import json
import re
import threading
import concurrent.futures
from config import Config
from google.genai import types

# Safe concurrency limit for simultaneous Gemini API network workers
MAX_CONCURRENT_GEMINI_CALLS = 4

# Persistent module-level thread pool executor to avoid shutdown(wait=True) blocking on timeouts
_ai_executor = concurrent.futures.ThreadPoolExecutor(
    max_workers=MAX_CONCURRENT_GEMINI_CALLS,
    thread_name_prefix="smartdesk-ai-worker"
)

# Concurrency telemetry & monitoring
_telemetry_lock = threading.Lock()
_telemetry = {
    "total_requests": 0,
    "active_workers": 0,
    "max_concurrency": MAX_CONCURRENT_GEMINI_CALLS,
    "completed": 0,
    "timeouts": 0,
    "fallbacks": 0,
    "concurrency_sheds": 0
}

def get_ai_telemetry():
    """Returns current concurrency telemetry for monitoring and health reporting."""
    with _telemetry_lock:
        return dict(_telemetry)

# Attempt to initialize genai client safely
_genai_client = None

def get_genai_client():
    global _genai_client
    if _genai_client is None:
        api_key = Config.GEMINI_API_KEY
        if api_key:
            try:
                from google import genai
                # Configure 30-second timeout at the HTTP transport layer (30,000 ms)
                http_options = types.HttpOptions(timeout=30000)
                _genai_client = genai.Client(api_key=api_key, http_options=http_options)
            except Exception as e:
                _genai_client = None
    return _genai_client

VALID_CATEGORIES = ["Network", "Hardware", "Software", "Email", "Access Management", "Other"]
VALID_PRIORITIES = ["Low", "Medium", "High", "Critical"]
VALID_TICKET_TYPES = ["Incident", "Service Request"]


def apply_itil_priority_guardrail(title, description, impact, urgency, candidate_priority, reason=""):
    """
    Enforces strict ITIL Service Management priority bounding:
    - Critical (P1): Strictly reserved for enterprise/multi-user or production infrastructure outages
      combined with High Impact and High Urgency.
      A single individual user's issue MUST NEVER be Critical, even with an important client meeting.
    - High (P2): Appropriate for single-user incidents where an urgent client meeting, executive presentation,
      or severe operational blockage is documented, or where user reports High Impact/Urgency.
    - Medium (P3): Standard single-user operational issue with Medium Impact and Medium Urgency.
    - Low (P4): Low impact and low urgency non-blocking requests.
    """
    text = f"{title} {description}".lower()
    impact_val = impact.capitalize() if impact else "Medium"
    urgency_val = urgency.capitalize() if urgency else "Medium"

    is_enterprise_outage = any(w in text for w in [
        "entire", "all users", "company-wide", "datacenter", "widespread",
        "all employees", "all staff", "global outage", "everyone", "system wide"
    ])
    has_client_meeting = any(w in text for w in [
        "client meeting", "urgent meeting", "board meeting", "presentation",
        "customer call", "client presentation", "executive meeting"
    ])

    adjusted_priority = candidate_priority or "Medium"
    guardrail_note = ""

    # Rule 1: Critical is ONLY permitted for enterprise/multi-user outages with High impact & High urgency
    if adjusted_priority == "Critical":
        if not (impact_val == "High" and urgency_val == "High" and is_enterprise_outage):
            if has_client_meeting or impact_val == "High" or urgency_val == "High":
                adjusted_priority = "High"
                guardrail_note = " (ITIL Guardrail: Scaled to High; single-user incident with meeting/urgency does not warrant enterprise Critical)"
            else:
                adjusted_priority = "Medium"
                guardrail_note = " (ITIL Guardrail: Scaled to Medium; Medium impact and urgency cannot be Critical)"

    # Rule 2: If user reports Medium + Medium, ensure client meeting scales to High, else Medium
    if impact_val == "Medium" and urgency_val == "Medium":
        if adjusted_priority == "Critical":
            adjusted_priority = "High" if has_client_meeting else "Medium"
        elif has_client_meeting and adjusted_priority == "Medium":
            adjusted_priority = "High"
            guardrail_note = " (ITIL Guardrail: Time-sensitive client meeting elevates Medium/Medium incident to High)"

    # Rule 3: Low impact + Low urgency cannot exceed Low
    if impact_val == "Low" and urgency_val == "Low" and not has_client_meeting:
        adjusted_priority = "Low"

    # Rule 4: Enterprise outage with High impact & High urgency must be Critical
    if impact_val == "High" and urgency_val == "High" and is_enterprise_outage:
        adjusted_priority = "Critical"
        guardrail_note = " (ITIL Guardrail: Confirmed Critical for enterprise-wide service disruption)"

    full_reason = f"{reason}{guardrail_note}".strip()
    return adjusted_priority, full_reason


def rule_based_fallback(title, description, impact="Medium", urgency="Medium", reason_prefix="[Fallback Engine]"):
    """
    Deterministic rule-based classification fallback when Gemini API is offline, timed out, or unreachable.
    Conforms strictly to ITIL ITSM priority and routing standards.
    """
    text = f"{title} {description}".lower()

    # Determine category and assigned team
    if any(k in text for k in ["vpn", "wifi", "wi-fi", "internet", "dns", "lan", "connection", "router", "network", "gateway"]):
        category = "Network"
        assigned_team = "Network Operations"
        rec_steps = [
            "Check physical LAN cable connection or local Wi-Fi signal strength.",
            "Verify gateway reachability by pinging internal network endpoints.",
            "Restart the VPN client and re-authenticate via corporate SSO/MFA.",
            "Flush local DNS cache via 'ipconfig /flushdns'."
        ]
        suggested_response = (
            "We have received your network connectivity issue. Our Network Operations team has been notified. "
            "Please ensure your local internet is active and try restarting your VPN client with fresh MFA."
        )
    elif any(k in text for k in ["password", "reset", "login", "unlock", "access", "permission", "sso", "mfa", "authenticator"]):
        category = "Access Management"
        assigned_team = "Identity & Access Management (IAM)"
        rec_steps = [
            "Verify corporate portal credentials through the Self-Service Password Reset portal.",
            "Ensure Microsoft Authenticator or Duo MFA push is approved on your registered mobile device.",
            "Wait 15 minutes if your account has triggered a temporary lockout.",
            "Contact your direct manager for permission elevation approval if requesting new folder/repo access."
        ]
        suggested_response = (
            "Your access request/incident has been logged with Identity & Access Management. "
            "If this is an account lockout, please allow 15 minutes before re-attempting or use the self-service portal."
        )
    elif any(k in text for k in ["outlook", "email", "mailbox", "inbox", "exchange", "calendar", "mail"]):
        category = "Email"
        assigned_team = "Enterprise Messaging & Collaboration"
        rec_steps = [
            "Check mailbox storage capacity to ensure quota has not been exceeded.",
            "Access webmail via Outlook Web Access (OWA) to confirm backend service status.",
            "Restart Microsoft Outlook in safe mode (outlook.exe /safe).",
            "Verify send/receive settings and re-sync local OST file."
        ]
        suggested_response = (
            "Thank you for reaching out. We have assigned this to Enterprise Messaging. "
            "In the meantime, you can continue accessing your emails via Outlook Web App."
        )
    elif any(k in text for k in ["laptop", "monitor", "screen", "keyboard", "mouse", "printer", "battery", "charger", "hardware", "dock"]):
        category = "Hardware"
        assigned_team = "Workplace Tech Support"
        rec_steps = [
            "Check cable seating, power adapters, and USB-C docking connections.",
            "Perform a hard power cycle by holding power button for 15 seconds.",
            "Test on another display or peripheral port if available.",
            "Bring the device to the on-site IT walk-up service desk for diagnostic inspection."
        ]
        suggested_response = (
            "Your hardware support ticket has been dispatched to Workplace Tech Support. "
            "An engineer will coordinate with you for diagnostic inspection or replacement parts."
        )
    elif any(k in text for k in ["crash", "freeze", "bug", "install", "software", "license", "update", "application", "excel", "teams"]):
        category = "Software"
        assigned_team = "Application Support"
        rec_steps = [
            "Restart the affected application and check for pending Windows/Mac updates.",
            "Verify application permissions and license status in Company Portal.",
            "Clear application cache and temp data.",
            "Reinstall the software package from the approved Enterprise Software Center."
        ]
        suggested_response = (
            "Your application issue has been logged with Application Support. "
            "Please check Company Portal for software re-installation or self-service updates."
        )
    else:
        category = "Other"
        assigned_team = "Service Desk Tier 1"
        rec_steps = [
            "Restart your system to clear transient OS states.",
            "Gather error messages, screenshots, and system event timestamps.",
            "A Service Desk agent will review your ticket shortly."
        ]
        suggested_response = (
            "Your IT request has been assigned to Service Desk Tier 1. "
            "An agent will review your details and contact you shortly."
        )

    # Determine ticket type
    if any(k in text for k in ["request", "new", "order", "grant", "install", "provide", "setup"]):
        ticket_type = "Service Request"
    else:
        ticket_type = "Incident"

    # Calculate initial candidate priority based on basic matrix
    impact_val = impact.capitalize() if impact else "Medium"
    urgency_val = urgency.capitalize() if urgency else "Medium"

    if impact_val == "High" and urgency_val == "High":
        raw_priority = "Critical"
        raw_reason = "High impact affecting operations combined with high urgency."
    elif impact_val == "High" or urgency_val == "High":
        raw_priority = "High"
        raw_reason = "Significant operational impact or urgent user dependency identified."
    elif impact_val == "Low" and urgency_val == "Low":
        raw_priority = "Low"
        raw_reason = "Low operational impact and non-blocking urgency."
    else:
        raw_priority = "Medium"
        raw_reason = "Standard operational impact with regular service turnaround."

    # Enforce ITIL Guardrails on fallback priority
    guarded_priority, guarded_reason = apply_itil_priority_guardrail(
        title=title,
        description=description,
        impact=impact,
        urgency=urgency,
        candidate_priority=raw_priority,
        reason=raw_reason
    )

    return {
        "ticket_type": ticket_type,
        "issue_summary": title.strip(),
        "category": category,
        "priority": guarded_priority,
        "reason_for_priority": f"{reason_prefix} {guarded_reason}",
        "assigned_support_team": assigned_team,
        "recommended_troubleshooting_steps": rec_steps,
        "suggested_response_to_employee": suggested_response,
        "analysis_source": "rule_based_fallback"
    }


def _call_gemini_raw(client, model_name, prompt):
    """Executes the synchronous call to Gemini API with active thread tracking."""
    with _telemetry_lock:
        _telemetry["active_workers"] += 1
    try:
        return client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
    finally:
        with _telemetry_lock:
            _telemetry["active_workers"] = max(0, _telemetry["active_workers"] - 1)


def analyze_ticket_with_gemini(title, description, impact="Medium", urgency="Medium", timeout_seconds=30):
    """
    Sends ticket details to Gemini using google-genai SDK for enterprise IT classification.
    Enforces:
    1. Safe concurrency bounds (siphons to fallback if all workers busy).
    2. Strict 30-second timeout on a persistent thread pool (no shutdown wait).
    3. Strict ITIL priority guardrails on returned priority.
    """
    with _telemetry_lock:
        _telemetry["total_requests"] += 1
        # Concurrency safety check: if worker pool is currently saturated, avoid queuing
        if _telemetry["active_workers"] >= MAX_CONCURRENT_GEMINI_CALLS:
            _telemetry["concurrency_sheds"] += 1
            _telemetry["fallbacks"] += 1
            print(f"[SmartDesk AI] Concurrency limit reached ({MAX_CONCURRENT_GEMINI_CALLS}/{MAX_CONCURRENT_GEMINI_CALLS}). Siphoning to fallback.")
            return rule_based_fallback(
                title, description, impact, urgency,
                reason_prefix="[Fallback Engine - Concurrency Cap]"
            )

    client = get_genai_client()
    model_name = Config.GEMINI_MODEL or "gemini-3.8-flash"

    if not client or not Config.GEMINI_API_KEY:
        with _telemetry_lock:
            _telemetry["fallbacks"] += 1
        return rule_based_fallback(title, description, impact, urgency, reason_prefix="[Fallback Engine - No API Key]")

    prompt = f"""You are an enterprise IT Service Management (ITSM) AI classifier for SmartDesk AI.
Analyze the following employee IT incident or request and produce a strictly valid JSON response.

Input Details:
- Issue Title: {title}
- Description: {description}
- User Reported Impact: {impact}
- User Reported Urgency: {urgency}

Allowed Categories:
Network, Hardware, Software, Email, Access Management, Other

Allowed Priorities:
Low, Medium, High, Critical

Strict ITIL Priority Determination Rules:
- Critical: Reserved ONLY for enterprise-wide or multi-user outages affecting core business operations or production infrastructure.
  IMPORTANT RULE: A single individual user's issue (even with an important client meeting, deadline, or executive involvement) MUST NEVER be classified as Critical.
- High: Severe impact where an individual user is completely blocked from a time-critical business deliverable (e.g., immediate client presentation) with no workaround, or high impact affecting a team.
- Medium: Standard operational issues affecting a single user or department where workarounds are possible or the user reports Medium Impact and Medium Urgency. If the user selects Impact: Medium and Urgency: Medium, the priority must NOT be Critical; assign Medium (or High only if an imminent deadline is documented, but NEVER Critical).
- Low: Non-blocking inquiries, minor inconveniences, or requests with low impact and low urgency.

Allowed Ticket Types:
Incident, Service Request

Assign a realistic support team such as:
Network Operations, Workplace Tech Support, Application Support, Enterprise Messaging & Collaboration, Identity & Access Management (IAM), or Service Desk Tier 1.

Return ONLY a single valid JSON object with the exact keys:
{{
  "ticket_type": "Incident or Service Request",
  "issue_summary": "Concise 1-sentence technical summary of the issue",
  "category": "One of: Network, Hardware, Software, Email, Access Management, Other",
  "priority": "One of: Low, Medium, High, Critical",
  "reason_for_priority": "Clear justification based on impact, business urgency and scope",
  "assigned_support_team": "Specific support team name",
  "recommended_troubleshooting_steps": [
    "Step 1 actionable guidance",
    "Step 2 actionable guidance",
    "Step 3 actionable guidance",
    "Step 4 actionable guidance"
  ],
  "suggested_response_to_employee": "Professional, empathetic, and actionable response addressing the employee"
}}
"""

    primary_model = Config.GEMINI_MODEL or "gemini-3.8-flash"
    candidate_models = [primary_model]
    if "gemini-3.5-flash" not in candidate_models:
        candidate_models.append("gemini-3.5-flash")

    response = None
    last_error = None
    used_model = primary_model

    for m in candidate_models:
        try:
            future = _ai_executor.submit(_call_gemini_raw, client, m, prompt)
            response = future.result(timeout=timeout_seconds)
            used_model = m
            break
        except concurrent.futures.TimeoutError:
            print(f"[SmartDesk AI] Model {m} timed out after {timeout_seconds}s.")
            last_error = f"TimeoutError after {timeout_seconds}s"
            break  # If timed out, break immediately to avoid blocking user further
        except Exception as e:
            api_key = Config.GEMINI_API_KEY or ""
            err_msg = str(e).replace(api_key, "[REDACTED_API_KEY]") if api_key else str(e)
            print(f"[SmartDesk AI] Model {m} unavailable ({err_msg[:100]}). Trying next candidate...")
            last_error = err_msg
            continue

    if response is None:
        with _telemetry_lock:
            if "TimeoutError" in str(last_error):
                _telemetry["timeouts"] += 1
            _telemetry["fallbacks"] += 1
        print(f"[SmartDesk AI] All Gemini models unavailable ({last_error}). Activating automatic rule-based fallback.")
        return rule_based_fallback(title, description, impact, urgency, reason_prefix="[Fallback Engine]")

    try:
        response_text = response.text.strip()
        # Clean any markdown code blocks
        clean_json = re.sub(r"^```(?:json)?\s*", "", response_text, flags=re.MULTILINE)
        clean_json = re.sub(r"\s*```$", "", clean_json, flags=re.MULTILINE).strip()

        data = json.loads(clean_json)

        # Schema Validation
        ticket_type = data.get("ticket_type", "Incident")
        if ticket_type not in VALID_TICKET_TYPES:
            ticket_type = "Incident"

        category = data.get("category", "Other")
        if category not in VALID_CATEGORIES:
            category = "Other"

        raw_priority = data.get("priority", "Medium")
        if raw_priority not in VALID_PRIORITIES:
            raw_priority = "Medium"

        summary = data.get("issue_summary") or title
        raw_reason = data.get("reason_for_priority") or "Determined by ITSM classification guidelines."
        assigned_team = data.get("assigned_support_team") or "Service Desk Tier 1"
        steps = data.get("recommended_troubleshooting_steps")
        if not isinstance(steps, list) or len(steps) == 0:
            steps = ["Check system diagnostics and contact support desk."]
        suggested_resp = data.get("suggested_response_to_employee") or "Your issue has been logged and assigned."

        # Enforce ITIL Guardrail on model output
        guarded_priority, guarded_reason = apply_itil_priority_guardrail(
            title=title,
            description=description,
            impact=impact,
            urgency=urgency,
            candidate_priority=raw_priority,
            reason=raw_reason
        )

        with _telemetry_lock:
            _telemetry["completed"] += 1

        return {
            "ticket_type": ticket_type,
            "issue_summary": summary,
            "category": category,
            "priority": guarded_priority,
            "reason_for_priority": guarded_reason,
            "assigned_support_team": assigned_team,
            "recommended_troubleshooting_steps": steps,
            "suggested_response_to_employee": suggested_resp,
            "analysis_source": "gemini"
        }

    except concurrent.futures.TimeoutError:
        with _telemetry_lock:
            _telemetry["timeouts"] += 1
            _telemetry["fallbacks"] += 1
        print(f"[SmartDesk AI] Gemini analysis timed out promptly after {timeout_seconds} seconds. Returning rule-based fallback without blocking.")
        return rule_based_fallback(title, description, impact, urgency, reason_prefix="[Fallback Engine - Gemini 30s Timeout]")

    except Exception as e:
        with _telemetry_lock:
            _telemetry["fallbacks"] += 1
        api_key = Config.GEMINI_API_KEY or ""
        err_msg = str(e).replace(api_key, "[REDACTED_API_KEY]") if api_key else str(e)
        print(f"[SmartDesk AI] Gemini analysis failed ({err_msg}). Activating automatic deterministic rule-based fallback.")
        return rule_based_fallback(title, description, impact, urgency, reason_prefix="[Fallback Engine - Gemini Offline]")
