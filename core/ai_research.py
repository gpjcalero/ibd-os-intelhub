"""
IBD OS — AI Research Module (Agent 3 Strategist)
Genera reportes de estrategia comercial usando OpenRouter o Ollama.
Soporta Streaming y filtrado de tags <think>.
"""
import json
import requests
import re
from typing import Optional, List, Dict, Generator, Union, Any
from core.schemas import StrategyReport

def clean_think_tags(text: str) -> str:
    """Elimina bloques de razonamiento <think>...</think> de modelos como DeepSeek-R1."""
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

def research_with_openrouter(
    api_key: str, 
    company_name: str,
    country: str = "Global",
    contact_name: str = "",
    contact_title: str = "",
    model_name: str = "anthropic/claude-3-sonnet"
) -> Generator[str, None, Union[StrategyReport, None]]:
    """
    Agent 3 — Commercial Strategist (Cloud).
    """
    prompt = f"""Eres un estratega de ventas senior de Porcelanosa Grupo.
Analiza la empresa {company_name} en {country} para una posible venta de materiales de construcción premium.
Contacto: {contact_name} ({contact_title}).

Responde en JSON con: summary, key_facts, recommended_approach, email_draft, linkedin_draft, risks, confidence.
"""
    
    try:
        headers = { "Authorization": f"Bearer {api_key}", "Content-Type": "application/json" }
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}
        }
        
        yield f"☁️ Conectando con nube ({model_name})..."
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=60)
        
        if res.status_code == 200:
            content = res.json()['choices'][0]['message']['content']
            data = json.loads(clean_think_tags(content))
            yield StrategyReport(**data)
        else:
            yield f"❌ Error OpenRouter: {res.text}"
            yield None
    except Exception as e:
        yield f"❌ Error: {str(e)}"
        yield None

def research_with_ollama(
    model_name: str,
    company_name: str,
    country: str = "Global",
    contact_name: str = "",
    contact_title: str = ""
) -> Generator[str, None, Union[StrategyReport, None]]:
    """
    Agent 3 — Commercial Strategist (Local).
    """
    prompt = f"""Eres un estratega de ventas senior de Porcelanosa Grupo (Estrategia Local).
Analiza {company_name} para {country}.
Contacto: {contact_name} ({contact_title}).

Responde en JSON ESTRICTO.
"""
    
    try:
        actual_model = model_name.replace("ollama/", "")
        payload = {
            "model": actual_model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
            "format": StrategyReport.model_json_schema()
        }
        
        yield f"🧠 Iniciando {actual_model} local..."
        res = requests.post("http://localhost:11434/api/chat", json=payload, stream=True, timeout=600)
        
        content_text = ""
        for line in res.iter_lines():
            if line:
                chunk = json.loads(line.decode('utf-8'))
                content_text += chunk.get('message', {}).get('content', '')
                yield f"🧠 Generando estrategia... ({len(content_text)} chars)"
                if chunk.get('done'): break
        
        data = json.loads(clean_think_tags(content_text))
        yield StrategyReport(**data)
    except Exception as e:
        yield f"❌ Error Ollama: {str(e)}"
        yield None
