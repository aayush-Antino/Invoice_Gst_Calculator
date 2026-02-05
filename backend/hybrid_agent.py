import os
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import text
from database import engine
from structured_agent import process_structured_query
from unstructured_agent import process_unstructured_query
from google import genai

# Initialize Gemini client
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY is not set in your environment!")

client = genai.Client(api_key=api_key)
model_name = "gemini-2.5-flash"

def process_hybrid_query(query: str):
    # Step 1: Structured SQL (Skip NLP generation to save time)
    structured_result = process_structured_query(query, generate_nlp=False)
    sql_query = structured_result.get("sql_query")
    
    # Reuse the results already fetched by structured_agent
    rows = structured_result.get("query_result", [])
    data_context = str(rows) if rows else "No data found"

    # Step 2: Unstructured RAG
    unstructured_result = process_unstructured_query(query)
    gst_rule_context = unstructured_result.get("rag_answer", "No rules found")

    # Step 3: Final reasoning
    prompt = f"""
    You are a Hybrid Compliance Auditor.

    User Query: "{query}"

    1. Data Retrieved (SQL): "{sql_query}"
    Data Result:
    {data_context}

    2. GST Rules (RAG):
    {gst_rule_context}

    Task: Combine data + rules to answer the query.
    Output final conclusion.
    """

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config={
                "temperature": 0.0,
                "max_output_tokens": 400
            }
        )
        final_result = response.text.strip()
        return {
            "hybrid_analysis": {
                "sql_used": sql_query,
                "gst_rule_applied": gst_rule_context,
                "final_result": final_result
            }
        }
    except Exception as e:
        return {"error": str(e)}
