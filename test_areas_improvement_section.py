"""
Quick test to verify "What went wrong" section is generated correctly.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def test_areas_for_improvement():
    """Test the new areas for improvement section"""
    print("\n" + "="*80)
    print("Testing 'What went wrong and needs to be improved' Section")
    print("="*80)
    
    from app.services.report_generator import ReportGenerator
    
    try:
        print("\n1. Testing HTML generation with concerns...")
        generator = ReportGenerator()
        
        # Create mock file records
        class MockFile:
            def __init__(self, file_type, filename, text):
                self.file_type = file_type
                self.original_filename = filename
                self.extracted_text = text
        
        files = [MockFile("client_feedback", "test.docx", "Test feedback content")]
        
        # Create comprehensive YOY analysis with concerns
        test_yoy = {
            "new_achievements": ["New achievement 1"],
            "new_skills": ["Kubernetes"],
            "skill_progression": [
                {"skill": "Python", "from": "Intermediate", "to": "Advanced"}
            ],
            "growth_areas": ["Leadership skills"],
            "promotion_or_change": "Promoted to Senior Engineer",
            "summary": "Mixed performance year",
            "overall_assessment": "Needs Improvement",
            
            # NEW: Areas that went wrong
            "areas_of_concern": [
                "Code quality metrics declined 15% year-over-year",
                "Missed 3 critical project deadlines",
                "Reduced team collaboration and communication",
                "Technical debt increased significantly"
            ],
            "improvement_priorities": [
                "Focus on code quality and testing practices",
                "Develop project management and planning skills",
                "Improve communication and documentation",
                "Address technical debt systematically"
            ],
            "unmet_goals": [
                "Failed to complete AWS certification by Q4 2025",
                "Did not mentor junior team members as committed",
                "Architecture redesign project incomplete"
            ],
            "feedback_gaps": [
                "Self-assessment rated performance as 'Good' but peer feedback suggests 'Needs Improvement'",
                "Committed to mentoring 2 developers but only worked with 1",
                "Planned 2 technical talks but delivered 0"
            ],
            "overall_concerns": "While technical skills improved, overall performance and reliability concerns emerged. Project delivery and team collaboration need immediate attention."
        }
        
        html = generator.generate_html(
            file_records=files,
            employee_name="Test User",
            review_year=2027,
            yoy_analysis=test_yoy,
        )
        
        if not html:
            print("   ❌ HTML generation failed")
            return False
        
        print("   ✓ HTML generated successfully")
        
        # Verify all sections are present
        print("\n2. Checking for 'What went wrong' section...")
        
        checks = [
            ("areas-for-improvement-yoy", "Section ID"),
            ("What went wrong and needs to be improved", "Section title"),
            ("Areas of Concern", "Concerns heading"),
            ("Code quality metrics declined", "Concern content"),
            ("Missed 3 critical project deadlines", "Concern content 2"),
            ("Unmet Goals from Previous Year", "Unmet goals heading"),
            ("Failed to complete AWS certification", "Unmet goal content"),
            ("Priority Areas for Next Review Period", "Priorities heading"),
            ("Focus on code quality", "Priority content"),
            ("Feedback Gaps and Discrepancies", "Feedback gaps heading"),
            ("Self-assessment rated performance", "Gap content"),
            ("While technical skills improved", "Overall concerns summary"),
        ]
        
        missing = []
        for check_str, desc in checks:
            if check_str in html:
                print(f"   ✓ Found: {desc}")
            else:
                print(f"   ❌ Missing: {desc}")
                missing.append(desc)
        
        if missing:
            return False
        
        # Verify TOC includes the new link
        print("\n3. Checking Table of Contents...")
        if 'href="#areas-for-improvement-yoy"' in html:
            print("   ✓ TOC link to 'What went wrong' section present")
        else:
            print("   ❌ TOC link missing")
            return False
        
        # Save HTML for inspection
        output_file = "test_areas_improvement.html"
        with open(output_file, "w") as f:
            f.write(html)
        print(f"\n   Generated report saved to: {output_file}")
        
        print("\n" + "="*80)
        print("✓ All tests passed! 'What went wrong' section working correctly.")
        print("="*80)
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_areas_for_improvement()
    sys.exit(0 if success else 1)
