"""
PORCELANOSA OS - Core: Web Research Engine
Skills 6-8: Company Deep Research, Relevance Mapper, Next Best Action
"""

import re
import json
import uuid
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd


@dataclass
class ResearchSource:
    """Una fuente de investigación."""
    url: str
    title: str
    snippet: str
    accessed_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ResearchFact:
    """Un hecho verificable extraído."""
    fact: str
    source_url: str
    confidence: str  # 'high', 'medium', 'low'
    category: str    # 'project', 'team', 'market', 'financial', 'news', 'signal'


@dataclass
class ResearchSnapshot:
    """Snapshot completo de investigación."""
    snapshot_id: str
    entity_type: str
    entity_id: str
    entity_name: str
    
    # Fuentes
    sources: List[ResearchSource]
    
    # Hechos extraídos
    facts: List[ResearchFact]
    
    # Análisis
    summary: str
    quality_grade: str  # 'rich', 'moderate', 'sparse', 'insufficient'
    
    # Porcelanosa-specific
    porcelanosa_fit: str
    decision_maker_hypothesis: str
    timing_signals: str
    value_proposition: str
    why_porcelanosa: str
    
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class OutreachDraft:
    """Borrador de comunicación."""
    channel: str  # 'linkedin', 'email', 'call'
    content: str
    key_facts_used: List[str]
    call_to_action: str


# ============================================
# SKILL 6: Company Deep Research (Web)
# ============================================

# Templates de hechos por tipo de empresa (para demo sin API)
RESEARCH_TEMPLATES = {
    'architect': {
        'facts': [
            "Estudio fundado hace más de 10 años con presencia consolidada en el mercado",
            "Portfolio incluye proyectos de hospitality premium y residencial de lujo",
            "Equipo multidisciplinar con departamentos de arquitectura e interiorismo",
            "Proyectos activos en múltiples países del sudeste asiático",
            "Colaboraciones previas con operadores hoteleros internacionales",
            "Certificaciones en sostenibilidad (LEED/BREEAM) en varios proyectos",
            "Presencia activa en LinkedIn con actualizaciones de proyectos recientes",
            "Participación en ferias y eventos del sector construcción"
        ],
        'signals': [
            "Fase de crecimiento con nuevos proyectos anunciados",
            "Búsqueda de partners para proyectos internacionales",
            "Interés declarado en materiales premium y sostenibles"
        ]
    },
    'developer': {
        'facts': [
            "Promotora con landbank activo en destinos turísticos clave",
            "Pipeline de desarrollo incluye hoteles y residencial de alto standing",
            "Experiencia en proyectos turnkey y gestión integral",
            "Alianzas con operadores hoteleros internacionales",
            "Facturación consolidada superior a $50M anuales",
            "Equipo de procurement centralizado para proyectos múltiples",
            "Expansión anunciada a nuevos mercados regionales"
        ],
        'signals': [
            "Nuevos proyectos en fase de diseño/prescripción",
            "Reclutando perfiles de project management",
            "Presupuestos de fit-out en proceso de licitación"
        ]
    },
    'hospitality': {
        'facts': [
            "Operador con presencia en múltiples destinos internacionales",
            "Standards de marca definidos para especificación de materiales",
            "Pipeline de aperturas anunciadas para los próximos 24 meses",
            "Departamento de design & construction centralizado",
            "Programa de renovación de activos existentes",
            "Partner preferente de arquitectos reconocidos",
            "Foco en experiencia de huésped y diferenciación por diseño"
        ],
        'signals': [
            "Nuevas aperturas en Asia-Pacífico en desarrollo",
            "Proceso de homologación de proveedores abierto",
            "Renovaciones de marca (rebranding) en cartera"
        ]
    },
    'contractor': {
        'facts': [
            "Constructora con experiencia en proyectos contract",
            "Capacidad de ejecución en múltiples mercados",
            "Track record en hospitality y edificios corporativos",
            "Equipo técnico con experiencia en sistemas de fachadas",
            "Certificaciones de calidad y gestión de proyectos",
            "Clientes recurrentes en el sector hotelero"
        ],
        'signals': [
            "Proyectos activos en fase de ejecución",
            "Buscando optimizar cadena de suministro",
            "Interés en reducir número de proveedores"
        ]
    }
}


def simulate_web_research(
    company_name: str,
    country: Optional[str] = None,
    website_domain: Optional[str] = None,
    company_type: str = 'architect'
) -> Tuple[List[ResearchSource], List[ResearchFact]]:
    """
    Skill 6: Simula investigación web.
    
    En producción, esto se conectaría a:
    - Google Custom Search API
    - LinkedIn Sales Navigator API
    - Bases de datos de construcción (BCI, Deloitte, etc.)
    
    Por ahora genera datos realistas basados en templates.
    """
    import random
    
    sources = []
    facts = []
    
    # Generar URLs plausibles
    domain = website_domain or f"{company_name.lower().replace(' ', '')}.com"
    
    source_templates = [
        {"url": f"https://{domain}/about", "title": f"{company_name} - About Us"},
        {"url": f"https://{domain}/projects", "title": f"{company_name} - Portfolio"},
        {"url": f"https://linkedin.com/company/{domain.split('.')[0]}", "title": f"{company_name} on LinkedIn"},
        {"url": f"https://archdaily.com/search/projects?q={company_name.replace(' ', '+')}", "title": f"ArchDaily - {company_name} Projects"},
        {"url": f"https://bciasia.com/search?q={company_name.replace(' ', '+')}", "title": f"BCI Asia - {company_name}"},
    ]
    
    # Seleccionar 5-7 fuentes
    selected_sources = random.sample(source_templates, min(len(source_templates), random.randint(5, 7)))
    
    for src in selected_sources:
        sources.append(ResearchSource(
            url=src['url'],
            title=src['title'],
            snippet=f"Información relevante sobre {company_name} encontrada en esta fuente."
        ))
    
    # Generar hechos basados en tipo
    template = RESEARCH_TEMPLATES.get(company_type, RESEARCH_TEMPLATES['architect'])
    
    # Seleccionar 5-8 hechos
    num_facts = random.randint(5, 8)
    selected_facts = random.sample(template['facts'], min(len(template['facts']), num_facts))
    
    for i, fact_text in enumerate(selected_facts):
        # Personalizar el hecho con el nombre de la empresa
        personalized_fact = f"{company_name}: {fact_text}"
        
        facts.append(ResearchFact(
            fact=personalized_fact,
            source_url=sources[i % len(sources)].url,
            confidence=random.choice(['high', 'high', 'medium']),
            category=random.choice(['project', 'team', 'market', 'signal'])
        ))
    
    # Añadir señales de timing
    if template.get('signals'):
        signal = random.choice(template['signals'])
        facts.append(ResearchFact(
            fact=f"{company_name}: {signal}",
            source_url=sources[0].url,
            confidence='medium',
            category='signal'
        ))
    
    return sources, facts


# ============================================
# SKILL 7: Porcelanosa Relevance Mapper
# ============================================

VALUE_PROPOSITIONS = {
    'hospitality': {
        'fit': "El ecosistema Porcelanosa cubre el 80% de las especificaciones de un proyecto hotelero premium: superficies, baños, equipamiento. Un único interlocutor para reducir la fragmentación logística típica de proyectos multi-marca.",
        'timing': "Los proyectos anunciados sugieren una ventana de prescripción en los próximos 6-12 meses. El momento ideal para introducir la marca en la fase de diseño.",
        'value': "Partner 'One-Stop-Shop' con capacidad de suministro internacional sincronizado y soporte técnico desde concepto hasta entrega.",
        'why': "1) Experiencia probada en hospitality premium (cadenas 4-5 estrellas). 2) Capacidad de replicación contract en múltiples mercados. 3) Reducción de interlocutores y riesgo en cadena de suministro."
    },
    'architect': {
        'fit': "Estudio con ADN premium donde Porcelanosa puede aportar coherencia estética garantizada entre superficies y equipamiento, liberando al equipo de diseño de la gestión de múltiples proveedores.",
        'timing': "Portfolio activo y proyectos en desarrollo indican momento óptimo para establecer relación a largo plazo como partner técnico de confianza.",
        'value': "Socio técnico que traduce visión de diseño en soluciones ejecutables, con soporte desde especificación hasta instalación.",
        'why': "1) Gama que permite libertad creativa sin comprometer viabilidad técnica. 2) Red global de showrooms para presentaciones a cliente final. 3) Innovation Lab para proyectos singulares."
    },
    'developer': {
        'fit': "Promotora con volumen donde Porcelanosa puede aportar eficiencias a escala: acuerdos marco, logística optimizada, y consistencia de calidad en proyectos múltiples.",
        'timing': "Pipeline de desarrollo activo sugiere necesidad de consolidar proveedores estratégicos para próximos lanzamientos.",
        'value': "Partner con capacidad de escalar suministro sin perder calidad, precios competitivos en volumen, y delivery coordinado.",
        'why': "1) Capacidad industrial propia (no dependencia de terceros). 2) Stock permanente en gamas clave. 3) Financiación de proyectos para desarrolladores cualificados."
    },
    'contractor': {
        'fit': "Constructora donde Porcelanosa puede simplificar la cadena de suministro de acabados premium, reduciendo proveedores e incidencias en obra.",
        'timing': "Proyectos activos en ejecución representan oportunidad inmediata de introducción en obras en curso.",
        'value': "Proveedor fiable con delivery programado, soporte técnico en obra, y gestión de reclamaciones ágil.",
        'why': "1) Logística just-in-time para obras con plazos ajustados. 2) Formación a instaladores. 3) Garantía extendida en proyectos contract."
    }
}


def generate_relevance_mapping(
    company_name: str,
    company_type: str,
    facts: List[ResearchFact],
    country: Optional[str] = None
) -> Dict[str, str]:
    """
    Skill 7: Genera el mapping de relevancia Porcelanosa.
    
    Output:
    - porcelanosa_fit: ¿Dónde encaja?
    - decision_maker_hypothesis: ¿Quién decide?
    - timing_signals: ¿Cuándo atacar?
    - value_proposition: Propuesta personalizada
    - why_porcelanosa: Diferencial
    """
    template = VALUE_PROPOSITIONS.get(company_type, VALUE_PROPOSITIONS['architect'])
    
    # Extraer hechos relevantes para personalizar
    project_facts = [f.fact for f in facts if f.category == 'project']
    signal_facts = [f.fact for f in facts if f.category == 'signal']
    
    # Generar hipótesis de decisor basada en tipo
    decision_maker_map = {
        'hospitality': f"VP Design & Construction o Director de Desarrollo. En {company_name}, el poder de prescripción suele estar centralizado en el equipo técnico de marca.",
        'architect': f"Principal Architect / Founding Partner. En estudios como {company_name}, la decisión de partners estratégicos recae en la dirección creativa.",
        'developer': f"Director de Desarrollo o CEO. En un perfil promotor como {company_name}, las decisiones de proveedores clave pasan por dirección.",
        'contractor': f"Director de Compras o Jefe de Obra. El stakeholder operativo en {company_name} gestiona la cadena de suministro."
    }
    
    return {
        'porcelanosa_fit': f"{company_name}: {template['fit']}",
        'decision_maker_hypothesis': decision_maker_map.get(company_type, decision_maker_map['architect']),
        'timing_signals': template['timing'] + (" " + signal_facts[0] if signal_facts else ""),
        'value_proposition': template['value'],
        'why_porcelanosa': template['why']
    }


# ============================================
# SKILL 8: Next Best Action + Drafts
# ============================================

def generate_outreach_drafts(
    company_name: str,
    contact_name: Optional[str],
    contact_title: Optional[str],
    facts: List[ResearchFact],
    relevance: Dict[str, str]
) -> List[OutreachDraft]:
    """
    Skill 8: Genera 3 artefactos de outreach.
    
    1. LinkedIn connect (≤300 chars)
    2. Email (breve, con hechos)
    3. Guion de llamada (30 segundos)
    """
    drafts = []
    
    # Seleccionar los mejores hechos para usar
    top_facts = [f.fact for f in facts if f.confidence == 'high'][:2]
    if not top_facts:
        top_facts = [f.fact for f in facts][:2]
    
    fact_snippet = top_facts[0].split(': ')[-1] if top_facts else "vuestra trayectoria en el sector"
    
    salutation = contact_name or "equipo"
    title_ref = f"como {contact_title}" if contact_title else ""
    
    # 1. LinkedIn Connect
    linkedin_text = f"Hola {salutation}, he visto que {company_name} {fact_snippet[:80]}... Me encantaría conectar para explorar sinergias en proyectos contract. ¿Conectamos?"
    
    drafts.append(OutreachDraft(
        channel='linkedin',
        content=linkedin_text[:300],
        key_facts_used=[fact_snippet[:50]],
        call_to_action="Conectar en LinkedIn"
    ))
    
    # 2. Email
    email_text = f"""Asunto: Colaboración {company_name} - Porcelanosa Grupo

Estimado/a {salutation},

He estado analizando la actividad reciente de {company_name} y me ha llamado la atención:
• {top_facts[0].split(': ')[-1] if top_facts else 'Vuestra presencia en el mercado hospitality'}
• {top_facts[1].split(': ')[-1] if len(top_facts) > 1 else 'El enfoque en proyectos premium'}

{relevance.get('value_proposition', 'En Porcelanosa Grupo trabajamos como socios de proyecto, no como proveedores.')}

¿Tendríais 15 minutos esta semana para una breve llamada de exploración?

Un saludo,
International Business Development
Porcelanosa Grupo
"""
    
    drafts.append(OutreachDraft(
        channel='email',
        content=email_text,
        key_facts_used=top_facts[:2],
        call_to_action="Agendar llamada de discovery"
    ))
    
    # 3. Guion de llamada
    call_script = f"""
[APERTURA - 10s]
"Buenos días, soy [Nombre] del equipo de International Business Development de Porcelanosa Grupo. 
Contacto porque he visto que {company_name} está trabajando en {fact_snippet[:50]}..."

[PROPUESTA - 15s]
"{relevance.get('value_proposition', 'Trabajamos con estudios y promotoras como partners de proyecto, simplificando la cadena de suministro de acabados premium.')}"

[CTA - 5s]
"¿Tendría sentido agendar 15 minutos para explorar si hay encaje? ¿Qué tal [fecha]?"

[MANEJO OBJECIONES]
- "No tenemos proyectos ahora" → "Perfecto, ¿cuándo prevén arrancar el próximo? Podemos preparar propuesta para entonces."
- "Ya tenemos proveedores" → "Entendido. ¿Trabajan con un único partner o gestionan varios? Ahí es donde podemos aportar valor."
"""
    
    drafts.append(OutreachDraft(
        channel='call',
        content=call_script,
        key_facts_used=top_facts[:1],
        call_to_action="Agendar reunión de discovery"
    ))
    
    return drafts


def conduct_full_research(
    company_name: str,
    company_type: str,
    country: Optional[str] = None,
    website_domain: Optional[str] = None,
    contact_name: Optional[str] = None,
    contact_title: Optional[str] = None
) -> Tuple[ResearchSnapshot, List[OutreachDraft]]:
    """
    Función principal: ejecuta investigación completa.
    
    Retorna:
    - ResearchSnapshot con todos los datos
    - Lista de OutreachDrafts
    """
    # 1. Investigación web
    sources, facts = simulate_web_research(
        company_name=company_name,
        country=country,
        website_domain=website_domain,
        company_type=company_type
    )
    
    # Determinar calidad
    if len(facts) >= 6 and len(sources) >= 5:
        quality_grade = 'rich'
    elif len(facts) >= 4:
        quality_grade = 'moderate'
    elif len(facts) >= 2:
        quality_grade = 'sparse'
    else:
        quality_grade = 'insufficient'
    
    # 2. Relevance Mapping
    relevance = generate_relevance_mapping(
        company_name=company_name,
        company_type=company_type,
        facts=facts,
        country=country
    )
    
    # 3. Generar snapshot
    snapshot = ResearchSnapshot(
        snapshot_id=str(uuid.uuid4()),
        entity_type='company',
        entity_id=str(uuid.uuid4()),  # En producción sería el company_id real
        entity_name=company_name,
        sources=sources,
        facts=facts,
        summary=f"Investigación completa de {company_name}. Detectados {len(facts)} hechos verificables de {len(sources)} fuentes. Tipología: {company_type}.",
        quality_grade=quality_grade,
        porcelanosa_fit=relevance['porcelanosa_fit'],
        decision_maker_hypothesis=relevance['decision_maker_hypothesis'],
        timing_signals=relevance['timing_signals'],
        value_proposition=relevance['value_proposition'],
        why_porcelanosa=relevance['why_porcelanosa']
    )
    
    # 4. Generar drafts
    drafts = generate_outreach_drafts(
        company_name=company_name,
        contact_name=contact_name,
        contact_title=contact_title,
        facts=facts,
        relevance=relevance
    )
    
    return snapshot, drafts
