from alttabs.instrument import FretPosition, PlayedNote, presets
from alttabs.pitch import Interval
from alttabs.score import RealizedEvent, TabRenderer
from alttabs.tab import TabParser


def transpose_events(events, fretboard, interval: Interval):
    new_events = []

    for event in events:
        new_notes = []

        for note in event.notes:
            new_pitch = note.pitch.transpose(interval)

            string = note.position.string
            fret = fretboard.fret_for(string, new_pitch)

            if fret is None:
                # naive fallback: pick first available position
                pos = fretboard.positions_for(new_pitch)[0]
                new_notes.append(fretboard.note_at(pos.string, pos.fret))
            else:
                new_notes.append(PlayedNote(new_pitch, FretPosition(string, fret)))

        new_events.append(
            RealizedEvent(event.measure_index, event.at_column, new_notes)
        )

    return new_events


parser = TabParser(presets["acoustic_guitar"])
renderer = TabRenderer(presets["acoustic_guitar"])

text = """
e|-0---------------|-0---------------|-3-------3-------|-2-------2-------|
B|-1-------1-------|-0-------0-------|-0-----0---0-----|-3-----3---3-----|
G|-2-----2---2-----|-1-----1---1-----|-0---0-------0---|-2---2-------2---|
D|-2---2-------2---|-0---0-------0---|-0-------------0-|-0-------------0-|
A|-0-------------0-|-2-------------2-|-2---------------|-----------------|
E|-----------------|-0---------------|-3---------------|-----------------|
"""

parsed = parser.parse(text)

events = [
    RealizedEvent(
        measure_index=event.measure_index,
        at_column=event.at_column,
        notes=list(event.notes),
    )
    for event in parsed.events
]
transposed = transpose_events(events, presets["acoustic_guitar"], Interval(2))
print("Original:")
print(renderer.render_preserving_columns(events))
print("Transposed:")
print(renderer.render_preserving_columns(transposed))
