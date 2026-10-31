#!/usr/bin/env python3
"""langcheck: everything a player can read has a friendly name.

Vintage Story shows the code itself when a lang entry is missing ("block-foo-bar", "backrooms:some-key",
"worldconfig-backroomsMenace-Very low"), so this checks every place a name is looked up:

  1. blocks, items, entities: every variant path (variantgroups expanded: states, loadFromProperties, allowedVariants)
     has `block-<path>` / `item-<path>` / `item-creature-<path>` in assets/backrooms/lang/en.json, exactly or through
     a wildcard key (the game's rule: one trailing `*` is a prefix match, any other `*` a regex, see TranslationService).
     Names that look like codes (lower case, hyphen, no space) are flagged too.
  2. world config: `worldattribute-<code>` (+ `-desc`) and `worldconfig-<code>-<name>` for every `names` entry, in the
     English and both Spanish worldconfig lang files; `playstyle-<langCode>` and `playstyle-desc-<langCode>`.
  3. code: every lang key in src (Say.T, Lang.Get/GetL/GetMatching/HasTranslation, RegisterHotKey, and any
     "backrooms:key" literal) carries the `backrooms:` domain (or is a key the game's own lang has) and exists.
  4. handbook and tutorial: every guide page's title/text key (GuideSystem.cs Added[]), and the tutorial step titles in
     assets/game/lang/en.json.

    python tools/langcheck.py              report; exit 1 on any finding
    python tools/langcheck.py --fix-list   also print a stub of the missing en.json keys to paste into a generator
    python tools/langcheck.py --es         also list backrooms keys the Spanish files lack (information, never a finding)

Pure Python 3, no third-party packages.
"""
import glob
import itertools
import json
import os
import re
import sys

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
ASSETS = os.path.join(REPO, "assets", "backrooms")


# ------------------------------------------------------------------ a tolerant JSON reader (comments, bare keys, trailing commas)

class _P:
    def __init__(self, s):
        self.s, self.i = s, 0

    def ws(self):
        s = self.s
        while self.i < len(s):
            c = s[self.i]
            if c in " \t\r\n\ufeff":
                self.i += 1
            elif s.startswith("//", self.i):
                j = s.find("\n", self.i)
                self.i = len(s) if j < 0 else j
            elif s.startswith("/*", self.i):
                j = s.find("*/", self.i + 2)
                self.i = len(s) if j < 0 else j + 2
            else:
                break

    def value(self):
        self.ws()
        c = self.s[self.i]
        if c == "{":
            self.i += 1
            o = {}
            while True:
                self.ws()
                if self.s[self.i] == "}":
                    self.i += 1
                    return o
                k = self.key()
                self.ws()
                if self.s[self.i] != ":":
                    raise ValueError("expected : at %d" % self.i)
                self.i += 1
                o[k] = self.value()
                self.ws()
                if self.s[self.i] == ",":
                    self.i += 1
        if c == "[":
            self.i += 1
            a = []
            while True:
                self.ws()
                if self.s[self.i] == "]":
                    self.i += 1
                    return a
                a.append(self.value())
                self.ws()
                if self.s[self.i] == ",":
                    self.i += 1
        if c in "\"'":
            return self.string()
        m = re.compile(r"[^\s,\]\}:]+").match(self.s, self.i)
        if not m:
            raise ValueError("bad token at %d" % self.i)
        self.i = m.end()
        w = m.group(0)
        if w == "true":
            return True
        if w == "false":
            return False
        if w == "null":
            return None
        try:
            return int(w)
        except ValueError:
            try:
                return float(w)
            except ValueError:
                return w

    def key(self):
        if self.s[self.i] in "\"'":
            return self.string()
        m = re.compile(r"[A-Za-z0-9_$.\-]+").match(self.s, self.i)
        if not m:
            raise ValueError("bad key at %d" % self.i)
        self.i = m.end()
        return m.group(0)

    def string(self):
        q = self.s[self.i]
        self.i += 1
        out = []
        while self.s[self.i] != q:
            c = self.s[self.i]
            if c == "\\":
                n = self.s[self.i + 1]
                if n == "u":
                    out.append(chr(int(self.s[self.i + 2:self.i + 6], 16)))
                    self.i += 6
                    continue
                out.append({"n": "\n", "t": "\t", "r": "\r", "b": "\b", "f": "\f"}.get(n, n))
                self.i += 2
            else:
                out.append(c)
                self.i += 1
        self.i += 1
        return "".join(out)


def read_json(path):
    with open(path, encoding="utf-8-sig") as f:
        text = f.read()
    return _P(text).value()


def read_lang(path):
    """A lang file: JSON with optional leading // lines (the Spanish files)."""
    if not os.path.exists(path):
        return {}
    return read_json(path)


# ------------------------------------------------------------------ the game's wildcard rule

class LangIndex:
    def __init__(self, entries):
        self.exact, self.prefix, self.regex = {}, {}, []
        for k, v in entries.items():
            if "*" not in k:
                self.exact[k] = v
            elif k.count("*") == 1 and k.endswith("*"):
                self.prefix[k[:-1]] = v
            else:
                self.regex.append((re.compile("^" + re.escape(k).replace(r"\*", "(.*)") + "$"), v))

    def match(self, key):
        """The text the game would show for `key` (GetMatching), or None."""
        if key in self.exact:
            return self.exact[key]
        for p, v in self.prefix.items():
            if key.startswith(p):
                return v
        for rx, v in self.regex:
            if rx.match(key):
                return v
        return None

    def has_prefix(self, p):
        return any(k.startswith(p) for k in self.exact) or any(k.startswith(p) or p.startswith(k) for k in self.prefix)


def game_dir():
    d = os.environ.get("VINTAGE_STORY") or r"G:\Games\Vintagestory"
    return d if os.path.isdir(d) else None


# ------------------------------------------------------------------ 1. blocks, items, entities

_props_cache = {}


def load_properties(ref):
    """worldproperties states for a loadFromProperties reference ("block/wood", "game:block/wood")."""
    if ref in _props_cache:
        return _props_cache[ref]
    domain, _, path = ref.rpartition(":")
    roots = [os.path.join(REPO, "assets", domain or "backrooms")] if domain != "game" else []
    gd = game_dir()
    if gd:
        roots += [os.path.join(gd, "assets", d) for d in ([domain] if domain else []) + ["game", "survival", "creative"]]
    roots.append(ASSETS)
    states = None
    for r in roots:
        f = os.path.join(r, "worldproperties", path + ".json")
        if os.path.exists(f):
            try:
                d = read_json(f)
            except (ValueError, IndexError):
                continue
            states = [v["code"] if isinstance(v, dict) else v for v in d.get("variants", [])]
            break
    _props_cache[ref] = states
    return states


def wild(pattern, s):
    pattern = pattern.split(":")[-1]
    return re.match("^" + re.escape(pattern).replace(r"\*", ".*") + "$", s) is not None


def expand(doc, notes, where):
    """Variant paths of a block/item/entity definition."""
    code = doc.get("code")
    if not isinstance(code, str):
        return []
    groups = doc.get("variantgroups") or []
    lists = []
    for g in groups:
        if not isinstance(g, dict):
            continue
        for extra in set(g) - {"code", "states", "loadFromProperties"}:
            notes.append("%s: variantgroup %s uses %s, which langcheck does not expand" % (where, g.get("code"), extra))
        if "states" in g:
            st = [str(s) for s in g["states"]]
        elif "loadFromProperties" in g:
            st = load_properties(g["loadFromProperties"])
            if st is None:
                notes.append("%s: cannot find worldproperties %s (its variants are not checked)" % (where, g["loadFromProperties"]))
                st = ["?"]
        else:
            notes.append("%s: variantgroup %s has no states" % (where, g.get("code")))
            st = ["?"]
        lists.append(st)
    paths = ["-".join([code] + list(c)) for c in itertools.product(*lists)] if lists else [code]
    allowed, skip = doc.get("allowedVariants"), doc.get("skipVariants")
    if isinstance(allowed, list):
        paths = [p for p in paths if any(wild(a, p) for a in allowed)]
    if isinstance(skip, list):
        paths = [p for p in paths if not any(wild(s, p) for s in skip)]
    return paths


def generator_for(code, src_file, gens):
    """The generator that writes this asset: the one naming its file, else the ones quoting its code."""
    base = os.path.basename(src_file)
    hits = [g for g, t in gens.items() if base in t or ("'%s'" % os.path.splitext(base)[0]) in t]
    if not hits:
        hits = [g for g, t in gens.items() if '"%s"' % code in t or "'%s'" % code in t]
    return ", ".join(hits[:3]) if hits else "none found (hand-written)"


ASSET_CODES = set()
CODEY = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)+$")


def check_assets(en, idx, problems, notes):
    gens = {}
    for f in sorted(glob.glob(os.path.join(REPO, "tools", "gen_*.py"))):
        try:
            gens[os.path.basename(f)] = open(f, encoding="utf-8", errors="replace").read()
        except OSError:
            pass
    kinds = [("blocktypes", "block-", "block"), ("itemtypes", "item-", "item"), ("entities", "item-creature-", "entity")]
    counts = {}
    coded = set()
    missing = {}   # key -> (kind, file, generator)
    for sub, prefix, kind in kinds:
        n = 0
        for f in sorted(glob.glob(os.path.join(ASSETS, sub, "**", "*.json"), recursive=True)):
            rel = os.path.relpath(f, REPO).replace("\\", "/")
            if "/projectile/" in rel:
                continue   # arrows and thrown things are never shown by name (no inventory stack, no hover text)
            try:
                doc = read_json(f)
            except (ValueError, IndexError) as e:
                problems.append(("parse", "%s: cannot read (%s)" % (rel, e)))
                continue
            if not isinstance(doc, dict) or doc.get("enabled") is False:
                continue
            for p in expand(doc, notes, rel):
                n += 1
                ASSET_CODES.add(p)
                ASSET_CODES.add(doc["code"])
                key = prefix + p
                text = idx.match(key)
                if text is None:
                    missing.setdefault(key, (kind, rel, generator_for(doc["code"], rel, gens)))
                elif CODEY.match(text) and (key, text) not in coded:
                    coded.add((key, text))
                    problems.append(("codey", "%s: %s -> \"%s\" looks like a code (%s)" % (rel, key, text, kind)))
        counts[kind] = n
    for key, (kind, rel, gen) in sorted(missing.items(), key=lambda kv: (kv[1][2], kv[1][1], kv[0])):
        problems.append(("unnamed", "%s: no name for %s (%s) [generator, maybe: %s]" % (rel, key, kind, gen)))
    notes.append("checked %d blocks, %d items, %d entities (variant paths)" % (counts["block"], counts["item"], counts["entity"]))
    return missing


LANGJSON_SKIP = {"code", "offBlock", "dispenses", "takes", "leavesBottle", "spearEntityCode", "item", "result", "block", "entity"}


def check_json_keys(idx, problems, stub):
    """Lang keys written in the assets themselves (dialogue, trade, entity name tags): "backrooms:key" strings."""
    def walk(o, name, out):
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, k, out)
        elif isinstance(o, list):
            for v in o:
                walk(v, name, out)
        elif isinstance(o, str) and name not in LANGJSON_SKIP:
            out.append(o)
    for f in glob.glob(os.path.join(ASSETS, "**", "*.json"), recursive=True):
        rel = os.path.relpath(f, REPO).replace("\\", "/")
        if "/lang/" in rel:
            continue
        try:
            doc = read_json(f)
        except (ValueError, IndexError):
            continue
        out = []
        walk(doc, "", out)
        for v in out:
            m = re.fullmatch(r"backrooms:([a-z0-9._\-]+)", v)
            if m and idx.match(m.group(1)) is None and m.group(1) not in ASSET_CODES:
                problems.append(("code", "%s: lang key %s has no entry in assets/backrooms/lang/en.json" % (rel, v)))
                stub["code"].append(m.group(1))


# ------------------------------------------------------------------ 2. world config

def check_worldconfig(problems, stub):
    wc = read_json(os.path.join(REPO, "worldconfig.json"))
    langdir = os.path.join(REPO, "assets", "game", "lang")
    files = ["worldconfig-en.json", "worldconfig-es-419.json", "worldconfig-es-es.json"]
    langs = {f: read_lang(os.path.join(langdir, f)) for f in files}
    for f, d in langs.items():
        if not d:
            problems.append(("worldconfig", "assets/game/lang/%s: missing or empty" % f))

    def need(key, why):
        for f in files:
            if key not in langs[f]:
                problems.append(("worldconfig", "assets/game/lang/%s: no %s (%s)" % (f, key, why)))
                if f == "worldconfig-en.json":
                    stub["worldconfig"].append(key)

    for a in wc.get("worldConfigAttributes", []):
        c = a["code"]
        need("worldattribute-" + c, "setting name")
        need("worldattribute-%s-desc" % c, "setting description")
        names, values = a.get("names") or [], a.get("values") or []
        if names and len(names) != len(values):
            problems.append(("worldconfig", "worldconfig.json: %s has %d names for %d values" % (c, len(names), len(values))))
        for n in names:
            need("worldconfig-%s-%s" % (c, n), "dropdown entry")
    for ps in wc.get("playstyles", []):
        lc = ps.get("langCode", ps["code"])
        need("playstyle-" + lc, "playstyle name")
        need("playstyle-desc-" + lc, "playstyle description")


# ------------------------------------------------------------------ 3. strings in code

CALL = re.compile(r"""(?:Say\.T|Tell|Lang\.(?:Get|GetL|GetMatching|GetMatchingL|GetIfExists|HasTranslation|GetWithFallback)|RegisterHotKey)\s*\(""")
LIT = re.compile(r'"((?:[^"\\]|\\.)*)"')
DOMAINED = re.compile(r'"(backrooms:[^"]*)"')
# a literal handed to one of these is an asset code, not text
_W = "message msg text title said hint lang say chat label waypoint toast error tip prompt caption speak notification".split()
LANGCTX = re.compile(r"(?<![a-z])(?:%s)(?![a-z])" % "|".join(w + "|" + w.capitalize() for w in _W))
ASSETCALL = re.compile(r'(?:AssetLocation|GetBlock|GetItem|GetEntityType|GetBlockId|BlockId|Id|Is|Ours|L3999Block|L188Sided)\s*\(\s*\$?$')


def strip_comment(line):
    out, q, i = [], False, 0
    while i < len(line):
        c = line[i]
        if q:
            out.append(c)
            if c == "\\":
                out.append(line[i + 1:i + 2])
                i += 1
            elif c == '"':
                q = False
        else:
            if c == '"':
                q = True
            elif line.startswith("//", i):
                break
            out.append(c)
        i += 1
    return "".join(out)


def check_code(en, idx, game_en, asset_codes, problems, stub):
    keys = set(en)
    seen = set()
    for f in sorted(glob.glob(os.path.join(REPO, "src", "**", "*.cs"), recursive=True)):
        rel = os.path.relpath(f, REPO).replace("\\", "/")
        lines = open(f, encoding="utf-8-sig", errors="replace").read().split("\n")
        for n, raw in enumerate(lines, 1):
            line = strip_comment(raw)
            if not line.strip():
                continue
            # a) any "backrooms:key" literal must exist (a literal that is a prefix of a built key, or built with
            #    string concatenation/interpolation, must at least have a key under it)
            for m in DOMAINED.finditer(line):
                full = m.group(1)
                key = full[len("backrooms:"):]
                dynamic = "{" in key or key.endswith("-") or key.endswith("_") or re.match(r'\s*\+', line[m.end():]) is not None
                key = key.split("{")[0]
                # lang keys are lower case without a path; attribute names have capitals, assets a slash
                if not key or "/" in key or not re.fullmatch(r"[a-z0-9._\-]+", key) or ASSETCALL.search(line[:m.start()].rstrip("$")):
                    continue
                if not (LANGCTX.search(line) or CALL.search(line)):
                    continue   # an attribute name or an asset code (the capitals/slash/call rules above catch most), not text
                if dynamic:
                    ok = any(k.startswith(key) for k in keys)
                else:
                    ok = idx.match(key) is not None
                if not ok and (rel, n, key) not in seen:
                    seen.add((rel, n, key))
                    problems.append(("code", "%s:%d: %s has no entry in assets/backrooms/lang/en.json" % (rel, n, full)))
                    stub["code"].append(key)
            # b) literal keys passed to the lookup calls must carry the domain (or be a key of the game's own lang)
            for cm in CALL.finditer(line):
                args = line[cm.end():]
                is_hotkey = "RegisterHotKey" in cm.group(0)
                is_say = cm.group(0).startswith("Say.T")
                is_getl = cm.group(0).startswith("Lang.GetL")
                lits = list(LIT.finditer(args))
                if not lits:
                    continue
                # the key argument: first literal for Lang.Get*, the first literal after the player for Say.T/GetL
                # (those two take a player/language first and a key second; a literal as the first argument would be it)
                cand = lits[0] if not is_hotkey else (lits[1] if len(lits) > 1 else lits[0])
                if is_hotkey:
                    # RegisterHotKey(code, "description", ...): the description is the second argument
                    parts = args.split(",", 2)
                    if len(parts) > 1 and LIT.fullmatch(parts[1].strip()):
                        lit = LIT.fullmatch(parts[1].strip()).group(1)
                        problems.append(("code", "%s:%d: RegisterHotKey description \"%s\" is plain text; use Lang.Get(\"backrooms:...\")" % (rel, n, lit)))
                    continue
                if args.lstrip().startswith('"') or is_say or is_getl:
                    k = cand.group(1)
                    pre = args[:cand.start()]
                    # the literal must be the argument directly (not nested in another call/expression)
                    depth_ok = pre.count("(") == pre.count(")")
                    if not depth_ok or not (pre.strip() == "" or re.fullmatch(r"[\s\w.\[\]]*,\s*", pre)):
                        continue
                    if k.startswith("backrooms:") or k.startswith("game:") or k.startswith("survival:"):
                        continue
                    if ":" in k and re.match(r"^[a-z]+:", k):
                        continue
                    if k in game_en:
                        continue
                    if "{" in k or k == "":
                        continue
                    problems.append(("code", "%s:%d: lang key \"%s\" has no backrooms: domain (looked up in the game's own lang, it shows raw)" % (rel, n, k)))
                    stub["code"].append(k)


# ------------------------------------------------------------------ 4. handbook and tutorial

def check_guide(en, problems, stub):
    f = os.path.join(REPO, "src", "GuideSystem.cs")
    if os.path.exists(f):
        src = open(f, encoding="utf-8-sig").read()

        def block(name):
            m = re.search(r"\b" + name + r"\b[^=]*=\s*(?:new[^{]*)?\{(.*?)\n\s*\};", src, re.S)
            return m.group(1) if m else ""

        rewritten = re.findall(r'=\s*"([a-z0-9\-]+)"', block("Rewritten"))
        added = re.findall(r'"([a-z0-9\-]+)"', block("Added"))
        bridged = re.findall(r'=\s*"([a-z0-9\-]+)"', block("Bridged"))
        if not (rewritten and added and bridged):
            problems.append(("guide", "src/GuideSystem.cs: cannot find the Rewritten/Added/Bridged tables (langcheck needs updating)"))
        wanted = []
        for g in rewritten + added:
            wanted += ["guide-%s-title" % g, "guide-%s-text" % g]
        wanted += ["guide-bridge-%s" % b for b in bridged]
        for k in wanted:
            if k not in en:
                problems.append(("guide", "src/GuideSystem.cs: handbook text %s is not in assets/backrooms/lang/en.json" % k))
                stub["guide"].append(k)
    gl = read_lang(os.path.join(REPO, "assets", "game", "lang", "en.json"))
    tf = os.path.join(REPO, "src", "Tutorial", "BackroomsTutorial.cs")
    if os.path.exists(tf):
        t = open(tf, encoding="utf-8-sig").read()
        m = re.search(r'const string Code = "([^"]+)"', t)
        if m and "title-tutorial-" + m.group(1) not in gl:
            problems.append(("guide", "assets/game/lang/en.json: no title-tutorial-%s (the tutorial's handbook title)" % m.group(1)))
            stub["tutorial"].append("title-tutorial-" + m.group(1))
        for k in sorted(set(re.findall(r'Text\((\d+)\)', t)) | set(re.findall(r'Text\("([^"]+)"\)', t))):
            key = "tutorial-backrooms-" + k
            if key not in en:
                problems.append(("guide", "src/Tutorial/BackroomsTutorial.cs: step text %s is not in assets/backrooms/lang/en.json" % key))
                stub["tutorial"].append(key)
    for k, v in gl.items():
        if k.startswith("title-tutorial-") and (not v or CODEY.match(v)):
            problems.append(("guide", "assets/game/lang/en.json: %s -> \"%s\" looks like a code" % (k, v)))


# ------------------------------------------------------------------ main

def main(argv):
    problems, notes = [], []
    stub = {"block/item/entity": [], "worldconfig": [], "code": [], "guide": [], "tutorial": []}
    try:
        en = read_lang(os.path.join(ASSETS, "lang", "en.json"))
    except (ValueError, IndexError) as e:
        print("[parse] assets/backrooms/lang/en.json: %s" % e)
        return 1
    idx = LangIndex(en)
    gd = game_dir()
    game_en = read_lang(os.path.join(gd, "assets", "game", "lang", "en.json")) if gd else {}
    game_en = dict(game_en)
    game_en.update(read_lang(os.path.join(REPO, "assets", "game", "lang", "en.json")))
    if not gd:
        notes.append("game not found (VINTAGE_STORY): game-key and worldproperties checks are limited")

    for k, v in en.items():
        if not isinstance(v, str) or not v.strip():
            problems.append(("empty", "assets/backrooms/lang/en.json: %s has an empty value (the game treats it as missing and shows the key)" % k))
    for fn in ("es-419.json", "es-es.json"):
        for k, v in read_lang(os.path.join(ASSETS, "lang", fn)).items():
            if not isinstance(v, str) or not v.strip():
                problems.append(("empty", "assets/backrooms/lang/%s: %s has an empty value" % (fn, k)))
    missing = check_assets(en, idx, problems, notes)
    check_json_keys(idx, problems, stub)
    stub["block/item/entity"] = sorted(missing)
    check_worldconfig(problems, stub)
    check_code(en, idx, game_en, ASSET_CODES, problems, stub)
    check_guide(en, problems, stub)

    if "--es" in argv:
        for f in ("es-419.json", "es-es.json"):
            es = read_lang(os.path.join(ASSETS, "lang", f))
            lack = [k for k in en if k not in es]
            notes.append("backrooms/lang/%s lacks %d of %d en.json keys (information only)" % (f, len(lack), len(en)))

    by = {}
    for kind, msg in problems:
        by.setdefault(kind, []).append(msg)
    for kind in ("unnamed", "codey", "empty", "worldconfig", "code", "guide", "parse"):
        for msg in by.get(kind, []):
            print("[%s] %s" % (kind, msg))
    for n in notes:
        print("note: " + n)
    if "--fix-list" in argv:
        print("\n# stub of missing keys (paste into the generator that writes the asset, then give each a name)")
        for k, v in stub.items():
            for key in sorted(set(v)):
                print('\t"%s": "",   # %s' % (key, k))
    if problems:
        print("langcheck: %d problem(s)" % len(problems))
        return 1
    print("langcheck: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
