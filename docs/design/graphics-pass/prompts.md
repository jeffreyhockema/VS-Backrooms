# Graphics pass: prompts

Templates for the sessions and agents the [plan](README.md) names. Fill the parts in angle brackets. Each prompt
is the whole context the agent gets, so it points at the files rather than repeating them.

## Worker (one per batch; Opus)

```
You are doing batch <Bn> of the Backrooms mod's graphics pass. Read, in this order:
  docs/design/graphics-pass/README.md      (the plan; sections 1, 3, 6 and 9 are binding)
  docs/design/graphics-pass/tracker.md     (the "lessons" section, and the rows of earlier batches)
  docs/design/graphics-pass/inventory.md   (your batch's rows: what is wrong and the fix idea for each)
  docs/DEVELOPING.md                       (build, harness, generators, shotbot)
  <the level's design doc(s) under docs/design/>

Scope of this batch: <the batch row from README.md section 7, verbatim>.
Generators you own for this batch: <list>. Other generators: read, do not change, unless a shared primitive in
tools/matlib.py or detail_kit.py needs an option, and then say so in your report.

Hard rules:
- Vanilla assets, shaders, lighting, the mod's palette and lore decisions, and the world layout do not change.
  If a fix seems to need one of those, write it in the report and leave the asset as it is.
- Saves must keep working (docs/DEVELOPING.md, "Keeping saves working"): never rename or remove a block, item
  or entity code, a variant group or a registered class name. New textures and shapes on existing codes are fine;
  a prop that needs a new footprint gets a new code beside the old one.
- Every change lives in a generator. Never hand-edit a PNG or JSON that a generator writes.
- Textures: structure, then shading, then low grain. Multiples of 8 px. Seamless. Alternates on large surfaces.
- Models: hardware and dials are geometry; different top and side textures; tools/check_zfight.py clean.
- Work on branch gfx/<Bn> off main, in this tree (no worktree). Build with: bash tools/locked.sh mod gfx
  Regenerate with: bash tools/locked.sh run python tools/<generator>.py
- Close the client before every build. Never build or run the harness while shots are being taken.
- Do not git stash. Do not touch bin/Debug.

The loop:
1. Offline: change generators; after each change run tools/texsheet.py --tile on the folder and the preview tool
   on changed models. Compare with the vanilla references named in the inventory (G:\Games\Vintagestory\assets\
   survival\textures\...). Iterate here until you would grade your own sheet B or better everywhere.
2. Regenerate, restore blocktypes/detail/exitlintel*.json if only their key order changed, build (0 warnings), run
   the harness: layouthash for versions 1 and 4 must be unchanged; validatelevel <n> for your levels.
3. Shoot: python tools/shotbot/batch.py --spots review/spots/<level>.json --build <scratch mods dir>
   --out review/<Bn>/after ; then python tools/shotbot/compare.py review/baseline/<level> review/<Bn>/after
   --out review/<Bn>/compare-round<k>.jpg
4. Spawn a reviewer (Opus) with the reviewer prompt from docs/design/graphics-pass/prompts.md, giving it only the
   compare sheet, the texsheets and the rubric. Fix what it finds. At most three rounds.
5. Append your report to tracker.md under your batch: per asset family what changed and the final grade; what is
   carried and why; lessons for later batches. Give the path of the final compare sheet. Do not merge.

Report back the tracker entry and the sheet path. If the user may be at the keyboard, ask before the first shoot.
```

## Reviewer (blind; Opus, spawned by the worker or the overseer)

```
You are grading a before/after sheet from the Backrooms mod's graphics pass. You have not seen the changes and must
not ask what they were. Read docs/design/graphics-pass/README.md section 3 (the rubric) and nothing else of the plan.

Files: <compare sheet path> (before above the magenta line, after below, one column per named spot),
<texsheet paths> (textures at 4x with vanilla references in the first row).

For every spot and every asset family you can identify, give:
  grade A-D (rubric), the specific fault in one sentence (which element, what is flat / painted / repeating /
  mis-scaled / out of place beside the vanilla block in frame), and whether the "after" is better, same or worse
  than the "before". Call out anything that moved away from the lore or palette, and anything that looks like a
  layout change. Say when a shot is too dark or too far to judge, rather than guessing.

Return a table, hardest problems first, then one paragraph on what the batch still needs to reach B everywhere.
```

## Inventory (Phase 1; a fresh Opus session)

```
Build the inventory for the Backrooms mod's graphics pass. Read docs/design/graphics-pass/README.md (sections 2,
3 and 7) and docs/DEVELOPING.md (the Assets section). Look at every sheet in review/baseline/ and every texsheet in
review/baseline/texsheets/. Open docs/screenshots/ for the hero shots.

Write review/inventory.md: one section per batch B3..B17 (README.md section 7), one row per asset family:
  family | generator function (file:function) | where seen (level, spot names) | grade A-D | fault | fix idea |
  closest vanilla reference (path) | priority 1-3 (1 = seen in most playthroughs and below B).
Group by what is generated together so a worker can take a section and know which functions to change. Mark hero
assets (what the gallery shows) with *. Where you cannot see an asset in any shot, say so and name a spot to add.

Do not change any file under assets/ or tools/. Report the counts per grade per batch at the end.
```

## Overseer gate (Fable, or the user)

```
Gate for batch <Bn>. Read the batch's tracker entry and open <final compare sheet>. Then:
- git diff main..gfx/<Bn> --stat ; confirm nothing under assets/game/, no src/Worldgen/WorldLayout* change, no
  AtmosphereSystem or lighting change, no palette or lore change not called out in the report.
- Spot-check three asset families against the rubric yourself, including one the reviewer graded A.
- Confirm layouthash (v1, v4) unchanged and the build warning count is 0 from the report, or rerun.
Merge to main with the batch's report as the commit body, or send back with the specific items and grades.
```
