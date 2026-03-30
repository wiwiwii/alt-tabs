from alttabs.instrument import FretBoard, PlayedNote


class TabParseError(Exception):
    pass


class TabStringLine:
    """
    One ASCII tab line for one string, split into measures.

    Example:
        e|--3--10--|--0--|
    becomes:
        measures = ["--3--10--", "--0--"]
    """

    def __init__(self, string: int, measures: list[str], raw_label: str | None = None):
        self.string = string
        self.measures = measures
        self.raw_label = raw_label


class TabEvent:
    """
    Notes starting at one source column inside one measure.

    measure_index:
        Zero-based measure index.
    at_column:
        Character index inside that measure.
    notes:
        Played notes starting at that measure-local column.
    """

    def __init__(self, measure_index: int, at_column: int, notes: list[PlayedNote]):
        self.measure_index = measure_index
        self.at_column = at_column
        self.notes = notes


class ParsedTab:
    """
    Full parsed tab block.

    string_lines:
        Ordered lines as given in the input.
    events:
        Musical events grouped by measure and onset column.
    measure_count:
        Number of measures in the tab.
    measure_widths:
        Width of each measure content, excluding barlines.
    """

    def __init__(
        self,
        string_lines: list[TabStringLine],
        events: list[TabEvent],
        measure_count: int,
        measure_widths: list[int],
    ):
        self.string_lines = string_lines
        self.events = events
        self.measure_count = measure_count
        self.measure_widths = measure_widths


class TabParser:
    """
    Narrow ASCII tab parser.

    Supported:
    - lines like e|--0--3--|--2--|
    - lines like |--0--3--|--2--|
    - multi-digit frets
    - chords by same-column onset
    - measure-aware parsing

    Not supported yet:
    - h / p / / / \\ / b / r / x / ~ / parentheses
    - rhythmic inference
    """

    def __init__(self, fretboard: FretBoard):
        self.fretboard = fretboard

    def parse(self, text: str) -> ParsedTab:
        raw_lines = [line.rstrip() for line in text.splitlines() if line.strip()]
        if not raw_lines:
            raise TabParseError("Empty tab")

        string_lines = self._parse_string_lines(raw_lines)
        self._validate_measure_structure(string_lines)
        events = self._extract_events(string_lines)

        measure_count = len(string_lines[0].measures)
        measure_widths = [len(measure) for measure in string_lines[0].measures]

        return ParsedTab(
            string_lines=string_lines,
            events=events,
            measure_count=measure_count,
            measure_widths=measure_widths,
        )

    def _parse_string_lines(self, raw_lines: list[str]) -> list[TabStringLine]:
        parsed = []
        expected_strings = [spec.number for spec in self.fretboard.tuning.strings]

        if len(raw_lines) != len(expected_strings):
            raise TabParseError(
                f"Expected {len(expected_strings)} lines for this instrument, got {len(raw_lines)}"
            )

        for idx, raw in enumerate(raw_lines):
            string_number, label, content = self._split_label_and_content(
                raw, fallback_index=idx
            )
            measures = self._split_measures(content)
            parsed.append(
                TabStringLine(
                    string=string_number,
                    measures=measures,
                    raw_label=label,
                )
            )

        parsed_numbers = [line.string for line in parsed]
        if sorted(parsed_numbers) != sorted(expected_strings):
            raise TabParseError(
                f"Parsed string numbers {parsed_numbers} do not match instrument strings {expected_strings}"
            )

        return parsed

    def _split_label_and_content(self, raw: str, fallback_index: int):
        """
        Accept:
            e|--0--|--3--|
            B|--1--|--3--|
            |--0--|--3--|

        If there is no label, map by physical line order to the fretboard's tuning order.
        """
        if "|" not in raw:
            raise TabParseError(f"Missing '|' separator in line: {raw}")

        before_bar, after_bar = raw.split("|", 1)
        label = before_bar.strip()

        if label:
            string_number = self._string_number_from_label(label, raw)
            return string_number, label, "|" + after_bar

        tuning_order = [spec.number for spec in self.fretboard.tuning.strings]
        string_number = tuning_order[fallback_index]
        return string_number, None, "|" + after_bar

    def _split_measures(self, content: str) -> list[str]:
        """
        Split a content string like:
            |--3--|--0--|
        into:
            ["--3--", "--0--"]
        """
        if not content.startswith("|"):
            raise TabParseError(f"Measure content must start with '|': {content}")
        if not content.endswith("|"):
            raise TabParseError(f"Measure content must end with '|': {content}")

        parts = content.split("|")
        # "|--3--|--0--|" -> ["", "--3--", "--0--", ""]
        if parts[0] != "" or parts[-1] != "":
            raise TabParseError(f"Malformed measure bars: {content}")

        measures = parts[1:-1]
        if not measures:
            raise TabParseError("Tab must contain at least one measure")

        return measures

    def _validate_measure_structure(self, string_lines: list[TabStringLine]):
        """
        All strings must have:
        - the same number of measures
        - the same width for corresponding measures
        """
        expected_count = len(string_lines[0].measures)
        expected_widths = [len(measure) for measure in string_lines[0].measures]

        for line in string_lines:
            if len(line.measures) != expected_count:
                raise TabParseError("All strings must have the same number of measures")

            widths = [len(measure) for measure in line.measures]
            if widths != expected_widths:
                raise TabParseError(
                    "Corresponding measures must have identical widths across strings"
                )

    def _string_number_from_label(self, label: str, raw: str) -> int:
        """
        Guitar:
            e B G D A E
        Bass:
            G D A E

        Ambiguity: uppercase E appears on guitar low E and bass low E.
        Resolve using instrument string count.
        """
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

        if label.isdigit():
            numeric = int(label)
            if numeric in tuning_numbers:
                return numeric
            raise TabParseError(f"Label '{label}' not valid for this instrument: {raw}")

        raise TabParseError(
            f"Unsupported or ambiguous string label '{label}' in line: {raw}"
        )

    def _extract_events(self, string_lines: list[TabStringLine]) -> list[TabEvent]:
        """
        Scan all measures on all lines. Whenever a digit starts at column c on a string,
        parse the full integer fret number on that line, then create/group an event at:
            (measure_index, column)
        """
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
