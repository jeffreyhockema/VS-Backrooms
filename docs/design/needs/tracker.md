# Needs: tracker

| Piece | Branch | Worker | State | Notes |
|---|---|---|---|---|
| plan | needs | Fable | written 2026-10-24; all six pieces merged, build clean; blind review round running | README, decisions, prompts, `src/Needs/NeedsApi.cs` stub (builds) |
| A core | needs-core | Opus | merged into needs 2026-10-24 | |
| B beds | needs-beds | Sonnet | merged into needs 2026-10-24 | |
| C water | needs-water | Sonnet | merged into needs 2026-10-24 | |
| D hud | needs-hud | Sonnet | merged into needs 2026-10-24 | |
| E spear | needs-spear | Sonnet | merged into needs 2026-10-24 | |
| F docs | needs-docs | Haiku | merged into needs 2026-10-24 | |

Integration order: A, B, C, D, E, F into `needs`; then a blind review round, a fix round, the full `tools/aitest`
harness plus `--only needs`, a load of a 0.514.0-era world, the zip; then `main` (tell peer sessions first).
