"""Schemas for the consolidated PR profile output."""
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class SkillsSummary(BaseModel):
    """Structured skills breakdown mirroring the PR report format."""
    languages: List[str] = Field(default_factory=list, description="Spoken / written languages")
    domain_expertise: List[str] = Field(
        default_factory=list,
        description="QA/QM, architecture, domain-specific competencies",
    )
    automation_technical: List[str] = Field(
        default_factory=list,
        description="Automation, DevOps, cloud, engineering technical skills",
    )
    practices_tools: List[str] = Field(
        default_factory=list,
        description="Methodologies, frameworks, tooling",
    )
    other: List[str] = Field(default_factory=list, description="Any skills not categorised above")


class FeedbackSummary(BaseModel):
    """Consolidated feedback from all feedback-type documents."""
    team_and_stakeholders: List[str] = Field(
        default_factory=list,
        description="Positive feedback quotes / highlights from colleagues and stakeholders",
    )
    areas_for_improvement: List[str] = Field(
        default_factory=list,
        description="Development suggestions and improvement areas",
    )


class ActivityEntry(BaseModel):
    """A single project or function activity entry."""
    title: str = Field(description="Project / initiative / committee name")
    description: Optional[str] = Field(default=None, description="Short description of the work")
    contributions: List[str] = Field(
        default_factory=list, description="Key contributions (bullet points)"
    )
    source_type: str = Field(
        default="project", description="project | function | compliance"
    )


class ConsolidatedProfileResponse(BaseModel):
    """
    Full consolidated PR profile built from one or more uploaded documents.

    Mirrors the structure of the HTML performance-review report:
      • Skills Summary
      • Certifications
      • Learning
      • Feedback  (team + areas for improvement)
      • Activity  (project + function activities)
    """

    # ── Source metadata ─────────────────────────────────────────────────────
    upload_ids: List[int] = Field(description="All upload IDs that were analysed")
    pr_profile_id: Optional[int] = Field(default=None)
    document_types_included: List[str] = Field(
        default_factory=list, description="Upload types that contributed to this profile"
    )
    total_docs_analyzed: int = Field(default=0)
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    # ── Profile content ──────────────────────────────────────────────────────
    skills_summary: SkillsSummary = Field(default_factory=SkillsSummary)
    certifications: List[str] = Field(
        default_factory=list,
        description="Certification / accreditation entries across all documents",
    )
    learning: List[str] = Field(
        default_factory=list,
        description="Learning & development items across all documents",
    )
    feedback: FeedbackSummary = Field(default_factory=FeedbackSummary)
    activity: List[ActivityEntry] = Field(
        default_factory=list, description="Project and function activity entries"
    )

    # ── Per-section raw text (for debugging / review) ────────────────────────
    raw_sections: Optional[Dict[str, List[str]]] = Field(
        default=None,
        description="Optional: all raw section texts grouped by category",
    )
