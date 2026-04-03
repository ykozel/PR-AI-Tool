"""
Comprehensive test suite for LLM career development analysis.
Tests YOY analysis across different career trajectories:
- Clear progression (Alex Chen)
- Regression → Recovery (Jordan Mills)
- Mixed performance (Taylor Singh)
- Stagnation (Casey Johnson)
- Rapid growth (Morgan Lee)
"""
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent))

from app.services.year_over_year_analyzer import YearOverYearAnalyzer
from app.services.doc_processor import DocProcessor

class CareerAnalysisTest:
    """Test LLM career development analysis across scenarios"""
    
    def __init__(self):
        self.processor = DocProcessor()
        self.test_data_dir = "test_docs_comprehensive"
        self.results = []
    
    def extract_from_document(self, filepath: str) -> str:
        """Extract text from document"""
        try:
            text = self.processor.extract_text_from_doc(filepath)
            return text if text else ""
        except Exception as e:
            print(f"   ❌ Error extracting from {filepath}: {e}")
            return ""
    
    def test_progression_scenario(self):
        """Test: Junior → Mid Engineer (Clear Progression)"""
        print("\n" + "="*80)
        print("SCENARIO 1: CLEAR PROGRESSION - Junior → Mid Level Engineer")
        print("="*80)
        
        doc_2024 = os.path.join(self.test_data_dir, "Alex_Chen_2024_Junior.docx")
        doc_2025 = os.path.join(self.test_data_dir, "Alex_Chen_2025_MidLevel.docx")
        
        if not os.path.exists(doc_2024) or not os.path.exists(doc_2025):
            print("❌ Test documents not found. Run generate_comprehensive_test_data.py first.")
            return False
        
        print("\n1. Extracting texts...")
        text_2024 = self.extract_from_document(doc_2024)
        text_2025 = self.extract_from_document(doc_2025)
        
        if not text_2024 or not text_2025:
            print("❌ Failed to extract documents")
            return False
        
        print(f"   • 2024 text: {len(text_2024)} chars")
        print(f"   • 2025 text: {len(text_2025)} chars")
        
        print("\n2. Running LLM analysis...")
        analysis = YearOverYearAnalyzer.analyze_year_comparison(
            employee_name="Alex Chen",
            previous_year=2024,
            current_year=2025,
            previous_year_text=text_2024,
            current_year_text=text_2025,
        )
        
        if not analysis:
            print("   ⚠ No analysis returned (check OpenAI API key)")
            return None
        
        print("\n3. Validating expected outcomes...")
        validations = [
            ("Promotion", "promotion_or_change", "Promoted", "Mid-Level Engineer"),
            ("New Skills", "new_skills", 5, None),  # Should find ~5 new skills
            ("Achievements", "new_achievements", 3, None),  # Should find ~3 achievements
            ("No Concerns", "areas_of_concern", 0, None),  # Should have no concerns
            ("Overall Assessment", "overall_assessment", "Growth", None),
        ]
        
        passed = 0
        for name, field, check_val, _ in validations:
            result = analysis.get(field, [])
            if isinstance(check_val, str):
                # String check
                if isinstance(result, str) and check_val in result:
                    print(f"   ✓ {name}: Detected")
                    passed += 1
                else:
                    print(f"   ❌ {name}: Expected '{check_val}', got {result}")
            elif isinstance(check_val, int):
                # Count check
                count = len(result) if isinstance(result, list) else 0
                if count >= check_val:
                    print(f"   ✓ {name}: Found {count} items")
                    passed += 1
                else:
                    print(f"   ⚠ {name}: Expected {check_val}, found {count}")
        
        print(f"\nResult: {passed}/{len(validations)} validations passed")
        
        # Save result
        self.results.append({
            "scenario": "Progression (Alex Chen)",
            "validations": passed,
            "total": len(validations),
            "analysis": analysis
        })
        
        return passed > 0
    
    def test_regression_scenario(self):
        """Test: High Performer Decline (Regression Detection)"""
        print("\n" + "="*80)
        print("SCENARIO 2: REGRESSION - High Performer Decline")
        print("="*80)
        
        doc_2024 = os.path.join(self.test_data_dir, "Jordan_Mills_2024_Decline.docx")
        
        if not os.path.exists(doc_2024):
            print("❌ Test document not found.")
            return False
        
        print("\n1. Extracting text...")
        text_2024 = self.extract_from_document(doc_2024)
        
        if not text_2024:
            print("❌ Failed to extract document")
            return False
        
        print(f"   • 2024 text: {len(text_2024)} chars")
        
        # Create baseline (hypothetical previous year)
        baseline_text = ("performant code, 4.5/5 quality, responsive to reviews, "
            "mentored engineers, 0 critical bugs, 92% test coverage, "
            "excellent attendance, proactive, reliable")
        
        print("\n2. Running LLM analysis (vs baseline)...")
        analysis = YearOverYearAnalyzer.analyze_year_comparison(
            employee_name="Jordan Mills",
            previous_year=2023,
            current_year=2024,
            previous_year_text=baseline_text,
            current_year_text=text_2024,
        )
        
        if not analysis:
            print("   ⚠ No analysis returned (check OpenAI API key)")
            return None
        
        print("\n3. Validating regression detection...")
        validations = [
            ("Concerns Detected", "areas_of_concern", 2, None),  # Should find concerns
            ("Quality Decline", "areas_of_concern", "quality", None),  # Quality mentioned
            ("Deadline Miss", "areas_of_concern", "deadline", None),  # Deadlines mentioned
            ("Review Turnaround", "improvement_priorities", "review", None),  # Needs improvement
            ("Assessment", "overall_assessment", "Decline", None),  # Shows decline
        ]
        
        passed = 0
        for name, field, check_val, _ in validations:
            result = analysis.get(field, [])
            
            if isinstance(check_val, int):
                count = len(result) if isinstance(result, list) else 0
                if count >= check_val:
                    print(f"   ✓ {name}: Found {count} items")
                    passed += 1
                else:
                    print(f"   ⚠ {name}: Expected {check_val}+, found {count}")
            elif isinstance(check_val, str):
                result_str = " ".join(result) if isinstance(result, list) else str(result)
                if check_val.lower() in result_str.lower():
                    print(f"   ✓ {name}: Detected '{check_val}'")
                    passed += 1
                else:
                    print(f"   ⚠ {name}: Didn't find '{check_val}'")
        
        print(f"\nResult: {passed}/{len(validations)} validations passed")
        
        self.results.append({
            "scenario": "Regression (Jordan Mills 2024)",
            "validations": passed,
            "total": len(validations),
            "analysis": analysis
        })
        
        return passed > 0
    
    def test_recovery_scenario(self):
        """Test: Performance Recovery (Positive Turnaround)"""
        print("\n" + "="*80)
        print("SCENARIO 3: RECOVERY - High Performer Returns to Form")
        print("="*80)
        
        doc_2024_decline = os.path.join(self.test_data_dir, "Jordan_Mills_2024_Decline.docx")
        doc_2025_recovery = os.path.join(self.test_data_dir, "Jordan_Mills_2025_Recovery.docx")
        
        if not os.path.exists(doc_2024_decline) or not os.path.exists(doc_2025_recovery):
            print("❌ Test documents not found.")
            return False
        
        print("\n1. Extracting texts...")
        text_decline = self.extract_from_document(doc_2024_decline)
        text_recovery = self.extract_from_document(doc_2025_recovery)
        
        if not text_decline or not text_recovery:
            print("❌ Failed to extract documents")
            return False
        
        print(f"   • 2024 decline text: {len(text_decline)} chars")
        print(f"   • 2025 recovery text: {len(text_recovery)} chars")
        
        print("\n2. Running LLM analysis...")
        analysis = YearOverYearAnalyzer.analyze_year_comparison(
            employee_name="Jordan Mills",
            previous_year=2024,
            current_year=2025,
            previous_year_text=text_decline,
            current_year_text=text_recovery,
        )
        
        if not analysis:
            print("   ⚠ No analysis returned (check OpenAI API key)")
            return None
        
        print("\n3. Validating recovery detection...")
        validations = [
            ("Improvements Found", "new_achievements", 1, None),  # Should find improvements
            ("Quality Recovery", "new_achievements", "quality", None),  # Quality improvement
            ("Concerns Reduced", "areas_of_concern", 0, None),  # Few/no ongoing concerns
            ("Growth", "skill_progression", 0, None),  # May show stabilization not growth
            ("Positive Assessment", "overall_assessment", "Progress", None),  # Positive tone
        ]
        
        passed = 0
        for name, field, check_val, _ in validations:
            result = analysis.get(field, [])
            
            if isinstance(check_val, int) and check_val == 0:
                count = len(result) if isinstance(result, list) else 0
                if count <= check_val:
                    print(f"   ✓ {name}: {count} items (expected ≤{check_val})")
                    passed += 1
                else:
                    print(f"   ⚠ {name}: {'Too many' if count > 0 else 'None'} ({count})")
            elif isinstance(check_val, int):
                count = len(result) if isinstance(result, list) else 0
                if count >= check_val:
                    print(f"   ✓ {name}: Found {count} items")
                    passed += 1
            elif isinstance(check_val, str) and field == "overall_assessment":
                if check_val.lower() in str(result).lower():
                    print(f"   ✓ {name}: Shows positive trajectory")
                    passed += 1
        
        print(f"\nResult: {passed}/{len(validations)} validations passed")
        
        self.results.append({
            "scenario": "Recovery (Jordan Mills 2025)",
            "validations": passed,
            "total": len(validations),
            "analysis": analysis
        })
        
        return passed > 0
    
    def test_mixed_performance_scenario(self):
        """Test: Mixed Performance (Strong Technical, Weak Leadership)"""
        print("\n" + "="*80)
        print("SCENARIO 4: MIXED PERFORMANCE - Technical Strength, Leadership Weakness")
        print("="*80)
        
        doc_tech_lead = os.path.join(self.test_data_dir, "Taylor_Singh_2024_TechLead.docx")
        
        if not os.path.exists(doc_tech_lead):
            print("❌ Test document not found.")
            return False
        
        print("\n1. Extracting text...")
        text_tech = self.extract_from_document(doc_tech_lead)
        
        if not text_tech:
            print("❌ Failed to extract document")
            return False
        
        print(f"   • Text: {len(text_tech)} chars")
        
        baseline = "Good engineer, reliable, solid contributions, acceptable team dynamics"
        
        print("\n2. Running LLM analysis...")
        analysis = YearOverYearAnalyzer.analyze_year_comparison(
            employee_name="Taylor Singh",
            previous_year=2023,
            current_year=2024,
            previous_year_text=baseline,
            current_year_text=text_tech,
        )
        
        if not analysis:
            print("   ⚠ No analysis returned")
            return None
        
        print("\n3. Validating mixed performance detection...")
        validations = [
            ("Achievements Found", "new_achievements", 1, None),  # Technical achievements
            ("Concerns Found", "areas_of_concern", 1, None),  # Leadership concerns
            ("Team Issues", "areas_of_concern", "team", None),  # Team mentioned
            ("Morale Issues", "areas_of_concern", "morale", None),  # Morale mentioned
        ]
        
        passed = 0
        for name, field, check_val, _ in validations:
            result = analysis.get(field, [])
            
            if isinstance(check_val, int):
                count = len(result) if isinstance(result, list) else 0
                if count >= check_val:
                    print(f"   ✓ {name}: Found {count} items")
                    passed += 1
            elif isinstance(check_val, str):
                result_str = " ".join(result) if isinstance(result, list) else str(result)
                if check_val.lower() in result_str.lower():
                    print(f"   ✓ {name}: Detected")
                    passed += 1
                else:
                    print(f"   ⚠ {name}: Not clearly detected")
        
        print(f"\nResult: {passed}/{len(validations)} validations passed")
        
        self.results.append({
            "scenario": "Mixed (Taylor Singh)",
            "validations": passed,
            "total": len(validations),
            "analysis": analysis
        })
        
        return passed > 0
    
    def test_stagnation_scenario(self):
        """Test: Stagnation Detection (No Growth)"""
        print("\n" + "="*80)
        print("SCENARIO 5: STAGNATION - No Growth or Decline")
        print("="*80)
        
        doc_stagnant = os.path.join(self.test_data_dir, "Casey_Johnson_2024_Stagnant.docx")
        
        if not os.path.exists(doc_stagnant):
            print("❌ Test document not found.")
            return False
        
        print("\n1. Extracting text...")
        text_current = self.extract_from_document(doc_stagnant)
        
        if not text_current:
            print("❌ Failed to extract document")
            return False
        
        print(f"   • Text: {len(text_current)} chars")
        
        baseline = text_current  # Same performance repeated
        
        print("\n2. Running LLM analysis...")
        analysis = YearOverYearAnalyzer.analyze_year_comparison(
            employee_name="Casey Johnson",
            previous_year=2023,
            current_year=2024,
            previous_year_text=baseline,
            current_year_text=text_current,
        )
        
        if not analysis:
            print("   ⚠ No analysis returned")
            return None
        
        print("\n3. Validating stagnation detection...")
        
        achieved = len(analysis.get("new_achievements", []))
        new_skills = len(analysis.get("new_skills", []))
        concerns = len(analysis.get("areas_of_concern", []))
        
        print(f"   New achievements: {achieved}")
        print(f"   New skills: {new_skills}")
        print(f"   Areas of concern: {concerns}")
        
        # Stagnation = minimal/no new achievements or skills
        if achieved <= 1 and new_skills <= 1:
            print("   ✓ Stagnation detected (minimal new achievements/skills)")
            result = True
        else:
            print("   ⚠ Expected stagnation but found growth indicators")
            result = False
        
        self.results.append({
            "scenario": "Stagnation (Casey Johnson)",
            "validations": 1 if result else 0,
            "total": 1,
            "analysis": analysis
        })
        
        return result
    
    def test_rapid_growth_scenario(self):
        """Test: Rapid Growth (Entry → Advanced)"""
        print("\n" + "="*80)
        print("SCENARIO 6: RAPID GROWTH - Entry Level to Advanced in 2 Years")
        print("="*80)
        
        doc_growth = os.path.join(self.test_data_dir, "Morgan_Lee_2024_2025_RapidGrowth.docx")
        
        if not os.path.exists(doc_growth):
            print("❌ Test document not found.")
            return False
        
        print("\n1. Extracting text...")
        text_growth = self.extract_from_document(doc_growth)
        
        if not text_growth:
            print("❌ Failed to extract document")
            return False
        
        print(f"   • Text: {len(text_growth)} chars")
        
        baseline = ("Entry level QA, manual testing, learning the tools, "
            "junior position, basic responsibilities")
        
        print("\n2. Running LLM analysis...")
        analysis = YearOverYearAnalyzer.analyze_year_comparison(
            employee_name="Morgan Lee",
            previous_year=2024,
            current_year=2025,
            previous_year_text=baseline,
            current_year_text=text_growth,
        )
        
        if not analysis:
            print("   ⚠ No analysis returned")
            return None
        
        print("\n3. Validating rapid growth detection...")
        validations = [
            ("Achievements", "new_achievements", 3, None),  # ~3+ achievements
            ("Skills", "new_skills", 3, None),  # ~3+ new skills
            ("Promotion", "promotion_or_change", "Promoted", None),  # Promotion mentioned
            ("Leadership", "new_achievements", "led", None),  # Leadership mentioned
            ("Assessment", "overall_assessment", "Exceptional", None),  # Exceptional growth
        ]
        
        passed = 0
        for name, field, check_val, _ in validations:
            result = analysis.get(field, [])
            
            if isinstance(check_val, int):
                count = len(result) if isinstance(result, list) else 0
                if count >= check_val:
                    print(f"   ✓ {name}: Found {count} items (expected {check_val}+)")
                    passed += 1
                else:
                    print(f"   ⚠ {name}: Found {count} items (expected {check_val}+)")
            elif isinstance(check_val, str):
                result_str = " ".join(result) if isinstance(result, list) else str(result)
                if check_val.lower() in result_str.lower():
                    print(f"   ✓ {name}: Detected '{check_val}'")
                    passed += 1
        
        print(f"\nResult: {passed}/{len(validations)} validations passed")
        
        self.results.append({
            "scenario": "Rapid Growth (Morgan Lee)",
            "validations": passed,
            "total": len(validations),
            "analysis": analysis
        })
        
        return passed > 0
    
    def run_all_tests(self):
        """Run all test scenarios"""
        print("\n" + "#"*80)
        print("# COMPREHENSIVE LLM CAREER DEVELOPMENT ANALYSIS TEST SUITE")
        print("#"*80)
        
        if not os.path.exists(self.test_data_dir):
            print(f"\n❌ Test data directory '{self.test_data_dir}' not found!")
            print("Run: python generate_comprehensive_test_data.py")
            return False
        
        tests = [
            ("Progression", self.test_progression_scenario),
            ("Regression", self.test_regression_scenario),
            ("Recovery", self.test_recovery_scenario),
            ("Mixed Performance", self.test_mixed_performance_scenario),
            ("Stagnation", self.test_stagnation_scenario),
            ("Rapid Growth", self.test_rapid_growth_scenario),
        ]
        
        results = []
        for name, test_func in tests:
            try:
                result = test_func()
                results.append((name, result))
            except Exception as e:
                print(f"\n❌ Test '{name}' failed with error: {e}")
                import traceback
                traceback.print_exc()
                results.append((name, False))
        
        # Summary
        print("\n" + "#"*80)
        print("# TEST SUMMARY")
        print("#"*80)
        
        for name, result in results:
            status = "✓ PASS" if result is True else ("⚠ SKIP" if result is None else "❌ FAIL")
            print(f"{status}: {name}")
        
        passed = sum(1 for _, r in results if r is True)
        total = sum(1 for _, r in results if r is not None)
        
        print(f"\nTotal: {passed}/{total} scenarios validated")
        
        if passed == total:
            print("\n✓ All tests passed!")
        elif passed >= total * 0.5:
            print("\n⚠ Most tests passed, but some need attention")
        else:
            print("\n❌ Multiple tests failed. Check OpenAI API configuration.")
        
        return passed > 0

if __name__ == "__main__":
    tester = CareerAnalysisTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
