import re
from datetime import date, datetime
from clinical_entities import extract_clinical_entities
from clinical_flags import classify_lab_result, _extract_numeric_value, REFERENCE_RANGES

def detect_trend(test_name: str, values: list[float]) -> str:
    """
    Determine clinical trend using medical reference ranges:
    - If latest value is closer to normal range -> IMPROVING
    - If latest value is further from normal range -> DECLINING
    - If essentially unchanged -> STABLE
    - If insufficient history -> INSUFFICIENT_DATA
    """
    if len(values) < 2:
        return "INSUFFICIENT_DATA"
        
    test_key = test_name.lower()
    if test_key not in REFERENCE_RANGES:
        # Fallback to simple numeric trend if test has no reference range
        previous = values[-2]
        latest = values[-1]
        epsilon = 0.0001
        if latest > previous + epsilon:
            return "IMPROVING"
        elif latest < previous - epsilon:
            return "DECLINING"
        else:
            return "STABLE"
            
    config = REFERENCE_RANGES[test_key]
    low = config["low"]
    high = config["high"]
    
    def get_distance(val: float) -> float:
        if val < low:
            return float(low - val)
        elif val > high:
            return float(val - high)
        else:
            return 0.0
            
    previous_dist = get_distance(values[-2])
    latest_dist = get_distance(values[-1])
    
    epsilon = 0.0001
    
    if latest_dist < previous_dist - epsilon:
        return "IMPROVING"
    elif latest_dist > previous_dist + epsilon:
        return "DECLINING"
    else:
        return "STABLE"

def get_report_sorting_date(report) -> date:
    """
    Helper to extract the best sorting date from a report model or dictionary, 
    safeguarding against mixed datetime/date comparisons in Python.
    """
    r_date = report.report_date if hasattr(report, "report_date") else report.get("report_date")
    c_at = report.created_at if hasattr(report, "created_at") else report.get("created_at")
    
    if r_date:
        if isinstance(r_date, datetime):
            return r_date.date()
        elif isinstance(r_date, date):
            return r_date
        # Parse if string
        try:
            return date.fromisoformat(str(r_date)[:10])
        except ValueError:
            pass
            
    if c_at:
        if isinstance(c_at, datetime):
            return c_at.date()
        elif isinstance(c_at, date):
            return c_at
        # Parse if string
        try:
            return date.fromisoformat(str(c_at)[:10])
        except ValueError:
            pass
            
    return date.min

def build_timeline(reports: list) -> dict:
    """
    Build chronological laboratory histories and calculate clinical trends.
    """
    # Sort reports chronologically by date
    sorted_reports = sorted(reports, key=get_report_sorting_date)
    
    target_tests = ["hemoglobin", "wbc", "rbc", "platelets", "glucose"]
    timeline = {}
    
    # Initialize structures
    for test in target_tests:
        timeline[test] = {
            "report_count": 0,
            "latest_value": None,
            "latest_date": None,
            "trend": "INSUFFICIENT_DATA",
            "history": []
        }
        
    for report in sorted_reports:
        # Load properties depending on database model or dict
        r_id = report.id if hasattr(report, "id") else report.get("id")
        ocr_text = report.ocr_text if hasattr(report, "ocr_text") else report.get("ocr_text")
        ocr_status = report.ocr_status if hasattr(report, "ocr_status") else report.get("ocr_status")
        
        # Skip if report has no OCR text or is not ready
        if not ocr_text or ocr_status != "ready":
            continue
            
        r_date = get_report_sorting_date(report)
        date_str = r_date.isoformat() if r_date != date.min else None
        
        # Extract clinical entities
        extracted = extract_clinical_entities(ocr_text)
        
        for test in target_tests:
            if test in extracted:
                raw_val = extracted[test]
                num_val = _extract_numeric_value(raw_val)
                
                # Classify status using existing flags
                classification = classify_lab_result(test, raw_val)
                
                timeline[test]["history"].append({
                    "report_id": str(r_id),
                    "report_date": date_str,
                    "value": raw_val,
                    "numeric_value": num_val,
                    "unit": classification.get("unit", ""),
                    "status": classification.get("status", "UNKNOWN")
                })
                
    # Calculate trends and populate latest summaries
    for test in target_tests:
        history = timeline[test]["history"]
        timeline[test]["report_count"] = len(history)
        if history:
            timeline[test]["latest_value"] = history[-1]["value"]
            timeline[test]["latest_date"] = history[-1]["report_date"]
            
            # Extract numeric floats (filtering out None values)
            numeric_values = [
                h["numeric_value"]
                for h in history
                if h["numeric_value"] is not None
            ]
            timeline[test]["trend"] = detect_trend(test, numeric_values)
            
    return timeline
