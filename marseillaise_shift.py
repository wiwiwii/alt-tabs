from alttabs.instrument import presets
from alttabs.pitch import Interval
from alttabs.position_shift import (
    PositionBias,
    RetabPreferences,
    shift_monophonic_events,
)
from alttabs.score import RealizedEvent, TabRenderer
from alttabs.tab import TabParser
from alttabs.transform import transpose_monophonic_events
from src.alttabs.input_tab import parse_tab_text, to_realized_events

# text = """
# e|----------------|
# B|----------------|
# G|--0--2--4--5----|
# D|----------------|
# A|----------------|
# E|----------------|
# """

with open("la_marseillaise.txt") as f:
    text = f.read()

fretboard = presets["acoustic_guitar"]
parsed_blocks = parse_tab_text(text, fretboard)
# parser = TabParser(fretboard)
renderer = TabRenderer(fretboard)

# parsed = parser.parse(text)

events = to_realized_events(parsed_blocks)
source_events = [
    RealizedEvent(
        measure_index=event.measure_index,
        at_column=event.at_column,
        notes=list(event.notes),
    )
    for event in events
]

transposed = transpose_monophonic_events(
    source_events,
    fretboard,
    Interval(-7),
)

shifted = shift_monophonic_events(
    transposed,
    fretboard,
    RetabPreferences(
        anchor_string=6,
        anchor_fret=3,
        bias=PositionBias.DOWN,
        max_fret_deviation=6,
    ),
)

print(renderer.render(shifted, measures_per_line=2))
