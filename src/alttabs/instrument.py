from alttabs.pitch import Interval, Pitch


class InvalidFret(Exception):
    pass


class InvalidString(Exception):
    pass


class InvalidTuning(Exception):
    pass


class StringSpec:
    """
    Represent a guitar/bass string, identified by a unique positive number,
    with its open pitch.
    """

    def __init__(self, number: int, open_pitch: Pitch):
        if not isinstance(number, int):
            raise TypeError("String number must be an int")
        if number <= 0:
            raise InvalidString("String number must be positive")

        self.number = number
        self.open_pitch = open_pitch


class Tuning:
    """Represent the set of strings for one instrument."""

    def __init__(self, strings: list[StringSpec]):
        if not strings:
            raise InvalidTuning("Tuning must contain at least one string")

        numbers = [string.number for string in strings]
        if len(numbers) != len(set(numbers)):
            raise InvalidTuning("String numbers must be unique")

        self.strings = strings
        self._by_number = {string.number: string for string in strings}

    def get_string(self, number: int) -> StringSpec:
        try:
            return self._by_number[number]
        except KeyError:
            raise InvalidString(f"Unknown string number: {number}")


class FretPosition:
    """Represent a playable fret position."""

    def __init__(self, string: int, fret: int):
        if not isinstance(string, int):
            raise TypeError("String must be an int")
        if not isinstance(fret, int):
            raise TypeError("Fret must be an int")
        if string <= 0:
            raise InvalidString("String number must be positive")
        if fret < 0:
            raise InvalidFret("Fret cannot be negative")

        self.string = string
        self.fret = fret


class PlayedNote:
    """One realized note on a fretted instrument."""

    def __init__(self, pitch: Pitch, position: FretPosition):
        self.pitch = pitch
        self.position = position


class FretBoard:
    """Represent a fretted instrument with one tuning and a maximum fret."""

    def __init__(self, tuning: Tuning, max_fret: int):
        if not isinstance(max_fret, int):
            raise TypeError("max_fret must be an int")
        if max_fret < 0:
            raise InvalidFret("max_fret cannot be negative")

        self.tuning = tuning
        self.max_fret = max_fret

    def _validate_fret(self, fret: int):
        if not isinstance(fret, int):
            raise TypeError("Fret must be an int")
        if fret < 0 or fret > self.max_fret:
            raise InvalidFret(f"Fret must be between 0 and {self.max_fret}")

    def pitch_at(self, string: int, fret: int) -> Pitch:
        """Return the pitch played on a given string at a given fret."""
        self._validate_fret(fret)
        string_spec = self.tuning.get_string(string)
        return string_spec.open_pitch.transpose(Interval(fret))

    def is_valid_position(self, position: FretPosition) -> bool:
        try:
            self.tuning.get_string(position.string)
        except InvalidString:
            return False
        return 0 <= position.fret <= self.max_fret

    def note_at(self, string: int, fret: int) -> PlayedNote:
        """Return a PlayedNote at a given string/fret."""
        position = FretPosition(string, fret)
        if not self.is_valid_position(position):
            raise InvalidFret("Invalid played position")
        pitch = self.pitch_at(string, fret)
        return PlayedNote(pitch, position)

    def fret_for(self, string: int, pitch: Pitch):
        """Return the fret for this pitch on this string, or None if impossible."""
        string_spec = self.tuning.get_string(string)
        fret = pitch.value - string_spec.open_pitch.value

        if fret < 0 or fret > self.max_fret:
            return None
        return fret

    def positions_for(self, pitch: Pitch):
        """Return all playable positions for a given pitch."""
        result = []
        for string_spec in self.tuning.strings:
            fret = self.fret_for(string_spec.number, pitch)
            if fret is not None:
                result.append(FretPosition(string_spec.number, fret))
        return result


guitar_strings = [
    StringSpec(1, Pitch(64)),
    StringSpec(2, Pitch(59)),
    StringSpec(3, Pitch(55)),
    StringSpec(4, Pitch(50)),
    StringSpec(5, Pitch(45)),
    StringSpec(6, Pitch(40)),
]
bass_strings = [
    StringSpec(1, Pitch(43)),
    StringSpec(2, Pitch(38)),
    StringSpec(3, Pitch(33)),
    StringSpec(4, Pitch(28)),
]

STANDARD_GUITAR_TUNING = Tuning(guitar_strings)
STANDARD_BASS_TUNING = Tuning(bass_strings)

presets = {
    "acoustic_guitar": FretBoard(STANDARD_GUITAR_TUNING, 15),
    "electric_guitar": FretBoard(STANDARD_GUITAR_TUNING, 22),
    "bass": FretBoard(STANDARD_BASS_TUNING, 22),
}
