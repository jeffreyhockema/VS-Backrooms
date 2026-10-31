# Needs: tracker

| Piece | Branch | Worker | State | Notes |
|---|---|---|---|---|
| plan | needs | Fable | written 2026-10-24; all six pieces merged; three blind reviews (core, beds, water/HUD/assets) found 0 high / ~6 medium / ~14 low, all fixed 2026-10-24 (7a0c99a..b0677cb); harness needs+iso-rates+felt-rates pass; layout untouched | README, decisions, prompts, `src/Needs/NeedsApi.cs` stub (builds) |
| A core | needs-core | Opus | merged into needs 2026-10-24 | |
| B beds | needs-beds | Sonnet | merged into needs 2026-10-24 | |
| C water | needs-water | Sonnet | merged into needs 2026-10-24 | |
| D hud | needs-hud | Sonnet | merged into needs 2026-10-24 | |
| E spear | needs-spear | Sonnet | merged into needs 2026-10-24 | |
| F docs | needs-docs | Haiku | merged into needs 2026-10-24 | |

Integration order: A, B, C, D, E, F into `needs`; then a blind review round, a fix round, the full `tools/aitest`
harness plus `--only needs`, a load of a 0.514.0-era world, the zip; then `main` (tell peer sessions first).

Deviations from the plan after review: drinking from world water needs crouch + empty hands (liquids would otherwise block selection under water); night-visit odds in the text follow the formula (6% / 22% / 37%); beds wake you for pain, something close, hunger or thirst even with fatigue off.

Not yet: a client play-test (nothing here has been seen in a real client), the merge to main (peers vs-backrooms-9a/-23 to be told first), the version bump (0.515.0 or 0.516.0: the user's call).
