"""
IBD OS - Market Thermometer (Agent 0)
Analiza un país y rinde cuentas vía generator (streaming).
Usa Qwen local (Ollama) o OpenCloud (OpenRouter).
"""
import json
import re
import requests
from typing import Optional, List, Dict, Generator, Union, Any
from datetime import datetime
from core.schemas import ThermometerResult

def analyze_market(
    country: str,
    objective: str,
    model_name: str = "ollama/qwen3.5:latest",
    api_key: str = ""
) -> Generator[str, None, Union[ThermometerResult, None]]:
    """
    Market Thermometer: Analiza un país y rinde cuentas vía generator.
    Yields: strings con el progreso/status.
    Returns: ThermometerResult objeto al finalizar.
    """
    yield "🌐 Buscando contexto en tiempo real..."
    web_context = ""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            query = f"construction architecture interior design market trends {country} {datetime.now().year}"
            results = list(ddgs.text(query, max_results=5))
            if results:
                web_context = "CONTEXTO RECIENTE DE INTERNET:\n"
                for r in results:
                    web_context += f"- {r.get('title', '')}: {r.get('body', '')}\n"
    except Exception as e:
        yield f"⚠️ Contexto web no disponible: {str(e)}"

    prompt = f"""Eres un estratega de mercado internacional de Grupo Porcelanosa.
PAÍS OBJETIVO: {country}
OBJETIVO DEL COMERCIAL: {objective}

{web_context}

Analiza el mercado y responde en JSON ESTRICTO según el esquema solicitado.
"""

    content_text = ""
    try:
        if model_name.startswith("ollama/"):
            actual_model = model_name.replace("ollama/", "")
            yield f"🧠 Iniciando {actual_model} local..."
            
            payload = {
                "model": actual_model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": True,
                "format": ThermometerResult.model_json_schema()
            }
            
            response = requests.post("http://localhost:11434/api/chat", json=payload, stream=True, timeout=600)
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line.decode('utf-8'))
                    content_text += chunk.get('message', {}).get('content', '')
                    yield f"🧠 Analizando... ({len(content_text)} caracteres recibidos)"
                    if chunk.get('done'): break
        else:
            yield f"☁️ Consultando nube ({model_name})..."
            headers = { "Authorization": f"Bearer {api_key}", "Content-Type": "application/json" }
            payload = { 
                "model": model_name, 
                "messages": [{"role":"user","content":prompt}], 
                "response_format": {"type":"json_object"} 
            }
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=60)
            if res.status_code == 200:
                content_text = res.json()['choices'][0]['message']['content']
            else:
                raise Exception(f"Error OpenRouter: {res.text}")

        # Final Parse
        yield "📊 Estructurando datos finales..."
        data = json.loads(content_text)
        data['country'] = country
        data['objective'] = objective
        yield ThermometerResult(**data)
    except Exception as e:
        yield f"❌ Error crítico: {str(e)}"
        yield None
