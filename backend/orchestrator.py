import os
from dotenv import load_dotenv
load_dotenv()
from google import genai

# Initialize Gemini client
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY is not set in your environment!")

client = genai.Client(api_key=api_key)
model_name = "gemini-2.5-flash"

def classify_query(query: str) -> str:
    """
    Classifies a user query into one of three categories:
    STRUCTURED_QUERY, UNSTRUCTURED_QUERY, HYBRID_QUERY
    """
    prompt = f"""
    Role: You are a query router for a GST & Invoice Analysis System.

    Categories:
    1. STRUCTURED_QUERY: SQL/data queries
    2. UNSTRUCTURED_QUERY: GST rules/compliance
    3. HYBRID_QUERY: Needs both data + rule analysis

    User Query: "{query}"

    Task: Return ONLY the category name in uppercase.
    """

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config={
                "temperature": 0.0,
                "max_output_tokens": 100
            }
        )
        classification = response.text.strip().upper()

        valid_classes = ["STRUCTURED_QUERY", "UNSTRUCTURED_QUERY", "HYBRID_QUERY"]
        for c in valid_classes:
            if c in classification:
                return c
        return "HYBRID_QUERY"
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Classification error: {e}")
        return "HYBRID_QUERY"
