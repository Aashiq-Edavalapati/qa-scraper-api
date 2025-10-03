import wikipediaapi
import requests # <-- Moved import to the top
from playwright.sync_api import sync_playwright
import trafilatura
from serpapi import SerpApiClient

def get_wikipedia_data(topic: str) -> str:
    """Fetches the full text content of a Wikipedia page for a given topic."""
    wiki_api = wikipediaapi.Wikipedia(
        language='en',
        user_agent='QADatasetGenerator/1.0 (aashiqedavalapati.vercel.app)'
    )
    page = wiki_api.page(topic)
    if not page.exists():
        print(f"Page '{topic}' does not exist on Wikipedia.")
        return f"ERROR: Could not find a Wikipedia page for '{topic}'."
    print(f"Successfully fetched page: {page.title}")
    return page.text

def _scrape_article_content(url: str) -> str:
    """
    Helper function to download, clean, and extract main content from a URL
    using Playwright to support JavaScript-heavy sites. Refactored for clarity.
    """
    print(f"Starting Playwright scrape for URL: {url}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(user_agent='QADatasetGenerator/1.0')
            # Add a 30-second timeout to the page navigation
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            html = page.content()
            cleaned_text = trafilatura.extract(html)
            
            if cleaned_text:
                print(f"Successfully scraped content from: {url}")
                return cleaned_text
            else:
                print(f"Failed to extract any content from: {url}")
                return ""
        except Exception as e:
            print(f"An error occurred during Playwright scrape of {url}: {e}")
            return ""
        finally:
            # Ensure the browser is always closed
            browser.close()

def get_gnews_data(topic: str, api_key: str) -> str:
    """Fetches news articles for a topic from GNews and scrapes their content."""
    if not api_key:
        return "ERROR: GNews API Key is not configured."

    url = f"https://gnews.io/api/v4/search?q={topic}&lang=en&max=5&apikey={api_key}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        articles = response.json().get('articles', [])
        if not articles:
            return "No news articles found for this topic."
        
        all_article_text = []
        print(f"Found {len(articles)} articles. Scraping with Playwright...")
        for article in articles:
            content = _scrape_article_content(article['url'])
            if content:
                all_article_text.append(content)
        return "\n\n---\n\n".join(all_article_text)
    except requests.RequestException as e:
        return f"ERROR: Could not connect to GNews API: {e}"

def get_serpapi_data(topic: str, api_key: str) -> str:
    """Performs a Google search via SerpAPI and scrapes the top results."""
    if not api_key:
        return "ERROR: SerpAPI Key was not provided."

    print(f"Performing SerpAPI search for: {topic}")
    try:
        params = {"q": topic, "engine": "google", "api_key": api_key}
        client = SerpApiClient(params)
        results = client.get_dict()
        
        organic_results = results.get("organic_results", [])
        if not organic_results:
            return "No web results found for this topic via SerpAPI."
            
        all_web_text = []
        print(f"Found {len(organic_results)} web results. Scraping top 3 with Playwright...")
        for result in organic_results[:3]:
            url = result.get("link")
            if url:
                content = _scrape_article_content(url)
                if content:
                    all_web_text.append(content)
        return "\n\n---\n\n".join(all_web_text)
    except Exception as e:
        return f"ERROR: An error occurred with SerpAPI: {e}"