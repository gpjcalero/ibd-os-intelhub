"""
IBD OS - Web Enricher (Agent 0.5)
Verifica empresas scrapeando su web con requests+BeautifulSoup (gratis).
Usa Qwen local para clasificar si encaja con el objetivo.
"""
import json
import re
import requests as req
from typing import Optional, Dict
from dataclasses import dataclass
from bs4 import BeautifulSoup


@dataclass
class WebEnrichmentResult:
    company_name: str
    url: str
    is_target: bool  # True = encaja, False = no encaja
    verdict: str     # "✅ Target" / "❌ Not Target" / "⚠️ Uncertain"
    reason: str      # Explicación de 1 línea
    extracted_description: str  # Lo que se extrajo de la web
    confidence: str


def enrich_company(
    company_name: str,
    website_url: str,
    objective: str = "arquitectos que especifican materiales de construcción",
    model_name: str = "qwen3.5:latest"
) -> WebEnrichmentResult:
    """
    1. Scrapea la web de la empresa (requests + BeautifulSoup)
    2. Envía el texto a Qwen local para clasificar
    """
    
    # --- 1. SCRAPE WEB ---
    extracted_text = ""
    try:
        url = website_url.strip()
        if not url.startswith("http"):
            url = "http://" + url
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = req.get(url, headers=headers, timeout=10, allow_redirects=True)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraer title
            title = soup.title.string.strip() if soup.title and soup.title.string else ""
            
            # Extraer meta description
            meta_desc = ""
            meta_tag = soup.find('meta', attrs={'name': 'description'})
            if meta_tag and meta_tag.get('content'):
                meta_desc = meta_tag['content'].strip()
            
            # Extraer texto visible del body (primeros 800 chars)
            body_text = ""
            if soup.body:
                for script_or_style in soup.body(['script', 'style', 'nav', 'footer', 'header']):
                    script_or_style.decompose()
                body_text = soup.body.get_text(separator=' ', strip=True)[:800]
            
            extracted_text = f"Title: {title}\nDescription: {meta_desc}\nContent: {body_text}"
        else:
            extracted_text = f"Error HTTP {response.status_code}"
    except Exception as e:
        extracted_text = f"Error accessing website: {str(e)[:100]}"
    
    if not extracted_text or extracted_text.startswith("Error"):
        return WebEnrichmentResult(
            company_name=company_name, url=website_url,
            is_target=False, verdict="⚠️ Uncertain",
            reason=f"No se pudo acceder a la web: {extracted_text[:100]}",
            extracted_description=extracted_text, confidence="low"
        )
    
    # --- 2. CLASSIFY WITH QWEN ---
    prompt = f"""Analiza la siguiente información extraída de la web de '{company_name}' ({website_url}).

INFORMACIÓN EXTRAÍDA:
{extracted_text[:600]}

PREGUNTA: ¿Es esta empresa relevante para Porcelanosa Grupo como {objective}?
Porcelanosa vende: cerámica, baños, cocinas, fachadas ventiladas, piedra natural.

Responde en JSON:
{{
    "is_target": true/false,
    "reason": "Explicación de máximo 1 línea",
    "confidence": "high/medium/low"
}}
"""
    
    try:
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "Classify companies. Reply only in valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "format": "json"
        }
        
        ollama_response = req.post(
            "http://localhost:11434/api/chat",
            data=json.dumps(payload), timeout=60
        )
        
        if ollama_response.status_code == 200:
            content = ollama_response.json()['message']['content']
            data = json.loads(content.strip())
            
            is_target = data.get("is_target", False)
            verdict = "✅ Target" if is_target else "❌ Not Target"
            
            return WebEnrichmentResult(
                company_name=company_name, url=website_url,
                is_target=is_target, verdict=verdict,
                reason=data.get("reason", "Sin razón"),
                extracted_description=extracted_text[:300],
                confidence=data.get("confidence", "medium")
            )
    except Exception as e:
        pass
    
    return WebEnrichmentResult(
        company_name=company_name, url=website_url,
        is_target=False, verdict="⚠️ Uncertain",
        reason="Error en la clasificación IA",
        extracted_description=extracted_text[:300], confidence="low"
    )
