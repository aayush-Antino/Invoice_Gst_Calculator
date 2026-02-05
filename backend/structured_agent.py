import os
import json
from datetime import datetime
from dotenv import load_dotenv

from sqlalchemy import text
from google import genai
from google.genai import types

from database import (
    engine,
    SessionLocal,
    Invoice,
    InvoiceItem
)

# =========================
# Environment & Gemini Setup
# =========================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY is not set!")

client = genai.Client(api_key=api_key)
model_name = "gemini-2.5-flash"

# =========================
# SAFE TYPE HELPERS
# =========================

def safe_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except:
        return default


def safe_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except:
        return default


# =========================
# Invoice Extraction
# =========================

def extract_invoice_data(file_bytes: bytes, mime_type: str):
    """
    Extract structured invoice data from PDF/image using Gemini
    """
    prompt = """
    Extract invoice information into VALID JSON.

    Seller name is usually the company/brand at the TOP of the invoice.
    Buyer name is usually mentioned after "Invoice to".

    Invoice:
    - invoice_id (string)
    - invoice_date (YYYY-MM-DD or null)

    Seller:
    - seller_name
    - seller_state
    - seller_gstin

    Buyer:
    - buyer_name
    - buyer_state
    - buyer_gstin

    Items (array):
    - description
    - quantity
    - unit_price
    - total_price
    - hsn_code
    - item_category
    - cgst_rate
    - sgst_rate
    - igst_rate
    - tax_amount

    Totals:
    - sub_total
    - cgst_total
    - sgst_total
    - igst_total
    - total_tax
    - grand_total

    Return ONLY raw JSON.
    """

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=[
                prompt,
                types.Part.from_bytes(
                    data=file_bytes,
                    mime_type=mime_type
                )
            ]
        )

        clean_text = (
            response.text
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        return json.loads(clean_text)

    except Exception as e:
        print("Invoice extraction error:", e)
        return None


# =========================
# Save Invoice to Database
# =========================

def save_invoice_to_db(data: dict):
    """
    Save extracted invoice data to DB (NULL-SAFE)
    """
    db = SessionLocal()

    try:
        # ---------- Invoice Date ----------
        invoice_date = datetime.utcnow().date()
        if data.get("invoice_date"):
            try:
                invoice_date = datetime.strptime(
                    data["invoice_date"], "%Y-%m-%d"
                ).date()
            except:
                pass

        # ---------- Invoice Header ----------
        invoice = Invoice(
            invoice_id=data.get("invoice_id"),
            invoice_date=invoice_date,

            seller_name=data.get("seller_name") or "UNKNOWN SELLER",
            seller_state=data.get("seller_state"),
            seller_gstin=data.get("seller_gstin"),

            buyer_name=data.get("buyer_name") or "UNKNOWN BUYER",
            buyer_state=data.get("buyer_state"),
            buyer_gstin=data.get("buyer_gstin"),

            sub_total=safe_float(data.get("sub_total")),
            cgst_total=safe_float(data.get("cgst_total")),
            sgst_total=safe_float(data.get("sgst_total")),
            igst_total=safe_float(data.get("igst_total")),
            total_tax=safe_float(data.get("total_tax")),
            grand_total=safe_float(data.get("grand_total")),

            payment_method=data.get("payment_method"),
            terms_conditions=data.get("terms_conditions"),
        )

        db.add(invoice)
        db.flush()  # ensure invoice_id is available

        # ---------- Line Items ----------
        for item in data.get("items", []):
            db.add(
                InvoiceItem(
                    invoice_id=invoice.invoice_id,
                    description=item.get("description") or "Item",

                    quantity=safe_int(item.get("quantity"), 1),
                    unit_price=safe_float(item.get("unit_price")),
                    total_price=safe_float(item.get("total_price")),

                    hsn_code=item.get("hsn_code"),
                    item_category=item.get("item_category"),

                    cgst_rate=safe_float(item.get("cgst_rate")),
                    sgst_rate=safe_float(item.get("sgst_rate")),
                    igst_rate=safe_float(item.get("igst_rate")),
                    tax_amount=safe_float(item.get("tax_amount")),
                )
            )

        db.commit()
        return True

    except Exception as e:
        print("DB Save error:", e)
        db.rollback()
        return False

    finally:
        db.close()


# =========================
# SQL Execution
# =========================

def execute_sql_query(sql_query: str):
    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql_query))
            return [dict(row) for row in result.mappings()]
    except Exception as e:
        return f"SQL Error: {e}"


# =========================
# Natural Language Answer
# =========================

def format_natural_language_answer(query, sql_query, results):
    prompt = f"""
    User Question: {query}
    SQL Executed: {sql_query}
    SQL Result: {results}

    Answer clearly and concisely.
    """

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        return response.text.strip()
    except:
        return "Unable to generate answer."


# =========================
# Structured Query Handler
# =========================

def process_structured_query(query: str):
    sql_result = _generate_sql_only(query)

    if "error" in sql_result:
        return sql_result

    sql_query = sql_result["sql_query"]
    results = execute_sql_query(sql_query)
    answer = format_natural_language_answer(query, sql_query, results)

    return {
        "sql_query": sql_query,
        "query_result": results,
        "structured_answer": answer
    }


# =========================
# SQL Generator
# =========================

def _generate_sql_only(query: str):
    schema = """
    Table: invoices
    - invoice_id
    - invoice_date
    - seller_name
    - buyer_name
    - sub_total
    - total_tax
    - grand_total

    Table: invoice_items
    - invoice_id
    - description
    - quantity
    - unit_price
    - total_price
    - hsn_code
    - item_category
    - tax_amount
    """

    prompt = f"""
    Convert the user question into a valid SQLite SQL query.

    Database Schema:
    {schema}

    User Question: "{query}"

    Rules:
    - Output ONLY SQL
    - No explanations
    - No markdown
    """

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config={"temperature": 0}
        )

        return {"sql_query": response.text.strip()}

    except Exception as e:
        return {"error": str(e)}
