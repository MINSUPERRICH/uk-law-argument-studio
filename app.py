from __future__ import annotations

import os
import streamlit as st
from dotenv import load_dotenv

from agents.legal_agents import (
    run_stage1_counter_arguments,
    run_stage2_fact_check,
    run_stage3_sur_rebuttal,
)
from renderer.a2ui_streamlit import render_a2ui_surface

load_dotenv()

st.set_page_config(
    page_title="UK & EU Law A2UI Argumentation Studio",
    page_icon="⚖️",
    layout="wide",
)

SAMPLE_ESSAY = """Silver was right that the threat was the channel rather than the format, and right that the industry could not hold it.
Digital distribution dissolved manufacturing and retail margins, shifting value toward intellectual property control.
After the March 2001 injunction requiring Napster to filter its directories, major labels licensed Apple in 2003 on restricted terms.
Yet this survival raises a normative question: when copyright exclusivity shifts gatekeeping power to concentrated catalogues and dominant platforms,
whether copyright serves creator remuneration and public access remains unresolved."""


def resolve_api_key() -> str:
    if "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"]
    if os.getenv("GEMINI_API_KEY"):
        return os.getenv("GEMINI_API_KEY", "")
    return st.session_state.get("manual_api_key", "")


with st.sidebar:
    st.header("Configuration")
    model_id = st.selectbox(
        "Gemini Model",
        options=["gemini-4-carbon", "gemini-4-argon", "gemini-4-hydrogen"],
        index=0,
        help="gemini-4-carbon is recommended for deep legal reasoning and fact-checking.",
    )
    jurisdiction = st.selectbox(
        "Legal System Focus",
        options=[
            "UK Law (England & Wales) + EU / Assimilated Law",
            "UK Law (England & Wales) Only",
            "EU Law (CJEU / Directives / Regulations) Only",
        ],
        index=0,
    )
    if not resolve_api_key():
        st.text_input(
            "GEMINI_API_KEY",
            type="password",
            key="manual_api_key",
            help="Set in .streamlit/secrets.toml for production.",
        )

    if st.button("Reset Session", use_container_width=True):
        for k in list(st.session_state.keys()):
            if k != "manual_api_key":
                del st.session_state[k]
        st.rerun()

st.title("UK & EU Law A2UI Argumentation Studio")
st.caption("Powered by Gemini 4 Carbon, Google Search Grounding, and A2UI 1.0 Declarative UI")

if "round_num" not in st.session_state:
    st.session_state.round_num = 1
if "essay_text" not in st.session_state:
    st.session_state.essay_text = ""

col_in, col_sample = st.columns([5, 1])
with col_sample:
    st.write("")
    st.write("")
    if st.button("Load UK IP Sample", use_container_width=True):
        st.session_state.essay_text = SAMPLE_ESSAY
        st.rerun()

with col_in:
    essay_text = st.text_area(
        "Paste your UK/EU Law Essay Draft or Legal Argument",
        key="essay_text",
        height=180,
        placeholder="Paste a paragraph or full essay draft here...",
    )

api_key = resolve_api_key()

# Stage 1 Trigger
if st.button("Stage 1: Generate Multi-Angle Counter-Arguments", type="primary", disabled=not (api_key and essay_text.strip())):
    with st.status("Running Stage 1 Agent (Generating UK/EU Counter-Arguments)...", expanded=True):
        surface1 = run_stage1_counter_arguments(
            api_key=api_key,
            model_id=model_id,
            essay_text=essay_text,
            jurisdiction=jurisdiction,
            round_num=st.session_state.round_num,
        )
        st.session_state.surface1 = surface1
        st.session_state.pop("surface2", None)
        st.session_state.pop("surface3", None)

# Render Stage 1 & Stage 2 Trigger
if "surface1" in st.session_state:
    st.divider()
    s1_state = render_a2ui_surface(st.session_state.surface1, st.session_state.round_num)
    selected_cards = s1_state.get("selected_cards", [])

    if st.button("Stage 2: Fact-Check Selected Arguments (Google Search)", disabled=not selected_cards):
        with st.status("Running Stage 2 Agent (Verifying UK/EU Statutes & Cases)...", expanded=True):
            surface2, urls = run_stage2_fact_check(
                api_key=api_key,
                model_id=model_id,
                essay_text=essay_text,
                selected_cards=selected_cards,
                jurisdiction=jurisdiction,
                round_num=st.session_state.round_num,
            )
            st.session_state.surface2 = surface2
            st.session_state.grounding_urls = urls
            st.session_state.selected_cards = selected_cards
            st.session_state.pop("surface3", None)

# Render Stage 2 & Stage 3 Trigger
if "surface2" in st.session_state:
    st.divider()
    render_a2ui_surface(st.session_state.surface2, st.session_state.round_num)

    if st.session_state.get("grounding_urls"):
        with st.expander("Live Search Grounding Sources"):
            for u in st.session_state.grounding_urls:
                st.markdown(f"- {u}")

    strategy_choice = st.selectbox(
        "Preferred Sur-Rebuttal Angle",
        options=[
            "Distinguish Precedent & Narrow Scope",
            "Purposive Statutory / EU Retained Law Interpretation",
            "Law Commission 3-Axis Critique & Normative Synthesis",
        ],
    )

    if st.button("Stage 3: Draft Sur-Rebuttal (OSCOLA + Normative Synthesis)"):
        with st.status("Running Stage 3 Agent (Drafting Sur-Rebuttal)...", expanded=True):
            surface3 = run_stage3_sur_rebuttal(
                api_key=api_key,
                model_id=model_id,
                essay_text=essay_text,
                selected_cards=st.session_state.get("selected_cards", []),
                fact_check_summary=st.session_state.surface2.model_dump(),
                chosen_strategy=strategy_choice,
                jurisdiction=jurisdiction,
                round_num=st.session_state.round_num,
            )
            st.session_state.surface3 = surface3

# Render Stage 3 & Export / Next Round
if "surface3" in st.session_state:
    st.divider()
    s3_state = render_a2ui_surface(st.session_state.surface3, st.session_state.round_num)
    edited_draft = s3_state.get("rebuttal_state", {}).get("edited_draft", "")

    col_dl, col_next = st.columns(2)
    with col_dl:
        st.download_button(
            "Download Sur-Rebuttal (.md)",
            data=edited_draft,
            file_name=f"sur_rebuttal_round_{st.session_state.round_num}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col_next:
        if st.button("Advance to Next Round (Use Sur-Rebuttal as Input)", use_container_width=True):
            st.session_state.essay_text = edited_draft
            st.session_state.round_num += 1
            for k in ["surface1", "surface2", "surface3", "grounding_urls"]:
                st.session_state.pop(k, None)
            st.rerun()
