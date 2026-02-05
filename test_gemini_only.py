
import os
from google import genai
from dotenv import load_dotenv

# Load from specific path
load_dotenv("./backend/.env")

api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key found: {'Yes' if api_key else 'No'}")

if api_key:
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents="Say 'API works'"
        )
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("API Key is missing!")
