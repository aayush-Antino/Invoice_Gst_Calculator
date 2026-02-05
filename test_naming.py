
import os
from google import genai
from dotenv import load_dotenv

load_dotenv("./backend/.env")
api_key = os.getenv("GEMINI_API_KEY")

if api_key:
    client = genai.Client(api_key=api_key)
    try:
        # Testing with full prefix
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents="Say 'Full name works'"
        )
        print(f"Full name response: {response.text}")
    except Exception as e:
        print(f"Full name failed: {e}")
        
    try:
        # Testing without prefix
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Say 'Short name works'"
        )
        print(f"Short name response: {response.text}")
    except Exception as e:
        print(f"Short name failed: {e}")
else:
    print("No API Key found")
