# Technical Documentation: Multi-Agent Invoice & GST System

This document provides a comprehensive overview of the Multi-Agent System for Invoice Analysis and GST Compliance.

## 1. Project Overview
The system is designed to handle both structured invoice data (SQL) and unstructured GST regulations (RAG). It uses an AI Orchestrator to route user queries to the appropriate agent.

---

## 2. Directory Structure & File Map

### Root Directory
- `start_app.bat`: Startup script for Windows. Initializes the environment and starts both backend and frontend.
- `PROJECT_DOCUMENTATION.md`: This file.
- `venv/`: Python virtual environment.

### Backend (`/backend`)
- `main.py`: **Entry Point**. FastAPI application defining API routes (upload, ingest, query).
- `database.py`: **Database Connection**. Sets up SQLAlchemy and defines the `Invoice` model for SQLite.
- `invoices.db`: **SQL Storage**. The SQLite database file containing structured invoice data.
- `chroma_db/`: **Vector Storage**. Folder containing the ChromaDB persistent storage for RAG.
- `.env`: Contains sensitive configuration like `GEMINI_API_KEY`.
- `orchestrator.py`: Uses Gemini to classify user queries into `STRUCTURED`, `UNSTRUCTURED`, or `HYBRID`.
- `structured_agent.py`: Handles SQL generation, execution, and invoice data extraction.
- `unstructured_agent.py`: Handles PDF text extraction and ChromaDB queries for RAG.
- `hybrid_agent.py`: Manages complex queries requiring both SQL data and RAG context.
- `seed_data.py`: Script to populate the SQLite database with initial sample data.
- `requirements.txt`: Python dependencies.

### Frontend (`/frontend`)
- `src/App.jsx`: **Frontend Entry Point**. Main React component for the chat interface and file uploads.
- `src/index.css`: Global styles.
- `package.json`: Node.js dependencies and scripts.
- `vite.config.js`: Vite configuration for the development server.

---

## 3. Core Workflows

### 3.1 Uploading & Data Processing

#### **A. Invoice Upload (`/upload-invoice`)**
1. **Upload**: User uploads an image or PDF invoice via the UI.
2. **Extraction**: `structured_agent.py` sends the file to Gemini with a prompt to extract fields (ID, Date, GSTIN, Totals, etc.) as JSON.
3. **Storage**: The extracted JSON is validated and saved/merged into `invoices.db` using SQLAlchemy.

#### **B. GST Document Upload (`/upload-gst-doc`)**
1. **Upload**: User uploads a GST rule or notice (PDF).
2. **Extraction**: `unstructured_agent.py` uses Gemini to extract all text from the document.
3. **Ingestion**: The text is chunked and stored in the `gst_documents` collection within the **ChromaDB** vector database (`/backend/chroma_db`).

### 3.2 Query Processing Flow (`/query`)
1. **Classification**: The `orchestrator` determines the intent.
2. **Routing**:
   - **STRUCTURED**: `structured_agent` generates a SQL query, executes it on `invoices.db`, and formats the result.
   - **UNSTRUCTURED**: `unstructured_agent` retrieves relevant chunks from ChromaDB and answers using Gemini.
   - **HYBRID**: `hybrid_agent` performs both steps and synthesizes a combined answer.

---

## 4. Technical Details

- **Backend Entry**: `uvicorn main:app` in the `backend/` directory.
- **Frontend Entry**: `npm run dev` in the `frontend/` directory.
- **Database Connection**: 
  - **SQL**: `sqlite:///./invoices.db` (initialized in `database.py`).
  - **Vector**: Persistent ChromaDB client at `./chroma_db` (initialized in `unstructured_agent.py`).
- **AI Models**: Primarily uses `gemini-2.5-flash` for extraction, classification, and reasoning.
