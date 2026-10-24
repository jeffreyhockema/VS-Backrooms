# Needs: tracker

| Piece | Branch | Worker | State | Notes |
|---|---|---|---|---|
| plan | needs | Fable | written 2026-10-24 | README, decisions, prompts, `src/Needs/NeedsApi.cs` stub (builds) |
| A core | needs-core | Opus | started 2026-10-24 | |
| B beds | needs-beds | Sonnet | started 2026-10-24 | |
| C water | needs-water | Sonnet | started 2026-10-24 | |
| D hud | needs-hud | Sonnet | started 2026-10-24 | |
| E spear | needs-spear | Sonnet | started 2026-10-24 | |
| F docs | needs-docs | Haiku | started 2026-10-24 | |

Integration order: A, B, C, D, E, F into `needs`; then a blind review round, a fix round, the full `tools/aitest`
harness plus `--only needs`, a load of a 0.514.0-era world, the zip; then `main` (tell peer sessions first).
