from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from alttabs.instrument import FretBoard, PlayedNote
from alttabs.pitch import Pitch
from alttabs.score import RealizedEvent, TabRenderer


class MidiTabError(Exception):
    pass


def midi_file_to_events_lowest_note(
    midi_path: str | Path,
    fretboard: FretBoard,
    events_per_measure: int = 16,
) -> list[RealizedEvent]:
    try:
        import mido
    except Exception as exc:
        raise MidiTabError(
            "MIDI dependency missing. Install `mido` to convert MIDI to tabs."
        ) from exc

    midi = mido.MidiFile(str(midi_path))
    notes_by_tick: dict[int, list[int]] = defaultdict(list)

    for track in midi.tracks:
        absolute_tick = 0
        for msg in track:
            absolute_tick += msg.time
            if msg.type == "note_on" and getattr(msg, "velocity", 0) > 0:
                notes_by_tick[absolute_tick].append(int(msg.note))

    if not notes_by_tick:
        raise MidiTabError("No note-on events found in MIDI output.")

    sorted_ticks = sorted(notes_by_tick.keys())
    realized: list[RealizedEvent] = []

    for idx, tick in enumerate(sorted_ticks):
        midi_note = min(notes_by_tick[tick])  # lowest-note policy for polyphony
        pitch = Pitch(midi_note)
        positions = fretboard.positions_for(pitch)
        if not positions:
            continue

        # Prefer thicker string for "lowest line" reading when possible.
        pos = max(positions, key=lambda p: p.string)
        measure_index = idx // events_per_measure
        at_column = 1 + (idx % events_per_measure) * 2

        realized.append(
            RealizedEvent(
                measure_index=measure_index,
                at_column=at_column,
                notes=[PlayedNote(pitch=pitch, position=pos)],
            )
        )

    if not realized:
        raise MidiTabError("MIDI notes are out of range for selected instrument.")

    return realized


def render_midi_file_to_tab(
    midi_path: str | Path,
    fretboard: FretBoard,
    measures_per_line: int = 2,
) -> str:
    events = midi_file_to_events_lowest_note(midi_path, fretboard)
    return TabRenderer(fretboard).render(events, measures_per_line=measures_per_line)
