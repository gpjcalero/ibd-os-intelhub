"""
AGENTE 1: PROSPECTOR B2B (SCORING ENGINE)
Versión vectorizada optimizada para despliegue web.
Implementa la lógica estricta definida en '01-prospector-b2b.md'.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional

def score_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Motor de Scoring del Agente Prospector B2B.
    Calcula:
    1. Account Fit Score (0-50)
    2. Lead Power Score (0-30)
    
    El score final (0-100) se completa tras el cruce con tenders (+20).
    """
    # Evitar SettingWithCopyWarning
    df = df.copy()

    # --- 0. NORMALIZACIÓN DE COLUMNAS (Búsqueda inteligente) ---
    cols_map = {
        'sector': next((c for c in df.columns if any(x in c.lower() for x in ['sic', 'activity', 'industry', 'sector'])), None),
        'size': next((c for c in df.columns if any(x in c.lower() for x in ['employee', 'staff', 'size'])), None),
        'financial': next((c for c in df.columns if any(x in c.lower() for x in ['turnover', 'profit', 'revenue', 'sales'])), None),
        'website': next((c for c in df.columns if 'web' in c.lower()), None),
        'linkedin_co': next((c for c in df.columns if 'linkedin' in c.lower() and 'company' in c.lower()), None),
        'job_title': next((c for c in df.columns if any(x in c.lower() for x in ['job', 'title', 'role'])), None),
        'seniority': next((c for c in df.columns if 'seniority' in c.lower()), None),
        'email': next((c for c in df.columns if 'email' in c.lower() and 'direct' in c.lower()), None), # Prioridad direct
        'phone': next((c for c in df.columns if 'phone' in c.lower() and 'direct' in c.lower()), None),
        'linkedin_pers': next((c for c in df.columns if 'linkedin' in c.lower() and 'company' not in c.lower()), None)
    }
    
    # Fallback para email genérico si no hay directo explícito
    if not cols_map['email']:
        cols_map['email'] = next((c for c in df.columns if 'email' in c.lower()), None)

    # --- 1. ACCOUNT FIT SCORE (0-50 pts) ---
    df['Account_Score'] = 0
    
    # 1.1 Sector Fit (0-20 pts)
    if cols_map['sector']:
        sector_text = df[cols_map['sector']].astype(str).str.lower()
        # High Priority (20 pts): Arquitectura, Construcción, Real Estate
        high_prio = sector_text.str.contains('architect|arquitect|construct|build|real estate|inmobiliaria|promot|develop', na=False)
        df.loc[high_prio, 'Account_Score'] += 20
        # Med Priority (10 pts): Retail, Hospitality, Design
        med_prio = sector_text.str.contains('retail|hospitality|hotel|design|interior', na=False) & ~high_prio
        df.loc[med_prio, 'Account_Score'] += 10
    
    # 1.2 Tamaño (0-10 pts)
    if cols_map['size']:
        # Intentamos extraer números si es string
        try:
            sizes = pd.to_numeric(df[cols_map['size']], errors='coerce').fillna(0)
            # Percentiles simples del dataset
            p75 = sizes.quantile(0.75)
            p50 = sizes.quantile(0.50)
            df.loc[sizes >= p75, 'Account_Score'] += 10
            df.loc[(sizes >= p50) & (sizes < p75), 'Account_Score'] += 5
        except:
            pass # Si falla conversión numérica, 0 pts
            
    # 1.3 Capacidad Económica (0-10 pts) - Similar lógica
    if cols_map['financial']:
        try:
            financials = pd.to_numeric(df[cols_map['financial']], errors='coerce').fillna(0)
            p75_fin = financials.quantile(0.75)
            df.loc[financials >= p75_fin, 'Account_Score'] += 10
        except:
            pass

    # 1.4 Señal Digital (0-10 pts)
    if cols_map['website']:
        has_web = df[cols_map['website']].notna() & (df[cols_map['website']] != '')
        df.loc[has_web, 'Account_Score'] += 5
    if cols_map['linkedin_co']:
        has_li_co = df[cols_map['linkedin_co']].notna() & (df[cols_map['linkedin_co']] != '')
        df.loc[has_li_co, 'Account_Score'] += 5

    # --- 2. LEAD POWER SCORE (0-30 pts) ---
    df['Lead_Score'] = 0
    
    # 2.1 Role Relevance (0-15 pts)
    if cols_map['job_title']:
        titles = df[cols_map['job_title']].astype(str).str.lower()
        # Decision Makers (15 pts)
        decision = titles.str.contains('ceo|director|head|lead|manager|gerente|owner|founder|socio|partner|arquitecto|architect', na=False)
        df.loc[decision, 'Lead_Score'] += 15
        # Influencers (8 pts)
        influencer = titles.str.contains('designer|interior|compras|purchase|procurement|engineer|técnico', na=False) & ~decision
        df.loc[influencer, 'Lead_Score'] += 8

    # 2.2 Seniority (0-10 pts)
    # Si tenemos columna explicita, la usamos. Si no, inferimos del título
    is_senior = titles.str.contains('senior|chief|head|principal', na=False) if cols_map['job_title'] else pd.Series(False, index=df.index)
    df.loc[is_senior, 'Lead_Score'] += 10

    # 2.3 Reachability (0-5 pts)
    if cols_map['email']:
        has_email = df[cols_map['email']].astype(str).str.contains('@', na=False)
        # Penalizar genéricos
        generic_domains = ['gmail', 'yahoo', 'hotmail', 'outlook']
        is_generic = df[cols_map['email']].astype(str).str.lower().str.contains('|'.join(generic_domains), na=False)
        
        # 3 pts por email corporativo, 1 por genérico
        df.loc[has_email & ~is_generic, 'Lead_Score'] += 3
        df.loc[has_email & is_generic, 'Lead_Score'] += 1
        
    if cols_map['phone']:
        has_phone = df[cols_map['phone']].notna() & (df[cols_map['phone']] != '')
        df.loc[has_phone, 'Lead_Score'] += 1
        
    if cols_map['linkedin_pers']:
        has_li_pers = df[cols_map['linkedin_pers']].notna() & (df[cols_map['linkedin_pers']] != '')
        df.loc[has_li_pers, 'Lead_Score'] += 1

    # --- 3. TENDER OPPORTUNITY SCORE (Placeholder 0-20) ---
    # Esto se rellena tras el matching
    df['Tender_Score'] = 0 
    
    # --- 4. TOTAL SCORE ---
    # Cap en 100 por seguridad
    df['Total_Score'] = df['Account_Score'] + df['Lead_Score'] + df['Tender_Score']
    df['Total_Score'] = df['Total_Score'].clip(upper=100)
    
    # --- 5. CATEGORIZACIÓN ---
    conditions = [
        (df['Total_Score'] >= 60),
        (df['Total_Score'] >= 40),
        (df['Total_Score'] < 40)
    ]
    choices = ['Strategic Account (A)', 'Potential Opportunity (B)', 'Low Priority (C)']
    df['Pipeline_Category'] = np.select(conditions, choices, default='Low Priority (C)')
    
    # --- 6. AGREGAMOS FIT_SCORE LEGACY ---
    # Para compatibilidad con gráficos existentes que usan 'Fit_Score'
    df['Fit_Score'] = df['Account_Score'] 

    return df
