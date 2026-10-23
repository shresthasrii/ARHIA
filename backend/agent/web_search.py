import re
import urllib.parse
import logging
import requests
from typing import Dict, Any, List, Optional

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

logger = logging.getLogger("ARHIEA.WebSearch")

def get_entity_wiki_summary(query: str) -> Optional[str]:
    """Fetches high-accuracy summary from Wikipedia API for people, places, concepts, or entities."""
    clean = re.sub(r"^(who is|who was|what is|what was|where is|tell me about|explain)\s+", "", query, flags=re.IGNORECASE).strip().rstrip("?.!")
    if not clean:
        return None

    try:
        title_encoded = urllib.parse.quote(clean.replace(" ", "_"))
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title_encoded}"
        resp = requests.get(url, headers={"User-Agent": "ARHIEA-Assistant/1.0"}, timeout=3.5)
        if resp.status_code == 200:
            data = resp.json()
            extract = data.get("extract")
            if extract and len(extract) > 20:
                sentences = extract.split(". ")
                return ". ".join(sentences[:2]) + ("." if not sentences[0].endswith(".") else "")
    except Exception as e:
        logger.debug(f"Wikipedia summary lookup notice: {e}")
    return None

def search_web_summary(query: str, max_results: int = 3) -> Dict[str, Any]:
    """Searches the live web via Wikipedia and DuckDuckGo for factual, biographical, or real-time questions."""
    wiki_summary = get_entity_wiki_summary(query)
    if wiki_summary:
        return {
            "success": True,
            "query": query,
            "summary": wiki_summary,
            "message": wiki_summary
        }

    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                body = r.get("body", "")
                if body:
                    results.append({
                        "title": r.get("title", ""),
                        "snippet": body,
                        "href": r.get("href", "")
                    })

        if not results:
            return {
                "success": False,
                "query": query,
                "message": f"I couldn't find information regarding '{query}'."
            }

        top_snippet = results[0]["snippet"]
        return {
            "success": True,
            "query": query,
            "results": results,
            "summary": top_snippet,
            "message": top_snippet
        }
    except Exception as e:
        logger.debug(f"Web search error: {e}")
        return {
            "success": False,
            "query": query,
            "error": str(e),
            "message": f"Could not retrieve web information at this time."
        }
