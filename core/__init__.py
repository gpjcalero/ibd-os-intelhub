"""
PORCELANOSA OS - Core Package (v7.0)
Exports clean interfaces for Agent 0, 1, 2, and 3.
"""

from .normalizer import (
    normalize_company_name
)

from .scoring import (
    score_dataframe
)

from .matching import (
    process_tenders,
    B2BMatcher
)

from .ai_research import (
    research_with_openrouter,
    research_with_ollama,
    clean_think_tags
)

from .market_thermometer import (
    analyze_market
)

from .schemas import (
    ThermometerResult,
    StrategyReport,
    EnrichmentResult
)

__all__ = [
    'normalize_company_name',
    'score_dataframe',
    'process_tenders',
    'B2BMatcher',
    'research_with_openrouter',
    'research_with_ollama',
    'analyze_market',
    'ThermometerResult',
    'StrategyReport',
    'EnrichmentResult'
]
