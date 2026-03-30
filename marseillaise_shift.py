from alttabs.instrument import presets
from alttabs.pipeline import TransformRequest, transform_tab
from alttabs.pitch import Interval
from alttabs.position_shift import PositionBias
from alttabs.score import RealizedEvent, TabRenderer
from alttabs.tab import TabParser
from alttabs.transform import transpose_monophonic_events
from alttabs.input_tab import parse_tab_text, to_realized_events

with open("la_marseillaise.txt") as f:
    text = f.read()


result = transform_tab(
    TransformRequest(
        text=text,
        instrument="acoustic_guitar",
        shift_positions=True,
        bias=PositionBias.DOWN,
        anchor_string=6,
        anchor_fret=3,
        max_fret_deviation=6,
        measures_per_line=2,
    )
)

print(result.rendered_tab)
