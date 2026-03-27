# Alt-tabs: transpose and shift guitar (and bass) tabs

This lib takes guitar and bass tabs as input, and modifies them according to the user's preferences:

- The position in which the notes are played can be shifted for different finger movements (e.g. play an A on the 5th fret of the E string instead of the open A string)
- The key can be changed
- All of this happens automatically when a new position is selected on the fretboard: it will be where the first note is played. The rests follows.
- It is possible to give a "bias" instruction, so the next notes will be played either down to the table, up to the nut or centered around the starting position.
