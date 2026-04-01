"""
AGENTE 1: PROSPECTOR B2B (SCORING ENGINE v2 — Dynamic)
Acepta un scoring_profile opcional del Market Thermometer para ponderaciones dinámicas.
Implementa jerarquía SIC: International SIC Code > NACE Rev.2 > SIC Activity > Industry.
"""
import pandas as pd
import numpy as np
import re
from typing import Dict, Optional, Any


# ═══════════════════════════════════════════════════════════════════════════════
# DEFAULT SCORING PROFILE (cuando no hay Thermometer)
# ═══════════════════════════════════════════════════════════════════════════════
DEFAULT_PROFILE = {
    "target_sic": {
        "architectural": 25,
        "interior decor": 25,
        "interior design": 25,
        "construction of.*building": 15,
        "real estate": 12,
        "developer": 12,
        "hotel|hospitality": 15,
        "engineering": 5,
    },
    "target_titles": {
        "ceo|director|head|lead|manager|owner|founder|partner|principal": 15,
        "architect|interior|designer|specifier": 12,
        "purchase|procurement|compras": 10,
        "engineer|técnico": 5,
    },
    "min_employees": 5
}


def _find_sic_column(df: pd.DataFrame) -> Optional[str]:
    """
    Busca la columna de clasificación SIC por jerarquía de prioridad:
    1. International SIC Code / SIC Code (código numérico)
    2. NACE Rev. 2
    3. SIC Activity (descripción textual — la más útil para scoring)
    4. Industry classification / GDB Sector (fallback)
    """
    cols_lower = {c: c.lower() for c in df.columns}
    
    # Prioridad 1: SIC Activity (texto descriptivo, siempre la mejor señal)
    for col, lower in cols_lower.items():
        if 'sic' in lower and 'activity' in lower:
            # Verificar que no son todos iguales (señal útil)
            nunique = df[col].dropna().nunique()
            if nunique > 1:
                return col
    
    # Prioridad 2: General Activity
    for col, lower in cols_lower.items():
        if 'general' in lower and 'activity' in lower:
            nunique = df[col].dropna().nunique()
            if nunique > 1:
                return col
    
    # Prioridad 3: NACE
    for col, lower in cols_lower.items():
        if 'nace' in lower:
            nunique = df[col].dropna().nunique()
            if nunique > 1:
                return col
    
    # Prioridad 4: Industry classification (solo si tiene variedad)
    for col, lower in cols_lower.items():
        if 'industry' in lower or 'sector' in lower:
            nunique = df[col].dropna().nunique()
            if nunique > 1:
                return col
    
    # Último recurso: cualquier columna con industry/sector aunque sean todos iguales
    for col, lower in cols_lower.items():
        if 'industry' in lower or 'sector' in lower or 'activity' in lower:
            return col
    
    return None


def _categorize_sic(sic_text: str, target_sic: Dict[str, int]) -> tuple:
    """
    Clasifica un texto SIC y devuelve (categoría_emoji, puntuación).
    """
    text = str(sic_text).lower().strip()
    
    best_score = 0
    best_category = "❓ Other"
    
    # Map de categorías para display
    category_map = {
        "architectural": "🎯 Architect",
        "interior decor": "🎯 Interior Designer", 
        "interior design": "🎯 Interior Designer",
        "construction of.*building": "🏗️ Developer/Constructor",
        "real estate": "🏗️ Real Estate",
        "developer": "🏗️ Developer",
        "hotel|hospitality": "🏨 Hospitality",
        "engineering": "⚙️ Engineering",
    }
    
    for keyword, points in target_sic.items():
        try:
            if re.search(keyword, text):
                if points > best_score:
                    best_score = points
                    best_category = category_map.get(keyword, f"📋 {keyword.title()}")
        except re.error:
            if keyword in text:
                if points > best_score:
                    best_score = points
                    best_category = category_map.get(keyword, f"📋 {keyword.title()}")
    
    return best_category, best_score


def score_dataframe(df: pd.DataFrame, scoring_profile: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """
    Motor de Scoring del Agente Prospector B2B (v2 — Dynamic).
    
    Args:
        df: DataFrame con datos de Global Database
        scoring_profile: Perfil de ponderaciones del Market Thermometer.
                         Si None, usa DEFAULT_PROFILE.
    
    Calcula:
    1. SIC Fit Score (0-25) — basado en SIC Activity + perfil dinámico
    2. Account Fit Score (0-25) — tamaño + señal digital + financiero
    3. Lead Power Score (0-30) — cargo + seniority + contactabilidad
    4. Tender Score (0-20) — viene del matching posterior
    
    Total: 0-100
    """
    df = df.copy()
    profile = scoring_profile or DEFAULT_PROFILE
    
    # Extract and clamp target_sic to 25 Max
    target_sic_raw = profile.get("target_sic", DEFAULT_PROFILE["target_sic"])
    target_sic = {k: min(int(v), 25) for k, v in target_sic_raw.items()}
    
    # Extract and clamp target_titles to 15 Max
    target_titles_raw = profile.get("target_titles", DEFAULT_PROFILE["target_titles"])
    target_titles = {k: min(int(v), 15) for k, v in target_titles_raw.items()}
    
    min_emp = profile.get("min_employees", 5)
    
    # --- 0. DETECCIÓN INTELIGENTE DE COLUMNAS ---
    cols_map = {
        'sic': _find_sic_column(df),
        'size': next((c for c in df.columns if any(x in c.lower() for x in ['employee', 'staff', 'size'])), None),
        'financial': next((c for c in df.columns if any(x in c.lower() for x in ['turnover', 'revenue', 'sales'])), None),
        'website': next((c for c in df.columns if 'web' in c.lower() and 'visit' not in c.lower()), None),
        'linkedin_co': next((c for c in df.columns if 'linkedin' in c.lower() and 'company' in c.lower()), None),
        'job_title': next((c for c in df.columns if any(x in c.lower() for x in ['job', 'title'])), None),
        'seniority': next((c for c in df.columns if 'seniority' in c.lower()), None),
        'email': next((c for c in df.columns if 'email' in c.lower() and 'direct' in c.lower()), None),
        'phone': next((c for c in df.columns if 'phone' in c.lower() and 'direct' in c.lower()), None),
        'linkedin_pers': next((c for c in df.columns if 'linkedin' in c.lower() and 'company' not in c.lower()), None),
    }
    
    # Fallback email
    if not cols_map['email']:
        cols_map['email'] = next((c for c in df.columns if 'email' in c.lower()), None)

    # --- 1. SIC FIT SCORE (0-25 pts) — NUEVO: dinámico ---
    df['SIC_Score'] = 0
    df['SIC_Category'] = '❓ Other'
    
    if cols_map['sic']:
        sic_text = df[cols_map['sic']].astype(str)
        results = sic_text.apply(lambda x: _categorize_sic(x, target_sic))
        df['SIC_Category'] = results.apply(lambda x: x[0])
        df['SIC_Score'] = results.apply(lambda x: x[1])
    
    # --- 2. ACCOUNT FIT SCORE (0-25 pts) ---
    df['Account_Score'] = 0
    
    # 2.1 Tamaño empresa (0-10 pts)
    if cols_map['size']:
        try:
            sizes = pd.to_numeric(df[cols_map['size']], errors='coerce').fillna(0)
            # Bonus por tamaño mínimo del perfil
            df.loc[sizes >= min_emp, 'Account_Score'] += 3
            p75 = sizes.quantile(0.75)
            p50 = sizes.quantile(0.50)
            df.loc[sizes >= p75, 'Account_Score'] += 7
            df.loc[(sizes >= p50) & (sizes < p75), 'Account_Score'] += 4
        except:
            pass
    
    # 2.2 Capacidad económica (0-8 pts)
    if cols_map['financial']:
        try:
            financials = pd.to_numeric(df[cols_map['financial']], errors='coerce').fillna(0)
            p75_fin = financials.quantile(0.75)
            p50_fin = financials.quantile(0.50)
            df.loc[financials >= p75_fin, 'Account_Score'] += 8
            df.loc[(financials >= p50_fin) & (financials < p75_fin), 'Account_Score'] += 4
        except:
            pass

    # 2.3 Señal digital (0-7 pts)
    if cols_map['website']:
        has_web = df[cols_map['website']].notna() & (df[cols_map['website']].astype(str) != '') & (df[cols_map['website']].astype(str) != 'nan')
        df.loc[has_web, 'Account_Score'] += 4
    if cols_map['linkedin_co']:
        has_li_co = df[cols_map['linkedin_co']].notna() & (df[cols_map['linkedin_co']].astype(str) != '')
        df.loc[has_li_co, 'Account_Score'] += 3

    # --- 3. LEAD POWER SCORE (0-30 pts) ---
    df['Lead_Score'] = 0
    
    # 3.1 Role Relevance (0-15 pts) — dinámico desde perfil
    if cols_map['job_title']:
        titles = df[cols_map['job_title']].astype(str).str.lower()
        
        for keyword_regex, points in target_titles.items():
            try:
                matches = titles.str.contains(keyword_regex, na=False, regex=True)
                # Solo asignar si es mayor que lo que ya tiene
                df.loc[matches & (df['Lead_Score'] < points), 'Lead_Score'] = points
            except re.error:
                matches = titles.str.contains(keyword_regex, na=False, regex=False)
                df.loc[matches & (df['Lead_Score'] < points), 'Lead_Score'] = points

    # 3.2 Seniority bonus (0-10 pts)
    seniority_bonus = pd.Series(0, index=df.index)
    if cols_map['seniority']:
        sen = df[cols_map['seniority']].astype(str).str.lower()
        seniority_bonus.loc[sen.str.contains('cxo|owner|partner', na=False)] = 10
        seniority_bonus.loc[sen.str.contains('director', na=False) & (seniority_bonus == 0)] = 7
        seniority_bonus.loc[sen.str.contains('manager|senior', na=False) & (seniority_bonus == 0)] = 4
    elif cols_map['job_title']:
        titles = df[cols_map['job_title']].astype(str).str.lower()
        seniority_bonus.loc[titles.str.contains('senior|chief|head|principal', na=False)] = 7
    
    df['Lead_Score'] = df['Lead_Score'] + seniority_bonus

    # 3.3 Contactabilidad (0-5 pts)
    if cols_map['email']:
        has_email = df[cols_map['email']].astype(str).str.contains('@', na=False)
        generic_domains = ['gmail', 'yahoo', 'hotmail', 'outlook']
        is_generic = df[cols_map['email']].astype(str).str.lower().str.contains('|'.join(generic_domains), na=False)
        df.loc[has_email & ~is_generic, 'Lead_Score'] += 3
        df.loc[has_email & is_generic, 'Lead_Score'] += 1
    if cols_map['phone']:
        has_phone = df[cols_map['phone']].notna() & (df[cols_map['phone']].astype(str) != '')
        df.loc[has_phone, 'Lead_Score'] += 1
    if cols_map['linkedin_pers']:
        has_li = df[cols_map['linkedin_pers']].notna() & (df[cols_map['linkedin_pers']].astype(str) != '')
        df.loc[has_li, 'Lead_Score'] += 1

    # Cap Lead_Score at 30
    df['Lead_Score'] = df['Lead_Score'].clip(upper=30)

    # --- 4. TENDER SCORE (placeholder, rellenado post-matching) ---
    df['Tender_Score'] = 0

    # --- 5. TOTAL SCORE ---
    df['Total_Score'] = df['SIC_Score'] + df['Account_Score'] + df['Lead_Score'] + df['Tender_Score']
    df['Total_Score'] = df['Total_Score'].clip(upper=100)

    # --- 6. CATEGORIZACIÓN ---
    conditions = [
        (df['Total_Score'] >= 55),
        (df['Total_Score'] >= 35),
        (df['Total_Score'] < 35)
    ]
    choices = ['Strategic Account (A)', 'Potential Opportunity (B)', 'Low Priority (C)']
    df['Pipeline_Category'] = np.select(conditions, choices, default='Low Priority (C)')

    # --- 7. COMPATIBILITY ---
    df['Account_Score_Total'] = df['SIC_Score'] + df['Account_Score']
    df['Fit_Score'] = df['Account_Score_Total']

    return df
