# Sphere CLI (v0.5.0)

`sphere` is a local-first, command-line tool for running complex analyses using a multi-agent workflow. It connects to any LLM provider — local or cloud — and runs your queries through multiple AI perspectives to produce synthesized insights.

## Philosophy

This tool is built on the principles of:

- **Local-First**: All your data and analyses live on your machine in a Git-based log.
- **Provider Agnostic**: Works with Ollama, LM Studio, OpenAI, Anthropic, Groq, and more.
- **Transparency**: The entire process is logged and auditable.
- **Sovereignty**: Your thoughts are not their training data.

## Installation

```bash
# Clone or download the project
cd sphere_cli

# Install the tool
pip install -e .
```

## Quick Start

```bash
# 1. Configure your LLM (choose one)

# Option A: Local LLM with Ollama (free, private)
sphere llm setup --provider ollama --model llama3.2

# Option B: OpenAI (requires API key)
sphere llm setup --provider openai --api-key sk-xxx --model gpt-4o

# Option C: Anthropic Claude
sphere llm setup --provider anthropic --api-key sk-xxx

# 2. Run an analysis
sphere analyze "What are the implications of quantum computing for cryptography?"

# 3. View your analysis history
sphere log
```

---

## LLM Configuration (New in v0.5.0)

Sphere now supports real LLM integration with multiple providers.

### `sphere llm setup`

Configure your LLM provider.

```bash
# Local LLMs (no API key required)
sphere llm setup --provider ollama --model llama3.2
sphere llm setup --provider lmstudio --model local-model

# Cloud Providers (API key required)
sphere llm setup --provider openai --api-key sk-xxx --model gpt-4o
sphere llm setup --provider anthropic --api-key sk-xxx --model claude-3-5-sonnet-20241022
sphere llm setup --provider groq --api-key gsk_xxx --model llama-3.3-70b-versatile
sphere llm setup --provider together --api-key xxx --model meta-llama/Llama-3.3-70B-Instruct-Turbo
sphere llm setup --provider openrouter --api-key xxx --model anthropic/claude-3.5-sonnet
sphere llm setup --provider deepseek --api-key xxx --model deepseek-chat
sphere llm setup --provider morpheus --api-key xxx --model morpheus-default

# Custom OpenAI-compatible API
sphere llm setup --provider custom --base-url https://api.example.com/v1 --api-key xxx --model my-model
```

### `sphere llm status`

Check current LLM configuration.

```bash
sphere llm status
```

### `sphere llm test`

Test the LLM connection.

```bash
sphere llm test
sphere llm test --query "Explain quantum entanglement in one sentence."
```

### `sphere llm providers`

List all supported providers.

```bash
sphere llm providers
```

### `sphere llm models`

List available models (if supported by provider).

```bash
sphere llm models
```

### Supported Providers

| Provider | Type | Default Model | Notes |
|----------|------|---------------|-------|
| `ollama` | Local | llama3.2 | Free, private. Install from ollama.ai |
| `lmstudio` | Local | local-model | Free, private. Download from lmstudio.ai |
| `openai` | Cloud | gpt-4o | Requires API key from platform.openai.com |
| `anthropic` | Cloud | claude-3-5-sonnet | Requires API key from console.anthropic.com |
| `groq` | Cloud | llama-3.3-70b | Fast inference. Key from console.groq.com |
| `together` | Cloud | Llama-3.3-70B | Key from api.together.xyz |
| `openrouter` | Cloud | claude-3.5-sonnet | Unified API. Key from openrouter.ai |
| `deepseek` | Cloud | deepseek-chat | Key from platform.deepseek.com |
| `morpheus` | Cloud | morpheus-default | Decentralized AI. Key from mor.org |

---

## Analysis Commands

### `sphere analyze <query>`

Run a full multi-agent analysis on a complex question.

```bash
sphere analyze "What is the nature of consciousness?"
```

This will:
1. Load your active persona (12 agent perspectives by default)
2. Run each agent through the configured LLM
3. Synthesize all perspectives into a final report
4. Save the report to `~/.sphere/` and commit to Git

### `sphere log`

Query the analysis history.

```bash
sphere log                           # Show last 10 analyses
sphere log --query "consciousness"   # Filter by keyword
sphere log --after 2026-01-01        # Filter by date
sphere log --show abc1234            # Show specific report
```

### `sphere persona`

Manage agent personas.

```bash
sphere persona list          # List available personas
sphere persona use creative  # Switch persona
sphere persona show general  # Show persona details
```

### `sphere test <agent_role> <query>`

Test a single agent in isolation.

```bash
sphere test Rationalist "What is the nature of reality?"
```

---

## RSS Feed Commands

### `sphere feed add <url>`

Add RSS feeds to monitor.

```bash
sphere feed add https://news.ycombinator.com/rss --name "HN" --tags tech
sphere feed add https://techcrunch.com/feed/ --name "TechCrunch" --tags tech
```

### `sphere feed analyze`

Analyze news using multi-agent synthesis.

```bash
sphere feed analyze --query "What trends should founders watch?"
sphere feed analyze --since 24h --tags tech
sphere feed analyze --preset morning --email
```

### Feed Presets

```bash
sphere feed preset save morning --feeds tech --query "What should I know today?"
sphere feed preset list
sphere feed analyze --preset morning
```

---

## Email Digest Commands

### `sphere feed email setup`

Configure email delivery.

```bash
sphere feed email setup --provider gmail --username you@gmail.com --to you@gmail.com
```

### Send Analysis via Email

```bash
sphere feed analyze --preset morning --email
```

---

## The `~/.sphere` Directory

Your personal, private data store:

```
~/.sphere/
├── .git/              # Version control
├── llm_config.yaml    # LLM provider settings (600 permissions)
├── feeds.yaml         # RSS feed configuration
├── email_config.yaml  # Email settings (600 permissions)
├── feed_cache/        # Cached articles
├── presets/           # Analysis presets
├── personas/          # Agent configurations
├── report_*.md        # Analysis reports
├── feed_report_*.md   # Feed analysis reports
└── audit.log          # Audit trail
```

---

## Example Workflows

### Deep Analysis with Local LLM

```bash
# Set up Ollama (free, private)
sphere llm setup --provider ollama --model llama3.2

# Run analysis
sphere analyze "What are the second-order effects of widespread AI adoption?"
```

### Morning News Briefing

```bash
# One-time setup
sphere llm setup --provider groq --api-key gsk_xxx --model llama-3.3-70b-versatile
sphere feed add https://news.ycombinator.com/rss --name "HN" --tags tech
sphere feed preset save morning --feeds tech --query "What are the most important developments?"
sphere feed email setup --provider gmail --username you@gmail.com --to you@gmail.com

# Daily run (add to crontab)
sphere feed analyze --preset morning --email
```

### Research Analysis

```bash
# Use Claude for nuanced analysis
sphere llm setup --provider anthropic --api-key sk-xxx --model claude-3-5-sonnet-20241022

# Deep dive
sphere analyze "Compare the philosophical frameworks of Wittgenstein and Heidegger on the nature of language."
```

---

## Version History

### v0.5.0 (Current)

- **NEW:** Real LLM integration with multi-provider support
- **NEW:** `sphere llm setup/status/test/providers/models/delete` commands
- **NEW:** Support for Ollama, LM Studio, OpenAI, Anthropic, Groq, Together, OpenRouter, DeepSeek, Morpheus
- **NEW:** Custom OpenAI-compatible endpoint support
- **UPDATED:** `sphere analyze` now uses real LLM calls
- **UPDATED:** Feed analysis uses real multi-agent synthesis

### v0.4.0

- Email digest output for feed analysis
- SMTP configuration with provider presets
- `--email` flag on `sphere feed analyze`

### v0.3.0

- RSS feed management and analysis
- Article clustering by topic
- Feed presets for saved configurations

### v0.2.0

- Analysis history with `sphere log`
- Persona management
- Single agent testing

### v0.1.0

- Initial MVP with simulated analysis

---

## License

MIT License - Your intelligence, sovereign.
