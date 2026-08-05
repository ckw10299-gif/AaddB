---
name: aaddb
description: Batch-process A-side and B-side advertising videos with verified Chinese subtitles, glossary correction, matching landscape/portrait dimensions, Cartesian-product pairing across experience and reservation B libraries, classified outputs, deterministic naming, audible push-in edge-blur transitions, and final media QA. Use when Codex needs to create or repair A+B mixed videos, process A/B video libraries, add A-side subtitles and disclaimers, classify 体验/预约 outputs, or enforce the AaddB naming and transition rules.
---

# AaddB

Create all valid A+B combinations while preserving orientation, dialogue, audio, naming, and output structure.

## Workflow

1. Inventory the source tree with `scripts/inventory.py` and `ffprobe`.
2. Classify by actual dimensions first; use filename labels only as hints.
3. Deduplicate B files by SHA-256 before forming combinations.
4. Read `references/workflow.md` before transcribing or rendering.
5. Transcribe every horizontal and vertical A independently with `scripts/transcribe.py`.
6. Inspect word timestamps and confidence. Re-run unclear audio regions; never guess or copy timing between orientations.
7. Build separate ASS subtitles for each A/orientation using the required styles and disclaimer.
8. Form the Cartesian product of each A with every B in the same orientation, separately for `体验` and `预约`.
9. Render each pair with `scripts/render_transition.py`.
10. Verify counts, dimensions, FPS, audio tracks, subtitle events, transition frames, and filenames before reporting completion.

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

## Bundled resources

- `references/workflow.md`: detailed directory, parsing, subtitle, naming, transition, and QA rules.
- `scripts/inventory.py`: scan, probe, deduplicate, classify, and predict combinations.
- `scripts/transcribe.py`: high-accuracy local Whisper transcription with word timestamps and glossary hotwords.
- `scripts/render_transition.py`: render one verified A+B pair with the approved audible push-in edge-blur transition.
