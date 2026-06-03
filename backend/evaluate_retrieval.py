import json
import sys
from pathlib import Path

# Add the backend directory to sys.path so we can import modules when running directly
_BACKEND_DIR = Path(__file__).resolve().parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from report_vector_store import search_similar_chunks, load_vector_store
from clinical_query_rewriter import rewrite_query

def run_retrieval_evaluation():
    print("======================================================================")
    print("      NEUROSCRIBE CLINICAL RETRIEVAL QUALITY & EVALUATION SUITE       ")
    print("======================================================================")
    
    # 1. Load evaluation cases
    cases_path = _BACKEND_DIR / "evaluation_cases.json"
    if not cases_path.is_file():
        print(f"Error: evaluation_cases.json not found at {cases_path}")
        return 1
        
    with open(cases_path, "r", encoding="utf-8") as f:
        cases = json.load(f)
        
    # 2. Ensure vector store is loaded
    load_vector_store()
    
    total_cases = len(cases)
    top_1_hits = 0
    top_5_hits = 0
    passed_cases = 0
    failed_cases = 0
    
    results_report = []
    
    for i, case in enumerate(cases, start=1):
        name = case["name"]
        query = case["query"]
        expected_entity = case.get("expected_entity", "")
        expected_value = case.get("expected_value", "")
        
        rewritten = rewrite_query(query)
        
        # Run retrieval for top 5 chunks
        results = search_similar_chunks(query, top_k=5)
        
        rank_found = None
        top_1_match = False
        top_5_match = False
        
        # Look for matching chunks in retrieved results
        for rank, chunk in enumerate(results, start=1):
            text = chunk.get("chunk_text", "").lower()
            
            # Check if chunk contains expected_entity or expected_value
            entity_match = expected_entity.lower() in text if expected_entity else False
            value_match = expected_value.lower() in text if expected_value else False
            
            if entity_match or value_match:
                if rank_found is None:
                    rank_found = rank
                if rank == 1:
                    top_1_match = True
                top_5_match = True
                
        # Update metrics
        if top_1_match:
            top_1_hits += 1
        if top_5_match:
            top_5_hits += 1
            passed_cases += 1
            status = "PASS"
        else:
            failed_cases += 1
            status = "FAIL"
            
        # Top-1 retrieved chunk info
        top_chunk_index = "N/A"
        top_chunk_score = 0.0
        top_chunk_preview = "N/A"
        
        if results:
            top_chunk = results[0]
            top_chunk_index = top_chunk.get("chunk_index", "N/A")
            top_chunk_score = top_chunk.get("similarity_score", 0.0)
            top_chunk_preview = top_chunk.get("chunk_text", "")[:120].replace("\n", " ") + "..."
            
        case_report = {
            "name": name,
            "query": query,
            "rewritten": rewritten,
            "top_chunk_index": top_chunk_index,
            "top_chunk_score": top_chunk_score,
            "top_chunk_preview": top_chunk_preview,
            "rank_found": rank_found if rank_found is not None else "Not Found",
            "top_1_accuracy": "100%" if top_1_match else "0%",
            "top_5_accuracy": "100%" if top_5_match else "0%",
            "status": status
        }
        results_report.append(case_report)
        
        # Print details for each case
        print(f"\nCASE {i}: {name}")
        print(f"  Query          : \"{query}\"")
        print(f"  Rewritten Query: \"{rewritten}\"")
        print(f"  Top Retrieved  : Chunk #{top_chunk_index} (Score: {top_chunk_score:.4f})")
        print(f"  Preview        : \"{top_chunk_preview}\"")
        print(f"  Rank Found     : {case_report['rank_found']}")
        print(f"  Top 1 Accuracy : {case_report['top_1_accuracy']}")
        print(f"  Top 5 Accuracy : {case_report['top_5_accuracy']}")
        print(f"  Status         : {status}")
        print("-" * 70)
        
    # Calculate percentages
    top_1_accuracy_pct = (top_1_hits / total_cases) * 100 if total_cases > 0 else 0.0
    top_5_accuracy_pct = (top_5_hits / total_cases) * 100 if total_cases > 0 else 0.0
    retrieval_accuracy_pct = top_5_accuracy_pct
    
    print("\n" + "=" * 70)
    print("                     EVALUATION SUMMARY METRICS                       ")
    print("=" * 70)
    print(f"  Total Test Cases           : {total_cases}")
    print(f"  Passed (Found in Top 5)    : {passed_cases}")
    print(f"  Failed (Not in Top 5)      : {failed_cases}")
    print(f"  Top 1 Accuracy             : {top_1_accuracy_pct:.2f}%")
    print(f"  Top 5 Accuracy (Overall)   : {top_5_accuracy_pct:.2f}%")
    print(f"  Retrieval Accuracy Score   : {retrieval_accuracy_pct:.2f}%")
    print("=" * 70)
    
    # Save a JSON file with report results
    report_out_path = _BACKEND_DIR / "retrieval_evaluation_report.json"
    report_data = {
        "summary": {
            "total_cases": total_cases,
            "passed": passed_cases,
            "failed": failed_cases,
            "top_1_accuracy_pct": round(top_1_accuracy_pct, 2),
            "top_5_accuracy_pct": round(top_5_accuracy_pct, 2),
            "retrieval_accuracy_pct": round(retrieval_accuracy_pct, 2)
        },
        "cases": results_report
    }
    with open(report_out_path, "w", encoding="utf-8") as out_f:
        json.dump(report_data, out_f, indent=2)
        
    print(f"Saved detailed evaluation report to {report_out_path.name}")
    print("=" * 70 + "\n")
    return 0

if __name__ == "__main__":
    sys.exit(run_retrieval_evaluation())
