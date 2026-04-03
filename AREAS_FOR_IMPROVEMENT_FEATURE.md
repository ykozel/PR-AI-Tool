# New Feature: "What Went Wrong and Needs to be Improved" Section

## Overview

The year-over-year analysis now includes a dedicated section that identifies areas of concern, regression, and improvement needs compared to the previous year. This provides a balanced view of employee performance by highlighting both achievements and areas that need attention.

## What's New

### 1. Extended YOY Analysis Fields

The `YearOverYearAnalyzer` now extracts and analyzes:

- **areas_of_concern**: Issues, skill decline, or performance regression
- **improvement_priorities**: High-priority improvement areas for next review
- **unmet_goals**: Goals from previous year that weren't achieved
- **feedback_gaps**: Discrepancies between feedback and actual performance
- **overall_concerns**: Summary of main concern areas (or null if performance improving)

### 2. New HTML Section

**Title**: "What went wrong and needs to be improved"
**Location**: Displays immediately after "Achievements over a year" section
**ID**: `#areas-for-improvement-yoy`
**Styling**: Orange/amber color scheme (contrasts with achievement section's green)

### 3. Section Structure

```html
<h2>What went wrong and needs to be improved</h2>

[Summary blockquote with overall concerns]

<h3>Areas of Concern</h3>
- List of regression or concern areas

<h3>Unmet Goals from Previous Year</h3>
- Goals and commitments not fulfilled

<h3>Feedback Gaps and Discrepancies</h3>
- Notable differences between feedback and performance

<h3>Priority Areas for Next Review Period</h3>
- Specific improvement actions needed
```

### 4. Table of Contents

The section is automatically added to TOC only if concerns exist:
```
What went wrong and needs to be improved
```

## LLM Analysis Logic

The updated prompt instructs the LLM to:

**PART 1** (existing): Identify achievements, skills, and growth
**PART 2** (new): Identify concerns, regression, and improvement areas

The LLM looks for:
- Skills that declined or weren't maintained
- Missed deadlines or unfulfilled commitments
- Reduced productivity or contributions
- Quality issues or technical debt
- Communication or collaboration problems
- Missed training/certification goals
- Misalignment between feedback and performance

## HTML Output Example

```html
<h2 id="areas-for-improvement-yoy">What went wrong and needs to be improved</h2>

<blockquote>
  <p>
    While technical contributions were strong, project delivery challenges and 
    collaboration gaps emerged. Performance reliability and team engagement 
    require focused improvement.
  </p>
</blockquote>

<h3>Areas of Concern</h3>
<ul>
  <li>Code review turnaround time increased 40% (delays in development cycle)</li>
  <li>Test coverage declined from 85% to 72%</li>
  <li>Participated in only 2 of 6 scheduled team meetings</li>
  <li>Documentation quality reduced significantly</li>
</ul>

<h3>Unmet Goals from Previous Year</h3>
<ul>
  <li>Kubernetes certification not completed (planned for Q3)</li>
  <li>Mentoring program participation dropped</li>
  <li>Architecture documentation incomplete</li>
</ul>

<h3>Feedback Gaps and Discrepancies</h3>
<ul>
  <li>Self-rated collaboration as 'Excellent', but peer feedback indicates 'Needs Improvement'</li>
  <li>Reported high code quality focus but quality metrics declined</li>
</ul>

<h3>Priority Areas for Next Review Period</h3>
<ul>
  <li>Implement systematic code review practices to improve quality</li>
  <li>Focus on test automation and coverage improvement</li>
  <li>Commit to mentoring and knowledge sharing activities</li>
</ul>
```

## Styling

The section uses a warning/concern color scheme:

- **Primary Color**: #fd7e14 (orange)
- **Background**: Light background (#fffbf5)
- **Text Color**: Dark brown (#6b4423)
- **Blockquote**: Orange-themed for emphasis

This visually distinguishes it from the green "Achievements over a year" section.

## CSS Classes

```css
#areas-for-improvement-yoy { /* Main section styling */ }
#areas-for-improvement-yoy blockquote { /* Summary blockquote */ }
#areas-for-improvement-yoy h3 { /* Subsection headings */ }
#areas-for-improvement-yoy ul { /* Lists */ }
#areas-for-improvement-yoy li { /* List items */ }
```

## Conditional Display

The section only appears if the YOY analysis includes any of:
- `areas_of_concern` (non-empty list)
- `improvement_priorities` (non-empty list)
- `unmet_goals` (non-empty list)
- `overall_concerns` (non-null)

If none of these are populated, the section is omitted entirely, maintaining cleaner HTML for employees with purely positive performance reviews.

## Integration Points

### Upload Endpoint
- YOY analysis automatically triggered
- All fields (including concerns) captured
- Section rendered in final HTML

### Regenerate Endpoint
- Re-runs full YOY analysis including concerns
- Updates cached analysis
- Regenerates HTML with updated concerns

### API Response
- Upload response indicates if YOY analysis was generated

## Data Flow

```
Upload 2027 Documents
        ↓
Extract Previous Year Data (2025)
        ↓
YearOverYearAnalyzer.analyze_year_comparison()
        ↓
LLM Comparison:
  - Part 1: New achievements ✓
  - Part 2: What went wrong ✓
        ↓
Structured JSON:
  - new_achievements, new_skills, etc.
  - areas_of_concern, improvement_priorities, etc.
        ↓
Store in profile.yoy_analysis
        ↓
ReportGenerator.generate_html()
        ↓
HTML Sections:
  - Achievements over a year (green)
  - What went wrong and needs improvement (orange)
```

## Use Cases

### Performance Improvement Conversations
Use the "What went wrong" section to guide:
- Targeted coaching sessions
- PIP (Performance Improvement Plan) discussions
- Goal setting for next review period
- Skill development planning

### Balanced Feedback
Provides context for:
- Both positive and constructive feedback
- Acknowledgment of achievements alongside areas to work on
- Data-driven performance discussions

### Career Development
Identifies:
- Skill gaps that need filling
- Reliability or consistency issues
- Team collaboration opportunities
- Professional growth areas

## Configuration

No additional configuration needed. The feature uses:
- Existing `OPENAI_API_KEY` for LLM calls
- Existing `AI_MODEL` setting
- Standard error handling and graceful degradation

## Error Handling

- If LLM call fails: Section omitted, report still generates
- If JSON parsing fails: Section omitted, no errors thrown
- If previous year unavailable: Analysis not run (no concerns to report)
- Graceful degradation ensures reports always generate successfully

## Testing

Run the comprehensive test:
```bash
python test_areas_improvement_section.py
```

This verifies:
✓ All concern fields are rendered
✓ Section title appears in TOC
✓ Subsection headings present
✓ Content properly escaped
✓ Styling applied correctly
✓ Optional sections conditionally displayed

## Format Example

**Input Analysis from LLM**:
```json
{
  "areas_of_concern": [
    "Code review turnaround increased 40%",
    "Test coverage declined from 85% to 72%"
  ],
  "improvement_priorities": [
    "Implement code review best practices",
    "Focus on test automation"
  ],
  "overall_concerns": "Performance reliability needs improvement"
}
```

**Output in HTML**:
```html
<h3>Areas of Concern</h3>
<ul>
  <li>Code review turnaround increased 40%</li>
  <li>Test coverage declined from 85% to 72%</li>
</ul>

<h3>Priority Areas for Next Review Period</h3>
<ul>
  <li>Implement code review best practices</li>
  <li>Focus on test automation</li>
</ul>
```

## Summary

This feature provides:

✅ **Balanced Assessment**: Shows both achievements and areas for improvement
✅ **LLM-Powered Analysis**: Intelligent identification of concerns and regressions
✅ **Structured Data**: JSON fields for programmatic access
✅ **Visual Distinction**: Clear styling separates concerns from achievements
✅ **Conditional Display**: Section only appears when concerns exist
✅ **Non-Blocking**: Failure to generate doesn't prevent report generation
✅ **User-Friendly**: Clear section hierarchy and descriptive headings

The section empowers HR professionals and managers to:
- Have evidence-based performance conversations
- Identify specific improvement areas
- Track progress on commitments year-over-year
- Support employee development more effectively
