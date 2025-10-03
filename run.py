import os
import threading
import uuid
import json
from flask import Flask, request, jsonify, url_for, render_template
from flask_cors import CORS  # <-- 1. IMPORT THIS
from datetime import datetime

# --- Bring in our existing data fetching and cleaning logic ---
from app.data_fetcher import get_wikipedia_data, get_gnews_data, get_serpapi_data
from app.text_cleaner import clean_wikipedia_text, clean_generic_text
from config import Config

# --- App Setup ---
app = Flask(__name__)
CORS(app)  # <-- 2. INITIALIZE CORS HERE
app.config.from_object(Config)

# This in-memory dictionary will act as our simple task database
tasks = {}

# --- The Scraping Function (to be run in a thread) ---
def run_scraping_task(task_id, topic, gnews_api_key, serpapi_api_key):
    """This function contains the logic that used to be in our Celery task."""
    print(f"Thread started for task {task_id} with topic: {topic}")
    try:
        # Step 1: Wikipedia
        tasks[task_id]['status'] = '1/3 - Fetching & cleaning Wikipedia...'
        raw_wiki_text = get_wikipedia_data(topic)
        wiki_text = clean_wikipedia_text(raw_wiki_text) if not raw_wiki_text.startswith("ERROR:") else ""

        # Step 2: GNews
        tasks[task_id]['status'] = '2/3 - Fetching & cleaning GNews...'
        raw_gnews_text = get_gnews_data(topic, gnews_api_key)
        gnews_text = clean_generic_text(raw_gnews_text) if not raw_gnews_text.startswith("ERROR:") else ""

        # Step 3: SerpAPI
        tasks[task_id]['status'] = '3/3 - Fetching & cleaning web search...'
        raw_web_text = get_serpapi_data(topic, serpapi_api_key)
        web_text = clean_generic_text(raw_web_text) if not raw_web_text.startswith("ERROR:") else ""

        combined_text = "\n\n".join(filter(None, [wiki_text, gnews_text, web_text]))
        if not combined_text.strip():
            raise ValueError("Could not retrieve any clean data for the topic from any source.")

        # Prepare the final result
        final_result = {
            'task_id': task_id,
            'topic': topic,
            'timestamp_utc': datetime.utcnow().isoformat(),
            'sources_used': ['Wikipedia', 'GNews', 'SerpAPI'],
            'character_count': len(combined_text),
            'content': combined_text
        }
        
        # Update the task store with the final result
        tasks[task_id]['status'] = 'SUCCESS'
        tasks[task_id]['result'] = final_result
        print(f"Task {task_id} completed successfully.")

    except Exception as e:
        print(f"Task {task_id} failed: {e}")
        tasks[task_id]['status'] = 'FAILURE'
        tasks[task_id]['error'] = str(e)


# --- API Routes ---
@app.route('/')
def index():
    """Serves the simple HTML page for testing."""
    return "API is running." # Changed from render_template for simplicity

@app.route('/generate', methods=['POST'])
def generate():
    """Starts the scraping task in a new background thread."""
    topic = request.form['topic']
    task_id = str(uuid.uuid4()) # Create a unique ID for our task

    # Store the initial state of the task
    tasks[task_id] = {'status': 'PENDING'}

    # Get API keys from the application config
    gnews_key = app.config.get('GNEWS_API_KEY')
    serpapi_key = app.config.get('SERPAPI_API_KEY')
    
    # Create and start the background thread
    thread = threading.Thread(
        target=run_scraping_task,
        args=(task_id, topic, gnews_key, serpapi_key)
    )
    thread.start()

    return jsonify({
        'message': 'Scraping task has been started.',
        'task_id': task_id,
        'status_url': url_for('status', task_id=task_id, _external=True)
    }), 202

@app.route('/status/<task_id>')
def status(task_id):
    """Checks the status of a task."""
    task = tasks.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    response = {
        'task_id': task_id,
        'state': task.get('status'),
        'result': task.get('result', None),
        'error': task.get('error', None)
    }
    return jsonify(response)


if __name__ == '__main__':
    app.run(debug=True)