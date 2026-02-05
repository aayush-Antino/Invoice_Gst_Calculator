from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from dotenv import load_dotenv
import os

# Load env vars first
load_dotenv()

# Agents
from orchestrator import classify_query
from structured_agent import process_structured_query, extract_invoice_data, save_invoice_to_db
from unstructured_agent import process_unstructured_query, ingest_document_text, ingest_document_file
from hybrid_agent import process_hybrid_query
from database import init_db
from gst_watchdog import start_watchdog_background

app = FastAPI(title="Invoice & GST Compliance System")

@app.on_event("startup")
def startup_event():
    init_db()
    start_watchdog_background()

class QueryRequest(BaseModel):
    query: str

class IngestRequest(BaseModel):
    doc_id: str
    content: str

@app.get("/")
def read_root():
    return {"status": "System Operational"}

@app.post("/ingest")
def ingest_doc(request: IngestRequest):
    try:
        ingest_document_text(request.doc_id, request.content)
        return {"status": "success", "message": f"Document {request.doc_id} ingested."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-invoice")
async def upload_invoice(file: UploadFile = File(...)):
    try:
        content = await file.read()
        extracted_data = extract_invoice_data(content, file.content_type)
        if extracted_data:
            success = save_invoice_to_db(extracted_data)
            if success:
                return {"status": "success", "data": extracted_data}
            else:
                raise HTTPException(status_code=500, detail="Failed to save to database")
        else:
            raise HTTPException(status_code=400, detail="Failed to extract data from invoice")
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")



@app.post("/query")
def process_query(request: QueryRequest):
    query = request.query
    
    # 1. Orchestrator
    query_type = classify_query(query)
    
    response = {
        "query_type": query_type,
        "reasoning": "Classified by AI Orchestrator",
        "sql_query": None,
        "rag_answer": None,
        "hybrid_analysis": None
    }
    
    # 2. Routing
    if query_type == "STRUCTURED_QUERY":
        result = process_structured_query(query)
        response.update(result)
        
    elif query_type == "UNSTRUCTURED_QUERY":
        result = process_unstructured_query(query)
        response.update(result)
        
    else: # HYBRID_QUERY
        result = process_hybrid_query(query)
        response.update(result)
        
    return response

