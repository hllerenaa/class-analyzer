"""Capa IA pluggable. Un token + provider y genera el reporte.

Providers: claude | gemini | deepseek | ollama
Todos via HTTP (requests), sin SDKs.
"""
import json
import requests

TIMEOUT = 120


def _claude(api_key, model, prompt, base_url):
    url = (base_url or "https://api.anthropic.com") + "/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    body = {
        "model": model or "claude-3-5-haiku-latest",
        "max_tokens": 1500,
        "messages": [{"role": "user", "content": prompt}],
    }
    r = requests.post(url, headers=headers, json=body, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()["content"][0]["text"]


def _gemini(api_key, model, prompt, base_url):
    base = base_url or "https://generativelanguage.googleapis.com"
    m = model or "gemini-1.5-flash"
    url = f"{base}/v1beta/models/{m}:generateContent?key={api_key}"
    body = {"contents": [{"parts": [{"text": prompt}]}]}
    r = requests.post(url, json=body, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]


def _openai_compatible(api_key, model, prompt, base_url, default_base):
    url = (base_url or default_base) + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1500,
    }
    r = requests.post(url, headers=headers, json=body, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def _deepseek(api_key, model, prompt, base_url):
    return _openai_compatible(
        api_key, model or "deepseek-chat", prompt, base_url,
        "https://api.deepseek.com",
    )


def _ollama(api_key, model, prompt, base_url):
    base = base_url or "http://localhost:11434"
    url = base + "/api/chat"
    body = {
        "model": model or "llama3.1",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }
    r = requests.post(url, json=body, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()["message"]["content"]


_DISPATCH = {
    "claude": _claude,
    "gemini": _gemini,
    "deepseek": _deepseek,
    "ollama": _ollama,
}


def generate_report(provider, api_key, model, base_url, prompt):
    provider = (provider or "ollama").lower()
    fn = _DISPATCH.get(provider)
    if not fn:
        raise ValueError(f"Provider no soportado: {provider}")
    if provider != "ollama" and not api_key:
        raise ValueError(f"Falta API key para provider '{provider}'")
    return fn(api_key, model, prompt, base_url)
