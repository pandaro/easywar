# Easy War - unita' "mech_script_3": mech pesante ciclope con gatling e cannone, generato solo da script.
# Derivato da mech_script_2.py: stessa pipeline, forme e palette nuove.
# Va in easywar_work/base/mech_script_3.py. Il nome del file e' il nome dell'unita'.
#
# Cosa genera: mech_script_3.s3o, mech_script_31.png, mech_script_32.png,
# mech_script_3.lua e la definizione unita' units/base/mech_script_3.lua (solo se manca). Poi consegna nel gioco.
#
# Uso:
#   flatpak run org.blender.Blender --background --python /home/p/.spring/games/easywar.sdd/easywar_work/base/mech_script_3.py | grep -E "MECH|S3O_ROOT|DEPLOY|TRIANGOLI"
#
# Disegno di partenza: mech pesante con torso massiccio, cockpit superiore, spallacci a pod cilindrici,
# braccio destro con gatling a 6 canne, braccio sinistro con cannone, gambe corte e piedi larghi con ruote.
# NON verificato nel motore: proporzioni, resa del colore squadra, canali di tex2.
import os, sys, re, json, math, struct, zlib, shutil
import numpy as np

HERE = None
try:
    HERE = os.path.abspath(__file__)
except NameError:
    if "--python" in sys.argv:
        HERE = os.path.abspath(sys.argv[sys.argv.index("--python") + 1])
    else:
        HERE = os.path.abspath("mech_script_3.py")

P = {
    "target_height": 36.0,
    "yaw_deg": 180.0,
    "flip_v": True,
    "tex_size": 256,
    "out_dir": None,
    "deploy": True,
    "weapon": "mech_gun",
    "game_dir": os.path.expanduser("~/.spring/games/easywar.sdd"),
    "dir_model": "objects3d/base",
    "dir_textures": "unittextures",
    "dir_script": "scripts/base",
}
NAME = os.path.splitext(os.path.basename(HERE))[0]
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
for a in argv:
    if a.strip().startswith("{"):
        P.update(json.loads(a))
    elif a.strip():
        NAME = a.strip()
OUT = P["out_dir"] or os.path.join(os.path.dirname(HERE), "out")


# ---- forme (tutto generato da qui: nessun file esterno) ---------------------------------------------

ZONES = {
    "armor":  (0.0, 0.5, 0.5, 1.0),
    "dark":   (0.5, 0.5, 1.0, 1.0),
    "team":   (0.0, 0.0, 0.5, 0.5),
    "accent": (0.5, 0.0, 1.0, 0.5),
}
COLORS = {"armor": (180, 185, 190), "dark": (40, 42, 48), "team": (210, 210, 215), "accent": (235, 120, 40)}


def loft(secs, ch=0.0):
    verts, rings = [], []
    for y, cx, cz, w, d in secs:
        if w == 0 and d == 0:
            rings.append([len(verts)]); verts.append((cx, y, cz)); continue
        hw, hd = w / 2.0, d / 2.0
        if ch > 0:
            a, b = hw * (1 - ch), hd * (1 - ch)
            pts = [(-a, -hd), (a, -hd), (hw, -b), (hw, b), (a, hd), (-a, hd), (-hw, b), (-hw, -b)]
        else:
            pts = [(-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd)]
        rings.append(list(range(len(verts), len(verts) + len(pts))))
        verts += [(cx + px, y, cz + pz) for px, pz in pts]
    faces = []
    for r0, r1 in zip(rings, rings[1:]):
        n = max(len(r0), len(r1))
        for i in range(n):
            j = (i + 1) % n
            if len(r0) == 1:
                faces.append([r0[0], r1[i], r1[j]])
            elif len(r1) == 1:
                faces.append([r0[i], r0[j], r1[0]])
            else:
                faces.append([r0[i], r0[j], r1[j], r1[i]])
    for r in (rings[0], rings[-1]):
        if len(r) > 1:
            faces.append(list(r))
    return verts, faces


def extrude(profile, layers):
    px = sum(p[0] for p in profile) / len(profile)
    py = sum(p[1] for p in profile) / len(profile)
    n = len(profile)
    verts, rings = [], []
    for z, s in layers:
        rings.append(list(range(len(verts), len(verts) + n)))
        verts += [(px + (x - px) * s, py + (y - py) * s, z) for x, y in profile]
    faces = []
    for r0, r1 in zip(rings, rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            faces.append([r0[i], r0[j], r1[j], r1[i]])
    for r, (z, s) in ((rings[0], layers[0]), (rings[-1], layers[-1])):
        c = len(verts); verts.append((px, py, z))
        for i in range(n):
            faces.append([c, r[i], r[(i + 1) % n]])
    return verts, faces


def circle(cx, cy, r, n=12):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def cyl_x(y, z, x0, x1, r, n=8):
    """Cilindro lungo l'asse X, centrato in (y,z) nel piano YZ."""
    verts, ring0, ring1 = [], [], []
    for i in range(n):
        a = 2 * math.pi * i / n
        cy = y + r * math.cos(a)
        cz = z + r * math.sin(a)
        ring0.append(len(verts)); verts.append((x0, cy, cz))
    for i in range(n):
        a = 2 * math.pi * i / n
        cy = y + r * math.cos(a)
        cz = z + r * math.sin(a)
        ring1.append(len(verts)); verts.append((x1, cy, cz))
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.append([ring0[i], ring0[j], ring1[j], ring1[i]])
    faces.append(list(reversed(ring0)))
    faces.append(list(ring1))
    return verts, faces


def cyl_z(x, y, z0, z1, r, n=8):
    """Cilindro lungo l'asse Z, centrato in (x,y) nel piano XY."""
    verts, ring0, ring1 = [], [], []
    for i in range(n):
        a = 2 * math.pi * i / n
        cx = x + r * math.cos(a)
        cy = y + r * math.sin(a)
        ring0.append(len(verts)); verts.append((cx, cy, z0))
    for i in range(n):
        a = 2 * math.pi * i / n
        cx = x + r * math.cos(a)
        cy = y + r * math.sin(a)
        ring1.append(len(verts)); verts.append((cx, cy, z1))
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.append([ring0[i], ring0[j], ring1[j], ring1[i]])
    faces.append(list(reversed(ring0)))
    faces.append(list(ring1))
    return verts, faces


# ---- il robot -------------------------------------------------------------------------------------

PIECES = {
    "base":    (None,    (0.0, 0.0, 0.0)),
    "head":    ("base",  (0.0, 34.0, -2.0)),
    "arm_r":   ("base",  (5.0, 26.0, 0.0)),
    "fore_r":  ("arm_r", (8.0, 20.0, 0.0)),
    "gatling": ("fore_r",(8.5, 16.0, 0.5)),   # arma destra
    "leg_r":   ("base",  (4.0, 16.0, 0.0)),
    "shin_r":  ("leg_r", (4.0, 10.0, 0.0)),
    "foot_r":  ("shin_r",(4.0, 4.0, 0.0)),
    "cannon":  ("fore_l",(-8.5, 16.0, 0.5)),  # arma sinistra (fore_l generato automaticamente)
}

PARTS = [
    # ---- TORSO ----
    ("base", "armor", loft([(16, 0, 0, 8, 6), (23, 0, 0, 10, 7), (30, 0, 0, 9, 6)], ch=0.2)),
    ("base", "dark",  extrude([(-4,28),(-2,30),(2,30),(4,28),(3,20),(-3,20)], [(2.5,0.9),(4.0,1.0)])),
    ("base", "dark",  loft([(22, -4.5, 0, 1.5, 3), (26, -4.5, 0, 1.5, 3)])),
    ("base", "dark",  loft([(22,  4.5, 0, 1.5, 3), (26,  4.5, 0, 1.5, 3)])),
    ("base", "armor", loft([(30, 0, -1, 6, 5), (34, 0, -2, 4, 4)], ch=0.1)),
    # ---- TESTA (sensore) ----
    ("head", "armor", loft([(34, 0, -2, 2, 2), (36, 0, -2, 1.5, 1.5)])),
    # ---- BRACCIO DESTRO (gatling) ----
    ("arm_r", "team",  cyl_x(26, 0, 4, 11, 4.5, 10)),          # pod spalla
    ("arm_r", "dark",  cyl_x(26, 0, 11, 11.5, 3.5, 6)),       # piastra esagonale esterna
    ("arm_r", "armor", loft([(24, 8, 0, 3, 3), (20, 8, 0, 2.5, 2.5)])),  # braccio superiore
    ("fore_r", "dark", cyl_x(20, 0, 7, 9.5, 1.8, 6)),          # giunto gomito
    ("fore_r", "armor", loft([(20, 8.5, 0.5, 3, 3.5), (16, 8.5, 0.5, 2.5, 3)])),  # avambraccio
    ("gatling", "dark", cyl_z(8.5, 14, 0.5, 4.5, 2.5, 8)),     # tamburo
    # 6 canne
    *[("gatling", "dark", cyl_z(8.5 + 1.2*math.cos(2*math.pi*i/6), 14 + 1.2*math.sin(2*math.pi*i/6),
                                4.5, 9, 0.5, 4)) for i in range(6)],
    # ---- BRACCIO SINISTRO (cannone) ----
    ("cannon", "armor", loft([(16, -8.5, 0.5, 3, 3.5), (12, -8.5, 1.5, 4, 4)])),  # corpo
    ("cannon", "dark",  cyl_z(-8.5, 13, 2, 9, 1.5, 8)),        # canna
    ("cannon", "dark",  cyl_z(-8.5, 13, 9, 10, 1.8, 6)),       # freno di bocca
    # ---- GAMBA DESTRA ----
    ("leg_r", "armor", loft([(16, 4, 0, 4, 5), (10, 4, 0, 3.5, 4.5)])),  # coscia
    ("shin_r", "dark", cyl_x(10, 0, 2, 6, 2.5, 8)),            # ginocchio
    ("shin_r", "armor", loft([(10, 4, 0, 3.5, 4), (4, 4, 0, 3, 3.5)])),  # gambale
    ("foot_r", "dark", cyl_x(4, 0, 3, 5, 1.5, 6)),             # caviglia
    ("foot_r", "armor", loft([(0, 4, 2, 6, 10), (2, 4, 2, 6, 10), (4, 4, 1, 5, 8)])),  # piede
    ("foot_r", "dark", cyl_x(2, 4, 0.5, 1.5, 1.2, 8)),         # ruota sinistra
    ("foot_r", "dark", cyl_x(2, 4, 6.5, 7.5, 1.2, 8)),         # ruota destra
]


def rot_matrix(ax, ay, az):
    cx, sx = math.cos(math.radians(ax)), math.sin(math.radians(ax))
    cy, sy = math.cos(math.radians(ay)), math.sin(math.radians(ay))
    cz, sz = math.cos(math.radians(az)), math.sin(math.radians(az))
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return rz @ ry @ rx


def to_blender(p):
    return (p[0], -p[2], p[1])


def all_parts():
    out = []
    for piece, zone, (verts, faces) in PARTS:
        sides = [(piece, 1.0)]
        if piece.endswith("_r"):
            sides.append((piece[:-2] + "_l", -1.0))
        for name, sx in sides:
            v = np.array(verts, dtype=float) * np.array([sx, 1.0, 1.0])
            c = v.mean(0)
            fs = []
            for f in faces:
                p = v[f]
                n = np.zeros(3)
                for i in range(len(f)):
                    a, b = p[i], p[(i + 1) % len(f)]
                    n += np.cross(a, b)
                if np.linalg.norm(n) < 1e-9:
                    continue
                fs.append(list(f) if np.dot(n, p.mean(0) - c) >= 0 else list(f)[::-1])
            out.append((name, zone, v, fs))
    return out


def piece_table():
    t = dict(PIECES)
    for name, (parent, o) in PIECES.items():
        if name.endswith("_r"):
            par = parent[:-2] + "_l" if parent and parent.endswith("_r") else parent
            t[name[:-2] + "_l"] = (par, (-o[0], o[1], o[2]))
    return t


def face_uvs(pts, zone, lo, hi):
    n = np.zeros(3)
    for i in range(len(pts)):
        n += np.cross(pts[i], pts[(i + 1) % len(pts)])
    ax = int(np.argmax(np.abs(n)))
    iu, iv = [(2, 1), (0, 2), (0, 1)][ax]
    u0, v0, u1, v1 = ZONES[zone]
    m = 0.06
    out = []
    for p in pts:
        a = (p[iu] - lo[iu]) / max(hi[iu] - lo[iu], 1e-6)
        b = (p[iv] - lo[iv]) / max(hi[iv] - lo[iv], 1e-6)
        u = u0 + (m + a * (1 - 2 * m)) * (u1 - u0)
        v = v0 + (m + b * (1 - 2 * m)) * (v1 - v0)
        out.append((u, 1.0 - v if P["flip_v"] else v))
    return out


def assemble():
    parts = all_parts()
    allp = np.vstack([v for _, _, v, _ in parts])
    lo, hi = allp.min(0), allp.max(0)
    k = P["target_height"] / (hi[1] - lo[1])
    y0 = lo[1]

    def conv(p):
        return np.array(to_blender((p[0] * k, (p[1] - y0) * k, p[2] * k)))

    table = piece_table()
    origin = {n: conv(np.array(o, dtype=float)) for n, (_, o) in table.items()}
    out = {n: {"parent": par, "loc": tuple(origin[n] - (origin[par] if par else 0.0)), "verts": [], "polys": [], "uvs": []}
           for n, (par, _) in table.items()}
    for name, zone, v, faces in parts:
        d = out[name]
        base = len(d["verts"])
        plo, phi = v.min(0), v.max(0)
        d["verts"] += [tuple(conv(p) - origin[name]) for p in v]
        for f in faces:
            d["polys"].append([base + i for i in f])
            d["uvs"] += face_uvs(v[f], zone, plo, phi)
    size = (float((hi[0] - lo[0]) * k), float((hi[2] - lo[2]) * k), float((hi[1] - lo[1]) * k))
    return size, k, out


def make_tex1(n):
    img = np.zeros((n, n, 4), np.uint8)
    for name, (u0, v0, u1, v1) in ZONES.items():
        x0, x1 = int(u0 * n), int(u1 * n)
        r0, r1 = int((1 - v1) * n), int((1 - v0) * n)
        h, w = r1 - r0, x1 - x0
        t = np.linspace(1.0, 0.0, h)[:, None] * np.ones((1, w))
        ex = np.minimum(np.arange(w), np.arange(w)[::-1])[None, :] / (0.12 * w)
        ey = np.minimum(np.arange(h), np.arange(h)[::-1])[:, None] / (0.12 * h)
        edge = np.clip(np.minimum(ex, ey), 0.0, 1.0)
        shade = (0.72 + 0.28 * t) * (0.80 + 0.20 * edge)
        col = np.array(COLORS[name], dtype=float)[None, None, :] * shade[:, :, None]
        img[r0:r1, x0:x1, :3] = np.clip(col, 0, 255).astype(np.uint8)
        img[r0:r1, x0:x1, 3] = 255 if name == "team" else 0
    return img


def make_tex2(size=64):
    t = np.zeros((size, size, 4), np.uint8)
    t[:, :, 1] = 128
    t[:, :, 3] = 255
    return t


def write_png_rgba(path, arr):
    h, w = arr.shape[:2]
    raw = np.zeros((h, w * 4 + 1), np.uint8)
    raw[:, 1:] = arr.reshape(h, w * 4)

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    data = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw.tobytes(), 6)) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(data)


def write_unitdef(name, size_xyz, move, cat):
    gd = P["game_dir"]
    target = os.path.join(gd, "units", "base", name + ".lua")
    if os.path.exists(target):
        print("DEPLOY unitdef gia' presente, non sovrascritta:", target)
        try:
            with open(target, encoding="utf-8") as f:
                has_weapons = re.search(r"\bweapons\s*=", f.read(), re.IGNORECASE) is not None
        except OSError:
            has_weapons = True
        if not has_weapons:
            print("DEPLOY ATTENZIONE: la definizione non ha armi, la mira non partira'.")
        return
    sx, sy, sz = size_xyz
    lines = [
        '-- Generata da mech_script_3.py. Da rivedere: valori non verificati nel motore.',
        'local unitName  =  "' + name + '"',
        '',
        'local unitDef  =  {',
        '   BuildPic = "Constructor.png",',
        '   Category = "' + cat + '",',
        '   ObjectName = "base/' + name + '.s3o",',
        '   name = "Mech script 3",',
        '   Side = "Vroomers",',
        '   UnitName = "Mech script 3",',
        '   script = "base/' + name + '.lua",',
        '   icontype = "builder",',
        '   Description = "Mech pesante con gatling e cannone.",',
        '   MaxDamage = 800,',
        '   idleTime = 300,',
        '   idleAutoHeal = 0,',
        '   RadarDistance = 0,',
        '   SightDistance = 500,',
        '   SoundCategory = "TANK",',
        '   Upright = 1,',
        '   corpse = [[constructor_dead]],',
        '   BuildCostEnergy = 150,',
        '   BuildCostMetal = 150,',
        '   Buildtime = 150,',
        '   maxAcc = 0.3,',
        '   BrakeRate = 0.1,',
        '   FootprintX = 2,',
        '   FootprintZ = 2,',
        '   MaxSlope = 45,',
        '   MaxVelocity = 1.2,',
        '   MaxWaterDepth = 5,',
        '   MovementClass = "' + move + '",',
        '   TurnRate = 800,',
        '   CanAttack = 1,',
        '   CanGuard = 1,',
        '   CanMove = 1,',
        '   CanPatrol = 1,',
        '   CanStop = 1,',
        '   LeaveTracks = 0,',
        '   Reclaimable = 0,',
        '   canSelfDestruct = 1,',
        '   repairable = 1,',
        '   collisionVolumeType = "box",',
        '   collisionVolumeOffsets = "0 0 0",',
        '   collisionVolumeScales = "%d %d %d",' % (round(sx), round(sz), round(sy)),
        '   BadTargetCategory = "NOTAIR",',
        '   explodeAs = [[MediumExplosion]],',
        '   selfDestructAs = [[MediumExplosion]],',
        '   NoChaseCategory = "AIR",',
        '   weapondefs = {',
        '      %s = {' % P["weapon"],
        '         areaofeffect = 10,',
        '         avoidfeature = false,',
        '         burst = 5,',
        '         burstrate = 0.08,',
        '         craterareaofeffect = 0,',
        '         craterboost = 0,',
        '         cratermult = 0,',
        '         cylindertargeting = 1,',
        '         edgeeffectiveness = 0.15,',
        '         firestarter = 100,',
        '         impulsefactor = 0.123,',
        '         intensity = 0.7,',
        '         name = "Mech heavy plasma gun",',
        '         noselfdamage = true,',
        '         range = 200,',
        '         reloadtime = 0.4,',
        '         rgbcolor = "1 0.9 0.3",',
        '         size = 2.0,',
        '         sprayangle = 1180,',
        '         tolerance = 5000,',
        '         turret = true,',
        '         weapontimer = 0.1,',
        '         weapontype = "Cannon",',
        '         weaponvelocity = 500,',
        '         damage = { default = 12 },',
        '      },',
        '   },',
        '   weapons = {',
        '      [1] = { def = "%s", onlytargetcategory = "NOTSUB" },' % P["weapon"],
        '      [2] = { def = "%s", onlytargetcategory = "NOTSUB" },' % P["weapon"],
        '   },',
        '}',
        '',
        'return lowerkeys({ [unitName]  =  unitDef })',
        '',
    ]
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("DEPLOY unitdef creata:", target, "| movementclass:", move, "| category:", cat)


def grab(path, key, default):
    try:
        with open(path, encoding="utf-8") as f:
            m = re.search(key + r'\s*=\s*"([^"]+)"', f.read(), re.IGNORECASE)
        return m.group(1) if m else default
    except OSError:
        return default


LUA = r"""-- Generato da mech_script_3.py per l'unita' @NAME@. Non modificare a mano: viene riscritto.
-- Animazioni: camminata, mira e sparo con due armi (1 = gatling destra, 2 = cannone sinistro).
-- Pezzi: base, head, arm_l/r, fore_l/r, gatling (destra), cannon (sinistra), leg_l/r, shin_l/r, foot_l/r.
--
-- CONVENZIONE DEL SEGNO: sull'asse x un angolo NEGATIVO porta il pezzo in avanti (FWD = -1).

local base, head = piece('base', 'head')
local arm_l, arm_r = piece('arm_l', 'arm_r')
local fore_l, fore_r = piece('fore_l', 'fore_r')
local gatling, cannon = piece('gatling', 'cannon')
local leg_l, leg_r = piece('leg_l', 'leg_r')
local shin_l, shin_r = piece('shin_l', 'shin_r')
local foot_l, foot_r = piece('foot_l', 'foot_r')

local FWD = -1
local rad = math.rad
local STEP = 220
local SPD = rad(170)
local AIM_SPD = rad(360)
local REST_DELAY = 2500

local SIG_WALK = 1
local SIG_AIM = { 2, 4 }
local SIG_REST = { 8, 16 }

local moving = false
local aiming = { false, false }
local ARM = { arm_r, arm_l }
local FORE = { fore_r, fore_l }
local HAND = { gatling, cannon }

local function X(p, a, spd)
  Turn(p, x_axis, FWD * rad(a), spd or SPD)
end

local function Leg(thigh, shin, foot, a_thigh, a_knee)
  X(thigh, a_thigh)
  X(shin, -a_knee)
  X(foot, a_knee - a_thigh)
end

local function Arms(a_right, a_left)
  if not aiming[1] then X(arm_r, a_right) end
  if not aiming[2] then X(arm_l, a_left) end
end

local function Walk()
  SetSignalMask(SIG_WALK)
  while true do
    Leg(leg_l, shin_l, foot_l, 25, 5)
    Leg(leg_r, shin_r, foot_r, -20, 10)
    Arms(18, -18)
    Sleep(STEP)
    Leg(leg_l, shin_l, foot_l, 5, 0)
    Leg(leg_r, shin_r, foot_r, 10, 40)
    Arms(0, 0)
    Sleep(STEP)
    Leg(leg_r, shin_r, foot_r, 25, 5)
    Leg(leg_l, shin_l, foot_l, -20, 10)
    Arms(-18, 18)
    Sleep(STEP)
    Leg(leg_r, shin_r, foot_r, 5, 0)
    Leg(leg_l, shin_l, foot_l, 10, 40)
    Arms(0, 0)
    Sleep(STEP)
  end
end

local function StandStill()
  for _, p in ipairs({ leg_l, leg_r, shin_l, shin_r, foot_l, foot_r }) do
    Turn(p, x_axis, 0, SPD)
  end
  Arms(0, 0)
end

function script.Create()
  Spring.Echo('[easywar] @NAME@ Create unitID=' .. tostring(unitID))
end

function script.StartMoving()
  if moving then return end
  moving = true
  Signal(SIG_WALK)
  StartThread(Walk)
end

function script.StopMoving()
  moving = false
  Signal(SIG_WALK)
  StandStill()
end

local function Rest(n)
  SetSignalMask(SIG_REST[n])
  Sleep(REST_DELAY)
  aiming[n] = false
  Turn(ARM[n], y_axis, 0, AIM_SPD / 2)
  Turn(ARM[n], x_axis, 0, AIM_SPD / 2)
  Turn(FORE[n], x_axis, 0, AIM_SPD / 2)
end

function script.AimFromWeapon(n)
  return FORE[n]
end

function script.QueryWeapon(n)
  return HAND[n]
end

function script.AimWeapon(n, heading, pitch)
  Signal(SIG_AIM[n])
  SetSignalMask(SIG_AIM[n])
  Signal(SIG_REST[n])
  aiming[n] = true
  Turn(ARM[n], x_axis, 0, AIM_SPD)
  Turn(ARM[n], y_axis, heading, AIM_SPD)
  Turn(FORE[n], x_axis, FWD * (rad(90) + pitch), AIM_SPD)
  WaitForTurn(ARM[n], y_axis)
  WaitForTurn(FORE[n], x_axis)
  StartThread(Rest, n)
  return true
end

function script.FireWeapon(n)
  Turn(HAND[n], x_axis, -FWD * rad(10), rad(900))
  Sleep(60)
  Turn(HAND[n], x_axis, 0, rad(240))
end

function script.Killed(recentDamage, maxHealth)
  return 1
end
""".replace("@NAME@", NAME)


# ---- parte Blender ------------------------------------------------------------------------------

def run_blender():
    import bpy, bmesh

    print("START", NAME, flush=True)
    os.makedirs(OUT, exist_ok=True)
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)

    size, k, data = assemble()
    print("MECH scala %.4f, dimensioni finali X/Y/Z %.1f %.1f %.1f" % ((k,) + size))
    objs = {}
    for name, d in data.items():
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(d["verts"], [], d["polys"])
        uv = mesh.uv_layers.new(name="UVMap")
        for li, uvc in enumerate(d["uvs"]):
            uv.data[li].uv = uvc
        mesh.update()
        ob = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(ob)
        bm = bmesh.new(); bm.from_mesh(mesh)
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        bm.to_mesh(mesh); bm.free()
        for p in mesh.polygons:
            p.use_smooth = False
        objs[name] = ob
    for name, d in data.items():
        if d["parent"]:
            objs[name].parent = objs[d["parent"]]
        objs[name].location = d["loc"]
    obj = objs["base"]
    print("MECH pezzi:", len(objs), sorted(objs))

    tex1 = make_tex1(P["tex_size"])
    names = (NAME + "1.png", NAME + "2.png")
    paths = tuple(os.path.join(OUT, n) for n in names)
    write_png_rgba(paths[0], tex1)
    write_png_rgba(paths[1], make_tex2())
    print("MECH texture scritte:", paths, "| pixel colore giocatore:", int((tex1[:, :, 3] > 127).sum()))

    mat = bpy.data.materials.new(NAME)
    mat.use_nodes = True
    bsdf = [n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"][0]
    tn = mat.node_tree.nodes.new("ShaderNodeTexImage")
    tn.image = bpy.data.images.load(paths[0])
    mat.node_tree.links.new(tn.outputs["Color"], bsdf.inputs["Base Color"])
    for ob in objs.values():
        ob.data.materials.append(mat)

    obj.rotation_euler = (0.0, 0.0, math.radians(P["yaw_deg"]))
    root = None
    op = None
    for mod in dir(bpy.ops):
        if mod.startswith("_"):
            continue
        try:
            m = getattr(bpy.ops, mod); nms = dir(m)
        except Exception:
            continue
        for nm in nms:
            if "s3o" in nm.lower() and "root" in nm.lower():
                op = getattr(m, nm); break
        if op:
            break
    if op is None:
        print("S3O_ROOT: operatore 'Add S3O Root' non trovato")
    else:
        before = set(bpy.data.objects.keys())
        print("S3O_ROOT", op("EXEC_DEFAULT", name=NAME, texture_name_1=names[0], texture_name_2=names[1]))
        new = [bpy.data.objects[n] for n in bpy.data.objects.keys() if n not in before]
        tops = [o for o in new if o.parent is None and o.type == "EMPTY"]
        if tops:
            root = tops[0]
            bpy.context.view_layer.update()
            obj.parent = root
            obj.matrix_parent_inverse = root.matrix_world.inverted()
            print("S3O_ROOT radice:", root.name)
    active = root or obj
    bpy.context.view_layer.objects.active = active
    for o in bpy.data.objects:
        o.select_set(o is active)

    s3o = os.path.join(OUT, NAME + ".s3o")
    try:
        print("S3O_ROOT export:", bpy.ops.s3o_tools.export_s3o("EXEC_DEFAULT", filepath=s3o),
              s3o, os.path.getsize(s3o) if os.path.exists(s3o) else "NON CREATO")
    except Exception as e:
        print("S3O_ROOT export errore:", e)
    lua_path = os.path.join(OUT, NAME + ".lua")
    with open(lua_path, "w", encoding="utf-8") as f:
        f.write(LUA)

    if P["deploy"]:
        gd = P["game_dir"]
        if not os.path.isdir(gd):
            print("DEPLOY saltato: cartella del gioco non trovata:", gd)
        elif not (os.path.exists(s3o) and os.path.getsize(s3o) > 0):
            print("DEPLOY saltato: il .s3o non e' stato creato")
        else:
            for src, dst in ((s3o, os.path.join(gd, P["dir_model"], NAME + ".s3o")),
                             (paths[0], os.path.join(gd, P["dir_textures"], names[0])),
                             (paths[1], os.path.join(gd, P["dir_textures"], names[1])),
                             (lua_path, os.path.join(gd, P["dir_script"], NAME + ".lua"))):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(src, dst)
                print("DEPLOY", dst, os.path.getsize(dst), "byte")
            sol = os.path.join(gd, "units", "base", "soldier.lua")
            write_unitdef(NAME, size, grab(sol, "movementclass", "Small Vechicle"),
                          grab(sol, "category", "TANK SMALL NOTAIR NOTSUB"))

    blend = os.path.join(OUT, NAME + ".blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend)
    print("BLENDER_VERSION", bpy.app.version_string)
    print("TRIANGOLI", sum(len(o.data.polygons) for o in objs.values()))
    print("SALVATO", blend)


if __name__ == "__main__":
    try:
        import bpy  # noqa
    except ImportError:
        bpy = None
    if bpy is not None:
        run_blender()
    else:
        print("Serve Blender: questo script va lanciato con 'blender --background --python'.")