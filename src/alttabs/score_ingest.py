from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET


class ScoreIngestError(Exception):
    pass


@dataclass(frozen=True)
class ScoreIngestResult:
    midi_path: Path
    musicxml_path: Path | None
    has_treble_clef: bool
    has_bass_clef: bool


def ingest_partition_to_midi(score_path: str | Path) -> ScoreIngestResult:
    """Convert score (image/PDF) to MIDI via Audiveris CLI and detect clefs from MusicXML."""
    score_path = Path(score_path)
    if not score_path.exists():
        raise ScoreIngestError(f"Score file not found: {score_path}")

    audiveris = shutil.which("audiveris")
    if not audiveris:
        raise ScoreIngestError(
            "Audiveris is not installed. Install Audiveris CLI to use partition OCR."
        )

    with tempfile.TemporaryDirectory(prefix="alttabs_omr_") as tmpdir:
        out_dir = Path(tmpdir)
        cmd = [
            audiveris,
            "-batch",
            "-export",
            "-output",
            str(out_dir),
            str(score_path),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise ScoreIngestError(
                "Audiveris failed to process partition. "
                f"stderr: {proc.stderr.strip() or 'unknown error'}"
            )

        midi_files = sorted(out_dir.rglob("*.mid")) + sorted(out_dir.rglob("*.midi"))
        xml_files = sorted(out_dir.rglob("*.mxl")) + sorted(out_dir.rglob("*.xml"))

        if not midi_files:
            raise ScoreIngestError("No MIDI output produced by Audiveris.")

        chosen_midi = midi_files[0]
        chosen_xml = xml_files[0] if xml_files else None
        has_treble, has_bass = detect_clefs_from_musicxml(chosen_xml) if chosen_xml else (False, False)

        persisted_dir = Path(tempfile.mkdtemp(prefix="alttabs_omr_keep_"))
        final_midi = persisted_dir / chosen_midi.name
        final_midi.write_bytes(chosen_midi.read_bytes())

        final_xml = None
        if chosen_xml:
            final_xml = persisted_dir / chosen_xml.name
            final_xml.write_bytes(chosen_xml.read_bytes())

    return ScoreIngestResult(
        midi_path=final_midi,
        musicxml_path=final_xml,
        has_treble_clef=has_treble,
        has_bass_clef=has_bass,
    )


def detect_clefs_from_musicxml(musicxml_path: Path) -> tuple[bool, bool]:
    try:
        root = ET.parse(musicxml_path).getroot()
    except Exception:
        return False, False

    has_treble = False
    has_bass = False

    for clef in root.findall(".//clef"):
        sign = clef.findtext("sign", default="").strip().upper()
        if sign == "G":
            has_treble = True
        if sign == "F":
            has_bass = True

    return has_treble, has_bass
