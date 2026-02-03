# llm_providers.py
# LLM Provider Abstraction Layer for Sphere CLI
# Supports: Ollama, LM Studio, OpenAI, Anthropic, Morpheus, and OpenAI-compatible APIs
# Authors: Ada (Architecture), Linus (Systems)

import os
import json
import requests
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Tuple, Generator
from datetime import datetime
import yaml

from . import audit

SPHERE_DIR = os.path.expanduser("~/.sphere")
LLM_CONFIG_FILE = os.path.join(SPHERE_DIR, "llm_config.yaml")

# Default configurations for known providers
PROVIDER_PRESETS = {
    "ollama": {
        "name": "Ollama",
        "type": "openai_compatible",
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",  # Ollama doesn't require a real key
        "default_model": "llama3.2",
        "notes": "Local LLM via Ollama. Install from https://ollama.ai"
    },
    "lmstudio": {
        "name": "LM Studio",
        "type": "openai_compatible",
        "base_url": "http://localhost:1234/v1",
        "api_key": "lm-studio",  # LM Studio doesn't require a real key
        "default_model": "local-model",
        "notes": "Local LLM via LM Studio. Download from https://lmstudio.ai"
    },
    "openai": {
        "name": "OpenAI",
        "type": "openai",
        "base_url": "https://api.openai.com/v1",
        "api_key": None,  # Required
        "default_model": "gpt-4o",
        "notes": "OpenAI API. Get key at https://platform.openai.com/api-keys"
    },
    "anthropic": {
        "name": "Anthropic",
        "type": "anthropic",
        "base_url": "https://api.anthropic.com",
        "api_key": None,  # Required
        "default_model": "claude-3-5-sonnet-20241022",
        "notes": "Anthropic Claude API. Get key at https://console.anthropic.com"
    },
    "morpheus": {
        "name": "Morpheus",
        "type": "openai_compatible",
        "base_url": "https://api.mor.org/v1",
        "api_key": None,  # Required
        "default_model": "morpheus-default",
        "notes": "Morpheus decentralized AI. Get key at https://mor.org"
    },
    "groq": {
        "name": "Groq",
        "type": "openai_compatible",
        "base_url": "https://api.groq.com/openai/v1",
        "api_key": None,  # Required
        "default_model": "llama-3.3-70b-versatile",
        "notes": "Groq fast inference. Get key at https://console.groq.com"
    },
    "together": {
        "name": "Together AI",
        "type": "openai_compatible",
        "base_url": "https://api.together.xyz/v1",
        "api_key": None,  # Required
        "default_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "notes": "Together AI. Get key at https://api.together.xyz"
    },
    "openrouter": {
        "name": "OpenRouter",
        "type": "openai_compatible",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": None,  # Required
        "default_model": "anthropic/claude-3.5-sonnet",
        "notes": "OpenRouter unified API. Get key at https://openrouter.ai/keys"
    },
    "deepseek": {
        "name": "DeepSeek",
        "type": "openai_compatible",
        "base_url": "https://api.deepseek.com/v1",
        "api_key": None,  # Required
        "default_model": "deepseek-chat",
        "notes": "DeepSeek API. Get key at https://platform.deepseek.com"
    },
    "custom": {
        "name": "Custom OpenAI-Compatible",
        "type": "openai_compatible",
        "base_url": None,  # Required
        "api_key": None,  # May be required
        "default_model": None,  # Required
        "notes": "Any OpenAI-compatible API endpoint"
    }
}


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.base_url = config.get("base_url")
        self.api_key = config.get("api_key")
        self.model = config.get("model") or config.get("default_model")
        self.timeout = config.get("timeout", 120)
        self.max_tokens = config.get("max_tokens", 4096)
        self.temperature = config.get("temperature", 0.7)
    
    @abstractmethod
    def complete(self, messages: List[Dict], **kwargs) -> Tuple[bool, str]:
        """
        Send a completion request to the LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
        
        Returns:
            Tuple of (success, response_text or error_message)
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> Tuple[bool, str]:
        """Test the connection to the LLM provider."""
        pass
    
    def get_info(self) -> Dict:
        """Get provider information."""
        return {
            "provider": self.config.get("provider_name", "Unknown"),
            "model": self.model,
            "base_url": self.base_url
        }


class OpenAICompatibleProvider(LLMProvider):
    """Provider for OpenAI and OpenAI-compatible APIs (Ollama, LM Studio, Groq, etc.)."""
    
    def complete(self, messages: List[Dict], **kwargs) -> Tuple[bool, str]:
        """Send completion request to OpenAI-compatible API."""
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        # Handle OpenRouter-specific headers
        if "openrouter" in self.base_url.lower():
            headers["HTTP-Referer"] = "https://sphereai.dev"
            headers["X-Title"] = "SphereAI"
        
        payload = {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens)
        }
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return True, content
            else:
                error_msg = f"API error {response.status_code}: {response.text[:500]}"
                audit.log_warning(f"LLM request failed: {error_msg}")
                return False, error_msg
                
        except requests.exceptions.Timeout:
            return False, f"Request timed out after {self.timeout}s"
        except requests.exceptions.ConnectionError:
            return False, f"Could not connect to {self.base_url}"
        except Exception as e:
            return False, f"Request failed: {str(e)}"
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test connection by sending a simple request."""
        test_messages = [
            {"role": "user", "content": "Say 'connection successful' in exactly two words."}
        ]
        
        success, result = self.complete(test_messages, max_tokens=20)
        
        if success:
            return True, f"Connected to {self.config.get('provider_name', 'provider')}. Model: {self.model}"
        else:
            return False, result
    
    def list_models(self) -> Tuple[bool, List[str]]:
        """List available models (if supported by the API)."""
        url = f"{self.base_url}/models"
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                models = [m.get("id", m.get("name", "unknown")) for m in data.get("data", [])]
                return True, models
            else:
                return False, []
        except:
            return False, []


class AnthropicProvider(LLMProvider):
    """Provider for Anthropic Claude API."""
    
    def complete(self, messages: List[Dict], **kwargs) -> Tuple[bool, str]:
        """Send completion request to Anthropic API."""
        url = f"{self.base_url}/v1/messages"
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        # Convert messages format (Anthropic uses different format)
        system_message = None
        anthropic_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        payload = {
            "model": kwargs.get("model", self.model),
            "messages": anthropic_messages,
            "max_tokens": kwargs.get("max_tokens", self.max_tokens)
        }
        
        if system_message:
            payload["system"] = system_message
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data["content"][0]["text"]
                return True, content
            else:
                error_msg = f"API error {response.status_code}: {response.text[:500]}"
                audit.log_warning(f"Anthropic request failed: {error_msg}")
                return False, error_msg
                
        except requests.exceptions.Timeout:
            return False, f"Request timed out after {self.timeout}s"
        except requests.exceptions.ConnectionError:
            return False, f"Could not connect to Anthropic API"
        except Exception as e:
            return False, f"Request failed: {str(e)}"
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test connection to Anthropic."""
        test_messages = [
            {"role": "user", "content": "Say 'connection successful' in exactly two words."}
        ]
        
        success, result = self.complete(test_messages, max_tokens=20)
        
        if success:
            return True, f"Connected to Anthropic. Model: {self.model}"
        else:
            return False, result


def get_provider(config: Optional[Dict] = None) -> Optional[LLMProvider]:
    """
    Get an LLM provider instance based on configuration.
    
    Args:
        config: Optional config override. If None, loads from config file.
    
    Returns:
        LLMProvider instance or None if not configured
    """
    if config is None:
        config = load_llm_config()
    
    if not config:
        return None
    
    provider_type = config.get("type", "openai_compatible")
    
    if provider_type == "anthropic":
        return AnthropicProvider(config)
    else:
        return OpenAICompatibleProvider(config)


def load_llm_config() -> Optional[Dict]:
    """Load LLM configuration from file."""
    if not os.path.exists(LLM_CONFIG_FILE):
        return None
    
    try:
        with open(LLM_CONFIG_FILE, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        audit.log_warning(f"Failed to load LLM config: {e}")
        return None


def save_llm_config(
    provider: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    **kwargs
) -> Tuple[bool, str]:
    """
    Save LLM configuration.
    
    Args:
        provider: Provider name (ollama, openai, anthropic, etc.)
        api_key: API key (if required)
        model: Model name override
        base_url: Base URL override
        **kwargs: Additional configuration options
    
    Returns:
        Tuple of (success, message)
    """
    preset = PROVIDER_PRESETS.get(provider.lower())
    
    if not preset and provider.lower() != "custom":
        return False, f"Unknown provider: {provider}. Use 'sphere llm providers' to list available providers."
    
    # Build configuration
    config = {
        "provider": provider.lower(),
        "provider_name": preset["name"] if preset else "Custom",
        "type": preset["type"] if preset else "openai_compatible",
        "base_url": base_url or (preset["base_url"] if preset else None),
        "api_key": api_key or (preset["api_key"] if preset else None),
        "model": model or (preset["default_model"] if preset else None),
        "configured_at": datetime.utcnow().isoformat() + "Z"
    }
    
    # Add any additional kwargs
    for key, value in kwargs.items():
        if value is not None:
            config[key] = value
    
    # Validate required fields
    if not config["base_url"]:
        return False, "Base URL is required. Use --base-url or select a known provider."
    
    if not config["model"]:
        return False, "Model is required. Use --model to specify."
    
    # Check if API key is required but missing
    if preset and preset["api_key"] is None and not api_key:
        if provider.lower() not in ["ollama", "lmstudio"]:
            return False, f"API key required for {preset['name']}. Use --api-key to provide it."
    
    # Save configuration
    os.makedirs(SPHERE_DIR, exist_ok=True)
    
    with open(LLM_CONFIG_FILE, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
    
    # Set restrictive permissions (contains API key)
    os.chmod(LLM_CONFIG_FILE, 0o600)
    
    audit.log_info(f"LLM configuration saved: {provider} / {config['model']}")
    return True, f"LLM configured: {config['provider_name']} ({config['model']})"


def delete_llm_config() -> Tuple[bool, str]:
    """Delete LLM configuration."""
    if not os.path.exists(LLM_CONFIG_FILE):
        return False, "No LLM configuration found."
    
    os.remove(LLM_CONFIG_FILE)
    audit.log_info("LLM configuration deleted")
    return True, "LLM configuration deleted."


def get_llm_status() -> Dict:
    """Get current LLM configuration status."""
    config = load_llm_config()
    
    if not config:
        return {
            "configured": False,
            "message": "No LLM configured. Run: sphere llm setup --provider <provider>"
        }
    
    return {
        "configured": True,
        "provider": config.get("provider_name", config.get("provider", "Unknown")),
        "model": config.get("model", "Unknown"),
        "base_url": config.get("base_url", "Unknown"),
        "type": config.get("type", "Unknown"),
        "configured_at": config.get("configured_at", "Unknown")
    }


def list_provider_presets() -> List[str]:
    """List available provider presets."""
    return list(PROVIDER_PRESETS.keys())


def get_provider_preset(name: str) -> Optional[Dict]:
    """Get a provider preset by name."""
    return PROVIDER_PRESETS.get(name.lower())


def call_llm(
    messages: List[Dict],
    system_prompt: Optional[str] = None,
    **kwargs
) -> Tuple[bool, str]:
    """
    Convenience function to call the configured LLM.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        system_prompt: Optional system prompt to prepend
        **kwargs: Additional parameters for the provider
    
    Returns:
        Tuple of (success, response_text or error_message)
    """
    provider = get_provider()
    
    if not provider:
        return False, "No LLM configured. Run: sphere llm setup --provider <provider>"
    
    # Prepend system prompt if provided
    if system_prompt:
        messages = [{"role": "system", "content": system_prompt}] + messages
    
    return provider.complete(messages, **kwargs)


def call_llm_with_retry(
    messages: List[Dict],
    system_prompt: Optional[str] = None,
    max_retries: int = 3,
    **kwargs
) -> Tuple[bool, str]:
    """
    Call LLM with automatic retry on failure.
    
    Args:
        messages: List of message dicts
        system_prompt: Optional system prompt
        max_retries: Maximum number of retry attempts
        **kwargs: Additional parameters
    
    Returns:
        Tuple of (success, response_text or error_message)
    """
    last_error = None
    
    for attempt in range(max_retries):
        success, result = call_llm(messages, system_prompt, **kwargs)
        
        if success:
            return True, result
        
        last_error = result
        audit.log_warning(f"LLM call failed (attempt {attempt + 1}/{max_retries}): {result}")
        
        # Don't retry on certain errors
        if "API key" in result or "authentication" in result.lower():
            break
    
    return False, f"LLM call failed after {max_retries} attempts. Last error: {last_error}"
