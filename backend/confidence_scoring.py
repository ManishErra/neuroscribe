import re

def calculate_confidence(
    retrieval_score: float,
    is_deterministic: bool,
    has_direct_match: bool,
    rank: int,
) -> tuple[float, list[str], dict]:
    """
    Calculate confidence score (0.0 to 1.0), generate explanation reasons, 
    and provide the component breakdown.
    """
    reasons = []
    
    # 1. Extraction Method
    if is_deterministic:
        base_certainty = 0.95
        reasons.append("Deterministic regex extraction")
    else:
        base_certainty = 0.75
        reasons.append("LLM fallback extraction")
        
    # 2. Retrieval Score
    if retrieval_score >= 0.80:
        reasons.append("High similarity score")
    elif retrieval_score >= 0.50:
        reasons.append("Medium similarity score")
    else:
        reasons.append("Low similarity score")
        
    # 3. Retrieval Rank
    if rank == 1:
        reasons.append("Top 1 retrieval result")
    elif rank <= 3:
        reasons.append(f"Top {rank} retrieval result")
    else:
        reasons.append(f"Top 5 retrieval result")
        
    # 4. Direct Match
    if has_direct_match:
        reasons.append("Direct entity name match")
        
    # Component calculations with explicit rounding to 2 decimal places
    retrieval_component = round(retrieval_score * 0.40, 2)
    extraction_component = round(base_certainty * 0.50, 2)
    direct_match_component = 0.10 if has_direct_match else 0.00
    
    score = round(retrieval_component + extraction_component + direct_match_component, 2)
    final_score = min(max(score, 0.0), 1.0)
    
    breakdown = {
        "retrieval_component": retrieval_component,
        "extraction_component": extraction_component,
        "direct_match_component": direct_match_component
    }
    
    return final_score, reasons, breakdown

def confidence_label(confidence: float) -> str:
    """
    Return label based on rounded confidence score to prevent floating point issues.
    """
    rounded = round(confidence, 2)
    if rounded >= 0.85:
        return "HIGH"
    elif rounded >= 0.60:
        return "MEDIUM"
    else:
        return "LOW"

def enrich_structured_answer(answer_dict: dict, results: list) -> dict:
    """
    Enrich a single structured answer dictionary with confidence scoring, 
    source attribution, and confidence breakdowns.
    """
    if not isinstance(answer_dict, dict):
        return answer_dict
        
    test = answer_dict.get("test", "")
    value = answer_dict.get("value", "")
    
    # Clean value for search
    val_clean = re.sub(r"[^\d.]", "", value) if value else ""
    
    matched_rank = None
    matched_chunk = None
    has_direct_match = False
    
    # 1. Find the source chunk in results
    if results:
        # Step 1.1: Match both test name and value
        for rank, chunk in enumerate(results, start=1):
            text = chunk.get("chunk_text", "").lower()
            if val_clean and val_clean in text:
                if test.lower() in text:
                    matched_rank = rank
                    matched_chunk = chunk
                    has_direct_match = True
                    break
                    
        # Step 1.2: Fallback to matching value only
        if matched_chunk is None and val_clean:
            for rank, chunk in enumerate(results, start=1):
                text = chunk.get("chunk_text", "").lower()
                if val_clean in text:
                    matched_rank = rank
                    matched_chunk = chunk
                    break
                    
        # Step 1.3: Fallback to matching test name only
        if matched_chunk is None and test:
            for rank, chunk in enumerate(results, start=1):
                text = chunk.get("chunk_text", "").lower()
                if test.lower() in text:
                    matched_rank = rank
                    matched_chunk = chunk
                    has_direct_match = True
                    break
                    
        # Step 1.4: Default to top result if still not matched
        if matched_chunk is None:
            matched_rank = 1
            matched_chunk = results[0]
            
    # Calculate score & reasons
    retrieval_score = 0.0
    rank = 1
    source_preview = "N/A"
    source_report_id = None
    
    if matched_chunk:
        retrieval_score = round(matched_chunk.get("similarity_score", 0.0), 4)
        rank = matched_rank or 1
        source_preview = matched_chunk.get("chunk_text", "")[:120].replace("\n", " ") + "..."
        source_report_id = matched_chunk.get("report_id")
        
        # Check direct entity name mention in the chunk
        if test.lower() in matched_chunk.get("chunk_text", "").lower():
            has_direct_match = True

    # Determine if extraction was deterministic
    is_deterministic = True
    
    confidence, reasons, breakdown = calculate_confidence(
        retrieval_score=retrieval_score,
        is_deterministic=is_deterministic,
        has_direct_match=has_direct_match,
        rank=rank
    )
    
    # Inject enhanced fields
    enriched = answer_dict.copy()
    enriched["confidence"] = confidence
    enriched["confidence_label"] = confidence_label(confidence)
    enriched["confidence_reason"] = reasons
    enriched["confidence_breakdown"] = breakdown
    enriched["retrieval_score"] = retrieval_score
    enriched["source_chunk_rank"] = rank
    enriched["source_preview"] = source_preview
    
    if source_report_id:
        enriched["source_report_id"] = source_report_id
        
    return enriched
