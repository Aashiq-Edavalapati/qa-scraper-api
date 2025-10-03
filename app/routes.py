from flask import current_app as app, request, jsonify, url_for, render_template
from .tasks import generate_qa_task

@app.route('/', methods=['GET'])
def index():
    """Serves the main page with a form to start a task."""
    # This route is now mainly for API testing or a potential admin view
    return "QA Generator API is running."

@app.route('/generate', methods=['POST'])
def start_generation():
    """Takes the topic from the form and starts the background task."""
    # Use request.form for form data from React
    topic = request.form.get('topic')
    if not topic:
        return jsonify({'error': 'Please enter a topic.'}), 400
    
    gnews_key = app.config.get('GNEWS_API_KEY')
    serpapi_key = app.config.get('SERPAPI_API_KEY')
    task = generate_qa_task.delay(topic, gnews_key, serpapi_key)
    
    return jsonify({
        'message': 'Your QA dataset generation has started!',
        'task_id': task.id,
        'check_status_url': url_for('get_status', task_id=task.id, _external=True)
    }), 202

@app.route('/status/<task_id>')
def get_status(task_id):
    """Checks and returns the status of the task."""
    task = generate_qa_task.AsyncResult(task_id)
    
    response_data = {
        'state': task.state,
        'info': task.info,
    }

    # --- FIXED: Directly assign the task's result ---
    # When the task is successful, task.result will contain the dictionary
    # we returned from the task function.
    if task.state == 'SUCCESS':
        response_data['result'] = task.result
    elif task.state == 'FAILURE':
        response_data['result'] = task.result # Include error info on failure
        
    return jsonify(response_data)
