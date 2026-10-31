# The corpse a death leaves

Player request: dying should not lose your things to a ten-minute despawn timer. Put them in a body where you fell,
leave it indefinitely, mark it on the map, and show it as the player's own body (a skeleton after a long time).

## What the game does

- A player's death runs `EntityBehaviorPlayerInventory.OnEntityDeath` (a main-thread task), which calls
  `PlayerInventoryManager.OnDeath`: each player inventory (hotbar with the offhand, backpack's four bag slots with the
  contents carried inside the bag stacks, crafting grid, mouse slot) spawns its stacks as `EntityItem`s, with a
  `minsecondsToDespawn` of the player type's `droppedItemsOnDeathTimer` (600 s). Worn clothes and armour stay on the player.
- `keepContents` (world config `deathPunishment` = keep) skips all of that.
- Vanilla's `WaypointMapLayer` adds a pinned "You died here" gravestone waypoint on `PlayerDeath` (and removes the old one).
- The death screen's "N in-game minutes left for player revival" is `EntityPlayer.RevivableIngameHoursLeft` (world config
  `playerRevivableHourAmount`, 0.5 h): the window in which another player can revive you. It shows only in multiplayer or on
  a LAN game. It is not about the items. `assets/game/lang/*.json` overrides its two lang keys to say so.
- There is no corpse entity in the game. (`ModSystemCorpseReturnTeleporter` only remembers where you died.)

## What the mod does

`CorpseSystem` hooks the drop instead of replacing it, so every inventory the game drops (and any another mod adds) is
caught the way the game would have dropped it, and a world that keeps inventory leaves no body:

1. `OnEntityDeath` (a player): remember the death position, yaw, skin tree (`skinConfig`) and worn clothes.
2. `OnEntitySpawn` (an `EntityItem`): within 1.2 s of a death and 2 blocks of its position the stack is taken (cloned, whole)
   and the item entity removed. Nothing else is touched.
3. 1.3 s later the body is made: `EntityCorpse` on the floor under the death (up to 48 blocks down; else the last firm
   ground the player stood on; else the death position). If anything fails the stacks are dropped loose with a week's timer.
4. A pinned skull waypoint ("My body (Level 3, day 12)", icon `skull_and_crossbones`) for the owner when the world's map
   setting makes waypoints; their older ones are unpinned and kept. Vanilla's own death marker is removed. When the owner
   wakes they are told (in chat) that the body waits, and, in worlds with no waypoints, which way it lies.

## The body

- `corpse`: class `BackroomsCorpse` (`EntityCorpse`), the game's `seraph-faceless` shape and `seraph-naked-hairless` texture,
  behaviours `extraskinnable` + `seraphinventory` (modelled on the game's `playerbot`), so the dead player's `skinConfig`
  and character inventory tree, copied into its watched attributes, dress it exactly; the skin parts it needs are the
  player type's own (`CorpseSystem.AssetsFinalize`). The client starts the seraph's `die` animation (it holds its last
  frame; an old body gets it at once).
- `corpse-bones`: the game's lying human skeleton (`block/bone/carcass/humanoid2`), recentred by `tools/gen_corpse.py`.
  The body is replaced by it after `BonesAfterDays` (3) in-game days, with the same contents and the same marker.
- Contents: `backrooms-corpsecontents`, an `InventoryGeneric` (as many slots as stacks, in rows of four) kept in the watched
  attributes (`corpseInv`), shown in the game's creature-contents dialog. Anyone may loot it (no owner lock). Right-click
  opens; sneak and right-click moves everything that fits to the player (shift-click rules). Emptied, it crumbles
  (particles, a gravel sound) and the record and marker go. It never despawns on its own, and `/backrooms clear` skips it.
- Save data `backrooms-corpses` (`CorpseRecord`s) is only the index for markers and commands; the entity and its things are
  saved with their chunk. A body found without a record (a lost index) makes its own (`Adopt`).

## Not done

- No lock to the owner (anyone may loot); the grave is not a block (no protection from land claims).
- The skeleton is the game's, in the game's bone textures, not our own model.
