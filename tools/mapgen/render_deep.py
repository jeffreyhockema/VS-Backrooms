import os, struct, sys, re
from PIL import Image
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src', 'Worldgen', 'Tiles.cs'), encoding='utf-8').read()
def enum(name):
    body = src[src.index('enum ' + name):]
    body = body[body.index('{') + 1:body.index('}')]
    body = re.sub(r'//.*', '', body)
    return [m for m in re.findall(r'^\s*([A-Z]\w*)\s*[,=]?', body, re.M)]
FK = enum('FloorKind'); WP = enum('WallPattern'); TK = enum('TileKind')
props = {m[0]: int(m[1]) for m in re.findall(r'public const byte (\w+) = (\d+);', src[src.index('class Props'):src.index('class Decor')])}
P = {v: k for k, v in props.items()}
FC = {'Lawn': (70, 110, 50), 'Grass': (90, 130, 60), 'Field': (120, 90, 55), 'Stubble': (190, 170, 100), 'DirtRoad': (140, 110, 75),
      'DirtTracks': (120, 95, 65), 'Asphalt': (50, 52, 56), 'AsphaltLeaves': (70, 60, 45), 'AsphaltWet': (40, 44, 52), 'AsphaltLine': (220, 200, 60),
      'AsphaltCrossing': (225, 225, 225), 'Manhole': (20, 20, 20), 'Sidewalk': (165, 162, 155), 'Driveway': (185, 182, 175), 'Porch': (170, 130, 90),
      'HouseWood': (150, 100, 60), 'HouseCarpet': (130, 115, 100), 'HouseTile': (220, 225, 230), 'HouseLino': (210, 180, 140), 'HouseRug': (150, 50, 60),
      'Garage': (120, 120, 118), 'PoolDeep': (90, 160, 200), 'PoolEdge': (210, 205, 190), 'Flowerbed': (90, 60, 40)}
WC = {'SidingWhite': (235, 232, 225), 'SidingBlue': (110, 140, 180), 'SidingYellow': (225, 205, 130), 'SidingGreen': (130, 170, 130),
      'Brick': (150, 70, 50), 'BarnRed': (150, 35, 25), 'BarnGrey': (130, 125, 115), 'Hedge': (30, 70, 30), 'Silo': (170, 175, 180), 'Rock': (90, 85, 80)}
PC = {'Tree': (20, 60, 20), 'Crop': (215, 185, 70), 'TallGrass': (110, 150, 70), 'Reeds': (100, 130, 60), 'HayBale': (230, 200, 90),
      'HayRoll': (235, 210, 100), 'Flowers': (230, 110, 170), 'Shrub': (40, 100, 40), 'Car': (60, 90, 200), 'CarPart': (60, 90, 200),
      'Tractor': (40, 140, 40), 'Streetlight': (255, 240, 150), 'PowerPole': (60, 40, 20), 'Vegetable': (60, 160, 60)}
d = open('tiles.bin', 'rb').read(); size = struct.unpack_from('<i', d, 0)[0]; n = size // 32; off = 4
img = Image.new('RGB', (size, size)); px = img.load()
for mz in range(n):
    for mx in range(n):
        for i in range(1024):
            k, fl, ce, flags, lvl, pat, var = d[off:off + 7]; off += 7
            x = mx * 32 + i % 32; z = mz * 32 + i // 32
            K = TK[k] if k < len(TK) else ''
            if K in ('Wall', 'Doorway', 'Door', 'ArchDoor', 'ArchWindow'):
                c = WC.get(WP[pat] if pat < len(WP) else '', (200, 190, 175) if WP[pat].startswith('Interior') else (90, 90, 90))
                if K == 'Doorway': c = tuple(int(v * 0.55) for v in c)
                if K == 'Door': c = (110, 60, 30)
            elif K == 'Bars': c = (150, 110, 70) if WP[pat] == 'Fence' else (60, 60, 60)
            elif K == 'Water': c = (40, 90, 160) if not (flags & 32) else (20, 40, 120)
            else:
                c = FC.get(FK[fl] if fl < len(FK) else '', (100, 100, 100))
                name = P.get(var)
                if var and name in PC: c = PC[name]
                elif var: c = (230, 140, 40)
            if flags & 1: c = (220, 40, 30)
            px[x, z] = c
scale = int(sys.argv[1]) if len(sys.argv) > 1 else 1
img.resize((size * scale, size * scale), Image.NEAREST).save(sys.argv[2] if len(sys.argv) > 2 else 'deep.png')
