# aitest: headless perception tests

Starts a dedicated server with the built mod, puts straw dummies and a Hound down in the dark Level 6 and asserts what
the Hound sees, hears and senses (`/backrooms dummy ...`, `/backrooms perceive ...`; see
`docs/design/entity-ai-overhaul/README.md`, sections 4 and 4.5).

    BACKROOMS_SCRATCH="$TEMP/backrooms-build" bash tools/locked.sh mod ai
    python tools/aitest/run.py --mods "$TEMP/backrooms-build/build-ai/Mods" [--data DIR] [--keep] [--only lost,fear] [--no-smoke] [--port N] [--groups all|smoke] [--rerun-failed N]

One PASS/FAIL line per case with its evidence (timeline: S seen, s sensed, h heard, . none, one character per second).
The full console log is written to `<data>/aitest.log`. The exit status is non-zero on any failed case or any
`[backrooms]` error line. The first world generation can take minutes; the server uses port 42733 (`--port N` changes it, so two harnesses can run at once). `--only` skips the
`dummies on` smoke run, and `--no-smoke` does the same without `--only`. An unknown name in `--only` stops before the server starts and exits non-zero. `--groups all` runs every case group and the smoke (what no `--only` does), `--groups smoke` only the 60 s dummies smoke (it excludes `--only`), and `--rerun-failed N` reruns each failed case up to N more times on the same server (the placement cases are flaky); `tools/gate.py` uses `--groups all --rerun-failed 1`.

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

## Ways back (`--only ways`)

`ways-rowhouse-back` (feedback round 2026-11): from a Level 11 dummy's spot, `/backrooms wayback rowhouse x z` takes the nearest
rowhouse door that opens into the Suburbs and then tries its way back as a player would, by the block standing where the way
back is written (rel 1 and 2: the kind a right-click uses, `ThresholdSystem.UseKindOf`), and asks the pry bar whether it would
break it. It passes when both halves of the Suburbs door lead home and the pry bar refuses. Layouts 9 to 15 left a door there
with no threshold that a pry bar destroyed: this case fails on that.

## Hound packs and encounter rates (`houndrate.py`, not a case)

`python tools/aitest/houndrate.py --mods <Mods> --port <n> --minutes 40 --label <name>` puts five straw dummies down (Level 3's
approach, Level 8 by the road and off it, Level 9's approach and threshold, seed 12345's spots from mapgen `bandspots`), has the
director direct them (`dummies on`) with the telemetry on, and counts the Hound packs (Hounds put down to stalk or hunt) and all
bodies (set pieces left out) per 10 real minutes for each. Headless Hounds never reach a dummy: a pack hunts until its time
runs out and leaves. Run the old build and the new side by side on two ports to compare.

## Needs cases (`--only needs`, thirst and fatigue)

`needs-boot` (no log line about the needs' player patch or behaviours failing), `needs-selftest` (`/backrooms needstest`: every
pure-math check of docs/design/needs/README.md passes) and `needs-rates` (`ratecheck 1 heartland 400 awake=0` against
`awake=70`: the director's needs multiplier is about 2.9; at 0 awake hours it is 1, so `iso-rates` is untouched).

## Path cases (`--only path`)

`path-cubicle-partition`: `/backrooms pathtest duller` across a Level 4 back partition (seed 12345) must plan a way round it (10+ steps for 4 blocks), not over it (3 steps, as the game's step test planned before `TallBlockPathing`).

## Struck Skin-Stealers and Flickering (`--only p7-stealer`, `--only p7-flicker`)

`p7-stealer-fed`, `p7-stealer-hungry` and `p7-stealer-glimpse`: a fed Skin-Stealer (`/backrooms feed fed`) stays docile near a
dummy, a hungry one comes for it, and a hungry one's glimpse is read from the log. `p7-flicker` starts a Level 1 Flickering
(`/backrooms flicker`) and asserts the lights go out and a Hound hunts until they come back.

## Felt rates (`--only felt`)

`felt-rates`: the director's placement dry-run in every busy level (the table in `FELT_LEVELS`): a roll that finds no spot is
silence, so a stalk or hunt must be placeable at least a quarter of the time wherever a dummy stands in the approach band.

## World cases (`--only world`)

`sapling-grows` (`/backrooms growtree`): a sapling planted in Levels 9 and 10 (oak) and 9 (acacia) is made due and grows into a
tree with logs and leaves. A spot under a roof is retried, since a tree rightly does not fit there.

## Progression cases (`--only prog`)

`prog-armour` (`armourtest` for a Smiler and a Hound: blows to kill by level and armour set), `prog-speed` (from danger .36 a
hunter runs at least 1.15 sprints, 1.4 from Level 9; the lore-slow Wretch and Duller keep their own pace), `prog-zero` (a dummy
at stability 0 in Level 3 is sent the worst hunter and after 60 s moved to Level 2) and `prog-zero-safe` (zero in Level 0 does
nothing in 70 s).

## Walker cases (`--only walk`)

`walker-smoke` and `walker-struck`: see "Simulated players" in `docs/DEVELOPING.md` (`tools/aitest/walk.py` runs the same
walker for a long session).

## Working props (`--only props`, 0.700)

`props-lure-firealarm`, `props-lure-caralarm`, `props-lure-radio` and `props-lure-clock`: a Hound stalking a dummy hears the
lure four blocks beyond it ("hears <kind> at") and goes to see, so the noise is on the bus (the clock case puts down a real
alarm clock and winds it, so its own timer is tested). `props-sprinkler` (a pulled fire alarm sprays the head over the scene
and puts out the firepit and torch under it), `props-steam` (a turned valve blasts the dummy after the hiss and its health
falls) and `props-breaker` (a thrown breaker darkens the lamps under it, stays dark after a restart, and a fuse brings it back).

## Balance fixes (`--only bal`, 2026-11)

`bal-l73-table` (the castle feeds each wanderer once per 12 game hours: two dummies, `bal table`), `bal-coran` (a Hound beside
Coran: the kill leaves no carcass), `bal-drops` (class-scaled drops read off the block types: Basement pantry shelf x0.25,
Level 36 snack shelf x0.35, Level 15 seat carpet fibre, Level 120 rack wire and boards), `bal-l14-cache` (a Level 14 supply
box pays the Level 4 to 6 pool and none of iron, tin bronze or temporal gears), `bal-l23-water` (the level's clean water is
only at the Heart of Water's pool and Base Seedling's spring) and `bal-l52-dispenser` (a Level 52 snack machine never
restocks; Level 9's does). They use `/backrooms bal ...` (`src/Cheats/RigCommands.cs`). The gate's `harness` stage runs this
group, so `--only bal` is a harness group, not a gate stage.

## Other scripts

`smalltest.py` (the small checks of the feedback round: the Faceling's tell before its shove, borax ore in Level 8 against the
world's layout version, vanilla liquids filling the water bar) and `armourtest.py` (`--only` names a table; `tables` also
checks the recipe warnings) exit 1 on a FAIL verdict, as `houndrate.py` does with `--max-packs-per-10 N` and
`--one-pack-at-a-time`.
