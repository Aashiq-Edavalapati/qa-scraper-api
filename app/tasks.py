import os
import json
from datetime import datetime
from . import celery
from .data_fetcher import get_wikipedia_data, get_gnews_data, get_serpapi_data
from .text_cleaner import clean_wikipedia_text, clean_generic_text

@celery.task(bind=True)
def generate_qa_task(self, topic, gnews_api_key, serpapi_api_key):
    """
    Streamlined workflow for scraping and cleaning data ONLY.
    """
    print(f"Starting task for topic: {topic}")
    
    try:
        # STEP 1: Fetch and Clean Wikipedia Data
        self.update_state(state='PROGRESS', meta={'status': '1/3 - Fetching & cleaning Wikipedia...'})
        raw_wiki_text = get_wikipedia_data(topic)
        wiki_text = clean_wikipedia_text(raw_wiki_text) if not raw_wiki_text.startswith("ERROR:") else ""

        # STEP 2: Fetch and Clean GNews Data
        self.update_state(state='PROGRESS', meta={'status': '2/3 - Fetching & cleaning GNews...'})
        raw_gnews_text = get_gnews_data(topic, gnews_api_key)
        gnews_text = clean_generic_text(raw_gnews_text) if not raw_gnews_text.startswith("ERROR:") else ""
        
        # STEP 3: Fetch and Clean Web Search Data
        self.update_state(state='PROGRESS', meta={'status': '3/3 - Fetching & cleaning web search...'})
        raw_web_text = get_serpapi_data(topic, serpapi_api_key)
        web_text = clean_generic_text(raw_web_text) if not raw_web_text.startswith("ERROR:") else ""

        # Combine the CLEANED text from all sources
        combined_text = "\n\n".join(filter(None, [wiki_text, gnews_text, web_text]))
        if not combined_text.strip():
            raise ValueError("Could not retrieve any clean data for the topic from any source.")

        # Save the cleaned data to a file (useful for logging/archiving)
        task_id = self.request.id
        output_dir = os.path.join(os.getcwd(), 'results')
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, f"{task_id}.json")
        
        # This dictionary is now our FINAL result.
        # It contains everything the downstream application (on your friend's laptop) will need.
        final_result = {
            'task_id': task_id,
            'topic': topic,
            'timestamp_utc': datetime.utcnow().isoformat(),
            'sources_used': ['Wikipedia', 'GNews', 'SerpAPI'],
            'character_count': len(combined_text),
            'content': combined_text
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(final_result, f, indent=4)
        print(f"Successfully saved cleaned data to {file_path}")

        # On success, the task now returns the dictionary containing the scraped content.
        self.update_state(state='SUCCESS', meta={'status': 'Complete!'})
        return {'status': 'Task complete!', 'result': final_result} # <-- CHANGED

    except Exception as e:
        self.update_state(state='FAILURE', meta={'status': f'An error occurred: {str(e)}'})
        return {'status': 'Task Failed!'}