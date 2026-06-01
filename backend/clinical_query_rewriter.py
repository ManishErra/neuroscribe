import re

def rewrite_query(query: str) -> str:
    """
    Expand user clinical queries with common synonyms and abbreviations.
    
    Rules:
    - Hb ↔ Hemoglobin ↔ HGB (Output: 'hemoglobin hgb blood hemoglobin')
    - WBC ↔ White Blood Cell (Output: 'white blood cell wbc white blood count')
    - RBC ↔ Red Blood Cell (Output: 'red blood cell rbc red blood count')
    - PLT ↔ Platelet (Output: 'platelet platelets plt platelet count')
    - Sugar ↔ Glucose (Output: 'glucose sugar blood glucose')
    - Creatinine ↔ Creat (Output: 'creatinine creat')
    """
    if not query or not query.strip():
        return ""
    
    lower_query = query.lower()
    expansions = []
    
    # 1. Hb / Hemoglobin / HGB
    if re.search(r"\b(hb|hemoglobin|hgb)\b", lower_query):
        expansions.append("hemoglobin hgb blood hemoglobin")
        
    # 2. WBC / White Blood Cell
    if re.search(r"\b(wbc|white\s+blood\s+cell(s)?|white\s+blood\s+count)\b", lower_query):
        expansions.append("white blood cell wbc white blood count")
        
    # 3. RBC / Red Blood Cell
    if re.search(r"\b(rbc|red\s+blood\s+cell(s)?|red\s+blood\s+count)\b", lower_query):
        expansions.append("red blood cell rbc red blood count")
        
    # 4. PLT / Platelet
    if re.search(r"\b(plt|platelet(s)?|platelet\s+count)\b", lower_query):
        expansions.append("platelet platelets plt platelet count")
        
    # 5. Sugar / Glucose
    if re.search(r"\b(sugar|glucose|blood\s+glucose)\b", lower_query):
        expansions.append("glucose sugar blood glucose")
        
    # 6. Creatinine / Creat
    if re.search(r"\b(creatinine|creat)\b", lower_query):
        expansions.append("creatinine creat")
        
    if expansions:
        expanded_str = " ".join(expansions)
        # Ensure we construct the output by appending with a space to the original query
        return f"{query} {expanded_str}"
        
    return query
