# aitest: headless perception tests

Starts a dedicated server with the built mod, puts straw dummies and a Hound down in the dark Level 6 and asserts what
the Hound sees, hears and senses (`/backrooms dummy ...`, `/backrooms perceive ...`; see
`docs/design/entity-ai-overhaul/README.md`, sections 4 and 4.5).

    BACKROOMS_SCRATCH="$TEMP/backrooms-build" bash tools/locked.sh mod ai
    python tools/aitest/run.py --mods "$TEMP/backrooms-build/build-ai/Mods" [--data DIR] [--keep] [--only lost,fear]

One PASS/FAIL line per case with its evidence (timeline: S seen, s sensed, h heard, . none, one character per second).
The full console log is written to `<data>/aitest.log`. The exit status is non-zero on any failed case or any
`[backrooms]` error line. The first world generation can take minutes; the server uses port 42733. `--only` skips the
`dummies on` smoke run.
