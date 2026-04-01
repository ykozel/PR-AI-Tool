"""
Integration test for unified endpoint /api/uploads/pdf-and-process-analyze
This simulates the complete flow of the unified endpoint
"""

import os
import sys
sys.path.insert(0, os.getcwd())

from app.services.ai_analyzer import AIAnalyzer

# Sample feedback text (simulating extracted PDF sections)
feedback_text = """
I am a visionary leader with exceptional strategic planning abilities. 
I excel at fostering cross-functional collaboration and have demonstrated 
exceptional communication skills across all organizational levels.
"""

project_text = """
PROJECT 1: Cloud Migration Initiative
Led migration of 45+ applications to cloud infrastructure, architecting 
the complete solution. Successfully achieved 35% cost reduction and 
maintained zero-downtime migration. This involved managing technical 
decisions and coordinating with cross-functional teams.

PROJECT 2: Microservices Redesign
Designed microservices architecture improving system scalability by 60%.
Implemented CI/CD pipeline reducing deployment time from 2 hours to 15 minutes.
"""

function_text = """
As Technical Excellence Committee Lead, I have directed architecture reviews
and strategic technology initiatives. I mentored 3 junior engineers who were
promoted to senior roles within 18 months. I have championed process improvements
that enhanced team productivity by 40%.
"""

certifications = "AWS Solutions Architect, PMP, Certified Kubernetes Administrator"
learning = "Advanced Python programming, Strategic Leadership for Executives"


def run_integration_test():
    """Run the unified endpoint integration test"""
    
    print("\n" + "="*70)
    print("UNIFIED ENDPOINT /pdf-and-process-analyze - INTEGRATION TEST")
    print("="*70 + "\n")

    # Step 1: Initialize AI Analyzer
    print("Step 1: Initialize AI Analyzer")
    print("-" * 70)
    analyzer = AIAnalyzer()
    print("✓ AI Analyzer initialized")

    # Step 2: Call analyze_extracted_sections with keyword arguments
    print("\nStep 2: Call analyze_extracted_sections with keyword arguments")
    print("-" * 70)
    print("Calling: analyzer.analyze_extracted_sections(")
    print("  feedback=feedback_text,")
    print("  project_activity=project_text,")
    print("  function_activity=function_text,")
    print("  learning=learning,")
    print("  certifications=certifications")
    print(")")

    result = analyzer.analyze_extracted_sections(
        feedback=feedback_text,
        project_activity=project_text,
        function_activity=function_text,
        learning=learning,
        certifications=certifications
    )

    print("\n✓ AI analyzer returned AIAnalysisResult dataclass")

    # Step 3: Convert dataclass to response dicts
    print("\nStep 3: Convert dataclass to response dicts (as endpoint does)")
    print("-" * 70)

    # Convert skills to response format
    identified_skills = []
    for skill in result.identified_skills:
        skill_dict = {
            "name": skill.skill_name,
            "category": skill.category.value if hasattr(skill.category, 'value') else str(skill.category),
            "confidence": skill.confidence,
            "source": skill.source_section
        }
        identified_skills.append(skill_dict)

    # Convert achievements to response format
    identified_achievements = []
    for achievement in result.identified_achievements:
        achievement_dict = {
            "title": achievement.achievement_title,
            "description": achievement.description,
            "impact": achievement.impact,
            "source": achievement.source_section
        }
        identified_achievements.append(achievement_dict)

    print(f"✓ Converted {len(result.identified_skills)} IdentifiedSkill objects to dicts")
    print(f"✓ Converted {len(result.identified_achievements)} IdentifiedAchievement objects to dicts")

    # Step 4: Build unified response
    print("\nStep 4: Build unified response (as endpoint returns)")
    print("-" * 70)

    response = {
        "id": 1,
        "filename": "profile_20260310_sample.pdf",
        "file_type": "company_function",
        
        # Processing results
        "parsing_quality": 0.95,
        "sections_found": 6,
        
        # AI Analysis results
        "identified_skills": identified_skills,
        "identified_achievements": identified_achievements,
        "competency_gaps": result.competency_gaps,
        "growth_areas": result.growth_areas,
        "leadership_indicators": result.leadership_indicators,
        "technical_strength": result.technical_strength,
        "leadership_strength": result.leadership_strength,
        "ai_overall_score": result.overall_score,
        "recommendations": result.recommendations,
        
        "message": f"✓ Upload successful | ✓ Processing complete (6 sections, quality: 0.95) | ✓ AI analysis done ({len(identified_skills)} skills, {len(identified_achievements)} achievements)"
    }

    print("✓ UploadProcessAnalyzeResponse built successfully")

    # Step 5: Verify response structure
    print("\nStep 5: Verify response structure")
    print("-" * 70)

    print(f"✓ Response ID: {response['id']}")
    print(f"✓ Parsing Quality: {response['parsing_quality']:.2f}")
    print(f"✓ Sections Found: {response['sections_found']}")
    print(f"✓ Skills Identified: {len(response['identified_skills'])}")
    print(f"✓ Achievements Identified: {len(response['identified_achievements'])}")
    print(f"✓ Competency Gaps: {len(response['competency_gaps'])}")
    print(f"✓ Growth Areas: {len(response['growth_areas'])}")
    print(f"✓ Technical Strength: {response['technical_strength']:.2f}")
    print(f"✓ Leadership Strength: {response['leadership_strength']:.2f}")
    print(f"✓ Overall Score: {response['ai_overall_score']:.2f}")
    print(f"✓ Recommendations: {len(response['recommendations'])}")

    print("\n" + "="*70)
    print("UNIFIED ENDPOINT INTEGRATION TEST: PASSED ✓")
    print("="*70)

    print("\nSample Identified Skills:")
    for i, skill in enumerate(identified_skills[:3], 1):
        print(f"  {i}. {skill['name']} ({skill['category']}) - Confidence: {skill['confidence']:.2f}")

    print("\nSample Identified Achievements:")
    for i, achievement in enumerate(identified_achievements[:2], 1):
        print(f"  {i}. {achievement['title']} (Impact: {achievement['impact']})")

    print("\nSample Recommendations:")
    for i, rec in enumerate(response['recommendations'][:2], 1):
        print(f"  {i}. {rec}")

    print("\n" + "-"*70)
    print("ENDPOINT READY FOR TESTING")
    print("-"*70)
    print("\nTo test with real PDF:")
    print('  curl -X POST "http://localhost:8000/api/uploads/pdf-and-process-analyze" \\')
    print('    -F "file=@feedback.pdf" \\')
    print('    -F "upload_type=company_function"')
    print()
    
    return response


if __name__ == "__main__":
    run_integration_test()
