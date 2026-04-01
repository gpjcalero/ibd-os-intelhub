"""
IBD OS — Strategic Intelligence Dashboard v6.0 (IntelHub Design)
Premium UI with Market Thermometer, dynamic scoring, web enrichment.
"""
import streamlit as st
import pandas as pd
import numpy as np
import sys
import os
import time
import json
import io
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════════
BUILD_STAMP = "v6.0 — IntelHub"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.normalizer import normalize_company_name
from core.scoring import score_dataframe
from core.ai_research import research_with_openrouter, research_with_ollama
from core.matching import process_tenders
from core.market_thermometer import analyze_market
from core.web_enricher import enrich_company

# ═══════════════════════════════════════════════════════════════════════════════
# PREMIUM CSS (IntelHub Dark Theme)
# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="IBD OS — Strategic Intelligence", page_icon="🤖", layout="wide")

PREMIUM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Base ── */
html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
.stApp {{ background: #f8fafc; color: #1e293b; }}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {{
    background: #ffffff;
    border-right: 1px solid #e2e8f0;
}}
section[data-testid="stSidebar"] .stMarkdown h1 {{ color: #1e3a8a; font-size: 1.4rem; }}
section[data-testid="stSidebar"] .stMarkdown p {{ color: #475569; }}

/* ── KPI Cards ── */
.kpi-row {{ display: flex; gap: 16px; margin: 16px 0 24px 0; }}
.kpi-card {{
    flex: 1;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 20px 24px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    transition: all 0.3s ease;
}}
.kpi-card:hover {{ border-color: #cbd5e1; transform: translateY(-2px); box-shadow: 0 8px 16px rgba(0,0,0,0.06); }}
.kpi-value {{ font-size: 2.2rem; font-weight: 700; color: #0f172a; margin: 4px 0; }}
.kpi-label {{ font-size: 0.85rem; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }}
.kpi-sub {{ font-size: 0.75rem; margin-top: 6px; font-weight: 500; }}
.kpi-sub.green {{ color: #16a34a; }}
.kpi-sub.yellow {{ color: #d97706; }}
.kpi-sub.purple {{ color: #9333ea; }}
.kpi-icon {{ float: right; font-size: 1.6rem; opacity: 0.8; }}

/* ── Section Headers ── */
.section-header {{
    background: #f1f5f9;
    padding: 14px 20px;
    border-left: 4px solid #2563eb;
    border-radius: 8px;
    margin: 28px 0 16px 0;
    font-weight: 600;
    color: #1e293b;
    font-size: 1.05rem;
    letter-spacing: 0.3px;
}}
.section-header.purple {{ border-left-color: #9333ea; background: #faf5ff; }}
.section-header.gold {{ border-left-color: #f59e0b; background: #fffbeb; }}

/* ── Top Bar ── */
.top-bar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 0;
    border-bottom: 1px solid #e2e8f0;
    margin-bottom: 8px;
}}
.top-bar h2 {{ margin: 0; color: #1e3a8a; font-size: 1.8rem; font-weight: 700; letter-spacing: -0.5px; }}
.top-bar .country-badge {{
    display: inline-flex; align-items: center; gap: 6px;
    background: #eff6ff; border: 1px solid #bfdbfe;
    padding: 4px 14px; border-radius: 20px; font-size: 0.85rem; color: #1d4ed8; font-weight: 500;
}}

/* ── Agent Tags ── */
.agent-tag {{
    display: inline-block; padding: 3px 10px; border-radius: 12px;
    font-size: 0.7rem; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase;
}}
.tag-1 {{ background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }}
.tag-2 {{ background: #f3e8ff; color: #6b21a8; border: 1px solid #e9d5ff; }}
.tag-3 {{ background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }}

/* ── Report Card ── */
.report-card {{
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 28px;
    margin: 16px 0;
    box-shadow: 0 4px 6px rgba(0,0,0,0.02);
}}
.report-card h3 {{ color: #1e293b; margin-top: 0; }}
.report-quote {{
    background: #f8fafc;
    border-left: 3px solid #3b82f6;
    padding: 16px 20px;
    border-radius: 0 8px 8px 0;
    margin: 16px 0;
    font-style: italic;
    color: #475569;
    line-height: 1.6;
}}

/* ── Score Bar ── */
.score-bar-container {{
    display: flex; gap: 20px; margin-top: 20px;
    background: #f8fafc; border-radius: 10px; padding: 16px 20px;
    border: 1px solid #e2e8f0;
}}
.score-item {{ flex: 1; }}
.score-item .label {{ font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; }}
.score-item .value {{ font-size: 1.2rem; font-weight: 700; color: #0f172a; margin-top: 4px; }}
.score-item .value.green {{ color: #16a34a; }}

/* ── Evidence & Risk Columns ── */
.evidence-box {{ padding: 12px 0; }}
.evidence-box h4 {{ color: #1e293b; font-size: 0.95rem; margin-bottom: 8px; font-weight: 600; }}
.evidence-box li {{ color: #475569; font-size: 0.9rem; line-height: 1.7; }}

/* ── Recent Reports ── */
.recent-card {{
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 16px;
    transition: all 0.2s ease;
    box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}}
.recent-card:hover {{ border-color: #3b82f6; box-shadow: 0 4px 12px rgba(59,130,246,0.1); }}
.recent-card .name {{ color: #1e293b; font-weight: 600; font-size: 0.95rem; }}
.recent-card .sub {{ color: #64748b; font-size: 0.85rem; }}
.badge-completed {{ background: #dcfce7; color: #166534; padding: 3px 10px; border-radius: 12px; font-size: 0.7rem; font-weight: 600; border: 1px solid #bbf7d0; }}

/* ── Tables ── */
div[data-testid="stDataFrame"] {{ background: #ffffff; border-radius: 10px; overflow: hidden; border: 1px solid #e2e8f0; }}

/* ── Buttons ── */
.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    color: white !important;
    letter-spacing: 0.3px !important;
    transition: all 0.2s ease !important;
}}
.stButton > button[kind="primary"]:hover {{
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(37,99,235,0.3) !important;
}}

/* ── Export Buttons ── */
.stDownloadButton > button, button[kind="secondary"] {{
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    color: #475569 !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}}
.stDownloadButton > button:hover, button[kind="secondary"]:hover {{
    border-color: #cbd5e1 !important;
    background: #f8fafc !important;
    color: #1e293b !important;
}}

/* ── Build Tag ── */
.build-tag {{ position: fixed; bottom: 5px; right: 12px; font-size: 0.65rem; color: #94a3b8; }}

/* ═══ PRINT STYLES (PDF Export) ═══ */
@media print {{
    section[data-testid="stSidebar"],
    .stButton, .stDownloadButton, .stFileUploader,
    .stTextInput, .stSelectbox,
    header, footer, .build-tag,
    [data-testid="stToolbar"] {{ display: none !important; }}
    
    .stApp {{
        background: #ffffff !important;
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
    }}
    .kpi-card, .report-card, .recent-card, .section-header {{
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
        break-inside: avoid;
        box-shadow: none !important;
        border: 1px solid #e2e8f0 !important;
    }}
    .main .block-container {{ padding: 1rem !important; max-width: 100% !important; }}
    
    /* Print header */
    .print-header {{
        display: block !important;
        text-align: center;
        padding: 20px 0;
        border-bottom: 2px solid #2563eb;
        margin-bottom: 20px;
    }}
    .print-footer {{
        display: block !important;
        text-align: center;
        font-size: 0.7rem;
        color: #64748b;
        padding-top: 20px;
        border-top: 1px solid #e2e8f0;
        margin-top: 30px;
    }}
}}
/* Hide print elements on screen */
.print-header, .print-footer {{ display: none; }}
</style>

<div class="print-header">
    <h1 style="color: #58a6ff; margin:0;">🤖 IBD OS — Strategic Intelligence Report</h1>
    <p style="color: #8b949e; margin:4px 0 0 0;">Porcelanosa Grupo — Confidencial — {datetime.now().strftime('%d/%m/%Y')}</p>
</div>
<div class="build-tag">{BUILD_STAMP}</div>
"""

st.markdown(PREMIUM_CSS, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# MATCH ID GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════
import hashlib

def generate_match_id(normalized_name: str) -> str:
    """Genera un ID único determinista basado en el nombre normalizado.
    Mismo nombre normalizado = mismo match_id → permite JOIN entre hojas.
    Formato: MID-XXXXXXXX (8 chars hex)"""
    if not normalized_name or pd.isna(normalized_name):
        return ""
    h = hashlib.md5(str(normalized_name).strip().lower().encode()).hexdigest()[:8]
    return f"MID-{h.upper()}"

# ═══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════════════════════
for key in ['contacts_scored', 'tenders_enriched', 'companies_classified', 'research_cache', 'detected_country', 'contacts_full', 'tenders_full']:
    if key not in st.session_state:
        st.session_state[key] = {} if key == 'research_cache' else None

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR (Premium)
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🤖 IBD OS")
    st.caption("Strategic Intelligence Platform")
    
    # ── SECURITY & AI SETTINGS ──
    api_key_input = st.text_input("🔑 OpenRouter API Key", type="password", placeholder="sk-or-v1-...")
    selected_model = st.selectbox(
        "🧠 AI Model (Agent 3)", 
        [
            "anthropic/claude-3.7-sonnet",
            "anthropic/claude-3.5-haiku",
            "google/gemini-2.5-pro",
            "google/gemini-2.5-flash",
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "deepseek/deepseek-chat",
            "--- Local (Ollama) ---",
            "ollama/qwen3.5:latest",
            "ollama/qwen3:4b",
            "--- Custom Model ---"
        ],
        index=0,
        help="Elige un modelo predefinido o '--- Custom Model ---' para escribir cualquier otro."
    )
    
    # ── CUSTOM MODEL INPUT ──
    if selected_model == "--- Custom Model ---":
        custom_model_str = st.text_input(
            "Escribe el ID exacto de OpenRouter", 
            value="openai/gpt-5.3-pro",
            help="Ej: openai/o3-mini, google/gemini-3.1-pro, moonshotai/moonlight-16b-a3b-instruct"
        )
        final_model = custom_model_str.strip()
    else:
        final_model = selected_model

    if not api_key_input and not final_model.startswith("ollama/"):
        st.warning("Introduce tu OpenRouter API Key para activar la IA completa.", icon="⚠️")
        
    st.markdown("---")
    
    # ── MARKET THERMOMETER (Agent 0) ──
    st.markdown('<span class="agent-tag" style="background:#f97316;">AGENT 0</span> &nbsp; <b>Market Thermometer</b>', unsafe_allow_html=True)
    thermo_country = st.text_input("🌍 País objetivo", placeholder="Ej: Sweden, Vietnam, UAE...")
    thermo_objective = st.selectbox(
        "🎯 Objetivo",
        ["Arquitectos", "Constructores / Promotores", "Interioristas / Contract", 
         "Hoteles / Resorts", "Distribuidores", "Reformistas residencial", "Otro"],
        index=0
    )
    
    if st.button("🌡️ ANALIZAR MERCADO", use_container_width=True):
        if not thermo_country:
            st.error("Introduce un país.")
        else:
            with st.spinner(f"Analizando mercado de {thermo_country}..."):
                result = analyze_market(
                    country=thermo_country,
                    objective=thermo_objective,
                    model_name="qwen3.5:latest"
                )
                st.session_state.thermometer_result = result
                st.rerun()
    
    # Show thermometer result if exists
    if 'thermometer_result' in st.session_state and st.session_state.thermometer_result:
        tr = st.session_state.thermometer_result
        with st.expander(f"🌡️ Resultado: {tr.country} → {tr.objective}", expanded=False):
            st.markdown(f"**Evaluación:** {tr.country_assessment}")
            if tr.recommended_segments:
                st.markdown("**Segmentos recomendados:**")
                for seg in tr.recommended_segments:
                    st.markdown(f"- {seg}")
            if tr.global_db_instructions:
                st.markdown("**Filtros para Global Database:**")
                gdi = tr.global_db_instructions
                if gdi.get('sic_codes'):
                    st.markdown(f"- **SIC Codes:** {', '.join(str(s) for s in gdi['sic_codes'])}")
                if gdi.get('nace_codes'):
                    st.markdown(f"- **NACE Rev.2:** {', '.join(str(s) for s in gdi['nace_codes'])}")
                if gdi.get('gdb_sectors'):
                    st.markdown(f"- **GDB Sectors:** {', '.join(gdi['gdb_sectors'])}")
                if gdi.get('job_titles'):
                    st.markdown(f"- **Job Titles:** {', '.join(gdi['job_titles'])}")
                if gdi.get('seniority'):
                    st.markdown(f"- **Seniority:** {', '.join(gdi['seniority'])}")
                if gdi.get('industry_keywords'):
                    st.markdown(f"- **Keywords:** {', '.join(gdi['industry_keywords'])}")
                if gdi.get('notes'):
                    st.info(gdi['notes'])
            if tr.risks:
                st.markdown("**⚠️ Riesgos:**")
                for r in tr.risks:
                    st.markdown(f"- {r}")
            if tr.opportunities:
                st.markdown("**🟢 Oportunidades:**")
                for o in tr.opportunities:
                    st.markdown(f"- {o}")
    
    st.markdown("---")
    
    # Agent 1
    st.markdown('<span class="agent-tag tag-1">AGENT 1</span> &nbsp; <b>Prospector B2B</b>', unsafe_allow_html=True)
    f_contacts = st.file_uploader("Base de Contactos", type=['xlsx'], key="fc", label_visibility="collapsed")
    
    st.markdown("")
    
    # Agent 2
    st.markdown('<span class="agent-tag tag-2">AGENT 2</span> &nbsp; <b>Matcher B2B</b>', unsafe_allow_html=True)
    f_tenders = st.file_uploader("Licitaciones", type=['xlsx'], key="ft", label_visibility="collapsed")
    
    st.markdown("---")
    
    if st.button("⚡ EJECUTAR AGENTES", type="primary", use_container_width=True):
        if not f_contacts:
            st.error("Sube al menos los contactos.")
        else:
            with st.status("Agentes procesando...", expanded=True) as s:
                # ── Agent 1: Prospector ──
                s.write("🟢 Agent 1 — Scoring contactos...")
                df = pd.read_excel(f_contacts)
                comp_col = next((c for c in df.columns if 'company' in c.lower()), df.columns[0])
                df['Normalized_Company'] = df[comp_col].astype(str).apply(normalize_company_name)
                
                # Pass scoring_profile from Thermometer if available
                scoring_profile = None
                if 'thermometer_result' in st.session_state and st.session_state.thermometer_result:
                    scoring_profile = st.session_state.thermometer_result.scoring_profile
                    s.write(f"🌡️ Usando perfil del Termómetro: {st.session_state.thermometer_result.country}")
                
                df_scored = score_dataframe(df, scoring_profile=scoring_profile)
                
                # ── MATCH ID: Clave de cruce para JOIN ──
                df_scored['match_id'] = df_scored['Normalized_Company'].apply(generate_match_id)
                
                # Detect country
                country_col = next((c for c in df.columns if 'country' in c.lower()), None)
                if country_col:
                    top_country = df[country_col].value_counts().index[0] if not df[country_col].isna().all() else "Global"
                    st.session_state.detected_country = str(top_country)
                else:
                    st.session_state.detected_country = "Global"
                
                # ── Agent 2: Matcher ──
                if f_tenders:
                    s.write("🟣 Agent 2 — Cruzando licitaciones...")
                    df_t = pd.read_excel(f_tenders)
                    df_tenders_matched = process_tenders(df_t, df_scored)
                    
                    # Añadir match_id a tenders (basado en matched_company normalizado)
                    df_tenders_matched['match_id'] = df_tenders_matched['matched_company'].apply(
                        lambda x: generate_match_id(normalize_company_name(str(x))) if pd.notna(x) and x != '' else ''
                    )
                    
                    st.session_state.tenders_enriched = df_tenders_matched
                    st.session_state.tenders_full = df_tenders_matched  # Guardamos TODO con columnas originales
                    
                    valid_matches = df_tenders_matched[df_tenders_matched['match_level'].isin(['Seguro', 'Probable'])]
                    if not valid_matches.empty:
                        matched_companies = valid_matches['matched_company'].unique()
                        mask = df_scored[comp_col].isin(matched_companies)
                        df_scored.loc[mask, 'Tender_Score'] = 20
                        df_scored['Total_Score'] = df_scored['SIC_Score'] + df_scored['Account_Score'] + df_scored['Lead_Score'] + df_scored['Tender_Score']
                        df_scored['Total_Score'] = df_scored['Total_Score'].clip(upper=100)
                        s.write(f"✅ {len(matched_companies)} empresas vinculadas a licitaciones")
                
                # ── Ranking (para tabla visual) ──
                s.write("📊 Generando pipeline...")
                web_col = next((c for c in df_scored.columns if 'web' in c.lower()), '')
                
                agg = {
                    comp_col: lambda x: x.mode()[0] if not x.empty else x.iloc[0],
                    'Total_Score': 'max', 'SIC_Score': 'max', 'Account_Score': 'max', 'Lead_Score': 'max', 'Tender_Score': 'max',
                    'SIC_Category': 'first',
                    'Pipeline_Category': lambda x: x.mode()[0] if not x.empty else 'C',
                    'match_id': 'first'
                }
                if web_col: agg[web_col] = 'first'
                
                ranking = df_scored.groupby('Normalized_Company').agg(agg).reset_index()
                rename = {comp_col: 'Empresa', 'Pipeline_Category': 'Categoría', 'SIC_Score': 'SIC', 'Account_Score': 'Account', 'Lead_Score': 'Lead', 'Tender_Score': 'Tender', 'SIC_Category': 'Tipo'}
                if web_col: rename[web_col] = 'Website'
                ranking = ranking.rename(columns=rename)
                
                st.session_state.contacts_scored = df_scored
                st.session_state.contacts_full = df_scored  # TODOS los datos originales + scores + match_id
                st.session_state.companies_classified = ranking.sort_values('Total_Score', ascending=False)
                s.update(label="✅ Pipeline listo", state="complete")
                time.sleep(0.5)
                st.rerun()
    
    st.markdown("---")
    st.caption("👤 Admin User")
    st.caption("Porcelanosa B2B")

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ═══════════════════════════════════════════════════════════════════════════════

if st.session_state.companies_classified is None:
    st.markdown("""
    <div style="text-align:center; padding: 80px 20px;">
        <h1 style="color: #58a6ff; font-size: 2.5rem;">🤖 Strategic Intelligence</h1>
        <p style="color: #8b949e; font-size: 1.1rem; max-width: 500px; margin: 16px auto;">
            Sube tus bases de datos en el panel lateral para activar los agentes de análisis.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

df_ranking = st.session_state.companies_classified
country = st.session_state.detected_country or "Global"

# ── TOP BAR ──
st.markdown(f"""
<div class="top-bar">
    <h2>Strategic Intelligence</h2>
    <span class="country-badge">🌍 {country}</span>
</div>
""", unsafe_allow_html=True)

# ── KPI CARDS ──
total_firms = len(df_ranking)
top_tier = len(df_ranking[df_ranking['Categoría'] == 'Strategic Account (A)'])
n_tenders = len(st.session_state.tenders_enriched) if st.session_state.tenders_enriched is not None else 0
n_matches = len(st.session_state.tenders_enriched[st.session_state.tenders_enriched['match_level'].isin(['Seguro', 'Probable'])]) if st.session_state.tenders_enriched is not None else 0

st.markdown(f"""
<div class="kpi-row">
    <div class="kpi-card">
        <span class="kpi-icon">📊</span>
        <div class="kpi-label">Total Firms Analyzed</div>
        <div class="kpi-value">{total_firms:,}</div>
        <div class="kpi-sub green">Pipeline completo</div>
    </div>
    <div class="kpi-card">
        <span class="kpi-icon">⭐</span>
        <div class="kpi-label">Top Tier Firms (A)</div>
        <div class="kpi-value">{top_tier}</div>
        <div class="kpi-sub yellow">Alto valor potencial</div>
    </div>
    <div class="kpi-card">
        <span class="kpi-icon">📋</span>
        <div class="kpi-label">Active Tenders</div>
        <div class="kpi-value">{n_tenders}</div>
        <div class="kpi-sub green">{'Cargadas' if n_tenders > 0 else 'Sin cargar'}</div>
    </div>
    <div class="kpi-card">
        <span class="kpi-icon">🔗</span>
        <div class="kpi-label">Matches Detected</div>
        <div class="kpi-value">{n_matches}</div>
        <div class="kpi-sub purple">{'Pendientes de revisión' if n_matches > 0 else '—'}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── PIPELINE TABLE ──
st.markdown('<div class="section-header">🏆 PIPELINE ESTRATÉGICO</div>', unsafe_allow_html=True)

search = st.text_input("🔍", placeholder="Buscar empresa por nombre...", label_visibility="collapsed")
df_show = df_ranking[df_ranking['Empresa'].str.contains(search, case=False, na=False)] if search else df_ranking

st.dataframe(
    df_show,
    use_container_width=True, height=350, hide_index=True,
    column_config={
        "Total_Score": st.column_config.ProgressColumn("Score Total", min_value=0, max_value=100, format="%d"),
        "Account": st.column_config.NumberColumn("🏢 Account", help="Sector + Tamaño + Web (0-50)"),
        "Lead": st.column_config.NumberColumn("👤 Lead", help="Cargo + Seniority + Contacto (0-30)"),
        "Tender": st.column_config.NumberColumn("📋 Tender", help="Licitaciones vinculadas (0-20)"),
        "Website": st.column_config.LinkColumn("🌐 Web")
    }
)

# ── EXPORT BUTTONS ──
exp1, exp2, exp3 = st.columns([1, 1, 4])

with exp1:
    # ── EXCEL MULTI-SHEET (Contactos + Licitaciones con match_id) ──
    def generate_excel():
        """Genera Excel con 2 hojas: Contactos (scored) + Licitaciones (matched).
        Ambas llevan match_id para JOIN cruzado."""
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # ── HOJA 1: CONTACTOS (todos los datos originales + scores + match_id) ──
            df_contacts = st.session_state.contacts_full.copy()
            
            # Reordenar: match_id primero, luego scores, luego el resto
            score_cols = ['match_id', 'Total_Score', 'Account_Score', 'Lead_Score', 'Tender_Score', 'Pipeline_Category', 'Normalized_Company']
            existing_score_cols = [c for c in score_cols if c in df_contacts.columns]
            other_cols = [c for c in df_contacts.columns if c not in score_cols]
            df_contacts = df_contacts[existing_score_cols + other_cols]
            
            df_contacts.to_excel(writer, sheet_name='Contactos', index=False)
            
            # ── HOJA 2: LICITACIONES (todos los datos originales + match results + match_id) ──
            if st.session_state.tenders_full is not None:
                df_tenders = st.session_state.tenders_full.copy()
                
                # Reordenar: match_id primero, luego match results, luego el resto
                match_cols = ['match_id', 'matched_company', 'match_level', 'match_score', 'match_reason']
                existing_match_cols = [c for c in match_cols if c in df_tenders.columns]
                other_cols = [c for c in df_tenders.columns if c not in match_cols]
                df_tenders = df_tenders[existing_match_cols + other_cols]
                
                df_tenders.to_excel(writer, sheet_name='Licitaciones', index=False)
        
        return output.getvalue()
    
    if st.session_state.contacts_full is not None:
        xlsx_data = generate_excel()
        st.download_button(
            "📊 Exportar Excel",
            data=xlsx_data,
            file_name=f"IBD_OS_{country}_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

with exp2:
    if st.button("📄 Exportar PDF", key="pdf_btn"):
        st.components.v1.html(
            "<script>window.parent.print();</script>",
            height=0, width=0
        )
        st.success("🖨️ Generando vista de impresión... (Si no abre, usa Ctrl+P)")

# ── SELECT TARGET + AGENT 3 ──
st.markdown("---")
c_sel, c_act = st.columns([2, 1])

with c_sel:
    selected_comp = st.selectbox("🎯 SELECT TARGET", df_show['Empresa'].unique(), label_visibility="collapsed")

with c_act:
    st.markdown('<span class="agent-tag tag-3">AGENT 3</span> &nbsp; <b>Commercial Strategist</b>', unsafe_allow_html=True)
    if st.button("🧠 GENERATE SALES STRATEGY", type="primary", use_container_width=True):
        with st.spinner("Strategist Agent analyzing..."):
            if not api_key_input and not final_model.startswith("ollama/"):
                st.error("Error: Se requiere una API Key en la barra lateral (no necesaria para modelos locales).")
            else:
                comp_norm = df_show[df_show['Empresa'] == selected_comp]['Normalized_Company'].iloc[0]
                contact_rows = st.session_state.contacts_scored[st.session_state.contacts_scored['Normalized_Company'] == comp_norm]
                best_contact = contact_rows.sort_values('Lead_Score', ascending=False).iloc[0]
                
                c_name_col = next((c for c in best_contact.index if 'name' in c.lower()), '')
                c_job_col = next((c for c in best_contact.index if 'job' in c.lower() or 'title' in c.lower()), '')
                
                if final_model.startswith("ollama/"):
                    model_id = final_model.replace("ollama/", "")
                    res = research_with_ollama(
                        model_name=model_id,
                        company_name=selected_comp,
                        country=str(best_contact.get('Country', '')),
                        contact_name=str(best_contact.get(c_name_col, '')),
                        contact_title=str(best_contact.get(c_job_col, ''))
                    )
                else:
                    res = research_with_openrouter(
                        api_key=api_key_input, company_name=selected_comp,
                        model_name=final_model,
                        country=str(best_contact.get('Country', '')),
                        contact_name=str(best_contact.get(c_name_col, '')),
                        contact_title=str(best_contact.get(c_job_col, ''))
                    )
                
                if res:
                    cache_key = f"{selected_comp}_{final_model}"
                    st.session_state.research_cache[cache_key] = {'result': res, 'model': final_model}
                    st.rerun()

# ── STRATEGIC REPORT (Agent 3 Output) ──
cache_key = f"{selected_comp}_{final_model}" if selected_comp else None
if cache_key and cache_key in st.session_state.research_cache:
    cached = st.session_state.research_cache[cache_key]
    res = cached['result']
    used_model = cached.get('model', 'unknown')
    
    st.markdown(f'<div class="section-header gold">🧠 STRATEGIC REPORT: {selected_comp}</div>', unsafe_allow_html=True)
    
    # Report Card with model badge
    model_badge = used_model.split('/')[-1] if '/' in used_model else used_model
    st.markdown(f"""
    <div class="report-card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <h3>Executive Analysis</h3>
            <span style="background:#f0f9ff; border:1px solid #bae6fd; color:#0369a1; padding:3px 10px; border-radius:12px; font-size:0.7rem; font-weight:600;">🤖 {model_badge}</span>
        </div>
        <div class="report-quote">{res.summary}</div>
        <div class="score-bar-container">
            <div class="score-item">
                <div class="label">Confidence</div>
                <div class="value">{res.confidence.upper()}</div>
            </div>
            <div class="score-item">
                <div class="label">Recommended Approach</div>
                <div class="value" style="font-size:0.85rem; font-weight:400;">{res.recommended_approach[:80]}...</div>
            </div>
            <div class="score-item">
                <div class="label">Status</div>
                <div class="value green">● Ready for Outreach</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Evidence & Risks
    col_e, col_r = st.columns(2)
    with col_e:
        st.markdown("##### ✅ Evidencias Clave")
        for k in res.key_facts:
            st.markdown(f"- {k}")
    with col_r:
        if res.risks:
            st.markdown("##### ⚠️ Riesgos / Objeciones")
            for r in res.risks:
                st.markdown(f"- {r}")
    
    # Communication Drafts
    with st.expander(f"📬 BORRADORES PARA {selected_comp} (Listos para enviar)", expanded=True):
        t1, t2 = st.tabs(["📧 Email B2B (Valor)", "🔗 LinkedIn Conexión"])
        with t1:
            st.text_area("", value=res.email_draft, height=200, key="email_area")
        with t2:
            st.text_area("", value=res.linkedin_draft, height=150, key="li_area")

# ── MATCHER SECTION ──
if st.session_state.tenders_enriched is not None and selected_comp:
    st.markdown('<div class="section-header purple">🔗 MATCHER B2B: Licitaciones Vinculadas</div>', unsafe_allow_html=True)
    
    matches = st.session_state.tenders_enriched[
        st.session_state.tenders_enriched['matched_company'].astype(str).str.contains(selected_comp, case=False, na=False)
    ]
    
    if not matches.empty:
        display_cols = ['match_level', 'match_score', 'match_reason']
        for candidate in ['Project Name', 'Name', 'Office Name', 'tender_name', 'Description', 'City', 'Country']:
            if candidate in matches.columns:
                display_cols.insert(0, candidate)
        if len(display_cols) == 3:
            orig_cols = [c for c in matches.columns if c not in ['match_level','match_score','match_reason','matched_company','contact_email','contact_phone','contact_linkedin']]
            if orig_cols: display_cols.insert(0, orig_cols[0])
        
        st.success(f"✅ {len(matches)} licitaciones vinculadas")
        st.dataframe(matches[display_cols], use_container_width=True, hide_index=True)
    else:
        st.caption("No se han detectado licitaciones para esta cuenta.")

# ── RECENT ANALYSIS REPORTS ──
if st.session_state.research_cache:
    st.markdown('<div class="section-header">📋 Recent Analysis Reports</div>', unsafe_allow_html=True)
    
    cache_items = list(st.session_state.research_cache.items())
    cols = st.columns(min(len(cache_items), 3))
    
    for i, (name, res) in enumerate(cache_items[:3]):
        with cols[i]:
            st.markdown(f"""
            <div class="recent-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size:1.2rem;">🏢</span>
                    <span class="badge-completed">Completed</span>
                </div>
                <div class="name" style="margin-top:8px;">{name}</div>
                <div class="sub">{res.confidence.upper()} confidence</div>
            </div>
            """, unsafe_allow_html=True)

# ── PRINT FOOTER ──
st.markdown(f"""
<div class="print-footer">
    IBD OS — Strategic Intelligence Platform — Porcelanosa Grupo — Confidencial — {datetime.now().strftime('%d/%m/%Y %H:%M')}
</div>
""", unsafe_allow_html=True)
