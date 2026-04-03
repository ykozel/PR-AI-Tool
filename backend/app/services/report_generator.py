"""HTML performance-review report generator.

The generator:
1. Combines raw text from all uploaded documents (labelled by type).
2. Uses an LLM (OpenAI) to intelligently allocate content into the correct
   PR sections when an API key is configured.
3. Falls back to the pattern-based ProfileConsolidator when no key is set.
4. Renders a fully self-contained, downloadable HTML file that matches the
   reference layout (stackedit two-panel design).
"""
import html as _html_lib
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.services.profile_consolidator import ProfileConsolidator

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Embedded CSS – mirrors the stackedit two-panel layout
# ---------------------------------------------------------------------------
_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: "Lato", "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 15px;
  line-height: 1.7;
  color: #333;
  display: flex;
  min-height: 100vh;
}
a { color: #4183c4; text-decoration: none; }
a:hover { text-decoration: underline; }

/* ── Left TOC panel ── */
.stackedit__left {
  position: fixed;
  top: 0; left: 0; bottom: 0;
  width: 260px;
  overflow-y: auto;
  background: #f7f7f7;
  border-right: 1px solid #e8e8e8;
  padding: 28px 18px;
}
.stackedit__toc ul { list-style: none; padding: 0; }
.stackedit__toc > ul > li { margin-bottom: 14px; }
.stackedit__toc > ul > li > a { font-size: 15px; font-weight: 700; color: #2c3e50; }
.stackedit__toc ul ul { padding-left: 14px; margin-top: 6px; }
.stackedit__toc ul ul li { margin-bottom: 5px; }
.stackedit__toc ul ul li a { font-size: 13px; color: #666; }

/* ── Right content panel ── */
.stackedit__right { margin-left: 260px; width: 100%; }
.stackedit__html { max-width: 780px; padding: 48px 56px 96px; }

h1 {
  font-size: 2em; font-weight: 700;
  margin-bottom: 10px;
  border-bottom: 2px solid #eaecef; padding-bottom: 14px;
  color: #2c3e50;
}
h2 {
  font-size: 1.25em; font-weight: 700;
  margin-top: 36px; margin-bottom: 14px;
  color: #2c3e50;
  border-bottom: 1px solid #eaecef; padding-bottom: 8px;
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
}
h3 {
  font-size: 1.05em; font-weight: 600;
  margin-top: 22px; margin-bottom: 10px;
  color: #555;
}
p { margin-bottom: 14px; }
ul { margin: 8px 0 14px 26px; }
li { margin-bottom: 5px; }
blockquote {
  border-left: 4px solid #dfe2e5;
  padding: 10px 18px; margin: 14px 0;
  color: #6a737d; background: #fafbfc;
  border-radius: 0 4px 4px 0;
}
blockquote p { margin: 0; font-style: italic; }

/* ── Feedback section ── */
.feedback-quote {
  border-left: 4px solid #4183c4;
  background: #eef4fb;
  padding: 12px 20px;
  margin: 12px 0;
  border-radius: 0 6px 6px 0;
  color: #1a3a5c;
}
.feedback-quote p {
  margin: 0;
  line-height: 1.65;
}

.improvement-note {
  border-left: 4px solid #a0bbd8;
  background: #f4f8fd;
  padding: 10px 18px;
  margin: 10px 0;
  border-radius: 0 6px 6px 0;
  color: #2c4a6a;
}
.improvement-note p { margin: 0; line-height: 1.6; }
strong { font-weight: 700; }

/* ── Year navigation ── */
.year-navigation {
  background: #f0f5ff;
  border: 1px solid #d4e3ff;
  border-radius: 4px;
  padding: 16px;
  margin-bottom: 24px;
  font-size: 14px;
}
.year-navigation-title {
  font-weight: 700;
  color: #2c3e50;
  margin-bottom: 10px;
  font-size: 14px;
}
.year-links {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
}
.year-link {
  display: inline-block;
  padding: 6px 12px;
  background: white;
  border: 1px solid #d4e3ff;
  border-radius: 3px;
  color: #4183c4;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.2s;
}
.year-link:hover {
  background: #4183c4;
  color: white;
  text-decoration: none;
}
.year-link.current {
  background: #4183c4;
  color: white;
  border-color: #4183c4;
  cursor: default;
}
.year-separator {
  color: #999;
  margin: 0 4px;
}

/* ── Year-over-Year Analysis Section ── */
#achievements-yoy {
  border-top: 3px solid #28a745;
  padding-top: 24px;
  margin-top: 48px;
}
#achievements-yoy blockquote {
  border-left: 4px solid #28a745;
  background: #f0fdf4;
  color: #1a5a2a;
}
#achievements-yoy h3 {
  color: #1a5a2a;
  margin-top: 20px;
}
#achievements-yoy ul {
  margin-left: 26px;
}
#achievements-yoy li {
  margin-bottom: 8px;
  line-height: 1.65;
}

/* ── Areas for Improvement Section ── */
#areas-for-improvement-yoy {
  border-top: 3px solid #fd7e14;
  padding-top: 24px;
  margin-top: 48px;
  background: #fffbf5;
  padding-left: 20px;
  padding-right: 20px;
  padding-bottom: 20px;
  margin-left: -20px;
  margin-right: -20px;
  border-left: 4px solid #fd7e14;
}
#areas-for-improvement-yoy blockquote {
  border-left: 4px solid #fd7e14;
  background: #fff3e0;
  color: #6b4423;
}
#areas-for-improvement-yoy h3 {
  color: #6b4423;
  margin-top: 20px;
}
#areas-for-improvement-yoy ul {
  margin-left: 26px;
}
#areas-for-improvement-yoy li {
  margin-bottom: 8px;
  line-height: 1.65;
  color: #5a3a1a;
}
#areas-for-improvement-yoy h2 {
  color: #fd7e14;
  border-bottom-color: #fd7e14;
}

/* ── Achievements section ── */
#achievements {
  border-top: 3px solid #0d7a5f;
  padding-top: 24px;
  margin-top: 48px;
}
#achievements h2 { color: #0d7a5f; border-bottom-color: #0d7a5f; }
#achievements blockquote {
  border-left: 4px solid #0d7a5f;
  background: #f0fdf8;
  color: #065042;
}
#achievements blockquote p { color: #065042; }
#achievements ul { margin-left: 26px; }
#achievements li { margin-bottom: 8px; line-height: 1.65; color: #065042; }

/* ── Fallbacks section ── */
#fallbacks {
  border-top: 3px solid #c47d00;
  padding-top: 24px;
  margin-top: 48px;
  background: #fffcf0;
  padding-left: 20px;
  padding-right: 20px;
  padding-bottom: 20px;
  margin-left: -20px;
  margin-right: -20px;
  border-left: 4px solid #c47d00;
}
#fallbacks h2 { color: #c47d00; border-bottom-color: #c47d00; }
#fallbacks ul { margin-left: 26px; }
#fallbacks li { margin-bottom: 8px; line-height: 1.65; color: #5a3e00; }

/* ── Verbatim feedback blocks ── */
.feedback-block {
  background: #f8f9fb;
  border: 1px solid #e4e8ed;
  border-radius: 6px;
  padding: 18px 24px 10px;
  margin: 10px 0 24px;
}
/* Engagement/project metadata: compact definition list */
.fb-meta { display: grid; grid-template-columns: max-content 1fr; gap: 2px 12px; margin: 0 0 12px; font-size: 0.9em; color: #555; }
.fb-meta dt { font-weight: 600; color: #444; white-space: nowrap; }
.fb-meta dd { margin: 0; color: #555; }
/* Section headings inside a feedback block */
h4.fb-heading {
  font-size: 0.95em; font-weight: 700; color: #2c3e50;
  margin: 16px 0 8px; padding-bottom: 4px;
  border-bottom: 1px solid #e4e8ed;
}
h4.fb-heading:first-child { margin-top: 0; }
/* Satisfaction ratings list */
.fb-ratings { list-style: none; margin: 4px 0 12px; padding: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 4px 16px; }
.fb-ratings li { font-size: 0.92em; color: #444; padding: 3px 0; border-bottom: 1px dotted #e0e0e0; }
/* Attributed quote block */
.fb-attr {
  border-left: 3px solid #4183c4;
  background: #f0f5fb;
  border-radius: 0 4px 4px 0;
  padding: 10px 16px;
  margin: 10px 0;
}
.fb-attr-who { display: block; font-size: 0.85em; font-weight: 700; color: #4183c4; margin-bottom: 4px; }
.fb-attr p { margin: 0; color: #1a3a5c; line-height: 1.65; font-style: normal; }
.fb-attr p::before, .fb-attr p::after { content: none; }
/* Plain paragraph text inside feedback block */
p.fb-text { margin-bottom: 10px; color: #333; line-height: 1.7; }

/* ── Section origin badges ── */
.badge-ai, .badge-verbatim {
  font-size: 0.58em; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;
  padding: 2px 10px; border-radius: 10px; white-space: nowrap; flex-shrink: 0;
}
.badge-ai   { color: #1848b3; background: #eaf1ff; border: 1px solid #c2d6f8; }
.badge-verbatim { color: #1a6b3c; background: #eaf4ee; border: 1px solid #b0d9be; }
"""

# ---------------------------------------------------------------------------
# LLM prompt templates
# ---------------------------------------------------------------------------
_LLM_SYSTEM = (
    "You are a precise information extractor for HR documents. "
    "Return ONLY a valid JSON object – no markdown, no code fences, no explanation."
)

_LLM_PROMPT = """You are a senior HR analyst extracting structured performance-review data.

Employee name: {employee_name}
Review year: {year}

SCAN ALL DOCUMENTS — skills, learning, and activity may appear in any document type.

Return ONLY a valid JSON object with this exact structure:
{{
  "skills_summary": {{
    "languages": ["Language (proficiency level)"],
    "qa_qm_expertise": ["QA/QM methodology, domain knowledge, or testing expertise"],
    "automation_technical": ["Automation tool, DevOps technology, engineering skill, or cloud platform"],
    "practices_tools": ["Practice, methodology, reporting tool, dashboard, or test management tool"]
  }},
  "certifications": ["Certification or accreditation name — NOT document headers or section titles"],
  "learning": {{
    "2025": ["Course, training, workshop, or self-study item completed or planned"],
    "2026": ["Learning item planned for 2026"]
  }},
  "achievements": {{
    "summary": "2\u20133 sentence narrative of the person's key achievements and impact this review period",
    "highlights": [
      "Concrete achievement with numbers or metrics where available"
    ]
  }},
  "fallbacks": [
    "Development area, growth suggestion, or improvement noted in any document"
  ],
  "activity": [
    {{
      "year": {year},
      "title": "Project, initiative, or engagement name",
      "description": "2\u20133 sentence description of the work performed",
      "contributions": ["Key contribution, outcome, or achievement"],
      "type": "project"
    }}
  ]
}}

Extraction rules:
- skills_summary: SCAN ALL DOCUMENTS — extract tools, technologies, methodologies from feedback docs, PDPs, project docs, everything
- learning: SCAN ALL DOCUMENTS — extract courses, certifications pursued, training from any source; group by year; only include years with actual content
- activity: SCAN ALL DOCUMENTS — one entry per distinct project/initiative; include work described in feedback docs and PDPs
- achievements.summary: synthesise the person's main impact in 2\u20133 sentences from ALL documents
- achievements.highlights: specific, concrete achievements (quantified where possible) from ANY document
- fallbacks: collect ALL improvement suggestions, development gaps, growth areas from EVERY document
- certifications: ONLY actual certification names/abbreviations (e.g. 'ISTQB Advanced', 'AWS Certified Solutions Architect'); return empty list if none found
- Keep list items concise (one line, no trailing period)
- Do not invent content — extract only what is explicitly stated

DOCUMENTS:
{combined_text}"""


# ---------------------------------------------------------------------------
# Feedback type metadata
# ---------------------------------------------------------------------------

# Upload types that are rendered as feedback subsections (order controls display order)
_FEEDBACK_TYPE_ORDER = [
    "company_function",
    "auto_feedback",
    "project_feedback",
    "client_feedback",
    "additional_feedback",
]

_FEEDBACK_TYPES = set(_FEEDBACK_TYPE_ORDER)

_FEEDBACK_LABELS: Dict[str, str] = {
    "company_function": "Company Function Feedback",
    "auto_feedback": "Auto Feedback",
    "project_feedback": "Project Feedback",
    "client_feedback": "Client Feedback",
    "additional_feedback": "Additional Feedback",
}

# Base feedback types (without numbering suffix) in display order
_FEEDBACK_BASE_ORDER = list(_FEEDBACK_TYPE_ORDER)


def _feedback_label(key: str) -> str:
    """Convert a feedback_by_type key to a human-readable label.
    Handles both bare keys ('client_feedback') and numbered ones ('client_feedback_2').
    """
    import re as _re
    m = _re.match(r'^(.+?)(?:_(\d+))?$', key)
    if m:
        base, num = m.group(1), m.group(2)
        base_label = _FEEDBACK_LABELS.get(base, base.replace("_", " ").title())
        if num:
            return f"{base_label} {num}"
        return base_label
    return key.replace("_", " ").title()


def _ordered_feedback_keys(feedback_by_type: Dict[str, Any]) -> List[str]:
    """Return feedback keys in a stable display order:
    base types first (in _FEEDBACK_BASE_ORDER order), then numbered variants
    of each, then any unknown types alphabetically.
    """
    import re as _re
    result: List[str] = []
    seen = set()
    # First pass: known base types + their numbered variants
    for base in _FEEDBACK_BASE_ORDER:
        variants = sorted(
            [
                k for k in feedback_by_type
                if _re.match(rf'^{_re.escape(base)}(?:_\d+)?$', k)
            ],
            key=lambda k: int(_re.search(r'_(\d+)$', k).group(1)) if _re.search(r'_(\d+)$', k) else 0,
        )
        for v in variants:
            if v not in seen:
                result.append(v)
                seen.add(v)
    # Second pass: any remaining unknown keys
    for k in sorted(feedback_by_type):
        if k not in seen:
            result.append(k)
    return result


def _extract_feedback_lines(text: str) -> List[str]:
    """Extract non-trivial lines from a feedback document's raw text."""
    lines = []
    for raw in text.splitlines():
        clean = re.sub(r"^[\s\-•*▪·]+", "", raw).strip()
        if clean and len(clean) > 15 and _is_clean_item(clean):
            lines.append(clean)
    return lines


# Patterns that identify raw form/table artefacts that should never surface in the report
_FORM_JUNK_RE = re.compile(
    r"""(
        \[[ X]\]                       (?# checkbox markers [ ] or [X])
      | \|                             (?# table-cell pipes)
      | If\ you\ have\ additional      (?# form comment prompt)
      | ^Department:\s                 (?# table label)
      | ^Review\ Date:\s               (?# table label)
      | ^Period:\s                     (?# table label)
      | ^Employee\ (?:Name|ID)         (?# table label)
      | ^Line\ Manager:\s              (?# table label)
      | ^HR\ Partner:\s                (?# table label)
      | ^Sign-Off\b                    (?# section heading artefact)
    )""",
    re.VERBOSE | re.IGNORECASE | re.MULTILINE,
)

# Numbered form-question pattern (e.g. "15. QA Strategy and QA process*")
_NUMBERED_QUESTION_RE = re.compile(r"^\d{1,2}\.\s.{3,}\*\s*$", re.MULTILINE)


def _is_clean_item(text: str) -> bool:
    """Return True when a line is genuine content (not a form/table artefact)."""
    # Reject section-type markers such as [CLIENT FEEDBACK] or [CLIENT FEEDBACK] QA ...
    if text.lstrip().startswith("["):
        return False
    return not bool(_FORM_JUNK_RE.search(text)) and not bool(_NUMBERED_QUESTION_RE.match(text))


def _clean_items(items: List[str], max_len: int = 180) -> List[str]:
    """Filter and truncate a list of extracted strings for display."""
    result = []
    seen: set = set()
    for raw in items:
        item = raw.strip()
        if not item or not _is_clean_item(item):
            continue
        # Skip items that are whole paragraphs (multiple complete sentences)
        if len(item) > max_len:
            continue
        key = item.lower()
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def _parse_cert_text(text: str) -> List[str]:
    """Split a raw certification text into display-ready lines."""
    # Semi-colon delimited (pattern extractor joined them that way)
    parts = [p.strip() for p in re.split(r";\s*", text) if p.strip()]
    # Drop generic header words
    skip = {"certifications and qualifications", "planned certifications (2026)",
            "planned certifications (2025)", "certifications"}
    return [p for p in parts if p.lower() not in skip and _is_clean_item(p)]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slug(text: str) -> str:
    return _SLUG_RE.sub("-", text.lower()).strip("-")


def _esc(text: Any) -> str:
    """HTML-escape a value."""
    return _html_lib.escape(str(text), quote=False)


def _as_str_list(value: Any) -> List[str]:
    """Coerce to a list of non-empty strings."""
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


# ---------------------------------------------------------------------------
# Internal data model
# ---------------------------------------------------------------------------
@dataclass
class PRReportData:
    employee_name: str
    employee_role: str
    current_project: str
    review_year: int
    languages: List[str] = field(default_factory=list)
    qa_qm_expertise: List[str] = field(default_factory=list)
    automation_technical: List[str] = field(default_factory=list)
    practices_tools: List[str] = field(default_factory=list)
    certifications_text: str = ""
    learning: Dict[str, List[str]] = field(default_factory=dict)  # year_str -> items
    # feedback_by_type: keys are upload type values (e.g. "auto_feedback"), values are raw doc lines
    feedback_by_type: Dict[str, List[str]] = field(default_factory=dict)
    feedback_improvement: List[str] = field(default_factory=list)
    activity: List[Dict[str, Any]] = field(default_factory=list)
    achievements_summary: str = ""
    achievements_highlights: List[str] = field(default_factory=list)
    fallbacks: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------
class ReportGenerator:
    """
    Generates a self-contained, downloadable HTML PR report from uploaded
    documents.  Uses an LLM for intelligent content allocation when an
    OpenAI API key is configured; falls back to pattern-based extraction
    otherwise.
    """

    # Maximum characters of combined document text sent to the LLM (~6 k tokens for GPT-4o)
    _MAX_LLM_CHARS = 25_000

    def generate_html(
        self,
        file_records: list,
        employee_name: str,
        employee_role: str = "",
        current_project: str = "",
        review_year: Optional[int] = None,
        year_hierarchy: Optional[Dict[str, Any]] = None,
        yoy_analysis: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Build and return a self-contained HTML string.

        Args:
            file_records:    UploadedFile ORM objects with ``extracted_text`` set.
            employee_name:   Full name shown as the report H1.
            employee_role:   Current role / title.
            current_project: Current project assignment.
            review_year:     Review year (defaults to current year).
            year_hierarchy:  Optional year navigation dict with keys:
                            - current_year, all_years, previous_year, next_year
            yoy_analysis:    Optional YOY analysis dict with keys:
                            - new_achievements, new_skills, skill_progression, growth_areas,
                            - promotion_or_change, summary, overall_assessment
        """
        year = review_year or datetime.utcnow().year
        combined = self._combine_texts(file_records)

        data: Optional[PRReportData] = None
        if settings.openai_api_key and combined:
            data = self._extract_with_llm(combined, employee_name, employee_role, current_project, year)

        if data is None:
            data = self._extract_with_patterns(
                file_records, employee_name, employee_role, current_project, year
            )

        # Feedback is always populated verbatim from raw document text,
        # regardless of whether the LLM or pattern path was used.
        data.feedback_by_type = self._build_verbatim_feedback(file_records)

        return self._render(data, year_hierarchy=year_hierarchy, yoy_analysis=yoy_analysis)

    # ------------------------------------------------------------------
    # Text combination
    # ------------------------------------------------------------------

    def _combine_texts(self, file_records: list) -> str:
        """Combine extracted texts into a single string for the LLM.
        When multiple files share the same upload type, they are numbered:
        [CLIENT_FEEDBACK], [CLIENT_FEEDBACK_2], [CLIENT_FEEDBACK_3], …
        so the LLM can attribute feedback to the correct numbered source.
        """
        type_counts: Dict[str, int] = {}
        parts = []
        for rec in file_records:
            if not rec.extracted_text:
                continue
            base_type = (rec.file_type or "unknown").upper()
            type_counts[base_type] = type_counts.get(base_type, 0) + 1
            n = type_counts[base_type]
            label = base_type if n == 1 else f"{base_type}_{n}"
            parts.append(
                f"=== [{label}] {rec.original_filename} ===\n{rec.extracted_text}"
            )
        return "\n\n".join(parts)

    # ------------------------------------------------------------------
    # LLM extraction
    # ------------------------------------------------------------------

    def _extract_with_llm(
        self,
        combined_text: str,
        employee_name: str,
        employee_role: str,
        current_project: str,
        year: int,
    ) -> Optional[PRReportData]:
        try:
            from openai import OpenAI  # type: ignore[import]
        except ImportError:
            logger.warning("openai package not installed – using pattern extraction")
            return None

        text = combined_text[: self._MAX_LLM_CHARS]
        if len(combined_text) > self._MAX_LLM_CHARS:
            logger.info(
                f"Combined text truncated {len(combined_text)} → {self._MAX_LLM_CHARS} chars for LLM"
            )

        prompt = _LLM_PROMPT.format(
            employee_name=employee_name,
            year=year,
            combined_text=text,
        )

        try:
            client = OpenAI(api_key=settings.openai_api_key)
            response = client.chat.completions.create(
                model=settings.ai_model,
                messages=[
                    {"role": "system", "content": _LLM_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=2000,
            )
            raw = (response.choices[0].message.content or "{}").strip()
            # Strip accidental markdown code fences
            raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
            raw = re.sub(r"```\s*$", "", raw).strip()

            parsed = json.loads(raw)
            return self._json_to_data(parsed, employee_name, employee_role, current_project, year)

        except Exception as exc:
            logger.error(f"LLM extraction failed ({exc}) – falling back to pattern extraction")
            return None

    def _json_to_data(
        self,
        parsed: Dict,
        employee_name: str,
        employee_role: str,
        current_project: str,
        year: int,
    ) -> PRReportData:
        ss = parsed.get("skills_summary", {})
        fb = parsed.get("feedback", {})

        # Normalize learning keys to strings
        learning: Dict[str, List[str]] = {
            str(k): _as_str_list(v) for k, v in parsed.get("learning", {}).items()
        }

        # Normalize activity list
        activity: List[Dict[str, Any]] = []
        for act in parsed.get("activity", []):
            if isinstance(act, dict):
                activity.append(
                    {
                        "year": int(act.get("year", year)),
                        "title": str(act.get("title", "")).strip(),
                        "description": str(act.get("description", "")).strip(),
                        "contributions": _as_str_list(act.get("contributions", [])),
                        "type": str(act.get("type", "project")).strip(),
                    }
                )

        # Feedback verbatim is populated by generate_html; LLM feedback output is not used here.
        feedback_by_type: Dict[str, List[str]] = {}

        # Achievements
        ach = parsed.get("achievements", {})
        if isinstance(ach, dict):
            achievements_summary = str(ach.get("summary", "")).strip()
            achievements_highlights = _as_str_list(ach.get("highlights", []))
        else:
            achievements_summary, achievements_highlights = "", []

        raw_certs = parsed.get("certifications", [])
        if isinstance(raw_certs, list):
            certs_list = [str(c).strip() for c in raw_certs if str(c).strip()]
            certs = "; ".join(certs_list)
        else:
            certs = str(raw_certs).strip()
        # Sanity-check: if the value is suspiciously long (i.e. a doc dump), discard it
        if len(certs) > 500:
            certs = ""
        return PRReportData(
            employee_name=employee_name,
            employee_role=employee_role,
            current_project=current_project,
            review_year=year,
            languages=_as_str_list(ss.get("languages", [])),
            qa_qm_expertise=_as_str_list(ss.get("qa_qm_expertise", [])),
            automation_technical=_as_str_list(ss.get("automation_technical", [])),
            practices_tools=_as_str_list(ss.get("practices_tools", [])),
            certifications_text=certs or "Not applicable / not a focus during this review period",
            learning=learning,
            feedback_by_type=feedback_by_type,
            feedback_improvement=[],
            achievements_summary=achievements_summary,
            achievements_highlights=achievements_highlights,
            fallbacks=_as_str_list(parsed.get("fallbacks", [])),
            activity=activity,
        )

    # ------------------------------------------------------------------
    # Pattern-based fallback (uses ProfileConsolidator)
    # ------------------------------------------------------------------

    def _extract_with_patterns(
        self,
        file_records: list,
        employee_name: str,
        employee_role: str,
        current_project: str,
        year: int,
    ) -> PRReportData:
        profile = ProfileConsolidator().consolidate(file_records)
        ss = profile.skills_summary

        certs_text = (
            "; ".join(profile.certifications)
            if profile.certifications
            else "Not applicable / not a focus during this review period"
        )

        # Learning: use consolidated result (ProfileConsolidator now scans all docs)
        learning: Dict[str, List[str]] = {}
        if profile.learning:
            learning[str(year)] = profile.learning

        # Activity: use consolidated result (all docs scanned)
        activity = [
            {
                "year": year,
                "title": act.title,
                "description": act.description or "",
                "contributions": act.contributions,
                "type": act.source_type,
            }
            for act in profile.activity
        ]

        # Feedback verbatim is populated by generate_html.
        # For the pattern path, use positive feedback sentences as achievement highlights.
        highlights = _clean_items(profile.feedback.team_and_stakeholders, max_len=300)

        return PRReportData(
            employee_name=employee_name,
            employee_role=employee_role,
            current_project=current_project,
            review_year=year,
            languages=ss.languages,
            qa_qm_expertise=ss.domain_expertise,
            automation_technical=ss.automation_technical,
            practices_tools=ss.practices_tools,
            certifications_text=certs_text,
            learning=learning,
            feedback_by_type={},
            feedback_improvement=[],
            achievements_summary="",
            achievements_highlights=highlights,
            fallbacks=list(dict.fromkeys(profile.feedback.areas_for_improvement)),
            activity=activity,
        )

    # ------------------------------------------------------------------
    # HTML rendering
    # ------------------------------------------------------------------

    def _render(self, data: PRReportData, year_hierarchy: Optional[Dict[str, Any]] = None, yoy_analysis: Optional[Dict[str, Any]] = None) -> str:
        slug = _slug(data.employee_name)
        toc = self._toc_html(data, slug, yoy_analysis=yoy_analysis)
        body = self._body_html(data, slug, year_hierarchy, yoy_analysis=yoy_analysis)

        return "".join(
            [
                "<!DOCTYPE html>\n",
                "<html>\n",
                "<head>\n",
                '  <meta charset="UTF-8">\n',
                '  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n',
                f"  <title>Performance Review \u2013 {_esc(data.employee_name)}</title>\n",
                "  <style>",
                _CSS,
                "</style>\n",
                "</head>\n",
                '<body class="stackedit">\n',
                '  <div class="stackedit__left">\n',
                '    <div class="stackedit__toc">\n',
                toc,
                "    </div>\n",
                "  </div>\n\n",
                '  <div class="stackedit__right">\n',
                '    <div class="stackedit__html">\n\n',
                body,
                "    </div>\n",
                "  </div>\n\n",
                "</body>\n",
                "</html>",
            ]
        )

    def _toc_html(self, data: PRReportData, slug: str, yoy_analysis: Optional[Dict[str, Any]] = None) -> str:
        name = _esc(data.employee_name)

        # Feedback sub-links in canonical order
        fb_links: List[str] = []
        for key in _ordered_feedback_keys(data.feedback_by_type):
            if not data.feedback_by_type.get(key):
                continue
            label = _feedback_label(key)
            sid = key.replace("_", "-")
            fb_links.append(
                f'              <li><a href="#feedback-{sid}">{_esc(label)}</a></li>\n'
            )
        fb_sub = "".join(fb_links)

        # New top-level section links for Achievements and Fallbacks
        analysis_links = ""
        if data.achievements_summary or data.achievements_highlights:
            analysis_links += '            <li><a href="#achievements">Achievements</a></li>\n'
        if data.fallbacks:
            analysis_links += '            <li><a href="#fallbacks">Fallbacks</a></li>\n'

        # Build YOY links if analysis exists
        yoy_links = ""
        if yoy_analysis:
            yoy_links = '            <li><a href="#achievements-yoy">Achievements over a year</a></li>\n'
            has_concerns = any([
                yoy_analysis.get("areas_of_concern"),
                yoy_analysis.get("improvement_priorities"),
                yoy_analysis.get("unmet_goals"),
                yoy_analysis.get("overall_concerns"),
            ])
            if has_concerns:
                yoy_links += '            <li><a href="#areas-for-improvement-yoy">What went wrong and needs improvement</a></li>\n'

        return (
            "      <ul>\n"
            f'        <li><a href="#{slug}">{name}</a>\n'
            "          <ul>\n"
            '            <li><a href="#skills-summary">Skills summary</a></li>\n'
            '            <li><a href="#certifications">Certifications</a></li>\n'
            '            <li><a href="#learning">Learning</a></li>\n'
            '            <li><a href="#feedback">Feedback</a>\n'
            + (
                ("              <ul>\n" + fb_sub + "              </ul>\n")
                if fb_sub
                else ""
            )
            + "            </li>\n"
            '            <li><a href="#activity">Activity</a></li>\n'
            + analysis_links
            + yoy_links
            + "          </ul>\n"
            "        </li>\n"
            "      </ul>\n"
        )

    def _body_html(self, data: PRReportData, slug: str, year_hierarchy: Optional[Dict[str, Any]] = None, yoy_analysis: Optional[Dict[str, Any]] = None) -> str:
        parts: List[str] = []

        # ── Year Navigation ──────────────────────────────────────────────────
        if year_hierarchy and year_hierarchy.get("all_years"):
            parts.append(self._year_navigation_html(year_hierarchy))

        # ── Header ──────────────────────────────────────────────────────────
        parts.append(f'      <h1 id="{slug}">{_esc(data.employee_name)}</h1>\n')
        parts.append("      <p>\n")
        parts.append(f"        Performance Review {data.review_year}")
        if data.current_project:
            parts.append(f"<br>\n        Current project: {_esc(data.current_project)}")
        if data.employee_role:
            parts.append(f"<br>\n        Role: {_esc(data.employee_role)}")
        parts.append("\n      </p>\n\n")

        # ── Sections ─────────────────────────────────────────────────────────
        parts.append(self._skills_html(data))
        parts.append(self._certifications_html(data))
        parts.append(self._learning_html(data))
        parts.append(self._feedback_html(data))
        parts.append(self._activity_html(data))

        # ── Achievements (GPT-synthesised) ───────────────────────────────────
        if data.achievements_summary or data.achievements_highlights:
            parts.append(self._achievements_html(data))

        # ── Fallbacks (GPT-synthesised areas for improvement) ────────────────
        if data.fallbacks:
            parts.append(self._fallbacks_html(data))

        # ── Year-over-Year Analysis ──────────────────────────────────────────
        if yoy_analysis:
            parts.append(self._yoy_analysis_html(yoy_analysis))
            
            # ── Areas for Improvement Section ────────────────────────────────
            # Check if there are concerns to report
            has_concerns = any([
                yoy_analysis.get("areas_of_concern"),
                yoy_analysis.get("improvement_priorities"),
                yoy_analysis.get("unmet_goals"),
                yoy_analysis.get("overall_concerns"),
            ])
            if has_concerns:
                parts.append(self._areas_for_improvement_html(yoy_analysis))

        return "".join(parts)

    # ── Section renderers ────────────────────────────────────────────────────

    def _year_navigation_html(self, year_hierarchy: Dict[str, Any]) -> str:
        """Generate year navigation HTML allowing navigation between years."""
        current = year_hierarchy.get("current_year")
        all_years = year_hierarchy.get("all_years", [])
        
        if not all_years or len(all_years) <= 1:
            return ""  # No navigation needed if only one year
        
        # Build year links
        year_links = []
        for yr in all_years:
            if yr == current:
                year_links.append(f'      <a href="#" class="year-link current">{yr}</a>\n')
            else:
                year_links.append(f'      <a href="/profile/{_esc(year_hierarchy.get("person_name", ""))}/{yr}" class="year-link">{yr}</a>\n')
        
        year_links_html = "".join(year_links)
        
        return (
            '      <div class="year-navigation">\n'
            '        <div class="year-navigation-title">Available Years</div>\n'
            '        <div class="year-links">\n'
            + year_links_html +
            '        </div>\n'
            '      </div>\n\n'
        )

    def _skills_html(self, data: PRReportData) -> str:
        p: List[str] = ['      <h2 id="skills-summary">Skills summary <span class="badge-ai">AI generated</span></h2>\n']

        any_content = False

        if data.languages:
            langs = _clean_items(data.languages)
            if langs:
                any_content = True
                p.append('      <p><strong>Languages:</strong></p>\n')
                p.append('      <ul>\n')
                for lang in langs:
                    p.append(f'        <li>{_esc(lang)}</li>\n')
                p.append('      </ul>\n')

        if data.qa_qm_expertise:
            items = _clean_items(data.qa_qm_expertise)
            if items:
                any_content = True
                p.append('      <p><strong>Domain expertise:</strong></p>\n')
                p.append('      <ul>\n')
                for item in items:
                    p.append(f'        <li>{_esc(item)}</li>\n')
                p.append('      </ul>\n')

        if data.automation_technical:
            items = _clean_items(data.automation_technical)
            if items:
                any_content = True
                p.append('      <p><strong>Automation &amp; technical:</strong></p>\n')
                p.append('      <ul>\n')
                for item in items:
                    p.append(f'        <li>{_esc(item)}</li>\n')
                p.append('      </ul>\n')

        if data.practices_tools:
            items = _clean_items(data.practices_tools)
            if items:
                any_content = True
                p.append('      <p><strong>Practices &amp; tools:</strong></p>\n')
                p.append('      <ul>\n')
                for item in items:
                    p.append(f'        <li>{_esc(item)}</li>\n')
                p.append('      </ul>\n')

        if not any_content:
            p.append('      <p>Skills information not extracted from the provided documents.</p>\n')

        p.append('\n')
        return ''.join(p)

    def _certifications_html(self, data: PRReportData) -> str:
        raw = (data.certifications_text or "").strip()
        fallback = "Not applicable / not a focus during this review period"
        p: List[str] = ['      <h2 id="certifications">Certifications <span class="badge-ai">AI generated</span></h2>\n']
        if not raw or raw == fallback:
            p.append(f'      <p>{_esc(fallback)}</p>\n\n')
            return ''.join(p)
        items = _parse_cert_text(raw)
        if items:
            p.append('      <ul>\n')
            for item in items:
                p.append(f'        <li>{_esc(item)}</li>\n')
            p.append('      </ul>\n\n')
        else:
            p.append(f'      <p>{_esc(raw)}</p>\n\n')
        return ''.join(p)

    def _learning_html(self, data: PRReportData) -> str:
        p: List[str] = ['      <h2 id="learning">Learning <span class="badge-ai">AI generated</span></h2>\n']
        if not data.learning:
            p.append('      <p>No learning items recorded.</p>\n')
        else:
            for year_key in sorted(data.learning.keys()):
                raw_items = data.learning[year_key]
                items = _clean_items(raw_items, max_len=220)
                if not items:
                    continue
                p.append(f'      <h3>{_esc(year_key)}</h3>\n')
                p.append('      <ul>\n')
                for item in items:
                    p.append(f'        <li>{_esc(item)}</li>\n')
                p.append('      </ul>\n')
        p.append('\n')
        return ''.join(p)

    def _feedback_html(self, data: PRReportData) -> str:
        p: List[str] = ['      <h2 id="feedback">Feedback <span class="badge-verbatim">Original</span></h2>\n']

        has_content = False
        for key in _ordered_feedback_keys(data.feedback_by_type):
            items = data.feedback_by_type.get(key, [])
            if not items:
                continue
            has_content = True
            label = _feedback_label(key)
            sid = key.replace("_", "-")
            p.append(f'      <h3 id="feedback-{sid}">{_esc(label)}</h3>\n\n')
            p.append('      <div class="feedback-block">\n')
            p.append(self._render_verbatim_lines(items))
            p.append('      </div>\n\n')

        if not has_content:
            p.append("      <p>No feedback recorded.</p>\n")

        p.append("\n")
        return "".join(p)

    def _activity_html(self, data: PRReportData) -> str:
        p: List[str] = ['      <h2 id="activity">Activity <span class="badge-ai">AI generated</span></h2>\n']

        if not data.activity:
            p.append("      <p>No activity recorded.</p>\n")
            return "".join(p)

        # Group by year
        by_year: Dict[int, List[Dict]] = {}
        for act in data.activity:
            yr = int(act.get("year", data.review_year))
            by_year.setdefault(yr, []).append(act)

        for yr in sorted(by_year.keys()):
            p.append(f"\n      <h3>{yr}</h3>\n\n")
            for act in by_year[yr]:
                title = _esc(act.get("title", ""))
                desc = _esc(act.get("description", ""))
                contributions: List[str] = act.get("contributions", [])

                p.append(f"      <p>\n        <strong>{title}:</strong>")
                if desc:
                    p.append(f"<br>\n        {desc}")
                p.append("\n      </p>\n")

                if contributions:
                    p.append("      <p>\n        <strong>Key contributions:</strong>\n      </p>\n")
                    p.append("      <ul>\n")
                    for c in contributions:
                        p.append(f"        <li>{_esc(c)}</li>\n")
                    p.append("      </ul>\n\n")

        return "".join(p)

    def _achievements_html(self, data: "PRReportData") -> str:
        """Render the GPT-synthesised achievements section."""
        p: List[str] = ['      <h2 id="achievements">Achievements <span class="badge-ai">AI generated</span></h2>\n\n']
        if data.achievements_summary:
            p.append('      <blockquote>\n')
            p.append(f'        <p>{_esc(data.achievements_summary)}</p>\n')
            p.append('      </blockquote>\n\n')
        if data.achievements_highlights:
            items = _clean_items(data.achievements_highlights, max_len=300)
            if items:
                p.append('      <ul>\n')
                for item in items:
                    p.append(f'        <li>{_esc(item)}</li>\n')
                p.append('      </ul>\n\n')
        return ''.join(p)

    def _fallbacks_html(self, data: "PRReportData") -> str:
        """Render the GPT-synthesised fallbacks / areas for improvement section."""
        p: List[str] = ['      <h2 id="fallbacks">Fallbacks <span class="badge-ai">AI generated</span></h2>\n\n']
        items = _clean_items(data.fallbacks, max_len=300)
        if items:
            p.append('      <ul>\n')
            for item in items:
                p.append(f'        <li>{_esc(item)}</li>\n')
            p.append('      </ul>\n\n')
        return ''.join(p)

    def _build_verbatim_feedback(self, file_records: list) -> Dict[str, List[str]]:
        """Return raw lines from each feedback document grouped by upload type.

        Lines are preserved verbatim (no extraction or filtering) except:
        - Completely empty lines are dropped
        - Pure section-marker lines like ``[CLIENT FEEDBACK]`` (entire line is a marker tag)
          are dropped — the section heading already labels the block
        """
        # Boilerplate form headers that add no information value
        _META_SKIP_RE = re.compile(
            r"^(client feedback form|project feedback form|auto feedback form"
            r"|company function feedback form|additional feedback form"
            r"|review period\b|engagement details\b|project details\b"
            r"|employee details\b|satisfaction ratings?\b)$",
            re.IGNORECASE,
        )
        type_counts: Dict[str, int] = {}
        result: Dict[str, List[str]] = {}
        for rec in file_records:
            if not rec.extracted_text:
                continue
            dtype = rec.file_type or "unknown"
            if dtype not in _FEEDBACK_TYPES:
                continue
            type_counts[dtype] = type_counts.get(dtype, 0) + 1
            n = type_counts[dtype]
            key = dtype if n == 1 else f"{dtype}_{n}"
            lines: List[str] = []
            for raw in rec.extracted_text.splitlines():
                ln = raw.strip()
                if not ln:
                    continue
                # Drop pure section-marker lines: "[CLIENT FEEDBACK]" or
                # "[CLIENT FEEDBACK] Header text"
                if re.match(r"^\[[\w\s]+\]", ln):
                    continue
                if _META_SKIP_RE.match(ln):
                    continue
                lines.append(ln)
            if lines:
                result[key] = lines
        return result

    def _render_verbatim_lines(self, lines: List[str]) -> str:
        """Render verbatim document lines as clean, grouped HTML.

        Classifies each line into one of:
          HEADING   – short (≤60 chars), no period, not a key-value pair
          METADATA  – "Key: short value" pairs (engagement details block)
          RATING    – contains "N / N" score or Yes/No answer
          ATTR      – "Person/Title: long sentence…" attributed quote
          BULLET    – line flagged as a bullet (starts with dash / etc. pre-strip)
          TEXT      – everything else (paragraph)

        Consecutive lines of the same group are rendered together, not
        individually boxed.
        """
        # ── Classify ──────────────────────────────────────────────────────
        _RATING_RE   = re.compile(r'\b\d\s*/\s*\d\b|:\s*(Yes|No)\b', re.IGNORECASE)
        _META_KV_RE  = re.compile(r'^([^:\n]{2,40}):\s+(.{2,60})$')
        _ATTR_RE     = re.compile(r'^(.{5,80}):\s+(.{60,})$')
        _HEADING_WORDS = {
            "what worked particularly well", "areas for improvement",
            "additional comments", "key achievements", "notable achievements",
            "technical contribution", "collaboration and teamwork",
            "initiative and problem-solving", "areas for development",
            "meeting commitments", "communication and responsiveness",
            "quality of work and technical competence",
        }

        LINE_HEADING  = "h"
        LINE_METADATA = "m"
        LINE_RATING   = "r"
        LINE_ATTR     = "a"
        LINE_TEXT     = "t"

        classified: List[tuple] = []  # (kind, line)

        for line in lines:
            if _RATING_RE.search(line):
                classified.append((LINE_RATING, line))
                continue
            # Attributed quote: "Name up to 80 chars: sentence 60+ chars"
            am = _ATTR_RE.match(line)
            if am and len(am.group(2)) >= 60:
                classified.append((LINE_ATTR, line))
                continue
            # Short key-value metadata
            kv = _META_KV_RE.match(line)
            if kv and len(line) <= 80:
                classified.append((LINE_METADATA, line))
                continue
            # Heading: short, no trailing period, or explicitly known heading text
            ln_lower = line.lower().rstrip(":")
            if (
                (len(line) <= 60 and not line.rstrip().endswith("."))
                or ln_lower in _HEADING_WORDS
            ):
                classified.append((LINE_HEADING, line))
                continue
            classified.append((LINE_TEXT, line))

        # ── Group consecutive same-kind lines and render ───────────────────
        parts: List[str] = []

        i = 0
        while i < len(classified):
            kind, line = classified[i]

            if kind == LINE_HEADING:
                parts.append(f'      <h4 class="fb-heading">{_esc(line)}</h4>\n')
                i += 1

            elif kind == LINE_METADATA:
                # Collect run of metadata lines into a compact <dl>
                parts.append('      <dl class="fb-meta">\n')
                while i < len(classified) and classified[i][0] == LINE_METADATA:
                    _, ml = classified[i]
                    kv = _META_KV_RE.match(ml)
                    if kv:
                        k, v = kv.group(1).strip(), kv.group(2).strip()
                        parts.append(f'        <dt>{_esc(k)}</dt><dd>{_esc(v)}</dd>\n')
                    else:
                        parts.append(f'        <dd>{_esc(ml)}</dd>\n')
                    i += 1
                parts.append('      </dl>\n')

            elif kind == LINE_RATING:
                # Collect run of rating lines into a <ul>
                parts.append('      <ul class="fb-ratings">\n')
                while i < len(classified) and classified[i][0] == LINE_RATING:
                    _, rl = classified[i]
                    parts.append(f'        <li>{_esc(rl)}</li>\n')
                    i += 1
                parts.append('      </ul>\n')

            elif kind == LINE_ATTR:
                # Each attribution is its own styled block
                am = _ATTR_RE.match(line)
                if am:
                    who  = am.group(1).strip()
                    text = am.group(2).strip()
                    parts.append(
                        f'      <div class="fb-attr">'
                        f'<span class="fb-attr-who">{_esc(who)}</span>'
                        f'<p>{_esc(text)}</p></div>\n'
                    )
                else:
                    parts.append(f'      <p>{_esc(line)}</p>\n')
                i += 1

            else:  # LINE_TEXT
                # Collect consecutive text lines into one <p>
                buf: List[str] = []
                while i < len(classified) and classified[i][0] == LINE_TEXT:
                    buf.append(classified[i][1])
                    i += 1
                if buf:
                    combined = " ".join(buf)
                    parts.append(f'      <p class="fb-text">{_esc(combined)}</p>\n')

        return ''.join(parts)

    def _yoy_analysis_html(self, yoy_analysis: Dict[str, Any]) -> str:
        """Generate HTML section for year-over-year achievement analysis."""
        p: List[str] = ['      <h2 id="achievements-yoy">Achievements over a year <span class="badge-ai">AI generated</span></h2>\n\n']
        
        # Overall summary at top
        summary = yoy_analysis.get("summary", "")
        if summary:
            p.append('      <blockquote>\n')
            p.append(f'        <p>{_esc(summary)}</p>\n')
            p.append('      </blockquote>\n\n')
        
        # Promotion or role change
        promotion = yoy_analysis.get("promotion_or_change", "")
        if promotion:
            p.append('      <h3>Role Changes</h3>\n')
            p.append(f'      <p>{_esc(promotion)}</p>\n\n')
        
        # New achievements
        new_achievements = yoy_analysis.get("new_achievements", [])
        if new_achievements:
            p.append('      <h3>New Achievements</h3>\n')
            p.append('      <ul>\n')
            for achievement in new_achievements:
                p.append(f'        <li>{_esc(achievement)}</li>\n')
            p.append('      </ul>\n\n')
        
        # New skills gained
        new_skills = yoy_analysis.get("new_skills", [])
        if new_skills:
            p.append('      <h3>New Skills Gained</h3>\n')
            p.append('      <ul>\n')
            for skill in new_skills:
                p.append(f'        <li>{_esc(skill)}</li>\n')
            p.append('      </ul>\n\n')
        
        # Skill progression (from → to)
        skill_progression = yoy_analysis.get("skill_progression", [])
        if skill_progression:
            p.append('      <h3>Skill Progression</h3>\n')
            p.append('      <ul>\n')
            for progression in skill_progression:
                if isinstance(progression, dict):
                    skill_name = progression.get("skill", "")
                    from_level = progression.get("from", "")
                    to_level = progression.get("to", "")
                    p.append(f'        <li>{_esc(skill_name)}: {_esc(from_level)} → {_esc(to_level)}</li>\n')
                else:
                    p.append(f'        <li>{_esc(str(progression))}</li>\n')
            p.append('      </ul>\n\n')
        
        # Growth areas / areas for development
        growth_areas = yoy_analysis.get("growth_areas", [])
        if growth_areas:
            p.append('      <h3>Growth Areas for Next Year</h3>\n')
            p.append('      <ul>\n')
            for area in growth_areas:
                p.append(f'        <li>{_esc(area)}</li>\n')
            p.append('      </ul>\n\n')
        
        # Overall assessment
        assessment = yoy_analysis.get("overall_assessment", "")
        if assessment:
            p.append('      <h3>Overall Assessment</h3>\n')
            p.append(f'      <p>{_esc(assessment)}</p>\n')
        
        return "".join(p)

    def _areas_for_improvement_html(self, yoy_analysis: Dict[str, Any]) -> str:
        """Generate HTML section for areas that need improvement compared to previous year."""
        p: List[str] = ['      <h2 id="areas-for-improvement-yoy">What went wrong and needs to be improved <span class="badge-ai">AI generated</span></h2>\n\n']
        
        # Overall concerns summary at top
        overall_concerns = yoy_analysis.get("overall_concerns", "")
        if overall_concerns:
            p.append('      <blockquote>\n')
            p.append(f'        <p>{_esc(overall_concerns)}</p>\n')
            p.append('      </blockquote>\n\n')
        
        # Areas of concern / regression
        areas_of_concern = yoy_analysis.get("areas_of_concern", [])
        if areas_of_concern:
            p.append('      <h3>Areas of Concern</h3>\n')
            p.append('      <ul>\n')
            for concern in areas_of_concern:
                p.append(f'        <li>{_esc(concern)}</li>\n')
            p.append('      </ul>\n\n')
        
        # Unmet goals from previous year
        unmet_goals = yoy_analysis.get("unmet_goals", [])
        if unmet_goals:
            p.append('      <h3>Unmet Goals from Previous Year</h3>\n')
            p.append('      <ul>\n')
            for goal in unmet_goals:
                p.append(f'        <li>{_esc(goal)}</li>\n')
            p.append('      </ul>\n\n')
        
        # Feedback gaps
        feedback_gaps = yoy_analysis.get("feedback_gaps", [])
        if feedback_gaps:
            p.append('      <h3>Feedback Gaps and Discrepancies</h3>\n')
            p.append('      <ul>\n')
            for gap in feedback_gaps:
                p.append(f'        <li>{_esc(gap)}</li>\n')
            p.append('      </ul>\n\n')
        
        # Improvement priorities
        improvement_priorities = yoy_analysis.get("improvement_priorities", [])
        if improvement_priorities:
            p.append('      <h3>Priority Areas for Next Review Period</h3>\n')
            p.append('      <ul>\n')
            for priority in improvement_priorities:
                p.append(f'        <li>{_esc(priority)}</li>\n')
            p.append('      </ul>\n\n')
        
        return "".join(p)