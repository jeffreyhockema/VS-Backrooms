# aitest: headless perception tests

Starts a dedicated server with the built mod, puts straw dummies and a Hound down in the dark Level 6 and asserts what
the Hound sees, hears and senses (`/backrooms dummy ...`, `/backrooms perceive ...`; see
`docs/design/entity-ai-overhaul/README.md`, sections 4 and 4.5).

    BACKROOMS_SCRATCH="$TEMP/backrooms-build" bash tools/locked.sh mod ai
    python tools/aitest/run.py --mods "$TEMP/backrooms-build/build-ai/Mods" [--data DIR] [--keep] [--only lost,fear] [--no-smoke] [--port N]

One PASS/FAIL line per case with its evidence (timeline: S seen, s sensed, h heard, . none, one character per second).
The full console log is written to `<data>/aitest.log`. The exit status is non-zero on any failed case or any
`[backrooms]` error line. The first world generation can take minutes; the server uses port 42733 (`--port N` changes it, so two harnesses can run at once). `--only` skips the
`dummies on` smoke run, and `--no-smoke` does the same without `--only`. An unknown name in `--only` stops before the server starts and exits non-zero.

## P1 cases (`--only p1`, belief-based Menace task)

`p1-hunt-to-search`, `p1-stalk-to-investigate`, `p1-sight-hunt`, `p1-glimpse-to-stalk`, `p1-vague-track`, `p1-legacy`,
`p1-no-errors`. They put an entity down with `/backrooms encounter` (with `entitylog on`) and assert on its kind changes
and decision lines in the console log. Headless entities think but do not walk, so the cases test decisions (timeouts,
noises, sight), not movement. Spots are random, so a case retries until the layout allows it: an entity that starts
nearer than it needs to be (a short tunnel), a hunt whose first path fails (Hunt -> Stalk at once), a dummy not in an
Approach-or-worse band (read from `/backrooms dummies off`, which lists each dummy's band; Level 6 has such spots),
and a glimpse that is a crossing (40%, which go straight to Leave). A case that never finds its spot reports SKIPPED.

`p1-hunt-to-search`: a hunt the director put down ("sent hunt") refreshes its belief every 2 s for its first
`sentHuntSeconds` (10) and only then does memory (8 s for the Hound) fade, so Hunt -> Search comes at about 18 to 40 s
(the case allows 45 s) and must not be followed by another Hunt. A hunt whose path fails (headless entities never walk)
goes Hunt -> Stalk by the no-path rule; the case drops those spots and retries. `p1-legacy` expects the Skin-Stealer and
the Death Rat (senses profiles since P2) to stay out of Investigate and Search.

## P2/P4 cases (`--only p26`)

`p2-fed-stealer` (an Ambient Skin-Stealer fed with `/backrooms feed fed` stays Ambient for 20 s; checked with
`/backrooms feed status`), `p4-strider-fear` (a hunting Hound and a Strider put down for the same Level 9 dummy: the
Strider logs "frightens hound" and the Hound's progress lines stop; the Watch sets the Hound's kind from outside, so no
"Hunt -> Leave" line appears), `p4-watcher-fires` (a Watcher hunting a lit Level 9 dummy logs "charges at" and "fires
at"). Entities that log no "starts:" line (Ambient stealer, Watcher, Strider) are read by entity code (`Enc(ident=False)`).

## P7 cases (`--only p7`, struck creatures fight back)

In Level 0 (the Lobby, where nothing hunts), the dummy carrying a candle: a creature that is struck must go to Hunt and stay there, with no stare-down, no Lobby call-off and no Leave, whatever it was doing.

`p7-hound-struck` and `p7-bacteria-struck` (struck, they hunt at once), `p7-bacteria-cornered` (the target 3 blocks off, inside its cornered range: within seconds it lunges, a provoked hunt) and `p7-bacteria-chased` (the target at about 9 blocks, carrying a torch: the Bacteria keeps falling back from it, and after its chase time howls and turns).

## Isolation cases (`--only iso`, the rate rolls and one kind at a time)

`iso-rates` runs `/backrooms ratecheck` for a set of levels and bands and asserts the bodies and sounds per hour against the isolation plan's bounds. `iso-one-kind` checks that the rolls with one menacing entity about put down no body at all (the control does), then that a stalking Hound about a Level 1 dummy for two minutes is the only body put down for it.

## Hound cases (`--only iso-hound`)

`iso-hound-nerve` (a dummy staring a Hound down from 10 blocks: no hunt for its nerve, then "hunts: nerve"), `iso-hound-back-turned` (the target's back turned, in sight within 16 blocks: hunted after 2 seconds), `iso-hound-runner` (a running dummy beats the stare: "hunts: ran") and `iso-hound-gives-up` (a dark dummy out of its line: its belief fades, it searches and leaves, and does not hunt again).

## Needs cases (`--only needs`, thirst and fatigue)

`needs-boot` (no log line about the needs' player patch or behaviours failing), `needs-selftest` (`/backrooms needstest`: every
pure-math check of docs/design/needs/README.md passes) and `needs-rates` (`ratecheck 1 heartland 400 awake=0` against
`awake=70`: the director's needs multiplier is about 2.9; at 0 awake hours it is 1, so `iso-rates` is untouched).
