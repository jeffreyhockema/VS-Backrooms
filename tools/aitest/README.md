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

## P1 cases (`--only p1`, belief-based Menace task)

`p1-hunt-to-search`, `p1-stalk-to-investigate`, `p1-sight-hunt`, `p1-glimpse-to-stalk`, `p1-vague-track`, `p1-legacy`,
`p1-no-errors`. They put an entity down with `/backrooms encounter` (with `entitylog on`) and assert on its kind changes
and decision lines in the console log. Headless entities think but do not walk, so the cases test decisions (timeouts,
noises, sight), not movement. Spots are random, so a case retries until the layout allows it: an entity that starts
nearer than it needs to be (a short tunnel), a hunt whose first path fails (Hunt -> Stalk at once), a dummy not in an
Approach-or-worse band (read from `/backrooms dummies off`, which lists each dummy's band; Level 6 has such spots),
and a glimpse that is a crossing (40%, which go straight to Leave). A case that never finds its spot reports SKIPPED.
`--port N` (default 42733) lets two harnesses run at once.
