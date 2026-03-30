# Alt-Tabs — Implementation Blueprint (Phase 0 Planning)

This document is the implementation base for the next stage. It translates product goals into concrete technical work, module-level changes, and acceptance criteria.

## Scope covered

1. Robust tab ingestion regardless of string-prefix format
2. Robust repeat detection (`x2`, `x3`, inline or nearby lines)
3. Comments/titles/section markers tolerated and preserved in output
4. Clean Streamlit error handling for unplayable transpositions/range limits
5. Sheet-music (partition) input via OCR/OMR → MIDI → existing tab generation pipeline
6. Keep monophonic output for now, but accept polyphonic input (tabs or score)
7. If score contains both clefs, ask user whether output should be guitar or bass tabs

---

## Current architecture summary (as of this plan)

- `src/alttabs/input_tab.py`
  - Splits text into fixed-size blocks (`split_raw_tab_blocks`) based on selected instrument string count.
  - Only supports repeat marker if it appears as standalone line immediately after a block.
  - Rejects non-tab lines during block build.
- `src/alttabs/tab.py`
  - Parses labels mainly as note-name labels (`eBGDAE` for guitar / `GDAE` for bass) or no label.
  - Does not support numeric string labels (`1..6` / `1..4`).
- `src/alttabs/pipeline.py`, `src/alttabs/transform.py`, `src/alttabs/position_shift.py`
  - Core transformation and re-fretting for monophonic streams.
  - Errors for non-playable range exist but are not normalized end-to-end.
- `app.py`
  - Streamlit app catches several exceptions and humanizes messages.
  - No score/partition input path yet.

---

## Decision 1 — Tab ingestion should support all common line prefixes

### Goal
Support guitar tabs with `eBGDAE`, `123456`, or no prefixes; and bass tabs with `GDAE`, `1234`, or no prefixes.

### Implementation decision
Introduce a **normalization + classification layer** before `TabParser`:

- New module: `src/alttabs/tab_preprocess.py`
  - `classify_line(line) -> LineKind` (tab line / repeat marker / comment / blank / unknown)
  - `normalize_tab_prefix(line, instrument) -> normalized_line`
  - Accept these prefix patterns:
    - Note names: `e|`, `B|`, `G|`, `D|`, `A|`, `E|`
    - Numeric labels: `1|`, `2|`, ... `6|` (or `4|` for bass)
    - Optional separators like spaces before first `|`
    - No label (line starts with `|`)

- Update `TabParser._string_number_from_label` in `src/alttabs/tab.py`
  - Add numeric label mapping by instrument string count and physical order.
  - Preserve existing letter-label behavior.

- Update `split_raw_tab_blocks` in `src/alttabs/input_tab.py`
  - Build blocks from lines classified as tab lines only.
  - Ignore/intercept non-tab lines rather than failing block count immediately.

### Why this design
Keeps parser strict for musical structure while moving "real-world messy input" handling into a dedicated preprocessing stage.

### Acceptance criteria
- Same musical content parses correctly with letter labels, numeric labels, or no labels.
- Mixed formatting across blocks is accepted.
- Invalid label/instrument combinations return clear errors.

---

## Decision 2 — Repeat markers should be detected flexibly

### Goal
Handle repeats when `xN` appears:
- right next to tablature,
- on the next line,
- on a nearby annotation line under/over a block.

### Implementation decision
Add repeat extraction rules in preprocess:

- Recognize patterns:
  - Standalone: `x2`
  - Trailing: `|----| x2`
  - Annotation style: `(x2)`, `repeat x2`, `X3`
- Attach repeat to nearest preceding complete tab block within a configurable lookback window (default 1–2 non-tab lines).
- Store repeat metadata in `RawTabBlock.repeat` (existing field reused).

### Why this design
Uses existing expansion logic (`to_realized_events`) while making detection robust to layout variations.

### Acceptance criteria
- Repeats are applied equivalently for inline and nearby-line forms.
- False positives in normal lyrics/comment lines are minimized by strict regex boundaries.

---

## Decision 3 — Comments must not fail parsing and should be rewritten in output

### Goal
Comments like `[Chorus]`, `1st verse`, section headers, etc. should not throw parser errors; they should appear in transformed output.

### Implementation decision
Create a **structured document model** for input:

- New dataclasses in `src/alttabs/input_tab.py` (or new `document.py`):
  - `DocumentItem = CommentItem | TabBlockItem`
  - `CommentItem(text, position_index)`
  - `TabBlockItem(raw_block, parsed_tab)`
- Parsing flow:
  - Keep comments while scanning.
  - Parse only tab blocks.
- Rendering flow:
  - Add renderer function that interleaves transformed tab blocks and comment lines in original relative order.
  - Normalize comments lightly (trim and preserve content).

### Why this design
Comments become first-class elements instead of side effects. This unlocks predictable output reconstruction and later richer formatting.

### Acceptance criteria
- Inputs containing comments + tabs do not error.
- Output preserves section comments in correct order relative to tab blocks.

---

## Decision 4 — Clean handling for unplayable transposition/range

### Goal
If requested transposition/anchor produces notes out of range, app should show clear, user-friendly error.

### Implementation decision
Unify domain errors with explicit types:

- New errors in `src/alttabs/errors.py`:
  - `RangeNotPlayableError`
  - `InvalidAnchorError`
  - `PolyphonyNotSupportedError` (for monophonic output stage)
- Raise these from:
  - `transpose_monophonic_events` (`src/alttabs/transform.py`) when no playable positions.
  - `shift_monophonic_events` (`src/alttabs/position_shift.py`) for anchor invalid/range dead-ends.
- In `src/alttabs/pipeline.py`, catch and rethrow as `PipelineError` with stable message codes or payload.
- In `app.py`, map those messages to explicit UI hints:
  - Suggest changing instrument, lowering transpose interval, or changing target fret/anchor.

### Why this design
Makes failures deterministic and debuggable; avoids leaking low-level exception text to UI.

### Acceptance criteria
- Unplayable requests show clean error banner (not stack trace, not vague generic failure).
- Message includes action guidance.

---

## Decision 5 — Partition (sheet-music) input via OCR/OMR to MIDI

### Goal
Accept score images/PDF, detect clef(s), extract notes/measures, and convert to MIDI for existing MIDI→tab workflow.

### Recommended tool
**Audiveris** (open-source OMR) as primary engine.

#### Rationale
- Mature OMR stack with MusicXML/MIDI export.
- Better suited than general OCR for notation semantics (staffs, clefs, note durations, measures).
- Supports batch processing for PDFs and images.

### Fallback/alternative
- **ScanScore** (commercial, strong UX/accuracy) if product allows paid dependency.
- **OpenOMR + custom post-processing** only if Audiveris integration is blocked.

### Implementation decision
Create a score ingestion adapter:

- New module: `src/alttabs/score_ingest.py`
  - `ingest_partition(file) -> ScoreIngestResult`
  - calls Audiveris CLI (or service wrapper)
  - returns:
    - `musicxml_path`
    - `midi_path`
    - detected staves/clefs by measure/staff
    - warnings/confidence flags
- Add measure segmentation from MusicXML (not raw OCR text):
  - parse measures, voices, and note onsets into internal event representation.
- Reuse existing MIDI/tab generation pipeline after conversion.

### Why this design
OMR should remain decoupled from tab transformation logic. MusicXML is the best intermediate for preserving structure.

### Acceptance criteria
- User can upload a score file and obtain MIDI-derived tab output.
- Treble-only score can route to guitar defaults; bass-only to bass defaults.

---

## Decision 6 — Polyphonic input support with monophonic output (for now)

### Goal
Input may contain chords/polyphony, but current output should remain monophonic.

### Implementation decision
Add explicit **polyphony reduction policy** at ingestion boundary:

- New enum: `PolyphonyPolicy` in `src/alttabs/pipeline.py`
  - `TOP_NOTE`, `BOTTOM_NOTE`, `FIRST_VOICE`, `ERROR`
- Default in UI: `TOP_NOTE` (musically common for melody extraction).
- For tab input:
  - when `TabEvent.notes` has multiple notes, reduce to selected policy before shift/transpose stage.
- For score/MIDI input:
  - flatten voices per time-slice using same policy.

### Why this design
Preserves forward compatibility with future polyphonic output while preventing current pipeline failures.

### Acceptance criteria
- Polyphonic input no longer crashes by default.
- Output is monophonic and deterministic according to policy.

---

## Decision 7 — Dual-clef score input should prompt instrument choice

### Goal
If partition contains both treble and bass clefs, app asks user whether to generate guitar or bass tabs.

### Implementation decision
- During score ingestion (`score_ingest.py`), return `detected_clefs = {treble: bool, bass: bool}`.
- In `app.py`:
  - If both clefs are present, show blocking radio/select:
    - "Generate Guitar Tabs"
    - "Generate Bass Tabs"
  - Use selection to choose target `instrument` preset and staff extraction strategy.
- Staff selection policy:
  - Guitar mode: prefer treble staff; optionally include merged voices per policy.
  - Bass mode: prefer bass staff.

### Why this design
Prevents silent wrong assumptions for piano/grand-staff scores.

### Acceptance criteria
- Dual-clef score triggers explicit choice before processing.
- Result uses selected instrument path.

---

## Cross-cutting refactor plan

1. Introduce a normalized document model (comments + tab blocks + metadata).
2. Add preprocessing/classification stage before `TabParser`.
3. Add error taxonomy and UI mapping.
4. Add score ingestion adapter (Audiveris + MusicXML/MIDI parsing).
5. Add polyphony reduction policy and wire into both tab and score inputs.
6. Extend Streamlit UI for score upload + dual-clef prompt + clearer error UX.

---

## Suggested delivery phases

- **Phase 1 (Parser hardening):** Decisions 1–3
- **Phase 2 (Error UX):** Decision 4
- **Phase 3 (Score ingestion):** Decisions 5 & 7
- **Phase 4 (Polyphony policy):** Decision 6

This sequencing isolates risk: robust text tabs first, then UX polish, then OMR integration.

---

## Non-goals for next implementation stage

- Full polyphonic tab rendering (chords in output)
- Advanced articulation retention (`h`, `p`, bends, slides) beyond current sanitization
- Rhythm-accurate ASCII spacing reconstruction

These can be planned once stable ingestion and score pipeline are in place.
