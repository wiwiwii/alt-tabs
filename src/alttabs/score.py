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


class TabParseError(Exception):
    pass


class TabRenderError(Exception):
    pass


class TabStringLine:
    def __init__(self, string: int, measures: list[str], raw_label: str | None = None):
        self.string = string
        self.measures = measures
        self.raw_label = raw_label


class ParsedTab:
    def __init__(
        self,
        string_lines: list[TabStringLine],
        events: list[TabEvent],
        measure_count: int,
    ):
        self.string_lines = string_lines
        self.events = events
        self.measure_count = measure_count


class TabParser:
    def __init__(self, fretboard: FretBoard):
        self.fretboard = fretboard

    def parse(self, text: str) -> ParsedTab:
        raw_lines = [line.rstrip() for line in text.splitlines() if line.strip()]
        if not raw_lines:
            raise TabParseError("Empty tab")

        string_lines = self._parse_string_lines(raw_lines)
        self._validate_measure_structure(string_lines)
        events = self._extract_events(string_lines)

        return ParsedTab(
            string_lines=string_lines,
            events=events,
            measure_count=len(string_lines[0].measures),
        )

    def _parse_string_lines(self, raw_lines: list[str]) -> list[TabStringLine]:
        expected_strings = [spec.number for spec in self.fretboard.tuning.strings]
        if len(raw_lines) != len(expected_strings):
            raise TabParseError(
                f"Expected {len(expected_strings)} lines for this instrument, got {len(raw_lines)}"
            )

        parsed = []
        for idx, raw in enumerate(raw_lines):
            string_number, label, content = self._split_label_and_content(raw, idx)
            measures = self._split_measures(content)
            parsed.append(
                TabStringLine(string=string_number, measures=measures, raw_label=label)
            )

        parsed_numbers = [line.string for line in parsed]
        if sorted(parsed_numbers) != sorted(expected_strings):
            raise TabParseError(
                f"Parsed string numbers {parsed_numbers} do not match instrument strings {expected_strings}"
            )

        return parsed

    def _split_label_and_content(self, raw: str, fallback_index: int):
        if "|" not in raw:
            raise TabParseError(f"Missing '|' separator in line: {raw}")

        before_bar, after_bar = raw.split("|", 1)
        label = before_bar.strip()

        if label:
            string_number = self._string_number_from_label(label, raw)
            return string_number, label, "|" + after_bar

        tuning_order = [spec.number for spec in self.fretboard.tuning.strings]
        return tuning_order[fallback_index], None, "|" + after_bar

    def _split_measures(self, content: str) -> list[str]:
        if not content.startswith("|"):
            raise TabParseError(f"Measure content must start with '|': {content}")
        if not content.endswith("|"):
            raise TabParseError(f"Measure content must end with '|': {content}")

        parts = content.split("|")
        # Example: "|--3--|--0--|" -> ["", "--3--", "--0--", ""]
        if parts[0] != "" or parts[-1] != "":
            raise TabParseError(f"Malformed measure bars: {content}")

        measures = parts[1:-1]
        if not measures:
            raise TabParseError("Tab must contain at least one measure")

        return measures

    def _validate_measure_structure(self, string_lines: list[TabStringLine]):
        expected_count = len(string_lines[0].measures)
        expected_widths = [len(m) for m in string_lines[0].measures]

        for line in string_lines:
            if len(line.measures) != expected_count:
                raise TabParseError("All strings must have the same number of measures")

            widths = [len(m) for m in line.measures]
            if widths != expected_widths:
                raise TabParseError(
                    "Corresponding measures must have identical widths across strings"
                )

    def _extract_events(self, string_lines: list[TabStringLine]) -> list[TabEvent]:
        events_by_key: dict[tuple[int, int], list[PlayedNote]] = {}

        for line in string_lines:
            for measure_index, measure in enumerate(line.measures):
                col = 0
                while col < len(measure):
                    ch = measure[col]

                    if ch.isdigit():
                        if col > 0 and measure[col - 1].isdigit():
                            col += 1
                            continue

                        start = col
                        end = col
                        while end < len(measure) and measure[end].isdigit():
                            end += 1

                        fret = int(measure[start:end])
                        played = self.fretboard.note_at(line.string, fret)

                        key = (measure_index, start)
                        if key not in events_by_key:
                            events_by_key[key] = []
                        events_by_key[key].append(played)

                        col = end
                        continue

                    col += 1

        keys = sorted(events_by_key.keys())
        return [
            TabEvent(
                measure_index=measure_index,
                at_column=at_column,
                notes=events_by_key[(measure_index, at_column)],
            )
            for measure_index, at_column in keys
        ]

    def _string_number_from_label(self, label: str, raw: str) -> int:
        tuning_numbers = [spec.number for spec in self.fretboard.tuning.strings]

        if label == "e":
            if 1 in tuning_numbers:
                return 1
            raise TabParseError(f"Label '{label}' not valid for this instrument: {raw}")

        if label in ("B", "G", "D", "A"):
            mapping = {"B": 2, "G": 3, "D": 4, "A": 5}
            string_number = mapping[label]
            if string_number not in tuning_numbers:
                raise TabParseError(
                    f"Label '{label}' not valid for this instrument: {raw}"
                )
            return string_number

        if label == "E":
            if len(tuning_numbers) == 6:
                return 6
            if len(tuning_numbers) == 4:
                return 4

        raise TabParseError(
            f"Unsupported or ambiguous string label '{label}' in line: {raw}"
        )


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
                parts = []
                for measure in chunk:
                    parts.append("|" + measure[string] + "|")

                content = "".join(parts)

                if self.show_labels:
                    line = f"{self._string_label(string)}{content}"
                else:
                    line = content

                lines.append(line)

            # blank line between systems (but not after last)
            if chunk_idx < len(chunks) - 1:
                lines.append("")

        return "\n".join(lines)

    def _render_single_measure(
        self, ordered_strings: list[int], events: list[RealizedEvent]
    ) -> dict[int, str]:
        if not events:
            # Smallest valid empty measure: |-|
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
            current_cursor = start + width

        measure_width = max(start + width + 1 for start, width, _ in placements)
        # +1 ensures at least one trailing dash before closing bar

        buffers = {string: ["-"] * measure_width for string in ordered_strings}

        for start, width, notes_by_string in placements:
            for string in ordered_strings:
                note = notes_by_string.get(string)
                if note is None:
                    continue

                fret_text = str(note.position.fret)
                for i, ch in enumerate(fret_text):
                    buffers[string][start + i] = ch

        # First and last chars remain '-'
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


class RenderedEventSegment:
    def __init__(self, width: int, by_string: dict[int, str]):
        self.width = width
        self.by_string = by_string
