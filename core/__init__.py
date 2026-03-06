"""
PORCELANOSA OS - Core Package (v4.0 AGENTIC)
Exports clean interfaces for Agent 1 (Prospector), Agent 2 (Matcher), and Agent 3 (Evaluator).
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
    AIResearchResult
)

__all__ = [
    # Normalizer (Agent 2 Support)
    'normalize_company_name',
    
    # Scoring (Agent 1)
    'score_dataframe',
    
    # Matching (Agent 2)
    'process_tenders',
    'B2BMatcher',
    
    # AI Research (Agent 3)
    'research_with_openrouter',
    'AIResearchResult'
]
