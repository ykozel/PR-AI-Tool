"""API routes for file upload and processing (refactored with DI and utilities)"""
import hashlib
import logging
import os
from datetime import datetime
from typing import Annotated, Optional, List

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core import (
    RepositoryFactory,
    FileValidationError,
    FileNotFoundError,
    ErrorHandler,
    MAX_FILE_SIZE_MB,
)
from app.core.constants import (
    UploadType,
    FeedbackType,
    FILE_TYPE_TO_FEEDBACK_TYPE,
)
from app.models.file import UploadedFile
from app.schemas.file_upload import (
    FileUploadResponse,
    FileProcessingResponse,
    FileListResponse,
    UploadStatusResponse,
    ExtractedSectionsResponse,
    SmartUploadResponse,
    UploadTypeEnum,
    UploadAndProcessResponse,
    UploadProcessAnalyzeResponse,
)
from app.services.doc_processor import DocProcessor
from app.services.document_processor import DocumentProcessor
from app.services.ai_analyzer import AIAnalyzer
from app.services.file_processing_orchestrator import FileProcessingOrchestrator
from app.services.report_generator import ReportGenerator
from app.utils.file_validation import FileValidator, FileOperations
from app.utils.file_upload import FileUploadManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/uploads", tags=["file-uploads"])

# Initialize services (keep for backward compatibility, but use dependency injection where possible)
file_manager = FileUploadManager()
doc_processor = DocProcessor()
document_processor = DocumentProcessor()
ai_analyzer = AIAnalyzer()


def get_orchestrator(db: Session = Depends(get_db)) -> FileProcessingOrchestrator:
    """Dependency injection: provide FileProcessingOrchestrator instance"""
    repo_factory = RepositoryFactory(db)
    return FileProcessingOrchestrator(repo_factory, doc_processor, document_processor, ai_analyzer)


@router.post(
    "/doc",
    response_model=SmartUploadResponse,
    summary="Upload a .doc/.docx file",
    description=(
        "Upload a feedback document for an employee. The document is automatically "
        "text-extracted and the HTML performance-review profile for that person and year "
        "is created (or updated if it already exists). All previously uploaded documents "
        "for the same person+year are included in the regenerated HTML."
    ),
)
async def upload_doc(
    file: Annotated[UploadFile, File(description=".doc or .docx file to upload")],
    upload_type: Annotated[
        UploadTypeEnum,
        Form(
            description=(
                "Type of feedback document: company_function, auto_feedback, "
                "project_feedback, client_feedback, additional_feedback, pdp, "
                "trainings, project_activity"
            )
        ),
    ],
    person_name: Annotated[
        str,
        Form(description="Employee full name, e.g. 'Emma Laurent'. Used to group all uploads into one profile."),
    ],
    review_year: Annotated[
        int,
        Form(description="Review year, e.g. 2025. Together with person_name identifies the profile."),
    ],
    uploaded_by_email: Annotated[
        Optional[str], Form(description="Email of the person uploading (optional)")
    ] = None,
    db: Session = Depends(get_db),
):
    """
    Upload a .doc/.docx feedback document and automatically maintain the
    single HTML report for this person + year.

    - First upload for a person+year → creates the profile and generates the HTML.
    - Subsequent uploads for the same person+year → adds the document and
      regenerates the HTML so all documents are reflected.
    """
    try:
        # 1. Read and validate
        content = await file.read()
        is_valid, error_msg = FileValidator.validate_doc_upload(file.filename or "", content)
        if not is_valid:
            raise FileValidationError(error_msg or "Invalid file")

        # 2. Save to disk
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_name = FileValidator.secure_filename(file.filename or "upload")
        unique_filename = f"profile_{timestamp}_{safe_name}"
        file_path = os.path.join("uploads", unique_filename)
        success, result = FileOperations.save_file(file_path, content)
        if not success:
            raise HTTPException(status_code=500, detail=result)

        # 3. Extract text
        extracted_text = doc_processor.extract_text_from_doc(file_path)

        # 3a. Deduplication: compute hash of extracted text and check for existing entry
        content_hash: Optional[str] = None
        if extracted_text:
            content_hash = hashlib.sha256(extracted_text.encode("utf-8")).hexdigest()

        # 4. Find or create the PRProfile for (person_name, review_year)
        factory = RepositoryFactory(db)
        profile = factory.get_pr_profile_repo().find_or_create(person_name, review_year)

        # Check for a duplicate document already linked to this profile
        if content_hash:
            existing = (
                db.query(UploadedFile)
                .filter(
                    UploadedFile.pr_profile_id == profile.id,
                    UploadedFile.content_hash == content_hash,
                )
                .first()
            )
            if existing:
                # Remove the file we just saved to disk – it's a duplicate
                try:
                    os.remove(file_path)
                except OSError:
                    pass
                all_files = (
                    db.query(UploadedFile)
                    .filter(
                        UploadedFile.pr_profile_id == profile.id,
                        UploadedFile.extracted_text.isnot(None),
                    )
                    .order_by(UploadedFile.uploaded_at)
                    .all()
                )
                return SmartUploadResponse(
                    upload_id=existing.id,
                    pr_profile_id=profile.id,
                    employee_name=person_name,
                    review_year=review_year,
                    files_in_profile=len(all_files),
                    html_updated=False,
                    message=(
                        f"Duplicate document detected – '{file.filename}' has identical content to "
                        f"'{existing.original_filename}' (upload #{existing.id}) already in this profile. "
                        f"No new entry was created."
                    ),
                )

        # 5. Create UploadedFile record linked to this profile
        db_file = UploadedFile(
            filename=unique_filename,
            original_filename=file.filename or "unknown",
            file_path=file_path,
            file_type=upload_type.value,
            file_size=len(content) / (1024 * 1024),
            content_hash=content_hash,
            pr_profile_id=profile.id,
            uploaded_by_email=uploaded_by_email,
            upload_status="completed" if extracted_text else "failed",
            extracted_text=extracted_text,
            processed_at=datetime.utcnow() if extracted_text else None,
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)

        # 6. Collect all files with extracted text for this profile
        all_files = (
            db.query(UploadedFile)
            .filter(
                UploadedFile.pr_profile_id == profile.id,
                UploadedFile.extracted_text.isnot(None),
            )
            .order_by(UploadedFile.uploaded_at)
            .all()
        )

        # 7. (Re)generate and store the HTML report
        html_updated = False
        generation_status = ""
        if all_files:
            try:
                generator = ReportGenerator()
                
                # Get year hierarchy for navigation
                year_hierarchy = factory.get_pr_profile_repo().get_year_hierarchy(person_name, review_year)
                year_hierarchy["person_name"] = person_name
                
                html = generator.generate_html(
                    file_records=all_files,
                    employee_name=person_name,
                    review_year=review_year,
                    year_hierarchy=year_hierarchy,
                )
                factory.get_pr_profile_repo().update_html(profile, html)
                html_updated = True
                generation_status = f"HTML profile updated from {len(all_files)} document(s)."
                logger.info(
                    f"HTML report updated for {person_name} ({review_year}), "
                    f"profile_id={profile.id}, files={len(all_files)}, "
                    f"linked_to_year={year_hierarchy.get('previous_year', 'N/A')}"
                )
            except Exception as exc:
                generation_status = f"HTML generation failed: {str(exc)}"
                logger.error(f"HTML generation failed for profile {profile.id}: {exc}", exc_info=True)
        else:
            generation_status = f"No files with extracted text yet. HTML will update when documents are processed. ({len(all_files)} files in profile)"

        return SmartUploadResponse(
            upload_id=db_file.id,
            pr_profile_id=profile.id,
            employee_name=person_name,
            review_year=review_year,
            files_in_profile=len(all_files),
            html_updated=html_updated,
            message=(
                f"Uploaded '{file.filename}' for {person_name} ({review_year}). "
                + f"Text extraction: {'OK' if extracted_text else 'FAILED'}. "
                + generation_status
            ),
        )

    except FileValidationError as e:
        raise e.to_http_exception()
    except HTTPException:
        raise
    except Exception as e:
        status, message = ErrorHandler.handle_exception(e, context="file_upload")
        raise HTTPException(status_code=status, detail=message)


@router.post(
    "/doc-and-process",
    response_model=UploadAndProcessResponse,
    summary="Upload and process .doc/.docx in one call",
    description="Upload a .doc/.docx file and automatically extract all sections in a single request"
)
async def upload_and_process_doc(
    file: Annotated[UploadFile, File(description=".doc or .docx file to upload")],
    upload_type: Annotated[UploadTypeEnum, Form(description="Type of feedback document: company_function, auto_feedback, project_feedback, client_feedback, additional_feedback, pdp, trainings, project_activity")],
    pr_profile_id: Annotated[Optional[int], Form(description="PR Profile ID to associate")] = None,
    uploaded_by_email: Annotated[Optional[str], Form(description="Email of uploader")] = None,
    db: Session = Depends(get_db),
    orchestrator: FileProcessingOrchestrator = Depends(get_orchestrator),
):
    """
    Upload and process a .doc/.docx file in a single request (DRY: uses orchestrator).
    
    Returns upload metadata + processing results (sections, structured data).
    """
    try:
        # Read and validate file
        content = await file.read()
        is_valid, error_msg = FileValidator.validate_doc_upload(file.filename or "", content)
        if not is_valid:
            raise FileValidationError(error_msg or "Invalid file")
        
        # Save file
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_name = FileValidator.secure_filename(file.filename or "upload")
        unique_filename = f"profile_{timestamp}_{safe_name}"
        file_path = os.path.join("uploads", unique_filename)
        
        success, result = FileOperations.save_file(file_path, content)
        if not success:
            raise HTTPException(status_code=500, detail=result)
        
        # Create database record
        repo = RepositoryFactory(db).get_uploaded_file_repo()
        db_file = repo.create(
            filename=unique_filename,
            original_filename=file.filename or "unknown",
            file_path=file_path,
            file_type=upload_type.value,
            file_size=len(content),
            pr_profile_id=pr_profile_id,
            uploaded_by_email=uploaded_by_email,
            upload_status="processing",
        )
        
        # Use orchestrator for processing (DRY: centralized logic)
        result = orchestrator.extract_and_process(
            file_id=db_file.id,
            file_path=file_path,
            upload_type=upload_type.value,
            run_ai_analysis=False,
        )
        
        if result.error:
            raise HTTPException(status_code=422, detail=result.error)
        
        # Return response with processed data
        return UploadAndProcessResponse(
            id=db_file.id,
            filename=db_file.filename,
            original_filename=db_file.original_filename,
            file_type=upload_type,
            file_size=len(content) / (1024 * 1024),
            uploaded_at=db_file.uploaded_at,
            processing_status="completed",
            parsing_quality=result.parsing_quality,
            sections_found=len(result.extracted_sections or {}),
            extracted_sections=result.extracted_sections or {},
            structured_data=result.structured_data or {},
            processed_at=datetime.utcnow(),
            message="File uploaded and processed successfully"
        )
        
    except FileValidationError as e:
        raise e.to_http_exception()
    except HTTPException:
        raise
    except Exception as e:
        status, message = ErrorHandler.handle_exception(e, context="upload_and_process")
        raise HTTPException(status_code=status, detail=message)


@router.post(
    "/process/{file_id}",
    response_model=FileProcessingResponse,
    summary="Process uploaded .doc/.docx file",
    description="Extract text and sections from an uploaded .doc/.docx document"
)
async def process_doc(
    file_id: int,
    db: Session = Depends(get_db),
    orchestrator: FileProcessingOrchestrator = Depends(get_orchestrator),
):
    """
    Process an uploaded .doc/.docx file to extract text and structured sections.
    Uses orchestrator to standardize processing logic (DRY principle).
    """
    try:
        repo = RepositoryFactory(db).get_uploaded_file_repo()
        db_file = repo.get_by_id(file_id)
        if not db_file:
            raise HTTPException(status_code=404, detail="File not found")

        # Return cached result if already processed
        if db_file.upload_status == "completed":
            return FileProcessingResponse(
                id=db_file.id,
                filename=db_file.filename,
                file_type=db_file.file_type,
                upload_status=db_file.upload_status,
                extracted_text_length=len(db_file.extracted_text) if db_file.extracted_text else 0,
                processed_at=db_file.processed_at,
            )

        result = orchestrator.extract_and_process(
            file_id=db_file.id,
            file_path=db_file.file_path,
            upload_type=db_file.file_type,
            run_ai_analysis=False,
        )

        if result.error:
            raise HTTPException(status_code=422, detail=result.error)

        logger.info(f"File processed successfully: {db_file.filename} (ID: {db_file.id})")

        return FileProcessingResponse(
            id=db_file.id,
            filename=db_file.filename,
            file_type=db_file.file_type,
            upload_status="completed",
            extracted_text_length=len(result.extracted_text) if result.extracted_text else 0,
            processed_at=datetime.utcnow(),
        )

    except HTTPException:
        raise
    except Exception as e:
        status_code, message = ErrorHandler.handle_exception(e, context="process_doc")
        raise HTTPException(status_code=status_code, detail=message)


@router.post(
    "/doc-and-process-analyze",
    response_model=UploadProcessAnalyzeResponse,
    summary="Upload, process, and analyze .doc/.docx in one operation",
    description="Upload a .doc/.docx file and perform complete document processing + AI analysis in a single request"
)
async def upload_process_analyze_doc(
    file: Annotated[UploadFile, File(description=".doc or .docx file to upload")],
    upload_type: Annotated[UploadTypeEnum, Form(description="Type of feedback document: company_function, auto_feedback, project_feedback, client_feedback, additional_feedback, pdp, trainings, project_activity")],
    pr_profile_id: Annotated[Optional[int], Form(description="PR Profile ID to associate")] = None,
    uploaded_by_email: Annotated[Optional[str], Form(description="Email of uploader")] = None,
    db: Session = Depends(get_db),
    orchestrator: FileProcessingOrchestrator = Depends(get_orchestrator),
):
    """
    Unified endpoint: upload â†’ extract sections â†’ AI analysis.

    Supported upload_type values:
      company_function, auto_feedback, project_feedback, client_feedback,
      additional_feedback, pdp, trainings, project_activity

    Returns UploadProcessAnalyzeResponse with:
    - Upload metadata (file info, timestamps)
    - Processing results (extracted sections, structured data, parsing quality)
    - AI analysis results (skills, achievements, competency gaps, growth areas, strengths)
    """
    start_time = datetime.utcnow()
    db_file = None

    try:
        # â”€â”€ PHASE 1: UPLOAD & VALIDATE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        content = await file.read()
        is_valid, error_msg = FileValidator.validate_doc_upload(file.filename or "", content)
        if not is_valid:
            raise FileValidationError(error_msg or "Invalid file")

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_name = FileValidator.secure_filename(file.filename or "upload")
        unique_filename = f"profile_{timestamp}_{safe_name}"
        file_path = os.path.join("uploads", unique_filename)

        success, save_result = FileOperations.save_file(file_path, content)
        if not success:
            raise HTTPException(status_code=500, detail=save_result)

        db_file = UploadedFile(
            original_filename=file.filename or "unknown",
            filename=unique_filename,
            file_path=file_path,
            file_type=upload_type.value,
            file_size=len(content),
            pr_profile_id=pr_profile_id,
            uploaded_by_email=uploaded_by_email,
            upload_status="processing",
            uploaded_at=start_time,
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)

        logger.info(f"File saved: {unique_filename} (DB ID: {db_file.id})")

        # â”€â”€ PHASES 2 & 3: PROCESS + AI ANALYSIS (via orchestrator) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        proc = orchestrator.extract_and_process(
            file_id=db_file.id,
            file_path=file_path,
            upload_type=upload_type.value,
            run_ai_analysis=True,
        )

        # Fail only if document processing itself failed (AI failure is non-fatal)
        if proc.error and proc.failed_phase not in (None, "ai_analysis"):
            raise HTTPException(status_code=422, detail=proc.error)

        ai = proc.ai_results or {}
        sections = proc.extracted_sections or {}
        processed_at = datetime.utcnow()

        logger.info(
            f"Unified operation completed for {unique_filename}: "
            f"{len(sections)} sections, quality={proc.parsing_quality:.2f}"
        )

        return UploadProcessAnalyzeResponse(
            id=db_file.id,
            filename=db_file.filename,
            original_filename=db_file.original_filename,
            file_type=upload_type,
            file_size=len(content) / (1024 * 1024),
            uploaded_at=db_file.uploaded_at,
            processing_status="completed",
            parsing_quality=proc.parsing_quality,
            sections_found=len(sections),
            extracted_sections=sections,
            structured_data=proc.structured_data or {},
            processed_at=processed_at,
            identified_skills=ai.get("identified_skills", []),
            identified_achievements=ai.get("identified_achievements", []),
            competency_gaps=ai.get("competency_gaps", []),
            growth_areas=ai.get("growth_areas", []),
            leadership_indicators=ai.get("leadership_indicators", []),
            technical_strength=ai.get("technical_strength", 0.0),
            leadership_strength=ai.get("leadership_strength", 0.0),
            ai_overall_score=ai.get("overall_score", 0.0),
            recommendations=ai.get("recommendations", []),
            analyzed_at=processed_at,
            message=(
                f"âœ“ Upload | âœ“ Processing ({len(sections)} sections, "
                f"quality: {proc.parsing_quality:.2f}) | âœ“ AI analysis"
            ),
        )

    except FileValidationError as e:
        raise e.to_http_exception()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in unified upload/process/analyze: {str(e)}", exc_info=True)
        if db_file:
            try:
                db_file.upload_status = "failed"
                db_file.extraction_error = str(e)
                db.add(db_file)
                db.commit()
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=f"Error in unified operation: {str(e)}")
@router.get(
    "/status/{file_id}",
    response_model=UploadStatusResponse,
    summary="Get upload status",
    description="Check the processing status of an uploaded file"
)
async def get_upload_status(
    file_id: int,
    db: Session = Depends(get_db),
):
    """Get the current status of an uploaded file"""
    db_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    return UploadStatusResponse(
        id=db_file.id,
        filename=db_file.filename,
        file_type=db_file.file_type,
        upload_status=db_file.upload_status,
        uploaded_at=db_file.uploaded_at,
        processed_at=db_file.processed_at,
        extraction_error=db_file.extraction_error,
    )


@router.get(
    "/list",
    response_model=FileListResponse,
    summary="List uploaded files",
    description="Get a list of all uploaded .doc/.docx files with pagination"
)
async def list_uploads(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of records to return"),
    file_type: Optional[UploadTypeEnum] = Query(None, description="Filter by file type"),
    db: Session = Depends(get_db),
):
    """List all uploaded files with optional filtering"""
    query = db.query(UploadedFile)
    
    if file_type:
        query = query.filter(UploadedFile.file_type == file_type.value)
    
    total = query.count()
    files = query.order_by(UploadedFile.uploaded_at.desc()).offset(skip).limit(limit).all()
    
    items = [
        FileUploadResponse(
            id=f.id,
            filename=f.filename,
            original_filename=f.original_filename,
            file_type=f.file_type,
            file_size=f.file_size,
            upload_status=f.upload_status,
            uploaded_at=f.uploaded_at,
        )
        for f in files
    ]
    
    return FileListResponse(total=total, items=items)


@router.delete(
    "/{file_id}",
    summary="Delete uploaded file",
    description="Delete an uploaded .doc/.docx file"
)
async def delete_upload(
    file_id: int,
    db: Session = Depends(get_db),
):
    """Delete an uploaded file and its database record"""
    try:
        db_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if not db_file:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Delete physical file
        success, msg = file_manager.delete_file(db_file.filename)
        
        # Delete database record
        db.delete(db_file)
        db.commit()
        
        logger.info(f"File deleted: {db_file.filename} (ID: {file_id})")
        
        return {
            "success": True,
            "message": f"File {db_file.original_filename} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file {file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")
