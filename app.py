import streamlit as st

from alttabs.pipeline import TransformRequest, transform_tab
from alttabs.position_shift import PositionBias

st.set_page_config(page_title="Alt Tabs", layout="wide")


# -----------------------------
# Config
# -----------------------------
INSTRUMENTS = {
    "acoustic_guitar": {
        "label": "Acoustic Guitar",
        "image": "assets/acoustic.png",
        "string_count": 6,
        "open_notes": ["E", "A", "D", "G", "B", "E"],
        "max_fret": 24,
    },
    "electric_guitar": {
        "label": "Electric Guitar",
        "image": "assets/electric.png",
        "string_count": 6,
        "open_notes": ["E", "A", "D", "G", "B", "E"],  # low -> high
        "max_fret": 24,
    },
    "bass": {
        "label": "Bass",
        "image": "assets/bass.png",
        "string_count": 4,
        "open_notes": ["E", "A", "D", "G"],  # low -> high
        "max_fret": 24,
    },
}


# -----------------------------
# State init
# -----------------------------
defaults = {
    "instrument": "acoustic_guitar",
    "transpose_semitones": 0,
    "shift_positions": False,
    "bias": PositionBias.CENTERED,
    "anchor_string": 6,
    "anchor_fret": 3,
    "max_fret_deviation": 6,
    "measures_per_line": 4,
    "text": "",
    "result": None,
    "error": None,
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# -----------------------------
# Helpers
# -----------------------------
def set_instrument(name: str):
    st.session_state.instrument = name

    string_count = INSTRUMENTS[name]["string_count"]

    # Keep anchor string valid when switching instrument
    if st.session_state.anchor_string > string_count:
        st.session_state.anchor_string = string_count


def select_position(string_number: int, fret: int):
    st.session_state.anchor_string = string_number
    st.session_state.anchor_fret = fret
    st.session_state.shift_positions = True


def render_instrument_selector():
    st.subheader("Instrument")

    cols = st.columns(3)
    instrument_keys = list(INSTRUMENTS.keys())

    for col, key in zip(cols, instrument_keys):
        cfg = INSTRUMENTS[key]
        selected = st.session_state.instrument == key

        with col:
            st.image(cfg["image"], use_container_width=True)
            button_label = f"{'●' if selected else '○'} {cfg['label']}"
            st.button(
                button_label,
                key=f"instrument_{key}",
                use_container_width=True,
                on_click=set_instrument,
                args=(key,),
                type="primary" if selected else "secondary",
            )


def render_fretboard_selector():
    instrument = st.session_state.instrument
    cfg = INSTRUMENTS[instrument]
    string_count = cfg["string_count"]
    max_fret = cfg["max_fret"]

    st.subheader("Target position")
    st.caption(
        "Click the fret where the first played note should land. "
        "This sets anchor_string and anchor_fret."
    )

    selected_string = st.session_state.anchor_string
    selected_fret = st.session_state.anchor_fret

    # Fret header
    header_cols = st.columns([1.2] + [1] * (max_fret + 1))
    with header_cols[0]:
        st.markdown("**String**")
    for fret in range(max_fret + 1):
        with header_cols[fret + 1]:
            st.markdown(f"**{fret}**")

    # Display top string first visually, but keep numbering consistent:
    # string 1 = highest-pitched string
    # string 6 or 4 = lowest-pitched string
    #
    # Your backend currently seems to use guitar-style numbering where:
    # 1 = high E, 6 = low E
    #
    # open_notes in config are low -> high, so reverse for rendering.
    visual_rows = []
    for idx in range(string_count):
        backend_string_number = idx + 1  # 1..N high->low? depends on your convention
        visual_rows.append(backend_string_number)

    # If your backend uses 1 = high string, 6 = low string, render low at bottom:
    # show high string first
    for string_number in visual_rows:
        row = st.columns([1.2] + [1] * (max_fret + 1))

        with row[0]:
            st.markdown(f"**{string_number}**")

        for fret in range(max_fret + 1):
            is_selected = string_number == selected_string and fret == selected_fret

            label = "●" if is_selected else "○"
            row[fret + 1].button(
                label,
                key=f"pos_s{string_number}_f{fret}",
                on_click=select_position,
                args=(string_number, fret),
                use_container_width=True,
                type="primary" if is_selected else "secondary",
            )

    st.caption(
        f"Selected target: string {st.session_state.anchor_string}, "
        f"fret {st.session_state.anchor_fret}"
    )


def run_transform():
    st.session_state.error = None
    st.session_state.result = None

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
        st.session_state.result = result

    except Exception as e:
        st.session_state.error = str(e)


# -----------------------------
# UI
# -----------------------------
st.title("Alt Tabs")

render_instrument_selector()

st.divider()

st.subheader("Input tab")
st.text_area(
    "Input tab",
    key="text",
    height=320,
    label_visibility="collapsed",
    placeholder="Paste tab here...",
)

controls_left, controls_right = st.columns([1.4, 1])

with controls_left:
    st.subheader("Transform")

    row1 = st.columns(3)
    row1[0].number_input(
        "Transpose (semitones)",
        min_value=-24,
        max_value=24,
        step=1,
        key="transpose_semitones",
    )
    row1[1].checkbox("Shift positions", key="shift_positions")
    row1[2].selectbox(
        "Bias",
        [PositionBias.DOWN, PositionBias.CENTERED, PositionBias.UP],
        key="bias",
        format_func=lambda x: x.value,
    )

    row2 = st.columns(3)
    row2[0].number_input(
        "Max fret deviation",
        min_value=1,
        max_value=24,
        step=1,
        key="max_fret_deviation",
    )
    row2[1].number_input(
        "Measures per line",
        min_value=1,
        max_value=16,
        step=1,
        key="measures_per_line",
    )
    row2[2].empty()

with controls_right:
    st.subheader("Selected position")
    st.metric("Anchor string", st.session_state.anchor_string)
    st.metric("Anchor fret", st.session_state.anchor_fret)

if st.session_state.shift_positions:
    render_fretboard_selector()

st.divider()

st.button("Transform", type="primary", use_container_width=True, on_click=run_transform)

st.divider()

st.subheader("Output")

if st.session_state.error:
    st.error(st.session_state.error)

if st.session_state.result:
    result = st.session_state.result

    st.code(result.rendered_tab)

    stats_cols = st.columns(3)
    stats_cols[0].metric("Parsed blocks", result.parsed_block_count)
    stats_cols[1].metric("Expanded events", result.expanded_event_count)
    stats_cols[2].metric("Measures", result.measure_count)

