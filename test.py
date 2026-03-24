from instrument import FretPosition, PlayedNote, presets
from pitch import Pitch
from score import RealizedEvent, TabRenderer
from tab import TabParser

parser = TabParser(presets["acoustic_guitar"])

# text = """
# e|--0-----3--|
# B|--1-----3--|
# G|--0-----0--|
# D|--2-----0--|
# A|--3-----2--|
# E|--------3--|
# """

text1 = """
e|-0---------------|-0---------------|-3-------3-------|-2-------2-------|
B|-1-------1-------|-0-------0-------|-0-----0---0-----|-3-----3---3-----|
G|-2-----2---2-----|-1-----1---1-----|-0---0-------0---|-2---2-------2---|
D|-2---2-------2---|-0---0-------0---|-0-------------0-|-0-------------0-|
A|-0-------------0-|-2-------------2-|-2---------------|-----------------|
E|-----------------|-0---------------|-3---------------|-----------------|
"""
text2 = """
e|-1-------1-------|-0-------0-------|-1---------------|-0---------------|
B|-1-----1---1-----|-1-----1---1-----|-3-------3-------|-0-------1-------|
G|-2---2-------2---|-0---0-------0---|-2-----2---2-----|-1-----1---1-----|
D|-3-------------3-|-2-------------2-|-0---0-------0---|-2---2-------2---|
A|-3---------------|-3---------------|---------------0-|-2-------------2-|
E|-----------------|-----------------|-----------------|-0---------------|
"""

parsed = parser.parse(text1)

for event in parsed.events:
    print("column", event.at_column)
    for note in event.notes:
        print(
            "  string",
            note.position.string,
            "fret",
            note.position.fret,
            "pitch",
            note.pitch.value,
        )


fretboard = presets["electric_guitar"]

events = [
    RealizedEvent(
        at_column=0,
        notes=[
            PlayedNote(Pitch(43), FretPosition(6, 3)),  # G2
            PlayedNote(Pitch(47), FretPosition(5, 2)),  # B2
            PlayedNote(Pitch(50), FretPosition(4, 0)),  # D3
        ],
    ),
    RealizedEvent(
        at_column=4,
        notes=[
            PlayedNote(Pitch(45), FretPosition(6, 5)),  # A2
        ],
    ),
    RealizedEvent(
        at_column=8,
        notes=[
            PlayedNote(Pitch(50), FretPosition(5, 5)),  # D3
            PlayedNote(Pitch(54), FretPosition(4, 4)),  # F#3
        ],
    ),
]

renderer = TabRenderer(fretboard)
print(renderer.render(events))
