class InvalidPitch(Exception):
    pass


class InvalidPitchClass(Exception):
    pass


class InvalidNoteName(Exception):
    pass


class Interval:
    """Interval in semitones."""

    def __init__(self, semitones: int):
        self.semitones = semitones


class Pitch:
    """Absolute pitch as a MIDI number (0..127)."""

    def __init__(self, value: int):
        if not isinstance(value, int):
            raise TypeError("Pitch value must be an int")
        if not 0 <= value <= 127:
            raise InvalidPitch("Pitch must be between 0 and 127")
        self.value = value

    def next_semitone(self):
        if self.value == 127:
            raise InvalidPitch("Cannot go above MIDI 127")
        return Pitch(self.value + 1)

    def prev_semitone(self):
        if self.value == 0:
            raise InvalidPitch("Cannot go below MIDI 0")
        return Pitch(self.value - 1)

    def transpose(self, interval: Interval):
        return Pitch(self.value + interval.semitones)

    def pitch_class(self):
        return PitchClass(self.value % 12)


class PitchClass:
    """Pitch class between 0 and 11."""

    def __init__(self, value: int):
        if not isinstance(value, int):
            raise TypeError("PitchClass value must be an int")
        if not 0 <= value <= 11:
            raise InvalidPitchClass("PitchClass must be between 0 and 11")
        self.value = value


class NoteName:
    """Readable note name. Convention: sharps, not flats. Scientific pitch notation."""

    LETTER_TO_SEMITONE = {
        "C": 0,
        "D": 2,
        "E": 4,
        "F": 5,
        "G": 7,
        "A": 9,
        "B": 11,
    }

    PITCH_CLASS_TO_NAME = [
        ("C", 0),
        ("C", 1),
        ("D", 0),
        ("D", 1),
        ("E", 0),
        ("F", 0),
        ("F", 1),
        ("G", 0),
        ("G", 1),
        ("A", 0),
        ("A", 1),
        ("B", 0),
    ]

    def __init__(self, octave: int, letter: str, accidental: int = 0):
        if letter not in self.LETTER_TO_SEMITONE:
            raise InvalidNoteName(f"Invalid note letter: {letter}")
        if accidental not in (-1, 0, 1):
            raise InvalidNoteName("Only -1 (flat), 0 (natural), 1 (sharp) supported")
        if not isinstance(octave, int):
            raise TypeError("Octave must be an int")

        self.octave = octave
        self.letter = letter
        self.accidental = accidental

    def to_pitch(self):
        semitone_in_octave = self.LETTER_TO_SEMITONE[self.letter] + self.accidental
        midi_value = (self.octave + 1) * 12 + semitone_in_octave
        return Pitch(midi_value)

    @classmethod
    def from_pitch(cls, pitch: Pitch):
        pitch_class = pitch.value % 12
        octave = (pitch.value // 12) - 1
        letter, accidental = cls.PITCH_CLASS_TO_NAME[pitch_class]
        return cls(octave=octave, letter=letter, accidental=accidental)

