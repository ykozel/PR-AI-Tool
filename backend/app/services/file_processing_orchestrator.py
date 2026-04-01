"""Unified file processing orchestrator - coordinates upload, processing, and analysis (Single Responsibility + DRY)"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from app.core.constants import (
    FeedbackType,
    UploadStatus,
    FILE_TYPE_TO_FEEDBACK_TYPE,
    ERROR_TEXT_EXTRACTION_FAILED,
    ERROR_DOCUMENT_PROCESSING_FAILED,
    ERROR_AI_ANALYSIS_FAILED,
)
from app.core.repositories import RepositoryFactory
from app.services.doc_processor import DocProcessor
from app.services.document_processor import DocumentProcessor
from app.services.ai_analyzer import AIAnalyzer

logger = logging.getLogger(__name__)


class ProcessingResult:
    """Encapsulates processing results from each stage"""
    
    def __init__(self):
        self.extracted_text: Optional[str] = None
        self.analysis: Optional[Dict[str, Any]] = None
        self.structured_data: Optional[Dict[str, Any]] = None
        self.extracted_sections: Optional[Dict[str, str]] = None
        self.ai_results: Optional[Dict[str, Any]] = None
        self.parsing_quality: float = 0.0
        self.error: Optional[str] = None
        self.failed_phase: Optional[str] = None


class FileProcessingOrchestrator:
    """
    Orchestrates the complete file processing pipeline:
    1. Extract text from .doc/.docx document
    2. Parse document into sections
    3. Run AI analysis (optional)

    Eliminates code duplication across endpoints.
    """

    def __init__(
        self,
        repo_factory: RepositoryFactory,
        doc_processor: Optional[DocProcessor] = None,
        document_processor: Optional[DocumentProcessor] = None,
        ai_analyzer: Optional[AIAnalyzer] = None,
    ):
        """Initialize with dependencies (dependency injection)"""
        self.repo = repo_factory
        self.doc_processor = doc_processor or DocProcessor()
        self.document_processor = document_processor or DocumentProcessor()
        self.ai_analyzer = ai_analyzer or AIAnalyzer()
    
    def extract_and_process(
        self,
        file_id: int,
        file_path: str,
        upload_type: str,
        run_ai_analysis: bool = False,
    ) -> ProcessingResult:
        """
        Execute complete processing pipeline with error handling.

        Args:
            file_id: Database ID of uploaded file
            file_path: Path to .doc/.docx file on disk
            upload_type: Type of upload (e.g. company_function, auto_feedback)
            run_ai_analysis: Whether to run AI analysis phase

        Returns:
            ProcessingResult with all phase results
        """
        result = ProcessingResult()
        uploaded_file_repo = self.repo.get_uploaded_file_repo()
        
        try:
            # Phase 1: Text Extraction
            result.extracted_text = self._extract_text(file_id, file_path)
            if not result.extracted_text:
                result.error = ERROR_TEXT_EXTRACTION_FAILED
                result.failed_phase = "text_extraction"
                self._mark_failed(file_id, result.error)
                return result
            
            # Phase 2: Document Processing
            feedback_type = self._normalize_feedback_type(upload_type)
            (result.analysis, 
             result.structured_data, 
             result.extracted_sections, 
             result.parsing_quality) = self._process_document(
                file_id, 
                result.extracted_text, 
                feedback_type
            )
            
            if not result.analysis:
                result.error = ERROR_DOCUMENT_PROCESSING_FAILED
                result.failed_phase = "document_processing"
                self._mark_failed(file_id, result.error)
                return result
            
            # Phase 3: AI Analysis (optional)
            if run_ai_analysis:
                result.ai_results = self._run_ai_analysis(
                    file_id,
                    result.structured_data
                )
                if result.ai_results is None:
                    result.error = ERROR_AI_ANALYSIS_FAILED
                    result.failed_phase = "ai_analysis"
                    logger.warning(f"AI analysis failed for file {file_id}, but processing succeeded")
                    # Don't fail entire operation if AI analysis fails
            
            # Mark file as completed
            uploaded_file_repo.set_completed(file_id, result.parsing_quality)
            logger.info(f"Successfully processed file {file_id}")
            
        except Exception as e:
            result.error = str(e)
            result.failed_phase = "unknown"
            logger.error(f"Processing error for file {file_id}: {str(e)}", exc_info=True)
            self._mark_failed(file_id, str(e))
        
        return result
    
    def _extract_text(self, file_id: int, file_path: str) -> Optional[str]:
        """Extract text from PDF, with caching"""
        uploaded_file_repo = self.repo.get_uploaded_file_repo()
        file_record = uploaded_file_repo.get_by_id(file_id)
        
        if not file_record:
            logger.error(f"File record not found: {file_id}")
            return None
        
        # Return cached text if already extracted
        if file_record.extracted_text:
            return file_record.extracted_text

        # Extract new text
        extracted_text = self.doc_processor.extract_text_from_doc(file_path)
        uploaded_file_repo.update(file_id, extracted_text=extracted_text)
        
        return extracted_text
    
    def _process_document(
        self,
        file_id: int,
        extracted_text: str,
        feedback_type: FeedbackType,
    ) -> tuple:
        """
        Process document into sections and structured data.
        
        Returns:
            (analysis, structured_data, extracted_sections, parsing_quality)
        """
        try:
            # Run document processing
            analysis = self.document_processor.process_document(
                extracted_text,
                feedback_type.value
            )
            
            # Extract structured data
            structured_data = self.document_processor.extract_structured_data(analysis)
            
            # Build sections dictionary using dynamic section names
            extracted_sections = {
                section.section_name: section.content
                for section in analysis.sections
            }
            
            return analysis, structured_data, extracted_sections, analysis.parsing_quality
            
        except Exception as e:
            logger.error(f"Document processing error for file {file_id}: {str(e)}")
            return None, None, None, 0.0
    
    def _run_ai_analysis(
        self,
        file_id: int,
        structured_data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Run AI analysis on structured data.
        
        Returns:
            Dictionary with AI analysis results, or None on error
        """
        try:
            ai_results = self.ai_analyzer.analyze_extracted_sections(
                feedback=structured_data.get("feedback"),
                project_activity=structured_data.get("project_activity"),
                function_activity=structured_data.get("function_activity"),
                learning=structured_data.get("learning"),
                certifications=structured_data.get("certifications"),
            )
            
            # Convert to dict format for response
            return {
                "identified_skills": [
                    {
                        "name": skill.skill_name,
                        "category": skill.category.value,
                        "confidence": skill.confidence,
                        "source": skill.source_section,
                    }
                    for skill in ai_results.identified_skills
                ],
                "identified_achievements": [
                    {
                        "title": ach.achievement_title,
                        "description": ach.description,
                        "impact": ach.impact,
                        "source": ach.source_section,
                    }
                    for ach in ai_results.identified_achievements
                ],
                "competency_gaps": ai_results.competency_gaps,
                "growth_areas": ai_results.growth_areas,
                "leadership_indicators": ai_results.leadership_indicators,
                "technical_strength": ai_results.technical_strength,
                "leadership_strength": ai_results.leadership_strength,
                "overall_score": ai_results.overall_score,
                "recommendations": ai_results.recommendations,
            }
            
        except Exception as e:
            logger.error(f"AI analysis error for file {file_id}: {str(e)}")
            return None
    
    def _normalize_feedback_type(self, upload_type: str) -> FeedbackType:
        """Convert upload type to normalized feedback type"""
        try:
            return FILE_TYPE_TO_FEEDBACK_TYPE.get(upload_type, FeedbackType.UNKNOWN)
        except (KeyError, AttributeError):
            return FeedbackType.UNKNOWN
    
    def _mark_failed(self, file_id: int, error_message: str) -> None:
        """Mark file processing as failed"""
        uploaded_file_repo = self.repo.get_uploaded_file_repo()
        uploaded_file_repo.set_failed(file_id, error_message)
