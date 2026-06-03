import json
import sys
from pathlib import Path

# Add backend dir to sys.path
_BACKEND_DIR = Path(__file__).resolve().parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from report_vector_store import search_similar_chunks, load_vector_store
from llm_service import generate_answer
from confidence_scoring import enrich_structured_answer

def validate_responses():
    print("======================================================================")
    print("           VALIDATING ENRICHED API RESPONSES FOR CLINICAL QA          ")
    print("======================================================================")
    
    # 1. Load vector store
    load_vector_store()
    
    # 2. Test cases to run
    test_queries = [
        {"test": "Hemoglobin", "query": "What is the Hb level?"},
        {"test": "WBC", "query": "What is the WBC count?"},
        {"test": "RBC", "query": "Show me RBC count"},
        {"test": "Platelets", "query": "What is the PLT count?"}
    ]
    
    for case in test_queries:
        test_name = case["test"]
        query = case["query"]
        
        print(f"\nQUERYING FOR: {test_name}")
        print(f"User Query: \"{query}\"")
        
        # Step A: Retrieve relevant chunks
        results = search_similar_chunks(query, top_k=5)
        if not results:
            print("[WARN] No chunks retrieved!")
            continue
            
        # Step B: Build context
        context = "\n\n".join(
            chunk.get("chunk_text", "")
            for chunk in results
        )
        
        from clinical_query_rewriter import rewrite_query
        expanded_query = rewrite_query(query)
        
        # Step C: Generate answer
        answer = generate_answer(context, expanded_query)
        
        # Step D: Parse
        parsed_answer = None
        try:
            if "\n\n" in answer.strip():
                parts = [p.strip() for p in answer.split("\n\n") if p.strip()]
                parsed_list = []
                for part in parts:
                    try:
                        parsed_list.append(json.loads(part))
                    except Exception:
                        pass
                if parsed_list:
                    parsed_answer = parsed_list
            
            if parsed_answer is None:
                parsed_answer = json.loads(answer)
        except Exception:
            parsed_answer = answer
            
        # Step E: Enrich
        if isinstance(parsed_answer, dict):
            enriched = enrich_structured_answer(parsed_answer, results)
        elif isinstance(parsed_answer, list):
            enriched = [
                enrich_structured_answer(item, results) if isinstance(item, dict) else item
                for item in parsed_answer
            ]
        else:
            enriched = parsed_answer
            
        # Step F: Print response
        print("API Response Output:")
        print(json.dumps(enriched, indent=2))
        print("-" * 70)
        
    print("======================================================================")
    print("                      VALIDATION COMPLETE!                            ")
    print("======================================================================")
    return 0

if __name__ == "__main__":
    sys.exit(validate_responses())
