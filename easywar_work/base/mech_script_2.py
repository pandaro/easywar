# Easy War - unita' "mech_script_2": robot ciclope generato solo da script (nessun kit, nessun file esterno).
# Derivato da mech_script_1.py: stessa architettura, forme e palette nuove.
# Va in easywar_work/base/mech_script_2.py. Il nome del file e' il nome dell'unita'.
#
# Cosa genera, secondo il canone dei nomi: mech_script_2.s3o, mech_script_21.png, mech_script_22.png,
# mech_script_2.lua e la definizione unita' units/base/mech_script_2.lua (solo se manca). Poi consegna nel gioco.
#
# Uso:
#   flatpak run org.blender.Blender --background --python /home/p/.spring/games/easywar.sdd/easywar_work/base/mech_script_2.py | grep -E "MECH|S3O_ROOT|DEPLOY|TRIANGOLI"
# Con parametri (JSON dopo "--"), per esempio:
#   ... mech_script_2.py -- '{"target_height":38,"deploy":false}'
#
# Disegno di partenza: robot umanoide snello, testa a casco con un solo occhio circolare arancione,
# petto trapezoidale con pannello, vita segmentata scura, bacino trapezoidale, spallacci larghi e piatti,
# braccia con avambraccio piu' grosso e mani a pinza con cerchio arancione, gambe lunghe con ginocchiere
# a diamante scure e piedi tondi a ventosa.
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
        HERE = os.path.abspath("mech_script_2.py")

P = {
    "target_height": 36.0,      # altezza in unita' del motore
    "yaw_deg": 180.0,           # come per le altre unita': Blender fronte -Y, poi 180 gradi
    "flip_v": True,             # il motore mostra le texture capovolte rispetto a Blender
    "tex_size": 256,
    "out_dir": None,            # None = cartella "out" accanto allo script
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
# Sistema di lavoro: X destra, Y verso l'alto, Z verso il fronte. Unita' libere: alla fine tutto viene
# scalato per arrivare a target_height. Ogni forma ritorna (vertici, facce): le facce sono liste di indici.

ZONES = {   # rettangoli (u0, v0, u1, v1) di tex1, con v verso l'alto come in Blender
    "armor":  (0.0, 0.5, 0.5, 1.0),
    "dark":   (0.5, 0.5, 1.0, 1.0),
    "team":   (0.0, 0.0, 0.5, 0.5),    # alpha alta = colore giocatore
    "accent": (0.5, 0.0, 1.0, 0.5),
}
COLORS = {"armor": (190, 195, 200), "dark": (50, 52, 58), "team": (220, 220, 225), "accent": (235, 120, 40)}


def loft(secs, ch=0.0):
    # Sezioni orizzontali (y, cx, cz, larghezza, profondita') unite tra loro. Una sezione con larghezza e
    # profondita' 0 e' una punta. ch > 0 smussa gli angoli (sezioni a 8 lati): piu' sfaccettato.
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
    # Sagoma vista di fronte (punti x, y) ripetuta a varie profondita': layers = [(z, scala), ...].
    # La scala stringe la sagoma attorno al suo centro: e' quello che da' le facce inclinate.
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
    # Cerchio nel piano XY (vista frontale): usato per l'occhio e i cerchi arancioni delle mani.
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


# ---- il robot -------------------------------------------------------------------------------------
# Pezzi: nome -> (genitore, origine = articolazione). Le parti di destra hanno x > 0; quelle di sinistra
# sono lo specchio. PARTS: (pezzo, zona, forma). I pezzi che finiscono in "_r" vengono specchiati in "_l".
PIECES = {
    "base":   (None,    (0.0, 0.0, 0.0)),
    "head":   ("base",  (0.0, 28.5, 0.0)),
    "arm_r":  ("base",  (3.5, 26.5, 0.0)),
    "fore_r": ("arm_r", (5.5, 19.5, 0.0)),
    "hand_r": ("fore_r", (5.7, 14.0, 0.0)),
    "leg_r":  ("base",  (1.5, 18.0, 0.0)),
    "shin_r": ("leg_r", (2.0, 10.0, 0.0)),
    "foot_r": ("shin_r", (2.2, 1.5, 0.0)),
}

PARTS = [
    # testa: casco arrotondato + occhio a due dischi (scuro + iride arancione)
    ("head", "armor",  loft([(28.5, 0, 0, 1.4, 1.0), (29.5, 0, 0, 2.8, 2.4),
                             (31.5, 0, 0, 3.4, 2.8), (33.5, 0, 0, 3.0, 2.4),
                             (34.5, 0, 0, 1.8, 1.4)], ch=0.3)),
    ("head", "dark",   extrude(circle(0, 31.5, 1.1, 12), [(1.2, 1.0), (1.6, 0.8), (1.8, 0.3)])),
    ("head", "accent", extrude(circle(0, 31.5, 0.5, 10), [(1.5, 1.0), (1.9, 0.6)])),
    # collo
    ("base", "dark",   loft([(27.3, 0, 0, 0.9, 0.8), (28.7, 0, 0, 1.0, 0.9)])),
    # petto trapezoidale + pannello frontale
    ("base", "armor",  extrude([(-3.0, 27.5), (3.0, 27.5), (2.2, 21.5), (-2.2, 21.5)],
                                [(-1.3, 0.7), (-0.3, 1.0), (0.8, 1.0), (1.3, 0.6)])),
    ("base", "dark",   extrude([(-1.2, 26.5), (1.2, 26.5), (1.0, 23.5), (-1.0, 23.5)],
                                [(1.2, 1.0), (1.5, 0.85)])),
    # vita segmentata
    ("base", "dark",   loft([(19.0, 0, 0, 1.3, 1.1), (19.5, 0, 0, 1.1, 0.9),
                             (20.0, 0, 0, 1.3, 1.1), (20.5, 0, 0, 1.1, 0.9),
                             (21.0, 0, 0, 1.3, 1.1), (21.5, 0, 0, 1.1, 0.9)])),
    # bacino trapezoidale
    ("base", "armor",  extrude([(-1.2, 19.5), (1.2, 19.5), (2.2, 15.5), (-2.2, 15.5)],
                                [(-1.2, 0.7), (-0.2, 1.0), (1.0, 0.8)])),
    # spallaccio destro (largo e piatto, attaccato al braccio)
    ("arm_r", "team",  loft([(25.8, 4.2, 0, 2.6, 1.2), (26.3, 4.2, 0, 3.6, 1.5),
                             (27.2, 4.2, 0, 4.0, 1.6), (27.9, 4.2, 0, 3.2, 1.4),
                             (28.2, 4.2, 0, 2.3, 1.0)], ch=0.25)),
    # braccio destro sottile
    ("arm_r", "armor", loft([(26.0, 5.0, 0, 1.0, 1.0), (22.0, 5.2, 0, 0.9, 0.9),
                             (19.5, 5.5, 0, 0.8, 0.8)])),
    # avambraccio destro piu' grosso + pannello
    ("fore_r", "armor", loft([(19.5, 5.5, 0, 0.9, 0.9), (18.0, 5.5, 0, 1.3, 1.2),
                              (15.5, 5.6, 0, 1.5, 1.3), (14.0, 5.7, 0, 1.2, 1.1)])),
    ("fore_r", "dark",  extrude([(5.0, 17.5), (6.1, 17.5), (5.9, 15.5), (5.2, 15.5)],
                                [(0.6, 1.0), (0.9, 0.85)])),
    # mano destra: palmo + due dita a pinza + cerchio arancione
    ("hand_r", "dark",  loft([(14.0, 5.7, 0, 1.1, 1.0), (13.0, 5.7, 0, 1.3, 1.2),
                              (12.2, 5.7, 0, 1.1, 1.0)])),
    ("hand_r", "dark",  loft([(12.5, 6.2, 0, 0.6, 0.6), (11.5, 6.0, 0.1, 0.5, 0.5),
                              (10.3, 5.8, 0.2, 0, 0)])),
    ("hand_r", "dark",  loft([(12.5, 5.3, 0, 0.6, 0.6), (11.5, 5.4, 0.1, 0.5, 0.5),
                              (10.3, 5.6, 0.2, 0, 0)])),
    ("hand_r", "accent", extrude(circle(5.7, 13.0, 0.4, 10), [(0.6, 1.0), (0.9, 0.6)])),
    # gamba destra: coscia, ginocchiera a diamante, gambale, piede tondo
    ("leg_r", "armor",  loft([(18.0, 1.5, 0, 1.4, 1.4), (15.0, 1.7, 0, 1.2, 1.2),
                              (10.0, 2.0, 0, 1.0, 1.0)])),
    ("shin_r", "dark",  extrude([(2.0, 11.5), (2.9, 10.0), (2.0, 8.5), (1.1, 10.0)],
                                [(0.4, 1.0), (0.9, 0.7)])),
    ("shin_r", "armor", loft([(10.0, 2.0, 0, 1.0, 1.0), (6.0, 2.1, 0, 1.2, 1.2),
                              (1.5, 2.2, 0, 1.4, 1.4)])),
    ("foot_r", "armor", loft([(1.5, 2.2, 0, 1.4, 1.4), (1.0, 2.2, 0, 2.0, 2.0),
                              (0.3, 2.2, 0, 2.0, 2.0), (0.0, 2.2, 0, 1.6, 1.6)], ch=0.3)),
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
    # Lavoro: Y su, fronte +Z. Blender: Z su, fronte -Y. Rotazione di 90 gradi attorno a X.
    return (p[0], -p[2], p[1])


def all_parts():
    # Aggiunge gli specchi di sinistra e orienta le facce verso l'esterno (normale lontana dal centro della parte).
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
                for i in range(len(f)):           # normale di Newell: regge anche con facce a piu' lati
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
    # Proiezione piana lungo l'asse dominante della faccia, dentro il rettangolo della zona.
    n = np.zeros(3)
    for i in range(len(pts)):
        n += np.cross(pts[i], pts[(i + 1) % len(pts)])
    ax = int(np.argmax(np.abs(n)))
    iu, iv = [(2, 1), (0, 2), (0, 1)][ax]      # facce laterali: v = altezza
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
    # Ritorna (dimensioni X/Y/Z in unita' motore, scala, {pezzo: dati}) con vertici relativi all'origine del pezzo.
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
    # Quattro zone di colore. Dentro ogni zona: piu' scuro in basso e ai bordi, cosi' ogni parte ha un minimo
    # di ombra propria. Alpha 255 solo nella zona "team" (colore giocatore).
    img = np.zeros((n, n, 4), np.uint8)
    for name, (u0, v0, u1, v1) in ZONES.items():
        x0, x1 = int(u0 * n), int(u1 * n)
        r0, r1 = int((1 - v1) * n), int((1 - v0) * n)        # riga 0 = alto
        h, w = r1 - r0, x1 - x0
        t = np.linspace(1.0, 0.0, h)[:, None] * np.ones((1, w))                  # 1 in alto, 0 in basso
        ex = np.minimum(np.arange(w), np.arange(w)[::-1])[None, :] / (0.12 * w)
        ey = np.minimum(np.arange(h), np.arange(h)[::-1])[:, None] / (0.12 * h)
        edge = np.clip(np.minimum(ex, ey), 0.0, 1.0)
        shade = (0.72 + 0.28 * t) * (0.80 + 0.20 * edge)
        col = np.array(COLORS[name], dtype=float)[None, None, :] * shade[:, :, None]
        img[r0:r1, x0:x1, :3] = np.clip(col, 0, 255).astype(np.uint8)
        img[r0:r1, x0:x1, 3] = 255 if name == "team" else 0
    return img


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
        '-- Generata da mech_script_2.py. Da rivedere: valori non verificati nel motore (movementclass, categoria, immagine).',
        'local unitName  =  "' + name + '"',
        '',
        'local unitDef  =  {',
        '   BuildPic = "Constructor.png", -- segnaposto',
        '   Category = "' + cat + '",',
        '   ObjectName = "base/' + name + '.s3o",',
        '   name = "Mech script 2",',
        '   Side = "Vroomers",',
        '   UnitName = "Mech script 2",',
        '   script = "base/' + name + '.lua",',
        '   icontype = "builder",',
        '   Description = "Robot ciclope snello con occhio arancione, pinze e ginocchia a diamante.",',
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


LUA = r"""-- Generato da mech_script_2.py per l'unita' @NAME@. Non modificare a mano: viene riscritto.
-- Animazioni: camminata (gambe e braccia), mira e sparo con due armi (arma 1 = mano destra, arma 2 = mano sinistra).
-- Pezzi: base (torso), head, arm_l/r (spalla), fore_l/r (gomito), hand_l/r (pugno),
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
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)

    # 1. Geometria: un oggetto Blender per pezzo, con genitore e posizione relativa
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

    # 2. Texture generate: tex1 a quattro zone (alpha = colore giocatore nella zona team), tex2 piatta
    tex1 = make_tex1(P["tex_size"])
    names = (NAME + "1.png", NAME + "2.png")
    paths = tuple(os.path.join(OUT, n) for n in names)
    write_png_rgba(paths[0], tex1)
    write_png_rgba(paths[1], make_tex2())
    print("MECH texture scritte:", paths, "| pixel colore giocatore:", int((tex1[:, :, 3] > 127).sum()))

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
