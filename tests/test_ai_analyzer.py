"""Tests for AI Analysis Layer"""
import pytest
from app.services.ai_analyzer import AIAnalyzer, SkillCategory, IdentifiedSkill, IdentifiedAchievement


class TestAIAnalyzerSkillExtraction:
    """Test skill extraction from different sections"""
    
    def setup_method(self):
        """Setup analyzer for each test"""
        self.analyzer = AIAnalyzer()
    
    def test_extract_technical_skills_from_project(self):
        """Test extraction of technical skills from project activity"""
        project_text = """
        Led migration of 45+ applications to cloud using AWS and Kubernetes.
        Designed microservices architecture with Docker containers.
        Implemented CI/CD pipelines for automated deployment.
        """
        
        skills = self.analyzer._extract_skills_from_project(project_text)
        
        assert len(skills) > 0
        skill_names = [s.skill_name.lower() for s in skills]
        assert any('aws' in name or 'cloud' in name for name in skill_names)
        assert any('kubernetes' in name or 'docker' in name for name in skill_names)
        assert all(s.category == SkillCategory.TECHNICAL for s in skills)
    
    def test_extract_leadership_skills_from_feedback(self):
        """Test extraction of leadership skills from feedback"""
        feedback_text = """
        John demonstrates exceptional leadership and strategic vision.
        Effectively manages team members and collaborates across departments.
        Shows strong problem-solving abilities and communication skills.
        """
        
        skills = self.analyzer._extract_skills_from_feedback(feedback_text)
        
        assert len(skills) > 0
        assert any(s.category == SkillCategory.SOFT_SKILLS for s in skills)
    
    def test_extract_certifications(self):
        """Test extraction of formal certifications"""
        cert_text = """
        Certifications:
        - AWS Solutions Architect Professional (renewed Jan 2025)
        - Certified Kubernetes Administrator (CKA)
        - Project Management Professional (PMP)
        """
        
        certs = self.analyzer._extract_certifications(cert_text)
        
        assert len(certs) > 0
        assert all(s.category == SkillCategory.CERTIFICATIONS for s in certs)
        cert_names = [s.skill_name.lower() for s in certs]
        assert any('aws' in name for name in cert_names)
        assert any('kubernetes' in name or 'cka' in name for name in cert_names)
    
    def test_extract_skills_from_learning(self):
        """Test extraction of skills from learning section"""
        learning_text = """
        Completed Advanced Kubernetes Administration Course (24 hours).
        Attended Cloud Architecture Best Practices Workshop (16 hours).
        Took AI/ML for Cloud Infrastructure program (32 hours).
        """
        
        skills = self.analyzer._extract_skills_from_learning(learning_text)
        
        assert len(skills) > 0
        assert all(len(s.skill_name) > 3 for s in skills)
    
    def test_extract_leadership_indicators_from_function_activity(self):
        """Test extraction of leadership indicators"""
        function_text = """
        Served as Lead/Co-Chair of Technical Excellence Committee.
        Managed cross-functional team of 25+ people.
        Directed major architectural decisions and guided engineering teams.
        """
        
        indicators = self.analyzer._extract_leadership_indicators(function_text)
        
        assert len(indicators) > 0
        assert any('lead' in indicator.lower() or 'managed' in indicator.lower() 
                   for indicator in indicators)


class TestAIAnalyzerAchievementExtraction:
    """Test achievement extraction"""
    
    def setup_method(self):
        """Setup analyzer for each test"""
        self.analyzer = AIAnalyzer()
    
    def test_extract_quantified_achievements(self):
        """Test extraction of achievements with quantified impact"""
        project_text = """
        Achieved 35% cost reduction through optimization strategies.
        Delivered cloud migration reducing infrastructure costs by $750K annually.
        Improved system performance by 60% through database optimization.
        """
        
        achievements = self.analyzer._extract_achievements(project_text, 'project_activity')
        
        assert len(achievements) > 0
        assert all(a.source_section == 'project_activity' for a in achievements)
        assert any(a.impact and '%' in a.impact for a in achievements)
    
    def test_extract_team_achievements(self):
        """Test extraction of team-related achievements"""
        project_text = """
        Built high-performing product team with 95% retention rate.
        Mentored 3 junior engineers, resulting in 2 promotions.
        Conducted 12 technical workshops impacting 80+ staff members.
        """
        
        achievements = self.analyzer._extract_achievements(project_text, 'project_activity')
        
        assert len(achievements) > 0
        assert any('team' in a.description.lower() for a in achievements)
    
    def test_extract_achievement_impact_metrics(self):
        """Test extraction of impact metrics from achievements"""
        text = "Reduced costs by 40% and improved efficiency by $2M annual savings."
        
        impact = self.analyzer._extract_impact_metrics(text)
        
        assert impact is not None
        assert '%' in impact or '$' in impact


class TestAIAnalyzerIntegration:
    """Test complete AI analysis integration"""
    
    def setup_method(self):
        """Setup analyzer for each test"""
        self.analyzer = AIAnalyzer()
    
    def test_analyze_complete_feedback_document(self):
        """Test analysis of complete feedback document with all sections"""
        feedback = """
        John demonstrates excellent problem-solving and communication skills.
        Shows strong leadership and strategic thinking abilities.
        """
        
        project_activity = """
        Led cloud migration initiative achieving 35% cost reduction.
        Designed microservices architecture with Kubernetes.
        Managed team of 8 engineers on critical project.
        """
        
        function_activity = """
        Served as Lead of Technical Excellence Committee.
        Directed architecture reviews for major projects.
        Mentored 3 engineers leading to 2 promotions.
        """
        
        learning = """
        Completed AWS Solutions Architect course.
        Certified Kubernetes Administrator.
        Attended AI/ML fundamentals training.
        """
        
        certifications = """
        AWS Solutions Architect Professional
        Certified Kubernetes Administrator (CKA)
        Project Management Professional (PMP)
        """
        
        result = self.analyzer.analyze_extracted_sections(
            feedback=feedback,
            project_activity=project_activity,
            function_activity=function_activity,
            learning=learning,
            certifications=certifications
        )
        
        # Verify result structure
        assert len(result.identified_skills) > 0
        assert len(result.identified_achievements) > 0
        assert len(result.leadership_indicators) > 0
        
        # Verify scores
        assert 0.0 <= result.technical_strength <= 1.0
        assert 0.0 <= result.leadership_strength <= 1.0
        assert 0.0 <= result.overall_score <= 1.0
        
        # Verify recommendations exist
        assert len(result.recommendations) > 0
        
        # Verify technical skills identified
        technical_categories = {
            s.category for s in result.identified_skills
            if s.category == SkillCategory.TECHNICAL
        }
        assert SkillCategory.TECHNICAL in technical_categories
        
        # Verify leadership identified
        assert result.leadership_strength > 0.5
    
    def test_analyze_minimal_document(self):
        """Test analysis with minimal content"""
        minimal_text = "Some basic work activities and achievements."
        
        result = self.analyzer.analyze_extracted_sections(feedback=minimal_text)
        
        # Should still return valid result structure
        assert isinstance(result.identified_skills, list)
        assert isinstance(result.identified_achievements, list)
        assert 0.0 <= result.overall_score <= 1.0
    
    def test_analyze_empty_document(self):
        """Test analysis with empty input"""
        result = self.analyzer.analyze_extracted_sections()
        
        # Should return empty but valid result
        assert result.identified_skills == []
        assert result.identified_achievements == []
        assert result.overall_score == 0.0


class TestSkillDeduplication:
    """Test skill deduplication and scoring"""
    
    def setup_method(self):
        """Setup analyzer for each test"""
        self.analyzer = AIAnalyzer()
    
    def test_deduplicate_similar_skills(self):
        """Test that similar skills are deduplicated"""
        skills = [
            IdentifiedSkill(
                skill_name="Leadership",
                category=SkillCategory.LEADERSHIP,
                confidence=0.8,
                source_section="feedback",
                evidence=["Evidence 1"]
            ),
            IdentifiedSkill(
                skill_name="Leadership",
                category=SkillCategory.LEADERSHIP,
                confidence=0.9,
                source_section="project_activity",
                evidence=["Evidence 2"]
            ),
        ]
        
        deduplicated = self.analyzer._deduplicate_and_score_skills(skills)
        
        assert len(deduplicated) == 1
        # Confidence should be increased for repeated skills
        assert deduplicated[0].confidence > 0.8
        # Evidence should be combined
        assert len(deduplicated[0].evidence) == 2
    
    def test_skill_scoring_increases_with_frequency(self):
        """Test that repeated skill mentions increase confidence"""
        initial_confidence = 0.7
        
        skills = [
            IdentifiedSkill(
                skill_name="Cloud Architecture",
                category=SkillCategory.TECHNICAL,
                confidence=initial_confidence,
                source_section="s1",
                evidence=["e1"]
            ),
            IdentifiedSkill(
                skill_name="Cloud Architecture",
                category=SkillCategory.TECHNICAL,
                confidence=initial_confidence,
                source_section="s2",
                evidence=["e2"]
            ),
            IdentifiedSkill(
                skill_name="Cloud Architecture",
                category=SkillCategory.TECHNICAL,
                confidence=initial_confidence,
                source_section="s3",
                evidence=["e3"]
            ),
        ]
        
        deduplicated = self.analyzer._deduplicate_and_score_skills(skills)
        
        assert len(deduplicated) == 1
        assert deduplicated[0].confidence > initial_confidence


class TestStrengthCalculation:
    """Test strength calculation algorithms"""
    
    def setup_method(self):
        """Setup analyzer for each test"""
        self.analyzer = AIAnalyzer()
    
    def test_technical_strength_high_with_many_technical_skills(self):
        """Test technical strength increases with more technical skills"""
        skills = [
            IdentifiedSkill(
                skill_name="AWS",
                category=SkillCategory.TECHNICAL,
                confidence=0.95,
                source_section="test"
            ),
            IdentifiedSkill(
                skill_name="Kubernetes",
                category=SkillCategory.TECHNICAL,
                confidence=0.9,
                source_section="test"
            ),
            IdentifiedSkill(
                skill_name="Python",
                category=SkillCategory.TECHNICAL,
                confidence=0.88,
                source_section="test"
            ),
        ]
        
        strength = self.analyzer._calculate_technical_strength(skills)
        
        assert strength > 0.8
        assert strength <= 1.0
    
    def test_leadership_strength_calculated_correctly(self):
        """Test leadership strength calculation"""
        indicators = [
            "Managed team of 10 engineers",
            "Led strategic initiative",
            "Mentored junior staff",
        ]
        
        skills = [
            IdentifiedSkill(
                skill_name="Team Leadership",
                category=SkillCategory.LEADERSHIP,
                confidence=0.9,
                source_section="test"
            ),
        ]
        
        strength = self.analyzer._calculate_leadership_strength(indicators, skills)
        
        assert 0.0 <= strength <= 1.0
        assert strength > 0.5  # Should be moderate to high


class TestRecommendationGeneration:
    """Test recommendation generation"""
    
    def setup_method(self):
        """Setup analyzer for each test"""
        self.analyzer = AIAnalyzer()
    
    def test_generate_recommendations_with_gaps(self):
        """Test that recommendations are generated for competency gaps"""
        from app.services.ai_analyzer import AIAnalysisResult
        
        result = AIAnalysisResult(
            identified_skills=[],
            competency_gaps=["Strategic Planning", "Public Speaking"],
            growth_areas=["Executive Leadership"]
        )
        
        recommendations = self.analyzer._generate_recommendations(result)
        
        assert len(recommendations) > 0
        assert any("Strategic Planning" in r or "Public Speaking" in r 
                   for r in recommendations)
    
    def test_recommend_leadership_development_for_low_leadership(self):
        """Test recommendations for low leadership development"""
        from app.services.ai_analyzer import AIAnalysisResult
        
        result = AIAnalysisResult(
            leadership_strength=0.3,
            technical_strength=0.8
        )
        
        recommendations = self.analyzer._generate_recommendations(result)
        
        assert any("leadership" in r.lower() for r in recommendations)


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def setup_method(self):
        """Setup analyzer for each test"""
        self.analyzer = AIAnalyzer()
    
    def test_handle_empty_strings(self):
        """Test handling of empty strings"""
        result = self.analyzer.analyze_extracted_sections(
            feedback="",
            project_activity="",
            function_activity=""
        )
        
        assert isinstance(result.identified_skills, list)
        assert isinstance(result.identified_achievements, list)
    
    def test_handle_special_characters(self):
        """Test handling of special characters in text"""
        text = "Achieved $2.5M cost reduction & 40% efficiency gain (Q1-Q4 2025)"
        
        achievements = self.analyzer._extract_achievements(text, 'test')
        
        assert len(achievements) > 0
        assert any(a.impact for a in achievements)
    
    def test_handle_very_long_text(self):
        """Test handling of very long text sections"""
        long_text = "Achievement: " + "improved performance " * 1000
        
        result = self.analyzer.analyze_extracted_sections(project_activity=long_text)
        
        # Should handle without crashing
        assert isinstance(result.identified_achievements, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
