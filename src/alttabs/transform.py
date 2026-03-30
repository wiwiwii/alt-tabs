from alttabs.instrument import PlayedNote
from alttabs.errors import PolyphonyNotSupportedError, RangeNotPlayableError
from alttabs.pitch import Interval
from alttabs.score import RealizedEvent


class TransformError(Exception):
    pass


def transpose_monophonic_events(
    events: list[RealizedEvent],
    fretboard,
    interval: Interval,
) -> list[RealizedEvent]:
    if not events:
        return []

    transposed = []

    for idx, event in enumerate(events):
        if len(event.notes) != 1:
            raise PolyphonyNotSupportedError(
                f"Event {idx} is not monophonic: expected 1 note, got {len(event.notes)}"
            )

        source_note = event.notes[0]
        new_pitch = source_note.pitch.transpose(interval)

        positions = fretboard.positions_for(new_pitch)
        if not positions:
            raise RangeNotPlayableError(
                f"No playable position for transposed pitch {new_pitch.value} in event {idx}"
            )

        pos = positions[0]
        provisional_note = PlayedNote(
            pitch=new_pitch,
            position=pos,
        )

        transposed.append(
            RealizedEvent(
                measure_index=event.measure_index,
                at_column=event.at_column,
                notes=[provisional_note],
                source_event=getattr(event, "source_event", None),
            )
        )

    return transposed
