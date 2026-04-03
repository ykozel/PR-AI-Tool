"""Profile consolidation service – merges extracted sections from N docs into one PR profile."""
import re
import logging
from typing import Dict, List, Optional, Tuple

from app.core.constants import FILE_TYPE_TO_FEEDBACK_TYPE, FeedbackType
from app.schemas.profile import (
    ActivityEntry,
    ConsolidatedProfileResponse,
    FeedbackSummary,
    SkillsSummary,
)
from app.services.document_processor import DocumentAnalysis, DocumentProcessor
from app.services.ai_analyzer import AIAnalyzer, AIAnalysisResult, SkillCategory

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Section-name keyword matchers (dynamic heading → logical category)
# ---------------------------------------------------------------------------

_CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "certifications": ["certif", "accreditat", "license", "licence", "credential"],
    "learning": [
        "learn", "training", "education", "course", "study",
        "workshop", "development", "upskill",
    ],
    "feedback": [
        "feedback", "evaluation", "assessment", "appraisal",
        "review", "comment", "colleague", "stakeholder", "peer",
    ],
    "activity": [
        "project", "activity", "initiative", "assignment", "contribution",
        "deliverable", "work", "task",
    ],
    "function": ["function", "committee", "compliance", "working group", "task force"],
    "skills": [
        "skill", "competenc", "expertise", "capabilit", "summary",
        "technical", "technology", "proficienc",
    ],
    "improvement": [
        "improvement", "develop", "gap", "grow", "recommendation",
        "potential", "could", "should",
    ],
}

# doc upload_type → which logical buckets its sections feed into (priority order)
_TYPE_BUCKET: Dict[str, List[str]] = {
    "company_function": ["feedback", "skills", "improvement"],
    "auto_feedback": ["feedback", "skills", "improvement"],
    "additional_feedback": ["feedback", "improvement"],
    "client_feedback": ["feedback"],
    "project_feedback": ["activity", "skills"],
    "project_activity": ["activity", "skills"],
    "pdp": ["learning", "skills"],
    "trainings": ["certifications", "learning"],
    "self_feedback": ["feedback", "skills"],
}


def _match_category(section_name: str) -> Optional[str]:
    """Return the best matching logical category for a dynamic section heading."""
    name_lower = section_name.lower()
    for category, keywords in _CATEGORY_KEYWORDS.items():
        if any(kw in name_lower for kw in keywords):
            return category
    return None


def _split_bullet_lines(text: str) -> List[str]:
    """Split a block of text into meaningful non-empty lines / bullet items."""
    lines = []
    for raw in text.splitlines():
        clean = re.sub(r"^[\s\-•*▪·]+", "", raw).strip()
        if clean and len(clean) > 3:
            lines.append(clean)
    return lines


def _split_sentences(text: str) -> List[str]:
    """Split text into individual sentences (for feedback quotes)."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in sentences if len(s.strip()) > 15]


def _is_improvement(text: str) -> bool:
    """Heuristic: does this feedback chunk sound like an improvement note?"""
    text_lower = text.lower()
    triggers = [
        "improvement", "could", "should", "would benefit",
        "develop", "growth area", "recommend", "potential to",
        "work on", "focus on", "improve", "further develop",
    ]
    return any(t in text_lower for t in triggers)


# ---------------------------------------------------------------------------
# SkillsSummary builder (from AI analysis result)
# ---------------------------------------------------------------------------

_LANGUAGE_HINTS = [
    "english", "french", "german", "russian", "polish", "dutch",
    "chinese", "japanese", "spanish", "portuguese", "arabic",
    "ukrainian", "swedish", "norwegian",
]


class ProfileConsolidator:
    """
    Consolidates extracted sections from multiple uploaded documents into one
    coherent ConsolidatedProfileResponse, matching the PR report output format:
      Skills Summary / Certifications / Learning / Feedback / Activity
    """

    def __init__(self) -> None:
        self._doc_processor = DocumentProcessor()
        self._ai_analyzer = AIAnalyzer()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def consolidate(
        self,
        file_records: list,           # List[UploadedFile]
        include_raw_sections: bool = False,
    ) -> ConsolidatedProfileResponse:
        """
        Build a consolidated PR profile from a collection of already-processed
        UploadedFile ORM records.

        Each record is expected to have ``extracted_text`` populated.
        Files without extracted text are skipped with a warning.

        Args:
            file_records: List of UploadedFile ORM objects (text already extracted).
            include_raw_sections: If True, attach the raw section texts per
                                  logical bucket in the response.

        Returns:
            ConsolidatedProfileResponse with all sections populated.
        """
        # ── 1. Parse each document and bucket its sections ─────────────────
        bucket: Dict[str, List[str]] = {
            "certifications": [],
            "learning": [],
            "feedback": [],
            "activity": [],
            "function": [],
            "skills": [],
            "improvement": [],
        }
        doc_types_seen: List[str] = []
        upload_ids: List[int] = []
        docs_analyzed = 0

        for record in file_records:
            if not record.extracted_text:
                logger.warning(f"Skipping upload {record.id}: no extracted text")
                continue

            upload_ids.append(record.id)
            doc_type = record.file_type or "unknown"
            doc_types_seen.append(doc_type)
            docs_analyzed += 1

            # Determine the default buckets for this doc type (used as fallback only)
            default_buckets = _TYPE_BUCKET.get(doc_type, ["feedback"])

            # Process document to extract its sections
            feedback_type = FILE_TYPE_TO_FEEDBACK_TYPE.get(doc_type, FeedbackType.UNKNOWN)
            analysis: DocumentAnalysis = self._doc_processor.process_document(
                record.extracted_text, feedback_type.value
            )

            for section in analysis.sections:
                # Use section-name keyword match to determine bucket;
                # if no match, try ALL buckets via keyword then fall back to default.
                category = _match_category(section.section_name)
                if not category:
                    # Content-first: check the section content itself for keywords
                    category = _match_category(section.content[:200]) or default_buckets[0]
                if category in bucket:
                    bucket[category].append(section.content)
                    # Cross-populate: skills content from any section, feedback from any section
                    if category not in ("skills", "improvement"):
                        # Also scan all sections for skills keywords
                        if any(kw in section.content.lower() for kw in ["skill", "expert", "profici", "compet", "technolog", "automat"]):
                            bucket["skills"].append(section.content)
                else:
                    bucket[default_buckets[0]].append(section.content)

            # If no sections were extracted, put full text into ALL relevant buckets
            if not analysis.sections:
                full_text = record.extracted_text
                # Always feed into skills and the type-default bucket
                bucket["skills"].append(full_text)
                bucket[default_buckets[0]].append(full_text)
                # Feed into other buckets based on content keywords
                text_lower = full_text.lower()
                if any(kw in text_lower for kw in ["certif", "accreditat", "course", "training", "workshop", "learn"]):
                    bucket["certifications"].append(full_text)
                    bucket["learning"].append(full_text)
                if any(kw in text_lower for kw in ["project", "initiative", "deliverable", "contribut"]):
                    bucket["activity"].append(full_text)
                if any(kw in text_lower for kw in ["feedback", "evaluat", "review", "apprais", "comment"]):
                    bucket["feedback"].append(full_text)
                if any(kw in text_lower for kw in ["improvement", "develop", "grow", "gap", "recommend"]):
                    bucket["improvement"].append(full_text)

        # ── 2. Build AI-powered skills summary ─────────────────────────────
        # Combine ALL document text for skill/cert extraction so nothing is missed
        all_text = "\n\n".join(
            rec.extracted_text for rec in file_records if rec.extracted_text
        )
        combined_feedback = "\n\n".join(bucket["feedback"])
        combined_activity = "\n\n".join(bucket["activity"])
        combined_function = "\n\n".join(bucket["function"])
        combined_learning = "\n\n".join(bucket["learning"])
        combined_certs = "\n\n".join(bucket["certifications"])
        combined_skills_text = "\n\n".join(bucket["skills"])

        ai_result: AIAnalysisResult = self._ai_analyzer.analyze_extracted_sections(
            feedback=all_text or None,
            project_activity=combined_activity or None,
            function_activity=combined_function or None,
            learning=combined_learning or None,
            certifications=combined_certs or None,
        )

        skills_summary = self._build_skills_summary(ai_result, combined_skills_text)

        # ── 3. Certifications ───────────────────────────────────────────────
        certifications = self._extract_certifications(combined_certs, ai_result)

        # ── 4. Learning items ───────────────────────────────────────────────
        # Pull learning from dedicated learning/pdp bucket only — no all_text fallback
        learning = self._extract_learning(combined_learning) if combined_learning else []

        # ── 5. Feedback (team + improvement) ───────────────────────────────
        feedback_summary = self._extract_feedback(
            combined_feedback, bucket["improvement"]
        )

        # ── 6. Activity entries ─────────────────────────────────────────────
        activity = self._extract_activity(
            bucket["activity"],
            bucket["function"],
            ai_result,
        )

        return ConsolidatedProfileResponse(
            upload_ids=upload_ids,
            document_types_included=list(dict.fromkeys(doc_types_seen)),  # preserve order, dedupe
            total_docs_analyzed=docs_analyzed,
            skills_summary=skills_summary,
            certifications=certifications,
            learning=learning,
            feedback=feedback_summary,
            activity=activity,
            raw_sections=bucket if include_raw_sections else None,
        )

    # ------------------------------------------------------------------
    # Section builders
    # ------------------------------------------------------------------

    def _build_skills_summary(
        self, ai_result: AIAnalysisResult, raw_skills_text: str
    ) -> SkillsSummary:
        """Categorise AI-identified skills into the four skill buckets."""
        languages: List[str] = []
        domain: List[str] = []
        automation: List[str] = []
        practices: List[str] = []
        other: List[str] = []

        # Detect languages from raw text
        for lang in _LANGUAGE_HINTS:
            if lang in raw_skills_text.lower():
                cap = lang.capitalize()
                if cap not in languages:
                    languages.append(cap)

        # Map AI-identified skills to buckets
        for skill in ai_result.identified_skills:
            name = skill.skill_name
            cat = skill.category

            if cat == SkillCategory.TECHNICAL:
                automation.append(name)
            elif cat in (SkillCategory.PROCESS, SkillCategory.DOMAIN):
                domain.append(name)
            elif cat == SkillCategory.SOFT_SKILLS:
                practices.append(name)
            elif cat == SkillCategory.LEADERSHIP:
                domain.append(name)  # leadership ≈ domain expertise in QA context
            elif cat == SkillCategory.CERTIFICATIONS:
                pass  # certs go to the certifications section
            else:
                other.append(name)

        # Parse raw skills text for lines that weren't caught by AI.
        # Only accept short, item-like lines (not full feedback sentences).
        for line in _split_bullet_lines(raw_skills_text):
            # Skip section-marker lines and long sentences
            if line.startswith("[") or len(line) > 80:
                continue
            line_lower = line.lower()
            if any(h in line_lower for h in _LANGUAGE_HINTS):
                if line not in languages:
                    languages.append(line)
            elif any(kw in line_lower for kw in ["automat", "devops", "cloud", "infra", "sdet", "ci/cd"]):
                if line not in automation:
                    automation.append(line)
            elif any(kw in line_lower for kw in ["dashboard", "metric", "sprint", "defect", "test case", "tools", "practice", "jira", "confluence"]):
                if line not in practices:
                    practices.append(line)
            elif any(kw in line_lower for kw in ["strategy", "planning", "process", "qa", "qm", "risk", "sign-off", "migration", "release"]):
                if line not in domain:
                    domain.append(line)

        return SkillsSummary(
            languages=_dedupe(languages),
            domain_expertise=_dedupe(domain),
            automation_technical=_dedupe(automation),
            practices_tools=_dedupe(practices),
            other=_dedupe(other),
        )

    def _extract_certifications(
        self, certs_text: str, ai_result: AIAnalysisResult
    ) -> List[str]:
        """Return a deduplicated list of certification strings."""
        certs: List[str] = []

        # From AI-identified cert skills
        for skill in ai_result.identified_skills:
            if skill.category == SkillCategory.CERTIFICATIONS:
                certs.append(skill.skill_name)

        # From raw text
        for line in _split_bullet_lines(certs_text):
            if line not in certs:
                certs.append(line)

        if not certs and certs_text:
            # The whole section is a single "not applicable" note
            processed = certs_text.strip()[:300]
            if processed:
                certs.append(processed)

        return _dedupe(certs) or ["Not applicable / not a focus during this review period"]

    def _extract_learning(self, learning_text: str) -> List[str]:
        """Return bullet-point learning items."""
        items = _split_bullet_lines(learning_text)
        return _dedupe(items)

    def _extract_feedback(
        self, feedback_text: str, improvement_chunks: List[str]
    ) -> FeedbackSummary:
        """Split feedback text into positive quotes vs improvement notes."""
        positive: List[str] = []
        improvements: List[str] = []

        # Process primary feedback text
        for sentence in _split_sentences(feedback_text):
            if _is_improvement(sentence):
                improvements.append(sentence)
            else:
                if len(sentence) > 20:
                    positive.append(sentence)

        # Improvement-labelled buckets
        for chunk in improvement_chunks:
            for sentence in _split_sentences(chunk):
                if sentence not in improvements:
                    improvements.append(sentence)

        return FeedbackSummary(
            team_and_stakeholders=_dedupe(positive),
            areas_for_improvement=_dedupe(improvements),
        )

    def _extract_activity(
        self,
        activity_chunks: List[str],
        function_chunks: List[str],
        ai_result: AIAnalysisResult,
    ) -> List[ActivityEntry]:
        """Build ActivityEntry objects from project + function sections."""
        entries: List[ActivityEntry] = []

        # ── Project activities ──────────────────────────────────────────────
        for chunk in activity_chunks:
            entry = self._parse_activity_chunk(chunk, source_type="project")
            if entry:
                entries.append(entry)

        # ── Function / committee activities ────────────────────────────────
        for chunk in function_chunks:
            entry = self._parse_activity_chunk(chunk, source_type="function")
            if entry:
                entries.append(entry)

        # Fall back: create entries from AI achievements if no activity sections found
        if not entries and ai_result.identified_achievements:
            for ach in ai_result.identified_achievements:
                entries.append(ActivityEntry(
                    title=ach.achievement_title[:120],
                    description=ach.description,
                    contributions=[ach.impact] if ach.impact else [],
                    source_type="project",
                ))

        return entries

    def _parse_activity_chunk(self, text: str, source_type: str) -> Optional[ActivityEntry]:
        """Parse a raw activity text block into a structured ActivityEntry."""
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if not lines:
            return None

        # The first non-empty line is treated as the title
        title = re.sub(r"^[\*\-•\d\.\:]+\s*", "", lines[0]).strip()
        if not title:
            title = "Activity"

        # Remaining lines: split into description vs bullet contributions
        description_parts: List[str] = []
        contributions: List[str] = []

        for line in lines[1:]:
            clean = re.sub(r"^[\-•*▪·]+\s*", "", line).strip()
            if not clean:
                continue
            # Short lines without sentence structure → contribution bullet
            if len(clean) < 120 and not clean.endswith((".", "!", "?")):
                contributions.append(clean)
            else:
                description_parts.append(clean)

        return ActivityEntry(
            title=title,
            description=" ".join(description_parts[:3]) if description_parts else None,
            contributions=contributions[:15],
            source_type=source_type,
        )


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _dedupe(items: List[str]) -> List[str]:
    """Order-preserving deduplication (case-insensitive)."""
    seen: set = set()
    result: List[str] = []
    for item in items:
        key = item.strip().lower()
        if key and key not in seen:
            seen.add(key)
            result.append(item.strip())
    return result
