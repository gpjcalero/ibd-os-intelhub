"""
IBD OS - Market Thermometer (Agent 0)
Analiza un país y genera un scoring_profile dinámico + instrucciones de descarga para Global Database.
Usa Qwen local (Ollama) → coste 0€.
"""
import json
import requests
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ThermometerResult:
    country: str
    objective: str
    country_assessment: str
    recommended_segments: list
    scoring_profile: Dict[str, Any]
    global_db_instructions: Dict[str, Any]
    risks: list
    opportunities: list
    confidence: str
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


def analyze_market(
    country: str,
    objective: str,
    model_name: str = "qwen3.5:latest"
) -> Optional[ThermometerResult]:
    """
    Market Thermometer: Analiza un país y devuelve:
    1. Scoring profile dinámico (para score_dataframe)
    2. Instrucciones de descarga para Global Database
    Incluye búsqueda web en vivo (DuckDuckGo) para contexto real-time.
    """
    import re
    from duckduckgo_search import DDGS
    import time
    
    # --- 1. LIVE WEB SEARCH (DuckDuckGo) ---
    web_context = ""
    try:
        query = f"construction architecture interior design market trends {country} {datetime.now().year}"
        results = DDGS().text(query, max_results=5)
        if results:
            web_context = "CONTEXTO WEB EN VIVO (Noticias y Tendencias Recientes):\n"
            for r in results:
                web_context += f"- {r.get('title', '')}: {r.get('body', '')}\n"
    except Exception as e:
        web_context = f"(Error obteniendo contexto web: {str(e)})"
        
    # --- 2. QWEN 3.5 LLM INFERENCE ---
    prompt = f"""Eres un estratega de mercado internacional de Grupo Porcelanosa.
Porcelanosa es un grupo español de 8 empresas que vende: cerámica y porcelánico (Porcelanosa, Venis, Urbatek),
baños (Noken, Systempool/Krion), cocinas y muebles (Gamadecor), fachadas ventiladas y soluciones constructivas (Butech),
y piedra natural (L'Antic Colonial).

PAÍS OBJETIVO: {country}
OBJETIVO DEL COMERCIAL: {objective}

{web_context}

Analiza el mercado y responde en JSON ESTRICTO con esta estructura:

{{
    "country_assessment": "Resumen de 3-5 líneas del mercado de materiales premium de construcción en {country}. Tendencias clave, estado del sector, oportunidades macro.",
    
    "recommended_segments": ["Segmento 1 a atacar", "Segmento 2", "Segmento 3"],
    
    "scoring_profile": {{
        "target_sic": {{
            "keyword_regex_1": puntos_0_a_25,
            "keyword_regex_2": puntos_0_a_25
        }},
        "target_titles": {{
            "keyword_regex_1": puntos_0_a_15,
            "keyword_regex_2": puntos_0_a_15
        }},
        "min_employees": numero_minimo
    }},
    
    "global_db_instructions": {{
        "sic_codes": ["71111", "74101"],
        "nace_codes": ["71.11", "74.10"],
        "gdb_sectors": ["Construction & Real Estate", "Professional Services"],
        "job_titles": ["Architect", "Design Director", "Partner"],
        "seniority": ["Director", "CXO", "Owner"],
        "industry_keywords": ["architect", "interior design"],
        "min_employees": 10,
        "min_revenue_eur": 500000,
        "growth_signals": ["Revenue Growth > 0%"],
        "notes": "Instrucciones adicionales para el comercial que va a descargar de Global Database"
    }},
    
    "risks": ["Riesgo 1 del mercado", "Riesgo 2"],
    "opportunities": ["Oportunidad 1", "Oportunidad 2", "Oportunidad 3"],
    "confidence": "high"
}}

REGLAS:
1. El "scoring_profile.target_sic" debe contener regex/keywords que se buscarán en la columna SIC Activity del Excel de Global Database. Pondera MÁS (25 pts) los que encajen con el objetivo del comercial. Pondera MENOS (5-10 pts) los que sean tangenciales.
2. El "scoring_profile.target_titles" debe reflejar qué cargos son relevantes para el objetivo del comercial en ese país.
3. Las "global_db_instructions" deben ser filtros EXACTOS y accionables para la plataforma Global Database (SIC codes internacionales, NACE Rev.2, sectores GDB, cargos, etc.).
4. Adapta TODO al país y objetivo. No uses respuestas genéricas.
5. El JSON debe ser válido y ser la ÚNICA salida.
"""

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are a Senior Market Intelligence Strategist for Porcelanosa Group. Always reply in valid JSON."},
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "format": "json"
    }

    try:
        url = "http://localhost:11434/api/chat"
        response = requests.post(url, data=json.dumps(payload), timeout=180)

        if response.status_code == 200:
            res_data = response.json()
            content_text = res_data['message']['content']

            # Parse JSON
            data = None
            cleaned = content_text.strip()
            cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
            cleaned = re.sub(r'\s*```$', '', cleaned)
            cleaned = cleaned.strip()

            try:
                data = json.loads(cleaned)
            except:
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
                return ThermometerResult(
                    country=country, objective=objective,
                    country_assessment=f"No se pudo parsear la respuesta del modelo. Texto raw: {content_text[:300]}",
                    recommended_segments=[], scoring_profile={}, global_db_instructions={},
                    risks=[], opportunities=[], confidence="low"
                )

            # Build scoring_profile with defaults
            scoring_profile = data.get("scoring_profile", {})
            if "target_sic" not in scoring_profile:
                scoring_profile["target_sic"] = {"architectural": 25, "interior": 20}
            if "target_titles" not in scoring_profile:
                scoring_profile["target_titles"] = {"architect|director|partner": 15}
            if "min_employees" not in scoring_profile:
                scoring_profile["min_employees"] = 5

            return ThermometerResult(
                country=country,
                objective=objective,
                country_assessment=data.get("country_assessment", ""),
                recommended_segments=data.get("recommended_segments", []),
                scoring_profile=scoring_profile,
                global_db_instructions=data.get("global_db_instructions", {}),
                risks=data.get("risks", []),
                opportunities=data.get("opportunities", []),
                confidence=data.get("confidence", "medium")
            )
        else:
            raise Exception(f"Ollama Error: {response.status_code}")

    except Exception as e:
        return ThermometerResult(
            country=country, objective=objective,
            country_assessment=f"❌ Error: {str(e)}. Verifica que Ollama está corriendo con el modelo '{model_name}'.",
            recommended_segments=[], scoring_profile={}, global_db_instructions={},
            risks=[], opportunities=[], confidence="low"
        )
