from pathlib import Path

import streamlit as st

from alttabs.input_tab import InputTabError
from alttabs.pipeline import PipelineError, TransformRequest, transform_tab
from alttabs.position_shift import PositionBias
from alttabs.score import TabParseError, TabRenderError
from alttabs.tab import TabParseError as ParserTabParseError
from alttabs.transform import TransformError
from src.alttabs.instrument import presets
from src.alttabs.pitch import NoteName
from ui.fretboard_component import fretboard_selector

st.set_page_config(page_title="Alt Tabs", layout="wide")

ROOT = Path(__file__).resolve().parent
ASSETS_DIR = ROOT / "assets"

INSTRUMENTS = {
    "acoustic_guitar": {
        "label": "Acoustic Guitar",
        "image": str(ASSETS_DIR / "martin.png"),
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
        "label": "Electric Guitar",
        "image": str(ASSETS_DIR / "telecaster.png"),
        "string_count": 6,
        "visible_frets": 22,
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
        "label": "Bass",
        "image": str(ASSETS_DIR / "musicman.png"),
        "string_count": 4,
        "visible_frets": 20,
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
    "shift_positions": True,
    "bias": PositionBias.DOWN,
    "anchor_string": None,
    "anchor_fret": None,
    "max_fret_deviation": 6,
    "measures_per_line": 2,
    "rendered_tab": "",
    "last_error": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def humanize_error(message: str, instrument: str) -> str:
    lower = message.lower()

    if "expected 4 lines" in lower and instrument != "bass":
        return "This looks like a bass tab, but the selected instrument is a guitar."
    if "expected 6 lines" in lower and instrument == "bass":
        return "This looks like a guitar tab, but the selected instrument is bass."
    if "incomplete tab block" in lower and instrument == "bass":
        return "Bass tabs must contain 4 non-empty string lines per block."
    if "incomplete tab block" in lower and instrument != "bass":
        return "Guitar tabs must contain 6 non-empty string lines per block."
    if "invalid tab line without '|'" in lower or "missing '|' separator" in lower:
        return "Invalid tab format. Each string line must contain measure bars '|'."
    if "measure content must start" in lower or "measure content must end" in lower:
        return "Invalid tab format. Every measure line must begin and end with '|'."
    if "same number of measures" in lower or "identical widths" in lower:
        return "The tab is malformed. All strings must have aligned measures."
    if "label 'b' not valid" in lower and instrument == "bass":
        return "This looks like a guitar tab, but the selected instrument is bass."
    if "label 'e' not valid" in lower and instrument == "bass":
        return "This looks like a guitar tab, but the selected instrument is bass."
    if "parsed string numbers" in lower:
        return "The string labels do not match the selected instrument."
    if "no notes were found" in lower:
        return "No playable notes were found in the tab."
    if "monophonic" in lower:
        return "Only monophonic tabs are supported right now."
    if "no playable position" in lower:
        return "Some notes cannot be played on the selected instrument in the requested position."
    if "invalid position" in lower or "invalid played position" in lower:
        return "The tab contains a fret position that is not valid for the selected instrument."

    return message


def recompute():
    if not st.session_state.text.strip():
        st.session_state.rendered_tab = ""
        st.session_state.last_error = ""
        return

    has_anchor = (
        st.session_state.shift_positions
        and st.session_state.anchor_string is not None
        and st.session_state.anchor_fret is not None
    )

    try:
        result = transform_tab(
            TransformRequest(
                text=st.session_state.text,
                instrument=st.session_state.instrument,
                shift_positions=st.session_state.shift_positions,
                bias=st.session_state.bias,
                anchor_string=st.session_state.anchor_string if has_anchor else None,
                anchor_fret=st.session_state.anchor_fret if has_anchor else None,
                max_fret_deviation=st.session_state.max_fret_deviation,
                measures_per_line=st.session_state.measures_per_line,
            )
        )
        st.session_state.rendered_tab = result.rendered_tab
        st.session_state.last_error = ""
    except (
        InputTabError,
        TabParseError,
        ParserTabParseError,
        TabRenderError,
        PipelineError,
        TransformError,
    ) as e:
        st.session_state.rendered_tab = ""
        st.session_state.last_error = humanize_error(
            str(e), st.session_state.instrument
        )
    except Exception:
        st.session_state.rendered_tab = ""
        st.session_state.last_error = "Could not process this tab."


def set_instrument(name: str):
    st.session_state.instrument = name
    string_count = INSTRUMENTS[name]["string_count"]
    visible_frets = INSTRUMENTS[name]["visible_frets"]

    if (
        st.session_state.anchor_string is not None
        and st.session_state.anchor_string > string_count
    ):
        st.session_state.anchor_string = None

    if (
        st.session_state.anchor_fret is not None
        and st.session_state.anchor_fret > visible_frets
    ):
        st.session_state.anchor_fret = None

    recompute()


def render_instrument_selector():
    left_col, right_col = st.columns([1.3, 1])
    with left_col:
        st.markdown("<div style='height: 1.8rem;'></div>", unsafe_allow_html=True)
        st.markdown("## Welcome to Alt-Tabs")
        st.markdown(
            "Pick your instrument, paste your tabs, and select the position "
            "you want to play it on using the fretboard below."
            "\nRight now, only monophonics melodies are supported "
            "(one note at a time)."
        )
    with right_col:
        st.subheader("Instrument")
        cols = st.columns(len(INSTRUMENTS), gap="small")
        instrument_keys = list(INSTRUMENTS.keys())

        for col, key in zip(cols, instrument_keys):
            cfg = INSTRUMENTS[key]
            selected = st.session_state.instrument == key

            with col:
                _, img_center, _ = st.columns([0.1, 8, 0.1])
                with img_center:
                    st.image(cfg["image"], use_container_width=True)

                st.markdown(
                    "<div style='height: 0.35rem;'></div>", unsafe_allow_html=True
                )

                _, btn_center, _ = st.columns([0.1, 8, 0.1])
                with btn_center:
                    st.button(
                        f"{'●' if selected else '○'} {cfg['label']}",
                        key=f"instrument_{key}",
                        use_container_width=True,
                        on_click=set_instrument,
                        args=(key,),
                        type="primary" if selected else "secondary",
                    )


st.title("Alt Tabs")

render_instrument_selector()

st.text_area(
    "Input tab",
    key="text",
    height=320,
    on_change=recompute,
)

cfg = INSTRUMENTS[st.session_state.instrument]

if (
    st.session_state.instrument == "bass"
    and st.session_state.anchor_string is not None
    and st.session_state.anchor_string > 4
):
    st.session_state.anchor_string = None

st.subheader("Target position")

component_result = fretboard_selector(
    instrument=st.session_state.instrument,
    string_count=cfg["string_count"],
    visible_frets=cfg["visible_frets"],
    selected_string=st.session_state.anchor_string,
    selected_fret=st.session_state.anchor_fret,
    theme=cfg["theme"],
    key="main_fretboard",
)

clicked_new_position = False

if component_result is not None:
    selected = getattr(component_result, "selectedPosition", None)

    new_string = None
    new_fret = None

    if selected:
        new_string = selected.get("stringNumber")
        new_fret = selected.get("fret")
    else:
        new_string = getattr(component_result, "selectedString", None)
        new_fret = getattr(component_result, "selectedFret", None)

    if new_string is not None:
        new_string = int(new_string)
    if new_fret is not None:
        new_fret = int(new_fret)

    if (
        new_string is not None
        and new_fret is not None
        and (
            new_string != st.session_state.anchor_string
            or new_fret != st.session_state.anchor_fret
            or not st.session_state.shift_positions
        )
    ):
        st.session_state.anchor_string = new_string
        st.session_state.anchor_fret = new_fret
        st.session_state.shift_positions = True
        clicked_new_position = True

st.selectbox(
    "Bias",
    [PositionBias.DOWN, PositionBias.CENTERED, PositionBias.UP],
    key="bias",
    width=200,
    format_func=lambda x: x.value,
    on_change=recompute,
)

if clicked_new_position:
    recompute()

if st.session_state.anchor_string is None or st.session_state.anchor_fret is None:
    st.caption("Selected target: none")
else:
    selected_note = presets[st.session_state.instrument].note_at(
        st.session_state.anchor_string,
        st.session_state.anchor_fret,
    )
    st.caption(
        f"Selected target: string {st.session_state.anchor_string}, "
        f"fret {st.session_state.anchor_fret}, "
        f"note {NoteName.from_pitch(selected_note.pitch)}"
    )

if st.session_state.last_error:
    st.caption(st.session_state.last_error)
elif st.session_state.rendered_tab:
    st.subheader("Output")
    st.code(st.session_state.rendered_tab)
