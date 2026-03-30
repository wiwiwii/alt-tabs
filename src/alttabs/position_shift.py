from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import inf

from alttabs.errors import InvalidAnchorError, PolyphonyNotSupportedError, RangeNotPlayableError
from alttabs.instrument import FretBoard, FretPosition, PlayedNote
from alttabs.score import RealizedEvent


class PositionShiftError(Exception):
    pass


class PositionBias(str, Enum):
    DOWN = "down"
    CENTERED = "centered"
    UP = "up"


@dataclass(frozen=True)
class RetabPreferences:
    """
    Preferences for re-choosing fretboard positions for a monophonic line.

    anchor_string / anchor_fret:
        The reference point the phrase should orbit around.

    max_fret_deviation:
        Preferred hard window around anchor_fret. If no candidate survives this
        filter for a note, the solver falls back to all playable candidates.

    prefer_open_strings:
        If None, follow the bias defaults.
        If True, explicitly reward open strings.
        If False, explicitly penalize open strings.

    Weights:
        Tweak these later once you hear / inspect results.
    """

    anchor_string: int
    anchor_fret: int
    bias: PositionBias = PositionBias.CENTERED
    max_fret_deviation: int = 6
    prefer_open_strings: bool | None = None

    anchor_distance_weight: float = 2.0
    movement_fret_weight: float = 1.5
    movement_string_weight: float = 2.0
    direction_bias_weight: float = 2.0
    open_string_weight: float = 1.0


@dataclass(frozen=True)
class Candidate:
    event_index: int
    position: FretPosition
    pitch_value: int


def shift_monophonic_events(
    events: list[RealizedEvent],
    fretboard: FretBoard,
    preferences: RetabPreferences,
) -> list[RealizedEvent]:
    """
    Re-fret a monophonic sequence while preserving pitches and event placement.

    Input:
        events: list[RealizedEvent]
            Each event must contain exactly one note.
        fretboard:
            Target instrument.
        preferences:
            Anchor + bias configuration.

    Output:
        New RealizedEvent list with the same measure_index / at_column and the
        same pitches, but newly chosen string/fret positions.
    """
    if not events:
        return []

    _validate_monophonic(events)
    _validate_anchor(fretboard, preferences)

    candidates_by_event = [
        _candidates_for_event(event, idx, fretboard, preferences)
        for idx, event in enumerate(events)
    ]

    best_path = _solve_best_path(candidates_by_event, preferences)

    shifted_events: list[RealizedEvent] = []
    for event, candidate in zip(events, best_path):
        shifted_events.append(
            RealizedEvent(
                measure_index=event.measure_index,
                at_column=event.at_column,
                notes=[
                    PlayedNote(
                        pitch=event.notes[0].pitch,
                        position=candidate.position,
                    )
                ],
                source_event=getattr(event, "source_event", None),
            )
        )

    return shifted_events


def _validate_monophonic(events: list[RealizedEvent]) -> None:
    for idx, event in enumerate(events):
        if len(event.notes) != 1:
            raise PolyphonyNotSupportedError(
                f"Event {idx} is not monophonic: expected 1 note, got {len(event.notes)}"
            )


def _validate_anchor(fretboard: FretBoard, preferences: RetabPreferences) -> None:
    anchor = FretPosition(preferences.anchor_string, preferences.anchor_fret)
    if not fretboard.is_valid_position(anchor):
        raise InvalidAnchorError(
            f"Invalid anchor position: string {anchor.string}, fret {anchor.fret}"
        )


def _candidates_for_event(
    event: RealizedEvent,
    event_index: int,
    fretboard: FretBoard,
    preferences: RetabPreferences,
) -> list[Candidate]:
    pitch = event.notes[0].pitch
    positions = fretboard.positions_for(pitch)

    if not positions:
        raise RangeNotPlayableError(
            f"No playable positions found for pitch {pitch.value} in event {event_index}"
        )

    preferred_positions = [
        pos
        for pos in positions
        if abs(pos.fret - preferences.anchor_fret) <= preferences.max_fret_deviation
    ]

    chosen_positions = preferred_positions if preferred_positions else positions

    return [
        Candidate(
            event_index=event_index,
            position=pos,
            pitch_value=pitch.value,
        )
        for pos in chosen_positions
    ]


def _solve_best_path(
    candidates_by_event: list[list[Candidate]],
    preferences: RetabPreferences,
) -> list[Candidate]:
    dp: list[list[float]] = []
    backpointers: list[list[int | None]] = []

    first_row: list[float] = []
    first_back: list[int | None] = []
    for candidate in candidates_by_event[0]:
        first_row.append(_initial_cost(candidate, preferences))
        first_back.append(None)

    dp.append(first_row)
    backpointers.append(first_back)

    for event_index in range(1, len(candidates_by_event)):
        row_costs: list[float] = []
        row_back: list[int | None] = []

        for current_idx, current in enumerate(candidates_by_event[event_index]):
            best_cost = inf
            best_prev_idx: int | None = None

            for prev_idx, prev in enumerate(candidates_by_event[event_index - 1]):
                cost = dp[event_index - 1][prev_idx] + _transition_cost(
                    prev, current, preferences
                )
                if cost < best_cost:
                    best_cost = cost
                    best_prev_idx = prev_idx

            row_costs.append(best_cost)
            row_back.append(best_prev_idx)

        dp.append(row_costs)
        backpointers.append(row_back)

    final_row = dp[-1]
    final_idx = min(range(len(final_row)), key=lambda i: final_row[i])

    path: list[Candidate] = []
    current_idx: int | None = final_idx

    for event_index in range(len(candidates_by_event) - 1, -1, -1):
        assert current_idx is not None
        path.append(candidates_by_event[event_index][current_idx])
        current_idx = backpointers[event_index][current_idx]

    path.reverse()
    return path


def _initial_cost(candidate: Candidate, preferences: RetabPreferences) -> float:
    return (
        preferences.anchor_distance_weight
        * abs(candidate.position.fret - preferences.anchor_fret)
        + preferences.direction_bias_weight
        * _direction_penalty(candidate.position.string, preferences)
        + preferences.open_string_weight
        * _open_string_penalty(candidate.position.fret, preferences)
    )


def _transition_cost(
    previous: Candidate,
    current: Candidate,
    preferences: RetabPreferences,
) -> float:
    return (
        preferences.anchor_distance_weight
        * abs(current.position.fret - preferences.anchor_fret)
        + preferences.movement_fret_weight
        * abs(current.position.fret - previous.position.fret)
        + preferences.movement_string_weight
        * abs(current.position.string - previous.position.string)
        + preferences.direction_bias_weight
        * _direction_penalty(current.position.string, preferences)
        + preferences.open_string_weight
        * _open_string_penalty(current.position.fret, preferences)
    )


def _direction_penalty(string_number: int, preferences: RetabPreferences) -> float:
    """
    Lower penalty is better.

    DOWN:
        Prefer larger string numbers (thicker / lower strings).
    UP:
        Prefer smaller string numbers (thinner / higher strings).
    CENTERED:
        Prefer strings near anchor_string.
    """
    if preferences.bias == PositionBias.DOWN:
        return (
            float(preferences.anchor_string - string_number)
            if string_number < preferences.anchor_string
            else 0.0
        )

    if preferences.bias == PositionBias.UP:
        return (
            float(string_number - preferences.anchor_string)
            if string_number > preferences.anchor_string
            else 0.0
        )

    return float(abs(string_number - preferences.anchor_string))


def _open_string_penalty(fret: int, preferences: RetabPreferences) -> float:
    if fret != 0:
        return 0.0

    if preferences.prefer_open_strings is True:
        return -1.0

    if preferences.prefer_open_strings is False:
        return 1.0

    if preferences.bias == PositionBias.UP:
        return -1.0

    if preferences.bias == PositionBias.DOWN:
        return 1.0

    return 0.5
