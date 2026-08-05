# AaddB workflow reference

## Directory contract

Expected source layout:

```text
root/
??? A?/
??? B?/
?   ??? ??/
?   ??? ??/
??? bgm/                 # optional
??? ?????.txt        # one term per line
??? ??/
    ??? ??/
    ??? ??/
```

Output category follows the B library. Do not add horizontal/vertical subfolders.

## Orientation and Cartesian product

Use probed dimensions as authority:

- width > height: horizontal; normalize to `1920x1080`.
- height > width: vertical; normalize to `1080x1920`.
- reject square or ambiguous media for manual review.

For every A, pair it with every unique B in the same orientation and category. Expected count:

```text
horizontal_A * horizontal_B + vertical_A * vertical_B
```

Compute the formula separately for `??` and `??`. Hash B files and skip exact duplicates.

## Subtitle recognition and validation

Use `large-v3-turbo` or a comparably accurate multilingual model, word timestamps, Chinese language, glossary hotwords, and no timing reuse between horizontal and vertical edits.

For every A:

1. Transcribe the full audio independently.
2. Inspect every word timestamp and probability.
3. Flag gaps longer than 1.5 seconds between dialogue events when visible speaking or strong vocal energy exists.
4. Re-transcribe suspicious time windows as isolated, normalized mono clips.
5. Treat low-confidence domain words as glossary candidates; correct text only when the intended term is supported.
6. Never invent a cue time. If recognition is unresolved, stop before rendering and report the exact interval.
7. Render an A-only preview and inspect frames at the midpoint of every subtitle event.

Maintain a glossary, including discovered terms such as:

```text
?????
??
???
??
????
```

### Subtitle styles

Main subtitle:

- white bold Microsoft YaHei or equivalent;
- black outline and subtle shadow;
- horizontally centered;
- around 65-70% of frame height;
- vertical reference: about 90 px at 1080x1920;
- horizontal reference: about 56 px at 1920x1080.

A-side disclaimer, visible for the entire A contribution:

```text
????????,????????
```

Place it in the lower-right safe area as small, low-emphasis white text.

## Transition and audio

Do not extend A with a cloned still frame. Determine `transition_offset` from the start of the final spoken word for each A edit independently.

Approved visual:

- about 0.4 seconds;
- `xfade=zoomin`;
- variable blur driven by a radial mask: center near zero blur, edges up to roughly radius 14;
- apply variable blur only to the transition slice for performance;
- inspect continuous frames for black frames, freezes, subtitle ghosting, and global double images.

Approved audio:

- retain the complete A audio at normal level;
- start B audio at the visual transition offset;
- fade B audio in over the transition while mixing with intact A audio;
- never insert silence;
- keep B audio aligned with B video after the transition.

## Filename parsing and output naming

A requester is normally a suffix such as `-ckw` in the A filename. If missing, require the user to provide it.

Example B filename:

```text
G36-V1560-1080x1920-20260724-cwt-??;ae;????;????;????.mp4
```

Parse:

- B sequence: `V1560`.
- B requester: `cwt`, the field after the date.
- B name: only the final semicolon-delimited label, `????`.
- Ignore project code, resolution, date, and earlier tags in the output name.

Output format:

```text
A???+B???+B??B??.mp4
```

Example:

```text
ckw+cwt+V1560????.mp4
```

Do not put `+` between sequence and B name. If horizontal and vertical outputs collide in the same category, append `??` or `??` only to the colliding names.

## Final QA

- Count equals the deduplicated Cartesian-product prediction.
- Experience and reservation counts match their respective B libraries.
- Horizontal outputs are `1920x1080`; vertical outputs are `1080x1920`.
- Video is H.264, 30 FPS; audio is AAC stereo unless the source requires otherwise.
- Every expected subtitle event appears and contains complete text.
- Verify difficult cues from the final outputs, not only the ASS or preview.
- The A final word remains audible.
- B audio is audible during the transition and synchronized afterward.
- Transition has real A motion, push-in, edge blur, no freeze, no black frames, and no obvious ghosting.
- Filenames contain the correct requesters, B sequence, and final B label.
