# email_digest.py
# Email Digest Output for Sphere CLI Feed Analysis
# Authors: Grace (Integration), Margaret (Reliability)

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional, Tuple, Dict
import yaml

from . import audit

SPHERE_DIR = os.path.expanduser("~/.sphere")
EMAIL_CONFIG_FILE = os.path.join(SPHERE_DIR, "email_config.yaml")


def get_email_config() -> Optional[Dict]:
    """Load email configuration from file."""
    if not os.path.exists(EMAIL_CONFIG_FILE):
        return None
    
    with open(EMAIL_CONFIG_FILE, "r") as f:
        return yaml.safe_load(f)


def save_email_config(
    smtp_server: str,
    smtp_port: int,
    username: str,
    password: str,
    from_email: str,
    to_emails: list,
    use_tls: bool = True
) -> Tuple[bool, str]:
    """
    Save email configuration.
    
    Args:
        smtp_server: SMTP server hostname (e.g., smtp.gmail.com)
        smtp_port: SMTP port (typically 587 for TLS, 465 for SSL)
        username: SMTP username (usually your email)
        password: SMTP password or app-specific password
        from_email: Sender email address
        to_emails: List of recipient email addresses
        use_tls: Whether to use TLS encryption
    
    Returns:
        Tuple of (success, message)
    """
    config = {
        "smtp_server": smtp_server,
        "smtp_port": smtp_port,
        "username": username,
        "password": password,
        "from_email": from_email,
        "to_emails": to_emails,
        "use_tls": use_tls,
        "configured_at": datetime.utcnow().isoformat() + "Z"
    }
    
    os.makedirs(SPHERE_DIR, exist_ok=True)
    
    with open(EMAIL_CONFIG_FILE, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
    
    # Set restrictive permissions on the config file (contains password)
    os.chmod(EMAIL_CONFIG_FILE, 0o600)
    
    audit.log_info(f"Email configuration saved to {EMAIL_CONFIG_FILE}")
    return True, f"Email configuration saved. Recipients: {', '.join(to_emails)}"


def delete_email_config() -> Tuple[bool, str]:
    """Delete email configuration."""
    if not os.path.exists(EMAIL_CONFIG_FILE):
        return False, "No email configuration found."
    
    os.remove(EMAIL_CONFIG_FILE)
    audit.log_info("Email configuration deleted")
    return True, "Email configuration deleted."


def test_email_connection() -> Tuple[bool, str]:
    """Test the email connection without sending."""
    config = get_email_config()
    if not config:
        return False, "No email configuration found. Run: sphere feed email setup"
    
    try:
        if config.get("use_tls", True):
            context = ssl.create_default_context()
            server = smtplib.SMTP(config["smtp_server"], config["smtp_port"])
            server.starttls(context=context)
        else:
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(config["smtp_server"], config["smtp_port"], context=context)
        
        server.login(config["username"], config["password"])
        server.quit()
        
        return True, f"Connection successful! Ready to send to: {', '.join(config['to_emails'])}"
    
    except smtplib.SMTPAuthenticationError:
        return False, "Authentication failed. Check your username and password."
    except smtplib.SMTPConnectError:
        return False, f"Could not connect to {config['smtp_server']}:{config['smtp_port']}"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"


def markdown_to_html(markdown_text: str) -> str:
    """Convert markdown to simple HTML for email."""
    import re
    
    html = markdown_text
    
    # Headers
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    
    # Bold and italic
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    
    # Links
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)
    
    # Lists
    html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    
    # Code blocks
    html = re.sub(r'```\n?(.*?)\n?```', r'<pre style="background:#f4f4f4;padding:10px;border-radius:4px;overflow-x:auto;">\1</pre>', html, flags=re.DOTALL)
    html = re.sub(r'`([^`]+)`', r'<code style="background:#f4f4f4;padding:2px 4px;border-radius:2px;">\1</code>', html)
    
    # Horizontal rules
    html = re.sub(r'^---+$', r'<hr style="border:none;border-top:1px solid #ddd;margin:20px 0;">', html, flags=re.MULTILINE)
    
    # Paragraphs (double newlines)
    html = re.sub(r'\n\n', r'</p><p>', html)
    
    # Wrap in basic HTML structure
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #00CED1; border-bottom: 2px solid #00CED1; padding-bottom: 10px; }}
            h2 {{ color: #333; margin-top: 30px; }}
            h3 {{ color: #555; }}
            a {{ color: #00CED1; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            li {{ margin: 5px 0; }}
            .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #888; }}
        </style>
    </head>
    <body>
        <p>{html}</p>
        <div class="footer">
            <p>Generated by <strong>SphereAI</strong> - Local-First Agentic Analysis</p>
            <p>Your thoughts are not their training data.</p>
        </div>
    </body>
    </html>
    """
    
    return html


def send_digest(
    subject: str,
    markdown_content: str,
    to_emails: Optional[list] = None
) -> Tuple[bool, str]:
    """
    Send a digest email with the analysis report.
    
    Args:
        subject: Email subject line
        markdown_content: The markdown report content
        to_emails: Optional override for recipient list
    
    Returns:
        Tuple of (success, message)
    """
    config = get_email_config()
    if not config:
        return False, "No email configuration found. Run: sphere feed email setup"
    
    recipients = to_emails or config.get("to_emails", [])
    if not recipients:
        return False, "No recipients configured."
    
    # Create message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config["from_email"]
    msg["To"] = ", ".join(recipients)
    
    # Add plain text version
    text_part = MIMEText(markdown_content, "plain")
    msg.attach(text_part)
    
    # Add HTML version
    html_content = markdown_to_html(markdown_content)
    html_part = MIMEText(html_content, "html")
    msg.attach(html_part)
    
    try:
        if config.get("use_tls", True):
            context = ssl.create_default_context()
            server = smtplib.SMTP(config["smtp_server"], config["smtp_port"])
            server.starttls(context=context)
        else:
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(config["smtp_server"], config["smtp_port"], context=context)
        
        server.login(config["username"], config["password"])
        server.sendmail(config["from_email"], recipients, msg.as_string())
        server.quit()
        
        audit.log_info(f"Digest email sent to: {', '.join(recipients)}")
        return True, f"Digest sent to: {', '.join(recipients)}"
    
    except smtplib.SMTPAuthenticationError:
        audit.log_warning("Email authentication failed")
        return False, "Authentication failed. Check your credentials."
    except smtplib.SMTPRecipientsRefused:
        audit.log_warning(f"Recipients refused: {recipients}")
        return False, "Recipients refused. Check email addresses."
    except Exception as e:
        audit.log_warning(f"Failed to send email: {e}")
        return False, f"Failed to send: {str(e)}"


def send_feed_report(
    report_content: str,
    query: str,
    article_count: int,
    cluster_count: int
) -> Tuple[bool, str]:
    """
    Send a feed analysis report as an email digest.
    
    Args:
        report_content: The full markdown report
        query: The analysis query
        article_count: Number of articles analyzed
        cluster_count: Number of topic clusters
    
    Returns:
        Tuple of (success, message)
    """
    today = datetime.utcnow().strftime("%Y-%m-%d")
    subject = f"[SphereAI] Feed Analysis: {query[:50]}... ({today})"
    
    # Add a header to the report
    header = f"""# SphereAI Feed Digest

**Date:** {today}
**Query:** {query}
**Articles Analyzed:** {article_count}
**Topic Clusters:** {cluster_count}

---

"""
    
    full_content = header + report_content
    
    return send_digest(subject, full_content)


# Common SMTP configurations for easy setup
SMTP_PRESETS = {
    "gmail": {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "use_tls": True,
        "notes": "Use an App Password (not your regular password). Enable 2FA first, then create an App Password at https://myaccount.google.com/apppasswords"
    },
    "outlook": {
        "smtp_server": "smtp.office365.com",
        "smtp_port": 587,
        "use_tls": True,
        "notes": "Use your regular Outlook/Microsoft account password."
    },
    "yahoo": {
        "smtp_server": "smtp.mail.yahoo.com",
        "smtp_port": 587,
        "use_tls": True,
        "notes": "Generate an App Password at https://login.yahoo.com/account/security"
    },
    "icloud": {
        "smtp_server": "smtp.mail.me.com",
        "smtp_port": 587,
        "use_tls": True,
        "notes": "Generate an App-Specific Password at https://appleid.apple.com"
    },
    "fastmail": {
        "smtp_server": "smtp.fastmail.com",
        "smtp_port": 587,
        "use_tls": True,
        "notes": "Generate an App Password in Fastmail settings."
    },
    "protonmail": {
        "smtp_server": "smtp.protonmail.ch",
        "smtp_port": 587,
        "use_tls": True,
        "notes": "Requires ProtonMail Bridge for SMTP access."
    }
}


def get_smtp_preset(provider: str) -> Optional[Dict]:
    """Get SMTP preset configuration for a provider."""
    return SMTP_PRESETS.get(provider.lower())


def list_smtp_presets() -> list:
    """List available SMTP presets."""
    return list(SMTP_PRESETS.keys())
