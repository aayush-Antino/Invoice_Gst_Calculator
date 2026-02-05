import os
from dotenv import load_dotenv
load_dotenv()
from google import genai
from google.genai import types

# Initialize Gemini client
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY is not set in your environment!")

client = genai.Client(api_key=api_key)
model_name = "gemini-2.5-flash"

from simple_vector_store import SimpleVectorStore

# Initialize Simple Vector Store
store = SimpleVectorStore("gst_vector_store.pkl")

# Chroma classes removed



def get_embeddings(texts: list[str]) -> list[list[float]]:
    try:
        response = client.models.embed_content(
            model="text-embedding-004",
            contents=texts,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
        )
        return [e.values for e in response.embeddings]
    except Exception as e:
        print(f"Embedding error: {e}")
        return [[0.0] * 768 for _ in range(len(texts))]

def extract_text_from_doc(file_bytes: bytes, mime_type: str):
    """
    Uses Gemini to extract text from a GST document (PDF/Image).
    """
    # Check file size (Gemini has limits)
    file_size_mb = len(file_bytes) / (1024 * 1024)
    print(f"File size: {file_size_mb:.2f} MB")
    
    # Skip very large files to prevent hanging
    if file_size_mb > 10:
        print(f"WARNING: File too large ({file_size_mb:.2f} MB). Skipping Gemini extraction.")
        print("For large PDFs, consider using a dedicated PDF parser instead.")
        return None
    
    prompt = "Extract all text from this document for RAG ingestion. If it's a GST rule or notice, ensure all details are captured."

    try:
        print("Calling Gemini API for text extraction...")
        response = client.models.generate_content(
            model=model_name,
            contents=[
                prompt,
                types.Part.from_bytes(data=file_bytes, mime_type=mime_type)
            ]
        )
        print("Gemini API call completed successfully")
        return response.text.strip()
    except Exception as e:
        print(f"Text extraction error details: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def ingest_document_text(doc_id: str, content: str):
    try:
        print(f"Starting ingestion for: {doc_id}")
        print(f"Content length: {len(content)} characters")
        
        # Limit content size to prevent large payloads (less critical for pickle but good practice)
        MAX_CONTENT_LENGTH = 50000 
        if len(content) > MAX_CONTENT_LENGTH:
            print(f"WARNING: Content too large ({len(content)} chars). Truncating.")
            content = content[:MAX_CONTENT_LENGTH]
        
        # Generate embeddings manually
        print("Generating embeddings...")
        embeddings = get_embeddings([content])
        print(f"Embeddings generated: {len(embeddings)} vectors")
        
        print("Upserting to Vector Store...")
        store.upsert(
            documents=[content],
            embeddings=embeddings,
            ids=[doc_id]
        )
        print(f"Successfully upserted {doc_id} to Vector Store")
    except Exception as e:
        print(f"Vector Store Upsert Error: {e}")
        import traceback
        traceback.print_exc()
        raise

def ingest_document_file(doc_id: str, file_bytes: bytes, mime_type: str):
    text_content = extract_text_from_doc(file_bytes, mime_type)
    if text_content:
        ingest_document_text(doc_id, text_content)
        return True
    else:
        # If extraction failed, we want to know why in main.py
        return False

def process_unstructured_query(query: str):
    # Generate embeddings manually for the query
    query_embeddings = get_embeddings([query])
    
    results = store.query(
        query_embeddings=query_embeddings,
        n_results=3
    )
    
    documents = results.get('documents', [[]])[0]
    context = "\n\n".join(documents) if documents else "No GST rules found."

    prompt = f"""
    Rule Context:
    {context}

    User Query: "{query}"

    Task: Answer strictly using the provided context. 
    If insufficient info, say so. Explain simply.
    """

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config={
                "temperature": 0.0,
                "max_output_tokens": 300
            }
        )
        return {"rag_answer": response.text.strip()}
    except Exception as e:
        return {"error": str(e)}
