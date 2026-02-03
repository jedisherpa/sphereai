# feed_fetcher.py
# RSS Feed Fetching and Article Extraction for Sphere CLI
# Authors: Margaret (Reliability), Linus (Systems)

import os
import json
import hashlib
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse
import time

# We'll use feedparser for RSS parsing
try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    FEEDPARSER_AVAILABLE = False

# We'll use requests for HTTP
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from . import audit
from . import feed_logic

SPHERE_DIR = os.path.expanduser("~/.sphere")
CACHE_DIR = os.path.join(SPHERE_DIR, "feed_cache")
ARTICLES_DIR = os.path.join(SPHERE_DIR, "articles")


def check_dependencies() -> Tuple[bool, str]:
    """Check if required dependencies are installed."""
    missing = []
    if not FEEDPARSER_AVAILABLE:
        missing.append("feedparser")
    if not REQUESTS_AVAILABLE:
        missing.append("requests")
    
    if missing:
        return False, f"Missing dependencies: {', '.join(missing)}. Install with: pip install {' '.join(missing)}"
    return True, "All dependencies available"


def fetch_feed(feed_url: str, timeout: int = 30) -> Tuple[bool, Dict]:
    """
    Fetch and parse an RSS feed.
    
    Args:
        feed_url: URL of the RSS feed
        timeout: Request timeout in seconds
    
    Returns:
        Tuple of (success, result_dict)
        result_dict contains 'entries' on success, 'error' on failure
    """
    deps_ok, deps_msg = check_dependencies()
    if not deps_ok:
        return False, {"error": deps_msg}
    
    try:
        audit.log_info(f"Fetching feed: {feed_url}")
        
        # Use requests to fetch with timeout, then parse
        response = requests.get(feed_url, timeout=timeout, headers={
            "User-Agent": "SphereAI/1.0 (Local RSS Reader)"
        })
        response.raise_for_status()
        
        feed = feedparser.parse(response.content)
        
        if feed.bozo and not feed.entries:
            return False, {"error": f"Failed to parse feed: {feed.bozo_exception}"}
        
        entries = []
        for entry in feed.entries:
            article = {
                "id": hashlib.md5(entry.get("link", entry.get("id", str(time.time()))).encode()).hexdigest()[:12],
                "title": entry.get("title", "Untitled"),
                "link": entry.get("link", ""),
                "published": parse_date(entry.get("published", entry.get("updated", ""))),
                "summary": clean_html(entry.get("summary", entry.get("description", ""))),
                "content": extract_content(entry),
                "author": entry.get("author", "Unknown"),
                "tags": [tag.get("term", "") for tag in entry.get("tags", [])]
            }
            entries.append(article)
        
        return True, {
            "feed_title": feed.feed.get("title", "Unknown Feed"),
            "feed_link": feed.feed.get("link", feed_url),
            "entries": entries,
            "fetched_at": datetime.utcnow().isoformat() + "Z"
        }
        
    except requests.exceptions.Timeout:
        audit.log_warning(f"Timeout fetching feed: {feed_url}")
        return False, {"error": f"Timeout fetching feed (>{timeout}s)"}
    except requests.exceptions.RequestException as e:
        audit.log_warning(f"Error fetching feed {feed_url}: {e}")
        return False, {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        audit.log_warning(f"Unexpected error fetching feed {feed_url}: {e}")
        return False, {"error": f"Unexpected error: {str(e)}"}


def parse_date(date_str: str) -> Optional[str]:
    """Parse various date formats to ISO format."""
    if not date_str:
        return None
    
    # feedparser usually provides a parsed time tuple
    try:
        import email.utils
        parsed = email.utils.parsedate_to_datetime(date_str)
        return parsed.isoformat() + "Z"
    except:
        pass
    
    # Try common formats
    formats = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.isoformat() + "Z"
        except ValueError:
            continue
    
    return date_str  # Return original if parsing fails


def clean_html(html_content: str) -> str:
    """Remove HTML tags and clean up text."""
    if not html_content:
        return ""
    
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', html_content)
    # Decode HTML entities
    import html
    clean = html.unescape(clean)
    # Normalize whitespace
    clean = re.sub(r'\s+', ' ', clean).strip()
    
    return clean


def extract_content(entry: Dict) -> str:
    """Extract the best available content from a feed entry."""
    # Try content field first (usually full article)
    if "content" in entry and entry["content"]:
        contents = entry["content"]
        if isinstance(contents, list) and contents:
            return clean_html(contents[0].get("value", ""))
    
    # Fall back to summary/description
    if "summary" in entry:
        return clean_html(entry["summary"])
    
    if "description" in entry:
        return clean_html(entry["description"])
    
    return ""


def fetch_all_feeds(since: Optional[datetime] = None, tags: Optional[List[str]] = None) -> Dict:
    """
    Fetch all configured feeds and return aggregated articles.
    
    Args:
        since: Only return articles published after this datetime
        tags: Only fetch feeds with these tags
    
    Returns:
        Dict with 'articles', 'errors', and 'stats'
    """
    feeds = feed_logic.get_feeds()
    
    if not feeds:
        return {
            "articles": [],
            "errors": [],
            "stats": {"feeds_total": 0, "feeds_success": 0, "articles_total": 0}
        }
    
    # Filter by tags if specified
    if tags:
        feeds = [f for f in feeds if any(t in f.get("tags", []) for t in tags)]
    
    all_articles = []
    errors = []
    feeds_success = 0
    
    for feed in feeds:
        success, result = fetch_feed(feed["url"])
        
        if success:
            feeds_success += 1
            for article in result["entries"]:
                # Add feed metadata to article
                article["feed_name"] = feed.get("name", "Unknown")
                article["feed_id"] = feed.get("id", "")
                article["feed_tags"] = feed.get("tags", [])
                
                # Filter by date if specified
                if since and article.get("published"):
                    try:
                        pub_date = datetime.fromisoformat(article["published"].replace("Z", "+00:00"))
                        if pub_date.replace(tzinfo=None) < since:
                            continue
                    except:
                        pass  # Include if we can't parse the date
                
                all_articles.append(article)
        else:
            errors.append({
                "feed": feed.get("name", feed["url"]),
                "error": result.get("error", "Unknown error")
            })
    
    # Sort by published date (newest first)
    all_articles.sort(key=lambda x: x.get("published", ""), reverse=True)
    
    return {
        "articles": all_articles,
        "errors": errors,
        "stats": {
            "feeds_total": len(feeds),
            "feeds_success": feeds_success,
            "articles_total": len(all_articles)
        }
    }


def cache_articles(articles: List[Dict], cache_name: str = "latest") -> str:
    """
    Cache fetched articles to disk.
    
    Args:
        articles: List of article dicts
        cache_name: Name for the cache file
    
    Returns:
        Path to the cache file
    """
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    cache_file = os.path.join(CACHE_DIR, f"{cache_name}.json")
    
    cache_data = {
        "cached_at": datetime.utcnow().isoformat() + "Z",
        "article_count": len(articles),
        "articles": articles
    }
    
    with open(cache_file, "w") as f:
        json.dump(cache_data, f, indent=2)
    
    audit.log_info(f"Cached {len(articles)} articles to {cache_file}")
    return cache_file


def load_cached_articles(cache_name: str = "latest") -> Optional[Dict]:
    """Load articles from cache."""
    cache_file = os.path.join(CACHE_DIR, f"{cache_name}.json")
    
    if not os.path.exists(cache_file):
        return None
    
    with open(cache_file, "r") as f:
        return json.load(f)


def get_cache_age(cache_name: str = "latest") -> Optional[timedelta]:
    """Get the age of a cache file."""
    cache_file = os.path.join(CACHE_DIR, f"{cache_name}.json")
    
    if not os.path.exists(cache_file):
        return None
    
    cached_data = load_cached_articles(cache_name)
    if not cached_data or "cached_at" not in cached_data:
        return None
    
    try:
        cached_at = datetime.fromisoformat(cached_data["cached_at"].replace("Z", "+00:00"))
        return datetime.utcnow().replace(tzinfo=cached_at.tzinfo) - cached_at
    except:
        return None
