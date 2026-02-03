# feed_analyzer.py
# Feed Analysis with Clustering and Multi-Agent Synthesis for Sphere CLI
# Authors: Ada (Algorithms), Alan (Theory), Dijkstra (Semantics)

import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

from . import audit
from . import logic
from . import feed_logic
from . import feed_fetcher

SPHERE_DIR = os.path.expanduser("~/.sphere")


def cluster_articles_by_topic(articles: List[Dict], max_clusters: int = 10) -> List[Dict]:
    """
    Cluster articles by topic using simple keyword extraction.
    
    This is a lightweight clustering approach that doesn't require ML dependencies.
    For production, you could integrate sentence-transformers for semantic clustering.
    
    Args:
        articles: List of article dicts
        max_clusters: Maximum number of topic clusters
    
    Returns:
        List of cluster dicts with 'topic', 'keywords', 'articles'
    """
    if not articles:
        return []
    
    # Extract keywords from each article
    from collections import Counter
    import re
    
    # Common stop words to filter out
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare', 'ought',
        'used', 'it', 'its', 'this', 'that', 'these', 'those', 'i', 'you', 'he',
        'she', 'we', 'they', 'what', 'which', 'who', 'whom', 'whose', 'where',
        'when', 'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more',
        'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
        'same', 'so', 'than', 'too', 'very', 'just', 'also', 'now', 'new',
        'one', 'two', 'first', 'last', 'long', 'great', 'little', 'own', 'other',
        'old', 'right', 'big', 'high', 'different', 'small', 'large', 'next',
        'early', 'young', 'important', 'few', 'public', 'bad', 'same', 'able'
    }
    
    def extract_keywords(text: str, top_n: int = 10) -> List[str]:
        """Extract top keywords from text."""
        # Tokenize and clean
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        # Filter stop words
        words = [w for w in words if w not in stop_words]
        # Count and return top N
        counts = Counter(words)
        return [word for word, _ in counts.most_common(top_n)]
    
    # Build keyword vectors for each article
    article_keywords = []
    for article in articles:
        text = f"{article.get('title', '')} {article.get('summary', '')} {article.get('content', '')}"
        keywords = extract_keywords(text)
        article_keywords.append({
            "article": article,
            "keywords": set(keywords)
        })
    
    # Simple clustering: group articles with overlapping keywords
    clusters = []
    used_articles = set()
    
    for i, item in enumerate(article_keywords):
        if i in used_articles:
            continue
        
        cluster_articles = [item["article"]]
        cluster_keywords = item["keywords"].copy()
        used_articles.add(i)
        
        # Find similar articles
        for j, other_item in enumerate(article_keywords):
            if j in used_articles:
                continue
            
            # Calculate keyword overlap
            overlap = len(item["keywords"] & other_item["keywords"])
            if overlap >= 2:  # At least 2 keywords in common
                cluster_articles.append(other_item["article"])
                cluster_keywords |= other_item["keywords"]
                used_articles.add(j)
        
        # Generate topic label from most common keywords
        all_text = " ".join([
            f"{a.get('title', '')} {a.get('summary', '')}" 
            for a in cluster_articles
        ])
        topic_keywords = extract_keywords(all_text, top_n=3)
        topic_label = " / ".join(topic_keywords).title() if topic_keywords else "General News"
        
        clusters.append({
            "topic": topic_label,
            "keywords": list(cluster_keywords)[:10],
            "articles": cluster_articles,
            "article_count": len(cluster_articles)
        })
    
    # Sort by article count (largest clusters first) and limit
    clusters.sort(key=lambda x: x["article_count"], reverse=True)
    return clusters[:max_clusters]


def summarize_cluster(cluster: Dict) -> str:
    """
    Create a summary of a cluster for analysis.
    
    Args:
        cluster: Cluster dict with 'topic', 'articles'
    
    Returns:
        Summary string suitable for multi-agent analysis
    """
    articles = cluster["articles"]
    topic = cluster["topic"]
    
    summary_parts = [f"## Topic: {topic}\n"]
    summary_parts.append(f"*{len(articles)} articles in this cluster*\n")
    
    for i, article in enumerate(articles[:5], 1):  # Limit to 5 articles per cluster
        summary_parts.append(f"\n### Article {i}: {article.get('title', 'Untitled')}")
        summary_parts.append(f"*Source: {article.get('feed_name', 'Unknown')}*")
        if article.get('published'):
            summary_parts.append(f"*Published: {article['published'][:10]}*")
        
        # Include summary or truncated content
        content = article.get('summary', '') or article.get('content', '')
        if len(content) > 500:
            content = content[:500] + "..."
        summary_parts.append(f"\n{content}\n")
    
    if len(articles) > 5:
        summary_parts.append(f"\n*...and {len(articles) - 5} more articles on this topic*")
    
    return "\n".join(summary_parts)


def analyze_feeds(
    query: str,
    since: Optional[str] = None,
    tags: Optional[List[str]] = None,
    preset: Optional[str] = None,
    use_cache: bool = True,
    max_age_hours: int = 1
) -> Tuple[bool, Dict]:
    """
    Fetch feeds, cluster articles, and run multi-agent analysis.
    
    Args:
        query: The analysis question to ask about the news
        since: Only analyze articles from this time period (e.g., "24h", "7d", "2024-01-15")
        tags: Only analyze feeds with these tags
        preset: Use a saved preset configuration
        use_cache: Whether to use cached articles if available
        max_age_hours: Maximum cache age in hours before re-fetching
    
    Returns:
        Tuple of (success, result_dict)
    """
    audit.log_info(f"Starting feed analysis with query: {query}")
    
    # Load preset if specified
    if preset:
        preset_config = feed_logic.load_preset(preset)
        if not preset_config:
            return False, {"error": f"Preset not found: {preset}"}
        
        # Override parameters from preset
        if not query and preset_config.get("query"):
            query = preset_config["query"]
        if preset_config.get("feeds"):
            tags = preset_config["feeds"]  # Preset feeds act as tag filter
    
    if not query:
        query = "What are the key insights, trends, and implications from this news?"
    
    # Parse the 'since' parameter
    since_datetime = None
    if since:
        since_datetime = parse_since(since)
    
    # Check cache
    cache_name = f"feed_analysis_{hashlib.md5(str(tags or 'all').encode()).hexdigest()[:8]}"
    
    if use_cache:
        cache_age = feed_fetcher.get_cache_age(cache_name)
        if cache_age and cache_age < timedelta(hours=max_age_hours):
            audit.log_info(f"Using cached articles (age: {cache_age})")
            cached = feed_fetcher.load_cached_articles(cache_name)
            articles = cached.get("articles", [])
        else:
            # Fetch fresh
            result = feed_fetcher.fetch_all_feeds(since=since_datetime, tags=tags)
            articles = result["articles"]
            
            if result["errors"]:
                for err in result["errors"]:
                    audit.log_warning(f"Feed error: {err['feed']} - {err['error']}")
            
            # Cache the results
            feed_fetcher.cache_articles(articles, cache_name)
    else:
        result = feed_fetcher.fetch_all_feeds(since=since_datetime, tags=tags)
        articles = result["articles"]
    
    if not articles:
        return False, {"error": "No articles found. Add feeds with 'sphere feed add <url>'"}
    
    audit.log_info(f"Analyzing {len(articles)} articles")
    
    # Cluster articles by topic
    clusters = cluster_articles_by_topic(articles)
    audit.log_info(f"Created {len(clusters)} topic clusters")
    
    # Build the analysis input
    analysis_input = build_analysis_input(query, clusters)
    
    # Run through the Sphere multi-agent analysis
    try:
        synthesis, audit_trail = logic.full_pmpe_analysis(analysis_input)
    except Exception as e:
        return False, {"error": f"Analysis failed: {str(e)}"}
    
    # Build the final report
    report = build_feed_report(query, clusters, synthesis, audit_trail, articles)
    
    return True, {
        "report": report,
        "clusters": clusters,
        "article_count": len(articles),
        "cluster_count": len(clusters),
        "synthesis": synthesis
    }


def parse_since(since_str: str) -> Optional[datetime]:
    """Parse a 'since' string into a datetime."""
    now = datetime.utcnow()
    
    # Handle relative times like "24h", "7d", "1w"
    import re
    match = re.match(r'^(\d+)([hdwm])$', since_str.lower())
    if match:
        value = int(match.group(1))
        unit = match.group(2)
        
        if unit == 'h':
            return now - timedelta(hours=value)
        elif unit == 'd':
            return now - timedelta(days=value)
        elif unit == 'w':
            return now - timedelta(weeks=value)
        elif unit == 'm':
            return now - timedelta(days=value * 30)
    
    # Handle date strings
    try:
        return datetime.fromisoformat(since_str)
    except:
        pass
    
    # Handle "today", "yesterday"
    if since_str.lower() == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif since_str.lower() == "yesterday":
        return (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    return None


def build_analysis_input(query: str, clusters: List[Dict]) -> str:
    """Build the input text for multi-agent analysis."""
    parts = [
        f"# Feed Analysis Request\n",
        f"**Query:** {query}\n",
        f"**Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n",
        f"**Topics:** {len(clusters)} clusters identified\n",
        "\n---\n",
        "# News Summary by Topic\n"
    ]
    
    for cluster in clusters:
        parts.append(summarize_cluster(cluster))
        parts.append("\n---\n")
    
    parts.append(f"\n# Analysis Request\n")
    parts.append(f"Based on the above news summary, please analyze: **{query}**\n")
    
    return "\n".join(parts)


def build_feed_report(
    query: str,
    clusters: List[Dict],
    synthesis: str,
    audit_trail: str,
    articles: List[Dict]
) -> str:
    """Build the final markdown report."""
    report_parts = [
        f"# Feed Analysis Report\n",
        f"- **Generated:** {datetime.utcnow().isoformat()}Z",
        f"- **Query:** {query}",
        f"- **Articles Analyzed:** {len(articles)}",
        f"- **Topic Clusters:** {len(clusters)}",
        "\n---\n",
        "## Executive Summary\n",
        synthesis,
        "\n---\n",
        "## Topics Covered\n"
    ]
    
    for i, cluster in enumerate(clusters, 1):
        report_parts.append(f"\n### {i}. {cluster['topic']}")
        report_parts.append(f"*{cluster['article_count']} articles*\n")
        
        # List article titles
        for article in cluster['articles'][:3]:
            report_parts.append(f"- [{article.get('title', 'Untitled')}]({article.get('link', '#')})")
        
        if cluster['article_count'] > 3:
            report_parts.append(f"- *...and {cluster['article_count'] - 3} more*")
    
    report_parts.append("\n---\n")
    report_parts.append("## Sources\n")
    
    # List unique sources
    sources = set()
    for article in articles:
        sources.add(article.get('feed_name', 'Unknown'))
    
    for source in sorted(sources):
        report_parts.append(f"- {source}")
    
    report_parts.append("\n---\n")
    report_parts.append("## Audit Trail\n")
    report_parts.append(f"```\n{audit_trail}\n```\n")
    
    return "\n".join(report_parts)
