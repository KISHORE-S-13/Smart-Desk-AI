import sys
import json
import urllib.request
from pathlib import Path
from io import BytesIO

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

def make_test_pdf():
    # Construct a valid PDF with extractable text stream
    content = (
        b"%PDF-1.4\n"
        b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
        b"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
        b"3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R>> endobj\n"
        b"4 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>> endobj\n"
        b"5 0 obj <</Length 160>> stream\n"
        b"BT\n"
        b"/F1 12 Tf\n"
        b"72 712 Td\n"
        b"(SmartDesk Enterprise VPN SOP: For split tunneling, enable route 10.0.0.0/8 in AnyConnect preferences.) Tj\n"
        b"ET\n"
        b"endstream\n"
        b"endobj\n"
        b"xref\n"
        b"0 6\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000056 00000 n \n"
        b"0000000111 00000 n \n"
        b"0000000212 00000 n \n"
        b"0000000281 00000 n \n"
        b"trailer <</Size 6 /Root 1 0 R>>\n"
        b"startxref\n"
        b"492\n"
        b"%%EOF\n"
    )
    return content

def test_upload():
    base_url = "http://127.0.0.1:5000/api"

    print("\n--- 1. Admin Authentication ---")
    login_data = json.dumps({"email": "admin@smartdesk.ai", "password": "Admin@123"}).encode()
    req = urllib.request.Request(f"{base_url}/login", data=login_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        adm_token = json.loads(r.read().decode())["token"]
        print("Admin token acquired.")

    print("\n--- 2. Uploading PDF via POST /api/knowledge/upload ---")
    pdf_bytes = make_test_pdf()
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="VPN_Split_Tunnel_Policy.pdf"\r\n'
        f"Content-Type: application/pdf\r\n\r\n"
    ).encode() + pdf_bytes + f"\r\n--{boundary}--\r\n".encode()

    upload_req = urllib.request.Request(
        f"{base_url}/knowledge/upload",
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Authorization": f"Bearer {adm_token}"
        }
    )

    with urllib.request.urlopen(upload_req) as r:
        res = json.loads(r.read().decode())
        print(f"Status Code: {r.getcode()}")
        print("Upload Response Message:", res.get("message"))
        article = res.get("article", {})
        print(f"Indexed Article Title: {article.get('title')}")
        print(f"Category: {article.get('category')}")
        print(f"Source: {article.get('source')}")
        print(f"Content Preview: {article.get('content')[:100]}...")
        assert article.get("source") == "uploaded_pdf"

    print("\n--- 3. Verifying Article in GET /api/knowledge/articles ---")
    req_list = urllib.request.Request(f"{base_url}/knowledge/articles", headers={"Authorization": f"Bearer {adm_token}"})
    with urllib.request.urlopen(req_list) as r:
        list_data = json.loads(r.read().decode())
        print(f"Total Knowledge Articles Indexed: {list_data['total']}")
        found = any(a["title"] == article["title"] for a in list_data["articles"])
        assert found, "Uploaded article not found in knowledge list!"
        print(">> PDF INGESTION & RAG STORAGE VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    test_upload()
