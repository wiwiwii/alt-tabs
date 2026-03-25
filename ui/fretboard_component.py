from pathlib import Path

import streamlit as st

DIST_DIR = Path(__file__).resolve().parent.parent / "dist"
JS = (DIST_DIR / "index.js").read_text(encoding="utf-8")

fretboard_component = st.components.v2.component(
    "alt_tabs_fretboard",
    js=JS,
)


def fretboard_selector(
    *,
    instrument: str,
    string_count: int,
    visible_frets: int,
    selected_string: int | None,
    selected_fret: int | None,
    theme: dict,
    key: str,
):
    return fretboard_component(
        key=key,
        default={
            "selectedString": selected_string,
            "selectedFret": selected_fret,
        },
        data={
            "instrument": instrument,
            "stringCount": string_count,
            "visibleFrets": visible_frets,
            "selectedString": selected_string,
            "selectedFret": selected_fret,
            "theme": theme,
        },
        on_selectedString_change=lambda: None,
        on_selectedFret_change=lambda: None,
    )

