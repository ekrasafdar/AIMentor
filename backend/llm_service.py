import os
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

# Load .env from the project root (one level up from backend)
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

API_KEY = os.getenv("GEMINI_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY)
    try:
        # Use gemini-flash-latest as it was verified to work
        model = genai.GenerativeModel('gemini-flash-latest')
    except Exception:
        # Fallback
        model = genai.GenerativeModel('gemini-flash-latest')
else:
    model = None

async def get_llm_response(history_text: str, user_input: str, system_instruction: str = "") -> str:
    """
    Sends the conversation context to the LLM and gets a response.
    """
    if not model:
        return "Error: GEMINI_API_KEY not found in .env file. Please set it up to enable the AI."

    # Construct the prompt
    prompt = f"{system_instruction}\n\nConversation History:\n{history_text}\n\nUser: {user_input}\nAssistant:"
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error communicating with AI: {str(e)}"
