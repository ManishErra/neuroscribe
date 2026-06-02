from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from database import get_db
from models import Patient, Report
from clinical_timeline import build_timeline, get_report_sorting_date
from clinical_comparison import generate_comparison
from clinical_summary import generate_clinical_summary_data
from clinical_entities import extract_clinical_entities
from auth_utils import get_current_user

router = APIRouter(tags=["Patient Insights"], dependencies=[Depends(get_current_user)])

@router.get("/patient-insights/{patient_id}")
def get_patient_insights(patient_id: str, db: DBSession = Depends(get_db)):
    """
    Get clinical summary, findings, abnormalities, and recommendations for a patient
    based on their latest laboratory report and clinical history trends.
    """
    # 1. Verify patient exists
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )
        
    # 2. Get all reports for the patient
    reports = db.query(Report).filter(Report.patient_id == patient_id).all()
    
    # 3. Filter for ready reports and find the latest one
    ready_reports = [r for r in reports if r.ocr_status == "ready" and r.ocr_text]
    if not ready_reports:
        raise HTTPException(
            status_code=404,
            detail="No ready laboratory reports found for this patient."
        )
        
    sorted_ready = sorted(ready_reports, key=get_report_sorting_date)
    latest_report = sorted_ready[-1]
    
    # 4. Build clinical timeline and comparison metrics
    timeline_data = build_timeline(reports)
    comparison_data = generate_comparison(timeline_data)
    
    # 5. Generate clinical summary data
    summary_res = generate_clinical_summary_data(
        patient_id=patient_id,
        latest_report_text=latest_report.ocr_text,
        latest_report_date=str(latest_report.report_date) if latest_report.report_date else None,
        timeline_data=timeline_data,
        comparison_data=comparison_data
    )
    
    return summary_res


@router.get("/patient-overview/{patient_id}")
def get_patient_overview(patient_id: str, db: DBSession = Depends(get_db)):
    """
    Get a high-level patient overview for the dashboard cards, including
    clinical status, clinical flags, latest extracted labs, and last activity details.
    """
    # 1. Verify patient exists
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )
        
    # 2. Get all reports for the patient
    reports = db.query(Report).filter(Report.patient_id == patient_id).all()
    
    # 3. Filter for ready reports
    ready_reports = [r for r in reports if r.ocr_status == "ready" and r.ocr_text]
    if not ready_reports:
        return {
            "patient_id": patient_id,
            "status": "STABLE",
            "clinical_flags": [],
            "latest_labs": {},
            "last_activity": {}
        }
        
    sorted_ready = sorted(ready_reports, key=get_report_sorting_date)
    latest_report = sorted_ready[-1]
    
    # 4. Build timeline and comparison
    timeline_data = build_timeline(reports)
    comparison_data = generate_comparison(timeline_data)
    
    # 5. Run summary logic to get clinical flags & abnormalities
    summary_res = generate_clinical_summary_data(
        patient_id=patient_id,
        latest_report_text=latest_report.ocr_text,
        latest_report_date=str(latest_report.report_date) if latest_report.report_date else None,
        timeline_data=timeline_data,
        comparison_data=comparison_data
    )
    
    flags = summary_res.get("clinical_flags", [])
    abnormalities = summary_res.get("abnormalities", [])
    
    # Determine Patient Status
    # - CRITICAL: multiple abnormalities or worsening trends
    # - WARNING: single abnormality or any out-of-range flag
    # - STABLE: no abnormalities
    worsening_present = any("Worsening" in flag for flag in flags)
    
    if len(abnormalities) > 1 or worsening_present:
        status = "CRITICAL"
    elif len(abnormalities) > 0:
        status = "WARNING"
    else:
        status = "STABLE"
        
    # Latest extracted labs key-value with units
    from clinical_flags import classify_lab_result
    extracted = extract_clinical_entities(latest_report.ocr_text)
    latest_labs = {}
    target_tests = ["hemoglobin", "wbc", "rbc", "platelets", "glucose"]
    for test in target_tests:
        if test in extracted:
            val = extracted[test]
            classification = classify_lab_result(test, val)
            unit = classification.get("unit", "")
            if unit and unit.lower() not in val.lower():
                latest_labs[test] = f"{val} {unit}"
            else:
                latest_labs[test] = val
            
    # Last activity details
    r_date = get_report_sorting_date(latest_report)
    last_activity = {
        "type": "laboratory_report",
        "date": r_date.isoformat() if r_date else None,
        "id": str(latest_report.id)
    }
    
    return {
        "patient_id": patient_id,
        "status": status,
        "clinical_flags": flags,
        "latest_labs": latest_labs,
        "last_activity": last_activity
    }
