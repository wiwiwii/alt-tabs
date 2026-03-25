import streamlit as st

from alttabs.pipeline import TransformRequest, transform_tab
from alttabs.position_shift import PositionBias
from ui.fretboard_component import fretboard_selector

st.set_page_config(page_title="Alt Tabs", layout="wide")

INSTRUMENTS = {
    "acoustic_guitar": {
        "string_count": 6,
        "visible_frets": 14,
        "theme": {
            "boardBase": "#1f1a17",
            "boardEdge": "#2b2521",
            "fretColor": "#b9bcc2",
            "nutColor": "#ddd3c3",
            "inlayColor": "#e7dfd2",
            "labelColor": "#d8d0c2",
            "stringColor": "#c5c9cf",
            "markerColor": "#d8b36a",
            "markerStroke": "#fff7e8",
            "hoverFill": "rgba(255,244,214,0.14)",
            "bgTop": "#171311",
            "bgBottom": "#0f0c0b",
        },
    },
    "electric_guitar": {
        "string_count": 6,
        "visible_frets": 14,
        "theme": {
            "boardBase": "#b98b56",
            "boardEdge": "#9a6f42",
            "fretColor": "#a9adb3",
            "nutColor": "#eee3d1",
            "inlayColor": "#111111",
            "labelColor": "#2a2119",
            "stringColor": "#b7bcc3",
            "markerColor": "#2a2a2a",
            "markerStroke": "#f5efe6",
            "hoverFill": "rgba(0,0,0,0.08)",
            "bgTop": "#191614",
            "bgBottom": "#110f0e",
        },
    },
    "bass": {
        "string_count": 4,
        "visible_frets": 14,
        "theme": {
            "boardBase": "#b98b56",
            "boardEdge": "#9a6f42",
            "fretColor": "#a9adb3",
            "nutColor": "#eee3d1",
            "inlayColor": "#111111",
            "labelColor": "#2a2119",
            "stringColor": "#cfd3d8",
            "markerColor": "#2a2a2a",
            "markerStroke": "#f5efe6",
            "hoverFill": "rgba(0,0,0,0.08)",
            "bgTop": "#191614",
            "bgBottom": "#110f0e",
        },
    },
}

defaults = {
    "text": "",
    "instrument": "acoustic_guitar",
    "transpose_semitones": 0,
    "shift_positions": False,
    "bias": PositionBias.CENTERED,
    "anchor_string": 6,
    "anchor_fret": 3,
    "max_fret_deviation": 6,
    "measures_per_line": 4,
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.title("Alt Tabs")

st.text_area("Input tab", key="text", height=300)

instrument = st.selectbox(
    "Instrument",
    ["acoustic_guitar", "electric_guitar", "bass"],
    key="instrument",
)

cfg = INSTRUMENTS[instrument]

if instrument == "bass" and st.session_state.anchor_string > 4:
    st.session_state.anchor_string = 4

component_result = fretboard_selector(
    instrument=instrument,
    string_count=cfg["string_count"],
    visible_frets=cfg["visible_frets"],
    selected_string=st.session_state.anchor_string,
    selected_fret=st.session_state.anchor_fret,
    theme=cfg["theme"],
    key="main_fretboard",
)

if component_result is not None:
    if getattr(component_result, "selectedString", None) is not None:
        st.session_state.anchor_string = int(component_result.selectedString)
    if getattr(component_result, "selectedFret", None) is not None:
        st.session_state.anchor_fret = int(component_result.selectedFret)
        st.session_state.shift_positions = True

col1, col2, col3 = st.columns(3)
with col1:
    st.number_input(
        "Transpose (semitones)",
        min_value=-24,
        max_value=24,
        step=1,
        key="transpose_semitones",
    )
with col2:
    st.checkbox("Shift positions", key="shift_positions")
with col3:
    st.selectbox(
        "Bias",
        [PositionBias.DOWN, PositionBias.CENTERED, PositionBias.UP],
        key="bias",
        format_func=lambda x: x.value,
    )

st.caption(
    f"Selected target: string {st.session_state.anchor_string}, fret {st.session_state.anchor_fret}"
)

if st.button("Transform", type="primary", use_container_width=True):
    try:
        result = transform_tab(
            TransformRequest(
                text=st.session_state.text,
                instrument=st.session_state.instrument,
                transpose_semitones=st.session_state.transpose_semitones,
                shift_positions=st.session_state.shift_positions,
                bias=st.session_state.bias,
                anchor_string=(
                    st.session_state.anchor_string
                    if st.session_state.shift_positions
                    else None
                ),
                anchor_fret=(
                    st.session_state.anchor_fret
                    if st.session_state.shift_positions
                    else None
                ),
                max_fret_deviation=st.session_state.max_fret_deviation,
                measures_per_line=st.session_state.measures_per_line,
            )
        )
        st.subheader("Output")
        st.code(result.rendered_tab)
    except Exception as e:
        st.error(str(e))

