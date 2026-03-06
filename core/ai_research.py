"""
IBD OS - AI Deep Research Engine (v3.1)
Optimizado para Gemini 2.0/3.0 Flash y Pro.
"""
import json
import urllib.parse
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import requests

@dataclass
class AIResearchResult:
    company_name: str
    summary: str
    key_facts: List[str]
    decision_makers: List[str]
    recent_projects: List[str]
    opportunities: List[str]
    risks: List[str]
    recommended_approach: str
    email_draft: str
    linkedin_draft: str
    sources: List[Dict[str, str]]
    confidence: str
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

def research_with_openrouter(
    api_key: str,
    company_name: str,
    model_name: str = "google/gemini-2.5-flash",
    country: str = "",
    contact_name: str = "",
    contact_title: str = ""
) -> Optional[AIResearchResult]:
    """
    Investigación PROFUNDA conectada a OpenRouter.
    Permite usar cientos de modelos (Gemini, Claude, OpenAI, DeepSeek...).
    """
    import time
    import re

    last_error_log = []

    prompt = f"""ERES UN ESTRATEGA COMERCIAL SENIOR (CONSULTOR B2B INDUSTRIAL).
Tu misión es analizar a '{company_name}' ({country}) para Porcelanosa Grupo.

OBJETIVO: Identificar oportunidades de colaboración (Offsite, Krion, Fachadas, Proyectos) y diseñar el abordaje comercial.

INPUT DATOS:
- Empresa: {company_name}
- Contacto Clave: {contact_name} {contact_title}

GENERA UN OUTPUT JSON ESTRICTO CON ESTA ESTRUCTURA DE ANÁLISIS EXPERTO:
{{
    "summary": "Resumen ejecutivo potente: qué hacen, dónde operan y por qué importan a Porcelanosa (8-10 líneas).",
    "key_facts": ["Evidencia de negocio 1 (con fuente)", "Evidencia 2", "Señal de compra detectada"],
    "radar_table": [
        {{"area": "Fachadas/Butech", "necesidad": "Eficiencia energética en torres", "nivel": "Alto"}},
        {{"area": "Industrialización", "necesidad": "Baños prefabricados (Monobath)", "nivel": "Medio"}}
    ],
    "hypothesis": [
        {{"titulo": "Hipótesis 1 (Principal)", "score": 5, "razon": "Por su proyecto X, necesitan Y..."}},
        {{"titulo": "Hipótesis 2 (Secundaria)", "score": 4, "razon": "..."}}
    ],
    "recommended_approach": "Propuesta de siguiente paso muy concreta (ej: Workshop Técnico o Visita Showroom).",
    "risks": ["Posible objeción 1", "Riesgo operativo"],
    "email_draft": "Asunto: ... Cuerpo: [120 palabras, enfoque colaboración, sin humo] ... CTA: ...",
    "linkedin_draft": "Mensaje directo (max 500 chars): Referencia específica + Propuesta valor + Pregunta cierre.",
    "confidence": "high"
}}

IMPORTANTE:
1. NO inventes datos. Si no hay info, deduce basado en el sector ({company_name} parece ser una... ).
2. Orienta todo a la venta consultiva de valor (calidad, plazos, sostenibilidad).
3. El JSON debe ser válido y la única salida.
"""

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are a Senior B2B Sales Strategist. You always reply in valid JSON format."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"}
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://ibd-os-intelhub.pages.dev",
        "X-Title": "IBD OS IntelHub",
        "Content-Type": "application/json"
    }

    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
        
        if response.status_code == 200:
            try:
                res_data = response.json()
                content_text = res_data['choices'][0]['message']['content']
                
                # --- PARSEADO ROBUSTO ---
                data = None
                cleaned = content_text.strip()
                cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
                cleaned = re.sub(r'\s*```$', '', cleaned)
                cleaned = cleaned.strip()
                
                try:
                    data = json.loads(cleaned)
                except:
                    # Fallback regex parsing
                    start = cleaned.find('{')
                    if start != -1:
                        depth = 0
                        end = start
                        for i in range(start, len(cleaned)):
                            if cleaned[i] == '{': depth += 1
                            elif cleaned[i] == '}': depth -= 1
                            if depth == 0:
                                end = i + 1
                                break
                        try:
                            data = json.loads(cleaned[start:end])
                        except:
                            pass
                
                if data is None:
                    # Last resort regex extraction
                    data = {}
                    for field_name in ['summary', 'email_draft', 'linkedin_draft', 'recommended_approach', 'confidence']:
                        match = re.search(rf'"{field_name}"\s*:\s*"((?:[^"\\]|\\.){{0,2000}})"', content_text, re.DOTALL)
                        if match:
                            data[field_name] = match.group(1).replace('\\n', '\n').replace('\\"', '"')
                    for arr_name in ['key_facts', 'risks']:
                        match = re.search(rf'"{arr_name}"\s*:\s*\[(.*?)\]', content_text, re.DOTALL)
                        if match:
                            items = re.findall(r'"((?:[^"\\]|\\.)*)"', match.group(1))
                            data[arr_name] = items

                encoded_name = urllib.parse.quote_plus(company_name)
                sources = [
                        {"title": f"Google: {company_name}", "url": f"https://www.google.com/search?q={company_name}"},
                        {"title": "LinkedIn", "url": f"https://www.linkedin.com/search/results/companies/?keywords={encoded_name}"}
                ]

                return AIResearchResult(
                    company_name=company_name,
                    summary=data.get("summary", content_text[:500]),
                    key_facts=data.get("key_facts", []),
                    decision_makers=data.get("decision_makers", []),
                    recent_projects=data.get("recent_projects", []),
                    opportunities=data.get("opportunities", []),
                    risks=data.get("risks", []),
                    recommended_approach=data.get("recommended_approach", ""),
                    email_draft=data.get("email_draft", "No generado."),
                    linkedin_draft=data.get("linkedin_draft", "No generado."),
                    sources=sources,
                    confidence=data.get("confidence", "medium")
                )
            except Exception as e:
                # Si falla el parseo pero hay texto
                if 'content_text' in locals() and content_text:
                    return AIResearchResult(
                        company_name=company_name, summary=content_text[:800],
                        key_facts=[], decision_makers=[], recent_projects=[], opportunities=[], risks=[],
                        recommended_approach="Ver resumen.", email_draft="Error formato.", linkedin_draft="Error formato.", 
                        sources=[], confidence="low"
                    )
                raise e
        else:
            err_msg = response.text[:100]
            raise Exception(f"OpenRouter API Error: {response.status_code} - {err_msg}")
            
    except Exception as e:
        return AIResearchResult(
            company_name=company_name,
            summary=f"❌ Error Final: {str(e)}. Verifica la API Key y el soporte del modelo en OpenRouter.",
            key_facts=[], decision_makers=[], recent_projects=[], opportunities=[], risks=[],
            recommended_approach="", email_draft="", linkedin_draft="", sources=[], confidence="low"
        )

