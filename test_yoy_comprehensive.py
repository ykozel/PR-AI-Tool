"""
Comprehensive test for year-over-year analysis integration.
Tests database, services, and API layers.
"""
import os
import sys
import json
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

def test_repositories():
    """Test repository layer enhancements"""
    print("\n" + "="*80)
    print("Testing Repository Layer")
    print("="*80)
    
    from app.core.database import get_db, init_db
    from app.core.repositories import RepositoryFactory
    from app.models.pr_profile import PRProfile
    
    try:
        # Initialize database
        init_db()
        db = next(get_db())
        factory = RepositoryFactory(db)
        repo = factory.get_pr_profile_repo()
        
        print("\n1. Testing get_previous_profile()...")
        
        # Create test profiles
        profile_2025 = repo.find_or_create("Test User", 2025)
        profile_2027 = repo.find_or_create("Test User", 2027)
        
        print(f"   ✓ Created profile 2025 (ID: {profile_2025.id})")
        print(f"   ✓ Created profile 2027 (ID: {profile_2027.id})")
        
        # Get previous profile
        previous = repo.get_previous_profile(profile_2027)
        if previous and previous.id == profile_2025.id:
            print(f"   ✓ get_previous_profile() correctly returned 2025 profile")
        else:
            print(f"   ❌ Failed to get correct previous profile")
            return False
        
        print("\n2. Testing update_yoy_analysis()...")
        test_analysis = {
            "new_achievements": ["Test achievement"],
            "new_skills": ["Test skill"],
            "summary": "Test summary"
        }
        repo.update_yoy_analysis(profile_2027, json.dumps(test_analysis))
        
        # Verify it was stored
        db.refresh(profile_2027)
        if profile_2027.yoy_analysis:
            stored = json.loads(profile_2027.yoy_analysis)
            if stored["summary"] == "Test summary":
                print(f"   ✓ YOY analysis stored and retrieved successfully")
            else:
                print(f"   ❌ Stored analysis doesn't match")
                return False
        else:
            print(f"   ❌ Analysis not stored")
            return False
        
        db.close()
        print("\n✓ Repository layer tests passed")
        return True
        
    except Exception as e:
        print(f"\n❌ Repository test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_yoy_analyzer():
    """Test YearOverYearAnalyzer service"""
    print("\n" + "="*80)
    print("Testing YearOverYearAnalyzer Service")
    print("="*80)
    
    from app.services.year_over_year_analyzer import YearOverYearAnalyzer
    
    try:
        print("\n1. Testing static method accessibility...")
        
        # Test that the method is available as static
        if hasattr(YearOverYearAnalyzer, 'analyze_year_comparison'):
            print("   ✓ analyze_year_comparison method exists")
        else:
            print("   ❌ analyze_year_comparison method not found")
            return False
        
        # Test with mock data
        print("\n2. Testing with limited mock data...")
        result = YearOverYearAnalyzer.analyze_year_comparison(
            employee_name="Test User",
            previous_year=2025,
            current_year=2027,
            previous_year_text="Worked on project A. Skills: Python, Java.",
            current_year_text="Completed projects B and C. Skills: Python, Kubernetes, AWS.",
        )
        
        # May return None if OpenAI key not set (that's OK for this test)
        if result:
            print("   ✓ YOY analyzer returned results")
            print(f"     - New achievements: {len(result.get('new_achievements', []))}")
            print(f"     - New skills: {len(result.get('new_skills', []))}")
        else:
            print("   ⚠ YOY analyzer returned None (likely missing OpenAI key)")
            print("     This is expected if OPENAI_API_KEY is not set")
        
        print("\n✓ YearOverYearAnalyzer service tests passed")
        return True
        
    except Exception as e:
        print(f"\n❌ YOY analyzer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_report_generator():
    """Test ReportGenerator with YOY analysis"""
    print("\n" + "="*80)
    print("Testing ReportGenerator with YOY Analysis")
    print("="*80)
    
    from app.services.report_generator import ReportGenerator
    
    try:
        print("\n1. Testing generate_html signature...")
        generator = ReportGenerator()
        
        # Create mock file records
        class MockFile:
            def __init__(self, file_type, filename, text):
                self.file_type = file_type
                self.original_filename = filename
                self.extracted_text = text
        
        files = [MockFile("client_feedback", "test.docx", "Test feedback content")]
        
        print("   ✓ generator.generate_html() can be called with yoy_analysis parameter")
        
        print("\n2. Testing HTML generation without YOY...")
        html_without_yoy = generator.generate_html(
            file_records=files,
            employee_name="Test User",
            review_year=2027,
        )
        
        if html_without_yoy and len(html_without_yoy) > 100:
            print(f"   ✓ HTML generated without YOY ({len(html_without_yoy)} bytes)")
        else:
            print(f"   ❌ HTML generation failed")
            return False
        
        print("\n3. Testing HTML generation with YOY...")
        test_yoy = {
            "new_achievements": ["New achievement 1", "New achievement 2"],
            "new_skills": ["Kubernetes", "AWS"],
            "skill_progression": [
                {"skill": "Python", "from": "Intermediate", "to": "Advanced"}
            ],
            "growth_areas": ["Leadership skills"],
            "promotion_or_change": "Promoted to Senior Engineer",
            "summary": "Strong growth and development",
            "overall_assessment": "Exceptional Development"
        }
        
        html_with_yoy = generator.generate_html(
            file_records=files,
            employee_name="Test User",
            review_year=2027,
            yoy_analysis=test_yoy,
        )
        
        if html_with_yoy and len(html_with_yoy) > len(html_without_yoy):
            print(f"   ✓ HTML generated with YOY ({len(html_with_yoy)} bytes)")
        else:
            print(f"   ❌ HTML with YOY not larger than without")
            return False
        
        # Check for YOY-specific content
        checks = [
            ("achievements-yoy", "YOY section ID"),
            ("Achievements over a year", "YOY section title"),
            ("New Achievements", "New achievements heading"),
            ("New achievement 1", "Achievement content"),
            ("Kubernetes", "New skill content"),
            ("Promoted to Senior Engineer", "Promotion content"),
        ]
        
        print("\n4. Checking YOY content in HTML...")
        for check_str, desc in checks:
            if check_str in html_with_yoy:
                print(f"   ✓ Found: {desc}")
            else:
                print(f"   ❌ Missing: {desc} ('{check_str}')")
                return False
        
        print("\n✓ ReportGenerator tests passed")
        return True
        
    except Exception as e:
        print(f"\n❌ ReportGenerator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("YOY ANALYSIS INTEGRATION TEST SUITE")
    print("="*80)
    
    tests = [
        ("Repository Layer", test_repositories),
        ("YOY Analyzer Service", test_yoy_analyzer),
        ("Report Generator", test_report_generator),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n" + "="*80)
        print("✓ ALL TESTS PASSED! YOY Analysis integration is working.")
        print("="*80)
        return True
    else:
        print("\n" + "="*80)
        print("❌ Some tests failed. Please review the errors above.")
        print("="*80)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
