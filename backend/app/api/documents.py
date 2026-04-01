"""API endpoints for document processing and section extraction"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.file import UploadedFile
from app.models.feedback import Feedback
from app.models.project_activity import ProjectActivity
from app.models.function_activity import FunctionActivity
from app.core.constants import FILE_TYPE_TO_FEEDBACK_TYPE
from app.services.doc_processor import DocProcessor
from app.services.document_processor import DocumentProcessor
from app.schemas.document_processing import (
    DocumentAnalysisRequest,
    DocumentAnalysisResponse,
    BulkProcessingRequest,
    BulkProcessingResponse,
    SectionExtractionRequest,
    SectionExtractionResponse,
    ExtractedSectionData,
    ProjectActivityData,
    FunctionActivityData
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["document-processing"])

doc_processor = DocProcessor()
document_processor = DocumentProcessor()


def _normalize_feedback_type(file_type: Optional[str], default: str = "unknown") -> str:
    """Map a DB file_type value to a normalized feedback type string."""
    ft = FILE_TYPE_TO_FEEDBACK_TYPE.get(file_type or "")
    return ft.value if ft else default


def _load_file_text(db: Session, upload_id: int) -> UploadedFile:
    """Retrieve an uploaded file, lazily extracting its text if needed.

    Raises HTTPException 404 if not found, 400 if text cannot be extracted.
    """
    uploaded_file = db.query(UploadedFile).filter(UploadedFile.id == upload_id).first()
    if not uploaded_file:
        raise HTTPException(status_code=404, detail="Upload not found")
    if not uploaded_file.extracted_text:
        extracted_text = doc_processor.extract_text_from_doc(uploaded_file.file_path)
        if not extracted_text:
            raise HTTPException(status_code=400, detail="Could not extract text from document")
        uploaded_file.extracted_text = extracted_text
        db.add(uploaded_file)
        db.commit()
    return uploaded_file


@router.post("/process/{upload_id}", response_model=DocumentAnalysisResponse)
def process_document(
    upload_id: int,
    feedback_type: Optional[str] = Query("unknown", description="Overrides auto-detected feedback type"),
    pr_profile_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Process an uploaded .doc/.docx document and extract all sections.

    Sections are detected dynamically regardless of their names or count.
    """
    try:
        uploaded_file = _load_file_text(db, upload_id)
        extracted_text = uploaded_file.extracted_text
        feedback_type_normalized = _normalize_feedback_type(
            uploaded_file.file_type, feedback_type or "unknown"
        )

        analysis = document_processor.process_document(extracted_text, feedback_type_normalized)
        structured_data = document_processor.extract_structured_data(analysis)

        extracted_sections = {
            section.section_name: section.content
            for section in analysis.sections
        }

        if pr_profile_id:
            _save_feedback_to_db(
                db, pr_profile_id, feedback_type_normalized, structured_data, upload_id
            )

        return DocumentAnalysisResponse(
            success=True,
            upload_id=upload_id,
            parsing_quality=analysis.parsing_quality,
            sections_found=len(analysis.sections),
            extracted_sections=extracted_sections,
            structured_data=structured_data,
            message=f"Successfully processed {len(analysis.sections)} sections"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing document {upload_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk-process", response_model=BulkProcessingResponse)
def bulk_process_documents(
    request: BulkProcessingRequest,
    db: Session = Depends(get_db)
):
    """Process multiple documents in bulk."""
    results = []
    successful = 0
    failed = 0

    for upload_id in request.upload_ids:
        try:
            uploaded_file = _load_file_text(db, upload_id)
            feedback_type_normalized = _normalize_feedback_type(uploaded_file.file_type)

            analysis = document_processor.process_document(
                uploaded_file.extracted_text or "", feedback_type_normalized
            )
            structured_data = document_processor.extract_structured_data(analysis)
            extracted_sections = {
                section.section_name: section.content
                for section in analysis.sections
            }

            if request.pr_profile_id:
                _save_feedback_to_db(
                    db, request.pr_profile_id, feedback_type_normalized,
                    structured_data, upload_id
                )

            results.append(DocumentAnalysisResponse(
                success=True,
                upload_id=upload_id,
                parsing_quality=analysis.parsing_quality,
                sections_found=len(analysis.sections),
                extracted_sections=extracted_sections,
                structured_data=structured_data,
                message="Processed successfully"
            ))
            successful += 1

        except Exception as e:
            logger.error(f"Error in bulk processing upload {upload_id}: {str(e)}")
            failed += 1

    return BulkProcessingResponse(
        total_documents=len(request.upload_ids),
        successfully_processed=successful,
        failed_documents=failed,
        results=results
    )


@router.get("/extract-section", response_model=SectionExtractionResponse)
def extract_section(
    upload_id: int,
    section_name: str = Query(..., description="Name of the section to extract"),
    db: Session = Depends(get_db)
):
    """
    Extract a specific named section from a processed document.

    Pass the exact section name as it appears in the document (case-insensitive).
    """
    try:
        uploaded_file = _load_file_text(db, upload_id)
        feedback_type_normalized = _normalize_feedback_type(uploaded_file.file_type)

        analysis = document_processor.process_document(
            uploaded_file.extracted_text, feedback_type_normalized
        )

        section = document_processor.get_section_by_name(analysis, section_name)

        if not section:
            raise HTTPException(
                status_code=404,
                detail=f"Section '{section_name}' not found in document"
            )

        items = document_processor.section_extractor.extract_bullet_points(section.content)

        return SectionExtractionResponse(
            section_name=section.section_name,
            content=section.content,
            items=items,
            confidence=section.confidence
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting section: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/project-activity/{upload_id}", response_model=ProjectActivityData)
def extract_project_activity(
    upload_id: int,
    section_name: str = Query("Project Activity", description="Section name to look up"),
    db: Session = Depends(get_db)
):
    """Extract and parse a project activity section into structured data."""
    try:
        uploaded_file = _load_file_text(db, upload_id)
        feedback_type_normalized = _normalize_feedback_type(uploaded_file.file_type, "project")

        analysis = document_processor.process_document(
            uploaded_file.extracted_text, feedback_type_normalized
        )

        section = document_processor.get_section_by_name(analysis, section_name)

        if not section:
            raise HTTPException(status_code=404, detail=f"Section '{section_name}' not found")

        return _parse_project_activity(section.content)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting project activity: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/function-activity/{upload_id}", response_model=FunctionActivityData)
def extract_function_activity(
    upload_id: int,
    section_name: str = Query("Function Activity", description="Section name to look up"),
    db: Session = Depends(get_db)
):
    """Extract and parse a function activity section into structured data."""
    try:
        uploaded_file = _load_file_text(db, upload_id)
        feedback_type_normalized = _normalize_feedback_type(uploaded_file.file_type, "function")

        analysis = document_processor.process_document(
            uploaded_file.extracted_text, feedback_type_normalized
        )

        section = document_processor.get_section_by_name(analysis, section_name)

        if not section:
            raise HTTPException(status_code=404, detail=f"Section '{section_name}' not found")

        return _parse_function_activity(section.content)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting function activity: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/{upload_id}")
def get_analysis_details(
    upload_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed analysis of a processed document."""
    try:
        uploaded_file = db.query(UploadedFile).filter(
            UploadedFile.id == upload_id
        ).first()

        if not uploaded_file:
            raise HTTPException(status_code=404, detail="Upload not found")

        if not uploaded_file.extracted_text:
            raise HTTPException(status_code=400, detail="Document not yet processed")

        feedback_type_normalized = _normalize_feedback_type(uploaded_file.file_type)

        analysis = document_processor.process_document(
            uploaded_file.extracted_text, feedback_type_normalized
        )

        return {
            "upload_id": upload_id,
            "file_name": uploaded_file.original_filename,
            "feedback_type": feedback_type_normalized,
            "parsing_quality": analysis.parsing_quality,
            "sections": [
                {
                    "name": s.section_name,
                    "confidence": s.confidence,
                    "content_length": len(s.content),
                }
                for s in analysis.sections
            ],
            "total_sections_found": len(analysis.sections),
            "total_text_length": len(analysis.full_text),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _save_feedback_to_db(
    db: Session,
    pr_profile_id: int,
    feedback_type: str,
    structured_data: dict,
    upload_id: int,
) -> None:
    """Persist extracted section data to the Feedback table."""
    try:
        sections = structured_data.get("sections", {})
        feedback = Feedback(
            pr_profile_id=pr_profile_id,
            source=feedback_type.lower(),
            certifications=sections.get("certifications"),
            learning=sections.get("learning"),
            project_activity=sections.get("project_activity"),
            function_activity=sections.get("function_activity"),
            feedback_text=sections.get("feedback"),
        )
        db.add(feedback)
        db.commit()
        logger.info(f"Saved feedback for upload {upload_id} to database")
    except Exception as e:
        logger.error(f"Error saving feedback to database: {str(e)}")
        db.rollback()


def _parse_project_activity(content: str) -> "ProjectActivityData":
    """Extract project activity fields from raw section text."""
    import re
    lines = content.split("\n")
    data: dict = {
        "project_name": "",
        "responsibilities_description": None,
        "key_contributions": None,
        "duration_start": None,
        "duration_end": None,
    }
    name_match = re.search(r"(?:project|initiative|assignment)[:\s]*(.+?)(?:\n|$)", content, re.IGNORECASE)
    if name_match:
        data["project_name"] = name_match.group(1).strip()
    elif lines:
        data["project_name"] = lines[0].strip()
    resp_match = re.search(r"(?:responsibilit|role|duty)[:\s]*(.+?)(?=\n|$)", content, re.IGNORECASE | re.DOTALL)
    if resp_match:
        data["responsibilities_description"] = resp_match.group(1).strip()
    contrib_match = re.search(r"(?:contribution|achievement|impact|result)[:\s]*(.+?)(?=\n|$)", content, re.IGNORECASE | re.DOTALL)
    if contrib_match:
        data["key_contributions"] = contrib_match.group(1).strip()
    durations = re.findall(r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\w+\s+\d{4})", content)
    if len(durations) >= 1:
        data["duration_start"] = durations[0]
    if len(durations) >= 2:
        data["duration_end"] = durations[1]
    return ProjectActivityData(**data)


def _parse_function_activity(content: str) -> "FunctionActivityData":
    """Extract function activity fields from raw section text."""
    import re
    lines = content.split("\n")
    data: dict = {
        "function_name": "",
        "activity_description": None,
        "key_contributions": None,
        "involvement_level": "Contributor",
    }
    name_match = re.search(r"(?:function|committee|working group|task force)[:\s]*(.+?)(?:\n|$)", content, re.IGNORECASE)
    if name_match:
        data["function_name"] = name_match.group(1).strip()
    elif lines:
        data["function_name"] = lines[0].strip()
    activity_match = re.search(r"(?:activit|involved|participated)[:\s]*(.+?)(?=\n|$)", content, re.IGNORECASE | re.DOTALL)
    if activity_match:
        data["activity_description"] = activity_match.group(1).strip()
    contrib_match = re.search(r"(?:contribution|outcome|impact|result)[:\s]*(.+?)(?=\n|$)", content, re.IGNORECASE | re.DOTALL)
    if contrib_match:
        data["key_contributions"] = contrib_match.group(1).strip()
    content_lower = content.lower()
    if any(w in content_lower for w in ["lead", "leading", "led", "leader"]):
        data["involvement_level"] = "Lead"
    elif any(w in content_lower for w in ["support", "supporting"]):
        data["involvement_level"] = "Support"
    return FunctionActivityData(**data)
