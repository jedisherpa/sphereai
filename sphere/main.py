"""
Main CLI entrypoint for the sphere tool.

Authors: Kent Beck, Rich Hickey, Martin Fowler
"""

import os
import sys
import subprocess
import json
from datetime import datetime
import click

from . import logic
from . import audit
from . import log_logic
from . import persona_logic
from . import test_logic
from . import feed_logic
from . import feed_fetcher
from . import feed_analyzer
from . import email_digest
from . import llm_providers

SPHERE_DIR = os.path.expanduser("~/.sphere")

def initialize_sphere_directory():
    """
    Ensures the ~/.sphere directory, its Git repository, and default personas exist.
    """
    if not os.path.exists(SPHERE_DIR):
        audit.log_info(f"Sphere directory not found. Creating at {SPHERE_DIR}")
        try:
            os.makedirs(SPHERE_DIR)
            subprocess.run(["git", "init"], cwd=SPHERE_DIR, check=True, capture_output=True)
            with open(os.path.join(SPHERE_DIR, ".gitignore"), "w") as f:
                f.write("audit.log\nfeed_cache/\nemail_config.yaml\nllm_config.yaml\n")
            audit.log_info(f"Successfully initialized Git repository in {SPHERE_DIR}")
        except (OSError, subprocess.CalledProcessError) as e:
            audit.handle_critical_failure(f"Failed to create or initialize sphere directory: {e}")
    else:
        if not os.path.isdir(os.path.join(SPHERE_DIR, ".git")):
            audit.handle_critical_failure(f"Error: {SPHERE_DIR} exists but is not a Git repository.")
    
    persona_logic.initialize_personas()
    feed_logic.initialize_feed_system()

@click.group()
def cli():
    """Sphere: A local-first agentic analysis tool."""
    audit_log_path = os.path.join(SPHERE_DIR, "audit.log")
    if not os.path.exists(SPHERE_DIR):
        os.makedirs(SPHERE_DIR, exist_ok=True)
    audit.initialize_logging(audit_log_path)

@cli.command()
@click.argument("query")
def analyze(query):
    """Run a new analysis on a complex question."""
    initialize_sphere_directory()
    audit.log_info("Starting analysis...")

    try:
        synthesis, audit_trail = logic.full_pmpe_analysis(query)
    except Exception as e:
        audit.handle_critical_failure(f"An unexpected error occurred during analysis: {e}")

    utc_now = datetime.utcnow()
    report_timestamp = utc_now.strftime("%Y%m%d_%H%M%S")
    report_filename = f"report_{report_timestamp}.md"
    report_filepath = os.path.join(SPHERE_DIR, report_filename)

    report_content = f"""# Analysis Report\n\n- **Timestamp**: {utc_now.isoformat()}Z\n- **Query**: \"{query}\"\n\n---\n\n## Synthesis\n\n{synthesis}\n\n---\n\n## Audit Trail\n\n```\n{audit_trail}\n```\n"""

    try:
        with open(report_filepath, "w") as f:
            f.write(report_content)
        audit.log_info(f"Report successfully saved to {report_filepath}")
    except IOError as e:
        audit.handle_critical_failure(f"Failed to write report file: {e}")

    try:
        subprocess.run(["git", "add", report_filename], cwd=SPHERE_DIR, check=True)
        commit_message = f"Analysis: {query[:50]}..."
        subprocess.run(["git", "commit", "-m", commit_message], cwd=SPHERE_DIR, check=True, capture_output=True)
        audit.log_info("Successfully committed report to Git log.")
    except subprocess.CalledProcessError as e:
        if "Please tell me who you are" in e.output.decode():
            audit.log_warning("Git user name and email not set. Please run: git config --global user.name \"Your Name\" and git config --global user.email \"you@example.com\"")
        else:
            audit.log_warning(f"Failed to commit report to Git. Error: {e.output.decode()}")

    click.echo(f"Analysis complete. Report saved to: {report_filepath}")

@cli.command()
@click.option("--query", "-q", help="Filter history by a keyword in the analysis query.")
@click.option("--after", help="Show history after this date (YYYY-MM-DD).")
@click.option("--before", help="Show history before this date (YYYY-MM-DD).")
@click.option("--show", help="Display the full report for a specific commit hash.")
@click.option("--limit", default=10, help="Number of entries to show.")
def log(query, after, before, show, limit):
    """Query the analysis history."""
    initialize_sphere_directory()
    if show:
        report_content = log_logic.show_report(show)
        click.echo(report_content)
    else:
        log_entries = log_logic.get_log(limit, query, after, before)
        if not log_entries:
            click.echo("No analysis history found.")
            return
        for entry in log_entries:
            styled_hash = click.style(entry["hash"][:7], fg="yellow")
            click.echo(f'[{entry["date"]}] {styled_hash} - {entry["subject"]}')

@cli.group()
def persona():
    """Manage agent personas."""
    pass

@persona.command(name="list")
def persona_list():
    """List available personas."""
    initialize_sphere_directory()
    personas = persona_logic.list_personas()
    for p in personas:
        if p["is_active"]:
            styled_name = click.style(p["name"], fg="green")
            click.echo(f"* {styled_name}")
        else:
            click.echo(f'  {p["name"]}')

@persona.command(name="use")
@click.argument("name")
def persona_use(name):
    """Set the active persona."""
    initialize_sphere_directory()
    success, message = persona_logic.use_persona(name)
    if success:
        click.echo(message)
    else:
        click.echo(click.style(message, fg="red"))

@persona.command(name="show")
@click.argument("name", required=False)
def persona_show(name):
    """Show the content of a persona."""
    initialize_sphere_directory()
    content, error = persona_logic.show_persona(name)
    if error:
        click.echo(click.style(error, fg="red"))
    else:
        click.echo(json.dumps(content, indent=2))

@cli.command()
@click.argument("agent_role")
@click.argument("query")
def test(agent_role, query):
    """Test a single agent with a specific query."""
    initialize_sphere_directory()
    success, result = test_logic.run_single_agent_test(agent_role, query)
    if success:
        click.echo(result)
    else:
        click.echo(click.style(result, fg="red"))


# ============================================================================
# FEED COMMANDS - RSS Feed Management and Analysis
# ============================================================================

@cli.group()
def feed():
    """Manage and analyze RSS feeds."""
    pass


@feed.command(name="add")
@click.argument("url")
@click.option("--name", "-n", help="Friendly name for the feed")
@click.option("--tags", "-t", multiple=True, help="Tags for categorization (can be used multiple times)")
def feed_add(url, name, tags):
    """Add a new RSS feed.
    
    Example:
        sphere feed add https://news.ycombinator.com/rss --name "Hacker News" --tags tech --tags news
    """
    initialize_sphere_directory()
    
    success, message = feed_logic.add_feed(url, name, list(tags) if tags else None)
    
    if success:
        click.echo(click.style(message, fg="green"))
    else:
        click.echo(click.style(message, fg="red"))


@feed.command(name="remove")
@click.argument("identifier")
def feed_remove(identifier):
    """Remove a feed by ID, name, or URL.
    
    Example:
        sphere feed remove "Hacker News"
        sphere feed remove abc12345
    """
    initialize_sphere_directory()
    
    success, message = feed_logic.remove_feed(identifier)
    
    if success:
        click.echo(click.style(message, fg="green"))
    else:
        click.echo(click.style(message, fg="red"))


@feed.command(name="list")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed feed information")
def feed_list(verbose):
    """List all configured feeds.
    
    Example:
        sphere feed list
        sphere feed list --verbose
    """
    initialize_sphere_directory()
    
    feeds = feed_logic.list_feeds()
    
    if not feeds:
        click.echo("No feeds configured. Add one with: sphere feed add <url>")
        return
    
    click.echo(f"\n{click.style('Configured Feeds', bold=True)} ({len(feeds)} total)\n")
    
    for feed in feeds:
        feed_id = click.style(feed.get("id", "???")[:8], fg="yellow")
        name = feed.get("name", "Unnamed")
        tags = feed.get("tags", [])
        
        if verbose:
            click.echo(f"  [{feed_id}] {name}")
            click.echo(f"      URL: {feed.get('url', 'N/A')}")
            if tags:
                click.echo(f"      Tags: {', '.join(tags)}")
            if feed.get("last_fetched"):
                click.echo(f"      Last fetched: {feed['last_fetched']}")
            click.echo()
        else:
            tags_str = f" [{', '.join(tags)}]" if tags else ""
            click.echo(f"  [{feed_id}] {name}{tags_str}")


@feed.command(name="fetch")
@click.option("--tags", "-t", multiple=True, help="Only fetch feeds with these tags")
@click.option("--since", "-s", help="Only fetch articles since (e.g., '24h', '7d', '2024-01-15')")
def feed_fetch(tags, since):
    """Fetch articles from all configured feeds.
    
    Example:
        sphere feed fetch
        sphere feed fetch --tags tech --since 24h
    """
    initialize_sphere_directory()
    
    # Check dependencies
    deps_ok, deps_msg = feed_fetcher.check_dependencies()
    if not deps_ok:
        click.echo(click.style(deps_msg, fg="red"))
        return
    
    click.echo("Fetching feeds...")
    
    since_dt = None
    if since:
        since_dt = feed_analyzer.parse_since(since)
    
    result = feed_fetcher.fetch_all_feeds(since=since_dt, tags=list(tags) if tags else None)
    
    # Show results
    stats = result["stats"]
    click.echo(f"\n{click.style('Fetch Complete', bold=True)}")
    click.echo(f"  Feeds: {stats['feeds_success']}/{stats['feeds_total']} successful")
    click.echo(f"  Articles: {stats['articles_total']} fetched")
    
    if result["errors"]:
        click.echo(f"\n{click.style('Errors:', fg='red')}")
        for err in result["errors"]:
            click.echo(f"  - {err['feed']}: {err['error']}")
    
    # Cache the results
    if result["articles"]:
        cache_path = feed_fetcher.cache_articles(result["articles"])
        click.echo(f"\nArticles cached to: {cache_path}")


@feed.command(name="analyze")
@click.option("--query", "-q", help="Analysis question (default: 'What are the key insights?')")
@click.option("--since", "-s", help="Only analyze articles since (e.g., '24h', '7d', 'today')")
@click.option("--tags", "-t", multiple=True, help="Only analyze feeds with these tags")
@click.option("--preset", "-p", help="Use a saved preset configuration")
@click.option("--no-cache", is_flag=True, help="Force fresh fetch, ignore cache")
@click.option("--email", "-e", is_flag=True, help="Send analysis as email digest")
def feed_analyze(query, since, tags, preset, no_cache, email):
    """Analyze news from RSS feeds using multi-agent synthesis.
    
    This command fetches articles from your configured feeds, clusters them
    by topic, and runs them through Sphere's multi-agent analysis engine.
    
    Examples:
        sphere feed analyze --query "What trends should founders watch?"
        sphere feed analyze --since 24h --tags tech
        sphere feed analyze --preset morning
        sphere feed analyze --preset morning --email
    """
    initialize_sphere_directory()
    
    # Check dependencies
    deps_ok, deps_msg = feed_fetcher.check_dependencies()
    if not deps_ok:
        click.echo(click.style(deps_msg, fg="red"))
        click.echo("\nInstall with: pip install feedparser requests")
        return
    
    # Check if we have feeds configured
    feeds = feed_logic.list_feeds()
    if not feeds and not preset:
        click.echo(click.style("No feeds configured.", fg="red"))
        click.echo("\nAdd feeds first:")
        click.echo("  sphere feed add https://news.ycombinator.com/rss --name 'Hacker News'")
        click.echo("  sphere feed add https://feeds.arstechnica.com/arstechnica/technology --name 'Ars Technica'")
        return
    
    click.echo(f"\n{click.style('Starting Feed Analysis', bold=True)}")
    if query:
        click.echo(f"Query: {query}")
    if since:
        click.echo(f"Since: {since}")
    if tags:
        click.echo(f"Tags: {', '.join(tags)}")
    if preset:
        click.echo(f"Preset: {preset}")
    if email:
        click.echo(f"Email: Enabled")
    click.echo()
    
    # Run the analysis
    with click.progressbar(length=3, label="Analyzing") as bar:
        bar.update(1)  # Fetching
        
        analysis_query = query or "What are the key insights, trends, and implications?"
        
        success, result = feed_analyzer.analyze_feeds(
            query=analysis_query,
            since=since,
            tags=list(tags) if tags else None,
            preset=preset,
            use_cache=not no_cache
        )
        
        bar.update(1)  # Processing
        bar.update(1)  # Complete
    
    if not success:
        click.echo(click.style(f"\nAnalysis failed: {result.get('error', 'Unknown error')}", fg="red"))
        return
    
    # Save the report
    utc_now = datetime.utcnow()
    report_timestamp = utc_now.strftime("%Y%m%d_%H%M%S")
    report_filename = f"feed_report_{report_timestamp}.md"
    report_filepath = os.path.join(SPHERE_DIR, report_filename)
    
    with open(report_filepath, "w") as f:
        f.write(result["report"])
    
    # Commit to Git
    try:
        subprocess.run(["git", "add", report_filename], cwd=SPHERE_DIR, check=True, capture_output=True)
        commit_message = f"Feed Analysis: {analysis_query[:40]}..."
        subprocess.run(["git", "commit", "-m", commit_message], cwd=SPHERE_DIR, check=True, capture_output=True)
    except subprocess.CalledProcessError:
        pass  # Git commit is optional
    
    # Display summary
    click.echo(f"\n{click.style('Analysis Complete', bold=True, fg='green')}")
    click.echo(f"  Articles analyzed: {result['article_count']}")
    click.echo(f"  Topic clusters: {result['cluster_count']}")
    click.echo(f"  Report saved to: {report_filepath}")
    
    # Send email if requested
    if email:
        click.echo(f"\n{click.style('Sending Email Digest...', bold=True)}")
        email_success, email_msg = email_digest.send_feed_report(
            report_content=result["report"],
            query=analysis_query,
            article_count=result["article_count"],
            cluster_count=result["cluster_count"]
        )
        if email_success:
            click.echo(click.style(f"  {email_msg}", fg="green"))
        else:
            click.echo(click.style(f"  {email_msg}", fg="red"))
    
    # Show synthesis preview
    click.echo(f"\n{click.style('Executive Summary', bold=True)}")
    click.echo("-" * 40)
    
    # Show first 500 chars of synthesis
    synthesis = result.get("synthesis", "")
    if len(synthesis) > 500:
        click.echo(synthesis[:500] + "...")
        click.echo(f"\n[Full report: {report_filepath}]")
    else:
        click.echo(synthesis)


# ============================================================================
# EMAIL COMMANDS - Email Digest Configuration
# ============================================================================

@feed.group(name="email")
def feed_email():
    """Configure email digest settings."""
    pass


@feed_email.command(name="setup")
@click.option("--provider", "-p", type=click.Choice(email_digest.list_smtp_presets()), help="Use preset for common email providers")
@click.option("--server", "-s", help="SMTP server hostname")
@click.option("--port", type=int, help="SMTP port (default: 587)")
@click.option("--username", "-u", help="SMTP username (usually your email)")
@click.option("--password", help="SMTP password or app password")
@click.option("--from-email", "-f", help="Sender email address")
@click.option("--to", "-t", multiple=True, required=True, help="Recipient email(s)")
def email_setup(provider, server, port, username, password, from_email, to):
    """Set up email configuration for digest delivery.
    
    Examples:
        # Using a provider preset (recommended)
        sphere feed email setup --provider gmail --username you@gmail.com --password "app-password" --to you@gmail.com
        
        # Custom SMTP server
        sphere feed email setup --server smtp.example.com --port 587 --username user --password pass --from-email sender@example.com --to recipient@example.com
    """
    initialize_sphere_directory()
    
    # Use provider preset if specified
    if provider:
        preset = email_digest.get_smtp_preset(provider)
        if preset:
            server = server or preset["smtp_server"]
            port = port or preset["smtp_port"]
            click.echo(f"\n{click.style('Provider Notes:', fg='yellow')} {preset.get('notes', '')}\n")
    
    # Validate required fields
    if not server:
        click.echo(click.style("Error: SMTP server required. Use --provider or --server", fg="red"))
        return
    
    if not username:
        click.echo(click.style("Error: Username required (--username)", fg="red"))
        return
    
    if not password:
        # Prompt for password securely
        password = click.prompt("SMTP Password", hide_input=True)
    
    from_email = from_email or username
    port = port or 587
    
    success, message = email_digest.save_email_config(
        smtp_server=server,
        smtp_port=port,
        username=username,
        password=password,
        from_email=from_email,
        to_emails=list(to),
        use_tls=True
    )
    
    if success:
        click.echo(click.style(message, fg="green"))
        
        # Test the connection
        click.echo("\nTesting connection...")
        test_success, test_msg = email_digest.test_email_connection()
        if test_success:
            click.echo(click.style(f"  {test_msg}", fg="green"))
        else:
            click.echo(click.style(f"  {test_msg}", fg="red"))
    else:
        click.echo(click.style(message, fg="red"))


@feed_email.command(name="test")
def email_test():
    """Test the email configuration by sending a test message."""
    initialize_sphere_directory()
    
    # First test the connection
    click.echo("Testing SMTP connection...")
    conn_success, conn_msg = email_digest.test_email_connection()
    
    if not conn_success:
        click.echo(click.style(f"Connection failed: {conn_msg}", fg="red"))
        return
    
    click.echo(click.style(f"  {conn_msg}", fg="green"))
    
    # Send a test email
    click.echo("\nSending test email...")
    
    test_content = f"""# SphereAI Test Email

This is a test email from your SphereAI installation.

**Timestamp:** {datetime.utcnow().isoformat()}Z

If you're reading this, your email configuration is working correctly!

---

## Next Steps

1. Add RSS feeds: `sphere feed add <url>`
2. Run an analysis: `sphere feed analyze --query "Your question"`
3. Send as digest: `sphere feed analyze --email`

---

*Your thoughts are not their training data.*
"""
    
    success, message = email_digest.send_digest(
        subject="[SphereAI] Test Email - Configuration Successful",
        markdown_content=test_content
    )
    
    if success:
        click.echo(click.style(f"  {message}", fg="green"))
    else:
        click.echo(click.style(f"  {message}", fg="red"))


@feed_email.command(name="status")
def email_status():
    """Show current email configuration status."""
    initialize_sphere_directory()
    
    config = email_digest.get_email_config()
    
    if not config:
        click.echo("No email configuration found.")
        click.echo("\nSet up with: sphere feed email setup --provider gmail --username you@gmail.com --to you@gmail.com")
        return
    
    click.echo(f"\n{click.style('Email Configuration', bold=True)}\n")
    click.echo(f"  Server: {config.get('smtp_server')}:{config.get('smtp_port')}")
    click.echo(f"  Username: {config.get('username')}")
    click.echo(f"  From: {config.get('from_email')}")
    click.echo(f"  To: {', '.join(config.get('to_emails', []))}")
    click.echo(f"  TLS: {'Enabled' if config.get('use_tls') else 'Disabled'}")
    click.echo(f"  Configured: {config.get('configured_at', 'Unknown')}")


@feed_email.command(name="delete")
@click.confirmation_option(prompt="Are you sure you want to delete the email configuration?")
def email_delete():
    """Delete email configuration."""
    initialize_sphere_directory()
    
    success, message = email_digest.delete_email_config()
    
    if success:
        click.echo(click.style(message, fg="green"))
    else:
        click.echo(click.style(message, fg="red"))


@feed_email.command(name="providers")
def email_providers():
    """List supported email provider presets."""
    click.echo(f"\n{click.style('Supported Email Providers', bold=True)}\n")
    
    for provider in email_digest.list_smtp_presets():
        preset = email_digest.get_smtp_preset(provider)
        click.echo(f"  {click.style(provider, fg='cyan')}")
        click.echo(f"    Server: {preset['smtp_server']}:{preset['smtp_port']}")
        click.echo(f"    Note: {preset.get('notes', 'N/A')}")
        click.echo()


# ============================================================================
# PRESET COMMANDS
# ============================================================================

@feed.group(name="preset")
def feed_preset():
    """Manage feed analysis presets."""
    pass


@feed_preset.command(name="save")
@click.argument("name")
@click.option("--feeds", "-f", multiple=True, help="Feed IDs or names to include")
@click.option("--query", "-q", required=True, help="Default analysis query")
@click.option("--schedule", "-s", help="Schedule (e.g., 'daily', 'weekly')")
def preset_save(name, feeds, query, schedule):
    """Save a new preset configuration.
    
    Example:
        sphere feed preset save morning --feeds tech --feeds news --query "What should I know today?"
    """
    initialize_sphere_directory()
    
    success, message = feed_logic.save_preset(name, list(feeds), query, schedule)
    
    if success:
        click.echo(click.style(message, fg="green"))
    else:
        click.echo(click.style(message, fg="red"))


@feed_preset.command(name="list")
def preset_list():
    """List all saved presets."""
    initialize_sphere_directory()
    
    presets = feed_logic.list_presets()
    
    if not presets:
        click.echo("No presets saved. Create one with: sphere feed preset save <name> --query '...'")
        return
    
    click.echo(f"\n{click.style('Saved Presets', bold=True)}\n")
    
    for preset_name in presets:
        preset = feed_logic.load_preset(preset_name)
        if preset:
            click.echo(f"  {click.style(preset_name, fg='cyan')}")
            click.echo(f"    Query: {preset.get('query', 'N/A')[:50]}...")
            if preset.get("feeds"):
                click.echo(f"    Feeds: {', '.join(preset['feeds'])}")
            if preset.get("schedule"):
                click.echo(f"    Schedule: {preset['schedule']}")
            click.echo()


@feed_preset.command(name="delete")
@click.argument("name")
def preset_delete(name):
    """Delete a preset."""
    initialize_sphere_directory()
    
    success, message = feed_logic.delete_preset(name)
    
    if success:
        click.echo(click.style(message, fg="green"))
    else:
        click.echo(click.style(message, fg="red"))


# ============================================================================
# LLM COMMANDS - Configure LLM Provider
# ============================================================================

@cli.group()
def llm():
    """Configure LLM provider for analysis."""
    pass


@llm.command(name="setup")
@click.option("--provider", "-p", type=click.Choice(llm_providers.list_provider_presets()), help="LLM provider preset")
@click.option("--api-key", "-k", help="API key (if required)")
@click.option("--model", "-m", help="Model name")
@click.option("--base-url", "-u", help="Base URL (for custom providers)")
@click.option("--timeout", "-t", type=int, default=120, help="Request timeout in seconds")
def llm_setup(provider, api_key, model, base_url, timeout):
    """Set up LLM provider for Sphere analysis.
    
    Examples:
        # Local LLM with Ollama (no API key needed)
        sphere llm setup --provider ollama --model llama3.2
        
        # Local LLM with LM Studio
        sphere llm setup --provider lmstudio --model local-model
        
        # OpenAI
        sphere llm setup --provider openai --api-key sk-xxx --model gpt-4o
        
        # Anthropic Claude
        sphere llm setup --provider anthropic --api-key sk-xxx --model claude-3-5-sonnet-20241022
        
        # Groq (fast inference)
        sphere llm setup --provider groq --api-key gsk_xxx --model llama-3.3-70b-versatile
        
        # Custom OpenAI-compatible API
        sphere llm setup --provider custom --base-url https://api.example.com/v1 --api-key xxx --model my-model
    """
    initialize_sphere_directory()
    
    if not provider:
        click.echo(click.style("Error: Provider required. Use --provider or see 'sphere llm providers'", fg="red"))
        return
    
    # Show provider notes
    preset = llm_providers.get_provider_preset(provider)
    if preset and preset.get("notes"):
        click.echo(f"\n{click.style('Provider Notes:', fg='yellow')} {preset['notes']}\n")
    
    # Prompt for API key if required but not provided
    if provider not in ["ollama", "lmstudio"] and not api_key:
        api_key = click.prompt("API Key", hide_input=True)
    
    success, message = llm_providers.save_llm_config(
        provider=provider,
        api_key=api_key,
        model=model,
        base_url=base_url,
        timeout=timeout
    )
    
    if success:
        click.echo(click.style(message, fg="green"))
        
        # Test the connection
        click.echo("\nTesting connection...")
        llm = llm_providers.get_provider()
        if llm:
            test_success, test_msg = llm.test_connection()
            if test_success:
                click.echo(click.style(f"  {test_msg}", fg="green"))
            else:
                click.echo(click.style(f"  {test_msg}", fg="red"))
    else:
        click.echo(click.style(message, fg="red"))


@llm.command(name="test")
@click.option("--query", "-q", default="What is 2+2? Reply with just the number.", help="Test query")
def llm_test(query):
    """Test the LLM connection with a simple query."""
    initialize_sphere_directory()
    
    status = llm_providers.get_llm_status()
    if not status["configured"]:
        click.echo(click.style(status["message"], fg="red"))
        return
    
    click.echo(f"Testing {status['provider']} ({status['model']})...\n")
    
    messages = [{"role": "user", "content": query}]
    success, response = llm_providers.call_llm(messages)
    
    if success:
        click.echo(click.style("Response:", bold=True))
        click.echo(response)
    else:
        click.echo(click.style(f"Error: {response}", fg="red"))


@llm.command(name="status")
def llm_status():
    """Show current LLM configuration."""
    initialize_sphere_directory()
    
    status = llm_providers.get_llm_status()
    
    if not status["configured"]:
        click.echo("No LLM configured.")
        click.echo("\nSet up with: sphere llm setup --provider <provider>")
        click.echo("\nAvailable providers:")
        for p in llm_providers.list_provider_presets():
            click.echo(f"  - {p}")
        return
    
    click.echo(f"\n{click.style('LLM Configuration', bold=True)}\n")
    click.echo(f"  Provider: {status['provider']}")
    click.echo(f"  Model: {status['model']}")
    click.echo(f"  Base URL: {status['base_url']}")
    click.echo(f"  Type: {status['type']}")
    click.echo(f"  Configured: {status['configured_at']}")


@llm.command(name="providers")
def llm_providers_list():
    """List available LLM provider presets."""
    click.echo(f"\n{click.style('Available LLM Providers', bold=True)}\n")
    
    click.echo(click.style("Local (No API Key Required):", fg="green"))
    for provider in ["ollama", "lmstudio"]:
        preset = llm_providers.get_provider_preset(provider)
        click.echo(f"  {click.style(provider, fg='cyan')}")
        click.echo(f"    URL: {preset['base_url']}")
        click.echo(f"    Model: {preset['default_model']}")
        click.echo(f"    Note: {preset.get('notes', 'N/A')}")
        click.echo()
    
    click.echo(click.style("Cloud (API Key Required):", fg="yellow"))
    for provider in ["openai", "anthropic", "groq", "together", "openrouter", "deepseek", "morpheus"]:
        preset = llm_providers.get_provider_preset(provider)
        if preset:
            click.echo(f"  {click.style(provider, fg='cyan')}")
            click.echo(f"    URL: {preset['base_url']}")
            click.echo(f"    Model: {preset['default_model']}")
            click.echo(f"    Note: {preset.get('notes', 'N/A')}")
            click.echo()


@llm.command(name="models")
def llm_models():
    """List available models from the configured provider (if supported)."""
    initialize_sphere_directory()
    
    status = llm_providers.get_llm_status()
    if not status["configured"]:
        click.echo(click.style("No LLM configured. Run: sphere llm setup --provider <provider>", fg="red"))
        return
    
    llm = llm_providers.get_provider()
    if not llm:
        click.echo(click.style("Could not initialize provider.", fg="red"))
        return
    
    if hasattr(llm, 'list_models'):
        click.echo(f"Fetching models from {status['provider']}...\n")
        success, models = llm.list_models()
        
        if success and models:
            click.echo(f"{click.style('Available Models:', bold=True)}\n")
            for model in models[:20]:  # Limit to 20
                if model == status['model']:
                    click.echo(f"  * {click.style(model, fg='green')} (current)")
                else:
                    click.echo(f"    {model}")
            if len(models) > 20:
                click.echo(f"\n  ...and {len(models) - 20} more")
        else:
            click.echo("Could not fetch model list. This provider may not support model listing.")
    else:
        click.echo("This provider does not support model listing.")


@llm.command(name="delete")
@click.confirmation_option(prompt="Are you sure you want to delete the LLM configuration?")
def llm_delete():
    """Delete LLM configuration."""
    initialize_sphere_directory()
    
    success, message = llm_providers.delete_llm_config()
    
    if success:
        click.echo(click.style(message, fg="green"))
    else:
        click.echo(click.style(message, fg="red"))


if __name__ == "__main__":
    cli()
