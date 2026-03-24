from pitch import Interval, Pitch


class InvalidFret(Exception):
    pass


class StringSpec:
    """
    Represent a guitar/bass string. Identified by a unique number, with its open pitch.
    """

    def __init__(self, number: int, open_pitch: Pitch):
        self.number = number
        self.open_pitch = open_pitch


class Tuning:
    """Represent a set of strings (for the whole instrument)"""

    def __init__(self, strings: list[StringSpec]):
        self.strings = strings


class FretPosition:
    """Represent a playable fret position"""

    def __init__(self, string: int, position: int):
        self.string = string
        self.position = position


class FretBoard:
    """Represent the entire instrument"""

    def __init__(self, tuning: Tuning, max_fret: int):
        self.tuning = tuning
        self.max_fret = max_fret

    def pitch_at(self, string, fret) -> Pitch:
        """returns the pitch when the strign is played at this position"""
        if fret > self.max_fret:
            raise InvalidFret
        return self.tuning.strings[string].open_pitch.transpose(Interval(fret))

    def fret_for(self, string: int, pitch: Pitch):
        """returns the fret to play that pitch on this string, None if impossible"""
        starting_pitch = self.tuning.strings[string].open_pitch.value
        if pitch.value < starting_pitch:
            return None
        fret = pitch.value - starting_pitch
        if fret > self.max_fret:
            return None
        return fret

    def positions_for(self, pitch: Pitch):
        """Returns list of possible positions to play a given pitch"""
        result = []
        for string in self.tuning.strings:
            fret = self.fret_for(string.number, pitch)
            if fret is not None:
                result.append(FretPosition(string.number, fret))
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
presets = {
    "acoustic_guitar": FretBoard(Tuning(guitar_strings), 15),
    "electric_guitar": FretBoard(Tuning(guitar_strings), 22),
    "bass": FretBoard(Tuning(bass_strings), 22),
}
