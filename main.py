from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import json
from datetime import datetime
from typing import Dict, List
from google.cloud import dialogflow
import os
from pathlib import Path
from dotenv import load_dotenv
import aiohttp
import html
import logging
from utils.logger_config import log_api_request, log_api_response, log_external_api_call

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize chat history
chat_history: List[Dict] = []

# Dialogflow settings
CREDENTIALS_PATH = str(Path(__file__).parent / os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "dialogflow_credentials.json"))
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_PATH
DIALOGFLOW_PROJECT_ID = os.getenv("DIALOGFLOW_PROJECT_ID")
DIALOGFLOW_LANGUAGE_CODE = "en"
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))

# OpenRouter settings
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

logger.info(f"Using credentials file: {CREDENTIALS_PATH}")
logger.info(f"Project ID: {DIALOGFLOW_PROJECT_ID}")
logger.info(f"File exists: {os.path.exists(CREDENTIALS_PATH)}")
logger.info(f"OpenRouter Model: {OPENROUTER_MODEL}")

async def get_openrouter_response(text: str) -> dict:
    """Get response from OpenRouter API"""
    if not OPENROUTER_API_KEY:
        error_msg = "OpenRouter API key not found in environment variables"
        log_external_api_call("OpenRouter", error=error_msg)
        raise ValueError(error_msg)

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": text}]
    }
    
    try:
        log_external_api_call("OpenRouter", request_data={"text": text})
        async with aiohttp.ClientSession() as session:
            async with session.post(OPENROUTER_API_URL, headers=headers, json=payload) as response:
                result = await response.json()
                
                if response.status != 200:
                    error_msg = f"OpenRouter API error: {result.get('error', 'Unknown error')}"
                    log_external_api_call("OpenRouter", error=error_msg)
                    raise ValueError(error_msg)
                
                log_external_api_call("OpenRouter", response_data=result)
                return result
    except Exception as e:
        error_msg = f"Error calling OpenRouter API: {str(e)}"
        log_external_api_call("OpenRouter", error=error_msg)
        raise

async def detect_intent(text: str) -> str:
    """Detect intent using Dialogflow with fallback to OpenRouter"""
    try:
        log_external_api_call("Dialogflow", request_data={"text": text})
        session_client = dialogflow.SessionsClient()
        session = session_client.session_path(DIALOGFLOW_PROJECT_ID, "unique-session-id")
        
        text_input = dialogflow.TextInput(text=text, language_code=DIALOGFLOW_LANGUAGE_CODE)
        query_input = dialogflow.QueryInput(text=text_input)
        
        response = session_client.detect_intent(request={"session": session, "query_input": query_input})
        
        confidence = response.query_result.intent_detection_confidence
        log_external_api_call("Dialogflow", response_data={
            "confidence": confidence,
            "intent": response.query_result.intent.display_name,
            "response": response.query_result.fulfillment_text
        })
        
        if confidence >= CONFIDENCE_THRESHOLD:
            return response.query_result.fulfillment_text
        
        # Fallback to OpenRouter for low confidence responses
        openrouter_response = await get_openrouter_response(text)
        return openrouter_response['choices'][0]['message']['content']
        
    except Exception as e:
        error_msg = f"Error in intent detection: {str(e)}"
        log_external_api_call("Dialogflow", error=error_msg)
        raise

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Render the main page"""
    try:
        log_api_request("/", "GET")
        response = templates.TemplateResponse(
            "index.html",
            {"request": request, "chat_history": chat_history}
        )
        log_api_response("/", response.status_code)
        return response
    except Exception as e:
        error_msg = f"Error rendering main page: {str(e)}"
        log_api_response("/", 500, error=error_msg)
        raise

@app.post("/process_input")
async def process_input(message: str = Form(...)):
    """Process user input and return response"""
    try:
        log_api_request("/process_input", "POST", {"message": message})
        
        # Process the message
        response_text = await detect_intent(message)
        
        # Update chat history
        chat_entry = {
            "user_input": html.escape(message),
            "bot_response": response_text,
            "timestamp": datetime.now().isoformat()
        }
        chat_history.append(chat_entry)
        
        response_data = {"response": response_text}
        log_api_response("/process_input", 200, response_data)
        return JSONResponse(response_data)
        
    except Exception as e:
        error_msg = f"Error processing input: {str(e)}"
        log_api_response("/process_input", 500, error=error_msg)
        return JSONResponse(
            {"error": str(e)},
            status_code=500
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
