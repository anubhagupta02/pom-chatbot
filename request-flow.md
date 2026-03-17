# POM Chatbot - Request Flow

## How index.html Calls app.py

**The connection happens via HTTP requests.** Here's the complete flow:

## Step-by-Step Flow

### 1. User clicks Submit button (index.html)
```html
<button class="btn btn-primary" onclick="submitQuery()">Submit</button>
```

### 2. JavaScript function executes (functions.js)
```javascript
async function submitQuery() {
    const query = document.getElementById('queryInput').value.trim();
    
    // Make HTTP POST request to backend
    const response = await fetch('/query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: query })
    });
    
    const data = await response.json();
    // ... handle response
}
```

### 3. HTTP Request is sent to Flask backend (app.py)

**Request details:**
- **URL**: `/query`
- **Method**: POST
- **Body**: `{"query": "Show me all active projects"}`

### 4. Flask app.py receives and processes (app.py)
```python
@app.route('/query', methods=['POST'])
def query():
    user_input = request.json.get('query')  # Get "Show me all active projects"
    
    # Step 1: Generate SQL using Gemini
    response = client.models.generate_content(model='...', contents=prompt)
    sql_query = response.text.strip()
    
    # Step 2: Validate SQL
    is_valid, error_msg = validate_sql(sql_query)
    if not is_valid:
        return jsonify({'error': f'Generated SQL is not safe: ...'}), 400
    
    # Step 3: Call POM API
    pom_response = requests.post(POM_API_URL, json={'sql': sql_query})
    data = pom_response.json()
    
    # Step 4: Return response to frontend
    return jsonify({'sql': sql_query, 'data': data})
```

### 5. Response sent back to JavaScript
```javascript
const data = await response.json();
// Returns: {sql: "SELECT * FROM projects", data: {...}}

if (response.ok) {
    displayResults(data);  // Render table in UI
}
```

### 6. HTML is updated (index.html)
```javascript
function displayResults(data) {
    document.getElementById('sqlDisplay').textContent = data.sql;
    // Build and render table...
}
```

---

## Visual Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ Browser (index.html)                                        │
│                                                             │
│ User Types: "Show me all active projects"                  │
│ User Clicks: Submit Button                                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ onclick="submitQuery()"
                     │ (functions.js is loaded)
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ JavaScript (functions.js)                                   │
│                                                             │
│ submitQuery() function:                                    │
│  - Get input value                                         │
│  - Make fetch() call                                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ HTTP POST /query
                     │ Content-Type: application/json
                     │ Body: {"query": "Show me all active..."}
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ Flask Backend (app.py)                                      │
│                                                             │
│ @app.route('/query', methods=['POST'])                     │
│ def query():                                               │
│   - Extract query from request.json                        │
│   - Call Gemini API (generate SQL)                         │
│   - Validate SQL                                           │
│   - Call POM API (execute SQL)                             │
│   - Return JSON response                                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ HTTP Response 200 OK
                     │ Content-Type: application/json
                     │ Body: {sql: "SELECT...", data: {...}}
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ JavaScript (functions.js)                                   │
│                                                             │
│ - Receive response                                         │
│ - Call displayResults(data)                                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ DOM Manipulation
                     │ displayResults():
                     │  - Set SQL text
                     │  - Build table rows
                     │  - Show results
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ Browser (index.html)                                        │
│                                                             │
│ ✅ Results displayed to user                               │
│    SQL shown, Table rendered                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow Details

### Request Payload (Browser → Flask)
```json
{
  "query": "Show me all active projects"
}
```

### Flask Processing Steps

1. **Parse Request**
   - Extract `query` from JSON body

2. **Generate SQL**
   - Call Gemini API with prompt
   - Gemini returns SQL (possibly with markdown)
   - Clean up markdown code blocks

3. **Validate SQL**
   - Check: Must start with SELECT
   - Check: No dangerous keywords (INSERT, UPDATE, DELETE, etc.)

4. **Execute SQL**
   - Send SQL to POM API
   - Receive results: `{columns: [...], data: [...]}`

5. **Return Response**
   - Send back to browser

### Response Payload (Flask → Browser)
```json
{
  "sql": "SELECT * FROM projects WHERE status = 'active'",
  "data": {
    "columns": ["id", "name", "status"],
    "data": [
      [1, "Project A", "active"],
      [2, "Project B", "active"]
    ]
  }
}
```

### Frontend Processing Steps

1. **Receive Response**
   - Parse JSON from response body

2. **Display SQL**
   - Show generated SQL query to user

3. **Build Table**
   - Extract columns from `data.columns`
   - Extract rows from `data.data`
   - Create HTML table dynamically

4. **Render Results**
   - Show table with Bootstrap styling

---

## HTTP Request/Response Examples

### Example Request (Chrome DevTools)
```
POST /query HTTP/1.1
Host: localhost:8000
Content-Type: application/json
Content-Length: 45

{"query":"Show me all active projects"}
```

### Example Response (HTTP 200)
```
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 234

{
  "sql": "SELECT * FROM projects WHERE status = 'active'",
  "data": {
    "columns": ["id", "name", "status"],
    "data": [[1, "Project A", "active"], [2, "Project B", "active"]]
  }
}
```

### Example Error Response (HTTP 400)
```
HTTP/1.1 400 BAD REQUEST
Content-Type: application/json

{
  "error": "Generated SQL is not safe: Query contains forbidden keyword: DELETE"
}
```

---

## Key Points

1. **No Direct File Import** 
   - index.html doesn't import or call app.py directly
   
2. **HTTP Bridge** 
   - They communicate via HTTP requests/responses
   
3. **RESTful Endpoint** 
   - `/query` is a REST endpoint that app.py exposes
   
4. **JSON Format** 
   - Data exchanged in JSON (browser-friendly)
   
5. **Async Communication** 
   - JavaScript `async/await` makes the request non-blocking
   
6. **Separation of Concerns**
   - Frontend: JavaScript (UI & User Interaction)
   - Backend: Python (Business Logic & API Calls)
   - Communication: HTTP/JSON protocol

---

## Different Languages

- **Frontend**: JavaScript (index.html, functions.js)
- **Backend**: Python (app.py)
- **Communication Protocol**: HTTP/JSON

The beauty of this architecture is that they don't need to know each other's implementation details — they just need to agree on the HTTP contract (URL, method, request format, response format).
