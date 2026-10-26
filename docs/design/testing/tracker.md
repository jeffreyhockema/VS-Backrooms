# Testing tracker

### Gate

`tools/gate.py` (see docs/DEVELOPING.md "The gate"): generators --check, lang, build, boot, mapgen, oldworld, harness, zip. Branch `testing-gate` (the name `testing/gate` could not be created: a branch `testing` exists). Baselines in `tools/gate.hashes.json` (layout hashes v1, 9, 10, 11, 12: far places hash v1 `fc427d581f53ea30`, v9 and v10 `29d61d9ae6a6664e`, v11 and v12 `8808cf5b8452ad21`, matching the progression tracker; validatelevel 0-20, deep and shortcut counts of v12). `run.py` gained `--groups all|smoke` and `--rerun-failed N`; `locked.sh` a `release` mode.

**First full run** (`python tools/gate.py --zip`, 2026-10-25, commit 10639ca): PASS in 44m41s.

| Stage | Result | Time |
|---|---|---|
| generators | pass | 0m00s |
| lang | pass (9 files) | 0m00s |
| build | pass | 1m00s |
| boot | pass (fresh seed, 0 missing, 0 errors) | 0m40s |
| mapgen | pass (hashes match, baselines recorded) | 2m19s |
| oldworld | pass (sunny cave tales copy, ratecheck answered) | 0m41s |
| harness | pass, 44/44 (prog-speed failed once, passed on the rerun) | 36m58s |
| zip | pass (bin/backroomsss_0.610.0.zip, 19.1 MB, version matches) | 3m00s |

**`--fast`**: PASS in 4m26s (build 2m00 under lock contention, boot 0m36, harness smoke 1m48; about 2m40 with a build already made).

Flaky case seen: `prog-speed` (a pace measurement, not a placement case). Reviewer (sonnet, blind): 15 findings; fixed: zip stage deletes only the current version's zip, baselines written only by a problem-free run and `--update-baselines` covers deep/spawn, parsers fail when expected lines are missing, ratecheck reply matched exactly, reader thread joined before reading logs, stdin closed on children, build error regex, harness log kept on timeout, second-resolution stamps, rerun skips cases without a function. Not changed: a missing old-world save skips (loudly) rather than fails; the boot log scan is 10 s after ready; no stale-build check for `--only` runs on an old build.
