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
    One contiguous tab block before parsing.

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
    - groups string lines into blocks sized for the selected instrument
    - attaches a following `xN` repeat marker to the preceding block
    - sanitizes unsupported symbols for the current narrow TabParser
    """
    parser = TabParser(fretboard)
    expected_string_count = len(fretboard.tuning.strings)
    raw_blocks = split_raw_tab_blocks(text, expected_string_count)

    parsed_blocks: list[ParsedTabBlock] = []
    for raw_block in raw_blocks:
        parsed = parser.parse(raw_block.sanitized_text)
        parsed_blocks.append(ParsedTabBlock(raw_block=raw_block, parsed_tab=parsed))

    return parsed_blocks


def split_raw_tab_blocks(text: str, expected_string_count: int) -> list[RawTabBlock]:
    """
    Split a large tab dump into instrument-sized blocks, optionally followed by `xN`.
    """
    raw_lines = text.splitlines()
    i = 0
    blocks: list[RawTabBlock] = []

    while i < len(raw_lines):
        while i < len(raw_lines) and not raw_lines[i].strip():
            i += 1

        if i >= len(raw_lines):
            break

        if not is_tab_line(raw_lines[i]):
            i += 1
            continue

        block_lines: list[str] = []
        start_i = i

        while i < len(raw_lines) and len(block_lines) < expected_string_count:
            line = raw_lines[i]
            if is_tab_line(line):
                block_lines.append(line.rstrip())
            i += 1

        if not block_lines:
            continue

        if len(block_lines) != expected_string_count:
            raise InputTabError(
                "Incomplete tab block starting near line "
                f"{start_i + 1}: expected {expected_string_count} non-empty lines, "
                f"got {len(block_lines)}"
            )

        repeat = 1
        for line in block_lines:
            inline_repeat = extract_repeat(line)
            if inline_repeat is not None:
                repeat = inline_repeat

        scan_i = i
        non_tab_seen = 0
        while scan_i < len(raw_lines) and non_tab_seen <= 2:
            candidate = raw_lines[scan_i].strip()
            if not candidate:
                scan_i += 1
                continue

            repeat_match = extract_repeat(candidate)
            if repeat_match is not None:
                repeat = repeat_match
                if scan_i == i:
                    i += 1
                break

            if is_tab_line(raw_lines[scan_i]):
                break

            non_tab_seen += 1
            scan_i += 1

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


def is_tab_line(line: str) -> bool:
    if "|" not in line:
        return False
    prefix, _ = line.split("|", 1)
    label = prefix.strip()
    if not label:
        return True
    return label in {"e", "B", "G", "D", "A", "E"} or label.isdigit()


def is_repeat_line(line: str) -> bool:
    return extract_repeat(line) is not None


def is_comment_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    return (not is_tab_line(stripped)) and (not is_repeat_line(stripped))


def extract_comment_lines(text: str) -> list[str]:
    comments: list[str] = []
    for line in text.splitlines():
        if is_comment_line(line):
            comments.append(line.strip())
    return comments


def extract_repeat(line: str) -> int | None:
    if "|" in line:
        line = line[line.rfind("|") + 1 :].strip()

    patterns = (
        r"^x(\d+)$",
        r"^\(x(\d+)\)$",
        r"^repeat\s*x(\d+)$",
    )
    for pattern in patterns:
        match = re.match(pattern, line, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


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

    last_bar = line.rfind("|")
    core = line[: last_bar + 1]

    before_bar, after_bar = core.split("|", 1)
    label = before_bar
    content = "|" + after_bar

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
