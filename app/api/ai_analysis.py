"""AI Analysis API endpoints for identifying skills, achievements, and insights"""
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.models.file import UploadedFile
from app.services.ai_analyzer import AIAnalyzer
from app.schemas.ai_analysis import (
    AIAnalysisRequest,
    AIAnalysisResponse,
    IdentifiedSkillResponse,
    IdentifiedAchievementResponse,
    BulkAIAnalysisRequest,
    BulkAIAnalysisResponse,
    SkillRecommendationRequest,
    SkillRecommendationResponse,
    ComparisonRequest,
    ComparisonResponse,
    SkillComparison,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["AI Analysis"])

# Initialize AI Analyzer
ai_analyzer = AIAnalyzer()


@router.post("/analyze/{upload_id}", response_model=AIAnalysisResponse)
async def analyze_feedback(
    upload_id: int,
    db: Session = Depends(get_db),
):
    """
    Analyze extracted sections from uploaded feedback to identify skills, achievements, and insights
    
    Args:
        upload_id: ID of the uploaded file
        db: Database session
        
    Returns:
        AIAnalysisResponse with identified skills, achievements, strengths, and recommendations
        
    Example:
        GET /api/ai/analyze/1
        
    Response:
        {
            "identified_skills": [
                {
                    "skill_name": "AWS (Cloud Architecture)",
                    "category": "technical",
                    "confidence": 0.95,
                    "source_section": "project_activity",
                    "evidence": ["Led migration of 45+ applications to cloud"]
                }
            ],
            "identified_achievements": [
                {
                    "achievement_title": "Cloud Migration Initiative",
                    "description": "...",
                    "impact": "35% cost reduction",
                    "confidence": 0.95
                }
            ],
            "technical_strength": 0.88,
            "leadership_strength": 0.82,
            "overall_score": 0.85,
            "recommendations": [
                "Strong technical foundation",
                "Ready for senior roles"
            ]
        }
    """
    try:
        # Retrieve uploaded file
        uploaded_file = db.query(UploadedFile).filter(UploadedFile.id == upload_id).first()
        if not uploaded_file:
            raise HTTPException(status_code=404, detail=f"Upload with ID {upload_id} not found")
        
        if not uploaded_file.extracted_text:
            raise HTTPException(
                status_code=400,
                detail="File has not been processed yet. Extract text first."
            )
        
        analysis = _analyze_file(uploaded_file)
        response = _to_analysis_response(upload_id, analysis)

        logger.info(f"AI analysis completed for upload_id={upload_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing upload {upload_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/bulk-analyze", response_model=BulkAIAnalysisResponse)
async def bulk_analyze_feedback(
    request: BulkAIAnalysisRequest,
    db: Session = Depends(get_db),
):
    """
    Analyze multiple uploaded files in bulk
    
    Args:
        request: BulkAIAnalysisRequest with upload_ids
        
    Returns:
        BulkAIAnalysisResponse with analyses for all uploads
    """
    try:
        analyses = []
        
        for upload_id in request.upload_ids:
            uploaded_file = db.query(UploadedFile).filter(UploadedFile.id == upload_id).first()
            if not uploaded_file or not uploaded_file.extracted_text:
                continue
            
            analysis = _analyze_file(uploaded_file)
            analyses.append(_to_analysis_response(upload_id, analysis))
        
        summary = f"Analyzed {len(analyses)} out of {len(request.upload_ids)} uploads successfully"
        
        return BulkAIAnalysisResponse(
            total_analyzed=len(analyses),
            analyses=analyses,
            summary=summary
        )
        
    except Exception as e:
        logger.error(f"Error in bulk analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Bulk analysis failed: {str(e)}")


@router.get("/skills/{upload_id}", response_model=List[IdentifiedSkillResponse])
async def get_identified_skills(
    upload_id: int,
    category: Optional[str] = Query(None, description="Filter by skill category"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
):
    """
    Get identified skills from an analyzed upload
    
    Args:
        upload_id: ID of the upload to analyze
        category: Optional skill category filter (technical, leadership, soft_skills, etc.)
        min_confidence: Minimum confidence threshold (0.0 to 1.0)
        
    Returns:
        List of identified skills
        
    Example:
        GET /api/ai/skills/1?category=technical&min_confidence=0.8
    """
    try:
        uploaded_file = db.query(UploadedFile).filter(UploadedFile.id == upload_id).first()
        if not uploaded_file or not uploaded_file.extracted_text:
            raise HTTPException(status_code=404, detail="Upload not found or not processed")
        
        analysis = _analyze_file(uploaded_file)

        # Filter skills
        skills = [
            IdentifiedSkillResponse(
                skill_name=skill.skill_name,
                category=skill.category.value,
                confidence=skill.confidence,
                source_section=skill.source_section,
                evidence=skill.evidence[:3]
            )
            for skill in analysis.identified_skills
            if (not category or skill.category.value == category)
            and skill.confidence >= min_confidence
        ]
        
        return sorted(skills, key=lambda s: s.confidence, reverse=True)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving skills: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/achievements/{upload_id}", response_model=List[IdentifiedAchievementResponse])
async def get_identified_achievements(
    upload_id: int,
    db: Session = Depends(get_db),
):
    """
    Get identified achievements from an analyzed upload
    
    Args:
        upload_id: ID of the upload
        
    Returns:
        List of identified achievements
        
    Example:
        GET /api/ai/achievements/1
    """
    try:
        uploaded_file = db.query(UploadedFile).filter(UploadedFile.id == upload_id).first()
        if not uploaded_file or not uploaded_file.extracted_text:
            raise HTTPException(status_code=404, detail="Upload not found or not processed")
        
        analysis = _analyze_file(uploaded_file)

        achievements = [
            IdentifiedAchievementResponse(
                achievement_title=ach.achievement_title,
                description=ach.description,
                impact=ach.impact,
                source_section=ach.source_section,
                confidence=ach.confidence
            )
            for ach in analysis.identified_achievements
        ]
        
        return sorted(achievements, key=lambda a: a.confidence, reverse=True)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving achievements: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommendations/skills", response_model=SkillRecommendationResponse)
async def get_skill_recommendations(
    request: SkillRecommendationRequest,
):
    """
    Get personalized skill recommendations based on analysis
    
    Args:
        request: SkillRecommendationRequest with identified skills and gaps
        
    Returns:
        SkillRecommendationResponse with personalized recommendations
    """
    try:
        recommendations = _generate_skill_recommendations(request)
        return recommendations
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare", response_model=ComparisonResponse)
async def compare_analyses(
    request: ComparisonRequest,
    db: Session = Depends(get_db),
):
    """
    Compare skills and achievements across multiple uploads to identify growth
    
    Args:
        request: ComparisonRequest with upload_ids
        
    Returns:
        ComparisonResponse showing skill evolution and growth trajectory
    """
    try:
        comparisons = []
        
        for upload_id in sorted(request.upload_ids):
            uploaded_file = db.query(UploadedFile).filter(UploadedFile.id == upload_id).first()
            if not uploaded_file or not uploaded_file.extracted_text:
                continue
            
            analysis = _analyze_file(uploaded_file)

            skills = [s.skill_name for s in analysis.identified_skills]
            certifications = [s for s in analysis.identified_skills if s.category.value == 'certifications']
            achievements_titles = [a.achievement_title for a in analysis.identified_achievements]
            
            comparison = SkillComparison(
                upload_id=upload_id,
                analyzed_at=uploaded_file.uploaded_at,
                total_skills=len(analysis.identified_skills),
                technical_skills_count=len([s for s in analysis.identified_skills if s.category.value == 'technical']),
                leadership_skills_count=len([s for s in analysis.identified_skills if s.category.value == 'leadership']),
                certifications=[s.skill_name for s in certifications],
                top_achievements=achievements_titles[:3],
                overall_strength=analysis.overall_score,
            )
            comparisons.append(comparison)
        
        # Analyze growth trajectory
        growth_trajectory = _analyze_growth_trajectory(comparisons)
        skill_evolution = _analyze_skill_evolution(comparisons)
        
        recommendations = [
            "Continue developing identified strength areas",
            "Address identified competency gaps with targeted training",
            "Leverage demonstrated expertise in leadership/mentoring"
        ]
        
        return ComparisonResponse(
            comparisons=comparisons,
            growth_trajectory=growth_trajectory,
            skill_evolution=skill_evolution,
            recommendations=recommendations[:3]
        )
        
    except Exception as e:
        logger.error(f"Error comparing analyses: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions

def _parse_extracted_sections(uploaded_file: UploadedFile) -> dict:
    """
    Parse extracted sections from the uploaded file
    
    In a real implementation, this would retrieve saved structured sections
    from the database or parse them from the extracted_text
    """
    # This is a placeholder - in production, sections would be stored separately
    # For now, return the full text so analyzer can work with it
    return {
        'feedback': uploaded_file.extracted_text,
        'project_activity': uploaded_file.extracted_text,
        'function_activity': uploaded_file.extracted_text,
        'learning': uploaded_file.extracted_text,
        'certifications': uploaded_file.extracted_text,
    }


def _analyze_file(uploaded_file: UploadedFile):
    """Run AI analysis on an uploaded file's extracted sections."""
    sections = _parse_extracted_sections(uploaded_file)
    return ai_analyzer.analyze_extracted_sections(
        feedback=sections.get('feedback'),
        project_activity=sections.get('project_activity'),
        function_activity=sections.get('function_activity'),
        learning=sections.get('learning'),
        certifications=sections.get('certifications'),
    )


def _to_analysis_response(upload_id: int, analysis) -> AIAnalysisResponse:
    """Convert an AIAnalysisResult to the API response schema."""
    return AIAnalysisResponse(
        upload_id=upload_id,
        identified_skills=[
            IdentifiedSkillResponse(
                skill_name=skill.skill_name,
                category=skill.category.value,
                confidence=skill.confidence,
                source_section=skill.source_section,
                evidence=skill.evidence[:3],
            )
            for skill in analysis.identified_skills
        ],
        identified_achievements=[
            IdentifiedAchievementResponse(
                achievement_title=ach.achievement_title,
                description=ach.description,
                impact=ach.impact,
                source_section=ach.source_section,
                confidence=ach.confidence,
            )
            for ach in analysis.identified_achievements
        ],
        competency_gaps=analysis.competency_gaps,
        growth_areas=analysis.growth_areas,
        leadership_indicators=analysis.leadership_indicators[:5],
        technical_strength=round(analysis.technical_strength, 2),
        leadership_strength=round(analysis.leadership_strength, 2),
        overall_score=round(analysis.overall_score, 2),
        recommendations=analysis.recommendations,
    )


def _generate_skill_recommendations(request: SkillRecommendationRequest) -> SkillRecommendationResponse:
    """Generate personalized skill recommendations"""
    
    # Categorize gaps by domain
    technical_gaps = [g for g in request.competency_gaps if any(
        t in g.lower() for t in ['technical', 'data', 'system', 'architecture']
    )]
    leadership_gaps = [g for g in request.competency_gaps if any(
        l in g.lower() for l in ['leadership', 'management', 'strategic']
    )]
    
    # Build recommendations
    priority_skills = request.competency_gaps[:3]
    
    certification_recs = []
    if technical_gaps:
        certification_recs.extend(['AWS Solutions Architect', 'Kubernetes Administrator (CKA)', 'GCP Professional'])
    if leadership_gaps:
        certification_recs.extend(['Project Management Professional (PMP)', 'Certified Scrum Master (CSM)'])
    
    learning_paths = []
    if technical_gaps:
        learning_paths.extend([
            'Cloud Architecture Fundamentals',
            'Advanced System Design',
            'Data Engineering Essentials'
        ])
    if leadership_gaps:
        learning_paths.extend([
            'Executive Leadership Program',
            'Strategic Planning & Execution',
            'Team Leadership & Development'
        ])
    
    mentorship_focus = [g for g in request.growth_areas[:2]] if request.growth_areas else ['Strategic Thinking']
    
    return SkillRecommendationResponse(
        priority_skills=priority_skills,
        certification_recommendations=certification_recs[:3],
        learning_paths=learning_paths[:3],
        mentorship_focus=mentorship_focus,
        timeline="6-12 months for significant improvement"
    )


def _analyze_growth_trajectory(comparisons: List[SkillComparison]) -> Optional[str]:
    """Analyze growth trajectory from multiple comparisons"""
    if len(comparisons) < 2:
        return None
    
    scores = [c.overall_strength for c in comparisons]
    growth = scores[-1] - scores[0] if scores else 0
    
    if growth > 0.1:
        return f"Strong growth trajectory: +{growth:.1%} improvement"
    elif growth > 0:
        return f"Positive growth: +{growth:.1%} improvement"
    elif growth == 0:
        return "Consistent performance"
    else:
        return f"Slight decline: {growth:.1%} change"


def _analyze_skill_evolution(comparisons: List[SkillComparison]) -> List[str]:
    """Analyze how skills have evolved"""
    evolution = []
    
    if len(comparisons) >= 2:
        tech_growth = comparisons[-1].technical_skills_count - comparisons[0].technical_skills_count
        if tech_growth > 0:
            evolution.append(f"Technical skills +{tech_growth}")
        
        leadership_growth = comparisons[-1].leadership_skills_count - comparisons[0].leadership_skills_count
        if leadership_growth > 0:
            evolution.append(f"Leadership skills +{leadership_growth}")
    
    return evolution
