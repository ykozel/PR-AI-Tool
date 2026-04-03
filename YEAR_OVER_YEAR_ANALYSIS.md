# Year-over-Year Achievement Analysis Feature

## Overview

This feature enables intelligent, LLM-powered analysis of employee achievements across multiple years. When a new year's documents are uploaded to the system, it automatically:

1. Identifies the previous year's profile
2. Extracts combined text from all documents in both years
3. Uses OpenAI API to compare achievements and identify growth
4. Stores the analysis in the database
5. Includes the analysis in the final HTML report under "Achievements over a year" section

## Implementation Components

### 1. YearOverYearAnalyzer Service

**File**: `app/services/year_over_year_analyzer.py`

**Key Method**: `analyze_year_comparison()` (static)

```python
YearOverYearAnalyzer.analyze_year_comparison(
    employee_name="Emma Laurent",
    previous_year=2025,
    current_year=2027,
    previous_year_text="...",  # Combined text from all 2025 documents
    current_year_text="..."    # Combined text from all 2027 documents
)
```

**Returns**: Dictionary with the following keys:
- `new_achievements`: List of new accomplishments not mentioned in previous year
- `new_skills`: List of new skills or competencies acquired
- `skill_progression`: List of skills with progression from/to levels
- `growth_areas`: Areas where employee made notable progress
- `promotion_or_change`: Description of role changes or promotions
- `summary`: 2-3 sentence summary of growth trajectory
- `overall_assessment`: Assessment level (e.g., "Exceptional Development")

**Error Handling**: Returns `None` if:
- OpenAI API key is not configured
- Text data is insufficient
- LLM call fails
- JSON parsing fails

### 2. Database Schema

**File**: `app/models/pr_profile.py`

Added column to `PRProfile` model:
```python
yoy_analysis = Column(Text, nullable=True)  # Stores JSON analysis
```

### 3. Repository Layer

**File**: `app/core/repositories.py`

New methods on `PRProfileRepository`:

```python
def get_previous_profile(profile: PRProfile) -> Optional[PRProfile]:
    """Get the previous year profile linked via previous_year_profile_id"""

def update_yoy_analysis(profile: PRProfile, yoy_analysis_json: str) -> PRProfile:
    """Store year-over-year analysis JSON"""
```

### 4. Report Generation

**File**: `app/services/report_generator.py`

**Modifications**:
- `generate_html()` now accepts optional `yoy_analysis` parameter
- `_toc_html()` adds "Achievements over a year" link when analysis present
- `_body_html()` renders YOY section at the end
- New method `_yoy_analysis_html()` renders analysis into HTML with:
  - Summary blockquote
  - Role changes section (h3)
  - New achievements list (h3 + bullet list)
  - New skills list (h3 + bullet list)
  - Skill progression (h3 + "Skill: from → to" format)
  - Growth areas (h3 + bullet list)
  - Overall assessment (h3)

**CSS Styling**:
- YOY section uses green color scheme (#28a745)
- Distinct styling from other sections
- Optimized blockquote styling for summaries

### 5. API Integration

**Upload Endpoint**: `POST /api/uploads/doc`

**Flow**:
1. File is uploaded and text extracted
2. Profile is created/updated
3. HTML generation begins
4. **NEW**: System checks for previous year profile
5. **NEW**: If previous year exists:
   - Fetches all files from previous year
   - Combines texts from both years
   - Calls `YearOverYearAnalyzer.analyze_year_comparison()`
   - Stores result in profile via `update_yoy_analysis()`
   - Passes analysis to `generate_html()`
6. HTML report generated with YOY section

**Regenerate Endpoint**: `POST /api/profiles/html/{person_name}/{year}/regenerate`

**Similar flow with YOY analysis regeneration**

## Usage Example

### Scenario: Emma Laurent - 2025 to 2027 Comparison

1. **Upload 2025 documents** (if not already done):
   - Emma_Laurent_Client_Feedback_2025.docx
   - Emma_Laurent_PDP_2025_2026.docx

2. **Upload 2027 documents**:
   ```bash
   POST /api/uploads/doc
   - file: Emma_Laurent_Client_Feedback_2027.docx
   - upload_type: client_feedback
   - person_name: Emma Laurent
   - review_year: 2027
   ```

3. **System automatically**:
   - Links 2027 to 2025 (most recent previous year)
   - Analyzes achievements growth
   - Generates HTML with "Achievements over a year" section

4. **View profile**:
   ```bash
   GET /api/profiles/html/Emma Laurent/2027
   ```
   → HTML includes year navigation + YOY analysis section

## HTML Report Structure

The "Achievements over a year" section appears after Activity section with:

```
## Achievements over a year

> [Summary blockquote]

### Role Changes
[Promotion or significant responsibility shift]

### New Achievements
- Achievement 1
- Achievement 2
- ...

### New Skills Gained
- Skill 1
- Skill 2
- ...

### Skill Progression
- Python: Intermediate → Advanced
- AWS: None → Proficient
- ...

### Growth Areas for Next Year
- Area 1
- Area 2

### Overall Assessment
[Assessment text]
```

## Testing

### Prerequisites
- OpenAI API key configured in environment (optional but required for full testing)
- Test documents in `test_docs/` directory:
  - Emma_Laurent_Client_Feedback_2025.docx
  - Emma_Laurent_PDP_2025_2026.docx
  - Emma_Laurent_Client_Feedback_2027.docx
  - Emma_Laurent_PDP_2027_2028.docx

### Run Tests

**Comprehensive test suite**:
```bash
python test_yoy_comprehensive.py
```

Tests:
- ✓ Repository layer (get_previous_profile, update_yoy_analysis)
- ✓ YOY analyzer service
- ✓ Report generator HTML generation
- ✓ YOY content in HTML

**Integration test with actual documents**:
```bash
python test_yoy_integration.py
```

## Configuration

### OpenAI API Integration

**File**: `app/core/config.py`

The feature uses existing configuration:
- `OPENAI_API_KEY`: Required for analysis
- `AI_MODEL`: Model to use (default: "gpt-3.5-turbo")

**Graceful Degradation**: If OpenAI API is not available:
- System logs warning
- Report still generates without YOY section
- No errors thrown

### Environment Setup

```bash
export OPENAI_API_KEY="sk-..."
export AI_MODEL="gpt-3.5-turbo"  # or gpt-4, etc.
```

## Performance Considerations

- **Text Truncation**: Each year's text truncated to 6,000 characters to manage token usage
- **Non-Blocking**: YOY analysis failure doesn't prevent report generation
- **Caching**: Analysis stored in profile to avoid re-running during regenerate
- **Latency**: LLM call adds ~2-5 seconds to upload time

## Error Handling

All errors are non-blocking:

| Error | Behavior |
|-------|----------|
| No OpenAI key | Logs warning, skips YOY analysis |
| No previous year | Skips YOY analysis (first year) |
| No previous files | Skips YOY analysis |
| LLM call fails | Logs error, includes YOY status in message |
| JSON parse fails | Logs error, skips YOY section |

## Future Enhancements

1. **Multi-Year Trends**: Compare 3+ years at once
2. **Interactive Frontend**: React component to display YOY analysis
3. **Custom Prompts**: Allow custom analysis prompts
4. **Caching**: Skip re-analysis if documents unchanged
5. **Comparision APIs**: Endpoint to retrieve YOY analysis as JSON
6. **Advanced Metrics**: Quantify skill progression levels
7. **Role Tracking**: Track job level/title changes across years
8. **Batch Analysis**: Analyze multiple employees at once

## Architecture Diagram

```
Upload 2027 Document
        ↓
   [Profile Created/Updated]
        ↓
    [Find Previous Year] ← Uses `get_most_recent_previous_year()`
        ↓
    [Yes] → [Extract Previous Year Files]
    [No]  → [Skip YOY Analysis]
        ↓
    [Combined Text from Both Years]
        ↓
    [YearOverYearAnalyzer.analyze_year_comparison()]
        ↓
    [LLM Comparison]
        ↓
    [JSON Results: new_achievements, new_skills, etc.]
        ↓
    [Store in profile.yoy_analysis]
        ↓
    [ReportGenerator.generate_html(yoy_analysis=...)]
        ↓
    [HTML with "Achievements over a year" section]
        ↓
    [Store HTML in profile]
        ↓
    [Return to Client]
```

## Code Files Changed

**New Files**:
- `app/services/year_over_year_analyzer.py` (120 lines)
- `test_yoy_comprehensive.py` (250+ lines)
- `test_yoy_integration.py` (200+ lines)

**Modified Files**:
- `app/models/pr_profile.py`: Added `yoy_analysis` column
- `app/core/repositories.py`: Added 2 new methods
- `app/services/report_generator.py`: Updated signatures, added YOY rendering, added CSS
- `app/api/uploads.py`: Added YOY analysis trigger
- `app/api/profiles.py`: Added YOY analysis to regenerate endpoint

## Support & Troubleshooting

**Q: Why is YOY analysis not appearing?**
- A: Check if previous year exists and has files with extracted text
- Check OPENAI_API_KEY is set
- Review server logs for errors

**Q: Can I use without OpenAI?**
- A: Yes, reports generate without YOY section if API not available

**Q: How long does analysis take?**
- A: ~2-5 seconds for LLM call, depends on OpenAI load

**Q: Is analysis re-run on regenerate?**
- A: No, stored analysis reused unless profile updated

**Q: Can I compare non-consecutive years?**
- A: Yes, system finds most recent previous year
