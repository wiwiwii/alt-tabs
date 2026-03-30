from pathlib import Path
import logging

import streamlit as st

from alttabs.fretboard_component import fretboard_selector
from alttabs.input_tab import InputTabError
from alttabs.pipeline import (
    PipelineError,
    PolyphonyPolicy,
    TransformRequest,
    transform_tab,
)
from alttabs.position_shift import PositionBias
from alttabs.instrument import presets
from alttabs.midi_to_tab import MidiTabError, render_midi_file_to_tab
from alttabs.pitch import NoteName
from alttabs.score_ingest import ScoreIngestError, ingest_partition_to_midi
from alttabs.score import TabRenderError
from alttabs.tab import TabParseError

LOGGER = logging.getLogger(__name__)

st.set_page_config(page_title="Alt Tabs", layout="wide")

ROOT = Path(__file__).resolve().parent
ASSETS_DIR = ROOT / "assets"

st.markdown(
    """
    <style>
    div[data-testid="stTextArea"] textarea {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas,
            "Liberation Mono", "Courier New", monospace !important;
        font-size: 0.95rem !important;
        line-height: 1.45 !important;
        white-space: pre !important;
        tab-size: 4;
    }

    div[data-testid="stCodeBlock"] pre,
    div[data-testid="stCodeBlock"] code {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas,
            "Liberation Mono", "Courier New", monospace !important;
    }

    .alt-tabs-problem {
        margin-top: 0.35rem;
        margin-bottom: 0.8rem;
        padding: 0.55rem 0.75rem;
        border-radius: 0.5rem;
        border: 1px solid rgba(255, 75, 75, 0.28);
        background: rgba(255, 75, 75, 0.08);
        color: rgb(255, 214, 214);
        font-size: 0.92rem;
        line-height: 1.35;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

INSTRUMENTS = {
    "acoustic_guitar": {
        "label": "Acoustic Guitar",
        "image": str(ASSETS_DIR / "martin.png"),
        "string_count": 6,
        "visible_frets": 15,
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


def humanize_error(message: str, instrument: str) -> str:
    lower = message.lower().strip()

    if "expected 4 non-empty lines" in lower and instrument == "bass":
        return "This looks like a guitar tab, but the selected instrument is bass. Bass tabs must use 4 strings per block."
    if "expected 6 non-empty lines" in lower and instrument != "bass":
        return "This looks like a bass tab, but the selected instrument is a guitar. Guitar tabs must use 6 strings per block."

    if "expected 4 lines for this instrument" in lower and instrument != "bass":
        return "This looks like a bass tab, but the selected instrument is a guitar."
    if "expected 6 lines for this instrument" in lower and instrument == "bass":
        return "This looks like a guitar tab, but the selected instrument is bass."

    if "invalid tab line without '|'" in lower or "missing '|' separator" in lower:
        return "Invalid tab format. Each string line must contain bar separators like |--0--|."
    if (
        "measure content must start with '|'" in lower
        or "measure content must end with '|'" in lower
    ):
        return "Invalid measure formatting. Every measure line must start and end with '|'."
    if "all strings must have the same number of measures" in lower:
        return "Invalid tab format. All strings must have the same number of measures."
    if "corresponding measures must have identical widths" in lower:
        return "Invalid tab format. Measures must stay aligned across all strings."
    if (
        "unsupported or ambiguous string label" in lower
        or "not valid for this instrument" in lower
    ):
        return "The string labels do not match the selected instrument."
    if "no notes were found" in lower or "empty tab" in lower:
        return "No playable notes were found in the tab."
    if "cannot shift positions on an empty event stream" in lower:
        return "No playable notes were found, so the target position cannot be applied."
    if "no playable position" in lower or "no playable positions found" in lower:
        return "Requested transposition/position is unplayable on this instrument. Try another target fret, lower transposition, or a different instrument."
    if "invalid anchor position" in lower:
        return "Selected target position is invalid for this instrument. Pick another string/fret."
    if "polyphonic input" in lower:
        return "Polyphonic input was reduced to one note at a time. Change polyphony policy if needed."
    if "only monophonic" in lower or "multiple notes on same string" in lower:
        return "Only simple monophonic tabs are supported right now."

    return message


defaults = {
    "text": "",
    "instrument": "acoustic_guitar",
    "shift_positions": True,
    "bias": PositionBias.DOWN,
    "anchor_string": None,
    "anchor_fret": None,
    "max_fret_deviation": 6,
    "polyphony_policy": PolyphonyPolicy.TOP_NOTE,
    "measures_per_line": 2,
    "rendered_tab": "",
    "last_error": "",
    "score_midi_path": None,
    "score_has_treble": False,
    "score_has_bass": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


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
                polyphony_policy=st.session_state.polyphony_policy,
                measures_per_line=st.session_state.measures_per_line,
            )
        )
        st.session_state.rendered_tab = result.rendered_tab
        st.session_state.last_error = ""
    except (InputTabError, PipelineError, TabParseError, TabRenderError) as exc:
        st.session_state.rendered_tab = ""
        st.session_state.last_error = humanize_error(
            str(exc), st.session_state.instrument
        )
    except Exception:
        LOGGER.exception("Unexpected error while processing tab")
        st.session_state.rendered_tab = ""
        st.session_state.last_error = (
            "Unexpected processing error. Please retry or adjust the input tab."
        )


def process_uploaded_score(uploaded_file):
    import tempfile

    suffix = Path(uploaded_file.name).suffix or ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name

    result = ingest_partition_to_midi(tmp_path)
    st.session_state.score_midi_path = str(result.midi_path)
    st.session_state.score_has_treble = result.has_treble_clef
    st.session_state.score_has_bass = result.has_bass_clef


def render_from_uploaded_score():
    midi_path = st.session_state.score_midi_path
    if not midi_path:
        return

    forced_instrument = st.session_state.instrument
    if st.session_state.score_has_treble and st.session_state.score_has_bass:
        forced_instrument = st.session_state.get("score_target_instrument", "acoustic_guitar")

    fretboard = presets[forced_instrument]
    rendered = render_midi_file_to_tab(
        midi_path=midi_path,
        fretboard=fretboard,
        measures_per_line=st.session_state.measures_per_line,
    )
    st.session_state.rendered_tab = rendered
    st.session_state.last_error = ""


def set_instrument(name: str):
    st.session_state.instrument = name
    string_count = INSTRUMENTS[name]["string_count"]
    visible_frets = INSTRUMENTS[name]["visible_frets"]

    if (
        st.session_state.anchor_string is not None
        and st.session_state.anchor_string > string_count
    ):
        st.session_state.anchor_string = string_count

    if (
        st.session_state.anchor_fret is not None
        and st.session_state.anchor_fret > visible_frets
    ):
        st.session_state.anchor_fret = visible_frets

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

with st.form("tab_input_form", clear_on_submit=False):
    st.text_area(
        "Input tab",
        key="text",
        height=320,
    )
    submitted = st.form_submit_button("Apply tab")

if submitted:
    recompute()

st.subheader("Or upload image/PDF (tab or score)")
uploaded = st.file_uploader(
    "Upload PDF/image",
    type=["pdf", "png", "jpg", "jpeg", "tiff", "bmp"],
)
process_ocr = st.button("Process with Audiveris OCR")
if process_ocr and uploaded is not None:
    try:
        process_uploaded_score(uploaded)
        if st.session_state.score_has_treble and st.session_state.score_has_bass:
            st.info("Both treble and bass clefs detected. Choose output instrument below.")
    except ScoreIngestError as exc:
        st.session_state.last_error = str(exc)
        st.session_state.rendered_tab = ""
    except Exception:
        LOGGER.exception("Unexpected OCR processing error")
        st.session_state.last_error = "Could not process uploaded score with Audiveris."
        st.session_state.rendered_tab = ""

if st.session_state.score_has_treble and st.session_state.score_has_bass:
    st.radio(
        "Detected both clefs. Generate tabs for:",
        options=["acoustic_guitar", "bass"],
        key="score_target_instrument",
        format_func=lambda x: "Guitar" if x != "bass" else "Bass",
    )

if st.session_state.score_midi_path:
    if st.button("Generate tabs from OCR MIDI"):
        try:
            render_from_uploaded_score()
        except (MidiTabError, TabRenderError, PipelineError) as exc:
            st.session_state.last_error = humanize_error(str(exc), st.session_state.instrument)
            st.session_state.rendered_tab = ""
        except Exception:
            LOGGER.exception("Unexpected MIDI-to-tab conversion error")
            st.session_state.last_error = "Could not convert OCR MIDI to tabs."
            st.session_state.rendered_tab = ""

cfg = INSTRUMENTS[st.session_state.instrument]

if (
    st.session_state.instrument == "bass"
    and st.session_state.anchor_string is not None
    and st.session_state.anchor_string > 4
):
    st.session_state.anchor_string = 4

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

selected_position = None
if component_result is not None:
    if isinstance(component_result, dict):
        selected_position = component_result.get("selectedPosition")
    else:
        selected_position = getattr(component_result, "selectedPosition", None)

selection_changed = False
if selected_position:
    new_string = int(selected_position["stringNumber"])
    new_fret = int(selected_position["fret"])

    if (
        new_string != st.session_state.anchor_string
        or new_fret != st.session_state.anchor_fret
    ):
        st.session_state.anchor_string = new_string
        st.session_state.anchor_fret = new_fret
        st.session_state.shift_positions = True
        selection_changed = True

if selection_changed:
    recompute()
    st.rerun()
st.selectbox(
    "Bias",
    [PositionBias.DOWN, PositionBias.CENTERED, PositionBias.UP],
    key="bias",
    width=200,
    format_func=lambda x: x.value,
    on_change=recompute,
)
st.selectbox(
    "Polyphony input policy",
    [
        PolyphonyPolicy.TOP_NOTE,
        PolyphonyPolicy.BOTTOM_NOTE,
        PolyphonyPolicy.FIRST_NOTE,
        PolyphonyPolicy.ERROR,
    ],
    key="polyphony_policy",
    width=240,
    format_func=lambda x: x.value,
    on_change=recompute,
)

if st.session_state.anchor_string is None or st.session_state.anchor_fret is None:
    st.caption("Selected target: none")
else:
    st.caption(
        f"Selected target: string {st.session_state.anchor_string}, fret "
        f"{st.session_state.anchor_fret}, note "
        f"{NoteName.from_pitch(presets[st.session_state.instrument].note_at(st.session_state.anchor_string, st.session_state.anchor_fret).pitch)}"
    )

if st.session_state.last_error:
    st.error(st.session_state.last_error)
elif st.session_state.rendered_tab:
    st.subheader("Output")
    st.code(st.session_state.rendered_tab)
