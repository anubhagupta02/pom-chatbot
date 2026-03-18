from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os

# Import the agent
from agent import process_user_query

load_dotenv()

app = Flask(__name__)


@app.route('/')
def index():
    """
    Serve the main HTML page
    """
    return render_template('index.html')


@app.route('/query', methods=['POST'])
def query():
    """
    Process natural language query using the agent.
    
    The agent orchestrates:
    1. SQL generation from natural language
    2. SQL validation for safety
    3. Execution via POM API
    
    Request body: {"query": "natural language query"}
    Response: {"sql": "...", "data": {...}, "steps": [...]}
    """
    user_input = request.json.get('query')
    
    if not user_input:
        return jsonify({'error': 'No query provided'}), 400
    
    try:
        print(f"[Flask] Received query: {user_input}")
        
        # Process query through the agent
        result = process_user_query(user_input)
        
        if not result.get('success'):
            print(f"[Flask] Agent failed: {result.get('error')}")
            return jsonify({'error': result.get('error')}), 400
        
        print(f"[Flask] Agent succeeded. SQL: {result.get('sql')}")
        
        # Return result to frontend
        return jsonify({
            'sql': result.get('sql'),
            'data': result.get('data')
        })
        
    except Exception as e:
        print(f"[Flask] Unexpected error: {str(e)}")
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500


@app.route('/query/stream', methods=['POST'])
def query_stream():
    """
    Stream query processing steps for real-time UI updates.
    
    This endpoint gradually streams each step of the agent workflow
    so the frontend can show progress.
    """
    user_input = request.json.get('query')
    
    if not user_input:
        return jsonify({'error': 'No query provided'}), 400
    
    # Note: Streaming would require SSE or WebSocket in production
    # For now, we process normally (can be enhanced later)
    try:
        from agent import pom_agent
        
        result = pom_agent.process_query(user_input)
        
        if not result.get('success'):
            return jsonify({'error': result.get('error')}), 400
        
        return jsonify({
            'sql': result.get('sql'),
            'data': result.get('data')
        })
        
    except Exception as e:
        return jsonify({'error': f'Streaming failed: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8000)