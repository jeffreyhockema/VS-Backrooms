"""Renders city.bin (written by `mapgen <seed> <n> citymap [dx dz]`): buildings shaded by height and style, streets, props."""
import re
import struct
import sys

from PIL import Image

src = open(r'C:\Users\icebu\Documents\~Projects\VS Backrooms\src\Worldgen\Tiles.cs', encoding='utf-8').read()


def enum(name):
    body = src[src.index('enum ' + name):]
    body = body[body.index('{') + 1:body.index('}')]
    body = re.sub(r'//.*', '', body)
    body = re.sub(r'///.*', '', body)
    return [m for m in re.findall(r'^\s*([A-Z]\w*)\s*[,=]?', body, re.M)]


FK = enum('FloorKind'); WP = enum('WallPattern'); TK = enum('TileKind')
props = {}
for m in re.findall(r'public const byte (\w+) = (\d+);', src[src.index('class Props'):src.index('class Decor')]):
    props.setdefault(int(m[1]), m[0])
STYLE = {'CityGlass': (110, 150, 190), 'CityMirror': (25, 25, 32), 'CityBrick': (150, 70, 50), 'CityBrickDark': (100, 55, 45),
         'CityStone': (205, 190, 160), 'CityConcrete': (150, 150, 145), 'Drywall': (220, 220, 210), 'Hotel': (120, 40, 40),
         'CityPlaster': (225, 220, 205), 'SnackMall': (230, 200, 200), 'InteriorBeige': (215, 200, 170), 'FountainRim': (190, 185, 175),
         'Elevator': (200, 170, 60), 'Hedge': (30, 70, 30)}
FC = {'Sidewalk': (172, 170, 162), 'Asphalt': (52, 54, 58), 'AsphaltWet': (40, 44, 52), 'AsphaltCracked': (70, 70, 70),
      'AsphaltDoubleNS': (220, 190, 40), 'AsphaltDoubleWE': (220, 190, 40), 'AsphaltBayNS': (200, 200, 200), 'AsphaltBayWE': (200, 200, 200),
      'AsphaltCrossing': (230, 230, 230), 'AsphaltCrossingNS': (230, 230, 230), 'Manhole': (20, 20, 20), 'Lawn': (80, 125, 55),
      'ParkPath': (175, 160, 125), 'CityPlaza': (190, 185, 178), 'Field': (150, 120, 60), 'PoolDeep': (60, 130, 190),
      'Flowerbed': (110, 70, 50)}
PC = {'Tree': (25, 75, 25), 'Car': (60, 90, 200), 'CarPart': (60, 90, 200), 'Streetlight': (255, 240, 150), 'Crop': (215, 185, 70),
      'TrafficLight': (255, 60, 60), 'Vending': (60, 220, 220), 'VendorCart': (60, 220, 220), 'Bench': (130, 90, 50), 'BusShelter': (90, 160, 90)}
d = open('city.bin', 'rb').read()
size = struct.unpack_from('<i', d, 0)[0]
off = 4
img = Image.new('RGB', (size, size))
px = img.load()
for z in range(size):
    for x in range(size):
        k, fl, pat, var, depth, zone, under, detail, over, roof = d[off:off + 10]
        off += 10
        K = TK[k]
        P = WP[pat] if pat < len(WP) else ''
        if depth > 0 and K in ('Wall', 'Floor', 'Doorway', 'Door'):
            # A building seen from above: its roof, shaded by height
            base = STYLE.get(P, (160, 160, 160))
            top = roof if roof and (detail & 4) == 0 and depth > roof and (over == 0) else depth
            s = 0.45 + 0.55 * min(1.0, top / 80.0)
            c = tuple(int(v * s) for v in base)
            if K == 'Wall' and detail & 8: c = tuple(int(v * 0.7) for v in c)
            if K == 'Doorway': c = (255, 255, 255)
            if K == 'Door': c = (230, 120, 30)
            if K == 'Wall' and P == 'Elevator': c = (200, 170, 60)
        elif K == 'Wall':
            c = STYLE.get(P, (90, 90, 90))
            if zone == 16: c = (10, 10, 14)
        elif K == 'Bars':
            c = (20, 20, 20)
        elif K == 'Water':
            c = (40, 90, 160) if under != 15 else (10, 30, 110)
        elif K == 'Pit':
            c = (120, 0, 120) if under == 11 else (255, 0, 255)
        else:
            c = FC.get(FK[fl] if fl < len(FK) else '', (100, 100, 100))
            name = props.get(var)
            if var and name in PC: c = PC[name]
            elif var: c = (230, 140, 40)
            if over == 20 and not var: c = tuple(int(v * 0.6 + w * 0.4) for v, w in zip(c, (30, 90, 30)))
        if under == 14: c = (255, 0, 0)
        if under == 16: c = (255, 255, 0)
        if under == 13: c = (0, 255, 0)
        px[x, z] = c
scale = int(sys.argv[1]) if len(sys.argv) > 1 else 1
img.resize((size * scale, size * scale), Image.NEAREST).save(sys.argv[2] if len(sys.argv) > 2 else 'city.png')
