"""
Tool definitions for POM Chatbot Agent
These tools define what actions the agent can perform
"""
from typing import Literal
import google.genai as genai
import requests
import re
import os
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load .env before reading environment variables
load_dotenv()

# Initialize Gemini client
client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

# ============================================================================
# TOOL 1: SQL GENERATOR TOOL
# ============================================================================

class SQLGeneratorRequest(BaseModel):
    """Input model for SQL generator"""
    query: str = Field(
        description="Natural language query to convert to SQL"
    )

class SQLGeneratorResponse(BaseModel):
    """Output model for SQL generator"""
    sql: str = Field(description="Generated SQL query")

def sql_generator_tool(query: str) -> dict:
    """
    TOOL: SQL Generator
    
    Converts natural language query to SQL using Gemini.
    
    Args:
        query: Natural language query (e.g., "Show all orders")
    
    Returns:
        Dictionary with generated SQL
    
    Example:
        Input: "Show all orders"
        Output: {
            "sql": "SELECT * FROM extnl_ord"
        }
        
    """
    prompt = f"""
    You are a SQL query generator for an Oracle database used in a POM (Project Object Model) system.
    
    Database tables:
    - extnl_ord (extnl_ord, crt_ts)
    
    Column types:
    - crt_ts is a TIMESTAMP column
    
    Oracle SQL Rules (follow strictly):
    - Always use Oracle syntax: SYSDATE, TRUNC(), NVL(), TO_DATE(), etc.
    - Do NOT use CURRENT_DATE, INTERVAL '1 day' (incorrect Oracle syntax)
    - For date intervals use: SYSDATE - 1, SYSDATE - 7, etc.
    - For TIMESTAMP columns, always use a range with TRUNC() to capture the full day:
        WHERE crt_ts >= TRUNC(SYSDATE - 1) AND crt_ts < TRUNC(SYSDATE)   -- yesterday
        WHERE crt_ts >= TRUNC(SYSDATE) AND crt_ts < TRUNC(SYSDATE + 1)   -- today
        WHERE crt_ts >= TRUNC(SYSDATE - 7) AND crt_ts < TRUNC(SYSDATE)   -- last 7 days
    - Never use: CURRENT_DATE, INTERVAL '1 day', crt_ts = TRUNC(...)
    
    Convert the following natural language query to Oracle SQL.
    Generate ONLY the SQL query, no explanations.
    
    Natural Language Query: {query}
    """
    
    try:
        response = client.models.generate_content(
            model='models/gemini-3.1-flash-lite-preview',
            contents=prompt
        )
        
        sql = response.text.strip()
        
        # Clean markdown if present
        if sql.startswith('```sql'):
            sql = sql[6:]
        if sql.endswith('```'):
            sql = sql[:-3]
        sql = sql.strip()
        
        return {
            "status": "success",
            "sql": sql
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": f"SQL Generation failed: {str(e)}"
        }


# ============================================================================
# TOOL 2: SQL VALIDATOR TOOL
# ============================================================================

class SQLValidatorRequest(BaseModel):
    """Input model for SQL validator"""
    sql: str = Field(description="SQL query to validate")

class SQLValidatorResponse(BaseModel):
    """Output model for SQL validator"""
    is_valid: bool = Field(description="Whether SQL is safe to execute")
    errors: list = Field(description="List of validation errors if any")
    message: str = Field(description="Validation message")

def sql_validator_tool(sql: str) -> dict:
    """
    TOOL: SQL Validator
    
    Validates SQL query for safety before execution.
    - Only SELECT queries allowed
    - Blocks dangerous keywords (INSERT, UPDATE, DELETE, DROP, etc.)
    
    Args:
        sql: SQL query to validate
    
    Returns:
        Dictionary with validation result
    
    Example:
        Input: "SELECT * FROM extnl_ord"
        Output: {
            "is_valid": True,
            "errors": [],
            "message": "SQL is safe to execute"
        }
    """
    sql_upper = sql.strip().upper()
    errors = []
    
    # Rule 1: Must start with SELECT
    if not sql_upper.startswith('SELECT'):
        errors.append("Only SELECT queries are allowed")
    
    # Rule 2: Check for dangerous keywords
    dangerous_keywords = [
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE',
        'ALTER', 'TRUNCATE', 'EXEC', 'EXECUTE', 
        'GRANT', 'REVOKE', 'BEGIN', 'COMMIT', 'ROLLBACK'
    ]
    
    for keyword in dangerous_keywords:
        if keyword in sql_upper:
            errors.append(f"Forbidden keyword found: {keyword}")
    
    # Rule 3: Check for suspicious patterns
    if '--' in sql:
        errors.append("SQL comments (--) not allowed")
    
    if '/*' in sql or '*/' in sql:
        errors.append("Multi-line comments not allowed")
    
    is_valid = len(errors) == 0
    
    return {
        "is_valid": is_valid,
        "errors": errors,
        "message": "SQL is safe" if is_valid else "SQL validation failed",
        "sql": sql
    }


# ============================================================================
# TOOL 3: POM API EXECUTOR TOOL
# ============================================================================

class POMAPIRequest(BaseModel):
    """Input model for POM API executor"""
    sql: str = Field(description="SQL query to execute")

class POMAPIResponse(BaseModel):
    """Output model for POM API executor"""
    success: bool = Field(description="Whether execution was successful")
    data: dict = Field(description="Query results")
    message: str = Field(description="Status message")

def pom_api_executor_tool(sql: str) -> dict:
    """
    TOOL: POM API Executor
    
    Executes validated SQL against POM API and returns results.
    
    Args:
        sql: Validated SQL query to execute
    
    Returns:
        Dictionary with execution results
    
    Example:
        Input: "SELECT * FROM extnl_ord"
        Output: {
            "success": True,
            "data": {
                "columns": ["extnl_ord", "crt_ts"],
                "data": [[1, "2023-01-01"], [2, "2023-01-02"]]
            }
        }
    """
    try:
        pom_api_url = os.getenv('POM_API_URL', 'https://api.example.com/query')
        
        if pom_api_url == 'https://api.example.com/query':
            return {
                "success": False,
                "error": "POM API URL not configured",
                "message": "Set POM_API_URL in environment variables"
            }
        
        response = requests.post(
            pom_api_url,
            json={'sql': sql},
            timeout=30
        )
        
        response.raise_for_status()
        data = response.json()
        print(f"[POM API] Response in tool: {data}")
        
        return {
            "success": True,
            "data": data,
            "message": "Query executed successfully"
        }
        
    except requests.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to call POM API"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Unexpected error in POM API call"
        }


# ============================================================================
# TOOL REGISTRY
# Defines all available tools for the agent
# ============================================================================

TOOLS = [
    {
        "name": "sql_generator",
        "description": "Converts natural language queries to SQL",
        "handler": sql_generator_tool,
        "input_model": SQLGeneratorRequest
    },
    {
        "name": "sql_validator",
        "description": "Validates SQL queries for safety before execution",
        "handler": sql_validator_tool,
        "input_model": SQLValidatorRequest
    },
    {
        "name": "pom_api_executor",
        "description": "Executes SQL queries against the POM API",
        "handler": pom_api_executor_tool,
        "input_model": POMAPIRequest
    }
]
