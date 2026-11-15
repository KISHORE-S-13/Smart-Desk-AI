import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai

def test_connectivity():
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        print(f"Error: .env file not found at {env_path}")
        return

    load_dotenv(dotenv_path=env_path)

    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

    if not api_key:
        print("Error: GEMINI_API_KEY is missing or empty in .env.")
        return

    print(f"Configuration loaded successfully from: {env_path}")
    print(f"GEMINI_API_KEY: Configured (length: {len(api_key)})")
    print(f"GEMINI_MODEL: {model_name}")

    try:
        client = genai.Client(api_key=api_key)
        prompt = "Classify this IT issue: My office VPN is not connecting."
        print(f"\nSending test prompt to {model_name}...")
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        print("\n--- Response Received ---")
        print(response.text)
    except Exception as e:
        err = str(e).replace(api_key, "[REDACTED_API_KEY]")
        print(f"Failed to generate content: {err}")

if __name__ == "__main__":
    test_connectivity()
