from datetime import date
import os
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session as DBSession

from database import get_db
from models import Patient, Report
from report_ocr_extract import extract_report_text

router = APIRouter(prefix="/reports", tags=["Reports"])

BACKEND_ROOT = Path(__file__).resolve().parent.parent

# =========================================
# UPLOAD CONFIG (Day 12 Phase 1)
# =========================================

UPLOAD_DIR_REPORTS = str(BACKEND_ROOT / "uploads" / "reports")

MAX_REPORT_FILE_SIZE_MB = 50

MAX_REPORT_FILE_SIZE_BYTES = MAX_REPORT_FILE_SIZE_MB * 1024 * 1024

ALLOWED_REPORT_MIME_TYPES = frozenset(
    {
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/jpg",
    }
)

OCR_TEXT_PREVIEW_MAX_CHARS = 2000

OCR_ERROR_DB_MAX_LEN = 8000


# =========================================
# REPORTS UPLOAD DIRECTORY
# =========================================

os.makedirs(UPLOAD_DIR_REPORTS, exist_ok=True)


# =========================================
# UPLOAD HELPERS
# =========================================


def _normalize_mime_type(content_type: Optional[str]) -> str:
    if not content_type:
        return ""
    return content_type.split(";")[0].strip().lower()


def validate_report_mime_type(content_type: Optional[str]) -> str:
    normalized = _normalize_mime_type(content_type)
    if normalized not in ALLOWED_REPORT_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                "Allowed types: PDF, PNG, JPEG."
            ),
        )
    return normalized


def validate_report_file_size(contents: bytes) -> None:
    if len(contents) > MAX_REPORT_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"File too large. "
                f"Maximum size is {MAX_REPORT_FILE_SIZE_MB}MB."
            ),
        )


def create_safe_report_filename(original_filename: Optional[str]) -> str:
    raw = original_filename or "upload"
    base = os.path.basename(raw).replace(" ", "_").replace("/", "_").replace("\\", "_")
    if not base or base == "." or base == "..":
        base = "upload"
    return f"{uuid.uuid4()}_{base}"


def cleanup_report_file(path: str) -> None:
    try:
        if os.path.isfile(path):
            os.remove(path)
    except OSError:
        pass


def resolve_uploaded_report_disk_path(file_path: str) -> str:
    """
    Resolve DB file_path to an absolute path under uploads/reports (no traversal).
    """
    if not file_path or not file_path.strip():
        raise HTTPException(
            status_code=400,
            detail="Report has no file_path.",
        )
    raw = file_path.strip()
    if ".." in raw.replace("\\", "/"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file_path.",
        )

    uploads_reports = (BACKEND_ROOT / "uploads" / "reports").resolve()
    candidate = (BACKEND_ROOT / raw).resolve()

    try:
        candidate.relative_to(uploads_reports)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Report file_path is outside uploads/reports.",
        )

    return str(candidate)


def validate_stored_report_mime(mime_type: Optional[str]) -> str:
    normalized = _normalize_mime_type(mime_type)
    if normalized not in ALLOWED_REPORT_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Report MIME type is not supported for OCR. "
                "Expected PDF, PNG, or JPEG."
            ),
        )
    return normalized


def _truncate_ocr_error(message: str) -> str:
    if len(message) <= OCR_ERROR_DB_MAX_LEN:
        return message
    return message[: OCR_ERROR_DB_MAX_LEN - 3] + "..."


def _text_preview(full: str) -> str:
    if len(full) <= OCR_TEXT_PREVIEW_MAX_CHARS:
        return full
    return full[: OCR_TEXT_PREVIEW_MAX_CHARS] + "..."


# ----- Pydantic -----


class ReportCreate(BaseModel):
    patient_id: str
    file_path: str = Field(..., min_length=1)
    original_filename: Optional[str] = None
    mime_type: Optional[str] = None
    title: Optional[str] = None
    report_date: Optional[date] = None


class ReportSummary(BaseModel):
    """List rows: metadata only (OCR fields omitted until OCR is implemented)."""

    id: str
    patient_id: str
    file_path: str
    original_filename: Optional[str] = None
    mime_type: Optional[str] = None
    title: Optional[str] = None
    report_date: Optional[str] = None
    ocr_status: str
    created_at: Optional[str] = None


class ReportDetail(BaseModel):
    """Single report / create response: full row shape for API stability."""

    id: str
    patient_id: str
    file_path: str
    original_filename: Optional[str] = None
    mime_type: Optional[str] = None
    title: Optional[str] = None
    report_date: Optional[str] = None
    ocr_status: str
    ocr_text: Optional[str] = None
    ocr_error: Optional[str] = None
    created_at: Optional[str] = None


class ReportOcrResponse(BaseModel):
    """Response after running OCR on a report (includes truncated preview only)."""

    id: str
    patient_id: str
    file_path: str
    mime_type: Optional[str] = None
    ocr_status: str
    ocr_error: Optional[str] = None
    text_preview: str
    extracted_char_count: int


def _to_summary(r: Report) -> ReportSummary:
    return ReportSummary(
        id=str(r.id),
        patient_id=str(r.patient_id),
        file_path=r.file_path,
        original_filename=r.original_filename,
        mime_type=r.mime_type,
        title=r.title,
        report_date=str(r.report_date) if r.report_date else None,
        ocr_status=r.ocr_status,
        created_at=str(r.created_at) if r.created_at else None,
    )


def _to_detail(r: Report) -> ReportDetail:
    return ReportDetail(
        id=str(r.id),
        patient_id=str(r.patient_id),
        file_path=r.file_path,
        original_filename=r.original_filename,
        mime_type=r.mime_type,
        title=r.title,
        report_date=str(r.report_date) if r.report_date else None,
        ocr_status=r.ocr_status,
        ocr_text=r.ocr_text,
        ocr_error=r.ocr_error,
        created_at=str(r.created_at) if r.created_at else None,
    )


# POST create report metadata
@router.post("/", response_model=ReportDetail)
def create_report(data: ReportCreate, db: DBSession = Depends(get_db)):

    path = data.file_path.strip()
    if not path:
        raise HTTPException(400, "file_path cannot be empty")

    patient = db.query(Patient).filter(Patient.id == data.patient_id).first()

    if not patient:
        raise HTTPException(404, "Patient not found")

    report = Report(
        id=uuid.uuid4(),
        patient_id=data.patient_id,
        file_path=path,
        original_filename=data.original_filename,
        mime_type=data.mime_type,
        title=data.title,
        report_date=data.report_date,
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    return _to_detail(report)


# =========================================
# REPORT FILE UPLOAD (Day 12 Phase 1)
# =========================================


@router.post(
    "/upload",
    response_model=ReportDetail,
)
async def upload_report(
    patient_id: str = Form(...),
    file: UploadFile = File(...),
    db: DBSession = Depends(get_db),
):

    # =====================================
    # VALIDATE PATIENT
    # =====================================

    patient = db.query(Patient).filter(Patient.id == patient_id).first()

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found",
        )

    # =====================================
    # VALIDATE MIME TYPE
    # =====================================

    mime_type = validate_report_mime_type(file.content_type)

    # =====================================
    # READ BODY + VALIDATE SIZE
    # =====================================

    contents = await file.read()

    validate_report_file_size(contents)

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="Empty file.",
        )

    # =====================================
    # WRITE FILE
    # =====================================

    filename = create_safe_report_filename(file.filename)

    relative_path = f"uploads/reports/{filename}"

    absolute_path = os.path.join(UPLOAD_DIR_REPORTS, filename)

    try:
        with open(absolute_path, "wb") as out:
            out.write(contents)
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"File save failed: {exc}",
        )

    # =====================================
    # PERSIST REPORT ROW
    # =====================================

    original_name = os.path.basename(file.filename) if file.filename else None
    if original_name and len(original_name) > 255:
        original_name = original_name[:255]

    report = Report(
        id=uuid.uuid4(),
        patient_id=patient_id,
        file_path=relative_path,
        original_filename=original_name,
        mime_type=mime_type,
        title=None,
        report_date=None,
        ocr_status="pending",
    )

    try:
        db.add(report)
        db.commit()
        db.refresh(report)
    except Exception as exc:
        db.rollback()
        cleanup_report_file(absolute_path)
        raise HTTPException(
            status_code=500,
            detail=f"Database save failed: {exc}",
        )

    # =====================================
    # SUCCESS
    # =====================================

    return _to_detail(report)


# =========================================
# REPORT OCR (Day 12)
# =========================================


@router.post(
    "/{report_id}/ocr",
    response_model=ReportOcrResponse,
)
def run_report_ocr(
    report_id: str,
    db: DBSession = Depends(get_db),
):

    # =====================================
    # LOAD REPORT
    # =====================================

    report = db.query(Report).filter(Report.id == report_id).first()

    if not report:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    # =====================================
    # VALIDATE MIME (stored on row)
    # =====================================

    mime_type = validate_stored_report_mime(report.mime_type)

    # =====================================
    # RESOLVE PATH + FILE EXISTS
    # =====================================

    disk_path = resolve_uploaded_report_disk_path(report.file_path)

    if not os.path.isfile(disk_path):
        report.ocr_status = "failed"
        report.ocr_error = _truncate_ocr_error(
            "Uploaded file is missing on disk; cannot run OCR."
        )
        report.ocr_text = None
        db.commit()
        db.refresh(report)
        return ReportOcrResponse(
            id=str(report.id),
            patient_id=str(report.patient_id),
            file_path=report.file_path,
            mime_type=report.mime_type,
            ocr_status=report.ocr_status,
            ocr_error=report.ocr_error,
            text_preview="",
            extracted_char_count=0,
        )

    # =====================================
    # EXTRACT TEXT
    # =====================================

    try:
        extracted = extract_report_text(disk_path, mime_type)
    except Exception as exc:
        err = _truncate_ocr_error(str(exc) or repr(exc))
        report.ocr_status = "failed"
        report.ocr_error = err
        report.ocr_text = None
        db.commit()
        db.refresh(report)
        return ReportOcrResponse(
            id=str(report.id),
            patient_id=str(report.patient_id),
            file_path=report.file_path,
            mime_type=report.mime_type,
            ocr_status=report.ocr_status,
            ocr_error=report.ocr_error,
            text_preview="",
            extracted_char_count=0,
        )

    # =====================================
    # PERSIST SUCCESS
    # =====================================

    report.ocr_text = extracted
    report.ocr_status = "ready"
    report.ocr_error = None
    db.commit()
    db.refresh(report)

    preview = _text_preview(extracted)

    return ReportOcrResponse(
        id=str(report.id),
        patient_id=str(report.patient_id),
        file_path=report.file_path,
        mime_type=report.mime_type,
        ocr_status=report.ocr_status,
        ocr_error=None,
        text_preview=preview,
        extracted_char_count=len(extracted),
    )


# GET all reports for a patient
@router.get("/patient/{patient_id}", response_model=List[ReportSummary])
def list_reports_for_patient(
    patient_id: str,
    db: DBSession = Depends(get_db),
):

    patient = db.query(Patient).filter(Patient.id == patient_id).first()

    if not patient:
        raise HTTPException(404, "Patient not found")

    rows = (
        db.query(Report)
        .filter(Report.patient_id == patient_id)
        .order_by(Report.created_at.desc())
        .all()
    )

    return [_to_summary(r) for r in rows]


# GET single report
@router.get("/{report_id}", response_model=ReportDetail)
def get_report(report_id: str, db: DBSession = Depends(get_db)):

    r = db.query(Report).filter(Report.id == report_id).first()

    if not r:
        raise HTTPException(404, "Report not found")

    return _to_detail(r)
