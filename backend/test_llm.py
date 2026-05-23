from llm_service import generate_answer


context = """
Hemoglobin level is 8.2 g/dL.
Patient may have anemia.
WBC count is normal.
"""

question = "Does the patient show signs of anemia?"

answer = generate_answer(
    context=context,
    question=question,
)

print("\nAI RESPONSE:\n")
print(answer)