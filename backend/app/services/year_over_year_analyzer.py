"""Year-over-year achievement analysis service.

Compares achievements, skills, and performance between two consecutive years
and identifies new accomplishments and skill development.
"""

import json
import logging
from typing import Optional, Dict, Any, List

from app.core.config import settings

logger = logging.getLogger(__name__)


YOY_ANALYSIS_PROMPT = """You are an HR analyst comparing employee performance between two consecutive years.

Employee: {employee_name}
Previous Year: {previous_year}
Current Year: {current_year}

PREVIOUS YEAR DATA:
{previous_year_data}

---

CURRENT YEAR DATA:
{current_year_data}

---

PART 1 - Positive Growth:
Compare these two years and identify:
1. New achievements not mentioned in previous year
2. New skills or competencies gained
3. Areas of growth and development
4. Promotions or role changes
5. New responsibilities or projects

PART 2 - Areas for Improvement:
Identify:
1. Areas of concern or regression compared to previous year
2. Skills that have declined or not been maintained
3. Missed opportunities or unfulfilled goals from previous year
4. Gaps between feedback expectations and current performance
5. Issues, challenges, or problems that need to be addressed

Return ONLY a valid JSON object with this exact structure:
{{
  "new_achievements": [
    "Achievement or accomplishment that is NEW in the current year",
    "Examples: new project lead, expanded scope, team growth, etc."
  ],
  "new_skills": [
    "Skill or capability acquired or significantly improved in current year",
    "Examples: AWS certification, advanced SQL, leadership skills, etc."
  ],
  "skill_progression": [
    {{"skill": "skill name", "from": "previous level", "to": "current level", "evidence": "brief evidence"}}
  ],
  "growth_areas": [
    "Area where employee has made notable progress year-over-year"
  ],
  "promotion_or_change": "Description of any role/title change, promotion, or significant responsibility shift, or null if no change",
  "areas_of_concern": [
    "Area, skill, or metric that has declined or regressed compared to previous year",
    "Examples: reduced code quality, missed deadlines, skill atrophy, reduced contributions, etc."
  ],
  "improvement_priorities": [
    "High-priority area for improvement in the next review period",
    "Examples: communication skills training, deadline management, specific technical upskilling, etc."
  ],
  "unmet_goals": [
    "Goals or commitments from previous year that were not achieved or abandoned"
  ],
  "feedback_gaps": [
    "Notable discrepancies between feedback and actual performance or behavior"
  ],
  "overall_concerns": "2-3 sentence summary of main areas of concern or regression, or null if performance stable/improving",
  "summary": "2-3 sentence summary of the employee's growth trajectory from previous to current year",
  "overall_assessment": "Brief assessment: 'Strong Growth', 'Solid Progress', 'Exceptional Development', 'Needs Improvement', 'Performance Concerns', etc."
}}"""


class YearOverYearAnalyzer:
    """Analyzes achievements across consecutive years for the same employee."""

    @staticmethod
    def analyze_year_comparison(
        employee_name: str,
        previous_year: int,
        current_year: int,
        previous_year_text: str,
        current_year_text: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze year-over-year achievements and growth.

        Args:
            employee_name: Employee name
            previous_year: Previous review year
            current_year: Current review year
            previous_year_text: Combined text from previous year documents
            current_year_text: Combined text from current year documents

        Returns:
            Dictionary with structured analysis or None if analysis fails
        """
        if not settings.openai_api_key:
            logger.warning("OpenAI API key not configured; skipping year-over-year analysis")
            return None

        if not previous_year_text or not current_year_text:
            logger.warning("Missing text data for year comparison")
            return None

        try:
            from openai import OpenAI  # type: ignore[import]
        except ImportError:
            logger.warning("openai package not installed")
            return None

        # Truncate texts if needed to stay within token limits
        max_chars = 6000  # Conservative limit per year
        prev_text = previous_year_text[:max_chars] if len(previous_year_text) > max_chars else previous_year_text
        curr_text = current_year_text[:max_chars] if len(current_year_text) > max_chars else current_year_text

        prompt = YOY_ANALYSIS_PROMPT.format(
            employee_name=employee_name,
            previous_year=previous_year,
            current_year=current_year,
            previous_year_data=prev_text,
            current_year_data=curr_text,
        )

        try:
            client = OpenAI(api_key=settings.openai_api_key)
            response = client.chat.completions.create(
                model=settings.ai_model,
                messages=[
                    {"role": "system", "content": "You are an HR analytics expert."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=1500,
            )
            
            response_text = response.choices[0].message.content
            
            # Parse JSON response
            data = json.loads(response_text)
            
            logger.info(
                f"Year-over-year analysis completed for {employee_name} ({previous_year}→{current_year}): "
                f"{len(data.get('new_achievements', []))} new achievements, "
                f"{len(data.get('new_skills', []))} new skills"
            )
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse year-over-year analysis JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Year-over-year analysis failed: {e}", exc_info=True)
            return None
