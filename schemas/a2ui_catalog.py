from __future__ import annotations

from typing import Literal, Union
from pydantic import BaseModel, Field


class CounterArgumentCard(BaseModel):
    card_id: str = Field(..., description="Unique ID for checkbox selection, e.g. ca_1")
    perspective: Literal[
        "Constitutional / Parliamentary Sovereignty",
        "EU / Assimilated Law",
        "Doctrinal / Common Law",
        "Law Commission / Reform Critique",
        "Normative / Policy",
    ]
    title: str = Field(..., description="Concise headline of the counter-argument")
    argument: str = Field(..., description="Substantive legal counter-argument")
    target_weakness: str = Field(..., description="Specific gap or vulnerability in the user's draft")
    suggested_authorities: list[str] = Field(
        default_factory=list,
        description="Relevant UK/EU statutes, cases, or Law Commission reports in OSCOLA format",
    )


class CounterArgumentDeck(BaseModel):
    component_type: Literal["CounterArgumentDeck"] = "CounterArgumentDeck"
    cards: list[CounterArgumentCard]


class FactCheckItem(BaseModel):
    authority_cited: str = Field(..., description="Statute, case, or report referenced in the argument")
    status: Literal["VERIFIED", "DISTORTED", "UNVERIFIED", "OVERTURNED"]
    original_claim: str = Field(..., description="What the draft or counter-argument claimed")
    legal_reality: str = Field(..., description="Verified legal position from primary UK/EU sources")
    oscola_citation: str = Field(..., description="Clean OSCOLA-formatted citation")
    source_url: str = Field(default="", description="Direct URL to legislation.gov.uk, National Archives, Law Commission, or EUR-Lex")


class FactCheckMatrix(BaseModel):
    component_type: Literal["FactCheckMatrix"] = "FactCheckMatrix"
    overall_reliability_note: str
    items: list[FactCheckItem]


class StrategyOption(BaseModel):
    strategy_id: str
    label: str
    description: str


class SurRebuttalBuilder(BaseModel):
    component_type: Literal["SurRebuttalBuilder"] = "SurRebuttalBuilder"
    recommended_strategy_id: str
    strategy_options: list[StrategyOption]
    draft_rebuttal: str = Field(..., description="First-Class UK/EU law sur-rebuttal prose with OSCOLA footnotes/citations")
    normative_takeaway: str = Field(..., description="Final normative synthesis balancing doctrine and policy")
    oscola_authorities: list[str] = Field(default_factory=list)


A2UIComponent = Union[CounterArgumentDeck, FactCheckMatrix, SurRebuttalBuilder]


class A2UISurface(BaseModel):
    """A2UI 1.0-aligned declarative surface payload."""
    protocol_version: Literal["1.0"] = "1.0"
    surface_id: str
    stage: Literal[1, 2, 3]
    title: str
    summary: str
    components: list[A2UIComponent]
