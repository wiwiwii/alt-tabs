from alttabs.instrument import presets
from alttabs.pitch import Interval
from alttabs.score import RealizedEvent, TabRenderer, to_pitch_events
from alttabs.tab import TabParser


def test_parse_convert_rerender_identity_like():
    parser = TabParser(presets["electric_guitar"])
    renderer = TabRenderer(presets["electric_guitar"])

    text = """
e|--0--3--|
B|--1--3--|
G|--0--0--|
D|--2--0--|
A|--3--2--|
E|-----3--|
"""
    parsed = parser.parse(text)

    realized = [
        RealizedEvent(at_column=event.at_column, notes=list(event.notes))
        for event in parsed.events
    ]

    rendered = renderer.render(realized)

    lines = rendered.splitlines()
    assert lines[0] == "e|0-3|"
    assert lines[1] == "B|1-3|"
    assert lines[2] == "G|0-0|"
    assert lines[3] == "D|2-0|"
    assert lines[4] == "A|3-2|"
    assert lines[5] == "E|--3|"


def test_transpose_and_retab_naive():
    parser = TabParser(presets["electric_guitar"])
    renderer = TabRenderer(presets["electric_guitar"])
    fretboard = presets["electric_guitar"]

    text = """
e|--0--1--3--|
B|-----------|
G|-----------|
D|-----------|
A|-----------|
E|-----------|
"""
    parsed = parser.parse(text)
    pitch_events = to_pitch_events(parsed.events)

    transposed = []
    for event in pitch_events:
        shifted = [pitch.transpose(Interval(12)) for pitch in event.pitches]
        notes = []
        for pitch in shifted:
            pos = fretboard.positions_for(pitch)[0]
            notes.append(fretboard.note_at(pos.string, pos.fret))
        transposed.append(RealizedEvent(at_column=event.at_column, notes=notes))

    rendered = renderer.render(transposed)
    lines = rendered.splitlines()

    assert lines[0] == "e|12-13-15|"


def test_cross_string_relocation_scenario():
    renderer = TabRenderer(presets["electric_guitar"])

    events = [
        RealizedEvent(
            at_column=0,
            notes=[presets["electric_guitar"].note_at(6, 3)],  # G2
        ),
        RealizedEvent(
            at_column=1,
            notes=[presets["electric_guitar"].note_at(5, 2)],  # B2
        ),
        RealizedEvent(
            at_column=2,
            notes=[presets["electric_guitar"].note_at(5, 4)],  # C#3
        ),
    ]

    rendered = renderer.render(events)
    lines = rendered.splitlines()

    assert lines[4] == "A|--2-4|"
    assert lines[5] == "E|3----|"
