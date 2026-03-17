# pom-chatbot
chatbot agent which calls pom-api on backend

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   - Copy `.env` file and fill in your API keys:
     - `GOOGLE_API_KEY`: Your Google Gemini AI API key 
     - `POM_API_URL`: The URL of your existing POM API

3. Run the application:
   ```bash
   source /venv/bin/python 
   python app.py
   ```

4. Open your browser to `http://localhost:8000`

## Features

- Natural language to SQL conversion using Gemini
- Integration with existing POM API
- Results displayed in interactive table format
- Responsive web interface
