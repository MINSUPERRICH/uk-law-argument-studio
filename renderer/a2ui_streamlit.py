from __future__ import annotations

from typing import Any
import streamlit as st

from schemas.a2ui_catalog import (
    A2UISurface,
    CounterArgumentDeck,
    FactCheckMatrix,
    SurRebuttalBuilder,
)


STATUS_STYLES = {
    "VERIFIED": ("Verified", "success"),
    "DISTORTED": ("Distorted / Misstated", "warning"),
    "UNVERIFIED": ("Unverified", "warning"),
    "OVERTURNED": ("Overturned / Repealed", "error"),
}


def render_a2ui_surface(surface: A2UISurface, round_num: int) -> dict[str, Any]:
    """Render an A2UI 1.0 declarative surface into native Streamlit widgets.
    Returns user interaction state (selected cards, chosen strategy, edited rebuttal)."""
    state_out: dict[str, Any] = {}

    st.subheader(f"Stage {surface.stage}: {surface.title}")
    st.caption(surface.summary)

    for comp in surface.components:
        if isinstance(comp, CounterArgumentDeck):
            state_out["selected_cards"] = _render_counter_argument_deck(comp, round_num)
        elif isinstance(comp, FactCheckMatrix):
            _render_fact_check_matrix(comp)
        elif isinstance(comp, SurRebuttalBuilder):
            state_out["rebuttal_state"] = _render_sur_rebuttal_builder(comp, round_num)

    with st.expander("Inspect Raw A2UI 1.0 JSON Payload"):
        st.json(surface.model_dump())

    return state_out


def _render_counter_argument_deck(deck: CounterArgumentDeck, round_num: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    if not deck.cards:
        st.info("No counter-arguments returned.")
        return selected

    tabs = st.tabs([f"{i+1}. {c.perspective}" for i, c in enumerate(deck.cards)])
    for tab, card in zip(tabs, deck.cards):
        with tab:
            st.markdown(f"**{card.title}**")
            st.write(card.argument)
            st.info(f"**Target Weakness:** {card.target_weakness}")
            if card.suggested_authorities:
                st.markdown("**Suggested UK/EU Authorities (OSCOLA):**")
                for auth in card.suggested_authorities:
                    st.markdown(f"- {auth}")

    st.markdown("#### Select counter-arguments to fact-check in Stage 2")
    cols = st.columns(len(deck.cards)) if len(deck.cards) <= 4 else [st.container() for _ in deck.cards]
    for col, card in zip(cols, deck.cards):
        with col:
            checked = st.checkbox(
                f"{card.title}",
                value=True,
                key=f"chk_r{round_num}_{card.card_id}",
            )
            if checked:
                selected.append(card.model_dump())
    return selected


def _render_fact_check_matrix(matrix: FactCheckMatrix) -> None:
    st.markdown(f"**Overall Reliability Assessment:** {matrix.overall_reliability_note}")
    for item in matrix.items:
        label, kind = STATUS_STYLES.get(item.status, (item.status, "info"))
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"**{item.authority_cited}**")
                st.caption(f"OSCOLA: `{item.oscola_citation}`")
            with c2:
                if kind == "success":
                    st.success(label)
                elif kind == "warning":
                    st.warning(label)
                else:
                    st.error(label)

            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**Claim in Draft / Counter-Argument**")
                st.write(item.original_claim)
            with col_b:
                st.markdown("**Verified Legal Position**")
                st.write(item.legal_reality)

            if item.source_url:
                st.markdown(f"[Primary / Verified Source]({item.source_url})")


def _render_sur_rebuttal_builder(builder: SurRebuttalBuilder, round_num: int) -> dict[str, Any]:
    strategy_labels = {s.strategy_id: f"{s.label} - {s.description}" for s in builder.strategy_options}
    option_ids = list(strategy_labels.keys())
    default_idx = option_ids.index(builder.recommended_strategy_id) if builder.recommended_strategy_id in option_ids else 0

    chosen_strategy = st.radio(
        "Select Sur-Rebuttal Strategy",
        options=option_ids,
        index=default_idx,
        format_func=lambda sid: strategy_labels.get(sid, sid),
        key=f"strategy_r{round_num}",
    )

    edited_draft = st.text_area(
        "Sur-Rebuttal Draft (Editable)",
        value=builder.draft_rebuttal,
        height=240,
        key=f"rebuttal_editor_r{round_num}",
    )
    st.success(f"**Normative Takeaway:** {builder.normative_takeaway}")

    if builder.oscola_authorities:
        with st.expander("OSCOLA Authorities Used"):
            for auth in builder.oscola_authorities:
                st.markdown(f"- {auth}")

    return {
        "chosen_strategy": chosen_strategy,
        "edited_draft": edited_draft,
    }
