# Google ADK Implementation Guide

## Overview

The POM Chatbot now uses **Google Agent Development Kit (ADK)** pattern to orchestrate SQL generation, validation, and execution as a coordinated workflow. This replaces the previous linear implementation.

## Architecture

### Before (Linear Flow)
```
User Query → Gemini → Validate → POM API → Return Result
```

### After (Agent-Orchestrated)
```
User Query → Agent Coordinator → Orchestrates:
                                    ├─ SQL Generator Tool
                                    ├─ SQL Validator Tool  
                                    ├─ POM API Executor Tool
                                    └─ Decision Making
                              → Return Result with Steps
```

---

## New Project Structure

```
pom-chatbot/
├── agent/                          # Agent module (NEW)
│   ├── __init__.py                 # Module exports
│   ├── agent.py                    # Main agent orchestrator
│   └── tools.py                    # Tool definitions
├── app.py                          # Flask backend (REFACTORED)
├── templates/
│   ├── index.html
│   └── functions.js
├── requirements.txt                # UPDATED: Added pydantic
└── request-flow.md
```

---

## Component Breakdown

### 1. **agent/tools.py** - Tool Definitions

Three main tools are defined:

#### Tool 1: SQL Generator
```python
def sql_generator_tool(query: str) -> dict
```
- **Purpose**: Convert natural language to SQL
- **Input**: User's natural language query
- **Output**: Generated SQL + reasoning
- **Uses**: Gemini API for NLP-to-SQL conversion

**Example:**
```
Input:  "Show me all active projects"
Output: {
  "sql": "SELECT * FROM projects WHERE status = 'active'",
  "reasoning": "Queried projects table with active status filter"
}
```

#### Tool 2: SQL Validator
```python
def sql_validator_tool(sql: str) -> dict
```
- **Purpose**: Verify SQL is safe to execute
- **Input**: Generated SQL query
- **Output**: Validation result with errors (if any)
- **Checks**:
  - Must start with SELECT
  - Blocks: INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, TRUNCATE, EXEC
  - Blocks SQL comments (-- and /* */)

**Example:**
```
Input:  "DELETE FROM projects"
Output: {
  "is_valid": False,
  "errors": ["Forbidden keyword found: DELETE"],
  "message": "SQL validation failed"
}
```

#### Tool 3: POM API Executor
```python
def pom_api_executor_tool(sql: str) -> dict
```
- **Purpose**: Execute SQL against POM database
- **Input**: Validated SQL query
- **Output**: Query results from POM API
- **Handles**: HTTP requests, error handling, timeout

**Example:**
```
Input:  "SELECT * FROM projects WHERE status = 'active'"
Output: {
  "success": True,
  "data": {
    "columns": ["id", "name", "status"],
    "data": [[1, "Project A", "active"]]
  }
}
```

---

### 2. **agent/agent.py** - Agent Orchestrator

The `POMChatbotAgent` class coordinates tool execution:

```python
class POMChatbotAgent:
    def process_query(self, user_query: str) -> dict
```

**Workflow:**

```
┌─────────────────────────────────┐
│  User Query Received            │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  STEP 1: SQL Generation         │
│  └─ sql_generator_tool()        │
│     - Convert NLP to SQL        │
│     - Return: sql + reasoning   │
└──────────────┬──────────────────┘
               │
               ├─ Error? → Return error
               │
               ▼
┌─────────────────────────────────┐
│  STEP 2: SQL Validation         │
│  └─ sql_validator_tool()        │
│     - Safety checks             │
│     - Return: valid or errors   │
└──────────────┬──────────────────┘
               │
               ├─ Invalid? → Return error
               │
               ▼
┌─────────────────────────────────┐
│  STEP 3: POM API Execution      │
│  └─ pom_api_executor_tool()     │
│     - Execute SQL               │
│     - Return: data or error     │
└──────────────┬──────────────────┘
               │
               ├─ Failed? → Return error
               │
               ▼
┌─────────────────────────────────┐
│  FINAL RESULT                   │
│  {                              │
│    "success": True,             │
│    "sql": "SELECT...",          │
│    "data": {...},               │
│    "steps": [...]               │
│  }                              │
└─────────────────────────────────┘
```

**Key Features:**
- **Sequential Execution**: Tools run in order
- **Error Handling**: Stops on first error, returns detailed error info
- **Step Tracking**: Records each step in execution history
- **Logging**: Prints progress to console with [Agent] prefix

---

### 3. **app.py** - Refactored Flask Backend

**Before:**
```python
# Direct implementation
@app.route('/query', methods=['POST'])
def query():
    # Generate SQL
    # Validate SQL
    # Call POM API
    # Return result
```

**After:**
```python
# Uses agent
@app.route('/query', methods=['POST'])
def query():
    from agent import process_user_query
    result = process_user_query(user_input)
    return jsonify(result)
```

**Changes:**
- ✅ Removed direct `google.genai` calls
- ✅ Removed inline validation logic
- ✅ Removed request library calls
- ✅ All logic delegated to agent module
- ✅ Added `/query/stream` endpoint for future streaming

---

## Data Flow Comparison

### Old Flow (Direct)
```
Request → app.py (inline processing) → Response
```

### New Flow (Agent-based)
```
Request → app.py (delegates to agent)
            ↓
        POMChatbotAgent.process_query()
            ├─ Call tool 1: sql_generator_tool()
            ├─ Call tool 2: sql_validator_tool()
            ├─ Call tool 3: pom_api_executor_tool()
            └─ Compile results + steps
            ↓
Response (with execution steps visible)
```

---

## Request/Response Format

### Request
```json
{
  "query": "Show me all active projects"
}
```

### Response (Success)
```json
{
  "sql": "SELECT * FROM projects WHERE status = 'active'",
  "data": {
    "columns": ["id", "name", "status"],
    "data": [[1, "Project A", "active"]]
  },
  "reasoning": "Queried projects table with active status filter",
  "steps": [
    {
      "step": 1,
      "action": "sql_generation",
      "status": "completed",
      "sql": "SELECT...",
      "reasoning": "..."
    },
    {
      "step": 2,
      "action": "sql_validation",
      "status": "completed",
      "validation_message": "SQL is safe"
    },
    {
      "step": 3,
      "action": "pom_api_execution",
      "status": "completed",
      "execution_message": "Query executed successfully"
    }
  ]
}
```

### Response (Error)
```json
{
  "error": "SQL validation failed: Forbidden keyword found: DELETE",
  "sql": "DELETE FROM projects",
  "steps": [
    {
      "step": 1,
      "action": "sql_generation",
      "status": "completed",
      "sql": "DELETE FROM projects"
    },
    {
      "step": 2,
      "action": "sql_validation",
      "status": "completed",
      "errors": ["Forbidden keyword found: DELETE"]
    }
  ]
}
```

---

## Benefits of ADK Pattern

| Aspect | Old | New (ADK) |
|--------|-----|-----------|
| **Code Organization** | Monolithic | Modular tools |
| **Reusability** | Tied to app.py | Standalone tools |
| **Testing** | Full integration test needed | Can test each tool |
| **Error Handling** | Linear stop | Detailed step tracking |
| **Observability** | Basic logs | Full execution steps |
| **Scalability** | Limited | Easier to add tools |
| **Extensibility** | Modify app.py | Add new tools easily |
| **Reasoning** | Hidden | Visible in response |

---

## Installation & Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set environment variables (.env)
```env
GOOGLE_API_KEY=your_gemini_api_key
POM_API_URL=https://your-pom-api.com/query
```

### 3. Run Flask
```bash
python app.py
```

---

## Adding New Tools

To add a new tool to the agent:

### Step 1: Define tool in `agent/tools.py`
```python
def my_new_tool(param: str) -> dict:
    """
    Tool description
    """
    try:
        # Implementation
        return {"success": True, "result": value}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### Step 2: Use in `agent/agent.py`
```python
from agent.tools import my_new_tool

# Inside POMChatbotAgent.process_query():
result = my_new_tool(param)
if not result["success"]:
    # Handle error
```

---

## Debugging

Check the Flask console for detailed logs:

```
[Agent] Processing query: Show me all active projects
[Agent] Generated SQL: SELECT * FROM projects WHERE status = 'active'
[Agent] Reasoning: Queried projects table with active status filter
[Agent] SQL validated successfully
[Agent] Query executed successfully
[Agent] Workflow complete. Result: success
```

---

## Future Enhancements

1. **Streaming**: Use Server-Sent Events (SSE) to stream steps in real-time
2. **Conversation History**: Multi-turn conversations with context
3. **Tool Chaining**: Complex workflows with dependent tools
4. **Error Recovery**: Agent can retry or fallback with different approaches
5. **Caching**: Cache SQL generation for repeated queries
6. **Analytics**: Track tool usage and performance metrics

---

## Summary of Changes

| File | Change | Why |
|------|--------|-----|
| **agent/tools.py** | NEW | Defines reusable tools |
| **agent/agent.py** | NEW | Orchestrates tool execution |
| **agent/__init__.py** | NEW | Module exports |
| **app.py** | REFACTORED | Delegates to agent (70% less code) |
| **requirements.txt** | UPDATED | Added pydantic for models |
| **templates/** | UNCHANGED | Works with new backend |

The agent is transparent to the frontend — it still receives the same response format, but now with added visibility into the execution steps.
