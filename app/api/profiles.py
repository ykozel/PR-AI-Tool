"""API endpoints for building consolidated PR profiles from multiple uploaded documents."""
import json
import logging
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.constants import UploadType
from app.core.repositories import RepositoryFactory
from app.models.file import UploadedFile
from app.models.pr_profile import PRProfile
from app.schemas.profile import ConsolidatedProfileResponse
from app.services.doc_processor import DocProcessor
from app.services.profile_consolidator import ProfileConsolidator
from app.services.report_generator import ReportGenerator
from app.services.year_over_year_analyzer import YearOverYearAnalyzer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/profiles", tags=["pr-profiles"])

_doc_processor = DocProcessor()
_consolidator = ProfileConsolidator()
_report_generator = ReportGenerator()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_filename(name: str) -> str:
    return re.sub(r"[^\w\-]", "_", name)


def _collect_report_context(
    db: Session,
    employee_name: str,
    year: int,
    current_files: List[UploadedFile],
) -> tuple:
    """Build (year_hierarchy, yoy_analysis) for generate_html().

    year_hierarchy  – dict with current_year, all_years, person_name
    yoy_analysis    – parsed JSON dict from YearOverYearAnalyzer, or None
    """
    repo = RepositoryFactory(db).get_pr_profile_repo()
    all_years = repo.get_all_years_for_employee(employee_name)
    year_hierarchy: Dict[str, Any] = {
        "current_year": year,
        "all_years": all_years,
        "person_name": employee_name,
    }

    yoy_analysis: Optional[Dict[str, Any]] = None
    prev_year = year - 1
    if prev_year in all_years:
        prev_profile = repo.get_by_name_year(employee_name, prev_year)
        if prev_profile:
            # Re-use persisted analysis when available
            if prev_profile.yoy_analysis:
                try:
                    yoy_analysis = json.loads(prev_profile.yoy_analysis)
                except Exception:
                    pass
            if yoy_analysis is None:
                prev_files = (
                    db.query(UploadedFile)
                    .filter(
                        UploadedFile.pr_profile_id == prev_profile.id,
                        UploadedFile.extracted_text.isnot(None),
                    )
                    .all()
                )
                prev_text = " ".join(
                    f.extracted_text for f in prev_files if f.extracted_text
                )
                curr_text = " ".join(
                    f.extracted_text for f in current_files if f.extracted_text
                )
                if prev_text and curr_text:
                    yoy_analysis = YearOverYearAnalyzer.analyze_year_comparison(
                        employee_name=employee_name,
                        previous_year=prev_year,
                        current_year=year,
                        previous_year_text=prev_text,
                        current_year_text=curr_text,
                    )

    return year_hierarchy, yoy_analysis


# ---------------------------------------------------------------------------
# Person+year HTML profile endpoints  (primary workflow)
# ---------------------------------------------------------------------------

@router.get(
    "/",
    summary="List all stored HTML profiles",
    description="Returns a list of all person+year profiles that have been created via document upload.",
)
def list_profiles(db: Session = Depends(get_db)):
    """List every PRProfile record that was created through the smart upload endpoint."""
    profiles = (
        db.query(PRProfile)
        .filter(PRProfile.employee_name.isnot(None))
        .order_by(PRProfile.employee_name, PRProfile.year)
        .all()
    )
    return [
        {
            "id": p.id,
            "employee_name": p.employee_name,
            "year": p.year,
            "has_html": bool(p.html_report),
            "files": (
                db.query(UploadedFile)
                .filter(UploadedFile.pr_profile_id == p.id)
                .count()
            ),
        }
        for p in profiles
    ]


@router.get(
    "/html/{person_name}/{year}",
    summary="Get the stored HTML profile for a person and year",
    description=(
        "Returns the pre-generated, self-contained HTML performance-review report "
        "for the given employee name and review year. The report is automatically "
        "created/updated whenever a document is uploaded via **POST /api/uploads/doc**."
    ),
    response_class=Response,
)
def get_profile_html(
    person_name: str,
    year: int,
    db: Session = Depends(get_db),
) -> Response:
    """Retrieve and serve the stored HTML report for a person+year combination."""
    profile = (
        db.query(PRProfile)
        .filter(PRProfile.employee_name == person_name, PRProfile.year == year)
        .first()
    )
    if not profile:
        raise HTTPException(
            status_code=404,
            detail=f"No profile found for '{person_name}' ({year}). "
            "Upload at least one document via POST /api/uploads/doc to create it.",
        )
    if not profile.html_report:
        raise HTTPException(
            status_code=404,
            detail=f"Profile exists for '{person_name}' ({year}) but no HTML has been generated yet.",
        )
    filename = f"PR_{_safe_filename(person_name)}_{year}.html"
    return Response(
        content=profile.html_report,
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/years/{person_name}/{year}",
    summary="Get year navigation hierarchy for a person",
    description=(
        "Returns all review years available for the given employee and marks the "
        "requested year as current. Used by the frontend to render year navigation."
    ),
)
def get_year_hierarchy(
    person_name: str,
    year: int,
    db: Session = Depends(get_db),
):
    repo = RepositoryFactory(db).get_pr_profile_repo()
    all_years = repo.get_all_years_for_employee(person_name)
    return {
        "person_name": person_name,
        "current_year": year,
        "all_years": all_years,
        "previous_year": (year - 1) if (year - 1) in all_years else None,
        "next_year": (year + 1) if (year + 1) in all_years else None,
        "has_yoy_analysis": any(
            bool(
                db.query(PRProfile.yoy_analysis)
                .filter(PRProfile.employee_name == person_name, PRProfile.year == year)
                .scalar()
            )
            for _ in [1]
        ),
    }


@router.post(
    "/html/{person_name}/{year}/regenerate",
    summary="Regenerate the HTML profile from all linked uploads",
    description=(
        "Forces a regeneration of the HTML report for the given person+year "
        "using all documents currently linked to that profile."
    ),
)
def regenerate_profile_html(
    person_name: str,
    year: int,
    db: Session = Depends(get_db),
):
    """Re-run the report generator over all files for this person+year and store the result."""
    profile = (
        db.query(PRProfile)
        .filter(PRProfile.employee_name == person_name, PRProfile.year == year)
        .first()
    )
    if not profile:
        raise HTTPException(
            status_code=404,
            detail=f"No profile found for '{person_name}' ({year}).",
        )

    files = (
        db.query(UploadedFile)
        .filter(
            UploadedFile.pr_profile_id == profile.id,
            UploadedFile.extracted_text.isnot(None),
        )
        .order_by(UploadedFile.uploaded_at)
        .all()
    )
    if not files:
        raise HTTPException(
            status_code=422,
            detail=f"No processed documents found for '{person_name}' ({year}). "
            "Upload documents first via POST /api/uploads/doc.",
        )

    try:
        year_hierarchy, yoy_analysis = _collect_report_context(db, person_name, year, files)
        html = _report_generator.generate_html(
            file_records=files,
            employee_name=person_name,
            review_year=year,
            year_hierarchy=year_hierarchy,
            yoy_analysis=yoy_analysis,
        )
    except Exception as exc:
        logger.error(f"HTML regeneration failed for {person_name}/{year}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Report generation failed: {exc}")

    profile.html_report = html
    if yoy_analysis:
        profile.yoy_analysis = json.dumps(yoy_analysis)
    db.add(profile)
    db.commit()

    return {
        "employee_name": person_name,
        "year": year,
        "pr_profile_id": profile.id,
        "files_included": len(files),
        "message": f"HTML report regenerated for '{person_name}' ({year}) from {len(files)} document(s).",
    }


# ---------------------------------------------------------------------------
# Profile rename / merge
# ---------------------------------------------------------------------------

class RenameProfileRequest(BaseModel):
    """Request body for renaming a profile's employee name."""
    new_name: str = Field(
        ...,
        min_length=1,
        description=(
            "The new employee name to assign.  "
            "If a profile already exists for (new_name, year), all uploaded files "
            "from the source profile are moved to it and the source profile is deleted. "
            "Otherwise the existing profile is renamed in-place."
        ),
    )


@router.post(
    "/html/{person_name}/{year}/rename",
    summary="Rename a profile's employee name (merges with existing if necessary)",
    description=(
        "Renames the employee name on a person+year profile and regenerates the HTML.\n\n"
        "**Merge behaviour:** if a profile already exists for `(new_name, year)`, "
        "all uploaded files from the source profile are moved to that target profile "
        "and the source profile is deleted.  The target profile's HTML is then "
        "regenerated to include all documents.\n\n"
        "**Rename behaviour:** if no profile exists yet for `(new_name, year)`, "
        "the existing profile is simply renamed in-place and its HTML regenerated."
    ),
)
def rename_profile(
    person_name: str,
    year: int,
    body: RenameProfileRequest,
    db: Session = Depends(get_db),
):
    """Move all uploads from one person-name to another (within the same year)."""
    new_name = body.new_name.strip()

    if new_name == person_name:
        raise HTTPException(status_code=400, detail="new_name is the same as the current name.")

    # Load source profile
    source = (
        db.query(PRProfile)
        .filter(PRProfile.employee_name == person_name, PRProfile.year == year)
        .first()
    )
    if not source:
        raise HTTPException(
            status_code=404,
            detail=f"No profile found for '{person_name}' ({year}).",
        )

    # Check whether a profile already exists for the target name
    target = (
        db.query(PRProfile)
        .filter(PRProfile.employee_name == new_name, PRProfile.year == year)
        .first()
    )

    if target:
        # ── Merge: move all files from source → target then drop source ────
        db.query(UploadedFile).filter(
            UploadedFile.pr_profile_id == source.id
        ).update({"pr_profile_id": target.id}, synchronize_session="fetch")
        db.delete(source)
        db.commit()
        profile = target
        action = "merged into existing"
    else:
        # ── Rename in-place ────────────────────────────────────────────────
        source.employee_name = new_name
        db.add(source)
        db.commit()
        db.refresh(source)
        profile = source
        action = "renamed"

    # Regenerate HTML with all now-linked files
    files = (
        db.query(UploadedFile)
        .filter(
            UploadedFile.pr_profile_id == profile.id,
            UploadedFile.extracted_text.isnot(None),
        )
        .order_by(UploadedFile.uploaded_at)
        .all()
    )
    if files:
        try:
            year_hierarchy, yoy_analysis = _collect_report_context(db, new_name, year, files)
            html = _report_generator.generate_html(
                file_records=files,
                employee_name=new_name,
                review_year=year,
                year_hierarchy=year_hierarchy,
                yoy_analysis=yoy_analysis,
            )
            profile.html_report = html
            if yoy_analysis:
                profile.yoy_analysis = json.dumps(yoy_analysis)
            db.add(profile)
            db.commit()
        except Exception as exc:
            logger.error(f"HTML regeneration failed after rename: {exc}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Rename succeeded but HTML regeneration failed: {exc}")

    return {
        "action": action,
        "old_name": person_name,
        "new_name": new_name,
        "year": year,
        "pr_profile_id": profile.id,
        "files_in_profile": len(files),
        "html_updated": bool(files),
        "message": (
            f"Profile '{person_name}' ({year}) {action} '{new_name}'. "
            f"HTML {'regenerated' if files else 'not updated (no processed files)'}."
        ),
    }


# ---------------------------------------------------------------------------
# Request schema (legacy manual workflow)
# ---------------------------------------------------------------------------

class ConsolidateRequest(BaseModel):
    """Request body for the consolidation endpoint."""

    upload_ids: List[int] = Field(
        ...,
        min_length=1,
        description=(
            "IDs of previously uploaded documents to consolidate. "
            "All supported types can be mixed: "
            + ", ".join(t.value for t in UploadType)
        ),
    )
    pr_profile_id: Optional[int] = Field(
        default=None,
        description="Optional PR Profile ID to scope the consolidation.",
    )
    include_raw_sections: bool = Field(
        default=False,
        description="Include raw per-category text chunks in the response (useful for debugging).",
    )


# ---------------------------------------------------------------------------
# Consolidate / report endpoints (legacy – use /html/{person}/{year} instead)
# ---------------------------------------------------------------------------

@router.post(
    "/consolidate",
    response_model=ConsolidatedProfileResponse,
    summary="Consolidate multiple documents into a unified PR profile",
    description=(
        "Upload documents one by one using **POST /api/uploads/doc**, then call this "
        "endpoint with all their IDs to receive a single structured performance-review "
        "profile containing:\n"
        "- **Skills Summary** (languages, domain expertise, automation, practices)\n"
        "- **Certifications**\n"
        "- **Learning**\n"
        "- **Feedback** (team & stakeholders, areas for improvement)\n"
        "- **Activity** (project and function activities with key contributions)"
    ),
)
def consolidate_profile(
    request: ConsolidateRequest,
    db: Session = Depends(get_db),
) -> ConsolidatedProfileResponse:
    """
    Build a consolidated PR profile from one or more uploaded documents.


    **Workflow**:
    1. Upload each document via ``POST /api/uploads/doc``
       (any mix of ``company_function``, ``auto_feedback``, ``project_feedback``,
       ``project_activity``, ``client_feedback``, ``additional_feedback``,
       ``pdp``, ``trainings``).
    2. Call this endpoint with all the returned ``id`` values.
    3. Receive a single structured profile.

    Documents without extracted text are automatically processed before
    consolidation; already-processed documents are served from cache.
    """
    # ── 1. Load all requested records ──────────────────────────────────────
    records: List[UploadedFile] = []
    missing: List[int] = []

    for uid in request.upload_ids:
        rec = db.query(UploadedFile).filter(UploadedFile.id == uid).first()
        if not rec:
            missing.append(uid)
        else:
            records.append(rec)

    if missing:
        raise HTTPException(
            status_code=404,
            detail=f"Upload IDs not found: {missing}",
        )

    # ── 2. Lazily extract text for any unprocessed files ───────────────────
    for rec in records:
        if not rec.extracted_text:
            logger.info(f"Extracting text for upload {rec.id} ({rec.original_filename})")
            text = _doc_processor.extract_text_from_doc(rec.file_path)
            if not text:
                raise HTTPException(
                    status_code=422,
                    detail=f"Could not extract text from upload {rec.id} ({rec.original_filename}). "
                    "Ensure the file is a valid .doc/.docx document.",
                )
            rec.extracted_text = text
            db.add(rec)

    db.commit()

    # ── 3. Consolidate ─────────────────────────────────────────────────────
    try:
        profile = _consolidator.consolidate(
            file_records=records,
            include_raw_sections=request.include_raw_sections,
        )
    except Exception as exc:
        logger.error(f"Consolidation failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Consolidation failed: {exc}")

    profile.pr_profile_id = request.pr_profile_id
    return profile


@router.get(
    "/consolidate/by-profile/{pr_profile_id}",
    response_model=ConsolidatedProfileResponse,
    summary="Consolidate all uploads linked to a PR Profile ID",
    description=(
        "Convenience endpoint: finds all uploads associated with a ``pr_profile_id`` "
        "and consolidates them automatically."
    ),
)
def consolidate_by_profile_id(
    pr_profile_id: int,
    file_type: Optional[UploadType] = Query(
        default=None, description="Filter to a specific document type"
    ),
    include_raw_sections: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> ConsolidatedProfileResponse:
    """
    Consolidate all uploads previously associated with a PR Profile ID.

    Upload documents with ``pr_profile_id`` set, then call this endpoint
    to get the full consolidated profile in one step.
    """
    query = db.query(UploadedFile).filter(UploadedFile.pr_profile_id == pr_profile_id)
    if file_type:
        query = query.filter(UploadedFile.file_type == file_type.value)

    records = query.order_by(UploadedFile.uploaded_at).all()

    if not records:
        raise HTTPException(
            status_code=404,
            detail=f"No uploads found for pr_profile_id={pr_profile_id}"
            + (f" with file_type={file_type.value}" if file_type else ""),
        )

    # Lazily extract text
    for rec in records:
        if not rec.extracted_text:
            text = _doc_processor.extract_text_from_doc(rec.file_path)
            if text:
                rec.extracted_text = text
                db.add(rec)

    db.commit()

    try:
        profile = _consolidator.consolidate(
            file_records=records,
            include_raw_sections=include_raw_sections,
        )
    except Exception as exc:
        logger.error(f"Consolidation failed for pr_profile_id={pr_profile_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Consolidation failed: {exc}")

    profile.pr_profile_id = pr_profile_id
    return profile


# ---------------------------------------------------------------------------
# HTML report generation
# ---------------------------------------------------------------------------

class ReportRequest(BaseModel):
    """Request body for the HTML report endpoint."""

    upload_ids: List[int] = Field(
        ...,
        min_length=1,
        description=(
            "IDs of previously uploaded documents to include in the report. "
            "Mix any document types: "
            + ", ".join(t.value for t in UploadType)
        ),
    )
    employee_name: str = Field(..., description="Employee full name (shown as H1 in the report)")
    employee_role: str = Field(default="", description="Current role / title")
    current_project: str = Field(default="", description="Current project assignment")
    review_year: Optional[int] = Field(
        default=None, description="Review year (defaults to current year)"
    )
    pr_profile_id: Optional[int] = Field(default=None)


def _load_and_extract(
    upload_ids: List[int], db: Session
) -> List[UploadedFile]:
    """
    Fetch UploadedFile records, lazily extracting text for any not yet processed.
    Raises 404 if any ID is missing.
    """
    records: List[UploadedFile] = []
    missing: List[int] = []

    for uid in upload_ids:
        rec = db.query(UploadedFile).filter(UploadedFile.id == uid).first()
        if not rec:
            missing.append(uid)
        else:
            records.append(rec)

    if missing:
        raise HTTPException(status_code=404, detail=f"Upload IDs not found: {missing}")

    for rec in records:
        if not rec.extracted_text:
            logger.info(f"Extracting text for upload {rec.id} ({rec.original_filename})")
            text = _doc_processor.extract_text_from_doc(rec.file_path)
            if not text:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"Could not extract text from upload {rec.id} "
                        f"({rec.original_filename}). "
                        "Ensure the file is a valid .doc/.docx document."
                    ),
                )
            rec.extracted_text = text
            db.add(rec)

    db.commit()
    return records


@router.post(
    "/report",
    summary="Generate downloadable HTML PR report",
    description=(
        "Upload documents one by one via **POST /api/uploads/doc**, then call this "
        "endpoint with all their IDs to receive a self-contained HTML performance-review "
        "report.\n\n"
        "The report contains the same sections as the reference format:\n"
        "**Skills Summary · Certifications · Learning · Feedback · Activity**\n\n"
        "An LLM (OpenAI) intelligently allocates content from each document to the "
        "appropriate section.  Falls back to pattern-based extraction when no API key "
        "is configured."
    ),
    response_class=Response,
)
def generate_report(
    request: ReportRequest,
    db: Session = Depends(get_db),
) -> Response:
    """
    Generate and download a self-contained HTML performance-review report.

    **Workflow**:
    1. Upload each document: ``POST /api/uploads/doc``
       (any mix of ``company_function``, ``auto_feedback``, ``project_feedback``,
       ``project_activity``, ``client_feedback``, ``additional_feedback``,
       ``pdp``, ``trainings``).
    2. Call this endpoint with all returned ``id`` values plus basic employee info.
    3. Download the ``.html`` file – open it in any browser, no external dependencies.
    """
    records = _load_and_extract(request.upload_ids, db)

    try:
        html_content = _report_generator.generate_html(
            file_records=records,
            employee_name=request.employee_name,
            employee_role=request.employee_role,
            current_project=request.current_project,
            review_year=request.review_year,
        )
    except Exception as exc:
        logger.error(f"Report generation failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Report generation failed: {exc}")

    safe_name = re.sub(r"[^\w\-]", "_", request.employee_name)
    year = request.review_year or __import__("datetime").datetime.utcnow().year
    filename = f"PR_{safe_name}_{year}.html"

    return Response(
        content=html_content,
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/report/by-profile/{pr_profile_id}",
    summary="Generate HTML report for all uploads linked to a PR Profile ID",
    description=(
        "Convenience endpoint: finds all uploads associated with a ``pr_profile_id`` "
        "and generates the HTML report automatically."
    ),
    response_class=Response,
)
def generate_report_by_profile(
    pr_profile_id: int,
    employee_name: str = Query(..., description="Employee full name"),
    employee_role: str = Query(default="", description="Role / title"),
    current_project: str = Query(default="", description="Current project"),
    review_year: Optional[int] = Query(default=None, description="Review year"),
    file_type: Optional[UploadType] = Query(
        default=None, description="Filter to a specific document type"
    ),
    db: Session = Depends(get_db),
) -> Response:
    """
    Generate an HTML report from all uploads linked to a given PR Profile ID.
    """
    query = db.query(UploadedFile).filter(UploadedFile.pr_profile_id == pr_profile_id)
    if file_type:
        query = query.filter(UploadedFile.file_type == file_type.value)

    records = query.order_by(UploadedFile.uploaded_at).all()
    if not records:
        raise HTTPException(
            status_code=404,
            detail=f"No uploads found for pr_profile_id={pr_profile_id}"
            + (f" with file_type={file_type.value}" if file_type else ""),
        )

    # Lazily extract text
    for rec in records:
        if not rec.extracted_text:
            text = _doc_processor.extract_text_from_doc(rec.file_path)
            if text:
                rec.extracted_text = text
                db.add(rec)
    db.commit()

    try:
        html_content = _report_generator.generate_html(
            file_records=records,
            employee_name=employee_name,
            employee_role=employee_role,
            current_project=current_project,
            review_year=review_year,
        )
    except Exception as exc:
        logger.error(f"Report generation failed for pr_profile_id={pr_profile_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Report generation failed: {exc}")

    safe_name = re.sub(r"[^\w\-]", "_", employee_name)
    year = review_year or __import__("datetime").datetime.utcnow().year
    filename = f"PR_{safe_name}_{year}.html"

    return Response(
        content=html_content,
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

