import requests, json, sys

# Test: simulate what a browser sends when files are selected but upload_types is provided as text
with open("test_docs/Emma_Laurent_Company_Function_Feedback_2025.docx", "rb") as f:
    docx1 = f.read()
with open("test_docs/Emma_Laurent_Auto_Feedback_2025.docx", "rb") as f:
    docx2 = f.read()

# Test correct payload
files_payload = [
    ("files", ("Company_Function.docx", docx1, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
    ("files", ("Auto_Feedback.docx", docx2, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
]
data = {"upload_types": json.dumps(["company_function", "auto_feedback"])}
r = requests.post("http://127.0.0.1:8000/api/uploads/bulk-upload", files=files_payload, data=data)
print("Correct payload - Status:", r.status_code)
print("Response:", r.text[:300])
print()

# Test: files sent as data (form fields), not as file uploads 
data_wrong = {
    "upload_types": json.dumps(["company_function", "auto_feedback"]),
    "files": docx1,  # binary as regular form field
}
r2 = requests.post("http://127.0.0.1:8000/api/uploads/bulk-upload", data=data_wrong)
print("Files as form data (wrong) - Status:", r2.status_code)
print("Response:", r2.text[:500])
