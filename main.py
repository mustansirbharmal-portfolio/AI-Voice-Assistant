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
        logger.error("OpenRouter API key not found in environment variables")
        return {
            "response": "OpenRouter API key not configured.",
            "source": "error"
        }

    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "http://localhost:8000",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": "You are a helpful AI assistant. Provide clear, concise, and accurate responses."},
                {"role": "user", "content": text}
            ]
        }

        logger.info(f"Sending request to OpenRouter with model: {OPENROUTER_MODEL}")
        async with aiohttp.ClientSession() as session:
            async with session.post(OPENROUTER_API_URL, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("Successfully received response from OpenRouter")
                    return {
                        "response": data["choices"][0]["message"]["content"],
                        "model": data["model"],
                        "source": "openrouter"
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"OpenRouter API error status {response.status}: {error_text}")
                    return {
                        "response": "I apologize, but I'm having trouble connecting to my knowledge base right now.",
                        "source": "error"
                    }
    except Exception as e:
        logger.error(f"OpenRouter API error: {e}")
        return {
            "response": "I apologize, but I'm having trouble processing your request right now.",
            "source": "error"
        }

async def detect_intent(text: str) -> dict:
    """Detect intent using Dialogflow with fallback to OpenRouter"""
    try:
        session_client = dialogflow.SessionsClient()
        session = session_client.session_path(DIALOGFLOW_PROJECT_ID, "unique-session-id")
        
        text_input = dialogflow.TextInput(text=text, language_code=DIALOGFLOW_LANGUAGE_CODE)
        query_input = dialogflow.QueryInput(text=text_input)

        try:
            logger.info("Sending request to Dialogflow")
            response = session_client.detect_intent(
                request={"session": session, "query_input": query_input}
            )
            
            confidence = response.query_result.intent_detection_confidence
            logger.info(f"Dialogflow confidence: {confidence}")

            if confidence >= CONFIDENCE_THRESHOLD:
                logger.info(f"Using Dialogflow response with intent: {response.query_result.intent.display_name}")
                return {
                    "intent": response.query_result.intent.display_name,
                    "response": response.query_result.fulfillment_text,
                    "confidence": confidence,
                    "source": "dialogflow"
                }
            
            logger.info("Confidence below threshold, falling back to OpenRouter")
            return await get_openrouter_response(text)

        except Exception as e:
            logger.error(f"Error in Dialogflow API call: {e}")
            return await get_openrouter_response(text)

    except Exception as e:
        logger.error(f"Error creating Dialogflow client: {e}")
        return await get_openrouter_response(text)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Render the main page"""
    return templates.TemplateResponse("index.html", {"request": request, "chat_history": chat_history})

@app.post("/process_input")
async def process_input(message: str = Form(...)):
    """Process user input and return response"""
    try:
        logger.info(f"Processing input: {message}")
        result = await detect_intent(message)
        
        formatted_response = result["response"]
        source_info = ""
        
        if result.get("source") == "dialogflow":
            source_info = f'<span class="source-info">Intent: {result["intent"]} (Confidence: {result["confidence"]:.2f})</span>'
            logger.info(f"Using Dialogflow response with intent: {result['intent']}")
        elif result.get("source") == "openrouter":
            source_info = f'<span class="source-info">Model: {result.get("model", "AI Model")}</span>'
            logger.info("Using OpenRouter response")
        else:
            logger.warning(f"Unknown source: {result.get('source')}")
        
        interaction = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_input": html.escape(message),
            "bot_response": formatted_response,
            "source_info": source_info
        }
        chat_history.append(interaction)
        
        return JSONResponse(content=interaction)
    except Exception as e:
        logger.error(f"Error processing input: {e}")
        return JSONResponse(
            content={
                "error": "An error occurred while processing your request",
                "details": str(e)
            },
            status_code=500
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
