"""Test cases for document processing module"""
import pytest
from app.services.document_processor import (
    DocumentProcessor,
    SectionExtractor,
    SectionType,
    ProjectActivityParser,
    FunctionActivityParser,
    ExtractedSection,
)


class TestSectionExtractor:
    """Test suite for SectionExtractor"""
    
    @pytest.fixture
    def extractor(self):
        """Provide a SectionExtractor instance"""
        return SectionExtractor()
    
    def test_explicit_numbered_sections(self, extractor):
        """Test extraction of explicitly numbered sections"""
        text = """
        1. Previous Year Link
        Reference to 2024 profile available at docs/2024_profile.pdf
        
        2. Certifications
        AWS Solutions Architect
        Azure Administrator Certified
        
        3. Learning
        • Machine Learning Fundamentals (Coursera)
        • Advanced Python Programming (Udemy)
        
        4. Feedback
        Excellent performance in Q1 objectives
        
        5. Project Activity
        Led cloud infrastructure migration project
        
        6. Function Activity
        Organized quarterly technical workshops
        """
        
        sections = extractor.extract_sections(text)
        
        assert len(sections) == 6
        assert sections[0].section_type == SectionType.PREVIOUS_YEAR_LINK
        assert sections[1].section_type == SectionType.CERTIFICATIONS
        assert sections[2].section_type == SectionType.LEARNING
        assert sections[3].section_type == SectionType.FEEDBACK
        assert sections[4].section_type == SectionType.PROJECT_ACTIVITY
        assert sections[5].section_type == SectionType.FUNCTION_ACTIVITY
    
    def test_keyword_fallback_extraction(self, extractor):
        """Test extraction by keywords when no explicit numbering"""
        text = """
        Previous Year Link
        Link to 2024 performance review
        
        Certifications and Qualifications
        AWS Solutions Architect Certification
        Kubernetes Administrator Certification
        
        Learning and Development
        Completed ML fundamentals course
        Attended workshop on microservices
        
        Performance Feedback
        Strong technical leadership
        Good communication skills
        
        Project Contributions
        Migration project lead
        Delivered on time
        
        Internal Function Activities
        Committee member for technical standards
        Lead trainer for new technologies
        """
        
        sections = extractor.extract_sections(text)
        
        assert len(sections) > 0
        section_types = [s.section_type for s in sections]
        assert SectionType.CERTIFICATIONS in section_types
        assert SectionType.LEARNING in section_types
    
    def test_bullet_point_extraction(self, extractor):
        """Test extraction of bullet points from content"""
        content = """
        • Designed new microservices architecture
        • Mentored junior developers
        • Led code review sessions
        - Improved code quality metrics
        * Reduced deployment time by 50%
        """
        
        bullets = extractor.extract_bullet_points(content)
        
        assert len(bullets) >= 5
        assert any("architecture" in b.lower() for b in bullets)
        assert any("mentored" in b.lower() for b in bullets)
    
    def test_section_content_parsing(self, extractor):
        """Test that section content is properly cleaned"""
        section_with_header = """
        5. Project Activity
        This is the project activity section
        
        Key achievements:
        • Achievement 1
        • Achievement 2
        """
        
        parsed = extractor._parse_section_content(section_with_header)
        
        # Should not contain the section number/header
        assert "5." not in parsed or len(parsed.split("5.")) == 2
        assert "Project Activity" not in parsed or parsed.count("Project Activity") == 1
        assert "Achievement" in parsed
    
    def test_empty_document_handling(self, extractor):
        """Test handling of empty or minimal documents"""
        sections = extractor.extract_sections("")
        assert len(sections) == 0
        
        sections = extractor.extract_sections("No structured content here")
        assert isinstance(sections, list)
    
    def test_partial_sections(self, extractor):
        """Test extraction when only some sections are present"""
        text = """
        1. Previous Year Link
        Reference: doc-2024-ref
        
        3. Learning
        Completed AWS training
        
        5. Project Activity
        Led data migration project
        """
        
        sections = extractor.extract_sections(text)
        
        assert len(sections) >= 3
        section_types = [s.section_type.value for s in sections]
        assert 1 in section_types or SectionType.PREVIOUS_YEAR_LINK in [s.section_type for s in sections]


class TestDocumentProcessor:
    """Test suite for DocumentProcessor"""
    
    @pytest.fixture
    def processor(self):
        """Provide a DocumentProcessor instance"""
        return DocumentProcessor()
    
    def test_complete_document_processing(self, processor):
        """Test processing of a complete document"""
        text = """
        1. Previous Year Link
        Reference to 2024 profile
        
        2. Certifications
        AWS Solutions Architect
        
        3. Learning
        Machine Learning course completed
        
        4. Feedback
        Strong performance in Q1
        
        5. Project Activity
        Led cloud migration project
        
        6. Function Activity
        Organized technical workshops
        """
        
        analysis = processor.process_document(text, "project")
        
        assert analysis.feedback_type == "project"
        assert analysis.parsing_quality >= 0.8
        assert len(analysis.sections) >= 5
        assert analysis.full_text == text
    
    def test_quality_calculation(self, processor):
        """Test parsing quality calculation"""
        # Perfect document with all sections
        perfect_text = "\n".join([
            "1. Previous Year Link\ntext",
            "2. Certifications\ntext",
            "3. Learning\ntext",
            "4. Feedback\ntext",
            "5. Project Activity\ntext",
            "6. Function Activity\ntext",
        ])
        
        analysis = processor.process_document(perfect_text, "unknown")
        assert analysis.parsing_quality > 0.9
        assert len(analysis.sections) == 6
        
        # Partial document
        partial_text = "1. Previous Year Link\ntext\n3. Learning\ntext"
        analysis = processor.process_document(partial_text, "unknown")
        assert analysis.parsing_quality < 0.9
    
    def test_structured_data_extraction(self, processor):
        """Test conversion to structured data"""
        text = """
        1. Previous Year Link
        Profile-2024
        
        2. Certifications
        AWS Solutions Architect
        
        3. Learning
        Advanced Python
        
        4. Feedback
        Great performance
        
        5. Project Activity
        Migration project
        
        6. Function Activity
        Committee member
        """
        
        analysis = processor.process_document(text, "self")
        structured = processor.extract_structured_data(analysis)
        
        assert structured['previous_year_link'] is not None
        assert structured['certifications'] is not None
        assert structured['learning'] is not None
        assert structured['feedback'] is not None
        assert structured['project_activity'] is not None
        assert structured['function_activity'] is not None
        assert structured['feedback_type'] == 'self'
        assert 'quality_score' in structured
    
    def test_get_section_by_type(self, processor):
        """Test retrieving specific section from analysis"""
        text = """
        1. Previous Year Link
        Text
        2. Certifications
        AWS Certified
        """
        
        analysis = processor.process_document(text, "unknown")
        
        cert_section = processor.get_section_by_type(
            analysis, SectionType.CERTIFICATIONS
        )
        
        assert cert_section is not None
        assert cert_section.section_type == SectionType.CERTIFICATIONS
        assert "AWS" in cert_section.content
    
    def test_missing_section_returns_none(self, processor):
        """Test that missing sections return None"""
        text = "1. Previous Year Link\nReference"
        
        analysis = processor.process_document(text, "unknown")
        
        missing = processor.get_section_by_type(
            analysis, SectionType.CERTIFICATIONS
        )
        
        assert missing is None
    
    def test_list_item_extraction(self, processor):
        """Test extraction of list items from section content"""
        content = """
        • Item one
        • Item two
        • Item three
        """
        
        items = processor.extract_list_items(content)
        
        assert len(items) == 3
        assert "Item one" in items
        assert "Item three" in items


class TestProjectActivityParser:
    """Test suite for ProjectActivityParser"""
    
    def test_parse_complete_project(self):
        """Test parsing a complete project activity"""
        content = """
        Project: Cloud Infrastructure Migration
        
        Responsibilities:
        Designed and implemented cloud migration strategy,
        Led team of engineers, managed stakeholder communication
        
        Contributions:
        Reduced infrastructure costs by 40%,
        Improved deployment speed by 60%,
        Zero downtime during migration
        
        Duration: 01/2024 - 06/2024
        """
        
        parsed = ProjectActivityParser.parse_project(content)
        
        assert parsed['project_name']
        assert parsed['responsibilities_description']
        assert parsed['key_contributions']
        assert parsed['duration_start'] == "01/2024"
        assert parsed['duration_end'] == "06/2024"
    
    def test_parse_project_without_dates(self):
        """Test parsing project without explicit dates"""
        content = """
        Custom CRM Development
        
        Led development of internal CRM system,
        Coordinated with stakeholders,
        Implemented best practices
        
        Result: 50% improvement in sales tracking
        """
        
        parsed = ProjectActivityParser.parse_project(content)
        
        assert parsed['project_name']
        assert parsed['responsibilities_description'] or parsed['activity_description']
    
    def test_minimal_project_parsing(self):
        """Test parsing minimal project information"""
        content = "Web Portal Enhancement Project"
        
        parsed = ProjectActivityParser.parse_project(content)
        
        assert parsed['project_name'] == "Web Portal Enhancement Project"


class TestFunctionActivityParser:
    """Test suite for FunctionActivityParser"""
    
    def test_parse_complete_function(self):
        """Test parsing a complete function activity"""
        content = """
        Function: Technical Excellence Committee
        
        Activities:
        Organized monthly technical workshops,
        Led knowledge sharing sessions,
        Mentored junior engineers
        
        Contributions:
        Improved knowledge sharing across teams,
        Mentored 5 junior engineers successfully,
        Increased technical awareness
        
        Role: Lead
        """
        
        parsed = FunctionActivityParser.parse_function(content)
        
        assert parsed['function_name']
        assert parsed['activity_description']
        assert parsed['key_contributions']
        assert parsed['involvement_level'] == 'Lead'
    
    def test_parse_support_role(self):
        """Test parsing function with support role"""
        content = """
        Working Group: Process Improvement Task Force
        
        Supporting team with analysis and documentation,
        Assisting in process mapping activities
        
        Help provided: Created documentation, Reviewed processes
        """
        
        parsed = FunctionActivityParser.parse_function(content)
        
        assert parsed['function_name']
        assert parsed['involvement_level'] in ['Support', 'Contributor']
    
    def test_parse_lead_role_detection(self):
        """Test detection of leadership role"""
        content = """
        Innovation Committee
        
        Leading initiative for digital transformation,
        Led team of 5 members,
        Leadership in agile adoption
        """
        
        parsed = FunctionActivityParser.parse_function(content)
        
        assert parsed['involvement_level'] == 'Lead'
    
    def test_minimal_function_parsing(self):
        """Test parsing minimal function information"""
        content = "HR Committee Member"
        
        parsed = FunctionActivityParser.parse_function(content)
        
        assert parsed['function_name'] == "HR Committee Member"
        assert parsed['involvement_level'] in ['Lead', 'Contributor', 'Support']


class TestIntegration:
    """Integration tests for document processing"""
    
    def test_end_to_end_processing(self):
        """Test complete processing pipeline"""
        processor = DocumentProcessor()
        
        sample_pdf_text = """
        PERFORMANCE REVIEW - 2025
        
        1. Previous Year Link
        Link to 2024 annual review: /docs/2024_review.pdf
        
        2. Certifications
        - AWS Solutions Architect Associate
        - Kubernetes Administrator Certified
        - Docker Certified Associate
        
        3. Learning
        Completed courses:
        - Cloud Computing Fundamentals
        - Advanced Python Programming
        - Machine Learning with TensorFlow
        
        4. Feedback
        Demonstrated excellent technical leadership and guidance.
        Strong communication skills with stakeholders.
        Proactive in solving complex problems.
        
        5. Project Activity
        Project: Enterprise Data Platform Migration
        Led the migration of 10+ data warehouses to cloud.
        
        Achievements:
        - Designed scalable architecture
        - Mentored team of 5 engineers
        - Reduced infrastructure costs by 45%
        - Completed on schedule
        
        Duration: Q1 2024 - Q3 2024
        
        6. Function Activity
        Committee: Technical Standards Board
        Led quarterly technical direction meetings.
        Mentored 3 junior developers.
        Organized knowledge sharing workshops.
        """
        
        # Process document
        analysis = processor.process_document(sample_pdf_text, "project")
        
        # Verify all sections found
        assert len(analysis.sections) == 6
        assert analysis.parsing_quality > 0.85
        
        # Verify structured data
        structured = processor.extract_structured_data(analysis)
        assert all(key in structured for key in [
            'previous_year_link', 'certifications', 'learning',
            'feedback', 'project_activity', 'function_activity'
        ])
        
        # Verify specialized parsers work
        project_section = processor.get_section_by_type(
            analysis, SectionType.PROJECT_ACTIVITY
        )
        if project_section:
            project_data = ProjectActivityParser.parse_project(project_section.content)
            assert 'Project_name' in project_data or project_data.get('project_name')
        
        function_section = processor.get_section_by_type(
            analysis, SectionType.FUNCTION_ACTIVITY
        )
        if function_section:
            function_data = FunctionActivityParser.parse_function(function_section.content)
            assert function_data['function_name']
    
    def test_batch_processing_multiple_types(self):
        """Test processing documents of different feedback types"""
        processor = DocumentProcessor()
        
        docs = [
            ("Project A description. 1. Previous Year Link\nRef. 2. Certifications\nCert X. 3. Learning\nCourse Y. 4. Feedback\nPositive. 5. Project Activity\nProject Z. 6. Function Activity\nFunc W.", "project"),
            ("Self feedback. 1. Previous Year Link\nRef. 2. Certifications\nCert. 3. Learning\nCourse. 4. Feedback\nReview. 5. Project Activity\nProject. 6. Function Activity\nFunc.", "self"),
            ("Function feedback. 1. Previous Year Link\nRef. 2. Certifications\nCert. 3. Learning\nCourse. 4. Feedback\nComment. 5. Project Activity\nProject. 6. Function Activity\nFunc.", "function"),
        ]
        
        for text, feedback_type in docs:
            analysis = processor.process_document(text, feedback_type)
            assert analysis.feedback_type == feedback_type
            assert len(analysis.sections) >= 3


@pytest.fixture
def sample_complete_document():
    """Provide a sample complete document for testing"""
    return """
    1. Previous Year Link
    Reference to 2024 profile available at company portal
    
    2. Certifications
    AWS Solutions Architect Associate Certification
    Kubernetes Administrator Certification
    
    3. Learning
    • Machine Learning Fundamentals (Coursera)
    • Advanced Python Programming (DataCamp)
    • Cloud Architecture Best Practices (Pluralsight)
    
    4. Feedback
    Strong technical leadership demonstrated throughout the year.
    Excellent collaboration with cross-functional teams.
    Proactive in mentoring junior developers.
    
    5. Project Activity
    Led migration of legacy applications to microservices architecture.
    
    Key Responsibilities:
    - Design of new architecture
    - Team coordination and mentoring
    - Stakeholder communication
    
    Key Contributions:
    - Reduced deployment time by 60%
    - Improved system reliability to 99.9%
    - Mentored 3 team members
    
    Duration: March 2024 - September 2024
    
    6. Function Activity
    Technical Standards Committee
    
    Activities Performed:
    - Led monthly technical review meetings
    - Established new coding standards
    - Organized quarterly technical workshops
    
    Impact:
    - Improved code quality metrics
    - Enhanced knowledge sharing
    - Increased team competency
    """
