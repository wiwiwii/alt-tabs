from __future__ import annotations

from dataclasses import dataclass

from alttabs.input_tab import parse_tab_text, to_realized_events
from alttabs.instrument import presets
from alttabs.pitch import Interval
from alttabs.position_shift import (
    PositionBias,
    RetabPreferences,
    shift_monophonic_events,
)
from alttabs.score import TabRenderer
from alttabs.transform import transpose_monophonic_events


class PipelineError(Exception):
    pass


@dataclass(frozen=True)
class TransformRequest:
    text: str
    instrument: str = "acoustic_guitar"

    # transpose_semitones: int = 0

    shift_positions: bool = False
    bias: PositionBias = PositionBias.DOWN
    anchor_string: int | None = None
    anchor_fret: int | None = None
    max_fret_deviation: int = 6
    prefer_open_strings: bool | None = None

    measures_per_line: int = 2


@dataclass(frozen=True)
class TransformResult:
    rendered_tab: str
    parsed_block_count: int
    expanded_event_count: int
    measure_count: int


def transform_tab(request: TransformRequest) -> TransformResult:
    if request.instrument not in presets:
        raise PipelineError(f"Unknown instrument preset: {request.instrument}")

    fretboard = presets[request.instrument]

    parsed_blocks = parse_tab_text(request.text, fretboard)
    events = to_realized_events(parsed_blocks)
    first_pitch = events[0].notes[0].pitch
    # if request.anchor_string is not None and request.anchor_fret is not None:
    #     target_pitch = fretboard.note_at(
    #         request.anchor_string, request.anchor_fret
    #     ).pitch
    #     events = transpose_monophonic_events(
    #         events, fretboard, Interval(first_pitch.value - target_pitch.value)
    #     )
    #
    # if request.transpose_semitones != 0:
    #     events = transpose_monophonic_events(
    #         events,
    #         fretboard,
    #         Interval(request.transpose_semitones),
    #     )

    if request.shift_positions:
        if not events:
            raise PipelineError("Cannot shift positions on an empty event stream")
        if request.anchor_string is not None and request.anchor_fret is not None:
            target_pitch = fretboard.note_at(
                request.anchor_string, request.anchor_fret
            ).pitch
            print(
                f"First pitch: {first_pitch.value}, target pitch: {target_pitch.value}"
            )
            print(f"Transposition: {target_pitch.value - first_pitch.value}")
            events = transpose_monophonic_events(
                events, fretboard, Interval(target_pitch.value - first_pitch.value)
            )

        if request.anchor_string is None or request.anchor_fret is None:
            first_note = events[0].notes[0]
            anchor_string = first_note.position.string
            anchor_fret = first_note.position.fret
        else:
            anchor_string = request.anchor_string
            anchor_fret = request.anchor_fret

        events = shift_monophonic_events(
            events,
            fretboard,
            RetabPreferences(
                anchor_string=anchor_string,
                anchor_fret=anchor_fret,
                bias=request.bias,
                max_fret_deviation=request.max_fret_deviation,
                prefer_open_strings=request.prefer_open_strings,
            ),
        )
    renderer = TabRenderer(fretboard)
    rendered = renderer.render(
        events,
        measures_per_line=request.measures_per_line,
    )

    measure_count = 0
    for block in parsed_blocks:
        measure_count += block.parsed_tab.measure_count * block.raw_block.repeat

    return TransformResult(
        rendered_tab=rendered,
        parsed_block_count=len(parsed_blocks),
        expanded_event_count=len(events),
        measure_count=measure_count,
    )
