from clinical_flags import REFERENCE_RANGES

# Configurable clinical significance thresholds
CLINICAL_THRESHOLDS = {
    "hemoglobin": 0.5,
    "glucose": 5.0,
    "wbc": 500.0,
    "platelets": 10000.0,
    "rbc": 0.1,  # Medically significant change for RBC count is typical 0.1 million/cmm
}

def calculate_change_metrics(test_name: str, history: list[dict]) -> dict:
    """
    Calculate comparative laboratory changes between the two most recent reports.
    Uses clinical significance thresholds and reference-range distance mapping.
    """
    test_key = test_name.lower()
    
    if len(history) < 2:
        return {
            "previous_value": history[-1]["value"] if len(history) == 1 else None,
            "current_value": history[-1]["value"] if len(history) == 1 else None,
            "absolute_change": None,
            "percentage_change": None,
            "change_classification": "INSUFFICIENT_DATA"
        }
        
    previous = history[-2]
    current = history[-1]
    
    previous_val = previous["value"]
    current_val = current["value"]
    previous_num = previous["numeric_value"]
    current_num = current["numeric_value"]
    
    if previous_num is None or current_num is None:
        return {
            "previous_value": previous_val,
            "current_value": current_val,
            "absolute_change": None,
            "percentage_change": None,
            "change_classification": "INSUFFICIENT_DATA"
        }
        
    # 1. Calculate raw numeric changes
    abs_change = current_num - previous_num
    pct_change = (abs_change / previous_num) * 100.0 if previous_num != 0 else 0.0
    
    # Round to 2 decimal places for clean representation
    abs_change = round(abs_change, 2)
    pct_change = round(pct_change, 2)
    
    # 2. Check Clinical Significance Threshold
    threshold = CLINICAL_THRESHOLDS.get(test_key, 0.0)
    if abs(abs_change) < threshold:
        return {
            "previous_value": previous_val,
            "current_value": current_val,
            "absolute_change": abs_change,
            "percentage_change": pct_change,
            "change_classification": "STABLE"
        }
        
    # 3. Reference-Range Distance Analysis
    if test_key not in REFERENCE_RANGES:
        # Fallback to naive increase/decrease if no reference range exists
        if abs_change > 0:
            classification = "IMPROVED"
        elif abs_change < 0:
            classification = "WORSENED"
        else:
            classification = "STABLE"
    else:
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
                
        prev_dist = get_distance(previous_num)
        curr_dist = get_distance(current_num)
        
        epsilon = 0.0001
        
        if curr_dist < prev_dist - epsilon:
            classification = "IMPROVED"
        elif curr_dist > prev_dist + epsilon:
            classification = "WORSENED"
        else:
            classification = "STABLE"
            
    return {
        "previous_value": previous_val,
        "current_value": current_val,
        "absolute_change": abs_change,
        "percentage_change": pct_change,
        "change_classification": classification
    }

def generate_comparison(timeline: dict) -> dict:
    """
    Generate comparative analysis across all target laboratory tests.
    """
    comparison = {}
    for test, data in timeline.items():
        history = data.get("history", [])
        comparison[test] = calculate_change_metrics(test, history)
    return comparison
