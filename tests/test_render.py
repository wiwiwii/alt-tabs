import pytest

from alttabs.instrument import FretPosition, PlayedNote, presets
from alttabs.pitch import Pitch
from alttabs.score import RealizedEvent, TabRenderer, TabRenderError


@pytest.fixture
def fretboard():
    return presets["electric_guitar"]


@pytest.fixture
def renderer(fretboard):
    return TabRenderer(fretboard)


def test_render_single_note(renderer):
    events = [
        RealizedEvent(
            at_column=0,
            notes=[PlayedNote(Pitch(67), FretPosition(1, 3))],
        )
    ]

    rendered = renderer.render(events)
    lines = rendered.splitlines()

    assert lines[0] == "e|3|"
    assert lines[1] == "B|-|"
    assert lines[2] == "G|-|"
    assert lines[3] == "D|-|"
    assert lines[4] == "A|-|"
    assert lines[5] == "E|-|"


def test_render_chord(renderer):
    events = [
        RealizedEvent(
            at_column=0,
            notes=[
                PlayedNote(Pitch(64), FretPosition(1, 0)),
                PlayedNote(Pitch(60), FretPosition(2, 1)),
                PlayedNote(Pitch(55), FretPosition(3, 0)),
                PlayedNote(Pitch(52), FretPosition(4, 2)),
                PlayedNote(Pitch(48), FretPosition(5, 3)),
            ],
        )
    ]

    rendered = renderer.render(events)
    lines = rendered.splitlines()

    assert lines[0] == "e|0|"
    assert lines[1] == "B|1|"
    assert lines[2] == "G|0|"
    assert lines[3] == "D|2|"
    assert lines[4] == "A|3|"
    assert lines[5] == "E|-|"


def test_render_multidigit_alignment(renderer):
    events = [
        RealizedEvent(
            at_column=0,
            notes=[PlayedNote(Pitch(67), FretPosition(1, 3))],
        ),
        RealizedEvent(
            at_column=4,
            notes=[PlayedNote(Pitch(74), FretPosition(1, 10))],
        ),
    ]

    rendered = renderer.render(events, min_gap=1)
    lines = rendered.splitlines()

    assert lines[0] == "e|3-10|"
    assert lines[1] == "B|----|"
    assert lines[2] == "G|----|"
    assert lines[3] == "D|----|"
    assert lines[4] == "A|----|"
    assert lines[5] == "E|----|"


def test_render_gap_enforcement(renderer):
    events = [
        RealizedEvent(
            at_column=0,
            notes=[PlayedNote(Pitch(67), FretPosition(1, 3))],
        ),
        RealizedEvent(
            at_column=2,
            notes=[PlayedNote(Pitch(69), FretPosition(1, 5))],
        ),
    ]

    rendered = renderer.render(events, min_gap=2)
    assert rendered.splitlines()[0] == "e|3--5|"


def test_render_duplicate_same_string_raises(renderer):
    events = [
        RealizedEvent(
            at_column=0,
            notes=[
                PlayedNote(Pitch(67), FretPosition(1, 3)),
                PlayedNote(Pitch(69), FretPosition(1, 5)),
            ],
        )
    ]

    with pytest.raises(TabRenderError):
        renderer.render(events)


def test_render_invalid_position_raises(renderer):
    events = [
        RealizedEvent(
            at_column=0,
            notes=[PlayedNote(Pitch(67), FretPosition(1, 99))],
        )
    ]

    with pytest.raises(TabRenderError):
        renderer.render(events)


def test_render_empty_event_raises(renderer):
    events = [RealizedEvent(at_column=0, notes=[])]
    with pytest.raises(TabRenderError):
        renderer.render(events)


def test_render_preserving_columns_exact(renderer):
    events = [
        RealizedEvent(at_column=0, notes=[PlayedNote(Pitch(67), FretPosition(1, 3))]),
        RealizedEvent(at_column=4, notes=[PlayedNote(Pitch(69), FretPosition(1, 5))]),
        RealizedEvent(at_column=8, notes=[PlayedNote(Pitch(71), FretPosition(1, 7))]),
    ]

    rendered = renderer.render_preserving_columns(events)
    assert rendered.splitlines()[0] == "e|3---5---7|"


def test_render_preserving_columns_collision_resolution(renderer):
    events = [
        RealizedEvent(at_column=2, notes=[PlayedNote(Pitch(74), FretPosition(1, 10))]),
        RealizedEvent(at_column=3, notes=[PlayedNote(Pitch(76), FretPosition(1, 12))]),
    ]

    rendered = renderer.render_preserving_columns(events)
    first_line = rendered.splitlines()[0]

    assert first_line == "e|--1012|"


def test_render_preserving_columns_sparse_layout(renderer):
    events = [
        RealizedEvent(at_column=20, notes=[PlayedNote(Pitch(67), FretPosition(1, 3))]),
    ]

    rendered = renderer.render_preserving_columns(events)
    first_line = rendered.splitlines()[0]

    assert first_line == "e|--------------------3|"
