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
    def __init__(
        self,
        measure_index: int,
        at_column: int,
        notes: list[PlayedNote],
        source_event=None,
    ):
        self.measure_index = measure_index
        self.at_column = at_column
        self.notes = notes
        self.source_event = source_event


class TabRenderError(Exception):
    pass


class TabRenderer:
    def __init__(self, fretboard: FretBoard, show_labels: bool = True):
        self.fretboard = fretboard
        self.show_labels = show_labels

    def render(
        self,
        events: list[RealizedEvent],
        measures_per_line: int = 2,
    ) -> str:
        ordered_strings = [spec.number for spec in self.fretboard.tuning.strings]

        if not events:
            return self._render_empty(ordered_strings)

        for event in events:
            self._validate_event(event)

        measure_count = max(event.measure_index for event in events) + 1

        measures_by_index = {i: [] for i in range(measure_count)}
        for event in events:
            measures_by_index[event.measure_index].append(event)

        rendered_measures = []
        for measure_index in range(measure_count):
            rendered_measures.append(
                self._render_single_measure(
                    ordered_strings,
                    sorted(measures_by_index[measure_index], key=lambda e: e.at_column),
                )
            )

        chunks = [
            rendered_measures[i : i + measures_per_line]
            for i in range(0, len(rendered_measures), measures_per_line)
        ]

        lines: list[str] = []

        for chunk_idx, chunk in enumerate(chunks):
            for string in ordered_strings:
                content = "|" + "|".join(measure[string] for measure in chunk) + "|"

                if self.show_labels:
                    line = f"{self._string_label(string)}{content}"
                else:
                    line = content

                lines.append(line)

            if chunk_idx < len(chunks) - 1:
                lines.append("")

        return "\n".join(lines)

    def _render_single_measure(
        self, ordered_strings: list[int], events: list[RealizedEvent]
    ) -> dict[int, str]:
        if not events:
            return {string: "-" for string in ordered_strings}

        current_cursor = 1
        placements = []

        for event in events:
            notes_by_string = {}
            for note in event.notes:
                string = note.position.string
                if string in notes_by_string:
                    raise TabRenderError(
                        f"Multiple notes on same string in event: string {string}"
                    )
                notes_by_string[string] = note

            width = max(len(str(note.position.fret)) for note in event.notes)

            start = max(1, event.at_column, current_cursor)
            placements.append((start, width, notes_by_string))
            current_cursor = start + width + 1

        measure_width = max(start + width + 1 for start, width, _ in placements)

        buffers = {string: ["-"] * measure_width for string in ordered_strings}

        for start, width, notes_by_string in placements:
            for string in ordered_strings:
                note = notes_by_string.get(string)
                if note is None:
                    continue

                fret_text = str(note.position.fret)
                for i, ch in enumerate(fret_text):
                    buffers[string][start + i] = ch

        for string in ordered_strings:
            buffers[string][0] = "-"
            buffers[string][-1] = "-"

        return {string: "".join(buffers[string]) for string in ordered_strings}

    def _validate_event(self, event: RealizedEvent):
        if not event.notes:
            raise TabRenderError("Cannot render empty event")

        for note in event.notes:
            if not self.fretboard.is_valid_position(note.position):
                raise TabRenderError(
                    f"Invalid position: string {note.position.string}, fret {note.position.fret}"
                )

    def _render_empty(self, ordered_strings: list[int]) -> str:
        lines = []
        for string in ordered_strings:
            content = "|-|"
            if self.show_labels:
                lines.append(f"{self._string_label(string)}{content}")
            else:
                lines.append(content)
        return "\n".join(lines)

    def _string_label(self, string: int) -> str:
        tuning_numbers = [spec.number for spec in self.fretboard.tuning.strings]

        if len(tuning_numbers) == 6:
            mapping = {1: "e", 2: "B", 3: "G", 4: "D", 5: "A", 6: "E"}
            return mapping.get(string, str(string))

        if len(tuning_numbers) == 4:
            mapping = {1: "G", 2: "D", 3: "A", 4: "E"}
            return mapping.get(string, str(string))

        return str(string)
