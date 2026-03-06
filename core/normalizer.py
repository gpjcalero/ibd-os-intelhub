"""
AGENTE 2: MATCHER B2B (NORMALIZER)
Módulo de normalización de nombres de empresas multi-país.
Implementa las reglas de limpieza de sufijos y ruido definidas en '02-matcher-b2b.md'.
"""
import re
import unicodedata

# Sufijos legales por región (regex pre-compiladas)
LEGAL_SUFFIXES = {
    'global': r'\b(ltd|limited|inc|llc|plc|corp|corporation|group|holding|holdings)\b',
    'es': r'\b(sl|s\.l\.|sa|s\.a\.|slu|s\.l\.u\.|scp|s\.c\.p\.)\b',
    'fr': r'\b(sas|sarl|sa|sci)\b',
    'de': r'\b(gmbh|ag|kg|ug)\b',
    'nordics': r'\b(ab|oy|as|a/s|aps)\b',
    'nl_be': r'\b(bv|nv)\b',
    'it': r'\b(spa|srl|s\.p\.a\.|s\.r\.l\.)\b'
}

# Palabras de ruido (generan falsos positivos si no se quitan)
NOISE_WORDS = r'\b(company|companies|studio|architects|arkitekter|arquitectos|bureau|consulting|design|partners|associates|oficina|taller|atelier)\b'

def normalize_company_name(name: str) -> str:
    """
    Normaliza un nombre de empresa para matching robusto.
    1. Lowercase + Trim.
    2. Eliminar puntuación.
    3. Normalizar conectores (& -> and).
    4. Eliminar sufijos legales y ruido.
    5. Folding de diacríticos (tildes).
    """
    if not isinstance(name, str) or not name:
        return ""
    
    # 1. Lowercase
    norm = name.lower().strip()
    
    # 5. Diacríticos (café -> cafe)
    norm = ''.join(c for c in unicodedata.normalize('NFD', norm) if unicodedata.category(c) != 'Mn')
    
    # 3. Conectores específicos
    norm = re.sub(r'\s+&\s+', ' and ', norm)
    norm = re.sub(r'\s+\+\s+', ' and ', norm)
    
    # 2. Puntuación (mantener solo alfanumérico y espacios)
    norm = re.sub(r'[^\w\s]', ' ', norm)
    
    # 4. Eliminar sufijos legales (iterar todas las regiones)
    for region, regex in LEGAL_SUFFIXES.items():
        norm = re.sub(regex, '', norm)
        
    # Eliminar ruido industrial (architects, etc)
    norm = re.sub(NOISE_WORDS, '', norm)
    
    # Colapsar espacios extra
    norm = re.sub(r'\s+', ' ', norm).strip()
    
    return norm
