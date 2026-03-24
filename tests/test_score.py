from alttabs.instrument import presets
from alttabs.score import PitchEvent, to_pitch_events
from alttabs.tab import TabParser


def test_to_pitch_events_integrity():
    parser = TabParser(presets["electric_guitar"])
    text = """
e|--0--3--|
B|--1--3--|
G|--0--0--|
D|--2--0--|
A|--3--2--|
E|-----3--|
"""
    parsed = parser.parse(text)
    pitch_events = to_pitch_events(parsed.events)

    assert len(pitch_events) == len(parsed.events)

    for tab_event, pitch_event in zip(parsed.events, pitch_events):
        assert pitch_event.at_column == tab_event.at_column
        assert len(pitch_event.pitches) == len(pitch_event.source_notes)
        for pitch, source_note in zip(pitch_event.pitches, pitch_event.source_notes):
            assert pitch.value == source_note.pitch.value


def test_pitch_events_do_not_mutate_source_notes():
    parser = TabParser(presets["electric_guitar"])
    text = """
e|--0--|
B|-----|
G|-----|
D|-----|
A|-----|
E|-----|
"""
    parsed = parser.parse(text)
    pitch_events = to_pitch_events(parsed.events)

    assert pitch_events[0].source_notes[0].pitch.value == 64

    pitch_events[0].pitches[0] = pitch_events[0].pitches[0].next_semitone()

    assert pitch_events[0].pitches[0].value == 65
    assert pitch_events[0].source_notes[0].pitch.value == 64
