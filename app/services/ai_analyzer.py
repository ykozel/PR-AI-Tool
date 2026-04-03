"""AI Layer for analyzing feedback, projects, and function activity to identify skills and achievements"""
import re
import logging
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class SkillCategory(Enum):
    """Categories of skills that can be identified"""
    TECHNICAL = "technical"
    LEADERSHIP = "leadership"
    PROCESS = "process"
    SOFT_SKILLS = "soft_skills"
    DOMAIN = "domain"
    CERTIFICATIONS = "certifications"


@dataclass
class IdentifiedSkill:
    """Structured representation of an identified skill"""
    skill_name: str
    category: SkillCategory
    confidence: float  # 0.0 to 1.0
    source_section: str  # 'feedback', 'project_activity', 'function_activity', 'learning'
    evidence: List[str] = field(default_factory=list)  # Quotes or phrases supporting this skill


@dataclass
class IdentifiedAchievement:
    """Structured representation of an identified achievement"""
    achievement_title: str
    description: str
    impact: Optional[str] = None  # Quantified impact (e.g., "35% cost reduction")
    source_section: str = "project_activity"  # Which section identified this
    confidence: float = 0.85


@dataclass
class AIAnalysisResult:
    """Complete AI analysis result"""
    identified_skills: List[IdentifiedSkill] = field(default_factory=list)
    identified_achievements: List[IdentifiedAchievement] = field(default_factory=list)
    competency_gaps: List[str] = field(default_factory=list)
    growth_areas: List[str] = field(default_factory=list)
    leadership_indicators: List[str] = field(default_factory=list)
    technical_strength: float = 0.0  # 0.0 to 1.0
    leadership_strength: float = 0.0  # 0.0 to 1.0
    overall_score: float = 0.0  # 0.0 to 1.0
    recommendations: List[str] = field(default_factory=list)


class AIAnalyzer:
    """AI Analysis engine for extracting insights from feedback documents"""
    
    # Technical skill patterns and keywords
    TECHNICAL_SKILLS = {
        'Cloud': ['aws', 'azure', 'gcp', 'cloud', 'kubernetes', 'docker', 'containerization', 'microservices'],
        'Data': ['data', 'analytics', 'python', 'sql', 'database', 'predictive', 'modeling', 'ml', 'machine learning', 'ai', 'big data'],
        'Architecture': ['architecture', 'design', 'system design', 'solution', 'framework', 'infrastructure'],
        'DevOps': ['ci/cd', 'devops', 'deployment', 'automation', 'pipeline', 'monitoring', 'logging'],
        'Security': ['security', 'compliance', 'audit', 'encryption', 'secure', 'gdpr', 'hipaa', 'pci-dss'],
        'Web': ['web', 'frontend', 'backend', 'api', 'rest', 'graphql', 'react', 'node'],
    }
    
    # Leadership and soft skill indicators
    LEADERSHIP_INDICATORS = [
        'lead', 'led', 'leading', 'leadership', 'managed', 'manager', 'team', 'mentor', 'mentored',
        'guided', 'directed', 'coordinated', 'orchestrated', 'championed', 'spearheaded', 'initiated',
        'oversee', 'strategic', 'strategic responsibility', 'vision', 'executive', 'stakeholder'
    ]
    
    SOFT_SKILLS = {
        'Communication': ['communication', 'communicate', 'present', 'presentation', 'speak', 'workshop', 'training', 'share knowledge'],
        'Problem-Solving': ['problem', 'solve', 'solution', 'challenge', 'overcame', 'resolved', 'identified', 'implemented'],
        'Collaboration': ['collaborate', 'collaboration', 'cross-functional', 'team', 'partnership', 'cooperative'],
        'Creativity': ['innovat', 'creative', 'novel', 'design', 'experiment', 'invent'],
        'Adaptability': ['adapt', 'flexible', 'change', 'evolve', 'learn', 'transform'],
    }
    
    # Impact indicators for achievements
    IMPACT_PATTERNS = [
        (r'(\d+)%\s+(?:reduction|improvement|increase|growth|boost|decrease)', 'percentage'),
        (r'\$(\d+[MK])\s+(?:saved|gained|revenue|cost|reduction|increase)', 'financial'),
        (r'(\d+)\s+(?:team|members|engineers|staff|people)', 'team_size'),
        (r'(?:zero-?downtime|zero-?defect|100%|99\.99%|99\.9%)', 'reliability'),
    ]
    
    # Achievement keywords
    ACHIEVEMENT_KEYWORDS = [
        'achieved', 'accomplished', 'delivered', 'launched', 'implemented', 'successful',
        'exceeded', 'improved', 'increased', 'reduced', 'optimized', 'transformed',
        'pioneered', 'established', 'created', 'built', 'architected'
    ]
    
    # Competency framework for identifying gaps
    CORE_COMPETENCIES = [
        'Strategic Thinking', 'Leadership', 'Communication', 'Technical Expertise',
        'Problem Solving', 'Collaboration', 'Innovation', 'Customer Focus',
        'Accountability', 'Adaptability', 'Analytical Skills', 'Project Management'
    ]
    
    def __init__(self):
        """Initialize the AI Analyzer"""
        self.identified_skills: Set[str] = set()
        self.identified_achievements: List[IdentifiedAchievement] = []
        self.logger = logging.getLogger(__name__)
    
    def analyze_extracted_sections(
        self,
        feedback: Optional[str] = None,
        project_activity: Optional[str] = None,
        function_activity: Optional[str] = None,
        learning: Optional[str] = None,
        certifications: Optional[str] = None
    ) -> AIAnalysisResult:
        """
        Analyze extracted sections and identify skills, achievements, and insights
        
        Args:
            feedback: Feedback section text
            project_activity: Project activity section text
            function_activity: Function activity section text
            learning: Learning section text
            certifications: Certifications section text
            
        Returns:
            AIAnalysisResult with identified skills and achievements
        """
        result = AIAnalysisResult()
        
        # Analyze each section
        if feedback:
            result.identified_skills.extend(self._extract_skills_from_feedback(feedback))
            result.leadership_indicators.extend(self._extract_leadership_indicators(feedback))
        
        if project_activity:
            result.identified_skills.extend(self._extract_skills_from_project(project_activity))
            result.identified_achievements.extend(self._extract_achievements(project_activity, 'project_activity'))
        
        if function_activity:
            result.identified_skills.extend(self._extract_skills_from_function(function_activity))
            result.identified_achievements.extend(self._extract_achievements(function_activity, 'function_activity'))
            result.leadership_indicators.extend(self._extract_leadership_indicators(function_activity))
        
        if learning:
            result.identified_skills.extend(self._extract_skills_from_learning(learning))
        
        if certifications:
            result.identified_skills.extend(self._extract_certifications(certifications))
        
        # Deduplicate and score skills
        result.identified_skills = self._deduplicate_and_score_skills(result.identified_skills)
        
        # Identify competency gaps
        result.competency_gaps = self._identify_competency_gaps(result.identified_skills)
        
        # Identify growth areas
        result.growth_areas = self._identify_growth_areas(feedback, project_activity, function_activity)
        
        # Calculate strength indicators
        result.technical_strength = self._calculate_technical_strength(result.identified_skills)
        result.leadership_strength = self._calculate_leadership_strength(
            result.leadership_indicators, 
            result.identified_skills
        )
        
        # Calculate overall score
        result.overall_score = (result.technical_strength + result.leadership_strength) / 2
        
        # Generate recommendations
        result.recommendations = self._generate_recommendations(result)
        
        return result
    
    def _extract_skills_from_feedback(self, feedback: str) -> List[IdentifiedSkill]:
        """Extract skills mentioned in feedback section"""
        skills = []
        feedback_lower = feedback.lower()
        
        # Look for explicit skill mentions
        for category, keywords in self.SOFT_SKILLS.items():
            for keyword in keywords:
                if keyword in feedback_lower:
                    skills.append(IdentifiedSkill(
                        skill_name=category,
                        category=SkillCategory.SOFT_SKILLS,
                        confidence=0.75,
                        source_section='feedback',
                        evidence=[self._extract_quote(feedback, keyword)]
                    ))
        
        # Look for positive descriptors
        positive_descriptors = [
            'excellent', 'strong', 'outstanding', 'exceptional', 'impressive',
            'remarkable', 'stellar', 'exemplary', 'proficient'
        ]
        
        for descriptor in positive_descriptors:
            if descriptor in feedback_lower:
                # Find what follows the descriptor
                match = re.search(rf'{descriptor}[^.!?]*(?:in|at|with|for)\s+([^.!?,]+)', feedback_lower)
                if match:
                    skill_mention = match.group(1).strip()
                    if len(skill_mention) > 3:
                        skills.append(IdentifiedSkill(
                            skill_name=skill_mention.title(),
                            category=SkillCategory.SOFT_SKILLS,
                            confidence=0.8,
                            source_section='feedback',
                            evidence=[feedback[match.start():match.end()]]
                        ))
        
        return skills
    
    def _extract_skills_from_project(self, project_activity: str) -> List[IdentifiedSkill]:
        """Extract technical and domain skills from project activity"""
        skills = []
        project_lower = project_activity.lower()
        
        # Extract technical skills — use word boundaries to avoid substring false-positives
        # (e.g. "ai" inside "Automation" or "main"). Record each category at most once.
        for tech_category, keywords in self.TECHNICAL_SKILLS.items():
            for keyword in keywords:
                if re.search(r'\b' + re.escape(keyword) + r'\b', project_lower):
                    skills.append(IdentifiedSkill(
                        skill_name=tech_category,
                        category=SkillCategory.TECHNICAL,
                        confidence=0.85,
                        source_section='project_activity',
                        evidence=[self._extract_quote(project_activity, keyword)]
                    ))
                    break  # one entry per category is enough
        
        # Extract domain skills (project-specific)
        domain_pattern = r'(?:project|initiative|system|platform)\s+(?:for|of|in)\s+([^\s,]+(?:\s+[^\s,]+)?)'
        for match in re.finditer(domain_pattern, project_activity, re.IGNORECASE):
            domain = match.group(1).strip()
            if len(domain) > 3:
                skills.append(IdentifiedSkill(
                    skill_name=f"{domain} Domain",
                    category=SkillCategory.DOMAIN,
                    confidence=0.7,
                    source_section='project_activity',
                    evidence=[domain]
                ))
        
        return skills
    
    def _extract_skills_from_function(self, function_activity: str) -> List[IdentifiedSkill]:
        """Extract leadership and operational skills from function activity"""
        skills = []
        function_lower = function_activity.lower()
        
        # Look for leadership-oriented skills
        leadership_skills = [
            'team leadership', 'strategic planning', 'process improvement',
            'cross-functional leadership', 'organizational development',
            'change management', 'project leadership'
        ]
        
        for skill in leadership_skills:
            if skill in function_lower:
                skills.append(IdentifiedSkill(
                    skill_name=skill.title(),
                    category=SkillCategory.LEADERSHIP,
                    confidence=0.8,
                    source_section='function_activity',
                    evidence=[self._extract_quote(function_activity, skill)]
                ))
        
        # Extract process/operational skills
        process_keywords = [
            'process', 'management', 'optimization', 'efficiency', 'quality',
            'compliance', 'framework', 'standard', 'methodology'
        ]
        
        for keyword in process_keywords:
            if keyword in function_lower:
                skills.append(IdentifiedSkill(
                    skill_name=f"{keyword.title()} Management",
                    category=SkillCategory.PROCESS,
                    confidence=0.75,
                    source_section='function_activity',
                    evidence=[self._extract_quote(function_activity, keyword)]
                ))
        
        return skills
    
    def _extract_skills_from_learning(self, learning: str) -> List[IdentifiedSkill]:
        """Extract skills from learning and development section"""
        skills = []
        learning_lower = learning.lower()
        
        # Look for course names and certifications
        course_pattern = r'(?:course|training|program|certification|completed)\s*:?\s*([^,\n]+)'
        for match in re.finditer(course_pattern, learning, re.IGNORECASE):
            course = match.group(1).strip()
            if len(course) > 3 and not course.endswith('hours'):
                skills.append(IdentifiedSkill(
                    skill_name=course,
                    category=SkillCategory.TECHNICAL if any(
                        kw in learning_lower for kw in ['programming', 'coding', 'data', 'cloud', 'analytics']
                    ) else SkillCategory.SOFT_SKILLS,
                    confidence=0.8,
                    source_section='learning',
                    evidence=[course]
                ))
        
        return skills
    
    def _extract_certifications(self, certifications: str) -> List[IdentifiedSkill]:
        """Extract formal certifications"""
        skills = []
        
        # Look for certification names
        cert_pattern = r'(?:certification|certified|credential)\s*:?\s*([^,\n]+?)(?:\(|,|-|$)'
        for match in re.finditer(cert_pattern, certifications, re.IGNORECASE):
            cert = match.group(1).strip()
            if len(cert) > 3:
                skills.append(IdentifiedSkill(
                    skill_name=cert,
                    category=SkillCategory.CERTIFICATIONS,
                    confidence=0.95,  # High confidence for explicit certifications
                    source_section='certifications',
                    evidence=[cert]
                ))
        
        # Also catch common cert abbreviations
        common_certs = ['AWS', 'GCP', 'Azure', 'PMP', 'CSPO', 'CISSP', 'CKA', 'CKAD', 'Six Sigma']
        for cert in common_certs:
            if cert in certifications:
                skills.append(IdentifiedSkill(
                    skill_name=cert,
                    category=SkillCategory.CERTIFICATIONS,
                    confidence=0.95,
                    source_section='certifications',
                    evidence=[cert]
                ))
        
        return skills
    
    def _extract_achievements(self, text: str, source: str) -> List[IdentifiedAchievement]:
        """Extract quantified achievements from text"""
        achievements = []
        text_lower = text.lower()
        
        # Look for achievement keywords
        for keyword in self.ACHIEVEMENT_KEYWORDS:
            pattern = rf'{keyword}[^.!?]+[.!?]'
            for match in re.finditer(pattern, text, re.IGNORECASE):
                achievement_text = match.group(0).strip()
                
                # Extract impact metrics
                impact = self._extract_impact_metrics(achievement_text)
                
                # Create title from achievement text
                title = achievement_text.split('-')[0].strip()[:100]  # First 100 chars
                
                achievements.append(IdentifiedAchievement(
                    achievement_title=title,
                    description=achievement_text,
                    impact=impact,
                    source_section=source,
                    confidence=0.85
                ))
        
        return achievements
    
    def _extract_impact_metrics(self, text: str) -> Optional[str]:
        """Extract quantified impact from achievement text"""
        for pattern, impact_type in self.IMPACT_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None
    
    def _extract_leadership_indicators(self, text: str) -> List[str]:
        """Extract leadership indicators from text"""
        indicators = []
        text_lower = text.lower()
        
        for indicator in self.LEADERSHIP_INDICATORS:
            if indicator in text_lower:
                # Extract context around indicator
                pattern = rf'[^.!?]*{indicator}[^.!?]*[.!?]'
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    context = match.group(0).strip()[:150]
                    if context not in indicators:
                        indicators.append(context)
        
        return indicators
    
    def _deduplicate_and_score_skills(self, skills: List[IdentifiedSkill]) -> List[IdentifiedSkill]:
        """Deduplicate skills and adjust confidence based on frequency"""
        skill_dict: Dict[str, IdentifiedSkill] = {}
        
        for skill in skills:
            # Normalize skill name for comparison
            normalized = skill.skill_name.lower().strip()
            
            if normalized in skill_dict:
                # Increase confidence for repeated mentions
                existing = skill_dict[normalized]
                existing.confidence = min(1.0, existing.confidence + 0.05)
                existing.evidence.extend(skill.evidence)
            else:
                skill_dict[normalized] = skill
        
        return list(skill_dict.values())
    
    def _identify_competency_gaps(self, skills: List[IdentifiedSkill]) -> List[str]:
        """Identify potential competency gaps"""
        gaps = []
        identified_competencies = {
            s.skill_name.lower() for s in skills
        }
        
        # Check for missing core competencies
        for competency in self.CORE_COMPETENCIES:
            if competency.lower() not in identified_competencies:
                # Adjust expectation based on demonstrated skills
                if 'technical' in identified_competencies or 'leadership' in identified_competencies:
                    gaps.append(competency)
        
        return gaps[:5]  # Return top 5 gaps
    
    def _identify_growth_areas(
        self,
        feedback: Optional[str] = None,
        project_activity: Optional[str] = None,
        function_activity: Optional[str] = None
    ) -> List[str]:
        """Identify areas for growth based on feedback and activities"""
        growth_areas = []
        
        # Look for improvement keywords
        improvement_patterns = [
            r'(?:further|continue|more|greater|improve|enhance|develop)\s+(?:in|at|for)\s+([^.,]+)',
            r'(?:areas?|rooms?)\s+(?:for|to)\s+(?:improve|grow|develop)\s*:?\s*([^.,]+)',
        ]
        
        combined_text = ' '.join([t for t in [feedback, project_activity, function_activity] if t])
        
        for pattern in improvement_patterns:
            for match in re.finditer(pattern, combined_text, re.IGNORECASE):
                area = match.group(1).strip()
                if len(area) > 3:
                    growth_areas.append(area)
        
        return list(set(growth_areas))[:5]  # Return top 5 unique areas
    
    def _calculate_technical_strength(self, skills: List[IdentifiedSkill]) -> float:
        """Calculate technical strength score based on identified skills"""
        technical_skills = [s for s in skills if s.category in [SkillCategory.TECHNICAL, SkillCategory.DOMAIN]]
        
        if not technical_skills:
            return 0.3  # Default low score if no technical skills found
        
        # Average confidence of technical skills, boosted by count
        avg_confidence = sum(s.confidence for s in technical_skills) / len(technical_skills)
        count_boost = min(0.3, len(technical_skills) * 0.05)
        
        return min(1.0, avg_confidence + count_boost)
    
    def _calculate_leadership_strength(
        self,
        leadership_indicators: List[str],
        skills: List[IdentifiedSkill]
    ) -> float:
        """Calculate leadership strength score"""
        leadership_skills = [s for s in skills if s.category == SkillCategory.LEADERSHIP]
        
        indicator_score = min(1.0, len(leadership_indicators) * 0.1)
        skill_score = sum(s.confidence for s in leadership_skills) / max(1, len(leadership_skills))
        
        return (indicator_score + skill_score) / 2
    
    def _generate_recommendations(self, result: AIAnalysisResult) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        # Recommend skill development for gaps
        if result.competency_gaps:
            recommendations.append(
                f"Consider developing: {', '.join(result.competency_gaps[:3])}"
            )
        
        # Recommend growth areas
        if result.growth_areas:
            recommendations.append(
                f"Focus growth on: {', '.join(result.growth_areas[:3])}"
            )
        
        # Leadership recommendations
        if result.leadership_strength > 0.7:
            recommendations.append("Strong leadership potential - consider mentorship opportunities")
        elif result.leadership_strength < 0.4:
            recommendations.append("Develop leadership skills through team projects or mentoring")
        
        # Technical recommendations
        if result.technical_strength > 0.8:
            recommendations.append("Leverage technical expertise for architecture/design roles")
        elif result.technical_strength < 0.4:
            recommendations.append("Pursue technical certifications or training programs")
        
        # Balanced profile
        if 0.4 < result.technical_strength < 0.8 and 0.4 < result.leadership_strength < 0.8:
            recommendations.append("Well-rounded profile - suitable for technical leadership roles")
        
        return recommendations[:5]  # Return top 5 recommendations
    
    def _extract_quote(self, text: str, keyword: str, context_length: int = 100) -> str:
        """Extract a quote containing the keyword with context"""
        idx = text.lower().find(keyword.lower())
        if idx >= 0:
            start = max(0, idx - context_length)
            end = min(len(text), idx + len(keyword) + context_length)
            return text[start:end].strip()
        return keyword
