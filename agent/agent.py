"""
POM Chatbot Agent
Main agent that orchestrates tools to convert NLP queries to results
"""

import json
import os
import google.genai as genai
from dotenv import load_dotenv
from agent.tools import sql_generator_tool, sql_validator_tool, pom_api_executor_tool

# Load .env before reading environment variables
load_dotenv()

# Initialize Gemini client
client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

class POMChatbotAgent:
    """
    Agent that orchestrates the SQL generation, validation, and execution workflow.
    
    This agent acts as a coordinator that:
    1. Receives natural language query
    2. Decides which tools to use and in what order
    3. Executes tools and processes results
    4. Returns final result to user
    """
    
    def __init__(self):
        self.model = 'models/gemini-3.1-flash-lite-preview'
        self.conversation_history = []
        
    def _create_system_prompt(self):
        """Creates the system prompt that guides agent behavior"""
        return """
You are POMChatbot, an intelligent SQL agent for a Project Object Model (POM) database.

Your role:
1. Understand natural language queries from users
2. Generate appropriate SQL queries
3. Validate queries for safety
4. Execute valid queries and return results

Available tools:
- sql_generator: Converts natural language to SQL
- sql_validator: Validates SQL for safety
- pom_api_executor: Executes SQL and returns results

Workflow:
1. First, use sql_generator to convert the user query to SQL
2. Then, use sql_validator to ensure the SQL is safe
3. If valid, use pom_api_executor to run the query
4. Return the results with the SQL query and execution results

Always follow this order. Do not execute unvalidated queries.
Provide clear error messages if anything fails.
"""
    
    def process_query(self, user_query: str) -> dict:
        """
        Main method to process a user query through the agent workflow.
        
        Args:
            user_query: Natural language query from user
        
        Returns:
            Dictionary with execution results containing:
            - sql: Generated SQL query
            - data: Query results from POM API
            - steps: Execution steps taken by agent
            - success: Whether overall execution succeeded
        """
        
        try:
            
            # ===== STEP 1: Generate SQL =====
            print(f"[Agent] Processing query: {user_query}")
            
            sql_result = sql_generator_tool(user_query)
            
            if sql_result.get("status") == "error":
                print(f"[Agent] SQL Generation failed: {sql_result.get('error')}")
                return {
                    "success": False,
                    "error": sql_result.get("error")
                }
            
            generated_sql = sql_result.get("sql")
            
            print(f"[Agent] Generated SQL: {generated_sql}")
            
            # ===== STEP 2: Validate SQL =====
            
            validation_result = sql_validator_tool(generated_sql)
            
            if not validation_result.get("is_valid"):
                print(f"[Agent] SQL Validation failed: {validation_result.get('errors')}")
                return {
                    "success": False,
                    "error": f"SQL validation failed: {validation_result.get('errors')}"
                }
            
            print(f"[Agent] SQL validated successfully")
            
            # ===== STEP 3: Execute on POM API =====
            
            execution_result = pom_api_executor_tool(generated_sql)
            
            if not execution_result.get("success"):
                print(f"[Agent] POM API execution failed: {execution_result.get('error')}")
                return {
                    "success": False,
                    "error": execution_result.get("error"),
                    "sql": generated_sql
                }
            
            query_data = execution_result.get("data", {})
            
            print(f"[Agent] Query executed successfully")
            
            # ===== FINAL RESULT =====
            final_result = {
                "success": True,
                "sql": generated_sql,
                "data": query_data
            }
            
            print(f"[Agent] Workflow complete. Result: success")
            return final_result
            
        except Exception as e:
            print(f"[Agent] Unexpected error: {str(e)}")
            return {
                "success": False,
                "error": f"Agent processing failed: {str(e)}"
            }
    
    def stream_query(self, user_query: str):
        """
        Stream query processing steps for real-time UI updates.
        
        Yields:
            Dictionary with each step's result
        """
        try:
            # Step 1: SQL Generation
            yield {"step": 1, "action": "Generating SQL...", "status": "in_progress"}
            
            sql_result = sql_generator_tool(user_query)
            
            if sql_result.get("status") == "error":
                yield {"step": 1, "status": "error", "error": sql_result.get("error")}
                return
            
            generated_sql = sql_result.get("sql")
            yield {"step": 1, "action": "SQL Generated", "status": "completed", "sql": generated_sql}
            
            # Step 2: SQL Validation
            yield {"step": 2, "action": "Validating SQL...", "status": "in_progress"}
            
            validation_result = sql_validator_tool(generated_sql)
            
            if not validation_result.get("is_valid"):
                yield {"step": 2, "status": "error", "errors": validation_result.get("errors")}
                return
            
            yield {"step": 2, "action": "SQL Validated", "status": "completed"}
            
            # Step 3: Execute SQL
            yield {"step": 3, "action": "Executing query...", "status": "in_progress"}
            
            execution_result = pom_api_executor_tool(generated_sql)
            
            if not execution_result.get("success"):
                yield {"step": 3, "status": "error", "error": execution_result.get("error")}
                return
            
            yield {
                "step": 3,
                "action": "Query executed",
                "status": "completed",
                "data": execution_result.get("data")
            }
            
        except Exception as e:
            yield {"status": "error", "error": f"Stream processing failed: {str(e)}"}


# ============================================================================
# Initialize default agent instance
# ============================================================================

pom_agent = POMChatbotAgent()


def process_user_query(query: str) -> dict:
    """
    Convenience function to process a query using the default agent.
    
    Args:
        query: Natural language query
    
    Returns:
        Result dictionary with sql, data, and execution steps
    """
    return pom_agent.process_query(query)
