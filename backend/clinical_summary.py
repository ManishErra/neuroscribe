import re
from typing import Dict, Any, List, Optional
from clinical_flags import classify_lab_result, REFERENCE_RANGES, _extract_numeric_value
from clinical_entities import extract_clinical_entities

TEST_DISPLAY_NAMES = {
    "hemoglobin": "Hemoglobin",
    "wbc": "WBC",
    "platelets": "Platelets",
    "glucose": "Glucose",
    "rbc": "RBC",
}

def generate_clinical_summary_data(
    patient_id: str,
    latest_report_text: str,
    latest_report_date: Optional[str] = None,
    timeline_data: Optional[Dict[str, Any]] = None,
    comparison_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Deterministic rule-based clinical summary and recommendation engine.
    Incorporates trend-awareness and change detection from timeline and comparison data.
    """
    extracted_entities = extract_clinical_entities(latest_report_text)
    
    findings: List[str] = []
    abnormalities: List[str] = []
    recommendations: List[str] = []
    clinical_flags: List[str] = []
    
    has_abnormal = False
    
    # Process each standard lab test in a logical order
    target_tests = ["hemoglobin", "rbc", "wbc", "platelets", "glucose"]
    
    # Track classifications for summary synthesis
    normal_tests = []
    abnormal_details = []
    
    for test in target_tests:
        if test not in extracted_entities:
            continue
            
        value = extracted_entities[test]
        classification = classify_lab_result(test, value)
        status = classification.get("status", "UNKNOWN")
        unit = classification.get("unit", "")
        ref_range = classification.get("reference_range", "")
        
        # Ensure value contains unit for premium findings/abnormalities representation
        if unit and unit.lower() not in value.lower():
            value_with_unit = f"{value} {unit}"
        else:
            value_with_unit = value
            
        display_name = TEST_DISPLAY_NAMES.get(test, test)
        
        # Get trend from timeline
        trend = "INSUFFICIENT_DATA"
        if timeline_data and test in timeline_data:
            trend = timeline_data[test].get("trend", "INSUFFICIENT_DATA")
            
        # Get change classification from comparison
        change = "INSUFFICIENT_DATA"
        if comparison_data and test in comparison_data:
            change = comparison_data[test].get("change_classification", "INSUFFICIENT_DATA")
            
        # 1. Determine clinical flag description & trend suffix
        trend_suffix = ""
        flag_suffix = ""
        
        if status in ["LOW", "HIGH"]:
            if trend == "IMPROVING" or change == "IMPROVED":
                trend_suffix = " - Improving"
                flag_suffix = " - Improving"
            elif trend == "DECLINING" or change == "WORSENED":
                trend_suffix = " - Worsening"
                flag_suffix = " - Worsening"
                
        # 2. Build Finding string
        status_desc = f"{status}{trend_suffix}" if status != "NORMAL" else "Normal"
        findings.append(f"{display_name}: {value_with_unit} ({status_desc})")
        
        # 3. Handle abnormal parameters
        if status == "LOW":
            has_abnormal = True
            prefix = "Low" if test != "wbc" else "Decreased"
            ab_detail = f"{prefix} {display_name.lower()} of {value_with_unit} (Reference: {ref_range} {unit})"
            
            # Append trend context to abnormality description
            if trend_suffix:
                ab_detail += f", which is currently {trend_suffix.replace(' - ', '').lower()}"
                
            abnormalities.append(ab_detail)
            abnormal_details.append(f"{test} ({value_with_unit})")
            
            # Clinical Flag
            flag_name = f"Low {TEST_DISPLAY_NAMES[test]}"
            if flag_suffix:
                flag_name += flag_suffix
            clinical_flags.append(flag_name)
            
            # Recommendations
            if test == "hemoglobin":
                if trend == "DECLINING" or change == "WORSENED":
                    recommendations.append(
                        "Hemoglobin is low and declining. Urgently evaluate for clinical signs of active bleeding, iron deficiency, or anemia. Consider iron panel, ferritin, and hematology consultation."
                    )
                else:
                    recommendations.append(
                        "Evaluate for nutritional deficiencies (Iron, Vitamin B12, Folate). Consider a peripheral blood smear and repeat CBC in 2-4 weeks."
                    )
            elif test == "rbc":
                recommendations.append(
                    "Investigate potential causes of erythropenia. Correlate with hemoglobin and hematocrit levels."
                )
            elif test == "wbc":
                recommendations.append(
                    "Investigate possible leukopenia or bone marrow suppression. Monitor closely for fever or other signs of infection."
                )
            elif test == "platelets":
                recommendations.append(
                    "Advise patient to avoid antiplatelet medications (e.g. aspirin) and monitor for bleeding or bruising. Repeat platelet count in 1-2 weeks."
                )
            elif test == "glucose":
                recommendations.append(
                    "Investigate causes of hypoglycemia (e.g. medication dosing, prolonged fasting). Advise dietary adjustment and close glucose monitoring."
                )
                
        elif status == "HIGH":
            has_abnormal = True
            prefix = "Elevated" if test != "wbc" else "Elevated"
            ab_detail = f"{prefix} {display_name.lower()} of {value_with_unit} (Reference: {ref_range} {unit})"
            
            if trend_suffix:
                ab_detail += f", which is currently {trend_suffix.replace(' - ', '').lower()}"
                
            abnormalities.append(ab_detail)
            abnormal_details.append(f"{test} ({value_with_unit})")
            
            # Clinical Flag
            flag_name = f"Elevated {TEST_DISPLAY_NAMES[test]}"
            if flag_suffix:
                flag_name += flag_suffix
            clinical_flags.append(flag_name)
            
            # Recommendations
            if test == "hemoglobin":
                recommendations.append(
                    "Investigate potential causes of polycythemia (e.g., chronic hypoxia, smoking, erythrocytosis). Advise adequate hydration."
                )
            elif test == "rbc":
                recommendations.append(
                    "Correlate with hematocrit/hemoglobin levels to evaluate for erythrocytosis or dehydration."
                )
            elif test == "wbc":
                if trend == "DECLINING" or change == "WORSENED":
                    recommendations.append(
                        "WBC count is elevated and worsening. Urgently check for active localized/systemic infection or severe inflammatory processes. Immediate clinical correlation is advised."
                    )
                else:
                    recommendations.append(
                        "Correlate WBC count clinically with signs of infection or inflammation (fever, localizing symptoms). Repeat CBC in 7-10 days."
                    )
            elif test == "platelets":
                recommendations.append(
                    "Investigate potential reactive thrombocytosis (e.g., secondary to infection or inflammation) or primary hematological disorders."
                )
            elif test == "glucose":
                recommendations.append(
                    "Recommend checking HbA1c to screen for or monitor diabetes mellitus. Review patient's carbohydrate intake and consider endocrine evaluation."
                )
        else:
            # NORMAL
            normal_tests.append(display_name.lower())
            
    # 4. Generate Overall Clinical Flags & Recommendations for completely normal cases
    if not has_abnormal:
        clinical_flags.append("Stable CBC")
        recommendations.append(
            "All laboratory values are within reference ranges. Maintain routine clinical monitoring and standard wellness follow-ups."
        )
        
    # 5. Natural Language Summary Synthesis
    date_context = f" dated {latest_report_date}" if latest_report_date else ""
    
    if not extracted_entities:
        summary = "No laboratory parameters were extracted from the clinical report. No active clinical findings could be synthesized."
        recommendations = ["Ensure a laboratory report is uploaded and OCR processed successfully."]
    elif not has_abnormal:
        summary = f"The patient's laboratory profile{date_context} is completely within normal reference ranges. All major hematological and metabolic indicators (including hemoglobin, white blood cells, platelets, and glucose) demonstrate a stable clinical baseline."
    else:
        ab_list_str = ", ".join(abnormalities)
        ab_list_str = ab_list_str[0].lower() + ab_list_str[1:] if ab_list_str else ""
        
        # Build trend summaries if we have history
        trend_insights = []
        for test in target_tests:
            if test in extracted_entities:
                tr = timeline_data[test].get("trend", "INSUFFICIENT_DATA") if timeline_data and test in timeline_data else "INSUFFICIENT_DATA"
                ch = comparison_data[test].get("change_classification", "INSUFFICIENT_DATA") if comparison_data and test in comparison_data else "INSUFFICIENT_DATA"
                st = classify_lab_result(test, extracted_entities[test]).get("status", "NORMAL")
                
                if st in ["LOW", "HIGH"] and tr in ["IMPROVING", "DECLINING"]:
                    trend_insights.append(f"{TEST_DISPLAY_NAMES[test].lower()} is {tr.lower()}")
                    
        trend_clause = ""
        if trend_insights:
            trend_clause = f" Notably, the {' and '.join(trend_insights)}."
            
        normal_clause = ""
        if normal_tests:
            normal_clause = f" The remaining parameters, including {', '.join(normal_tests)}, are within normal limits."
            
        summary = f"The patient's laboratory profile{date_context} is clinically significant for {ab_list_str}.{trend_clause}{normal_clause}"
        
    return {
        "patient_id": patient_id,
        "summary": summary,
        "findings": findings,
        "abnormalities": abnormalities,
        "recommendations": recommendations,
        "clinical_flags": clinical_flags
    }
