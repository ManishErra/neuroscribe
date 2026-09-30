"""
Query Intent Detection & Routing Layer for Ask NeuroScribe.

Identifies the clinical intent of user questions deterministically to route
retrieval to the appropriate patient-scoped evidence sources (transcripts,
notes, reports, profile) rather than relying exclusively on keyword overlap.
"""

from __future__ import annotations

import re
from enum import Enum


class QueryIntent(str, Enum):
    LAST_CONSULTATION = "LAST_CONSULTATION"
    PATIENT_STATEMENTS = "PATIENT_STATEMENTS"
    ACTIVE_MEDICATIONS = "ACTIVE_MEDICATIONS"
    MEDICATION_HISTORY = "MEDICATION_HISTORY"
    PATIENT_OVERVIEW = "PATIENT_OVERVIEW"
    RECENT_HISTORY = "RECENT_HISTORY"
    LAB_RESULT = "LAB_RESULT"
    MEDICATION_RECOMMENDATION = "MEDICATION_RECOMMENDATION"
    GENERAL_CLINICAL = "GENERAL_CLINICAL"


def normalize_question(question: str) -> str:
    """Normalize question text for rule-based intent matching."""
    text = (question or "").strip().lower()
    # Normalize excessive whitespace
    text = re.sub(r"\s+", " ", text)
    return text


def detect_query_intent(question: str) -> QueryIntent:
    """
    Classify clinical question into a QueryIntent using deterministic pattern matching.
    Does not make external LLM calls.
    """
    q = normalize_question(question)
    if not q:
        return QueryIntent.GENERAL_CLINICAL

    # 1. MEDICATION_RECOMMENDATION (Safety guard: never recommend treatments/prescriptions)
    med_recommendation_patterns = [
        r"\b(?:what|which)\s+(?:medication|medications|medicine|medicines|drug|drugs|treatment|pill|pills|prescription|prescriptions|dose)\s+(?:should|must|ought\s+to|can)\s+(?:the\s+patient|patient|they|he|she|i|we|dr|doctor)\s+(?:take|be\s+prescribed|start|use|get|receive|prescribe)\b",
        r"\bwhat\s+should\s+(?:the\s+patient|patient|they|he|she|i|we|dr|doctor)\s+(?:prescribe|take|give|start|receive)\b",
        r"\b(?:recommend|suggest|prescribe)\s+(?:a\s+|an\s+|any\s+)?(?:medication|treatment|medicine|drug|prescription|therapy|dose)\b",
        r"\bshould\s+(?:the\s+patient|patient|they|he|she|i|we)\s+(?:take|start|be\s+prescribed|use)\s+(?:any\s+|a\s+|the\s+)?(?:medication|medicine|drug|treatment|prescription)\b",
        r"\b(?:how\s+to|how\s+should\s+we)\s+treat\s+(?:this\s+|the\s+)?(?:patient|condition|disease|symptom)\b",
    ]
    for pattern in med_recommendation_patterns:
        if re.search(pattern, q):
            return QueryIntent.MEDICATION_RECOMMENDATION

    # 2. PATIENT_STATEMENTS (Questions specifically asking what the patient said/reported/complained)
    patient_statement_patterns = [
        r"\bwhat\s+did\s+(?:the\s+)?patient\s+(?:say|mention|report|state|complain|tell|express|describe|talk\s+about|discuss)\b",
        r"\bwhat\s+(?:was|were)\s+(?:the\s+)?patient(?:'s)?\s+(?:complaint|complaints|statements|words|concerns|symptoms\s+reported|symptoms\s+mentioned)\b",
        r"\b(?:did|has)\s+(?:the\s+)?patient\s+(?:say|mention|report|state|complain|express)\b",
        r"\bwhat\s+did\s+(?:the\s+)?patient\s+(?:feel|experience|bring\s+up)\b",
        r"\bpatient\s+(?:said|mentioned|reported|complained|stated|expressed)\b",
    ]
    for pattern in patient_statement_patterns:
        if re.search(pattern, q):
            return QueryIntent.PATIENT_STATEMENTS

    # 3. LAST_CONSULTATION (Summarizing or reviewing the last/recent consultation)
    last_consultation_patterns = [
        r"\b(?:summarize|summary\s+of|tell\s+me\s+about|what\s+happened\s+(?:in|during)|details\s+of|review|recap)\s+(?:the\s+)?(?:last|latest|recent|most\s+recent|previous|prior)\s+(?:consultation|session|visit|appointment|encounter|doctor\s+visit)\b",
        r"\b(?:last|latest|recent|most\s+recent|previous)\s+(?:consultation|session|doctor\s+visit|appointment)\s+(?:summary|notes|details|overview|recap)\b",
        r"\b(?:last|latest|recent|most\s+recent|previous)\s+(?:consultation|session)\b",
    ]
    for pattern in last_consultation_patterns:
        if re.search(pattern, q):
            return QueryIntent.LAST_CONSULTATION

    # 4. ACTIVE_MEDICATIONS (Current active medications or taking medications)
    active_med_patterns = [
        r"\b(?:what\s+are\s+(?:the\s+)?)?(?:active|current|prescribed|ongoing)\s+(?:medication|medications|medicines|medicine|meds|drugs|prescriptions)\b",
        r"\bwhat\s+(?:medication|medications|medicines|medicine|meds|drugs)\s+is\s+(?:the\s+)?patient\s+(?:currently\s+)?(?:taking|on|prescribed|using)\b",
        r"\bdoes\s+(?:the\s+)?patient\s+(?:take|have|use|receive)\s+(?:any\s+)?(?:medication|medications|medicine|medicines|meds|drugs|prescriptions)\b",
        r"\bis\s+(?:the\s+)?patient\s+on\s+(?:any\s+)?(?:medication|medications|medicine|medicines|meds|drugs)\b",
        r"\bwhat\s+(?:medicines|medications|meds)\s+(?:is|are)\s+(?:the\s+)?patient\s+(?:currently\s+)?on\b",
        r"\b(?:current|active)\s+(?:meds|medications|medicines|prescriptions)\b",
    ]
    for pattern in active_med_patterns:
        if re.search(pattern, q):
            return QueryIntent.ACTIVE_MEDICATIONS

    # 5. MEDICATION_HISTORY (Past/historical medications)
    med_history_patterns = [
        r"\b(?:medication|medicine|drug|prescription)\s+history\b",
        r"\b(?:past|previous|prior|historical|all)\s+(?:medications|medicines|meds|drugs|prescriptions)\b",
        r"\bhistory\s+of\s+(?:medication|medications|medicines|meds|drugs)\b",
    ]
    for pattern in med_history_patterns:
        if re.search(pattern, q):
            return QueryIntent.MEDICATION_HISTORY

    # 6. PATIENT_OVERVIEW (Overview, profile, or details of patient)
    patient_overview_patterns = [
        r"\b(?:tell\s+me\s+about|give\s+me\s+(?:the\s+)?details\s+(?:of|about)|give\s+me\s+details\s+about|what\s+do\s+we\s+know\s+about|describe|who\s+is|overview\s+of|profile\s+of)\s+(?:this\s+|the\s+)?patient\b",
        r"\b(?:give\s+me\s+(?:the\s+)?)?patient(?:'s)?\s+(?:details|profile|overview|summary|info|information)\b",
        r"\b(?:tell\s+me\s+about|describe)\s+(?:this\s+|the\s+)?patient\b",
        r"\bwhat\s+do\s+we\s+know\s+about\s+(?:this\s+|the\s+)?patient\b",
    ]
    for pattern in patient_overview_patterns:
        if re.search(pattern, q):
            return QueryIntent.PATIENT_OVERVIEW

    # 7. RECENT_HISTORY (Recent clinical trajectory/history/events)
    recent_history_patterns = [
        r"\b(?:give\s+me\s+(?:the\s+)?)?(?:patient(?:'s)?\s+)?recent\s+(?:history|clinical\s+history|timeline|events|summary|trajectory|record|progress|developments|updates)\b",
        r"\bwhat\s+has\s+happened\s+recently\b",
        r"\brecent\s+(?:clinical\s+|medical\s+)?summary\b",
    ]
    for pattern in recent_history_patterns:
        if re.search(pattern, q):
            return QueryIntent.RECENT_HISTORY

    # 8. LAB_RESULT (Specific lab tests or vital signs)
    lab_patterns = [
        r"\b(?:hemoglobin|haemoglobin|hgb|hb|glucose|sugar|blood\s+sugar|hba1c|platelet|platelets|plt|wbc|white\s+blood|rbc|red\s+blood|creatinine|creat|sodium|potassium|bilirubin|spo2|oxygen\s+sat(?:uration)?|blood\s+pressure|bp|pulse|heart\s+rate|temperature)\b",
    ]
    for pattern in lab_patterns:
        if re.search(pattern, q):
            return QueryIntent.LAB_RESULT

    return QueryIntent.GENERAL_CLINICAL
