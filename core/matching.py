"""
AGENTE 2: MATCHER B2B (MATCHING ENGINE)
Versión: 2.1 (Pure Python - Pyodide Compatible)
Propósito: Cruzar Licitaciones <-> Contactos con precisión quirúrgica.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from difflib import SequenceMatcher
from core.normalizer import normalize_company_name


# --- FUZZY MATCHING PURE PYTHON (Reemplazo de rapidfuzz) ---

def fuzz_ratio(s1: str, s2: str) -> int:
    """Calcula similitud 0-100 entre dos strings (como fuzz.ratio)."""
    if not s1 or not s2: return 0
    return int(SequenceMatcher(None, s1.lower(), s2.lower()).ratio() * 100)

def fuzz_token_sort_ratio(s1: str, s2: str) -> int:
    """Similitud ignorando orden de palabras (como fuzz.token_sort_ratio)."""
    if not s1 or not s2: return 0
    t1 = " ".join(sorted(s1.lower().split()))
    t2 = " ".join(sorted(s2.lower().split()))
    return int(SequenceMatcher(None, t1, t2).ratio() * 100)

def find_top_matches(query: str, choices, limit: int = 5):
    """Busca los top N matches (reemplazo de process.extract)."""
    scores = []
    for choice in choices:
        score = fuzz_token_sort_ratio(query, choice)
        scores.append((choice, score))
    scores.sort(key=lambda x: x[1], reverse=True)
    return [(name, score, idx) for idx, (name, score) in enumerate(scores[:limit])]

@dataclass
class MatchResult:
    tender_id: str
    matched_company_name: str
    match_level: str # 'Seguro', 'Probable', 'Revisar', 'Sin match'
    match_score: int # 0-100
    match_reason: str
    contact_email: str = ""
    contact_phone: str = ""
    contact_linkedin: str = ""
    
class B2BMatcher:
    """
    Agente Matcher B2B. Cruza una lista de empresas extraídas de licitaciones
    con una base de datos de contactos corporativos.
    """
    
    def __init__(self, contacts_df: pd.DataFrame):
        # Pre-procesar contactos para velocidad
        self.contacts_df = contacts_df.copy()
        
        # Detectar columnas clave en contactos
        self.col_name = next((c for c in contacts_df.columns if 'company' in c.lower()), 'Company Name')
        self.col_web = next((c for c in contacts_df.columns if 'web' in c.lower()), None)
        self.col_country = next((c for c in contacts_df.columns if 'country' in c.lower()), None)
        
        # Normalizar nombres de contactos al inicio (cache)
        self.contacts_df['Normalized_Name'] = self.contacts_df[self.col_name].astype(str).apply(normalize_company_name)
        
        # Crear mapa de dominios si existe web
        self.domain_map = {}
        if self.col_web:
            for idx, row in self.contacts_df.iterrows():
                web = str(row[self.col_web]).lower()
                domain = self._extract_domain(web)
                if domain:
                    self.domain_map[domain] = idx

    def _extract_domain(self, url: str) -> str:
        """Extrae 'porcelanosa.com' de 'https://www.porcelanosa.com/index'"""
        try:
            from urllib.parse import urlparse
            if not url.startswith(('http', 'www')): return ""
            if not url.startswith('http'): url = 'http://' + url
            netloc = urlparse(url).netloc
            parts = netloc.split('.')
            if len(parts) >= 2: return f"{parts[-2]}.{parts[-1]}"
            return netloc
        except:
            return ""

    def match_company(self, tender_company_raw: str, tender_country: str = "") -> Dict:
        """
        Core Matching Logic (Agente 2 - Fase 1 & 2)
        """
        if not tender_company_raw or pd.isna(tender_company_raw):
            return self._empty_match()

        normalized_tender = normalize_company_name(tender_company_raw)
        
        # --- FASE 1: EXACT MATCH ---
        exact_matches = self.contacts_df[self.contacts_df['Normalized_Name'] == normalized_tender]
        if not exact_matches.empty:
            # Si hay varios, priorizar por país
            best_match = exact_matches.iloc[0] # Default primero
            if tender_country:
                country_match = exact_matches[exact_matches[self.col_country].astype(str).str.contains(tender_country, case=False, na=False)]
                if not country_match.empty:
                    best_match = country_match.iloc[0]
            
            return self._build_match(normalized_tender, best_match, 100, "Seguro", "Exact Match")

        # --- FASE 2: DOMAIN MATCH (Si tuviéramos web en tender) ---
        # (Omitido porque tenders suelen venir sin URL limpia, pero la lógica estaría aquí)
        
        # --- FASE 3: FUZZY MATCH ---
        # Usamos token_sort_ratio para ignorar orden ("Grupo San José" == "San José Grupo")
        candidates = find_top_matches(
            normalized_tender, 
            self.contacts_df['Normalized_Name'].unique(), 
            limit=5
        )
        
        if not candidates:
            return self._empty_match()
            
        top1_name, top1_score, _ = candidates[0]
        
        # --- REGLAS DE DECISIÓN DEL AGENTE ---
        
        # Regla 1: Nombre muy corto (<4 chars) -> Riesgo alto
        if len(normalized_tender) < 4 and top1_score < 100:
             return self._build_match(tender_company_raw, None, top1_score, "Revisar", "Nombre corto (Riesgo)")

        # Regla 2: Niveles de Confianza
        match_row = self.contacts_df[self.contacts_df['Normalized_Name'] == top1_name].iloc[0]
        
        if top1_score >= 92:
            # Verificar brecha con el segundo (Top1 - Top2 >= 4)
            if len(candidates) > 1 and (top1_score - candidates[1][1] < 4):
                 return self._build_match(tender_company_raw, match_row, top1_score, "Revisar", "Ambigüedad (Top1 muy cerca de Top2)")
            return self._build_match(tender_company_raw, match_row, top1_score, "Seguro", f"Fuzzy High ({top1_score}%)")
            
        elif 86 <= top1_score < 92:
            return self._build_match(tender_company_raw, match_row, top1_score, "Probable", f"Fuzzy Medium ({top1_score}%)")
            
        elif 80 <= top1_score < 86:
            return self._build_match(tender_company_raw, match_row, top1_score, "Revisar", f"Fuzzy Low ({top1_score}%)")
            
        else:
            return self._empty_match()

    def _build_match(self, tender_comp, contact_row, score, level, reason):
        if contact_row is None:
             return {
                'matched_company': "", 'match_level': level, 'match_score': score, 
                'match_reason': reason, 'contact_email': "", 'contact_phone': "", 'contact_linkedin': ""
            }
            
        # Extraer datos contacto
        email = contact_row.get(next((c for c in self.contacts_df.columns if 'email' in c.lower()), ''), '')
        phone = contact_row.get(next((c for c in self.contacts_df.columns if 'phone' in c.lower()), ''), '')
        linkedin = contact_row.get(next((c for c in self.contacts_df.columns if 'linkedin' in c.lower()), ''), '')

        return {
            'matched_company': contact_row[self.col_name],
            'match_level': level,
            'match_score': score,
            'match_reason': reason,
            'contact_email': email,
            'contact_phone': phone,
            'contact_linkedin': linkedin
        }

    def _empty_match(self):
        return {
            'matched_company': "", 
            'match_level': "Sin match", 
            'match_score': 0, 
            'match_reason': "No candidates found",
            'contact_email': "", 'contact_phone': "", 'contact_linkedin': ""
        }

def process_tenders(tenders_df: pd.DataFrame, contacts_df: pd.DataFrame) -> pd.DataFrame:
    """Función principal para cruzar Tenders -> Contactos"""
    
    matcher = B2BMatcher(contacts_df)
    results = []
    
    # Identificar columna de empresa en tenders (Buyer / Entity / Client)
    tender_comp_col = next((c for c in tenders_df.columns if any(x in c.lower() for x in ['buyer', 'entity', 'client', 'company'])), None)
    
    if not tender_comp_col:
        # Si no hay columna de empresa, no podemos hacer match
        tenders_df['Match_Status'] = "Error: Sin columna empresa"
        return tenders_df

    for idx, row in tenders_df.iterrows():
        tender_comp = str(row[tender_comp_col])
        match_result = matcher.match_company(tender_comp)
        
        # Aplanar resultado
        res = row.to_dict()
        res.update(match_result)
        results.append(res)
        
    return pd.DataFrame(results)
