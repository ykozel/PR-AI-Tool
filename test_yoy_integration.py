"""
Test script to verify year-over-year analysis integration.
Tests the complete flow: upload documents for 2025 and 2027, verify yearover-year analysis is generated.
"""
import os
import sys
import json
from datetime import datetime

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db, init_db
from app.core.repositories import RepositoryFactory
from app.models.pr_profile import PRProfile
from app.models.file import UploadedFile
from app.services.report_generator import ReportGenerator
from app.services.year_over_year_analyzer import YearOverYearAnalyzer
from sqlalchemy.orm import Session

def test_yoy_analysis_integration():
    """Test complete YOY analysis flow"""
    
    # Setup database
    init_db()
    db = next(get_db())
    factory = RepositoryFactory(db)
    
    try:
        print("=" * 80)
        print("Testing Year-over-Year Analysis Integration")
        print("=" * 80)
        
        # Check if we have test documents
        test_docs_dir = "test_docs"
        emma_2025_client = os.path.join(test_docs_dir, "Emma_Laurent_Client_Feedback_2025.docx")
        emma_2025_pdp = os.path.join(test_docs_dir, "Emma_Laurent_PDP_2025_2026.docx")
        emma_2027_client = os.path.join(test_docs_dir, "Emma_Laurent_Client_Feedback_2027.docx")
        emma_2027_pdp = os.path.join(test_docs_dir, "Emma_Laurent_PDP_2027_2028.docx")
        
        required_docs = [emma_2025_client, emma_2025_pdp, emma_2027_client, emma_2027_pdp]
        missing = [d for d in required_docs if not os.path.exists(d)]
        
        if missing:
            print(f"\n❌ Missing test documents: {missing}")
            print("   Please ensure 2025 and 2027 test documents exist in test_docs/")
            return False
        
        print("\n✓ Test documents found")
        
        # Extract text from test documents manually
        from app.services.doc_processor import DocProcessor
        processor = DocProcessor()
        
        print("\n1. Extracting text from 2025 documents...")
        text_2025_client = processor.extract_text_from_doc(emma_2025_client)
        text_2025_pdp = processor.extract_text_from_doc(emma_2025_pdp)
        
        print(f"   - Client feedback 2025: {len(text_2025_client) if text_2025_client else 0} chars")
        print(f"   - PDP 2025: {len(text_2025_pdp) if text_2025_pdp else 0} chars")
        
        print("\n2. Extracting text from 2027 documents...")
        text_2027_client = processor.extract_text_from_doc(emma_2027_client)
        text_2027_pdp = processor.extract_text_from_doc(emma_2027_pdp)
        
        print(f"   - Client feedback 2027: {len(text_2027_client) if text_2027_client else 0} chars")
        print(f"   - PDP 2027: {len(text_2027_pdp) if text_2027_pdp else 0} chars")
        
        # Combine texts
        print("\n3. Combining texts by year...")
        text_2025_combined = f"[CLIENT_FEEDBACK]\n{text_2025_client}\n\n[PDP]\n{text_2025_pdp}"
        text_2027_combined = f"[CLIENT_FEEDBACK]\n{text_2027_client}\n\n[PDP]\n{text_2027_pdp}"
        
        print(f"   - 2025 combined: {len(text_2025_combined)} chars")
        print(f"   - 2027 combined: {len(text_2027_combined)} chars")
        
        # Test YOY analyzer
        print("\n4. Testing YearOverYearAnalyzer...")
        print("   Calling analyze_year_comparison()...")
        
        yoy_result = YearOverYearAnalyzer.analyze_year_comparison(
            employee_name="Emma Laurent",
            previous_year=2025,
            current_year=2027,
            previous_year_text=text_2025_combined,
            current_year_text=text_2027_combined,
        )
        
        if not yoy_result:
            print("   ❌ YOY analyzer returned no results")
            return False
        
        print("   ✓ YOY analysis generated successfully")
        print("\n5. YOY Analysis Results:")
        print(f"   - New achievements: {len(yoy_result.get('new_achievements', []))} found")
        print(f"   - New skills: {len(yoy_result.get('new_skills', []))} found")
        print(f"   - Skill progression: {len(yoy_result.get('skill_progression', []))} found")
        print(f"   - Growth areas: {len(yoy_result.get('growth_areas', []))} found")
        
        # Print some sample results
        if yoy_result.get("summary"):
            print(f"\n   Summary: {yoy_result['summary'][:100]}...")
        
        if yoy_result.get("new_achievements"):
            print(f"\n   Sample new achievements:")
            for achievement in yoy_result["new_achievements"][:2]:
                print(f"     - {achievement}")
        
        if yoy_result.get("new_skills"):
            print(f"\n   Sample new skills:")
            for skill in yoy_result["new_skills"][:2]:
                print(f"     - {skill}")
        
        # Test report generator with YOY analysis
        print("\n6. Testing ReportGenerator with YOY analysis...")
        
        # Create mock file records for generator
        class MockFileRecord:
            def __init__(self, file_type, filename, text):
                self.file_type = file_type
                self.original_filename = filename
                self.extracted_text = text
        
        files_2027 = [
            MockFileRecord("client_feedback", "Client_Feedback_2027.docx", text_2027_client),
            MockFileRecord("pdp", "PDP_2027_2028.docx", text_2027_pdp),
        ]
        
        generator = ReportGenerator()
        html = generator.generate_html(
            file_records=files_2027,
            employee_name="Emma Laurent",
            review_year=2027,
            year_hierarchy={
                "current_year": 2027,
                "all_years": [2025, 2027],
                "previous_year": 2025,
                "next_year": None,
                "person_name": "Emma Laurent",
            },
            yoy_analysis=yoy_result,
        )
        
        if not html:
            print("   ❌ HTML generation failed")
            return False
        
        print("   ✓ HTML generated successfully")
        
        # Check if YOY section exists in HTML
        if "achievements-yoy" in html and "Achievements over a year" in html:
            print("   ✓ YOY section found in HTML")
        else:
            print("   ⚠ YOY section not found in HTML")
        
        # Save HTML for manual inspection
        output_file = "test_yoy_report.html"
        with open(output_file, "w") as f:
            f.write(html)
        print(f"\n   Generated report saved to: {output_file}")
        
        print("\n" + "=" * 80)
        print("✓ All YOY analysis integration tests passed!")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_yoy_analysis_integration()
    sys.exit(0 if success else 1)
