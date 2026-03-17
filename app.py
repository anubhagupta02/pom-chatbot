from flask import Flask, render_template, request, jsonify
import google.genai as genai
import requests
import os
import re
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configure Gemini
client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

# POM API URL - replace with actual URL
POM_API_URL = os.getenv('POM_API_URL', 'https://api.example.com/query')

def validate_sql(sql):
    """Basic SQL validation to ensure only safe SELECT queries"""
    sql = sql.strip().upper()

    # Must start with SELECT
    if not sql.startswith('SELECT'):
        return False, "Only SELECT queries are allowed"

    # Check for dangerous keywords
    dangerous_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'TRUNCATE', 'EXEC', 'EXECUTE']
    for keyword in dangerous_keywords:
        if keyword in sql:
            return False, f"Query contains forbidden keyword: {keyword}"

    return True, None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/query', methods=['POST'])
def query():
    user_input = request.json.get('query')
    if not user_input:
        return jsonify({'error': 'No query provided'}), 400

    # Generate SQL using Gemini
    prompt = f"""
    Convert the following natural language query to SQL for a POM (Project Object Model) database.
    The database contains tables related to projects, tasks, users, etc.
    Generate only the SQL query, no explanations.

    Query: {user_input}
    """
    try:
        response = client.models.generate_content(
            model='models/gemini-3.1-flash-lite-preview',
            contents=prompt
        )
        sql_query = response.text.strip()
        # Clean up SQL if needed (remove markdown code blocks)
        if sql_query.startswith('```sql'):
            sql_query = sql_query[6:]
        if sql_query.endswith('```'):
            sql_query = sql_query[:-3]
        sql_query = sql_query.strip()
    except Exception as e:
        return jsonify({'error': f'Failed to generate SQL: {str(e)}'}), 500

    # Validate SQL
    is_valid, error_msg = validate_sql(sql_query)
    if not is_valid:
        return jsonify({'error': f'Generated SQL is not safe: {error_msg}'}), 400

    # Call POM API
    try:
        pom_response = requests.post(POM_API_URL, json={'sql': sql_query}, timeout=30)
        pom_response.raise_for_status()
        data = pom_response.json()
        print("data in app: ", data)
    except requests.RequestException as e:
        return jsonify({'error': f'POM API error: {str(e)}'}), 500

    return jsonify({'sql': sql_query, 'data': data})

if __name__ == '__main__':
    app.run(debug=True, port=8000)