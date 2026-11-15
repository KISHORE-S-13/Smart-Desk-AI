import os
from pathlib import Path
from config import Config
from models import KnowledgeArticle
from database import db
from services.ai_service import get_genai_client

SEED_ARTICLES = [
    {
        "title": "Corporate VPN Troubleshooting Guide",
        "category": "VPN",
        "tags": "vpn, cisco, anyconnect, globalprotect, remote, network, split tunnel",
        "content": (
            "1. Overview: All remote employees must connect to the corporate network via GlobalProtect or Cisco AnyConnect.\n"
            "2. Common Symptoms:\n"
            "   - 'Gateway Unreachable': Ensure your local home Wi-Fi or cellular hotspot has an active internet connection.\n"
            "   - 'Authentication Failed': Ensure you approved the MFA push notification on Duo or Microsoft Authenticator.\n"
            "   - 'Certificate Expired': If your machine certificate has expired, connect via ethernet at an office location or contact IT.\n"
            "3. Troubleshooting Steps:\n"
            "   a. Disconnect the VPN client, wait 10 seconds, and reconnect.\n"
            "   b. Flush DNS: Open Command Prompt as Administrator and run 'ipconfig /flushdns'.\n"
            "   c. Restart the 'PanGPS' or 'Cisco AnyConnect' service in Windows Services (services.msc).\n"
            "   d. If using home mesh Wi-Fi (Eero, Google Nest), disable IPv6 in router settings if connection drops frequently.\n"
            "4. Escalation: If unresolved after 3 attempts, submit a ticket under Category 'Network' with error code and screenshot."
        )
    },
    {
        "title": "Enterprise Wi-Fi (Corp-Secure) Connectivity",
        "category": "Wi-Fi",
        "tags": "wifi, wireless, 802.1x, eduroam, corp-secure, network, ssid",
        "content": (
            "1. SSID Selection:\n"
            "   - 'Corp-Secure': For corporate-managed laptops. Uses 802.1X certificate authentication automatically.\n"
            "   - 'Guest-Access': For visitors and personal mobile devices. Requires SMS/Email self-registration daily.\n"
            "2. Troubleshooting Connection Drops:\n"
            "   a. Forget the network: Windows Settings -> Network & Internet -> Wi-Fi -> Manage Known Networks -> Click 'Forget' on Corp-Secure.\n"
            "   b. Reconnect and choose 'Use my Windows user account'.\n"
            "   c. Check airplane mode switch and hardware wireless toggle.\n"
            "   d. Update Wi-Fi drivers from Enterprise Software Center.\n"
            "3. Static IP Warning: Do not set static IP addresses on corporate Wi-Fi; DHCP must remain enabled."
        )
    },
    {
        "title": "Self-Service Password Reset & Account Lockout",
        "category": "Password Reset",
        "tags": "password, reset, account, locked, sso, mfa, active directory, login",
        "content": (
            "1. Password Policy:\n"
            "   - Minimum 14 characters including uppercase, lowercase, numbers, and special symbols.\n"
            "   - Passwords expire every 90 days. History of last 10 passwords cannot be reused.\n"
            "2. Self-Service Portal: Navigate to https://sso.enterprise.internal/reset from any device with mobile browser.\n"
            "3. Account Lockout Policy:\n"
            "   - After 5 consecutive failed login attempts, accounts lock automatically for 15 minutes.\n"
            "   - Do NOT continue typing passwords during lockout; wait 15 minutes for the lockout counter to reset.\n"
            "4. MFA Issues: If your registered authenticator device is lost, stolen, or reset, contact the Service Desk via phone to verify identity with employee ID and date of birth."
        )
    },
    {
        "title": "Microsoft Outlook & Email Synchronization",
        "category": "Email",
        "tags": "email, outlook, exchange, mailbox, owa, sync, storage, ost",
        "content": (
            "1. Mailbox Storage Limits: Standard employee quota is 50 GB. Warnings are sent at 45 GB.\n"
            "2. Fixing 'Disconnected' or 'Trying to Connect' Status in Outlook:\n"
            "   a. Confirm internet access by browsing to internal portal.\n"
            "   b. Verify access to Outlook Web App (https://outlook.office.com). If OWA works, the server is healthy.\n"
            "   c. Launch Outlook in Safe Mode: Press Windows Key + R, type 'outlook.exe /safe', and hit Enter.\n"
            "   d. Rebuild OST file: File -> Account Settings -> Account Settings -> Data Files -> Open File Location -> Close Outlook and rename .ost to .ost.old.\n"
            "3. Phishing Reports: Forward suspicious emails as attachments to security@smartdesk.ai."
        )
    },
    {
        "title": "Software Installation & License Entitlement",
        "category": "Software Installation",
        "tags": "software, install, company portal, license, admin rights, privileges",
        "content": (
            "1. Approved Software Portal:\n"
            "   - Employees do NOT have standard local administrator privileges.\n"
            "   - All vetted tools (VS Code, Slack, Zoom, Docker Desktop, Chrome, Python) can be installed directly from the 'Company Portal' or 'Software Center' without admin credentials.\n"
            "2. Special Software Requests:\n"
            "   - For paid licenses (e.g. JetBrains, Figma Enterprise, Adobe Creative Cloud), submit a Service Request with manager cost-center approval.\n"
            "3. Temporary Admin Rights:\n"
            "   - Developers needing elevated privileges for local debugging can use the 'Make Me Admin' app for a 30-minute elevated session."
        )
    }
]

def seed_knowledge_base():
    """Seeds default knowledge articles if database is empty."""
    try:
        count = KnowledgeArticle.query.count()
        if count == 0:
            for item in SEED_ARTICLES:
                article = KnowledgeArticle(
                    title=item["title"],
                    category=item["category"],
                    tags=item["tags"],
                    content=item["content"],
                    source="system_seed"
                )
                db.session.add(article)
            db.session.commit()
            print(f"[SmartDesk AI] Seeded {len(SEED_ARTICLES)} initial knowledge base articles.")
    except Exception as e:
        db.session.rollback()
        print(f"[SmartDesk AI] Knowledge base seeding skipped or table not ready: {e}")


def search_knowledge_base(query, limit=3):
    """
    Retrieves the most relevant knowledge articles based on keyword matching across titles, categories, tags, and content.
    """
    query_tokens = [q.lower().strip() for q in query.split() if len(q.strip()) > 2]
    articles = KnowledgeArticle.query.all()
    
    scored = []
    for art in articles:
        score = 0
        text_corpus = f"{art.title} {art.category} {art.tags} {art.content}".lower()
        for token in query_tokens:
            if token in art.title.lower():
                score += 5
            elif token in art.tags.lower():
                score += 4
            elif token in art.category.lower():
                score += 3
            elif token in text_corpus:
                score += 1
        if score > 0:
            scored.append((score, art))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    results = [art for score, art in scored[:limit]]
    
    # If no keyword matches, fallback to first 2 articles for general context
    if not results and articles:
        results = articles[:2]
        
    return results


def answer_support_query(query, chat_history=None):
    """
    RAG generation: retrieves grounded company knowledge and calls Gemini to answer the query.
    Must adhere strictly to retrieved knowledge and never invent company-specific policies.
    """
    matched_articles = search_knowledge_base(query)
    
    knowledge_context = ""
    sources = []
    for art in matched_articles:
        knowledge_context += f"--- Document: {art.title} (Category: {art.category}) ---\n{art.content}\n\n"
        sources.append({"id": art.id, "title": art.title, "category": art.category})

    client = get_genai_client()
    model_name = Config.GEMINI_MODEL or "gemini-3.8-flash"

    if client and Config.GEMINI_API_KEY:
        system_prompt = (
            "You are SmartDesk AI Knowledge Assistant, an enterprise IT support chatbot.\n"
            "Your job is to assist employees with IT queries using ONLY the retrieved company knowledge documents below.\n"
            "CRITICAL RULES:\n"
            "1. Rely strictly on the facts in the provided Knowledge Base.\n"
            "2. Do NOT invent company-specific policies, URLs, or internal systems not mentioned in the context.\n"
            "3. If the knowledge base does not cover the employee's specific situation, state clearly that the specific answer is not in the knowledge repository and advise them to submit a formal IT Incident/Service Request.\n"
            "4. Provide clear, step-by-step troubleshooting instructions formatted nicely in Markdown.\n\n"
            f"=== RETRIEVED COMPANY KNOWLEDGE BASE ===\n{knowledge_context}\n"
            "=== END OF KNOWLEDGE BASE ===\n\n"
            f"Employee Query: {query}"
        )

        from services.ai_service import _ai_executor
        primary_model = Config.GEMINI_MODEL or "gemini-3.8-flash"
        candidate_models = [primary_model]
        if "gemini-3.5-flash" not in candidate_models:
            candidate_models.append("gemini-3.5-flash")

        for m in candidate_models:
            try:
                future = _ai_executor.submit(
                    client.models.generate_content,
                    model=m,
                    contents=system_prompt,
                )
                response = future.result(timeout=30)
                answer_text = response.text.strip()
                return {
                    "answer": answer_text,
                    "sources": sources,
                    "source_type": "gemini_rag"
                }
            except Exception as e:
                api_key = Config.GEMINI_API_KEY or ""
                err_msg = str(e).replace(api_key, "[REDACTED_API_KEY]") if api_key else str(e)
                print(f"[SmartDesk AI] Knowledge assistant model {m} failed: {err_msg[:80]}")
                continue

    # Fallback response grounded directly in retrieved docs
    if matched_articles:
        primary = matched_articles[0]
        fallback_answer = (
            f"### Knowledge Match: {primary.title}\n\n"
            f"{primary.content}\n\n"
            f"> *Note: This response was retrieved directly from the SmartDesk Knowledge Repository (Offline Mode).*"
        )
    else:
        fallback_answer = (
            "I could not find a matching internal IT policy or guide for your request. "
            "Please create a support ticket from your employee dashboard so a service desk engineer can assist you."
        )

    return {
        "answer": fallback_answer,
        "sources": sources,
        "source_type": "local_knowledge_base"
    }


def ingest_pdf_file(file_storage):
    """
    Extracts text from an uploaded PDF file using PyPDF and creates a KnowledgeArticle.
    """
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_storage)
        text_content = ""
        for page_idx, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                text_content += f"\n[Page {page_idx + 1}]\n" + text.strip()

        if not text_content.strip():
            return None, "PDF file appears empty or contains only scanned images without extractable text."

        title = Path(file_storage.filename).stem.replace("_", " ").title()
        
        # Categorize automatically based on content
        content_lower = text_content.lower()
        if "vpn" in content_lower or "network" in content_lower:
            cat = "VPN"
        elif "wifi" in content_lower or "wireless" in content_lower:
            cat = "Wi-Fi"
        elif "password" in content_lower or "mfa" in content_lower or "login" in content_lower:
            cat = "Password Reset"
        elif "outlook" in content_lower or "email" in content_lower:
            cat = "Email"
        elif "install" in content_lower or "software" in content_lower:
            cat = "Software Installation"
        else:
            cat = "General"

        article = KnowledgeArticle(
            title=f"Doc: {title}",
            category=cat,
            tags="uploaded, pdf, documentation",
            content=text_content[:10000], # Store up to 10k chars for knowledge indexing
            source="uploaded_pdf"
        )
        db.session.add(article)
        db.session.commit()
        return article, None
    except Exception as e:
        db.session.rollback()
        return None, str(e)
