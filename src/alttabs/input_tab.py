from __future__ import annotations

import re
from dataclasses import dataclass

from alttabs.instrument import FretBoard
from alttabs.score import RealizedEvent
from alttabs.tab import ParsedTab, TabParser


class InputTabError(Exception):
    pass


@dataclass(frozen=True)
class RawTabBlock:
    """
    One contiguous 6-line tab block before parsing.

    repeat:
        Number of times the block should be repeated.
    original_text:
        Raw original block text.
    sanitized_text:
        Text after lightweight sanitization for TabParser.
    """

    lines: list[str]
    repeat: int
    original_text: str
    sanitized_text: str


@dataclass(frozen=True)
class ParsedTabBlock:
    """
    Parsed result for one block, before flattening.
    """

    raw_block: RawTabBlock
    parsed_tab: ParsedTab


def load_tab_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def parse_tab_file(path: str, fretboard: FretBoard) -> list[ParsedTabBlock]:
    text = load_tab_file(path)
    return parse_tab_text(text, fretboard)


def parse_tab_text(text: str, fretboard: FretBoard) -> list[ParsedTabBlock]:
    """
    Parse a large raw tab text into independently parsed blocks.

    This function:
    - groups 6 string lines into blocks
    - attaches a following `xN` repeat marker to the preceding block
    - sanitizes unsupported symbols for the current narrow TabParser
    """
    parser = TabParser(fretboard)
    raw_blocks = split_raw_tab_blocks(text)

    parsed_blocks: list[ParsedTabBlock] = []
    for raw_block in raw_blocks:
        parsed = parser.parse(raw_block.sanitized_text)
        parsed_blocks.append(ParsedTabBlock(raw_block=raw_block, parsed_tab=parsed))

    return parsed_blocks


def split_raw_tab_blocks(text: str) -> list[RawTabBlock]:
    """
    Split a large tab dump into 6-line blocks, optionally followed by `xN`.

    Expected shape:
        [6 tab lines]
        [blank lines optional]
        x2           # optional repeat marker for previous block
        [blank lines optional]
        [next 6 tab lines]
    """
    raw_lines = text.splitlines()
    i = 0
    blocks: list[RawTabBlock] = []

    while i < len(raw_lines):
        # Skip blank lines between blocks
        while i < len(raw_lines) and not raw_lines[i].strip():
            i += 1

        if i >= len(raw_lines):
            break

        block_lines: list[str] = []
        start_i = i

        while i < len(raw_lines) and len(block_lines) < 6:
            line = raw_lines[i]
            if line.strip():
                block_lines.append(line.rstrip())
            i += 1

        if not block_lines:
            continue

        if len(block_lines) != 6:
            raise InputTabError(
                f"Incomplete tab block starting near line {start_i + 1}: expected 6 non-empty lines, got {len(block_lines)}"
            )

        repeat = 1

        # Skip blanks after the 6 lines
        while i < len(raw_lines) and not raw_lines[i].strip():
            i += 1

        # Optional repeat marker like x2
        if i < len(raw_lines):
            match = re.fullmatch(r"x(\d+)", raw_lines[i].strip(), flags=re.IGNORECASE)
            if match:
                repeat = int(match.group(1))
                i += 1

        original_text = "\n".join(block_lines)
        sanitized_lines = [sanitize_tab_line(line) for line in block_lines]
        sanitized_text = "\n".join(sanitized_lines)

        blocks.append(
            RawTabBlock(
                lines=block_lines,
                repeat=repeat,
                original_text=original_text,
                sanitized_text=sanitized_text,
            )
        )

    return blocks


def sanitize_tab_line(line: str) -> str:
    """
    Sanitize one tab line so the current narrow TabParser can ingest it.

    Current strategy:
    - preserve letters at the beginning as string labels
    - preserve bars, dashes, digits
    - convert unsupported ornaments (~ h p / \\ b r x parentheses etc.) to '-'

    This is intentionally lossy. It preserves note onsets well enough for the
    current parser, but not technique semantics.
    """
    if "|" not in line:
        raise InputTabError(f"Invalid tab line without '|': {line}")

    before_bar, after_bar = line.split("|", 1)
    label = before_bar
    content = "|" + after_bar

    # Replace unsupported symbols with dashes, but keep:
    # - digits
    # - bars
    # - dashes
    #
    # Everything else in the content area becomes '-'.
    sanitized_content_chars: list[str] = []
    for ch in content:
        if ch.isdigit() or ch in {"|", "-"}:
            sanitized_content_chars.append(ch)
        else:
            sanitized_content_chars.append("-")

    return f"{label}{''.join(sanitized_content_chars)}"


def to_realized_events(parsed_blocks: list[ParsedTabBlock]) -> list[RealizedEvent]:
    """
    Flatten parsed blocks into one event stream of RealizedEvents.

    Measure indices are offset across blocks, and repeats are expanded.
    """
    realized: list[RealizedEvent] = []
    measure_offset = 0

    for parsed_block in parsed_blocks:
        parsed = parsed_block.parsed_tab

        for _ in range(parsed_block.raw_block.repeat):
            for event in parsed.events:
                realized.append(
                    RealizedEvent(
                        measure_index=measure_offset + event.measure_index,
                        at_column=event.at_column,
                        notes=list(event.notes),
                    )
                )
            measure_offset += parsed.measure_count

    return realized


def ingest_tab_text_to_events(text: str, fretboard: FretBoard) -> list[RealizedEvent]:
    """
    Convenience function:
        big raw text -> parsed blocks -> flattened realized events
    """
    parsed_blocks = parse_tab_text(text, fretboard)
    return to_realized_events(parsed_blocks)


def ingest_tab_file_to_events(path: str, fretboard: FretBoard) -> list[RealizedEvent]:
    """
    Convenience function:
        file path -> big raw text -> parsed blocks -> flattened realized events
    """
    parsed_blocks = parse_tab_file(path, fretboard)
    return to_realized_events(parsed_blocks)


def describe_blocks(parsed_blocks: list[ParsedTabBlock]) -> None:
    for i, block in enumerate(parsed_blocks):
        print(
            f"[{i}] repeat={block.raw_block.repeat} "
            f"measures={block.parsed_tab.measure_count} "
            f"events={len(block.parsed_tab.events)}"
        )
