"""The Hub's English text (for tools/gen_hub.py): level 17's title keys (replacing the scaffold's placeholders), the
sub-zone titles in the Hub's range (1701-1799), and the messages of hub-plan.md section 4.8. Block and item names are
added by the modules that make them.
"""
from gen_hub_kit import LANG


def generate():
    LANG.update({
        # The level, its sub-zones (title keys 1701-1799)
        "level-17": "The Hub",
        "levelhint-17": "Safe, cold, and nothing to eat. Every door is a level; almost none will open.",
        "levelname-17": "The Hub",
        "level-1701": "The Tower",
        "levelhint-1701": "You will only be let in once.",
        "levelname-1701": "The Tower",
        "level-1702": "The Far Tunnels",
        "levelhint-1702": "The lamps give out from here on. Nobody has mapped what lies beyond.",
        "levelname-1702": "The Hub",
        # Doors and keys
        "hub-door-locked": "Locked. Its key is somewhere in the level it leads to.",
        "hub-door-dead": "Locked. Whatever lies behind it, its key is nowhere you can go.",
        "hub-door-turn": "The key turns three times.",
        "hub-door-open": "The slab grinds aside.",
        "hub-arrive-oneway": "You look back. There is no door, only wall.",
        "hub-arrive": "The door shuts behind you on silence.",
        "hub-arrive-manifest": "The door is gone.",
        "hub-key-found": "This key hums faintly when you strike it.",
        "hub-key-near": "The key rings, close by.",
        "waypoint-hubdoor": "The door to {0}",
        "hub-pinkdoor-refused": "The ribbon will not come undone. It seems to be waiting for someone who has brought a friend.",
        "hub-pinkdoor-open": "The ribbon slips loose by itself, and the door swings open onto somewhere warm.",
        # The Tower
        "hub-tower-refused": "The door does not know you any more.",
        "hub-tower-forbidden": "These thresholds are forbidden to wanderers.",
        "hub-keymaster-1": "More intruders. Say what you want, quickly.",
        "hub-keymaster-2": "A key, then. Choose, and go.",
        "hub-keymaster-3": "Your door is this way. Do not come back.",
        "hub-keymaster-angry": "Put that down. Out.",
        "hub-keymaster-choose": "Choose a key",
        # The outposts
        "hub-register-read": "The M.E.G. door register: the open doors and the Tower are now on your map.",
        "hub-camp-sign": "Camp Amber: new here? Ask us.",
        # The Keymaster
        "item-creature-hub-keymaster": "The Keymaster",
        "creature-hub-keymaster": "The Keymaster",
    })
