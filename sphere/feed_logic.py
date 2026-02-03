# feed_logic.py
# RSS Feed Management and Analysis for Sphere CLI
# Authors: Grace (Integration), Ada (Algorithms), Linus (Systems)

import os
import json
import yaml
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from . import audit

SPHERE_DIR = os.path.expanduser("~/.sphere")
FEEDS_FILE = os.path.join(SPHERE_DIR, "feeds.yaml")
CACHE_DIR = os.path.join(SPHERE_DIR, "feed_cache")
PRESETS_DIR = os.path.join(SPHERE_DIR, "presets")


def initialize_feed_system():
    """Initialize the feed system directories and files."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs(PRESETS_DIR, exist_ok=True)
    
    if not os.path.exists(FEEDS_FILE):
        with open(FEEDS_FILE, "w") as f:
            yaml.dump({"feeds": [], "default_query": "What are the key insights and implications?"}, f)
        audit.log_info(f"Created feeds configuration at {FEEDS_FILE}")


def get_feeds() -> List[Dict]:
    """Get all configured feeds."""
    initialize_feed_system()
    
    if not os.path.exists(FEEDS_FILE):
        return []
    
    with open(FEEDS_FILE, "r") as f:
        data = yaml.safe_load(f) or {}
    
    return data.get("feeds", [])


def add_feed(url: str, name: Optional[str] = None, tags: Optional[List[str]] = None) -> Tuple[bool, str]:
    """
    Add a new RSS feed.
    
    Args:
        url: The RSS feed URL
        name: Optional friendly name for the feed
        tags: Optional list of tags for categorization
    
    Returns:
        Tuple of (success, message)
    """
    initialize_feed_system()
    
    # Load existing feeds
    with open(FEEDS_FILE, "r") as f:
        data = yaml.safe_load(f) or {"feeds": []}
    
    feeds = data.get("feeds", [])
    
    # Check for duplicates
    for feed in feeds:
        if feed.get("url") == url:
            return False, f"Feed already exists: {url}"
    
    # Generate a unique ID
    feed_id = hashlib.md5(url.encode()).hexdigest()[:8]
    
    # Auto-generate name from URL if not provided
    if not name:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        name = parsed.netloc.replace("www.", "").replace(".com", "").replace(".org", "")
    
    new_feed = {
        "id": feed_id,
        "url": url,
        "name": name,
        "tags": tags or [],
        "added": datetime.utcnow().isoformat() + "Z",
        "last_fetched": None
    }
    
    feeds.append(new_feed)
    data["feeds"] = feeds
    
    with open(FEEDS_FILE, "w") as f:
        yaml.dump(data, f, default_flow_style=False)
    
    audit.log_info(f"Added feed: {name} ({url})")
    return True, f"Added feed: {name} (ID: {feed_id})"


def remove_feed(identifier: str) -> Tuple[bool, str]:
    """
    Remove a feed by ID, name, or URL.
    
    Args:
        identifier: Feed ID, name, or URL
    
    Returns:
        Tuple of (success, message)
    """
    initialize_feed_system()
    
    with open(FEEDS_FILE, "r") as f:
        data = yaml.safe_load(f) or {"feeds": []}
    
    feeds = data.get("feeds", [])
    original_count = len(feeds)
    
    # Find and remove the feed
    feeds = [f for f in feeds if not (
        f.get("id") == identifier or 
        f.get("name", "").lower() == identifier.lower() or 
        f.get("url") == identifier
    )]
    
    if len(feeds) == original_count:
        return False, f"Feed not found: {identifier}"
    
    data["feeds"] = feeds
    
    with open(FEEDS_FILE, "w") as f:
        yaml.dump(data, f, default_flow_style=False)
    
    audit.log_info(f"Removed feed: {identifier}")
    return True, f"Removed feed: {identifier}"


def list_feeds() -> List[Dict]:
    """List all configured feeds with their metadata."""
    return get_feeds()


def get_feed_by_identifier(identifier: str) -> Optional[Dict]:
    """Get a feed by ID, name, or URL."""
    feeds = get_feeds()
    for feed in feeds:
        if (feed.get("id") == identifier or 
            feed.get("name", "").lower() == identifier.lower() or 
            feed.get("url") == identifier):
            return feed
    return None


# Preset Management

def save_preset(name: str, feed_ids: List[str], query: str, schedule: Optional[str] = None) -> Tuple[bool, str]:
    """
    Save a feed preset for quick access.
    
    Args:
        name: Preset name
        feed_ids: List of feed IDs or names to include
        query: Default analysis query for this preset
        schedule: Optional cron-style schedule (e.g., "daily", "weekly")
    
    Returns:
        Tuple of (success, message)
    """
    initialize_feed_system()
    
    preset = {
        "name": name,
        "feeds": feed_ids,
        "query": query,
        "schedule": schedule,
        "created": datetime.utcnow().isoformat() + "Z"
    }
    
    preset_file = os.path.join(PRESETS_DIR, f"{name}.yaml")
    
    with open(preset_file, "w") as f:
        yaml.dump(preset, f, default_flow_style=False)
    
    audit.log_info(f"Saved preset: {name}")
    return True, f"Saved preset: {name}"


def load_preset(name: str) -> Optional[Dict]:
    """Load a preset by name."""
    preset_file = os.path.join(PRESETS_DIR, f"{name}.yaml")
    
    if not os.path.exists(preset_file):
        return None
    
    with open(preset_file, "r") as f:
        return yaml.safe_load(f)


def list_presets() -> List[str]:
    """List all available presets."""
    initialize_feed_system()
    
    if not os.path.exists(PRESETS_DIR):
        return []
    
    presets = []
    for filename in os.listdir(PRESETS_DIR):
        if filename.endswith(".yaml"):
            presets.append(filename[:-5])  # Remove .yaml extension
    
    return sorted(presets)


def delete_preset(name: str) -> Tuple[bool, str]:
    """Delete a preset by name."""
    preset_file = os.path.join(PRESETS_DIR, f"{name}.yaml")
    
    if not os.path.exists(preset_file):
        return False, f"Preset not found: {name}"
    
    os.remove(preset_file)
    audit.log_info(f"Deleted preset: {name}")
    return True, f"Deleted preset: {name}"
