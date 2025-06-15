import os
import requests
from bs4 import BeautifulSoup
import logging

def web_search(query: str, num_results: int = 3) -> str:
    """Performs a web search using Google Custom Search API and summarizes the top result's main content."""
    logger = logging.getLogger("WebSearchTool")
    api_key = os.environ.get("GOOGLE_CSE_API_KEY")
    cse_id = os.environ.get("GOOGLE_CSE_ID")
    if not api_key or not cse_id:
        return "Google Custom Search API key or CSE ID not set. Please set GOOGLE_CSE_API_KEY and GOOGLE_CSE_ID in your environment."
    search_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cse_id,
        "q": query,
        "num": num_results
    }
    try:
        resp = requests.get(search_url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", [])
        if not items:
            logger.warning(f"[Google CSE] No results found for '{query}'.")
            return "No web results found."
        url = items[0]["link"]
        logger.info(f"[Google CSE] Top result for '{query}': {url}")
        # Fetch and summarize the main content from the first result
        page = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        page.raise_for_status()
        soup = BeautifulSoup(page.text, "html.parser")
        paragraphs = soup.find_all('p')
        text = '\n'.join(p.get_text() for p in paragraphs if len(p.get_text()) > 40)
        if not text:
            text = soup.get_text()
        summary = text[:1000] if text else "No readable content found."
        return summary
    except Exception as e:
        logger.error(f"[Google CSE] Search or content extraction failed for '{query}': {e}")
        return f"Web search failed: {e}"

"""
Setup instructions:
- Get a Google API key: https://console.developers.google.com/
- Create a Custom Search Engine (CSE): https://cse.google.com/cse/all
- Set environment variables GOOGLE_CSE_API_KEY and GOOGLE_CSE_ID with your credentials.
"""
