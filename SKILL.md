---
name: aaddb
description: Batch-process A-side and B-side advertising videos with verified Chinese subtitles, glossary correction, matching landscape/portrait dimensions, Cartesian-product pairing across experience and reservation B libraries, classified outputs, deterministic naming, audible push-in edge-blur transitions, and final media QA. Use when Codex needs to create or repair A+B mixed videos, process A/B video libraries, add A-side subtitles and disclaimers, classify 体验/预约 outputs, or enforce the AaddB naming and transition rules.
---

# AaddB

Create all valid A+B combinations while preserving orientation, dialogue, audio, naming, and output structure.

## Workflow

1. Read `references/workflow.md`.
2. Run `scripts/batch.py ROOT --a-requester NAME --phase prepare`.
3. Review every generated `-字幕预览.mp4`. Correct its transcript JSON and rerun `prepare` until text and timing pass.
4. Run `scripts/batch.py ROOT --a-requester NAME --phase render --approve-subtitles` only after explicit subtitle approval.
5. Inspect the generated QA report and spot-check transition frames and audio before reporting completion.

## Hard rules

- Match horizontal A only to horizontal B; output `1920x1080`.
- Match vertical A only to vertical B; output `1080x1920`.
- Keep `成品/体验` and `成品/预约`; mix orientations inside each folder.
- Preserve the A-side final dialogue completely.
- Start the visual transition when the final spoken word begins; keep the A audio intact.
- Bring in B audio during the transition; do not create silence.
- Never freeze-copy the A tail to host a transition.
- Use a push-in transition with center-relative clarity and increasing edge blur.
- Do not burn or batch-render subtitles until the A-only subtitle preview passes QA.
- Never claim audio timing is verified when it was inferred from visuals or another edit.
- Name outputs as `A需求方+B需求方+A名称+B序号+B名称.mp4`, with `+` between every field.

## Bundled resources

- `references/workflow.md`: detailed directory, parsing, subtitle, naming, transition, and QA rules.
- `scripts/inventory.py`: scan, probe, deduplicate, classify, and predict combinations.
- `scripts/transcribe.py`: high-accuracy local Whisper transcription with word timestamps and glossary hotwords.
- `scripts/generate_ass.py`: generate orientation-specific ASS subtitles and the persistent A-side disclaimer.
- `scripts/render_transition.py`: render one verified A+B pair with the approved audible push-in edge-blur transition.
- `scripts/batch.py`: run inventory, transcription, preview, approved Cartesian-product rendering, naming, and QA.
- `scripts/qa.py`: validate output count, filenames, dimensions, FPS, and audio tracks.
