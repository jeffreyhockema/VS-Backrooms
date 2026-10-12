# Cross-level links: the reconciled list

The five plans each proposed links to the others and into the existing levels. This file settles where they overlapped
or disagreed. **Where it differs from a plan, this file wins.**

**Update 2026-10-09:** Level 3999 is restored (id 19) as an ordinary level (no ending; see the "User direction"
section at the end of `3999-plan.md`), and Level 188 is added (id 20). Their links to the five levels below are
settled in a second round once `188-plan.md` exists; until then, a 3999 or 188 link proposed by any plan is pending,
not void.

Rules, unchanged: every threshold always leads to the same place; walked through = two-way, fell/dived/taken = one-way.
Canon-backed exceptions that are one-way although walked: the Hub's carved doors, The End's Level 4 doorframe (both
"the doorway vanishes behind you"), and the Level ! entrances (they slam and lock).

## Links between the new levels

| From | Threshold | To | Way back | Owner of each side |
|---|---|---|---|---|
| Level ! | The true exit at the end of a lane (3 lanes in 17) | The End, beside an EXIT door | **None** (Level !'s "never re-enter" wins over the End plan's two-way proposal). A red "!" door is placed at the arrival, as Run's plan does for every exit | run: exit + marked door; end: arrival finder `EndExitArrival` |
| The Hub | Keyed carved door, `!` sigil | Level !, a lane's start room | None (key used up) | hub: door; run: arrival = start room finder |
| The Hub | Keyed carved door, Fun sigil | Level Fun, an elevator lobby | None (one-way, Hub canon; the Fun plan's two-way proposal is dropped) | hub; fun: lobby arrival finder |
| The Hub | Keyed carved door, End sigil | The End, beside an EXIT door | None | hub; end |
| The End | EXIT doors that lead to the Hub (25% of the unlocked ones) | The Hub, beside a **service door** | Two-way: that service door leads back to that EXIT door | end: door; hub: service-door arrival |
| The Hub | The **pink ribbon door** (replaces the keyed 974 door): no key needed, opens only for someone carrying something cute | That player's Level 974 house | None (taken) | hub: door block + check `L974.IsCute`; 974: arrival in own house |
| The End | A "=)" terminal (1 in 4 terminals) | Level Fun, an elevator lobby | None (taken) | end; fun |
| Any threshold | Kitty's detour (1 in 20 with something cute, 1 in 6 if held) | That player's Level 974 house | None | 974 (pre-arrival override hook from CONTRACT.md) |

Not linked: Level ! and Level Fun (canon has none; Level !'s horde stays our own entities), Level 974 to anything but
by the detour and the Hub's pink door, Level Fun → Hub.

## Shared entrance sites in existing levels (keep them disjoint)

Several plans put an entrance on the same kind of feature. Each still uses its own hash salt, but where two could
land on the same spot, the precedence below decides, and the loser does nothing there.

- **Level 37's dry corridor ends** (today all become office carpet → Level 4): one roll per corridor end, owned by a
  single helper in `WorldLayout.Level37.cs` (`PoolCorridorEndKind`, written by the **hub** agent, read by run):
  15% Level !'s red corridor, 20% the Hub's asphalt, 65% office carpet as now. Neither agent rolls its own.
- **Level 1:** Hub door (dead end of a winding maintenance hall in a corridor sector) > End EXIT door (1 in 25 locked
  room doors off the maintenance halls) > Fun stairs (1 in 20 ceiling stairs) > Run's door that shouldn't be there
  (a solid car-park district wall). A tile already claimed by an earlier entry is skipped by the later one.
- **Level 2:** Hub door (1 in 40 locked steel doors) and Run's false wall (blind tunnel ends): different features, no clash.
- **Level 11 lots:** the End's bookstore (midtown lot) and Fun's gym mascot doors (parking-garage lot) are different
  lot kinds; each is replanned over the top with its own Rng, as the cinema was. A lot is never both.
- **Level 5:** Fun's FUN doors take 1 in 150 locked rooms; The End's EXIT arrivals beside a locked guest door must skip
  a door that is a FUN door.

## Level keys (the Hub)

The Hub's keys are found in their own level. Each level agent places its own key in its level's loot, using the
Hub's item code `backrooms:hub-key-<tag>` (run, fun, end; 974 has no key, see the pink door). The **hub** agent's asset
script creates every key item (the existing levels' keys too) and owns the sigil table; other agents only reference
the code. Until the hub assets exist, reference the code anyway; it resolves at load.

## Handbook and README

Each plan's handbook text and "Ways Between Levels" rows are merged by the integration pass (phase 3), using the
links above.

## Round 2 (2026-10-09): Level 3999 and Level 188

User decisions: Level 3999 is an ordinary level (see `3999-plan.md` "User direction"); Level 188 is one shared
building (the Courtyard of Windows), and being pulled through a predatory window is death (canon: Entity 2).

| From | Threshold | To | Way back | Owner of each side |
|---|---|---|---|---|
| The Hub | Keyed carved door, 3999 sigil (ordinary, no "locked until visited") | Level 3999, beside a STAFF ONLY door | None (key used up) | hub: door + `hub-key-l3999` item and sigil (hub asset script); 3999: staff-door arrival finder |
| Level 3999 | A STAFF ONLY door | The Hub, beside a service door | Two-way: that service door | 3999: door; hub: service-door arrival |
| The Hub | **An open window** in a tunnel wall (no key; canon "look for a window in The Hub, and climb in") | Level 188, inside the matching courtyard window | Two-way: that window | hub: one window slot in its layout + a position lookup; 188: window block and arrival |
| Level Fun | A confetti window (one, salted) | Level 188 | Two-way | fun layout: a one-line salted hook written by the **188** agent; 188: arrival |
| The End | A terminal variant | Level 3999 | None (one-way) | 3999 agent, small salted edit in The End's terminal selection |
| Level 188 | The hatch in the courtyard deck | Level 37 | None (fell) | 188 |
| Level 188 | Fire exits | Levels 1, 5, 4, 2 | Two-way | 188 |
| Levels 0 and 1 | Windows (1 cell in 300 outer L0; 1 in 250 L1 warehouse sectors), salted | Level 188 | Two-way | 188 |

Entrance precedence in Level 1 gains Level 188's window last (after Run's door). Level 37 gains 3999's magenta tiles
(deep far Poolrooms, not a dry corridor end, so the corridor-end roll is unaffected) and receives 188's hatch drops.
