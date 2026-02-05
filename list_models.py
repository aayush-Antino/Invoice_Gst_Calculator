
import os
from google import genai
from dotenv import load_dotenv

load_dotenv("./backend/.env")
api_key = os.getenv("GEMINI_API_KEY")

if api_key:
    client = genai.Client(api_key=api_key)
    print("Listing models...")
    try:
        for m in client.models.list():
            print(f"Model: {m.name}")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("No API Key found")
