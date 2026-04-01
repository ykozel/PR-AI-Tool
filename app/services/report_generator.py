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
  font-style: italic;
  line-height: 1.65;
}
.feedback-quote p::before { content: "\201C"; font-size: 1.1em; color: #4183c4; margin-right: 2px; }
.feedback-quote p::after  { content: "\201D"; font-size: 1.1em; color: #4183c4; margin-left: 2px; }

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
"""

# ---------------------------------------------------------------------------
# LLM prompt templates
# ---------------------------------------------------------------------------
_LLM_SYSTEM = (
    "You are a precise information extractor for HR documents. "
    "Return ONLY a valid JSON object – no markdown, no code fences, no explanation."
)

_LLM_PROMPT = """You are a senior HR analyst extracting structured performance-review information from a set of HR documents.

Employee name: {employee_name}
Review year: {year}

Read EVERY document below in full, regardless of its type label, and extract ALL relevant information into the correct output sections.
Do NOT limit a section to only certain document types — skills may appear in any document, activity may appear in feedback docs, learning items may be in PDPs or feedback, etc.

Return ONLY a valid JSON object with this exact structure:
{{
  "skills_summary": {{
    "languages": ["Language (proficiency level)"],
    "qa_qm_expertise": ["QA/QM methodology, domain knowledge, or testing expertise item"],
    "automation_technical": ["Automation tool, DevOps technology, engineering skill, or cloud platform"],
    "practices_tools": ["Practice, methodology, reporting tool, dashboard, or test management tool"]
  }},
  "certifications": "List certifications/accreditations found in any document, or 'Not applicable / not a focus during this review period'",
  "learning": {{
    "2025": ["Course, training, workshop, or self-study item completed or planned"],
    "2026": ["Learning item"]
  }},
  "feedback": {{
    "by_source": {{
      "auto_feedback": ["Verbatim quote or close paraphrase of feedback found in auto-feedback doc"],
      "client_feedback": ["Feedback from client feedback doc"],
      "project_feedback": ["Feedback from project feedback doc"],
      "company_function": ["Feedback from company function doc"],
      "additional_feedback": ["Feedback from additional feedback doc"]
    }},
    "areas_for_improvement": [
      "Development suggestion, growth area, or improvement note found in ANY document"
    ]
  }},
  "activity": [
    {{
      "year": 2025,
      "title": "Project, initiative, committee, or function name",
      "description": "2-3 sentence description of the work performed",
      "contributions": ["Key contribution or achievement"],
      "type": "project"
    }}
  ]
}}

Extraction rules:
- SCAN ALL DOCUMENTS for EVERY section — do not skip a section because it seems unlikely for a given document type
- skills_summary: extract skills, tools, languages, methodologies mentioned anywhere — PDP, feedback docs, project descriptions, certifications, all of it
- learning: extract any mention of courses, trainings, workshops, planned studies, or certifications being pursued from ANY document; group by year when determinable
- activity: extract project work, initiatives, committee involvement, and key contributions from ANY document (feedback about a project = evidence of activity); one entry per distinct project/initiative
- feedback.by_source: place quotes/paraphrases under the key matching the === [DOCUMENT_TYPE] === label of the source document converted to lowercase; when the label is numbered (e.g. [CLIENT_FEEDBACK_2]) use that exact lowercase key (e.g. "client_feedback_2"); only include keys for types actually present; PDPs and activity docs that contain feedback-style text should go under their own label if it does not match a feedback type
- areas_for_improvement: collect development suggestions, gaps, or growth areas from ANY document
- certifications: collect from any document, including PDPs and training plans
- languages = spoken/written human languages; qa_qm_expertise = QA/QM domain/methodology; automation_technical = tools & engineering; practices_tools = dashboards, sprint practices, test management
- Keep list items concise (one line each, no trailing period)
- Only include learning years for which you have actual content
- Do not invent content — extract only what is present in the documents

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
    # feedback_by_type: keys are upload type values (e.g. "auto_feedback"), values are item lists
    feedback_by_type: Dict[str, List[str]] = field(default_factory=dict)
    feedback_improvement: List[str] = field(default_factory=list)
    activity: List[Dict[str, Any]] = field(default_factory=list)


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

    # Maximum characters of combined document text sent to the LLM (~4 k tokens)
    _MAX_LLM_CHARS = 15_000

    def generate_html(
        self,
        file_records: list,
        employee_name: str,
        employee_role: str = "",
        current_project: str = "",
        review_year: Optional[int] = None,
        year_hierarchy: Optional[Dict[str, Any]] = None,
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

        return self._render(data, year_hierarchy=year_hierarchy)

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

        # Build per-type feedback dict from by_source, with only non-empty entries
        by_source = fb.get("by_source", {})
        feedback_by_type: Dict[str, List[str]] = {}
        if isinstance(by_source, dict):
            for dtype, items in by_source.items():
                parsed_items = _as_str_list(items)
                if parsed_items:
                    feedback_by_type[dtype] = parsed_items
        # Fall back: if LLM returned old-style team_and_stakeholders, put it under a generic key
        if not feedback_by_type:
            old_style = _as_str_list(fb.get("team_and_stakeholders", []))
            if old_style:
                feedback_by_type["feedback"] = old_style

        certs = str(parsed.get("certifications", "")).strip()
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
            feedback_improvement=_as_str_list(fb.get("areas_for_improvement", [])),
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

        # Feedback: one unique key per file, numbered when same type appears more than once
        feedback_by_type: Dict[str, List[str]] = {}
        all_improvement_lines: List[str] = []
        type_counts: Dict[str, int] = {}

        for rec in file_records:
            if not rec.extracted_text:
                continue
            dtype = rec.file_type or "unknown"

            # Build a unique key for this file (e.g. client_feedback, client_feedback_2)
            if dtype in _FEEDBACK_TYPES:
                type_counts[dtype] = type_counts.get(dtype, 0) + 1
                n = type_counts[dtype]
                key = dtype if n == 1 else f"{dtype}_{n}"
            else:
                key = None  # non-feedback docs only contribute to improvement notes

            # Scan every line for improvement notes (any doc) or positive feedback (feedback docs)
            for line in _extract_feedback_lines(rec.extracted_text):
                line_lower = line.lower()
                if any(kw in line_lower for kw in [
                    "improvement", "could", "should", "would benefit",
                    "develop", "growth area", "recommend", "potential to",
                    "work on", "focus on", "improve", "further develop",
                ]):
                    all_improvement_lines.append(line)
                elif key is not None:
                    feedback_by_type.setdefault(key, []).append(line)


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
            feedback_by_type=feedback_by_type,
            feedback_improvement=list(dict.fromkeys(
                all_improvement_lines + profile.feedback.areas_for_improvement
            )),
            activity=activity,
        )

    # ------------------------------------------------------------------
    # HTML rendering
    # ------------------------------------------------------------------

    def _render(self, data: PRReportData, year_hierarchy: Optional[Dict[str, Any]] = None) -> str:
        slug = _slug(data.employee_name)
        toc = self._toc_html(data, slug)
        body = self._body_html(data, slug, year_hierarchy)

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

    def _toc_html(self, data: PRReportData, slug: str) -> str:
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
        if data.feedback_improvement:
            fb_links.append(
                '              <li><a href="#feedback-improvement">Areas for improvement</a></li>\n'
            )

        fb_sub = "".join(fb_links)

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
            "          </ul>\n"
            "        </li>\n"
            "      </ul>\n"
        )

    def _body_html(self, data: PRReportData, slug: str, year_hierarchy: Optional[Dict[str, Any]] = None) -> str:
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
        p: List[str] = ['      <h2 id="skills-summary">Skills summary</h2>\n']

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
        p: List[str] = ['      <h2 id="certifications">Certifications</h2>\n']
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
        p: List[str] = ['      <h2 id="learning">Learning</h2>\n']
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
        p: List[str] = ['      <h2 id="feedback">Feedback</h2>\n']

        has_content = False
        for key in _ordered_feedback_keys(data.feedback_by_type):
            items = data.feedback_by_type.get(key, [])
            if not items:
                continue
            has_content = True
            label = _feedback_label(key)
            sid = key.replace("_", "-")
            p.append(f'      <h3 id="feedback-{sid}">{_esc(label)}</h3>\n\n')
            for quote in items:
                p.append('      <blockquote class="feedback-quote">\n')
                p.append(f"        <p>{_esc(quote)}</p>\n")
                p.append("      </blockquote>\n\n")

        if data.feedback_improvement:
            has_content = True
            p.append('      <h3 id="feedback-improvement">Areas for improvement</h3>\n')
            for item in data.feedback_improvement:
                p.append('      <blockquote class="improvement-note">\n')
                p.append(f"        <p>{_esc(item)}</p>\n")
                p.append("      </blockquote>\n\n")

        if not has_content:
            p.append("      <p>No feedback recorded.</p>\n")

        p.append("\n")
        return "".join(p)

    def _activity_html(self, data: PRReportData) -> str:
        p: List[str] = ['      <h2 id="activity">Activity</h2>\n']

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
