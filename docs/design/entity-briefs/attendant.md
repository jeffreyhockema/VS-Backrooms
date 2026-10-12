# Arcade Attendant (Level 3999): design brief

## Sources
- **Fandom, "Level 399: Neon Paradise / The Final Arcade"** (the page that used to be Level 3999; its images are still named `Level 3999.jpg`): https://backrooms.fandom.com/wiki/Level_399 (wikitext read through the MediaWiki API). This is the only wiki article that describes the attendants:
  - "humanoid robots akin to [[Entity 29]]; their height is usually 5 feet tall (152.4 cm)"
  - "dress in a formal style, comparable to flight attendant outfits"
  - "do not have faces and are made of a special type of plastic"
  - "talk through a speaker embedded in their head, and speak in a formal manner"
  - "induce a calming sensation ... when it is being looked at"; docile, cannot attack; hand out prizes and serve food; "anatomy, biology, and psychology similar to humans"
  - Addendum (Phenomenon 399): an interviewed attendant, "R.T.", calls herself a wanderer who was killed and woke in this body.
- **Fandom, Entity 29 "Mannequins"**: https://backrooms.fandom.com/wiki/Entity_29. A normal plastic shop mannequin, featureless. So "akin to" means the attendant is a mannequin-type body.
- **Wikidot**: there is no Level 3999 page (http://backrooms-wiki.wikidot.com/level-3999 returns 404), and Level 399 is an unwritten slot (red link on http://backrooms-wiki.wikidot.com/normal-levels-i). It has no canon on the attendants.
- **Miraheze** (https://backrooms.miraheze.org): there is no Level 3999 article. The search index lists one, but the page ID now redirects to "Forbidden Articles".
- Escape the Backrooms guides (for example https://gamerjournalist.com/how-to-access-and-beat-level-3999-in-escape-the-backrooms/) describe the arcade but no attendants.

## Keep
- 152 cm, faceless, plastic, harmless and formal, a flight-attendant uniform.
- The plan's two colourways (plum with pink piping, navy with cyan), pillbox hat, neckerchief, white gloves, name badge, knee skirt and low heels.
- The entity code, texture code `skin`, shape path, texture paths and all 6 animation codes.

## Change
- **Egg-shaped robot head with a 3x3 mouth grille becomes a mannequin head** (canon: "akin to Entity 29"). It has a smooth face, a moulded nose, faint empty hollows where eyes would be, and no eyes or mouth. Its hair is moulded in the same plastic, swept back into a chignon. The old visor seam made it read as a knight's helmet.
- **The speakers move to where the ears are**, as two small round grilles of pale metal. Canon only says "embedded in their head", and this keeps the face completely blank.
- **The uniform is tailored.** It has padded shoulders, a nipped waist, and a flared, piped jacket hem over a separate darker pencil skirt with a back slit. The piped lapels close in a V over a white blouse. It has gold wings, a small name badge, gold buttons and flap pockets. The neckerchief is knotted at the side of the neck with two tails. Piping now runs only on the edges (lapels, front edge, hem, cuffs, collar and hat band), not across every box.
- **Gloves have thumbs**, so the palm-up point and serve read. The legs have calves and a knee seam. The court shoes have a heel counter and a heel.
- **Animations are reworked.** The clasp now sits at the waist; before, it floated in front of the chest. In idle the head slowly tilts about 17 degrees, a little too far, and holds. Point is out to the side and forward with the palm up. Serve is palms up at waist height. Wave has the elbow out and the forearm upright, rocking. Walk takes small gliding steps that stay inside the pencil skirt.

## Proportions (16 px = 1 block; feet at 0)
| Landmark | px |
|---|---|
| Shoe top / ankle | 0.8 to 1.0 |
| Knee | 7.0 |
| Skirt hem | 7.4 |
| Hip joint / jacket hem | 12.0 / 12.1 |
| Waist (elbow height) | 13.5 to 15.3 |
| Shoulder joint | 19.0 (pads to 19.6) |
| Chin / crown (hair) | 20.85 / 24.35 |
| Pillbox top | about 25.5 |
| Shoulder width / hip width | 5.1 (6.8 with arms) / 4.4 |
| Head (skull) | 2.85 deep x 2.7 wide x 2.9 tall |
| Wrist / fingertips | 12.0 / 10.0 |
