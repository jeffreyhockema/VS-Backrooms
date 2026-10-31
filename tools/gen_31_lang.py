"""Level 31 (experimental): gathers the level's lines that the shared generators (gen_notes.py, gen_guide.py) append at
the end of lang/en.json into the level's own block (right after levelname-24, where gen_31_content.py writes its lines),
so that the level's lines stay together. Those generators update a key where it already is, so once moved the lines
stay put. Run after them:  python tools/gen_31_lang.py
"""
import json
import os
import re

EN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "backrooms", "lang", "en.json")
MOVE = re.compile(r'^\t"(note-l31-|notetitle-l31-|journal-track-l31"|guide-level31-)')
OURS = re.compile(r'^\t"(level-24\d\d|levelhint-24|levelname-24|[^"]*l31-[^"]*|journal-track-l31|guide-level31-[^"]*)"\s*:')


def main():
    with open(EN, encoding="utf-8") as f:
        lines = f.read().split("\n")
    moved = [l for l in lines if MOVE.match(l)]
    rest = [l for l in lines if not MOVE.match(l)]
    start = next(i for i, l in enumerate(rest) if l.startswith('\t"level-24"'))
    end = start
    while end + 1 < len(rest) and OURS.match(rest[end + 1]):
        end += 1
    moved = [l if l.rstrip().endswith(",") else l.rstrip() + "," for l in moved]
    rest[end + 1:end + 1] = moved
    text = "\n".join(rest)
    # (The file's last entry has no comma, and no blank line before the closing brace)
    text = re.sub(r",\s*\n\}\s*$", "\n}\n", text)
    json.loads(text)
    with open(EN, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"gen_31_lang: {len(moved)} lines moved into Level 31's block")


if __name__ == "__main__":
    main()
