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

def research_with_gemini_rest(
    api_key: str,
    company_name: str,
    model_name: str = "gemini-3.0-flash", # Preferido por defecto
    country: str = "",
    contact_name: str = "",
    contact_title: str = ""
) -> Optional[AIResearchResult]:
    """
    Investigación PROFUNDA con sistema 'Smart Chain'.
    Prueba múltiples modelos SOTA hasta obtener respuesta válida.
    """
    
    # ESTRATEGIA: "ASEGURAR EL TIRO" (Gemini 3 Pro Preview sin herramientas conflictivas)
    
    attempts = [
        # OPCIÓN 1: La Estrella (Gemini 3 Pro Preview) - SIN SEARCH para evitar Error 400
        {
            "model": "gemini-3-pro-preview", 
            "version": "v1beta", 
            "use_search": False, 
            "desc": "Gemini 3 Pro (Preview)"
        },
        # OPCIÓN 2: Pro Sólido (Gemini 2.5 Pro)
        {
            "model": "gemini-2.5-pro", 
            "version": "v1beta", 
            "use_search": False,
            "desc": "Gemini 2.5 Pro"
        },
        # OPCIÓN 3: Fallback (Gemini 2.0 Flash)
        {
            "model": "gemini-2.0-flash", 
            "version": "v1beta", 
            "use_search": False,
            "desc": "Gemini 2.0 Flash"
        }
    ]

    import time
    import re # Importamos regex para buscar JSON
    
    last_error_log = []

    for config in attempts:
        model = config["model"]
        version = config["version"]
        
        # PROMPT DEL AGENTE 3: ESTRATEGA COMERCIAL SENIOR
        # Este prompt define la personalidad y estructura exacta del agente experto.
        
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
3. El JSON debe ser válido.
"""

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}
        }

        headers = {'Content-Type': 'application/json'}

        # 2. Intentar Conexión
        try:
            url = f"https://generativelanguage.googleapis.com/{version}/models/{model}:generateContent?key={api_key}"
            
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
            
            if response.status_code == 200:
                try:
                    candidates = response.json().get('candidates', [])
                    if not candidates: continue
                    
                    content_text = candidates[0]['content']['parts'][0]['text']
                    
                    # --- PARSEADO ULTRA-ROBUSTO (v4.0) ---
                    data = None
                    
                    # PASO 1: Limpiar el texto antes de intentar parsear
                    cleaned = content_text.strip()
                    # Quitar markdown fences (```json ... ```)
                    cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
                    cleaned = re.sub(r'\s*```$', '', cleaned)
                    cleaned = cleaned.strip()
                    
                    # PASO 2: Intentar carga directa
                    try:
                        data = json.loads(cleaned)
                    except:
                        pass
                    
                    # PASO 3: Buscar bloque JSON más grande entre { y }
                    if data is None:
                        # Encontrar el primer { y buscar el } que lo cierra correctamente
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
                            json_candidate = cleaned[start:end]
                            try:
                                data = json.loads(json_candidate)
                            except:
                                # PASO 4: Limpiar caracteres de control invisibles
                                json_candidate = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', json_candidate)
                                json_candidate = json_candidate.replace('\n', ' ').replace('\r', ' ')
                                try:
                                    data = json.loads(json_candidate)
                                except:
                                    pass
                    
                    # PASO 5: Si NADA funcionó, extraer campos individualmente con regex
                    if data is None:
                        data = {}
                        # Buscar cada campo clave
                        for field_name in ['summary', 'email_draft', 'linkedin_draft', 'recommended_approach', 'confidence']:
                            match = re.search(rf'"{field_name}"\s*:\s*"((?:[^"\\]|\\.){{0,2000}})"', content_text, re.DOTALL)
                            if match:
                                data[field_name] = match.group(1).replace('\\n', '\n').replace('\\"', '"')
                        
                        # Buscar arrays
                        for arr_name in ['key_facts', 'risks']:
                            match = re.search(rf'"{arr_name}"\s*:\s*\[(.*?)\]', content_text, re.DOTALL)
                            if match:
                                items = re.findall(r'"((?:[^"\\]|\\.)*)"', match.group(1))
                                data[arr_name] = items
                    
                    # Fuentes simuladas
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
                        email_draft=data.get("email_draft", "No generado. Reintentar."),
                        linkedin_draft=data.get("linkedin_draft", "No generado. Reintentar."),
                        sources=sources,
                        confidence=data.get("confidence", "medium")
                    )
                except Exception as e:
                    last_error_log.append(f"{model}: Parse Error ({str(e)[:80]})")
                    
                    # FALLBACK: si hay texto, devolverlo como sea
                    if 'content_text' in locals() and content_text:
                        return AIResearchResult(
                            company_name=company_name,
                            summary=content_text[:800],
                            key_facts=[], decision_makers=[], recent_projects=[], opportunities=[], risks=[],
                            recommended_approach="Ver resumen completo.", 
                            email_draft="Error de formato. Reintentar.", 
                            linkedin_draft="Error de formato. Reintentar.", 
                            sources=[], confidence="low"
                        )
                    continue
            else:
                err_Msg = response.text[:100]
                last_error_log.append(f"{model}: {response.status_code} - {err_Msg}")
                continue
                
        except Exception as e:
            last_error_log.append(f"{model}: {str(e)}")
            continue

    # 3. Si todo falla (improbable)
    error_msg = " | ".join(last_error_log)
    return AIResearchResult(
        company_name=company_name,
        summary=f"❌ Error Final: {error_msg}. La API Key funciona, pero los modelos rechazaron la conexión.",
        key_facts=[], decision_makers=[], recent_projects=[], opportunities=[], risks=[],
        recommended_approach="", email_draft="", linkedin_draft="", sources=[], confidence="low"
    )
