# Pre-Implementation Review Findings

Below are the issues that stand out immediately and are likely to cause bugs, regressions, or maintenance pain. Each item is formatted as a task stub for direct implementation tracking.

<task_stub>
P0 | Remove duplicate parsing models across `score.py` and `tab.py`
Why: `src/alttabs/score.py` redefines `TabParser`, `ParsedTab`, `TabStringLine`, and `TabParseError` that already exist in `src/alttabs/tab.py`. This creates two competing sources of truth for core parsing behavior and guarantees drift.
Evidence: `src/alttabs/score.py` lines 42-233 duplicate parser domain classes while `src/alttabs/tab.py` lines 4-236 defines the canonical parser. Downstream code imports parser errors from `alttabs.tab` but render errors from `alttabs.score`, proving split ownership.
Fix: Keep parser domain exclusively in `tab.py`; keep rendering/event domain in `score.py`. Delete duplicated parser classes from `score.py` and update imports.
Acceptance: There is exactly one `TabParser` implementation in the codebase and all parser-related imports reference `alttabs.tab`.
</task_stub>

<task_stub>
P0 | Standardize imports (`alttabs.*` vs `src.alttabs.*`)
Why: Mixed absolute package roots are used in runtime files. This is fragile and environment-dependent (editable install vs direct script execution), and can break imports in production or CI.
Evidence: `app.py` uses both `from alttabs...` (lines 5-10) and `from src.alttabs...` (lines 11-12). `marseillaise_shift.py` also imports from `src.alttabs...` (line 8).
Fix: Choose one package root (recommended: `alttabs.*`) and apply consistently; ensure entrypoints run with the same module resolution assumptions.
Acceptance: No `from src.alttabs` imports remain in runtime code; app launches consistently with documented command.
</task_stub>

<task_stub>
P1 | Harden block splitting to ignore non-tab lines/comments
Why: `split_raw_tab_blocks` currently consumes the next N non-empty lines as tab content. Any comment/header line (`[Chorus]`, `1st verse`) will be interpreted as a tab line and either fail parsing or corrupt block boundaries.
Evidence: In `src/alttabs/input_tab.py`, lines 93-97 append every non-empty line into `block_lines` until expected count is reached.
Fix: Add line classification (tab/comment/repeat/blank/unknown). Build blocks only from tab lines and preserve comments separately.
Acceptance: Mixed inputs with comments and tabs parse without block-size errors.
</task_stub>

<task_stub>
P1 | Expand repeat marker parsing beyond strict standalone next-line `xN`
Why: Current repeat handling only catches `xN` if it appears immediately after a block and as the full line. Common real tabs place repeat inline (`|...| x2`) or with variants (`(x2)`, `repeat x2`).
Evidence: `src/alttabs/input_tab.py` lines 114-118 use `re.fullmatch(r"x(\d+)", raw_lines[i].strip())` on a single following line only.
Fix: Add robust repeat extraction with accepted variants and nearest-block attachment rules.
Acceptance: Repeats are correctly detected for standalone, inline, and nearby annotation forms.
</task_stub>

<task_stub>
P1 | Avoid swallowing unexpected exceptions in Streamlit compute path
Why: A broad `except Exception` hides root causes and slows debugging. It also turns programming bugs into generic UX messages, making incident diagnosis difficult.
Evidence: `app.py` lines 213-217 catch all exceptions and replace with a generic string.
Fix: Catch known domain exceptions explicitly; for unknown exceptions, log traceback and show a stable error code/message.
Acceptance: Unexpected failures produce actionable logs while preserving user-friendly output.
</task_stub>

<task_stub>
P2 | Remove dead UI error helper or use it consistently
Why: `show_problem_message()` exists but is never used, while errors are rendered via `st.error(...)`. Dead helper functions mislead maintainers and create style inconsistency.
Evidence: `app.py` defines `show_problem_message` at lines 156-161; error rendering later uses `st.error(...)` at line 359.
Fix: Either remove the unused helper or route all error display through it.
Acceptance: No unused error-rendering path remains.
</task_stub>

<task_stub>
P2 | Align visible fret limits between UI config and backend presets
Why: Acoustic guitar UI shows 14 visible frets while backend preset supports 15 max fret. This mismatch can cause confusing behavior (playable backend notes not selectable in UI).
Evidence: `app.py` sets `"visible_frets": 14` for acoustic (line 58), while `src/alttabs/instrument.py` defines `acoustic_guitar` max fret as 15 (line 157).
Fix: Decide single source of truth for fret limits and keep UI/display + backend constraints aligned.
Acceptance: Selected instrument exposes consistent fret range in UI and processing.
</task_stub>

<task_stub>
P2 | Normalize error taxonomy across transform/shift/pipeline/app layers
Why: `TransformError` and `PositionShiftError` are raised in lower layers, but app-level handling keys primarily on message text in `humanize_error`. This is brittle and makes future feature work risky.
Evidence: `src/alttabs/transform.py` lines 22-34 and `src/alttabs/position_shift.py` lines 98-141 raise domain-specific errors; `app.py` message mapping (lines 117-153) relies on string contains checks.
Fix: Introduce explicit typed errors (or error codes) propagated through `PipelineError` and mapped in UI without substring matching.
Acceptance: UI error handling is type/code-based, and changing exception wording no longer breaks user messaging.
</task_stub>
