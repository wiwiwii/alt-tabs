import streamlit as st

from alttabs.pipeline import TransformRequest, transform_tab
from alttabs.position_shift import PositionBias

st.set_page_config(page_title="Alt Tabs", layout="wide")

st.title("Alt Tabs")

left, right = st.columns(2)

with left:
    text = st.text_area("Input tab", height=500)

    instrument = st.selectbox(
        "Instrument",
        ["acoustic_guitar", "electric_guitar", "bass"],
        index=0,
    )

    transpose_semitones = st.number_input(
        "Transpose (semitones)",
        min_value=-24,
        max_value=24,
        value=0,
        step=1,
    )

    shift_positions = st.checkbox("Shift positions", value=False)

    bias = st.selectbox(
        "Bias",
        [PositionBias.DOWN, PositionBias.CENTERED, PositionBias.UP],
        index=1,
        format_func=lambda x: x.value,
    )

    anchor_string = st.number_input(
        "Anchor string",
        min_value=1,
        max_value=6,
        value=6,
        step=1,
    )

    anchor_fret = st.number_input(
        "Anchor fret",
        min_value=0,
        max_value=24,
        value=3,
        step=1,
    )

    max_fret_deviation = st.number_input(
        "Max fret deviation",
        min_value=1,
        max_value=24,
        value=6,
        step=1,
    )

    measures_per_line = st.number_input(
        "Measures per line",
        min_value=1,
        max_value=16,
        value=4,
        step=1,
    )

    run = st.button("Transform", type="primary")

with right:
    if run:
        try:
            result = transform_tab(
                TransformRequest(
                    text=text,
                    instrument=instrument,
                    transpose_semitones=transpose_semitones,
                    shift_positions=shift_positions,
                    bias=bias,
                    anchor_string=anchor_string if shift_positions else None,
                    anchor_fret=anchor_fret if shift_positions else None,
                    max_fret_deviation=max_fret_deviation,
                    measures_per_line=measures_per_line,
                )
            )

            st.subheader("Output")
            st.code(result.rendered_tab)

            st.subheader("Stats")
            st.write(f"Parsed blocks: {result.parsed_block_count}")
            st.write(f"Expanded events: {result.expanded_event_count}")
            st.write(f"Measures: {result.measure_count}")

        except Exception as e:
            st.error(str(e))
