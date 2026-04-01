# PR Profile – User Requirements

**Document type:** User Requirements Specification  
**Application:** PR Profile Backend  
**Date:** 2026-03-30  

---

## Table of Contents

1. [Scope](#1-scope)
2. [Actors](#2-actors)
3. [Functional Requirements](#3-functional-requirements)
   - 3.1 [Document Upload](#31-document-upload)
   - 3.2 [Profile Management](#32-profile-management)
   - 3.3 [HTML Report](#33-html-report)
   - 3.4 [Document Processing & Analysis](#34-document-processing--analysis)
   - 3.5 [AI Analysis](#35-ai-analysis)
4. [User Flow](#4-user-flow)
   - 4.1 [Primary Flow – Build a Profile from Scratch](#41-primary-flow--build-a-profile-from-scratch)
   - 4.2 [Incremental Update Flow](#42-incremental-update-flow)
   - 4.3 [Force-Regeneration Flow](#43-force-regeneration-flow)
   - 4.4 [Rename Employee Flow](#44-rename-employee-flow)
5. [How to Use (Endpoint Reference)](#5-how-to-use-endpoint-reference)
   - 5.1 [Upload a Document](#51-upload-a-document)
   - 5.2 [Download the HTML Report](#52-download-the-html-report)
   - 5.3 [List All Profiles](#53-list-all-profiles)
   - 5.4 [Force-Regenerate HTML](#54-force-regenerate-html)
   - 5.5 [Rename an Employee](#55-rename-an-employee)
   - 5.6 [List Uploaded Files](#56-list-uploaded-files)
   - 5.7 [Advanced Endpoints](#57-advanced-endpoints)
6. [Upload Type Reference](#6-upload-type-reference)
7. [HTML Report Sections](#7-html-report-sections)
8. [Restrictions & Limitations](#8-restrictions--limitations)
9. [Configuration Reference](#9-configuration-reference)
10. [Error Reference](#10-error-reference)

---

## 1. Scope

PR Profile is a **REST API backend** that automates the generation of employee performance-review (PR) HTML profiles.

Authorised users upload `.doc` or `.docx` documents (feedback letters, PDPs, project logs, training records, etc.) for a named employee in a given review year. After each upload the system:

1. Extracts plain text from the document.
2. Finds the existing profile for that employee + year, or creates one.
3. Links the new document to the profile.
4. Re-analyses **all** linked documents together.
5. Overwrites the profile's HTML report with the latest consolidated result.

The HTML report is self-contained (no external dependencies) and can be opened in any browser.

**What is in scope:**

- Document upload and text extraction (`.doc` / `.docx`)
- Profile creation and management keyed by employee name + review year
- LLM-powered (OpenAI GPT-4) or pattern-based section extraction
- HTML report generation and storage
- Content-based deduplication of uploaded documents
- Raw document processing and AI skill/achievement analysis endpoints
- Profile renaming

**What is out of scope:**

- User authentication and role-based access (infrastructure exists but is not enforced)
- Email notifications
- Frontend / UI (the API is consumed programmatically or via the Swagger UI)
- PDF document support

---

## 2. Actors

| Actor | Description |
|---|---|
| **HR / Reviewer** | Uploads review documents and downloads finished HTML reports |
| **Manager** | May upload project feedback or client feedback documents |
| **System (automated)** | Calls upload endpoints from a CI pipeline or batch script |
| **Developer** | Configures the server, sets environment variables, calls advanced endpoints |

No login is required at this time. All endpoints are publicly accessible within the configured CORS origins.

---

## 3. Functional Requirements

### 3.1 Document Upload

| ID | Requirement |
|---|---|
| UR-01 | The system MUST accept `.doc` and `.docx` files only. |
| UR-02 | The system MUST reject files larger than **100 MB**. |
| UR-03 | The system MUST reject files with invalid magic bytes (structural corruption). |
| UR-04 | The system MUST reject empty files. |
| UR-05 | Each upload MUST be tagged with an `upload_type` value from the supported list (see §6). |
| UR-06 | Each upload MUST specify the employee's full name (`person_name`) and a four-digit `review_year`. |
| UR-07 | An optional uploader email (`uploaded_by_email`) MAY be provided for audit purposes. |
| UR-08 | After a successful upload the system MUST extract all text from the document and store it in the database. |
| UR-09 | If text extraction fails, the file record is marked `failed` and excluded from report generation; the upload still returns a response rather than crashing. |
| UR-10 | The system MUST compute a SHA-256 hash of the extracted text and reject a duplicate (same content) for the same profile with a `202 Accepted` response and a descriptive message instead of creating a new record. |

### 3.2 Profile Management

| ID | Requirement |
|---|---|
| UR-11 | A **PRProfile** is uniquely identified by `(employee_name, review_year)`. |
| UR-12 | The first upload for a name + year combination MUST create a new profile automatically. |
| UR-13 | Subsequent uploads for the same name + year MUST reuse the existing profile (no duplicates). |
| UR-14 | The system MUST support renaming an employee (updating `employee_name` on the profile). If the target name already exists for that year the two profiles MUST be merged. |
| UR-15 | Users MUST be able to list all profiles, including how many files are linked and whether an HTML report exists. |

### 3.3 HTML Report

| ID | Requirement |
|---|---|
| UR-16 | After every successful upload the system MUST regenerate the HTML report for the affected profile automatically; no separate trigger is required. |
| UR-17 | The HTML report MUST reflect **all** documents currently linked to the profile, not only the most recent upload. |
| UR-18 | The report MUST be self-contained (all CSS inline; no external resources). |
| UR-19 | Users MUST be able to download the report as a file attachment via a GET request. |
| UR-20 | Users MUST be able to force a full regeneration of the HTML at any time without uploading a new document. |
| UR-21 | If a profile has no HTML report yet (e.g., all documents failed extraction) the download endpoint MUST return `404`. |
| UR-22 | Multiple documents of the same `upload_type` for the same profile MUST each produce a separate numbered subsection in the report (e.g., "Client Feedback", "Client Feedback 2"). |

### 3.4 Document Processing & Analysis

| ID | Requirement |
|---|---|
| UR-23 | Users MAY request structured section extraction from any previously uploaded file (`/api/documents/process/{upload_id}`). |
| UR-24 | Users MAY request bulk processing of multiple upload IDs in a single call. |
| UR-25 | Users MAY request extraction of a specific named section from a document. |

### 3.5 AI Analysis

| ID | Requirement |
|---|---|
| UR-26 | When an OpenAI API key is configured the report generation MUST use GPT-4 (or the configured model) for intelligent section extraction and allocation. |
| UR-27 | When no API key is configured the system MUST fall back to pattern-based (keyword/regex) extraction silently—no error is surfaced to the caller. |
| UR-28 | Users MAY request on-demand AI skill and achievement analysis for any uploaded file. |
| UR-29 | Skill analysis MUST return confidence scores and a development recommendations list. |
| UR-30 | Achievement analysis MUST attempt to quantify impact (e.g., percentages, team size). |

---

## 4. User Flow

### 4.1 Primary Flow – Build a Profile from Scratch

```
Actor                               System
─────                               ──────
Prepare .docx document
Upload via POST /api/uploads/doc ──► Validate file (type, size, magic bytes)
 + person_name, review_year             │
 + upload_type                          │
                                   Extract text from document
                                        │
                                   Compute SHA-256 dedup hash
                                        │
                              (new) Create PRProfile(name, year)
                                        │
                                   Save UploadedFile record
                                        │
                                   Collect all files for profile
                                        │
                              LLM or pattern extraction across all files
                                        │
                                   Render self-contained HTML
                                        │
                                   Store HTML in PRProfile
                                        │
◄── SmartUploadResponse ─────────── Return response
 (upload_id, pr_profile_id,
  files_in_profile, html_updated)

Download HTML via
GET /api/profiles/html/{name}/{year} ──► Return HTML file as attachment
```

### 4.2 Incremental Update Flow

Each additional document upload for the **same employee + year** follows the same path, except:

- The existing `PRProfile` is reused (no new profile created).
- The new document and **all previously uploaded documents** are analysed together.
- The `html_report` column is overwritten with the updated report.
- `files_in_profile` in the response reflects the new total.

If the new document's content is identical to an already-linked document the upload is rejected as a duplicate (`202` response) and the HTML is **not** regenerated.

### 4.3 Force-Regeneration Flow

```
POST /api/profiles/html/{person_name}/{year}/regenerate

1. Locate the PRProfile by name + year  →  404 if not found
2. Load all UploadedFile records with extracted_text
3. Run full extraction (LLM or pattern)
4. Overwrite PRProfile.html_report
5. Return confirmation JSON
```

Use this when you have manually corrected the database, changed the AI model, or updated the prompt—without uploading a new document.

### 4.4 Rename Employee Flow

```
POST /api/profiles/html/{person_name}/{year}/rename
Body: {"new_name": "Alice Smith"}

• If no profile exists for (new_name, year):
    → Rename employee_name in PRProfile; return updated profile details.
• If a profile already exists for (new_name, year):
    → Merge: move all UploadedFile records to the target profile,
      delete the old profile, regenerate HTML for the merged profile.
```

---

## 5. How to Use (Endpoint Reference)

The API base URL is `http://localhost:8000`.  
Interactive documentation (Swagger UI) is available at `http://localhost:8000/docs`.

---

### 5.1 Upload a Document

```
POST /api/uploads/doc
Content-Type: multipart/form-data
```

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | file | ✓ | `.doc` or `.docx` document |
| `upload_type` | string | ✓ | See §6 for valid values |
| `person_name` | string | ✓ | Employee full name, e.g. `Emma Laurent` |
| `review_year` | integer | ✓ | Four-digit year, e.g. `2025` |
| `uploaded_by_email` | string | | Uploader's email (audit trail only) |

**curl:**
```bash
curl -X POST http://localhost:8000/api/uploads/doc \
  -F "file=@Emma_Laurent_PDP_2025.docx" \
  -F "upload_type=pdp" \
  -F "person_name=Emma Laurent" \
  -F "review_year=2025"
```

**Python:**
```python
import requests

with open("Emma_Laurent_PDP_2025.docx", "rb") as f:
    r = requests.post(
        "http://localhost:8000/api/uploads/doc",
        files={"file": ("PDP.docx", f)},
        data={"upload_type": "pdp", "person_name": "Emma Laurent", "review_year": 2025},
    )
print(r.json())
```

**Success response (201):**
```json
{
  "upload_id": 1,
  "pr_profile_id": 1,
  "employee_name": "Emma Laurent",
  "review_year": 2025,
  "files_in_profile": 1,
  "html_updated": true,
  "message": "Uploaded 'PDP.docx' for Emma Laurent (2025). HTML profile updated."
}
```

**Duplicate response (202):**
```json
{
  "upload_id": null,
  "pr_profile_id": 1,
  "employee_name": "Emma Laurent",
  "review_year": 2025,
  "files_in_profile": 1,
  "html_updated": false,
  "message": "Duplicate document: identical content already exists in this profile. Skipped."
}
```

---

### 5.2 Download the HTML Report

```
GET /api/profiles/html/{person_name}/{year}
```

- `person_name`: URL-encode spaces as `%20`
- Returns the file as a downloadable attachment (`Content-Disposition: attachment`)

**curl:**
```bash
curl "http://localhost:8000/api/profiles/html/Emma%20Laurent/2025" \
  -o "Emma_Laurent_2025_PR.html"
```

**Browser:** Open `http://localhost:8000/api/profiles/html/Emma%20Laurent/2025` directly — the browser will prompt to save the file.

**Python:**
```python
r = requests.get("http://localhost:8000/api/profiles/html/Emma%20Laurent/2025")
with open("Emma_Laurent_2025_PR.html", "wb") as f:
    f.write(r.content)
```

Returns `404` if the profile does not exist or has no HTML report yet.

---

### 5.3 List All Profiles

```
GET /api/profiles/
```

**Response:**
```json
[
  {
    "id": 1,
    "employee_name": "Emma Laurent",
    "year": 2025,
    "has_html": true,
    "files": 3
  }
]
```

---

### 5.4 Force-Regenerate HTML

```
POST /api/profiles/html/{person_name}/{year}/regenerate
```

No request body. Triggers full re-analysis and overwrites the stored HTML.

**Response:**
```json
{
  "employee_name": "Emma Laurent",
  "year": 2025,
  "html_updated": true,
  "files_processed": 3,
  "message": "HTML report regenerated successfully from 3 file(s)."
}
```

---

### 5.5 Rename an Employee

```
POST /api/profiles/html/{person_name}/{year}/rename
Content-Type: application/json
```

**Body:**
```json
{ "new_name": "Emma L. Laurent" }
```

If another profile exists for `(new_name, year)` the two profiles are automatically merged and the HTML is regenerated.

---

### 5.6 List Uploaded Files

```
GET /api/uploads/files?skip=0&limit=10&pr_profile_id=1&status=completed
```

| Parameter | Type | Description |
|---|---|---|
| `skip` | int | Pagination offset (default 0) |
| `limit` | int | Page size (default 10) |
| `pr_profile_id` | int | Filter by profile ID (optional) |
| `status` | string | Filter by status: `pending`, `processing`, `completed`, `failed` (optional) |

---

### 5.7 Advanced Endpoints

These endpoints are intended for developers and integrations needing lower-level control.

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/uploads/doc-and-process` | Upload + extract sections in one call |
| `POST` | `/api/uploads/doc-and-process-and-analyze` | Upload + extract + AI skill/achievement analysis |
| `POST` | `/api/documents/process/{upload_id}` | Re-process a specific upload |
| `POST` | `/api/documents/bulk-process` | Process multiple uploads at once |
| `GET` | `/api/documents/extract-section` | Extract a specific section from a document |
| `POST` | `/api/profiles/consolidate` | Build structured JSON from selected upload IDs |
| `GET` | `/api/profiles/consolidate/by-profile/{pr_profile_id}` | Consolidate all uploads for a profile |
| `POST` | `/api/profiles/report` | Generate HTML from selected upload IDs (without storing) |
| `GET` | `/api/profiles/report/by-profile/{pr_profile_id}` | Generate HTML for all uploads in a profile |
| `POST` | `/api/ai/analyze/{upload_id}` | AI analysis for a single upload |
| `POST` | `/api/ai/bulk-analyze` | AI analysis for multiple uploads |
| `GET` | `/api/ai/skills/{upload_id}` | Get identified skills (filterable) |
| `GET` | `/api/ai/achievements/{upload_id}` | Get identified achievements |
| `GET` | `/api/ai/recommendations/{upload_id}` | Get development recommendations |

---

## 6. Upload Type Reference

| Value | Meaning | Typical document |
|---|---|---|
| `company_function` | Feedback from company-wide function or committee | Cross-functional initiative review, committee assessment |
| `auto_feedback` | Self-assessment / automated feedback | Employee self-evaluation form |
| `project_feedback` | Feedback tied to a specific project | End-of-project review, internal project assessment |
| `client_feedback` | Feedback from an external client | Client satisfaction letter, partner review |
| `additional_feedback` | Any other feedback source | Ad-hoc peer feedback, miscellaneous |
| `pdp` | Personal Development Plan | Learning goals, career objectives, planned certifications |
| `trainings` | Training / certification records | Completed course certificates, attendance records |
| `project_activity` | Project description or activity log | Project brief, role description, deliverables list |

**Rules:**
- The value must be one of the above strings exactly (case-sensitive).
- Multiple documents with the same `upload_type` for the same profile are all accepted; each appears as a numbered subsection in the report (e.g., "Client Feedback", "Client Feedback 2", "Client Feedback 3").

---

## 7. HTML Report Sections

The generated report is structured as follows. Every section draws from **all** linked documents regardless of `upload_type`.

| Section | What it contains |
|---|---|
| **Skills Summary** | Technical languages, domain expertise, automation/tooling, practices |
| **Certifications** | Certificates listed, pursued, or mentioned across all documents |
| **Learning** | Courses and training items, grouped by year |
| **Feedback** | One subsection per upload (labelled by type and numbered if multiple); contains quotes and paraphrased observations |
| **Areas for Improvement** | Development gaps from PDPs, feedback notes, and self-assessments |
| **Activity** | Projects and initiatives extracted from project docs and inferred from feedback |

The report layout mimics a two-panel documentation layout (fixed table-of-contents on the left, content on the right) and contains only inline CSS—no external stylesheets or scripts.

---

## 8. Restrictions & Limitations

### File Restrictions

| Restriction | Detail |
|---|---|
| **Allowed formats** | `.doc` and `.docx` only. PDF, Excel, plain text, etc. are rejected. |
| **Maximum file size** | 100 MB per file. |
| **Minimum file content** | Empty files are rejected. |
| **Structural validity** | The file's magic bytes must match the declared extension. A renamed PDF with a `.docx` extension will be rejected. |
| **Filename length** | Sanitised filename is capped at 200 characters. |

### Profile & Upload Restrictions

| Restriction | Detail |
|---|---|
| **Profile key** | `(employee_name, review_year)` must be unique. The name is treated as a case-sensitive string—`"Emma Laurent"` and `"emma laurent"` would create separate profiles. |
| **Duplicate content** | A document whose extracted text is byte-for-byte identical to an already-linked document will be rejected as a duplicate (202 status). Only the text content matters; a re-saved file with a different name but the same text is still a duplicate. |
| **Year format** | `review_year` must be a four-digit integer (e.g., `2025`). |
| **Upload type** | Must be one of the eight valid values listed in §6. An invalid value returns a validation error. |

### Report Restrictions

| Restriction | Detail |
|---|---|
| **Report availability** | The HTML report endpoint returns 404 until at least one document has been successfully uploaded and processed for that profile. |
| **LLM dependency** | Without an `OPENAI_API_KEY` the system uses keyword/regex patterns, which may produce less complete or less accurate section extraction. |
| **Language** | The extraction prompts and patterns are optimised for English-language documents. Non-English content may yield incomplete results. |
| **Report storage** | The HTML is stored as text in the database, not on the filesystem. It is overwritten on every regeneration. There is no version history. |

### Network & Access Restrictions

| Restriction | Detail |
|---|---|
| **Authentication** | No authentication is enforced. All endpoints are open. Do not expose this service to the public internet without adding an authentication layer. |
| **CORS** | Allowed origins are `localhost:3000`, `localhost:5173`, `localhost:8000`, and any `localhost:*` origin. Cross-origin requests from other domains are blocked by default. |
| **Content size** | Very large documents (close to 100 MB) may consume significant memory during text extraction and LLM analysis. |

### Known Discrepancies / Technical Notes

- The `config.py` setting `max_file_size = 50` (MB) is overridden by the constant `MAX_FILE_SIZE_MB = 100` in `constants.py`. The effective limit is **100 MB**.
- The `allowed_file_types = ["pdf"]` in `config.py` is unused; the actual validation always enforces `.doc` / `.docx`.
- The `secret_key` default value (`"your-secret-key-change-in-production"`) must be replaced in any non-local deployment.
- The `self_feedback` upload type is accepted for backward compatibility but is deprecated in favour of `auto_feedback`.

---

## 9. Configuration Reference

Create a `.env` file in the project root to override defaults.

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | *(unset)* | Enables LLM-powered extraction. Without it, pattern-based fallback is used. |
| `AI_MODEL` | `gpt-4` | OpenAI model identifier. |
| `DATABASE_URL` | `sqlite:///./pr_profile.db` | SQLAlchemy connection string. Switch to PostgreSQL for production. |
| `DEBUG` | `false` | Enables FastAPI debug mode. Do not use in production. |
| `SECRET_KEY` | `your-secret-key-change-in-production` | Used for JWT signing. **Must be changed** before any deployment. |

**Minimal `.env` for LLM-powered reports:**
```env
OPENAI_API_KEY=sk-...
AI_MODEL=gpt-4o
DATABASE_URL=sqlite:///./pr_profile.db
SECRET_KEY=<random-256-bit-hex>
```

**PostgreSQL example:**
```env
DATABASE_URL=postgresql+psycopg2://user:password@localhost/pr_profile
```

---

## 10. Error Reference

| HTTP Status | Condition | Typical message |
|---|---|---|
| 400 | Invalid file extension | `Only .doc and .docx files are allowed` |
| 400 | File too large | `File size exceeds 100MB limit` |
| 400 | Empty file | `Uploaded file is empty` |
| 400 | Invalid magic bytes | `File does not appear to be a valid .docx document` |
| 400 | Missing required field | Pydantic validation error detail |
| 202 | Duplicate content | `Duplicate document: identical content already exists in this profile. Skipped.` |
| 404 | Profile not found | `No profile found for 'Emma Laurent' (2025)` |
| 404 | Upload ID not found | `Upload not found` |
| 404 | No HTML report yet | `No HTML report available for this profile` |
| 422 | Text extraction failed | `Could not extract text from document` |
| 422 | Document parsing error | `DocumentProcessingError: ...` |
| 500 | Report generation error | `Report generation failed: ...` |
| 500 | Database error | `Internal server error` |

Internal exception details (stack traces) are never returned to the caller; they are logged server-side only.
