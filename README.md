# AI Voice Assistant

A simple AI Voice Assistant built with FastAPI, featuring voice recognition and basic intent matching.

## Google Drive Video Demonstration Link
Link: https://drive.google.com/file/d/1L88-7qppnCnnLB2_xEMUiyxvc1t09nO0/view?usp=sharing

## Features

- Text and voice input support
- Basic intent recognition system
- Real-time chat interface
- Responsive design using Bootstrap
- Docker support

## Prerequisites

- Python 3.9+
- Docker (optional)

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Without Docker

```bash
uvicorn main:app --reload
```

### With Docker

```bash
docker build -t ai-voice-assistant .
docker run -p 8000:8000 ai-voice-assistant
```

Visit `http://localhost:8000` in your browser to use the application.

## Project Structure

```
.
├── main.py              # FastAPI application
├── static/              # Static files
│   ├── css/            # CSS styles
│   └── js/             # JavaScript files
├── templates/          # HTML templates
├── requirements.txt    # Python dependencies
└── Dockerfile         # Docker configuration
```

## Dialogflow Setup

1. **Prerequisites**:
   - Google Cloud account
   - Dialogflow ES project
   - Google Cloud project credentials

2. **Setup Steps**:
   1. Go to [Google Cloud Console](https://console.cloud.google.com)
   2. Create a new project or select an existing one
   3. Enable the Dialogflow API for your project
   4. Create a service account:
      - Go to "IAM & Admin" > "Service Accounts"
      - Click "Create Service Account"
      - Give it a name and grant "Dialogflow API Client" role
      - Create a new JSON key and download it
   5. Save the downloaded JSON key file as `dialogflow_credentials.json` in your project root
   6. Update `DIALOGFLOW_PROJECT_ID` in `main.py` with your project ID

3. **Create Intents in Dialogflow**:
   1. Go to [Dialogflow Console](https://dialogflow.cloud.google.com/)
   2. Select your project
   3. Create intents for:
      - Greetings
      - Farewells
      - Time queries
      - Date queries
      - Weather queries
   4. For each intent:
      - Add training phrases
      - Add responses
      - Save the intent

## Current Features

- Basic intent recognition for:
  - Greetings
  - Farewells
  - Time queries
  - Date queries
  - Weather queries (placeholder)
- Voice input support
- Chat history
- Responsive UI

## Future Improvements

- Integration with advanced NLP services
- MongoDB integration for persistent storage
- More sophisticated intent recognition
- Multi-language support
