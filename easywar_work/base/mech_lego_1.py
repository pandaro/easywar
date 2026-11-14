# Easy War - unita' "mech_lego_1": plasmabot bipede montato con i pezzi del kit "Kaiser's Legos".
# SCRIPT AUTONOMO: non usa easywar_lib.py. Secondo approccio da confrontare con quello procedurale:
# qui il modello e' un assemblaggio di pezzi pronti (ricetta nella tabella SPEC qui sotto) e la texture e' l'atlas del kit.
# Va in easywar_work/base/mech_lego_1.py. Il nome del file e' il nome dell'unita'.
#
# Cosa serve in easywar_work/legos/ (i file originali del kit):
#   legosv2.obj
#   lego2skin2048_2-2.png     (atlas 2048x2048)
#
# Cosa genera, secondo il canone dei nomi: mech_lego_1.s3o, mech_lego_11.png,
# mech_lego_12.png, mech_lego_1.lua e la definizione unita' units/base/mech_lego_1.lua
# (solo se manca). Poi consegna tutto nel gioco.
#
# Uso:
#   flatpak run org.blender.Blender --background --python /home/p/.spring/games/easywar.sdd/easywar_work/base/mech_lego_1.py | grep -E "LEGO|S3O_ROOT|DEPLOY|TRIANGOLI"
# Con parametri (JSON dopo "--"), per esempio:
#   ... mech_lego_1.py -- '{"target_height":36,"team_mode":"none","deploy":false}'
#
# Tutte le coordinate della ricetta sono nel sistema di Wings 3D usato dal kit: Y verso l'alto, fronte verso +Z,
# unita' del kit (il pezzo K072 e' un blocco 2 x 1.25 x 2). Le rotazioni sono in gradi, attorno al centro del pezzo.
# I pezzi grigi danno il corpo, i rossi diventano colore giocatore (alpha) nel motore.
# Disegno di partenza: mech con elmo largo, spallacci grandi, guanti grossi e gambe a trapezio, 26 pezzi, con un'arma
# per mano (canna in basso: quando l'avambraccio si alza in avanti, la canna segue l'asse di mira).
# NON verificato nel motore: orientamento, proporzioni, resa del colore squadra, canali di tex2, segno delle rotazioni.
import os, sys, re, json, math, struct, zlib, shutil
import numpy as np

HERE = None
try:
    HERE = os.path.abspath(__file__)
except NameError:
    if "--python" in sys.argv:
        HERE = os.path.abspath(sys.argv[sys.argv.index("--python") + 1])
    else:
        HERE = os.path.abspath("mech_lego_1.py")

P = {
    "kit_dir": None,            # None = easywar_work/legos (cartella sopra "base")
    "obj": "legosv2.obj",
    "atlas": "lego2skin2048_2-2.png",
    "target_height": 34.0,      # altezza in unita' del motore (il soldato e' 36, l'engineer 41, il K116 40)
    "yaw_deg": 180.0,           # come per le altre unita': Blender fronte -Y, poi 180 gradi
    "flip_v": True,             # il motore mostra le texture capovolte rispetto a Blender
    "tex_size": 2048,           # 2048 = atlas intero; 1024 = ridotto a meta' (meno memoria)
    # "red" = la parte rossa del kit diventa colore giocatore (alpha alta); "none" = nessun colore squadra
    "team_mode": "red",
    "out_dir": None,            # None = cartella "out" accanto allo script
    "deploy": True,
    "weapon": "mech_gun",       # nome dell'arma definita dentro la definizione dell'unita' (arma 1 = destra, 2 = sinistra)
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
if P["kit_dir"] is None:
    P["kit_dir"] = os.path.join(os.path.dirname(os.path.dirname(HERE)), "legos")
OUT = P["out_dir"] or os.path.join(os.path.dirname(HERE), "out")


# ---- ricetta del robot (sistema Wings: Y su, fronte +Z, unita' del kit) -----------------------------

# Nome dell'oggetto nell'obj per ogni pezzo e skin (dal catalogo kaiser_legos_catalogo.json).
KIT = {
    ("K020", "grey"): "Object191",
    ("K025", "grey"): "Object189",
    ("K047", "grey"): "Object210",
    ("K047", "red"): "Object34",
    ("K048", "grey"): "Object203",
    ("K062", "light"): "Object304",
    ("K062", "red"): "Object75",
    ("K068", "grey"): "Object222",
}

# Pezzi del modello (nomi unici, gerarchia). origine = posizione dell'articolazione, nello stesso sistema.
PIECES = {
    "base":   (None,    (0.0, 0.0, 0.0)),
    "head":   ("base",  (0.0, 8.1, 0.0)),
    "arm_l":  ("base",  (-3.2, 8.6, 0.0)),
    "arm_r":  ("base",  (3.2, 8.6, 0.0)),
    "fore_l": ("arm_l", (-4.0, 7.2, 0.0)),
    "fore_r": ("arm_r", (4.0, 7.2, 0.0)),
    "hand_l": ("fore_l", (-4.0, 5.0, 0.0)),
    "hand_r": ("fore_r", (4.0, 5.0, 0.0)),
    "leg_l":  ("base",  (-1.34, 5.5, 0.0)),
    "leg_r":  ("base",  (1.34, 5.5, 0.0)),
    "shin_l": ("leg_l", (-1.4, 3.4, 0.0)),
    "shin_r": ("leg_r", (1.4, 3.4, 0.0)),
    "foot_l": ("shin_l", (-1.4, 0.7, 0.0)),
    "foot_r": ("shin_r", (1.4, 0.7, 0.0)),
}

# (pezzo, codice kit, skin, centro (x, y, z), rotazione (x, y, z) in gradi, dimensioni finali (x, y, z) o None)
# Le dimensioni sono quelle DOPO la rotazione. Con ("pre", (x, y, z)) il pezzo viene stirato PRIMA di ruotarlo.
SPEC = [
    ('foot_r', 'K047', 'grey', (1.4, 0.35, 0.35), (0, 0, 0), (2.5, 0.7, 3.0)),
    ('shin_r', 'K048', 'grey', (1.4, 2.05, 0.0), (0, 0, 0), (2.3, 2.7, 2.2)),
    ('shin_r', 'K062', 'red', (1.4, 3.3, 1.0), (0, 0, 0), (1.3, 0.9, 0.3)),
    ('leg_r', 'K048', 'grey', (1.34, 4.5, 0.0), (0, 0, 180), (1.8, 2.1, 1.9)),
    ('arm_r', 'K047', 'red', (3.55, 8.9, 0.0), (0, 90, 0), (2.7, 2.6, 2.8)),
    ('arm_r', 'K020', 'grey', (3.8, 7.5, 0.0), (0, 0, 0), (0.9, 0.9, 0.9)),
    ('fore_r', 'K048', 'grey', (4.0, 6.2, 0.0), (0, 0, 0), (2.0, 2.5, 2.2)),
    ('fore_r', 'K062', 'red', (4.0, 5.7, 1.1), (0, 0, 0), (1.2, 0.8, 0.25)),
    ('hand_r', 'K020', 'grey', (4.0, 4.7, 0.0), (0, 0, 0), (1.0, 0.6, 1.0)),
    ('hand_r', 'K025', 'grey', (4.0, 3.6, 0.0), (0, 0, 0), (0.5, 1.9, 0.6)),
    ('foot_l', 'K047', 'grey', (-1.4, 0.35, 0.35), (0, 0, 0), (2.5, 0.7, 3.0)),
    ('shin_l', 'K048', 'grey', (-1.4, 2.05, 0.0), (0, 0, 0), (2.3, 2.7, 2.2)),
    ('shin_l', 'K062', 'red', (-1.4, 3.3, 1.0), (0, 0, 0), (1.3, 0.9, 0.3)),
    ('leg_l', 'K048', 'grey', (-1.34, 4.5, 0.0), (0, 0, 180), (1.8, 2.1, 1.9)),
    ('arm_l', 'K047', 'red', (-3.55, 8.9, 0.0), (0, -90, 0), (2.7, 2.6, 2.8)),
    ('arm_l', 'K020', 'grey', (-3.8, 7.5, 0.0), (0, 0, 0), (0.9, 0.9, 0.9)),
    ('fore_l', 'K048', 'grey', (-4.0, 6.2, 0.0), (0, 0, 0), (2.0, 2.5, 2.2)),
    ('fore_l', 'K062', 'red', (-4.0, 5.7, 1.1), (0, 0, 0), (1.2, 0.8, 0.25)),
    ('hand_l', 'K020', 'grey', (-4.0, 4.7, 0.0), (0, 0, 0), (1.0, 0.6, 1.0)),
    ('hand_l', 'K025', 'grey', (-4.0, 3.6, 0.0), (0, 0, 0), (0.5, 1.9, 0.6)),
    ('base', 'K025', 'grey', (0, 5.5, 0), (0, 0, 0), (3.2, 0.9, 1.6)),
    ('base', 'K020', 'grey', (0, 6.2, 0), (0, 0, 0), (1.7, 0.8, 1.5)),
    ('base', 'K048', 'grey', (0, 7.4, 0), (0, 0, 180), (3.9, 2.0, 2.8)),
    ('base', 'K062', 'red', (0, 7.3, 1.45), (0, 0, 0), (1.3, 1.1, 0.3)),
    ('head', 'K068', 'grey', (0, 9.5, 0.1), (0, 0, 0), (4.3, 2.8, 3.0)),
    ('head', 'K062', 'light', (0, 9.8, 1.6), (0, 0, 0), (2.4, 0.7, 0.3)),
]


# ---- parti senza Blender (si possono provare anche fuori) -------------------------------------

def parse_obj(path, wanted):
    # Legge vertici e facce solo degli oggetti richiesti. Gli indici di v/vt sono globali nel file.
    v, vt, cur, objs = [], [], None, {}
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("v "):
                v.append(tuple(float(x) for x in line.split()[1:4]))
            elif line.startswith("vt "):
                vt.append(tuple(float(x) for x in line.split()[1:3]))
            elif line.startswith("o "):
                cur = line[2:].strip()
                if cur in wanted:
                    objs[cur] = []
            elif line.startswith("f ") and cur in objs:
                objs[cur].append([tuple(int(x) - 1 for x in t.split("/")[:2]) for t in line.split()[1:]])
    return v, vt, objs


def rot_matrix(ax, ay, az):
    cx, sx = math.cos(math.radians(ax)), math.sin(math.radians(ax))
    cy, sy = math.cos(math.radians(ay)), math.sin(math.radians(ay))
    cz, sz = math.cos(math.radians(az)), math.sin(math.radians(az))
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return rz @ ry @ rx


def wings_to_blender(p):
    # Wings: Y su, fronte +Z. Blender: Z su, fronte -Y. Rotazione di 90 gradi attorno a X (verso preservato).
    return (p[0], -p[2], p[1])


def assemble(obj_path):
    # Ritorna (dimensioni finali X/Y/Z, scala, {pezzo: dati}) dove i dati sono vertici (relativi all'origine del pezzo,
    # gia' in Blender e in unita' del motore), poligoni (indici), UV per angolo (u, v) e posizione relativa al genitore.
    wanted = {KIT[(k, s)] for _, k, s, _, _, _ in SPEC}
    v, vt, objs = parse_obj(obj_path, wanted)
    missing = sorted(wanted - set(objs))
    if missing:
        raise RuntimeError("oggetti non trovati nell'obj: " + str(missing))
    placed = {}
    for piece, k, s, pos, rot, size in SPEC:
        faces = objs[KIT[(k, s)]]
        idx = sorted({i for f in faces for i, _ in f})
        pts = np.array([v[i] for i in idx])
        centre = (pts.max(0) + pts.min(0)) / 2.0
        pts = pts - centre
        if size and size[0] == "pre":
            pts = pts * (np.array(size[1]) / (pts.max(0) - pts.min(0)))
            pts = pts @ rot_matrix(*rot).T
        else:
            pts = pts @ rot_matrix(*rot).T
            if size:
                pts = pts * (np.array(size) / (pts.max(0) - pts.min(0)))
        pts = pts + np.array(pos)
        remap = {o: n for n, o in enumerate(idx)}
        placed.setdefault(piece, []).append((pts, [[(remap[i], t) for i, t in f] for f in faces]))
    allp = np.vstack([p for lst in placed.values() for p, _ in lst])
    lo, hi = allp.min(0), allp.max(0)           # sistema Wings
    height = hi[1] - lo[1]
    k = P["target_height"] / height
    cx, cz, y0 = 0.0, 0.0, lo[1]       # il robot e' simmetrico attorno a X = 0 e Z = 0 e' l'asse delle gambe: la base resta nell'origine

    def conv(p):   # Wings (kit) -> Blender in unita' del motore, piedi a terra, centrato
        return np.array(wings_to_blender(((p[0] - cx) * k, (p[1] - y0) * k, (p[2] - cz) * k)))

    origin = {n: conv(np.array(o)) for n, (_, o) in PIECES.items()}
    out = {}
    for name, (parent, _) in PIECES.items():
        verts, polys, uvs = [], [], []
        for pts, faces in placed.get(name, []):
            base = len(verts)
            for p in pts:
                verts.append(tuple(conv(p) - origin[name]))
            for f in faces:
                polys.append([base + i for i, _ in f])
                for _, t in f:
                    uvs.append(vt_of(vt, t))
        loc = origin[name] - (origin[parent] if parent else 0.0)
        out[name] = {"parent": parent, "loc": tuple(loc), "verts": verts, "polys": polys, "uvs": uvs}
    size = (float((hi[0] - lo[0]) * k), float((hi[2] - lo[2]) * k), float(height * k))
    return size, k, out


def vt_of(vt, t):
    u, w = vt[t]
    return (u, 1.0 - w if P["flip_v"] else w)


def make_tex1(rgb, mode, size):
    # rgb: array (h, w, 3) uint8, riga 0 = alto. Restituisce RGBA uint8 con alpha = maschera colore giocatore.
    if mode == "red":
        r = rgb[:, :, 0].astype(np.int32)
        rest = np.maximum(rgb[:, :, 1], rgb[:, :, 2]).astype(np.int32)
        a = np.clip((r - rest - 30) * 255 // 60, 0, 255).astype(np.uint8)
    else:
        a = np.zeros(rgb.shape[:2], np.uint8)
    out = np.dstack([rgb, a])
    if size and out.shape[0] != size:
        k = out.shape[0] // size
        out = out.reshape(size, k, size, k, 4).astype(np.float32).mean(axis=(1, 3)).round().astype(np.uint8)
    return out


def make_tex2(size=64):
    # Ipotesi da verificare: R = bagliore, G = riflessione. Qui bagliore 0, riflessione media, B 0.
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
            print("DEPLOY ATTENZIONE: la definizione non ha armi, la mira non partira'. Aggiungi questa riga dentro unitDef:")
            print("DEPLOY    (cancella il file e rilancia lo script: la ricrea con weapondefs e weapons)")
        return
    sx, sy, sz = size_xyz
    lines = [
        '-- Generata da mech_lego_1.py. Da rivedere: valori non verificati nel motore (movementclass, categoria, immagine).',
        'local unitName  =  "' + name + '"',
        '',
        'local unitDef  =  {',
        '   BuildPic = "Constructor.png", -- segnaposto',
        '   Category = "' + cat + '",',
        '   ObjectName = "base/' + name + '.s3o",',
        '   name = "Mech lego 1",',
        '   Side = "Vroomers",',
        '   UnitName = "Mech lego 1",',
        '   script = "base/' + name + '.lua",',
        '   icontype = "builder",',
        '   Description = "Mech con una arma per mano, montato con i pezzi del kit.",',
        '   MaxDamage = 500,',
        '   idleTime = 300,',
        '   idleAutoHeal = 0,',
        '   RadarDistance = 0,',
        '   SightDistance = 500,',
        '   SoundCategory = "TANK",',
        '   Upright = 1,',
        '   corpse = [[constructor_dead]],',
        '   BuildCostEnergy = 100,',
        '   BuildCostMetal = 100,',
        '   Buildtime = 100,',
        '   maxAcc = 0.35,',
        '   BrakeRate = 0.1,',
        '   FootprintX = 2,',
        '   FootprintZ = 2,',
        '   MaxSlope = 45,',
        '   MaxVelocity = 1.4,',
        '   MaxWaterDepth = 5,',
        '   MovementClass = "' + move + '",',
        '   TurnRate = 1000,',
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
        '   -- Arma modellata sull\'esempio "emg2". Tolti apposta: explosiongenerator e suoni dell\'esempio (file di un altro gioco,',
        '   -- qui potrebbero non esistere) e il danno "vtol". Da aggiungere quando ci sono i file giusti.',
        '   weapondefs = {',
        '      %s = {' % P["weapon"],
        '         areaofeffect = 8,',
        '         avoidfeature = false,',
        '         burst = 3,',
        '         burstrate = 0.1,',
        '         craterareaofeffect = 0,',
        '         craterboost = 0,',
        '         cratermult = 0,',
        '         cylindertargeting = 1,',
        '         edgeeffectiveness = 0.15,',
        '         firestarter = 100,',
        '         impulsefactor = 0.123,',
        '         intensity = 0.7,',
        '         name = "Mech hand plasma gun",',
        '         noselfdamage = true,',
        '         range = 180,',
        '         reloadtime = 0.3,',
        '         rgbcolor = "1 0.95 0.4",',
        '         size = 1.75,',
        '         sprayangle = 1180,',
        '         tolerance = 5000,',
        '         turret = true,',
        '         weapontimer = 0.1,',
        '         weapontype = "Cannon",',
        '         weaponvelocity = 500,',
        '         damage = {',
        '            default = 9,',
        '         },',
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


LUA = r"""-- Generato da mech_lego_1.py per l'unita' @NAME@. Non modificare a mano: viene riscritto.
-- Animazioni: camminata (gambe e braccia), mira e sparo con due armi (arma 1 = mano destra, arma 2 = mano sinistra).
-- Pezzi: base (torso), head, arm_l/r (spalla), fore_l/r (gomito), hand_l/r (polso + arma),
--        leg_l/r (anca), shin_l/r (ginocchio), foot_l/r (caviglia).
--
-- CONVENZIONE DEL SEGNO (dedotta dal test dell'engineer, dove un angolo positivo sull'asse x
-- ha portato il braccio indietro): sull'asse x un angolo NEGATIVO porta il pezzo in avanti.
-- Se nel gioco gambe e braccia vanno al contrario, basta mettere FWD = 1.

local base, head = piece('base', 'head')
local arm_l, arm_r = piece('arm_l', 'arm_r')
local fore_l, fore_r = piece('fore_l', 'fore_r')
local hand_l, hand_r = piece('hand_l', 'hand_r')
local leg_l, leg_r = piece('leg_l', 'leg_r')
local shin_l, shin_r = piece('shin_l', 'shin_r')
local foot_l, foot_r = piece('foot_l', 'foot_r')

local FWD = -1                 -- segno di "avanti" sull'asse x
local rad = math.rad
local STEP = 220               -- millisecondi per fase del passo (4 fasi = un passo completo)
local SPD = rad(170)           -- velocita' di rotazione durante il passo (radianti al secondo)
local AIM_SPD = rad(360)       -- velocita' del braccio quando mira
local REST_DELAY = 2500        -- dopo quanto tempo senza sparare le braccia tornano giu'

local SIG_WALK = 1
local SIG_AIM = { 2, 4 }       -- un segnale per arma
local SIG_REST = { 8, 16 }

local moving = false
local aiming = { false, false }    -- [1] = destra, [2] = sinistra
local ARM = { arm_r, arm_l }
local FORE = { fore_r, fore_l }
local HAND = { hand_r, hand_l }

-- Gira un pezzo sull'asse x: a > 0 = in avanti (il segno lo mette FWD).
local function X(p, a, spd)
  Turn(p, x_axis, FWD * rad(a), spd or SPD)
end

-- Una posa delle gambe: coscia, ginocchio (positivo = piegato) e piede tenuto piatto.
local function Leg(thigh, shin, foot, a_thigh, a_knee)
  X(thigh, a_thigh)
  X(shin, -a_knee)
  X(foot, a_knee - a_thigh)
end

-- Le braccia oscillano solo se quella mano non sta mirando.
local function Arms(a_right, a_left)
  if not aiming[1] then X(arm_r, a_right) end
  if not aiming[2] then X(arm_l, a_left) end
end

local function Walk()
  SetSignalMask(SIG_WALK)
  while true do
    -- 1: sinistra avanti, destra indietro e appoggiata
    Leg(leg_l, shin_l, foot_l, 25, 5)
    Leg(leg_r, shin_r, foot_r, -20, 10)
    Arms(18, -18)
    Sleep(STEP)
    -- 2: passaggio, la destra si stacca e si piega
    Leg(leg_l, shin_l, foot_l, 5, 0)
    Leg(leg_r, shin_r, foot_r, 10, 40)
    Arms(0, 0)
    Sleep(STEP)
    -- 3: destra avanti, sinistra indietro e appoggiata
    Leg(leg_r, shin_r, foot_r, 25, 5)
    Leg(leg_l, shin_l, foot_l, -20, 10)
    Arms(-18, 18)
    Sleep(STEP)
    -- 4: passaggio, la sinistra si stacca e si piega
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

-- ---- Armi: 1 = mano destra, 2 = mano sinistra -----------------------------------
-- A riposo l'arma punta in basso. Per mirare la spalla gira verso il bersaglio (heading) e il gomito
-- alza l'avambraccio di 90 gradi piu' l'inclinazione (pitch): la canna resta sull'asse di mira.
-- Funziona solo se la definizione dell'unita' ha due armi.

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

-- La spalla (con lo spallaccio) gira solo verso il bersaglio; e' il gomito che alza l'avambraccio e l'arma.
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

-- Rinculo: la mano con l'arma scatta indietro e torna.
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
    obj_path = os.path.join(P["kit_dir"], P["obj"])
    atlas_path = os.path.join(P["kit_dir"], P["atlas"])
    for p in (obj_path, atlas_path):
        if not os.path.exists(p):
            print("LEGO ERRORE: file del kit non trovato:", p)
            print("LEGO metti legosv2.obj e", P["atlas"], "in", P["kit_dir"])
            return

    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)

    # 1. Geometria: un oggetto Blender per pezzo, con genitore e posizione relativa
    size, k, data = assemble(obj_path)
    print("LEGO scala %.4f, dimensioni finali X/Y/Z %.1f %.1f %.1f" % ((k,) + size))
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
    print("LEGO pezzi:", len(objs), sorted(objs))

    # 2. Texture: atlas -> tex1 (con maschera colore giocatore) e tex2 piatta
    img = bpy.data.images.load(atlas_path)
    img.colorspace_settings.name = "Non-Color"
    w, h = img.size
    buf = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(buf)
    rgb = (buf.reshape(h, w, 4)[:, :, :3] * 255 + 0.5).astype(np.uint8)[::-1]   # riga 0 = alto
    print("LEGO atlas letto", w, "x", h, "| media RGB terzo sinistro:", rgb[:, :w // 3].reshape(-1, 3).mean(0).round(),
          "(attesa circa 240 78 78 se la lettura e' corretta)")
    tex1 = make_tex1(rgb, P["team_mode"], P["tex_size"])
    names = (NAME + "1.png", NAME + "2.png")
    paths = tuple(os.path.join(OUT, n) for n in names)
    write_png_rgba(paths[0], tex1)
    write_png_rgba(paths[1], make_tex2())
    print("LEGO texture scritte:", paths, "| pixel colore giocatore:", int((tex1[:, :, 3] > 127).sum()))

    # Materiale solo per l'anteprima in Blender (il motore usa i PNG)
    mat = bpy.data.materials.new(NAME)
    mat.use_nodes = True
    bsdf = [n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"][0]
    tn = mat.node_tree.nodes.new("ShaderNodeTexImage")
    tn.image = bpy.data.images.load(paths[0])
    mat.node_tree.links.new(tn.outputs["Color"], bsdf.inputs["Base Color"])
    for ob in objs.values():
        ob.data.materials.append(mat)

    # 3. Orientamento: rotazione del pezzo radice, poi radice S3O con compensazione
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

    # 4. Consegna nel gioco
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