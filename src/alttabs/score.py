from alttabs.instrument import FretBoard, PlayedNote
from alttabs.pitch import Pitch
from alttabs.tab import TabEvent


class PitchEvent:
    def __init__(
        self, at_column: int, pitches: list[Pitch], source_notes: list[PlayedNote]
    ):
        self.at_column = at_column
        self.pitches = pitches
        self.source_notes = source_notes


def to_pitch_events(tab_events: list[TabEvent]) -> list[PitchEvent]:
    result = []
    for event in tab_events:
        result.append(
            PitchEvent(
                at_column=event.at_column,
                pitches=[note.pitch for note in event.notes],
                source_notes=list(event.notes),
            )
        )
    return result


class RealizedEvent:
    def __init__(self, at_column: int, notes: list[PlayedNote], source_event=None):
        self.at_column = at_column
        self.notes = notes
        self.source_event = source_event


class TabRenderError(Exception):
    pass


class TabRenderer:
    def __init__(
        self, fretboard: FretBoard, show_labels: bool = True, bar_edges: bool = True
    ):
        self.fretboard = fretboard
        self.show_labels = show_labels
        self.bar_edges = bar_edges

    def render(self, events: list[RealizedEvent], min_gap: int = 1) -> str:
        """
        Render events into normalized ASCII tab.
        Does not preserve exact source columns.
        """
        if min_gap < 0:
            raise ValueError("min_gap must be >= 0")

        ordered_strings = [spec.number for spec in self.fretboard.tuning.strings]
        buffers = {string: [] for string in ordered_strings}

        first_event = True

        for event in events:
            self._validate_event(event)

            notes_by_string = {}
            for note in event.notes:
                string = note.position.string
                if string in notes_by_string:
                    raise TabRenderError(
                        f"Multiple notes on the same string in one event: string {string}"
                    )
                notes_by_string[string] = note

            event_width = max(len(str(note.position.fret)) for note in event.notes)

            if not first_event and min_gap > 0:
                for string in ordered_strings:
                    buffers[string].extend("-" * min_gap)

            for string in ordered_strings:
                note = notes_by_string.get(string)
                if note is None:
                    buffers[string].extend("-" * event_width)
                else:
                    fret_text = str(note.position.fret)
                    buffers[string].extend(fret_text)
                    buffers[string].extend("-" * (event_width - len(fret_text)))

            first_event = False

        lines = []
        for string in ordered_strings:
            content = "".join(buffers[string])

            if self.bar_edges:
                content = "|" + content + "|"

            if self.show_labels:
                label = self._string_label(string)
                line = (
                    f"{label}|{content[1:]}" if self.bar_edges else f"{label}|{content}"
                )
            else:
                line = content

            lines.append(line)

        return "\n".join(lines)

    def _validate_event(self, event: RealizedEvent):
        if not event.notes:
            raise TabRenderError("Cannot render an empty event")

        for note in event.notes:
            if not self.fretboard.is_valid_position(note.position):
                raise TabRenderError(
                    f"Invalid position: string {note.position.string}, fret {note.position.fret}"
                )

    def _string_label(self, string: int) -> str:
        """
        Standard labels for standard guitar / 4-string bass.
        Falls back to numeric labels otherwise.
        """
        tuning_numbers = [spec.number for spec in self.fretboard.tuning.strings]

        if len(tuning_numbers) == 6:
            mapping = {
                1: "e",
                2: "B",
                3: "G",
                4: "D",
                5: "A",
                6: "E",
            }
            return mapping.get(string, str(string))

        if len(tuning_numbers) == 4:
            mapping = {
                1: "G",
                2: "D",
                3: "A",
                4: "E",
            }
            return mapping.get(string, str(string))

        return str(string)

    def render_preserving_columns(self, events: list[RealizedEvent]) -> str:
        """
        Render events using at_column as a preferred start position.
        Later events are shifted right if needed to avoid overlap.
        """
        ordered_strings = [spec.number for spec in self.fretboard.tuning.strings]
        buffers = {string: [] for string in ordered_strings}

        current_cursor = 0

        for event in sorted(events, key=lambda e: e.at_column):
            self._validate_event(event)

            notes_by_string = {}
            for note in event.notes:
                string = note.position.string
                if string in notes_by_string:
                    raise TabRenderError(
                        f"Multiple notes on the same string in one event: string {string}"
                    )
                notes_by_string[string] = note

            event_width = max(len(str(note.position.fret)) for note in event.notes)
            start_col = max(event.at_column, current_cursor)

            for string in ordered_strings:
                missing = start_col - len(buffers[string])
                if missing > 0:
                    buffers[string].extend("-" * missing)

            for string in ordered_strings:
                note = notes_by_string.get(string)
                if note is None:
                    buffers[string].extend("-" * event_width)
                else:
                    fret_text = str(note.position.fret)
                    buffers[string].extend(fret_text)
                    buffers[string].extend("-" * (event_width - len(fret_text)))

            current_cursor = start_col + event_width

        lines = []
        for string in ordered_strings:
            content = "".join(buffers[string])
            content = "|" + content + "|"

            if self.show_labels:
                label = self._string_label(string)
                line = f"{label}|{content[1:]}"
            else:
                line = content

            lines.append(line)

        return "\n".join(lines)


class RenderedEventSegment:
    def __init__(self, width: int, by_string: dict[int, str]):
        self.width = width
        self.by_string = by_string
