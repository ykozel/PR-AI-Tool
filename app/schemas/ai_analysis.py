"""Schemas for AI Analysis endpoints"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class IdentifiedSkillResponse(BaseModel):
    """Schema for identified skill"""
    skill_name: str
    category: str  # 'technical', 'leadership', 'process', 'soft_skills', 'domain', 'certifications'
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0.0 to 1.0")
    source_section: str  # 'feedback', 'project_activity', 'function_activity', 'learning', 'certifications'
    evidence: List[str] = Field(default_factory=list, description="Quotes or text supporting this skill")


class IdentifiedAchievementResponse(BaseModel):
    """Schema for identified achievement"""
    achievement_title: str
    description: str
    impact: Optional[str] = Field(None, description="Quantified impact e.g., '35% cost reduction'")
    source_section: str = "project_activity"
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0.0 to 1.0")


class AIAnalysisRequest(BaseModel):
    """Request for AI analysis of extracted sections"""
    upload_id: int
    feedback: Optional[str] = None
    project_activity: Optional[str] = None
    function_activity: Optional[str] = None
    learning: Optional[str] = None
    certifications: Optional[str] = None
    pr_profile_id: Optional[int] = None


class AIAnalysisResponse(BaseModel):
    """Complete AI analysis response"""
    upload_id: int
    identified_skills: List[IdentifiedSkillResponse] = Field(default_factory=list)
    identified_achievements: List[IdentifiedAchievementResponse] = Field(default_factory=list)
    competency_gaps: List[str] = Field(default_factory=list, description="Skills to develop")
    growth_areas: List[str] = Field(default_factory=list, description="Focus areas for development")
    leadership_indicators: List[str] = Field(default_factory=list, description="Evidence of leadership")
    technical_strength: float = Field(ge=0.0, le=1.0, description="Technical capability score")
    leadership_strength: float = Field(ge=0.0, le=1.0, description="Leadership capability score")
    overall_score: float = Field(ge=0.0, le=1.0, description="Overall professional score")
    recommendations: List[str] = Field(default_factory=list, description="Personalized recommendations")
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    message: str = "AI analysis completed successfully"

    model_config = {
        "json_schema_extra": {
            "example": {
                "upload_id": 1,
                "identified_skills": [
                    {
                        "skill_name": "AWS (Cloud Infrastructure)",
                        "category": "technical",
                        "confidence": 0.95,
                        "source_section": "project_activity",
                        "evidence": ["AWS Solutions Architect Professional", "Led migration of 45+ applications to cloud"]
                    },
                    {
                        "skill_name": "Team Leadership",
                        "category": "leadership",
                        "confidence": 0.9,
                        "source_section": "function_activity",
                        "evidence": ["Managed cross-functional team of 8 engineers"]
                    }
                ],
                "identified_achievements": [
                    {
                        "achievement_title": "Cloud Migration Initiative",
                        "description": "Led migration of 45+ applications to cloud with zero downtime",
                        "impact": "35% cost reduction",
                        "source_section": "project_activity",
                        "confidence": 0.95
                    }
                ],
                "competency_gaps": ["Strategic Planning", "Public Speaking"],
                "growth_areas": ["AI/ML applications", "Executive presence"],
                "leadership_indicators": [
                    "Managed cross-functional team of 8 engineers",
                    "Mentored 3 junior engineers to senior roles"
                ],
                "technical_strength": 0.88,
                "leadership_strength": 0.82,
                "overall_score": 0.85,
                "recommendations": [
                    "Strong technical and leadership foundation",
                    "Ready for senior architecture or VP engineering roles",
                    "Consider executive leadership program for strategic planning"
                ],
                "message": "AI analysis completed successfully"
            }
        }
    }


class BulkAIAnalysisRequest(BaseModel):
    """Request for bulk AI analysis"""
    upload_ids: List[int]
    pr_profile_id: Optional[int] = None


class BulkAIAnalysisResponse(BaseModel):
    """Response for bulk AI analysis"""
    total_analyzed: int
    analyses: List[AIAnalysisResponse]
    summary: Optional[str] = None
    message: str = "Bulk AI analysis completed"


class SkillRecommendationRequest(BaseModel):
    """Request for skill recommendations"""
    identified_skills: List[IdentifiedSkillResponse]
    competency_gaps: List[str]
    growth_areas: List[str]
    industry: Optional[str] = None  # e.g., 'Technology', 'Finance', 'Healthcare'


class SkillRecommendationResponse(BaseModel):
    """Personalized skill recommendations"""
    priority_skills: List[str] = Field(description="High-priority skills to develop")
    certification_recommendations: List[str] = Field(description="Recommended certifications")
    learning_paths: List[str] = Field(description="Suggested learning paths and courses")
    mentorship_focus: List[str] = Field(description="Mentorship areas to focus on")
    timeline: Optional[str] = Field(None, description="Suggested timeline for development")
    message: str = "Recommendations generated"


class ComparisonRequest(BaseModel):
    """Request to compare skills across multiple uploads"""
    upload_ids: List[int]


class SkillComparison(BaseModel):
    """Skills comparison across uploads/time"""
    upload_id: int
    analyzed_at: datetime
    total_skills: int
    technical_skills_count: int
    leadership_skills_count: int
    certifications: List[str]
    top_achievements: List[str]
    overall_strength: float


class ComparisonResponse(BaseModel):
    """Comparison response"""
    comparisons: List[SkillComparison]
    growth_trajectory: Optional[str] = None
    skill_evolution: List[str] = Field(default_factory=list, description="How skills have evolved")
    recommendations: List[str] = Field(default_factory=list)
    message: str = "Comparison completed"
