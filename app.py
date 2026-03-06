"""
IBD OS — Strategic Intelligence Dashboard v5.0 (IntelHub Design)
Premium UI with KPI cards, glassmorphism, export features.
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
GEMINI_API_KEY = "AIzaSyCbWyJvuBEjlybS7kmL4EUekb5-nrt2pao"
BUILD_STAMP = "v5.0 — IntelHub"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.normalizer import normalize_company_name
from core.scoring import score_dataframe
from core.ai_research import research_with_gemini_rest
from core.matching import process_tenders

# ═══════════════════════════════════════════════════════════════════════════════
# PREMIUM CSS (IntelHub Dark Theme)
# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="IBD OS — Strategic Intelligence", page_icon="🤖", layout="wide")

PREMIUM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Base ── */
html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
.stApp {{ background: linear-gradient(135deg, #0a0e1a 0%, #0d1321 50%, #0a0f1e 100%); color: #c9d1d9; }}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #0d1117 0%, #0f1520 100%);
    border-right: 1px solid rgba(56,139,253,0.15);
}}
section[data-testid="stSidebar"] .stMarkdown h1 {{ color: #58a6ff; font-size: 1.4rem; }}

/* ── KPI Cards ── */
.kpi-row {{ display: flex; gap: 16px; margin: 16px 0 24px 0; }}
.kpi-card {{
    flex: 1;
    background: linear-gradient(135deg, rgba(22,27,34,0.9) 0%, rgba(13,17,23,0.95) 100%);
    border: 1px solid rgba(56,139,253,0.12);
    border-radius: 12px;
    padding: 20px 24px;
    backdrop-filter: blur(12px);
    transition: all 0.3s ease;
}}
.kpi-card:hover {{ border-color: rgba(56,139,253,0.35); transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.3); }}
.kpi-value {{ font-size: 2.2rem; font-weight: 700; color: #e6edf3; margin: 4px 0; }}
.kpi-label {{ font-size: 0.85rem; color: #8b949e; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }}
.kpi-sub {{ font-size: 0.75rem; margin-top: 6px; }}
.kpi-sub.green {{ color: #3fb950; }}
.kpi-sub.yellow {{ color: #d29922; }}
.kpi-sub.purple {{ color: #bc8cff; }}
.kpi-icon {{ float: right; font-size: 1.6rem; opacity: 0.6; }}

/* ── Section Headers ── */
.section-header {{
    background: linear-gradient(90deg, rgba(22,27,34,0.95) 0%, rgba(13,17,23,0.8) 100%);
    padding: 14px 20px;
    border-left: 4px solid #238636;
    border-radius: 8px;
    margin: 28px 0 16px 0;
    font-weight: 600;
    color: #e6edf3;
    font-size: 1.05rem;
    letter-spacing: 0.3px;
}}
.section-header.purple {{ border-left-color: #8957e5; }}
.section-header.gold {{ border-left-color: #d29922; }}

/* ── Top Bar ── */
.top-bar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 0;
    border-bottom: 1px solid rgba(48,54,61,0.6);
    margin-bottom: 8px;
}}
.top-bar h2 {{ margin: 0; color: #e6edf3; font-size: 1.5rem; font-weight: 600; }}
.top-bar .country-badge {{
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(56,139,253,0.1); border: 1px solid rgba(56,139,253,0.2);
    padding: 4px 14px; border-radius: 20px; font-size: 0.8rem; color: #58a6ff;
}}

/* ── Agent Tags ── */
.agent-tag {{
    display: inline-block; padding: 3px 10px; border-radius: 12px;
    font-size: 0.7rem; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase;
}}
.tag-1 {{ background: linear-gradient(135deg, #238636, #2ea043); color: white; }}
.tag-2 {{ background: linear-gradient(135deg, #8957e5, #a371f7); color: white; }}
.tag-3 {{ background: linear-gradient(135deg, #d29922, #e3b341); color: #0d1117; }}

/* ── Report Card ── */
.report-card {{
    background: linear-gradient(135deg, rgba(22,27,34,0.95) 0%, rgba(13,17,23,0.9) 100%);
    border: 1px solid rgba(56,139,253,0.1);
    border-radius: 12px;
    padding: 28px;
    margin: 16px 0;
}}
.report-card h3 {{ color: #e6edf3; margin-top: 0; }}
.report-quote {{
    background: rgba(56,139,253,0.04);
    border-left: 3px solid #58a6ff;
    padding: 16px 20px;
    border-radius: 0 8px 8px 0;
    margin: 16px 0;
    font-style: italic;
    color: #8b949e;
    line-height: 1.6;
}}

/* ── Score Bar ── */
.score-bar-container {{
    display: flex; gap: 20px; margin-top: 20px;
    background: rgba(13,17,23,0.6); border-radius: 10px; padding: 16px 20px;
    border: 1px solid rgba(48,54,61,0.4);
}}
.score-item {{ flex: 1; }}
.score-item .label {{ font-size: 0.7rem; color: #8b949e; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; }}
.score-item .value {{ font-size: 1.1rem; font-weight: 700; color: #e6edf3; margin-top: 4px; }}
.score-item .value.green {{ color: #3fb950; }}

/* ── Evidence & Risk Columns ── */
.evidence-box {{ padding: 12px 0; }}
.evidence-box h4 {{ color: #e6edf3; font-size: 0.9rem; margin-bottom: 8px; }}
.evidence-box li {{ color: #8b949e; font-size: 0.85rem; line-height: 1.7; }}

/* ── Recent Reports ── */
.recent-card {{
    background: rgba(22,27,34,0.9);
    border: 1px solid rgba(48,54,61,0.5);
    border-radius: 10px;
    padding: 16px;
    transition: all 0.2s ease;
}}
.recent-card:hover {{ border-color: rgba(56,139,253,0.3); }}
.recent-card .name {{ color: #e6edf3; font-weight: 600; font-size: 0.95rem; }}
.recent-card .sub {{ color: #8b949e; font-size: 0.8rem; }}
.badge-completed {{ background: #238636; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.65rem; font-weight: 600; }}

/* ── Tables ── */
div[data-testid="stDataFrame"] {{ background: transparent; border-radius: 10px; overflow: hidden; }}

/* ── Buttons ── */
.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, #da3633 0%, #f85149 100%) !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    letter-spacing: 0.3px !important;
    transition: all 0.2s ease !important;
}}
.stButton > button[kind="primary"]:hover {{
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px rgba(248,81,73,0.3) !important;
}}

/* ── Export Buttons ── */
.stDownloadButton > button {{
    background: linear-gradient(135deg, rgba(56,139,253,0.15), rgba(56,139,253,0.08)) !important;
    border: 1px solid rgba(56,139,253,0.3) !important;
    color: #58a6ff !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
}}

/* ── Build Tag ── */
.build-tag {{ position: fixed; bottom: 5px; right: 12px; font-size: 0.65rem; color: #30363d; }}

/* ═══ PRINT STYLES (PDF Export) ═══ */
@media print {{
    section[data-testid="stSidebar"],
    .stButton, .stDownloadButton, .stFileUploader,
    .stTextInput, .stSelectbox,
    header, footer, .build-tag,
    [data-testid="stToolbar"] {{ display: none !important; }}
    
    .stApp {{
        background: #0a0e1a !important;
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
    }}
    .kpi-card, .report-card, .recent-card, .section-header {{
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
        break-inside: avoid;
    }}
    .main .block-container {{ padding: 1rem !important; max-width: 100% !important; }}
    
    /* Print header */
    .print-header {{
        display: block !important;
        text-align: center;
        padding: 20px 0;
        border-bottom: 2px solid #238636;
        margin-bottom: 20px;
    }}
    .print-footer {{
        display: block !important;
        text-align: center;
        font-size: 0.7rem;
        color: #484f58;
        padding-top: 20px;
        border-top: 1px solid #30363d;
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
                df_scored = score_dataframe(df)
                
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
                        df_scored['Total_Score'] = df_scored['Account_Score'] + df_scored['Lead_Score'] + df_scored['Tender_Score']
                        df_scored['Total_Score'] = df_scored['Total_Score'].clip(upper=100)
                        s.write(f"✅ {len(matched_companies)} empresas vinculadas a licitaciones")
                
                # ── Ranking (para tabla visual) ──
                s.write("📊 Generando pipeline...")
                web_col = next((c for c in df_scored.columns if 'web' in c.lower()), '')
                
                agg = {
                    comp_col: lambda x: x.mode()[0] if not x.empty else x.iloc[0],
                    'Total_Score': 'max', 'Account_Score': 'max', 'Lead_Score': 'max', 'Tender_Score': 'max',
                    'Pipeline_Category': lambda x: x.mode()[0] if not x.empty else 'C',
                    'match_id': 'first'
                }
                if web_col: agg[web_col] = 'first'
                
                ranking = df_scored.groupby('Normalized_Company').agg(agg).reset_index()
                rename = {comp_col: 'Empresa', 'Pipeline_Category': 'Categoría', 'Account_Score': 'Account', 'Lead_Score': 'Lead', 'Tender_Score': 'Tender'}
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
            comp_norm = df_show[df_show['Empresa'] == selected_comp]['Normalized_Company'].iloc[0]
            contact_rows = st.session_state.contacts_scored[st.session_state.contacts_scored['Normalized_Company'] == comp_norm]
            best_contact = contact_rows.sort_values('Lead_Score', ascending=False).iloc[0]
            
            c_name_col = next((c for c in best_contact.index if 'name' in c.lower()), '')
            c_job_col = next((c for c in best_contact.index if 'job' in c.lower() or 'title' in c.lower()), '')
            
            res = research_with_gemini_rest(
                api_key=GEMINI_API_KEY, company_name=selected_comp,
                model_name="gemini-3-pro-preview",
                country=str(best_contact.get('Country', '')),
                contact_name=str(best_contact.get(c_name_col, '')),
                contact_title=str(best_contact.get(c_job_col, ''))
            )
            if res:
                st.session_state.research_cache[selected_comp] = res
                st.rerun()

# ── STRATEGIC REPORT (Agent 3 Output) ──
if selected_comp and selected_comp in st.session_state.research_cache:
    res = st.session_state.research_cache[selected_comp]
    
    st.markdown(f'<div class="section-header gold">🧠 STRATEGIC REPORT: {selected_comp}</div>', unsafe_allow_html=True)
    
    # Report Card
    st.markdown(f"""
    <div class="report-card">
        <h3>Executive Analysis</h3>
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
