"""Level 14 "The Hospital" (experimental): the furniture and equipment, their textures (tools/gen_14_props_tex.py), models
(tools/gen_14_props_a.py: reception and wards; tools/gen_14_props_b.py: surgery, torture chambers, T.14.R.G., contaminated
rooms, halls) and block types. The asset contract is docs/design/experimental-levels/14-plan.md section 4.

Reception rooms
    l14-desk-{endl|mid|supplies|lamp|phone|endr}-{side}   the oval reception desk, four tiles in a row (endl, two mids,
                                    endr; with side north endl is the west end): a veneered front with a raised transaction
                                    ledge to the side, the work surface behind; the ends curve back round the receptionist's
                                    side. supplies: bandages and pill bottles (drops them); lamp: a lit desk lamp (light 8)
    l14-waitchair-{plain|magazine|soda|torn}-{side}       a waiting-room seat, one a block, arms and beam shared in a row
    l14-floorlamp-{lower|upper}-{on|off}                  a standard lamp (upper on: light 12, warm)
    l14-magtable, l14-sodas                               a low table of magazines; bottles on the floor (walk-through)
Inpatient wards
    l14-bed-{head|foot}-{made|stripped}-{side}, l14-strapbed-{head|foot}-{side}   a white hospital bed, two blocks, head
                                    to the south of the foot (side = the way the foot lies from the head); BackroomsBed
    l14-curtain-{lower|upper}-{side}    a privacy curtain along the block's <side> edge (walk-through)
    l14-overbed-{side}, l14-monitor-{on|off}-{side} (on: light 4 green), l14-ventilator-{side}, l14-crib-{side},
    l14-teddy-{side} (walk-through), l14-desk2-{side}, l14-cabinet-{lower|upper}-{side}
Surgery
    l14-optable-{head|foot}-{side} (tilted head-down, head to the south), l14-surglamp (the top air block of a room;
    light 14 white; walk-through), l14-trolley-{clean|rusty}-{side}, l14-anaesthesia-{side},
    l14-equipshelf-{lower|upper}-{side}, l14-tuberack-{side}, l14-vines, l14-mouldfloor (walk-through)
Torture chambers
    l14-stretchers-{lower|upper}-{side}, l14-knifecab-{lower|upper}-{side}, l14-hook (top air block), l14-bloodpool
T.14.R.G.
    l14-trgdesk-{papers|radio|samples}-{side}, l14-samplerack-{side} (light 3 green), l14-crate-{side},
    l14-cell-{lower|upper}-{intact|broken}-{side} (the glass along the <side> edge; broken: shards on this block's floor)
Contaminated rooms
    l14-drum-{sealed|leaking} (leaking: light 4 green)
Halls
    l14-station-{counter|computer|corner}-{side} (corner: an L, the run continuing east with the same side and south
    with the side turned a quarter left: corner-north joins counter-north to its east and counter-west to its south),
    l14-linencart-{side}, l14-bench-{side}

Run from the worktree root:  bash tools/locked.sh run python tools/gen_14_props.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_14_props_tex as TX  # noqa: E402
import gen_14_props_kit as K  # noqa: E402
import gen_14_props_a as A  # noqa: E402
import gen_14_props_b as PB  # noqa: E402
import gen_14_r4 as R4  # noqa: E402
from gen_14_props_kit import block, drops, SIDES, WOOD, METAL, CLOTH, GLASS, PLANT, SOFT  # noqa: E402

WARM8, WARM12 = [7, 4, 8], [7, 4, 12]
GREEN4, GREEN3 = [23, 5, 4], [20, 5, 3]
WHITE14 = [8, 0, 14]
OOZE4 = [19, 6, 4]
BANDAGE = "game:bandage-clean"

# Display names (lang keys -> English); the level's builder merges them into en.json
NAMES = {
    "block-l14-desk-endl-*": "Reception Desk", "block-l14-desk-endr-*": "Reception Desk", "block-l14-desk-mid-*": "Reception Desk",
    "block-l14-desk-supplies-*": "Reception Desk (Medical Supplies)", "block-l14-desk-lamp-*": "Reception Desk (Lamp)",
    "block-l14-desk-phone-*": "Reception Desk (Telephone)",
    "block-l14-waitchair-plain-*": "Waiting Room Seat", "block-l14-waitchair-magazine-*": "Waiting Room Seat (Crumpled Magazine)",
    "block-l14-waitchair-soda-*": "Waiting Room Seat (Soft Drink Bottle)", "block-l14-waitchair-torn-*": "Waiting Room Seat (Torn)",
    "block-l14-floorlamp-*": "Floor Lamp", "block-l14-magtable": "Magazine Table", "block-l14-sodas": "Musty Soft Drink Bottles",
    "block-l14-bed-*-made-*": "Hospital Bed", "block-l14-bed-*-stripped-*": "Hospital Bed (Stripped)",
    "block-l14-strapbed-*": "Hospital Bed with Restraints", "block-l14-curtain-*": "Privacy Curtain",
    "block-l14-overbed-*": "Over-bed Table", "block-l14-monitor-on-*": "Patient Monitor (On)", "block-l14-monitor-off-*": "Patient Monitor",
    "block-l14-ventilator-*": "Ventilator", "block-l14-crib-*": "Hospital Bassinet", "block-l14-teddy-*": "Stuffed Teddy Bear",
    "block-l14-desk2-*": "Ward Desk", "block-l14-cabinet-*": "Medicine Cabinet",
    "block-l14-optable-*": "Operating Table", "block-l14-surglamp": "Surgical Light",
    "block-l14-trolley-clean-*": "Instrument Trolley", "block-l14-trolley-rusty-*": "Rusted Instrument Trolley",
    "block-l14-anaesthesia-*": "Anaesthesia Machine", "block-l14-equipshelf-*": "Shelf of Old Surgical Equipment",
    "block-l14-tuberack-*": "Overgrown Test Tubes", "block-l14-vines": "Creeping Vines", "block-l14-mouldfloor": "Mould",
    "block-l14-stretchers-*": "Rusted Stretchers", "block-l14-knifecab-*": "Cabinet of Knives", "block-l14-hook": "Chains and Meat Hook",
    "block-l14-bloodpool": "Pool of Blood",
    "block-l14-trgdesk-papers-*": "T.14.R.G. Field Desk (Papers)", "block-l14-trgdesk-radio-*": "T.14.R.G. Field Desk (Radio)",
    "block-l14-trgdesk-samples-*": "T.14.R.G. Field Desk (Samples)", "block-l14-samplerack-*": "Compound 14 Sample Rack",
    "block-l14-cell-*-intact-*": "Containment Chamber Glass", "block-l14-cell-*-broken-*": "Smashed Containment Chamber Glass",
    "block-l14-crate-*": "T.14.R.G. Supply Crate",
    "block-l14-drum-sealed": "Radioactive Waste Drum", "block-l14-drum-leaking": "Leaking Radioactive Waste Drum",
    "block-l14-station-*": "Nurses' Station", "block-l14-linencart-*": "Linen Cart", "block-l14-bench-*": "Hall Bench",
    # round 4
    "block-l14-gurney-*-plain-*": "Gurney", "block-l14-gurney-*-strap-*": "Gurney with Restraints", "block-l14-wheelchair-*": "Wheelchair",
    "block-l14-ivstand-*": "Drip Stand", "block-l14-stationback-*": "Nurses' Station Back Unit", "block-l14-vending-*": "Vending Machine (Empty)",
    "block-l14-locker-*": "Staff Lockers",
}

FULL = (0, 0, 0, 1, 1, 1)


def reception():
    block("l14-desk", [("part", ["endl", "mid", "supplies", "lamp", "phone", "endr"]), ("side", SIDES)], lambda v: A.desk(v["part"]),
          "Level 14's reception rooms: the oval reception desk, four tiles in a row (endl, two mids, endr; with side north endl is the "
          "west end): a veneered front toward <side> with a raised transaction ledge, the work surface behind; the ends sweep back round "
          "the receptionist's side. supplies: bandages, antibiotics and painkillers left out; lamp: a lit desk lamp; phone: a telephone",
          boxes=lambda v: ([(0, 0, 0, 1, 1.08, 0.44), (0, 0, 0.44, 0.45, 1.08, 1)] if v["part"] == "endl" else
                           [(0, 0, 0, 1, 1.08, 0.44), (0.55, 0, 0.44, 1, 1.08, 1)] if v["part"] == "endr" else
                           [(0, 0, 0, 1, 1.08, 0.42), (0, 0, 0.42, 1, 0.75, 0.75)]),
          sel=lambda v: [(0, 0, 0, 1, 1.08, 1)] if v["part"] in ("endl", "endr") else [(0, 0, 0, 1, 1.08, 0.78)],
          material="Wood", sounds=WOOD,
          data={"lightHsvByType": {"*-lamp-*": WARM8},
                "dropsByType": {"*-supplies-*": drops((BANDAGE, 1, 0.6), ("backrooms:l14-painkillers", 0.6, 0.5),
                                                      ("backrooms:l14-antibiotics", 0.3, 0.3)), "*": []}},
          inventory=["*-mid-north", "*-endl-north", "*-endr-north", "*-supplies-north", "*-lamp-north", "*-phone-north"])
    block("l14-waitchair", [("kind", ["plain", "magazine", "soda", "torn"]), ("side", SIDES)], lambda v: A.waitchair(v["kind"]),
          "Level 14's reception rooms: a waiting-room seat facing <side>, teal vinyl on a steel shell, one a block; in a row the beam and "
          "the armrests join. magazine: a crumpled magazine on it; soda: a musty soft-drink bottle; torn: the vinyl split to the foam",
          boxes=[(0, 0, 0.1, 1, 0.6, 0.85)], sel=[(0, 0, 0.1, 1, 1.2, 0.9)], material="Cloth", sounds=CLOTH,
          data={"dropsByType": {"*-soda-*": drops(("backrooms:emptybottle", 0.6, 0.4), ("backrooms:l14-stalesoda", 0.5, 0.5)), "*": []}})
    block("l14-floorlamp", [("part", ["lower", "upper"]), ("state", ["on", "off"])], lambda v: A.floorlamp(v["part"], v["state"] == "on"),
          "Level 14's reception rooms: a standard lamp two blocks high (lower: the weighted base and pole; upper: the fabric shade, lit "
          "when on)", boxes=lambda v: [(0.3, 0, 0.3, 0.7, 1, 0.7)] if v["part"] == "lower" else [(0.18, 0, 0.18, 0.82, 0.8, 0.82)],
          rot=None, material="Metal", sounds=METAL, data={"lightHsvByType": {"*-upper-on": WARM12}},
          inventory=["*-lower-on", "*-upper-on", "*-upper-off"])
    block("l14-magtable", [], lambda v: A.magtable(), "Level 14's reception rooms: a low table, magazines and brochures of unusual "
          "contents on it", boxes=[(0.06, 0, 0.12, 0.94, 0.44, 0.88)], material="Wood", sounds=WOOD)
    block("l14-sodas", [], lambda v: A.sodas(), "Level 14's reception rooms: musty soft-drink bottles on the floor, some with stale "
          "contents (walk-through)", boxes=None, sel=[(0.1, 0, 0.1, 0.9, 0.55, 0.9)], material="Glass", sounds=GLASS,
          data={"drops": drops(("backrooms:emptybottle", 0.6, 0.4), ("backrooms:l14-stalesoda", 0.5, 0.5)), "resistance": 0.5,
                "replaceable": 100})


def bed_data(made, strap=False):
    q = 0.5 if strap else None
    out = {"class": "BackroomsBed", "entityClassByType": {"*-head-*": "BackroomsBed"}}
    if strap:
        out["attributes"] = {"bedFoot": "side", "restQuality": q}
    else:
        out["attributesByType"] = {"*-stripped-*": {"bedFoot": "side", "restQuality": 0.6}, "*": {"bedFoot": "side", "restQuality": 0.8}}
    return out


def wards():
    bed_box = [(0.03, 0, 0, 0.97, 0.75, 1)]
    block("l14-bed", [("part", ["head", "foot"]), ("state", ["made", "stripped"]), ("side", SIDES)], lambda v: A.bed(v["part"], v["state"]),
          "Level 14's wards: a white hospital bed, two blocks (head, foot), the foot lying from the head toward <side> (so the head end "
          "is the headboard's): rails, castors, the chart on the footboard; made, or stripped to the stained mattress. Sleepable",
          boxes=bed_box, sel=lambda v: [(0.03, 0, 0, 0.97, 1.2 if v["part"] == "head" else 1.0, 1)], material="Cloth", sounds=CLOTH,
          data=bed_data(True), inventory=["*-head-made-north", "*-head-stripped-north"])
    block("l14-strapbed", [("part", ["head", "foot"]), ("side", SIDES)], lambda v: A.bed(v["part"], "strap"),
          "Level 14's behaviour unit: a hospital bed with leather restraint straps over the chest, hips and ankles and cuffs on the rails, "
          "two blocks as l14-bed", boxes=bed_box, sel=lambda v: [(0.03, 0, 0, 0.97, 1.2 if v["part"] == "head" else 1.0, 1)],
          material="Cloth", sounds=CLOTH, data=bed_data(True, strap=True), inventory=["*-head-north"])
    block("l14-curtain", [("part", ["lower", "upper"]), ("side", SIDES)], lambda v: A.curtain(v["part"]),
          "Level 14's wards: a pale green privacy curtain, drawn, hanging from a ceiling track along the block's <side> edge (upper: the "
          "track on drop rods reaching a block up, the mesh band; lower: the curtain to its hem). Walk-through",
          boxes=None, sel=[(0, 0, 0, 1, 1, 0.12)], material="Cloth", sounds=CLOTH, data={"resistance": 0.5})
    block("l14-overbed", [("side", SIDES)], lambda v: A.overbed(),
          "Level 14's wards: an over-bed table, a paper cup and a jug left on it", boxes=[(0.06, 0, 0.18, 0.94, 0.9, 0.82)],
          material="Metal", sounds=METAL)
    block("l14-monitor", [("state", ["on", "off"]), ("side", SIDES)], lambda v: R4.monitor(v["state"] == "on"),
          "Level 14's wards: a vital-signs monitor on a wheeled pole, its screen to <side>; on: an ECG trace still running",
          boxes=[(0.15, 0, 0.15, 0.85, 1, 0.85)], material="Metal", sounds=METAL, data={"lightHsvByType": {"*-on-*": GREEN4}})
    block("l14-ventilator", [("side", SIDES)], lambda v: A.ventilator(), "Level 14's wards: an ICU ventilator on a wheeled stand, its "
          "face to <side>, hoses looped out of it", boxes=[(0.06, 0, 0.12, 0.94, 1, 0.85)], material="Metal", sounds=METAL)
    block("l14-crib", [("side", SIDES)], lambda v: A.crib(), "Level 14's maternity unit: a bassinet, a clear tub on a white trolley, a "
          "pink blanket left in it", boxes=[(0.06, 0, 0.1, 0.94, 0.9, 0.9)], material="Metal", sounds=METAL)
    block("l14-teddy", [("side", SIDES)], lambda v: A.teddy(), "Level 14's maternity unit: a worn stuffed teddy bear sitting, facing "
          "<side>. Walk-through", boxes=None, sel=[(0.25, 0, 0.15, 0.75, 0.72, 0.72)], material="Cloth", sounds=CLOTH,
          data={"resistance": 0.5})
    block("l14-desk2", [("side", SIDES)], lambda v: A.desk2(), "Level 14's wards: a white ward desk, its kneehole and a chair tucked in "
          "toward <side>, charts left on it", boxes=[(0.03, 0, 0.0, 0.97, 0.78, 0.94)], material="Wood", sounds=WOOD)
    block("l14-cabinet", [("part", ["lower", "upper"]), ("side", SIDES)], lambda v: A.cabinet(v["part"]),
          "Level 14's wards: a tall white medicine cabinet, two blocks, glazed doors toward <side>, bottles and pill tubs on its shelves",
          boxes=[(0.06, 0, 0.14, 0.94, 1, 0.97)], material="Metal", sounds=METAL,
          data={"dropsByType": {"*-lower-*": drops((BANDAGE, 0.4, 0.4), ("backrooms:l14-painkillers", 0.3, 0.3)), "*": []}})


def surgery():
    block("l14-optable", [("part", ["head", "foot"]), ("side", SIDES)], lambda v: R4.optable(v["part"]),
          "Level 14's surgery rooms: an operating table on its column, two blocks (head, foot; the foot lies from the head toward "
          "<side>), its top tilted head-down, the pads cracked and stained, strapped",
          boxes=lambda v: [(0.12, 0, 0, 0.88, 1.0 if v["part"] == "foot" else 0.85, 1)], material="Metal", sounds=METAL,
          inventory=["*-head-north"])
    block("l14-surglamp", [], lambda v: R4.surglamp(), "Level 14's surgery rooms: a surgical light, three lamp heads on arms, hanging in "
          "the top block of a room from the ceiling, lit. Walk-through", boxes=None, sel=[(0.12, 0.2, 0.12, 0.88, 1, 0.88)],
          material="Metal", sounds=METAL, data={"lightHsv": WHITE14})
    block("l14-trolley", [("state", ["clean", "rusty"]), ("side", SIDES)], lambda v: PB.trolley(v["state"]),
          "Level 14's surgery rooms: an instrument trolley laid with scalpels, syringes, forceps and a stethoscope, as if in use; rusty: "
          "gone to rust, the drape bloodied", boxes=[(0.06, 0, 0.12, 0.94, 0.85, 0.88)], material="Metal", sounds=METAL,
          data={"drops": drops(("backrooms:glassshard", 0.5, 0), ("backrooms:metalbracket", 0.5, 0.5))})
    block("l14-anaesthesia", [("side", SIDES)], lambda v: PB.anaesthesia(), "Level 14's surgery rooms: an anaesthesia machine, its "
          "flowmeters and gauges to <side>, the breathing bag and gas cylinders on it", boxes=[(0.03, 0, 0.15, 0.97, 1, 0.98)],
          material="Metal", sounds=METAL)
    block("l14-equipshelf", [("part", ["lower", "upper"]), ("side", SIDES)], lambda v: PB.equipshelf(v["part"]),
          "Level 14's surgery rooms: rusted steel shelving, two blocks, crowded with old and damaged surgical equipment, open to <side>",
          boxes=[(0.06, 0, 0.14, 0.94, 1, 0.94)], material="Metal", sounds=METAL)
    block("l14-tuberack", [("side", SIDES)], lambda v: PB.tuberack(), "Level 14's surgery rooms: racks of test tubes of coloured "
          "liquids on a small steel table, moss and tiny plants growing out of them", boxes=[(0.1, 0, 0.15, 0.9, 0.6, 0.85)],
          sel=[(0.1, 0, 0.15, 0.9, 1.0, 0.85)], material="Glass", sounds=GLASS)
    block("l14-vines", [], lambda v: PB.vines(), "Level 14's surgery rooms: vegetation spilling over the floor. Walk-through", boxes=None,
          sel=[(0, 0, 0, 1, 0.3, 1)], material="Plant", sounds=PLANT, data={"resistance": 0.3, "replaceable": 4000})
    block("l14-mouldfloor", [], lambda v: PB.mouldfloor(), "Level 14: a black-green mould carpet over the floor, a thin layer. "
          "Walk-through", boxes=None, sel=[(0, 0, 0, 1, 0.1, 1)], material="Plant", sounds=SOFT, data={"resistance": 0.3, "replaceable": 4000})


def torture():
    block("l14-stretchers", [("part", ["lower", "upper"]), ("side", SIDES)], lambda v: R4.stretchers(v["part"]),
          "Level 14's torture chambers: rusted stretchers stacked atop each other, askew, a block and a half high (lower, upper)",
          boxes=lambda v: [(0.12, 0, 0, 0.88, 1 if v["part"] == "lower" else 0.6, 1)], material="Metal", sounds=METAL)
    block("l14-knifecab", [("part", ["lower", "upper"]), ("side", SIDES)], lambda v: PB.knifecab(v["part"]),
          "Level 14's torture chambers: a rusted metal cabinet, two blocks, its glazed doors toward <side> showing rows of knives, "
          "scalpels and razor blades", boxes=[(0.06, 0, 0.14, 0.94, 1, 0.97)], material="Metal", sounds=METAL,
          data={"dropsByType": {"*-lower-*": drops(("backrooms:scraper", 0.4, 0.4), ("backrooms:metalbracket", 0.6, 0)), "*": []}})
    block("l14-hook", [], lambda v: PB.hook(), "Level 14's torture chambers: rusted chains and a meat hook hanging in the top block of a "
          "room. Walk-through", boxes=None, sel=[(0.35, 0.05, 0.4, 0.75, 1, 0.75)], material="Metal", sounds=METAL)
    block("l14-bloodpool", [("side", SIDES)], lambda v: PB.bloodpool(), "Level 14's torture chambers: a pool of blood on the floor. Walk-through",
          boxes=None, sel=[(0, 0, 0, 1, 0.06, 1)], material="Other", sounds=SOFT, data={"resistance": 0.2, "replaceable": 4000})


def trg():
    block("l14-trgdesk", [("kind", ["papers", "radio", "samples"]), ("side", SIDES)], lambda v: PB.trgdesk(v["kind"]),
          "Level 14: the T.14.R.G.'s field desk, an olive steel table: their papers; their field radio; an open case of samples and a "
          "microscope", boxes=[(0.03, 0, 0.12, 0.97, 0.78, 0.88)], material="Metal", sounds=METAL)
    block("l14-samplerack", [("side", SIDES)], lambda v: PB.samplerack(), "Level 14: the T.14.R.G.'s rack of Compound 14, black vials "
          "with a dull sickly green glow", boxes=[(0.06, 0, 0.27, 0.94, 0.95, 0.75)], material="Glass", sounds=GLASS,
          data={"lightHsv": GREEN3, "drops": drops(("backrooms:glassshard", 1, 0))})
    block("l14-cell", [("part", ["lower", "upper"]), ("state", ["intact", "broken"]), ("side", SIDES)], lambda v: PB.cell(v["part"], v["state"]),
          "Level 14: a T.14.R.G. containment chamber's thick glass panel in a bolted steel frame along the block's <side> edge; "
          "broken: smashed out from beyond the glass, shards on this block's floor",
          boxes=lambda v: ([(0, 0, 0, 1, 1, 0.16)] if v["state"] == "intact" else
                           [(0, 0, 0, 0.11, 1, 0.16), (0.89, 0, 0, 1, 1, 0.16)] + ([(0, 0, 0, 1, 0.125, 0.16)] if v["part"] == "lower" else
                                                                                   [(0, 0.875, 0, 1, 1, 0.16)])),
          sel=lambda v: [(0, 0, 0, 1, 1, 0.16)] if v["state"] == "intact" or v["part"] == "upper" else [(0, 0, 0, 1, 1, 0.16), (0.1, 0, 0.16, 0.9, 0.05, 0.9)],
          material="Glass", sounds=GLASS, data={"resistance": 4})
    block("l14-crate", [("side", SIDES)], lambda v: PB.crate(), "Level 14: a T.14.R.G. supply crate, stencilled, from the colony's "
          "stockpile", boxes=[(0.06, 0, 0.09, 0.94, 0.85, 0.91)], material="Wood", sounds=WOOD,
          data={"drops": drops(("backrooms:crackers", 1, 1), ("backrooms:almondwater", 0.6, 0.6), (BANDAGE, 0.5, 0.5))})
    block("l14-drum", [("state", ["sealed", "leaking"])], lambda v: PB.drum(v["state"]),
          "Level 14's contaminated rooms: a steel drum with the radiation trefoil; leaking: rusted through, glowing green ooze pooled "
          "round it", boxes=[(0.12, 0, 0.12, 0.88, 0.9, 0.88)], rot=None, material="Metal", sounds=METAL,
          data={"lightHsvByType": {"*-leaking": OOZE4}})


def halls():
    block("l14-station", [("part", ["counter", "computer", "corner"]), ("side", SIDES)], lambda v: PB.station(v["part"]),
          "Level 14's halls: a nurses' station, its front with a ledge toward <side>, the work surface behind (computer: a beige "
          "computer on it, facing the nurse); corner: an L, the counter running on east (same side) and south (side turned a quarter "
          "left: corner-north joins counter-north to its east and counter-west to its south)",
          boxes=lambda v: ([(0, 0, 0, 1, 1.06, 0.35), (0, 0, 0.35, 1, 0.75, 0.82)] if v["part"] != "corner" else
                           [(0, 0, 0, 1, 1.06, 0.35), (0, 0, 0.35, 0.35, 1.06, 1), (0.35, 0, 0.35, 1, 0.75, 0.82)]),
          sel=lambda v: [(0, 0, 0, 1, 1.1, 0.85)] if v["part"] != "corner" else [(0, 0, 0, 1, 1.1, 1)],
          material="Wood", sounds=WOOD)
    block("l14-linencart", [("side", SIDES)], lambda v: PB.linencart(), "Level 14's halls: a linen cart of folded sheets and blankets, "
          "a laundry sack", boxes=[(0.06, 0, 0.15, 0.94, 1, 0.85)], material="Cloth", sounds=CLOTH)
    block("l14-bench", [("side", SIDES)], lambda v: PB.bench(), "Level 14's halls: a bench of pale slats on a steel frame, facing <side>",
          boxes=[(0.03, 0, 0.15, 0.97, 0.5, 0.8)], sel=[(0.03, 0, 0.15, 0.97, 0.95, 0.82)], material="Wood", sounds=WOOD)


def round4():
    """Round 4 (2026-11-02): the gurney, wheelchair and drip stand of the level's own, the nurses' station back unit."""
    block("l14-gurney", [("part", ["head", "foot"]), ("kind", ["plain", "strap"]), ("side", SIDES)], lambda v: R4.gurney(v["part"], v["kind"]),
          "Level 14: a gurney two blocks long (head, foot; the foot lies from the head toward <side>): castors, hydraulic columns in "
          "bellows, the deck and mattress, the back rest raised, a rumpled sheet, one side rail up; strap: restraints and blood",
          boxes=[(0.18, 0, 0, 0.82, 0.8, 1)], sel=lambda v: [(0.15, 0, 0, 0.85, 1.05 if v["part"] == "head" else 0.85, 1)],
          material="Metal", sounds=METAL, inventory=["*-head-plain-north", "*-head-strap-north"])
    block("l14-wheelchair", [("side", SIDES)], lambda v: R4.wheelchair(),
          "Level 14: a hospital wheelchair facing <side>: spoked wheels with push rims, castors, a cracked vinyl sling seat",
          boxes=[(0.06, 0, 0.05, 0.94, 0.75, 0.95)], sel=[(0.03, 0, 0, 0.97, 1.0, 1)], material="Metal", sounds=METAL)
    block("l14-ivstand", [("side", SIDES)], lambda v: R4.ivstand(),
          "Level 14: a drip stand, a saline bag on its hook and the line to an infusion pump on the pole, the pump's panel to <side>",
          boxes=[(0.4, 0, 0.4, 0.6, 1, 0.6)], sel=[(0.15, 0, 0.15, 0.85, 1, 0.85)], material="Metal", sounds=METAL)
    block("l14-stationback", [("part", ["lower", "upper"]), ("kind", ["board", "files"]), ("side", SIDES)],
          lambda v: R4.stationback(v["part"], v["kind"]),
          "Level 14: the back wall unit of a nurses' station, two blocks, its front to <side> and its back against a wall: a cupboard, "
          "a worktop with a phone and charts, pigeonholes (lower); a whiteboard of names or a rack of chart binders (upper)",
          boxes=lambda v: [(0, 0, 0.38, 1, 0.6, 1)] if v["part"] == "lower" else [(0, 0, 0.8, 1, 1, 1)],
          sel=lambda v: [(0, 0, 0.38, 1, 1, 1)] if v["part"] == "lower" else [(0, 0, 0.7, 1, 1, 1)],
          material="Wood", sounds=WOOD, inventory=["*-lower-board-north", "*-upper-board-north", "*-upper-files-north"])
    block("l14-locker", [("part", ["lower", "upper"]), ("state", ["closed", "ajar"]), ("side", SIDES)],
          lambda v: R4.locker(v["part"], v["state"] == "ajar"),
          "Level 14's staff rooms: a pair of grey-green staff lockers, two blocks high, fronts to <side>, louvred, one padlocked; "
          "ajar: the left one swung open, a shirt on its hook", boxes=[(0, 0, 0.17, 1, 1, 1)], material="Metal", sounds=METAL,
          inventory=["*-lower-closed-north", "*-upper-closed-north"])
    # A dead vending machine in the reception rooms: the mod's own broken one (shapes/block/detail/brokenvending.json), as a
    # block of the level's that drops only a stale soft drink now and then (the mod's drops a meal; balance is not ours)
    K.write_json(os.path.join(K.BLOCKS, "l14-vending.json"), {
        "code": "l14-vending", "variantgroups": [{"code": "side", "states": SIDES}],
        "shapeByType": {f"*-{sd}": {"base": "block/detail/brokenvending", "rotateY": K.ROTATE[sd]} for sd in SIDES},
        "creativeinventory": {"general": ["*-north"], "backrooms": ["*-north"]},
        "blockmaterial": "Metal", "drawtype": "json", "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0,
        "resistance": 4, "sounds": METAL, "collisionbox": {"x1": 0.05, "y1": 0, "z1": 0.1, "x2": 0.95, "y2": 1, "z2": 0.95},
        "selectionbox": {"x1": 0.05, "y1": 0, "z1": 0.1, "x2": 0.95, "y2": 1, "z2": 0.95},
        "drops": drops(("backrooms:l14-stalesoda", 0.4, 0.4), ("backrooms:glassshard", 0.5, 0.5))},
        "Level 14's reception rooms: a dead vending machine (the mod's broken vending machine), its glass smashed, long since emptied")
    K.CODES.append("l14-vending")


def check():
    problems = []
    for name in K.SHAPE_FILES:
        data = json.load(open(os.path.join(K.SHAPES, name + ".json"), encoding="utf-8"))
        used = {f["texture"][1:] for e in data["elements"] for f in e["faces"].values()}
        for k in used:
            if k not in data["textures"]:
                problems.append(f"{name}: #{k} undefined")
            elif not os.path.exists(os.path.join(TX.TEX, k + ".png")):
                problems.append(f"{name}: texture {k} missing")
    for code in K.CODES:
        raw = open(os.path.join(K.BLOCKS, code + ".json"), encoding="utf-8").read()
        data = json.loads(re.sub(r"^//.*$", "", raw, flags=re.M))
        shapes = [data["shape"]] if "shape" in data else list(data["shapeByType"].values())
        for s in shapes:
            if "block/14/" not in s["base"]:
                continue  # a shared shape (round 4's vending machine)
            path = os.path.join(K.SHAPES, s["base"].split("block/14/")[1] + ".json")
            if not os.path.exists(path):
                problems.append(f"{code}: shape {s['base']} missing")
    for p in problems:
        print("CHECK:", p)
    return not problems


def main():
    K.CODES.clear()
    K.SHAPE_FILES.clear()
    written = TX.textures()
    R4.textures()
    R4.locker_textures()
    reception()
    wards()
    surgery()
    torture()
    trg()
    halls()
    round4()
    ok = check()
    print(f"gen_14_props: {len(K.CODES)} block types, {len(K.SHAPE_FILES)} shapes, {len(written)} textures, {'ok' if ok else 'PROBLEMS'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
