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

text = """
e|----------------|
B|----------------|
G|--0--2--4--5----|
D|----------------|
A|----------------|
E|----------------|
"""

fretboard = presets["electric_guitar"]
parser = TabParser(fretboard)
renderer = TabRenderer(fretboard)

parsed = parser.parse(text)

source_events = [
    RealizedEvent(
        measure_index=event.measure_index,
        at_column=event.at_column,
        notes=list(event.notes),
    )
    for event in parsed.events
]

transposed = transpose_monophonic_events(
    source_events,
    fretboard,
    Interval(-12),
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

print(renderer.render_preserving_columns(shifted))
