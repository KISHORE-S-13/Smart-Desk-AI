import sys
import time
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from config import Config
from google import genai
from google.genai import types

def test_models():
    api_key = Config.GEMINI_API_KEY
    client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=10000))
    models_to_test = ["gemini-3.8-flash", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    
    for m in models_to_test:
        t0 = time.time()
        try:
            resp = client.models.generate_content(
                model=m,
                contents='Return valid JSON: {"reply": "connected"}'
            )
            elapsed = time.time() - t0
            print(f"Model {m}: AVAILABLE! (Response time: {elapsed:.2f}s)")
            print(f"Response: {resp.text.strip()}")
        except Exception as e:
            elapsed = time.time() - t0
            err = str(e).replace(api_key, "[REDACTED_API_KEY]")
            if "RESOURCE_EXHAUSTED" in err:
                code = "429 RESOURCE_EXHAUSTED (Quota Exceeded)"
            elif "503" in err:
                code = "503 UNAVAILABLE (High Demand)"
            elif "404" in err:
                code = "404 NOT FOUND"
            else:
                code = err[:80]
            print(f"Model {m}: FAILED ({code}) in {elapsed:.2f}s")

if __name__ == "__main__":
    test_models()
