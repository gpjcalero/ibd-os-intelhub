from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class ThermometerResult(BaseModel):
    country: str
    objective: str
    country_assessment: str
    recommended_segments: List[str]
    scoring_profile: Dict = Field(default_factory=dict)
    global_db_instructions: Dict = Field(default_factory=dict)
    risks: List[str]
    opportunities: List[str]
    confidence: str = "medium"

class StrategyReport(BaseModel):
    summary: str
    key_facts: List[str]
    recommended_approach: str
    email_draft: str
    linkedin_draft: str
    risks: List[str]
    confidence: str = "medium"

class EnrichmentResult(BaseModel):
    description: str
    status: str = "success"
    key_highlights: List[str] = []
