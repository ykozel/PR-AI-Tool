"""Document processing service for extracting and parsing .doc/.docx content into structured sections"""
import re
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ExtractedSection:
    """Dataclass for a parsed section"""
    section_name: str
    content: str
    raw_text: str
    confidence: float = 0.8


@dataclass
class DocumentAnalysis:
    """Complete analysis of an extracted document"""
    sections: List[ExtractedSection]
    full_text: str
    feedback_type: str
    parsing_quality: float


class SectionExtractor:
    """Extracts and parses all sections from document text regardless of their names"""

    def __init__(self):
        self.bullet_pattern = re.compile(
            r'[\s]*[-•*▪]\s+(.+?)(?=\n[-•*▪]|\Z)',
            re.MULTILINE | re.DOTALL
        )

    def extract_sections(self, text: str) -> List[ExtractedSection]:
        """
        Extract all sections from document text.

        Tries numbered sections first (any number), then falls back to
        heading-based detection for unnumbered documents.

        Args:
            text: Full extracted text from the document

        Returns:
            List of ExtractedSection objects
        """
        numbered = self._extract_numbered_sections(text)
        if numbered:
            return numbered
        return self._extract_by_headings(text)

    def _extract_numbered_sections(self, text: str) -> List[ExtractedSection]:
        """Extract any explicitly numbered sections (e.g. 1. Title, 2. Title ...)."""
        # Matches any positive integer followed by optional separator and a title
        section_pattern = re.compile(
            r'(?:^|\n)\s*(\d+)\s*[\.\:\-]?\s*(.+?)(?=\n\s*\d+\s*[\.\:\-]|\Z)',
            re.DOTALL
        )
        sections = []
        for match in section_pattern.finditer(text):
            title_line = match.group(2).split('\n')[0].strip()
            body = match.group(2).strip()
            if not title_line:
                continue
            sections.append(ExtractedSection(
                section_name=title_line,
                content=self._clean_body(body),
                raw_text=body,
                confidence=0.95,
            ))
        return sections

    def _extract_by_headings(self, text: str) -> List[ExtractedSection]:
        """
        Fallback: detect sections by heading-like lines.

        A heading is a short line (≤ 80 chars) that is either ALL-CAPS or
        Title-Cased and is followed by non-empty content.
        """
        # Split into lines and group into candidate heading + body blocks
        lines = text.splitlines()
        sections: List[ExtractedSection] = []
        current_heading: Optional[str] = None
        body_lines: List[str] = []

        heading_re = re.compile(
            r'^[A-Z][A-Za-z0-9 \-/&]{2,79}$'
        )

        def flush(heading: str, body: List[str]) -> None:
            body_text = '\n'.join(body).strip()
            if body_text:
                sections.append(ExtractedSection(
                    section_name=heading,
                    content=body_text,
                    raw_text=body_text,
                    confidence=0.7,
                ))

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if current_heading:
                    body_lines.append('')
                continue
            if heading_re.match(stripped) and len(stripped) <= 80:
                if current_heading:
                    flush(current_heading, body_lines)
                current_heading = stripped
                body_lines = []
            else:
                if current_heading:
                    body_lines.append(stripped)

        if current_heading:
            flush(current_heading, body_lines)

        return sections

    def _clean_body(self, content: str) -> str:
        """Strip the leading numbered header line from body text."""
        lines = content.split('\n')
        result = []
        skip = True
        for line in lines:
            if skip and re.match(r'^\s*\d+\s*[\.\:\-]', line):
                skip = False
                continue
            result.append(line.strip())
        return '\n'.join(result).strip()

    def extract_bullet_points(self, text: str) -> List[str]:
        """Extract bullet points from section content."""
        bullets = [m.group(1).strip() for m in self.bullet_pattern.finditer(text)]
        return bullets if bullets else [text]


class DocumentProcessor:
    """Main document processor - orchestrates extraction and analysis"""

    def __init__(self):
        self.section_extractor = SectionExtractor()

    def process_document(self, text: str, feedback_type: str = 'unknown') -> DocumentAnalysis:
        """
        Process extracted document text into structured sections.

        Args:
            text: Full extracted text from the .doc/.docx file
            feedback_type: Source document type (e.g. 'auto', 'project', 'function')

        Returns:
            DocumentAnalysis with all extracted sections
        """
        try:
            sections = self.section_extractor.extract_sections(text)
            parsing_quality = self._calculate_quality(sections, text)
            return DocumentAnalysis(
                sections=sections,
                full_text=text,
                feedback_type=feedback_type,
                parsing_quality=parsing_quality,
            )
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            return DocumentAnalysis(
                sections=[],
                full_text=text,
                feedback_type=feedback_type,
                parsing_quality=0.0,
            )

    def _calculate_quality(self, sections: List[ExtractedSection], text: str) -> float:
        """Calculate how well the parsing worked."""
        if not sections:
            return 0.0
        # Quality scales with sections found; cap at 1.0
        base_quality = min(len(sections) / max(len(sections), 1), 1.0)
        avg_confidence = sum(s.confidence for s in sections) / len(sections)
        return round((base_quality + avg_confidence) / 2, 2)

    def get_section_by_name(self, analysis: DocumentAnalysis, name: str) -> Optional[ExtractedSection]:
        """Find a section by an exact or case-insensitive name match."""
        name_lower = name.lower()
        for section in analysis.sections:
            if section.section_name.lower() == name_lower:
                return section
        return None

    def extract_structured_data(self, analysis: DocumentAnalysis) -> Dict[str, Any]:
        """
        Convert analysis to a structured dictionary for storage.

        All extracted sections are stored under their normalised name as key,
        making the structure fully dynamic regardless of section names.

        Args:
            analysis: DocumentAnalysis object

        Returns:
            Dictionary with all sections plus metadata
        """
        structured: Dict[str, Any] = {
            'quality_score': analysis.parsing_quality,
            'feedback_type': analysis.feedback_type,
            'sections': {},
        }
        for section in analysis.sections:
            key = re.sub(r'\s+', '_', section.section_name.strip().lower())
            structured['sections'][key] = section.content
        return structured
