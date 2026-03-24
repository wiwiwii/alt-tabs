import pytest

from alttabs.instrument import presets
from alttabs.tab import TabParseError, TabParser


@pytest.fixture
def parser():
    return TabParser(presets["electric_guitar"])


def test_parse_single_note(parser):
    text = """
e|--3--|
B|-----|
G|-----|
D|-----|
A|-----|
E|-----|
"""
    parsed = parser.parse(text)

    assert len(parsed.events) == 1
    event = parsed.events[0]
    assert len(event.notes) == 1

    note = event.notes[0]
    assert event.at_column == 3
    assert note.position.string == 1
    assert note.position.fret == 3
    assert note.pitch.value == 67  # G4


def test_parse_chord_alignment(parser):
    text = """
e|--0--|
B|--1--|
G|--0--|
D|--2--|
A|--3--|
E|-----|
"""
    parsed = parser.parse(text)

    assert len(parsed.events) == 1
    event = parsed.events[0]
    assert len(event.notes) == 5
    assert all(n.position.fret in {0, 1, 2, 3} for n in event.notes)
    assert event.at_column == 3


def test_parse_multiple_events(parser):
    text = """
e|--0--3--|
B|--1--3--|
G|--0--0--|
D|--2--0--|
A|--3--2--|
E|-----3--|
"""
    parsed = parser.parse(text)

    assert len(parsed.events) == 2
    assert parsed.events[0].at_column < parsed.events[1].at_column
    assert len(parsed.events[0].notes) == 5
    assert len(parsed.events[1].notes) == 6


def test_parse_multidigit_fret(parser):
    text = """
e|--10--|
B|------|
G|------|
D|------|
A|------|
E|------|
"""
    parsed = parser.parse(text)

    assert len(parsed.events) == 1
    note = parsed.events[0].notes[0]
    assert note.position.string == 1
    assert note.position.fret == 10
    assert note.pitch.value == 74


def test_parse_adjacent_multidigit_frets(parser):
    text = """
e|--10-11--|
B|---------|
G|---------|
D|---------|
A|---------|
E|---------|
"""
    parsed = parser.parse(text)

    assert len(parsed.events) == 2
    frets = [event.notes[0].position.fret for event in parsed.events]
    assert frets == [10, 11]


def test_parse_without_labels(parser):
    text = """
|--0--|
|--1--|
|--0--|
|--2--|
|--3--|
|-----|
"""
    parsed = parser.parse(text)

    assert [line.string for line in parsed.string_lines] == [1, 2, 3, 4, 5, 6]
    assert len(parsed.events) == 1
    assert len(parsed.events[0].notes) == 5


def test_parse_wrong_number_of_lines_raises(parser):
    text = """
e|--0--|
B|--1--|
G|--0--|
D|--2--|
A|--3--|
"""
    with pytest.raises(TabParseError):
        parser.parse(text)


def test_parse_missing_bar_raises(parser):
    text = """
e--0--|
B|-----|
G|-----|
D|-----|
A|-----|
E|-----|
"""
    with pytest.raises(TabParseError):
        parser.parse(text)
