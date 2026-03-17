# POM Chatbot - Current Architecture

## Overview
A Flask-based web application that converts natural language queries to SQL using Google Gemini API, validates them for safety, and executes them against a POM API.

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                          User Browser                         │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Frontend (Static Files)                                │  │
│  │  - index.html (form UI, results table)                │  │
│  │  - app.js (JavaScript functions & event handlers)     │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────┬───────────────────────────────────────────────┘
               │ HTTP POST /query
               │ {query: "natural language"}
               │
┌──────────────▼───────────────────────────────────────────────┐
│                      Flask Backend                            │
│                       (app.py)                                │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ GET / endpoint                                          │ │
│  │  └─> Serve index.html                                  │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ POST /query endpoint                                    │ │
│  │  1. Receive natural language query                      │ │
│  │  2. Call Gemini API → Generate SQL                     │ │
│  │  3. Validate SQL (safety checks):                       │ │
│  │     - Only SELECT allowed                              │ │
│  │     - Block: INSERT, UPDATE, DELETE, DROP, etc.        │ │
│  │  4. Call POM API with validated SQL                    │ │
│  │  5. Return {sql, data} as JSON                          │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Dependencies                                            │ │
│  │  - google.genai (Gemini API client)                    │ │
│  │  - requests (HTTP client)                              │ │
│  │  - flask (web framework)                               │ │
│  │  - python-dotenv (environment variables)               │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
└──────────────┬───────────────────────────┬───────────────────┘
               │                           │
         HTTP GET                    HTTP POST
    (API call)                   (API call)
               │                           │
┌──────────────▼──────────┐   ┌────────────▼──────────┐
│    Google Gemini        │   │     POM API           │
│    Generative AI        │   │ (Environment Config)  │
│                         │   │                       │
│ - Generate SQL          │   │ - Execute SQL         │
│   from natural language │   │ - Return results      │
│                         │   │   {columns, data}     │
└─────────────────────────┘   └────────────┬──────────┘
                                            │
                              ┌─────────────▼──────────┐
                              │  Oracle Database       │
                              │  (POM Database)        │
                              │                        │
                              │ - Projects, Tasks, Etc │
                              └────────────────────────┘
```

## Data Flow

### 1. User Input → Frontend
- User enters natural language query in input field
- Clicks "Submit" or presses Enter
- JavaScript: `submitQuery()` is triggered

### 2. Frontend → Backend
```
POST /query
Content-Type: application/json

{
  "query": "Show me all active projects"
}
```

### 3. Backend Processing
1. **Receive query** from request JSON
2. **Generate SQL** using Gemini:
   - Prompt: "Convert this NLP to SQL for POM database"
   - Model: `models/gemini-2.0-flash`
   - Clean up markdown code blocks if present
3. **Validate SQL**:
   - Must start with SELECT
   - Reject dangerous keywords (INSERT, UPDATE, DELETE, DROP, etc.)
4. **Call POM API**:
   - POST to `POM_API_URL` with generated SQL
   - Expected response: `{columns: [...], data: [[...]]}`
5. **Return Response**:
   ```json
   {
     "sql": "SELECT * FROM projects WHERE status = 'active'",
     "data": {
       "columns": ["id", "name", "status"],
       "data": [[1, "Project A", "active"], [2, "Project B", "active"]]
     }
   }
   ```

### 4. Backend → Frontend
Response JSON is sent back to browser

### 5. Frontend Result Display
- JavaScript: `displayResults(data)` is called
- Extract SQL: `data.sql`
- Extract table data: `data.data.data`
- Extract columns: `data.data.columns`
- Render HTML table with Bootstrap styling

## File Structure

```
pom-chatbot/
├── app.py                          # Flask backend
├── templates/
│   ├── index.html                  # Main UI
│   └── app.js                      # Frontend JavaScript
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables
├── README.md                        # Project documentation
├── architecture-diagram.md         # Future agent architecture
├── current-architecture.md         # Current implementation (this file)
└── __pycache__/                   # Python cache
```

## Environment Variables (.env)

```env
GOOGLE_API_KEY=your_gemini_api_key
POM_API_URL=https://your-pom-api.com/query
```

## Key Components

### Backend (Python)
- **Language**: Python 3.x
- **Framework**: Flask
- **AI**: Google Generative AI (Gemini)
- **HTTP**: requests library

### Frontend (JavaScript)
- **HTML**: Bootstrap 5 + custom CSS
- **JavaScript**: Vanilla JS (no frameworks)
- **Functions**:
  - `submitQuery()` — Form submission handler
  - `displayResults()` — Table rendering
  - `showError()` — Error display

### Security Features
- SQL validation on backend (only SELECT allowed)
- Dangerous keyword filtering
- POM API handles additional validation

## Deployment
- **Server**: Flask (development mode on port 8000)
- **Static Files**: Served by Flask
- **JavaScript**: Loaded externally from app.js
- **APIs**: Called from backend (not exposed to frontend)
