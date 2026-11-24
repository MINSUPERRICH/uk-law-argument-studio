from __future__ import annotations

import json
from typing import Any
from google import genai
from google.genai.types import GenerateContentConfig, GoogleSearch, Tool

from schemas.a2ui_catalog import (
    A2UISurface,
    CounterArgumentDeck,
    FactCheckMatrix,
    SurRebuttalBuilder,
)


def _get_client(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)


def run_stage1_counter_arguments(
    api_key: str,
    model_id: str,
    essay_text: str,
    jurisdiction: str,
    round_num: int = 1,
) -> A2UISurface:
    """Stage 1: Generate multi-perspective UK/EU legal counter-arguments as A2UI JSON."""
    client = _get_client(api_key)
    system_instruction = f"""You are a senior UK and EU Law academic examiner (Oxford/KCL LLB/LLM standard).
Jurisdiction focus: {jurisdiction}.
Analyze the user's legal essay or argument and generate 3 to 4 sharp, distinct counter-arguments
across different legal perspectives (Constitutional/Parliamentary Sovereignty, EU/Assimilated Law,
Doctrinal/Common Law, Law Commission/Reform Critique, or Normative/Policy).

Rules:
- Cite real, well-established UK/EU statutes, cases, or Law Commission reports in OSCOLA format.
- Pinpoint exact doctrinal or normative gaps in the user's text.
- Output strictly valid JSON matching the A2UISurface schema with stage=1 and a CounterArgumentDeck component."""

    prompt = f"""Round {round_num} Analysis.
Surface ID: stage1_round_{round_num}
Target text to critique:
---
{essay_text}
---"""

    response = client.models.generate_content(
        model=model_id,
        contents=prompt,
        config=GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=A2UISurface,
        ),
    )
    return A2UISurface.model_validate_json(response.text)


def run_stage2_fact_check(
    api_key: str,
    model_id: str,
    essay_text: str,
    selected_cards: list[dict[str, Any]],
    jurisdiction: str,
    round_num: int = 1,
) -> tuple[A2UISurface, list[str]]:
    """Stage 2: Verify cited UK/EU statutes, cases, and Law Commission reports using Google Search grounding,
    then serialize into a strict FactCheckMatrix A2UI surface."""
    client = _get_client(api_key)

    # Step 2A: Grounded verification using Google Search tool
    cards_summary = json.dumps(selected_cards, ensure_ascii=False, indent=2)
    search_prompt = f"""You are a meticulous UK and EU legal fact-checker ({jurisdiction}).
Verify every statute, section number, case citation, and Law Commission report mentioned in the
original text and the selected counter-arguments below.

Use Google Search to check primary sources (legislation.gov.uk, caselaw.nationalarchives.gov.uk,
lawcom.gov.uk, eur-lex.europa.eu, bailii.org).
For each authority, determine whether it is VERIFIED, DISTORTED (misstated holding/scope),
UNVERIFIED, or OVERTURNED/REPEALED (e.g., post-Brexit Retained/Assimilated EU Law changes),
and provide the exact OSCOLA citation and source URL.

Original text:
{essay_text}

Selected counter-arguments:
{cards_summary}
"""

    grounded_resp = client.models.generate_content(
        model=model_id,
        contents=search_prompt,
        config=GenerateContentConfig(
            tools=[Tool(google_search=GoogleSearch())],
        ),
    )

    grounding_urls: list[str] = []
    if grounded_resp.candidates and grounded_resp.candidates[0].grounding_metadata:
        gm = grounded_resp.candidates[0].grounding_metadata
        if getattr(gm, "grounding_chunks", None):
            for chunk in gm.grounding_chunks:
                web = getattr(chunk, "web", None)
                if web and getattr(web, "uri", None):
                    grounding_urls.append(web.uri)

    # Step 2B: Serialize verified findings into strict A2UI 1.0 JSON
    serialize_prompt = f"""Convert the following verified legal fact-check report into a valid A2UISurface JSON object.
Use stage=2, surface_id="stage2_round_{round_num}", and a single FactCheckMatrix component.
Preserve all exact OSCOLA citations and verified source URLs from the report. Never invent URLs.

Verified Report:
{grounded_resp.text}
"""

    structured_resp = client.models.generate_content(
        model=model_id,
        contents=serialize_prompt,
        config=GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=A2UISurface,
        ),
    )
    surface = A2UISurface.model_validate_json(structured_resp.text)
    return surface, list(dict.fromkeys(grounding_urls))


def run_stage3_sur_rebuttal(
    api_key: str,
    model_id: str,
    essay_text: str,
    selected_cards: list[dict[str, Any]],
    fact_check_summary: dict[str, Any],
    chosen_strategy: str,
    jurisdiction: str,
    round_num: int = 1,
) -> A2UISurface:
    """Stage 3: Generate a First-Class UK/EU sur-rebuttal and strategy selector as A2UI JSON."""
    client = _get_client(api_key)
    system_instruction = f"""You are a First-Class UK & EU Law writing coach ({jurisdiction}).
Your task is to help the author construct a persuasive sur-rebuttal that:
1. Respects the verified legal authorities from Stage 2 (never relying on distorted or overturned authorities).
2. Directly answers the selected Stage 1 counter-arguments using the chosen strategy: {chosen_strategy}.
3. Uses crisp, human, authoritative UK academic prose (avoiding AI boilerplate like 'moreover', 'furthermore', 'in conclusion').
4. Integrates OSCOLA citations cleanly and ends with a sharp normative takeaway.

Output strictly valid JSON matching A2UISurface with stage=3, surface_id="stage3_round_{round_num}",
and a single SurRebuttalBuilder component."""

    prompt = f"""Original Essay / Argument:
{essay_text}

Selected Counter-Arguments:
{json.dumps(selected_cards, ensure_ascii=False)}

Verified Fact-Check Results:
{json.dumps(fact_check_summary, ensure_ascii=False)}

Chosen Strategy: {chosen_strategy}
"""

    response = client.models.generate_content(
        model=model_id,
        contents=prompt,
        config=GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=A2UISurface,
        ),
    )
    return A2UISurface.model_validate_json(response.text)
