import pytest

from alttabs.pitch import Interval, InvalidNoteName, InvalidPitch, NoteName, Pitch


@pytest.mark.parametrize("value", [0, 1, 11, 12, 59, 60, 61, 127])
def test_pitch_note_roundtrip(value):
    pitch = Pitch(value)
    note = NoteName.from_pitch(pitch)
    rebuilt = note.to_pitch()
    assert rebuilt.value == value


@pytest.mark.parametrize(
    ("octave", "letter", "accidental", "expected"),
    [
        (-1, "C", 0, 0),  # C-1 = MIDI 0
        (0, "C", 0, 12),  # C0
        (4, "C", 0, 60),  # C4
        (4, "C", 1, 61),  # C#4
        (4, "D", -1, 61),  # Db4
        (8, "C", 0, 108),  # C8
    ],
)
def test_note_to_pitch(octave, letter, accidental, expected):
    note = NoteName(octave=octave, letter=letter, accidental=accidental)
    assert note.to_pitch().value == expected


def test_enharmonic_collapse():
    c_sharp = NoteName(octave=4, letter="C", accidental=1).to_pitch()
    d_flat = NoteName(octave=4, letter="D", accidental=-1).to_pitch()
    assert c_sharp.value == d_flat.value == 61


def test_interval_transpose_positive():
    assert Pitch(60).transpose(Interval(12)).value == 72


def test_interval_transpose_negative():
    assert Pitch(60).transpose(Interval(-12)).value == 48


def test_prev_semitone_lower_bound():
    with pytest.raises(InvalidPitch):
        Pitch(0).prev_semitone()


def test_next_semitone_upper_bound():
    with pytest.raises(InvalidPitch):
        Pitch(127).next_semitone()


def test_invalid_note_letter():
    with pytest.raises(InvalidNoteName):
        NoteName(octave=4, letter="H", accidental=0)
