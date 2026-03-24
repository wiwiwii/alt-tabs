import pytest

from alttabs.instrument import (
    FretPosition,
    InvalidFret,
    InvalidString,
    PlayedNote,
    presets,
)
from alttabs.pitch import Pitch


@pytest.fixture
def guitar():
    return presets["electric_guitar"]


@pytest.fixture
def bass():
    return presets["bass"]


def test_guitar_open_strings(guitar):
    assert guitar.pitch_at(1, 0).value == 64
    assert guitar.pitch_at(2, 0).value == 59
    assert guitar.pitch_at(3, 0).value == 55
    assert guitar.pitch_at(4, 0).value == 50
    assert guitar.pitch_at(5, 0).value == 45
    assert guitar.pitch_at(6, 0).value == 40


def test_bass_open_strings(bass):
    assert bass.pitch_at(1, 0).value == 43
    assert bass.pitch_at(2, 0).value == 38
    assert bass.pitch_at(3, 0).value == 33
    assert bass.pitch_at(4, 0).value == 28


def test_fret_mapping_examples(guitar):
    assert guitar.pitch_at(6, 3).value == 43  # G2
    assert guitar.pitch_at(5, 5).value == 50  # D3


@pytest.mark.parametrize(
    ("string", "fret"),
    [(1, 0), (1, 7), (3, 0), (4, 5), (6, 3), (6, 22)],
)
def test_pitch_at_and_fret_for_are_inverse(guitar, string, fret):
    pitch = guitar.pitch_at(string, fret)
    assert guitar.fret_for(string, pitch) == fret


def test_fret_for_below_open_string_returns_none(guitar):
    assert guitar.fret_for(1, Pitch(40)) is None


def test_fret_for_above_max_fret_returns_none(guitar):
    assert guitar.fret_for(6, Pitch(100)) is None


def test_positions_for_known_pitch_g3(guitar):
    positions = guitar.positions_for(Pitch(55))  # G3
    got = {(p.string, p.fret) for p in positions}
    print(f"got: {got}")
    expected = {
        (3, 0),  # open G string
        (4, 5),  # D string 5th fret
        (6, 15),  # low E string 15th fret
        (5, 10),  # A string, 10th fret
    }
    assert expected.issubset(got)


def test_pitch_at_negative_fret_raises(guitar):
    with pytest.raises(InvalidFret):
        guitar.pitch_at(1, -1)


def test_pitch_at_unknown_string_raises(guitar):
    with pytest.raises(InvalidString):
        guitar.pitch_at(7, 0)


def test_is_valid_position(guitar):
    assert guitar.is_valid_position(FretPosition(1, 0)) is True
    assert guitar.is_valid_position(FretPosition(6, 22)) is True
    assert guitar.is_valid_position(FretPosition(6, 23)) is False
    assert guitar.is_valid_position(FretPosition(7, 0)) is False


def test_note_at_returns_played_note(guitar):
    played = guitar.note_at(6, 3)
    assert isinstance(played, PlayedNote)
    assert played.pitch.value == 43
    assert played.position.string == 6
    assert played.position.fret == 3
