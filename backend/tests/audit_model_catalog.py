import sys
import time
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from config import Config
from google import genai
from google.genai import types

def audit_catalog_and_test_models():
    api_key = Config.GEMINI_API_KEY
    client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=15000))
    
    print("\n--- 1. GOOGLE GEMINI MODEL CATALOG AUDIT ---")
    models = list(client.models.list())
    print(f"Total available models: {len(models)}")
    
    flash_models = []
    for m in models:
        name = m.name.replace("models/", "")
        display = getattr(m, "display_name", "")
        desc = getattr(m, "description", "")
        if "flash" in name:
            flash_models.append((name, display))
            print(f"  • {name} [{display}]")

    print("\n--- 2. INDEPENDENT TESTING: PRIMARY MODEL (gemini-3.8-flash) ---")
    t0 = time.time()
    try:
        r1 = client.models.generate_content(
            model="gemini-3.8-flash",
            contents="Respond with JSON: {\"test\": \"primary_ping\"}"
        )
        elapsed1 = time.time() - t0
        print(f"Primary gemini-3.8-flash SUCCESS in {elapsed1:.2f}s:")
        print(f"Response: {r1.text.strip()[:120]}")
    except Exception as e:
        elapsed1 = time.time() - t0
        err = str(e).replace(api_key, "[REDACTED_API_KEY]")
        print(f"Primary gemini-3.8-flash returned exception in {elapsed1:.2f}s:")
        print(f"Details: {err}")

    print("\n--- 3. INDEPENDENT TESTING: BACKUP MODEL (gemini-3.5-flash) ---")
    t0 = time.time()
    try:
        r2 = client.models.generate_content(
            model="gemini-3.5-flash",
            contents="Respond with JSON: {\"test\": \"backup_ping\"}"
        )
        elapsed2 = time.time() - t0
        print(f"Backup gemini-3.5-flash SUCCESS in {elapsed2:.2f}s:")
        print(f"Response: {r2.text.strip()[:120]}")
    except Exception as e:
        elapsed2 = time.time() - t0
        err = str(e).replace(api_key, "[REDACTED_API_KEY]")
        print(f"Backup gemini-3.5-flash returned exception in {elapsed2:.2f}s:")
        print(f"Details: {err}")

if __name__ == "__main__":
    audit_catalog_and_test_models()
