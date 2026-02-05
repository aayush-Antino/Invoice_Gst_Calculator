from orchestrator import classify_query
try:
    q = "What is the tax rate for cement?"
    res = classify_query(q)
    print(f"Query: {q}")
    print(f"Classification: {res}")
    
    q2 = "List all invoices from Jan 2024"
    res2 = classify_query(q2)
    print(f"Query: {q2}")
    print(f"Classification: {res2}")
except Exception as e:
    print(f"Error: {e}")
