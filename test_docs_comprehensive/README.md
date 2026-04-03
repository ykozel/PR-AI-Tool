# Test Dataset Documentation

## Overview

This dataset contains **9 performance review documents** for **3 personas**, each with three document types (Client Feedback, Project Feedback, PDP). Use these to test the full upload-and-report pipeline.

## 📂 Files

```
test_docs_comprehensive/
├── 13_Elena_Rodriguez_2025_ClientFeedback.docx
├── 13_Elena_Rodriguez_2025_PDP.docx
├── 13_Elena_Rodriguez_2025_ProjectFeedback.docx
├── 14_James_Park_2025_ClientFeedback.docx
├── 14_James_Park_2025_PDP.docx
├── 14_James_Park_2025_ProjectFeedback.docx
├── 15_Priya_Sharma_2025_ClientFeedback.docx
├── 15_Priya_Sharma_2025_PDP.docx
└── 15_Priya_Sharma_2025_ProjectFeedback.docx
```

## 👥 Personas

| # | Name | Persona |
|---|---|---|
| 13 | Elena Rodriguez | Senior QA Engineer — process improvement and automation focus |
| 14 | James Park | Senior Full-Stack Developer — banking/fintech domain |
| 15 | Priya Sharma | Technical Lead / Solution Architect — cloud and delivery leadership |

## 📄 Document Types per Persona

| Upload type | File suffix | Content |
|---|---|---|
| `client_feedback` | `_ClientFeedback.docx` | Client satisfaction form with ratings, attributed quotes, section headings |
| `project_feedback` | `_ProjectFeedback.docx` | Internal project review from team/manager |
| `pdp` | `_PDP.docx` | Personal Development Plan with goals, planned learning, certifications |

## 🚀 Quick Upload

Upload all 9 files for a persona in one go (PowerShell):

```powershell
$base = "http://localhost:8000/api/uploads/doc"
$year = 2025

# Elena Rodriguez
@("client_feedback","project_feedback","pdp") | ForEach-Object {
    $type = $_
    $suffix = @{client_feedback="ClientFeedback";project_feedback="ProjectFeedback";pdp="PDP"}[$type]
    $file = "13_Elena_Rodriguez_2025_$suffix.docx"
    curl -X POST $base -F "file=@$file" -F "upload_type=$type" -F "person_name=Elena Rodriguez" -F "review_year=$year"
}
```

Or upload individually via the Swagger UI at **http://localhost:8000/docs**.

## 🔄 Regenerating the Files

To regenerate the `.docx` files from the generator script:

```powershell
cd c:\workspace\pr-profile
.venv\Scripts\python.exe generate_test_dataset_comprehensive.py
```

The script writes all 9 files into this directory.


## 📂 Directory Structure

```
test_docs_comprehensive/
├── 01_Alex_Chen_2023_Junior.docx              [3-year progression example]
├── 01_Alex_Chen_2024_MidLevel.docx
├── 01_Alex_Chen_2025_Senior.docx
├── 02_Jordan_Mills_2024_Regression.docx       [Performance crisis & recovery]
├── 02_Jordan_Mills_2025_Recovery.docx
├── 03_Taylor_Singh_2024_MixedPerformance.docx [Technical strong, leadership weak]
├── 03_Taylor_Singh_2025_MixedPerformance.docx
├── 04_Casey_Johnson_2024_Stagnation.docx      [Career plateau]
├── 04_Casey_Johnson_2025_Stagnation.docx
├── 05_Morgan_Lee_2024_RapidGrowth.docx        [Accelerated progression]
├── 05_Morgan_Lee_2025_RapidGrowth.docx
├── 06_Sam_Patel_2024_LateralMove.docx         [Cross-team transition]
├── 06_Sam_Patel_2025_LateralMove.docx
├── 07_Alex_Kumar_2024_Specialization.docx     [Technical depth specialist]
├── 07_Alex_Kumar_2025_Specialization.docx
├── 08_Sarah_Martinez_2024_BurnoutWarning.docx [Early intervention scenario]
├── 08_Sarah_Martinez_2025_BurnoutWarning.docx
├── 09_Michael_Chen_2024_Plateau.docx          [High performer plateau]
├── 09_Michael_Chen_2025_Plateau.docx
├── 10_Rachel_Foster_2024_TrackChange.docx     [Tech to management transition]
├── 10_Rachel_Foster_2025_TrackChange.docx
├── 11_David_Thompson_2024_Return.docx         [Post-leave ramp-up]
├── 11_David_Thompson_2025_Return.docx
├── 12_Jennifer_Wu_2024_Crisis.docx            [Crisis management]
├── 12_Jennifer_Wu_2025_Crisis.docx
├── README.md                                   [This file]
├── DATASET_STRUCTURE.md                        [Document mapping and organization]
├── SECTION_TYPES_GUIDE.md                      [Complete section type reference]
├── SECTION_TYPES_QUICK_REFERENCE.md            [Visual quick reference]
└── generate_test_dataset_comprehensive.py      [Generator script]
```

## 🎯 Scenario Types (12 Distinct Career Patterns)

### 1. **Clear Progression** - Alex Chen (3 years)
- **Pattern**: Junior → Mid-Level → Senior
- **Documents**: 3 years (2023-2025)
- **Tests**: Year-over-year growth, skill development, promotion trajectory
- **LLM Focus**: Can it detect consistent upward trajectory?

### 2. **Regression & Recovery** - Jordan Mills (2 years)
- **Pattern**: Decline (2024) → Recovery (2025)
- **Documents**: 2 years showing crisis and comeback
- **Tests**: Issue detection, intervention effectiveness, resilience
- **LLM Focus**: Can it identify personal circumstances impact and recovery?

### 3. **Mixed Performance** - Taylor Singh (2 years)
- **Pattern**: Technically exceptional + leadership weak
- **Documents**: Shows strong architecture work but team friction
- **Tests**: Multi-dimensional performance assessment
- **LLM Focus**: Can it distinguish technical vs. people skills?

### 4. **Stagnation** - Casey Johnson (2 years)
- **Pattern**: Adequate but no growth for 4+ years
- **Documents**: Plateau without progression or regression
- **Tests**: Detecting lack of development
- **LLM Focus**: Can it identify stagnation vs. steady contributor?

### 5. **Rapid Growth** - Morgan Lee (2 years)
- **Pattern**: Entry-level → Lead architect (accelerated)
- **Documents**: Shows quick skill acquisition
- **Tests**: Identifying high-potential candidates
- **LLM Focus**: Can it recognize acceleration vs. normal progression?

### 6. **Lateral Move** - Sam Patel (2 years)
- **Pattern**: Backend transfer to frontend with learning curve
- **Documents**: Shows transition period and successful adaptation
- **Tests**: Cross-functional skill transfer
- **LLM Focus**: Can it detect lateral moves vs. promotions/demotions?

### 7. **Specialization** - Dr. Alex Kumar (2 years)
- **Pattern**: Deep technical expertise development
- **Documents**: Specialist track vs. management ladder
- **Tests**: Recognizing multiple career paths
- **LLM Focus**: Can it distinguish specialist growth from leadership growth?

### 8. **Burnout Warning** - Sarah Martinez (2 years)
- **Pattern**: Early warning signs → intervention → recovery
- **Documents**: Shows burnout indicators and recovery trajectory
- **Tests**: Work-life balance and wellness signals
- **LLM Focus**: Can it recognize burnout indicators before crisis?

### 9. **High Performer Plateau** - Michael Chen (2 years)
- **Pattern**: Excellent performer with no advancement interest
- **Documents**: Strong technical work but no growth trajectory
- **Tests**: Distinguishing plateau from stagnation
- **LLM Focus**: Can it differentiate satisfied high performer from stuck employee?

### 10. **Track Change** - Rachel Foster (2 years)
- **Pattern**: Individual contributor → management track transition
- **Documents**: Shows shift in responsibilities and skill focus
- **Tests**: Identifying leadership readiness
- **LLM Focus**: Can it recognize IC-to-manager transitions?

### 11. **Return from Leave** - David Thompson (2 years)
- **Pattern**: Parental leave → ramp-up → full recovery
- **Documents**: Shows impact of absence and reintegration
- **Tests**: Work-life balance initiatives
- **LLM Focus**: Can it assess return-to-work impact?

### 12. **Crisis Management** - Jennifer Wu (2 years)
- **Pattern**: Major issue → leadership response → promotion
- **Documents**: Shows crisis handling capability and growth
- **Tests**: Problem-solving and responsibility management
- **LLM Focus**: Can it recognize crisis leadership competencies?

## 🏷️ Section Type Indicators

Every document includes **section type tags** that mark content categories for precise LLM parsing:

### Document Types
- `[PROGRESSION]` - Career growth scenario
- `[REGRESSION]` - Performance decline scenario  
- `[RECOVERY]` - Improvement from decline
- `[MIXED PERFORMANCE]` - Conflicting metrics
- `[STAGNATION]` - Career plateau
- `[RAPID GROWTH]` - Accelerated progression
- `[LATERAL MOVE]` - Cross-team transfer
- `[SPECIALIZATION]` - Technical depth focus
- `[BURNOUT]` - Employee wellness concern
- `[PLATEAU]` - High performer plateau
- `[TRACK CHANGE]` - Career path shift
- `[RETURN]` - Post-leave ramp-up
- `[CRISIS]` - Major issue handling

### Content Section Types
**Feedback Sections**:
- `[MANAGER FEEDBACK]` - Direct manager assessment
- `[CLIENT FEEDBACK]` - Stakeholder perspective
- `[TEAM FEEDBACK]` - Peer assessment
- `[SENIOR ENGINEER FEEDBACK]` - Lead engineer evaluation
- `[CTO FEEDBACK]` - Executive feedback

**Performance Sections**:
- `[SUMMARY]` - Overview of period
- `[PERFORMANCE METRICS]` - Quantitative data
- `[KEY ACHIEVEMENTS]` - Accomplishments
- `[CONCERNS]` - Issues or problems
- `[TECHNICAL ACHIEVEMENTS]` - Technical-specific wins

**Development Sections**:
- `[SKILLS & CERTIFICATION]` - Current expertise
- `[PDP - PROFESSIONAL DEVELOPMENT]` - Training completed
- `[TRAINING COMPLETED]` - Specific certifications
- `[DEVELOPMENT AREAS]` - Growth opportunities
- `[GOALS]` - Next period objectives

**Career Sections**:
- `[PROMOTION]` - Role advancement
- `[SELF-ASSESSMENT]` - Employee perspective
- `[RECOMMENDATIONS]` - Next steps
- `[PERSONAL CONTEXT]` - Life circumstances
- `[MENTORING]` - Mentoring activities

## 📊 LLM Testing Scenarios

### Test 1: Pattern Recognition
**Question**: Can the LLM identify scenario type from document content?
```
Input: 04_Casey_Johnson_2024_Stagnation.docx
Expected Output: [STAGNATION] - Employee shows no skill growth over 4 years
```

### Test 2: Year-over-Year Analysis
**Question**: Can the LLM track changes across years?
```
Input: 01_Alex_Chen_2024_MidLevel.docx + 01_Alex_Chen_2025_Senior.docx
Expected Output: Clear progression from mid to senior level, achievement progression
```

### Test 3: Multi-Source Analysis
**Question**: Can the LLM compare different feedback sources?
```
Input: 03_Taylor_Singh_2024_MixedPerformance.docx
Extract: [MANAGER FEEDBACK] vs [TEAM FEEDBACK]
Expected: Recognition that technical work is strong but people skills are weak
```

### Test 4: Indicator Detection
**Question**: Can the LLM detect warning signs?
```
Input: 08_Sarah_Martinez_2024_BurnoutWarning.docx
Extract: [BURNOUT INDICATORS] + [PERSONAL CONTEXT]
Expected: Recognition of burnout signals requiring intervention
```

### Test 5: Career Path Assessment
**Question**: Can the LLM assess multiple career paths?
```
Input: 07_Alex_Kumar_2024_Specialization.docx
Analysis: Compare specialist track vs management track progression
Expected: Recognition of technical specialization path
```

## 🚀 Using This Dataset

### For Manual Review:
1. Open any `.docx` file in Microsoft Word
2. Look for `[TYPE]` tags indicating content categories
3. Documents are organized chronologically (2023→2025)
4. Compare year-over-year for progression patterns

### For LLM Analysis:
1. Upload documents to your LLM analysis system
2. Use section type tags for precise content extraction
3. Create prompts targeting specific `[SECTION_TYPE]` content
4. Compare results across similar scenario types
5. Validate pattern recognition accuracy

### For Testing:
1. Start with simple pattern recognition (scenario detection)
2. Move to multi-year analysis (01_Alex_Chen_2023/2024/2025)
3. Test comparative analysis (10_Rachel_Foster feedback sources)
4. Validate complex scenarios (12_Jennifer_Wu crisis handling)

## 📝 Document Format

Each document follows this structure:

```
[SCENARIO_TYPE] Human-Readable Title
Employee Name
Year Range

[SUMMARY]
Overview section

[MANAGER FEEDBACK]
Direct manager's assessment

[CLIENT/STAKEHOLDER FEEDBACK]
External perspectives

[PERFORMANCE METRICS]
Quantitative data and scores

[KEY ACHIEVEMENTS]
Accomplishments

[SKILLS & CERTIFICATION]
Current expertise level

[PDP - PROFESSIONAL DEVELOPMENT]
Training and development completed

[GOALS]
Objectives for next period

[SELF-ASSESSMENT]
Employee's perspective
```

## 🔍 Content Validation

All documents have been:
- ✅ Generated with realistic career patterns
- ✅ Tagged with document type indicators (document-level)
- ✅ Tagged with section type indicators (content-level)
- ✅ Organized for chronological analysis
- ✅ Cross-referenced with supporting documentation

## 📚 Related Documentation

- **SECTION_TYPES_GUIDE.md** - Complete reference for all 30+ section types
- **SECTION_TYPES_QUICK_REFERENCE.md** - Visual quick reference card
- **DATASET_STRUCTURE.md** - Detailed document mapping

## 💡 Tips for LLM Testing

1. **Start Simple**: Begin with Clear Progression (Alex Chen) to validate basic pattern recognition
2. **Use Section Types**: Reference `[SECTION_TYPE]` tags when creating prompts
3. **Compare Scenarios**: Use similar scenarios (e.g., all Stagnation examples) to test consistency
4. **Track Year-over-Year**: Use 2024→2025 transitions to validate temporal analysis
5. **Test Edge Cases**: Use Mixed Performance or Crisis scenarios for complex analysis

---

**Total Documents**: 24 (12 employees × 2+ years each)  
**Scenarios**: 12 distinct career patterns  
**Years Covered**: 2023-2025  
**Format**: Microsoft Word (.docx)  
**Generated**: Automatically via `generate_test_dataset_comprehensive.py`
