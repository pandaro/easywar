# Easy War - unita' "soldier": mech Type-1 (vista frontale "MECH TYPE-1 (SLIMMED)"), modello, texture e script di
# animazione, tutto da script. SCRIPT AUTONOMO: non usa easywar_lib.py, kit di parti o file esterni.
# Va in easywar_work/base/soldier.py (la cartella e' libera). Il nome dell'unita' e' fisso: soldier.
#
# Genera soldier.s3o, soldier1.png, soldier2.png, soldier.lua. Se sotto units/ (anche nelle sottocartelle) c'e'
# la definizione di soldier, i file vanno sui percorsi indicati da ObjectName e script, e sostituiscono quelli
# attuali: la definizione non viene mai toccata e i file sostituiti finiscono prima in easywar_work/backup/.
#
# Dal disegno: busto monoblocco largo con cabina esagonale a due finestre, due spalle a blocco squadrato, braccio
# destro del foglio (sinistro del robot, a destra di chi guarda) = cannone ottagonale a tre fori con presa laterale,
# braccio sinistro del foglio = pinza; gambe a blocchi con ginocchio esagonale e piedi larghi a cuneo.
# Colore del giocatore: spalle, placca del pettorale, ginocchia. Palette provvisoria (COLORS), da decidere per fazione.
# La profondita' dei volumi non e' nel disegno: e' stimata (busto 185, spalle 150, cosce 110, piedi 220 px).
#
# Uso:
#   flatpak run org.blender.Blender --background --python /home/p/.spring/games/easywar.sdd/easywar_work/base/soldier.py | grep -E "MECH|S3O_ROOT|DEPLOY|TRIANGOLI|VERTICI"
# Con parametri (JSON dopo "--"), per esempio senza consegna e con altezza fissa:
#   ... soldier.py -- '{"deploy":false,"target_height":40}'
#
# NON verificato nel motore: proporzioni, lato del cannone, resa del colore giocatore, animazioni, canali di tex2.
import os, sys, re, json, math, struct, zlib, shutil, time
import numpy as np

HERE = None
try:
    HERE = os.path.abspath(__file__)
except NameError:
    if "--python" in sys.argv:
        HERE = os.path.abspath(sys.argv[sys.argv.index("--python") + 1])
    else:
        HERE = os.path.abspath("soldier.py")

P = {
    "target_height": "auto",    # altezza totale in unita' del motore
                                # "auto" = stessa altezza del modello attuale; se non c'e', fallback_height
    "fallback_height": 36.0,    # altezza del soldier attuale (si legge dal suo .s3o); il commander e' 44
    "yaw_deg": 180.0,           # come per le altre unita': Blender fronte -Y, poi 180 gradi
    "flip_v": True,             # il motore mostra le texture capovolte rispetto a Blender
    "mirror_x": False,          # True se nel gioco il cannone risulta sul braccio sbagliato
    "export_polygons": True,    # esporta quadrilateri e poligoni (meno vertici nel .s3o); se l'esportazione non
                                # torna, lo script ripiega da solo sui triangoli
    "tex_size": 256,
    "out_dir": None,            # None = cartella "out" accanto allo script
    "deploy": True,
    "backup": True,             # copia di sicurezza dei file sostituiti, in easywar_work/backup/
    "game_dir": os.path.expanduser("~/.spring/games/easywar.sdd"),
    "dir_textures": "unittextures",
}
NAME = "soldier"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
for a in argv:
    if a.strip().startswith("{"):
        P.update(json.loads(a))
    elif a.strip():
        NAME = a.strip()
OUT = P["out_dir"] or os.path.join(os.path.dirname(HERE), "out")


# ---- primitive (tutto generato da qui) ------------------------------------------------------------------
# Sistema di lavoro in centimetri: Y verso l'alto, Z verso il fronte, X verso la SINISTRA del robot (che e' la
# destra di chi lo guarda di fronte). Alla fine tutto viene scalato a target_height.
# Ogni primitiva ritorna (vertici, facce): le facce sono liste di indici, gia' orientate verso l'esterno.

def ring_mesh(rings, cap0=True, cap1=True):
    # Anelli di n punti uniti da fasce di quadrilateri, con due tappi. I tappi esclusi sono quelli nascosti.
    # Le facce sono coerenti per costruzione; il segno del volume dice se vanno rovesciate tutte.
    n = len(rings[0])
    v = np.array([p for r in rings for p in r], dtype=float)
    faces = []
    for k in range(len(rings) - 1):
        for i in range(n):
            j = (i + 1) % n
            faces.append([k * n + i, k * n + j, (k + 1) * n + j, (k + 1) * n + i])
    faces.append(list(range(n))[::-1])
    faces.append([(len(rings) - 1) * n + i for i in range(n)])
    c = v.mean(0)
    vol = 0.0
    for f in faces:
        p = v[f] - c
        for i in range(1, len(f) - 1):
            vol += float(np.dot(p[0], np.cross(p[i], p[i + 1])))
    if vol < 0:
        faces = [f[::-1] for f in faces]
    drop = [len(faces) - 2 + i for i, keep in enumerate((cap0, cap1)) if not keep]
    return v, [f for i, f in enumerate(faces) if i not in drop]


def cyl(p0, p1, r0, r1=None, n=6, caps=(True, True), phase=0.0):
    # Barra a sezione tonda (prisma a n lati) tra due punti; r1 diverso da r0 = barra rastremata.
    p0 = np.array(p0, dtype=float); p1 = np.array(p1, dtype=float)
    a = p1 - p0; a /= np.linalg.norm(a)
    ref = np.array([1.0, 0.0, 0.0]) if abs(a[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    u = np.cross(a, ref); u /= np.linalg.norm(u)
    w = np.cross(a, u)
    rings = []
    for p, r in ((p0, r0), (p1, r0 if r1 is None else r1)):
        rings.append([p + r * (math.cos(phase + 2 * math.pi * i / n) * u + math.sin(phase + 2 * math.pi * i / n) * w)
                      for i in range(n)])
    return ring_mesh(rings, caps[0], caps[1])


def loft(secs, caps=(True, True)):
    # Sezioni rettangolari impilate: (y, centro x, centro z, mezza larghezza x, mezza profondita' z).
    rings = [[(cx - hx, y, cz - hz), (cx + hx, y, cz - hz), (cx + hx, y, cz + hz), (cx - hx, y, cz + hz)]
             for (y, cx, cz, hx, hz) in secs]
    return ring_mesh(rings, caps[0], caps[1])


def box(c, s):
    return loft([(c[1] - s[1] / 2.0, c[0], c[2], s[0] / 2.0, s[2] / 2.0), (c[1] + s[1] / 2.0, c[0], c[2], s[0] / 2.0, s[2] / 2.0)])


def extrude(profile, z0, z1, s1=1.0, caps=(True, True)):
    # Sagoma convessa vista di fronte (x, y), estrusa da z0 a z1; s1 rimpicciolisce la faccia a z1 (smusso).
    pr = np.array(profile, dtype=float)
    c = pr.mean(0)
    r0 = [(x, y, z0) for x, y in pr]
    r1 = [(c[0] + (x - c[0]) * s1, c[1] + (y - c[1]) * s1, z1) for x, y in pr]
    return ring_mesh([r0, r1], caps[0], caps[1])


def lathe(prof, cx, cz, n=6, caps=(True, True)):
    # Solido di rotazione attorno a un asse verticale: prof = [(y, raggio), ...].
    rings = [[(cx + r * math.cos(2 * math.pi * i / n), y, cz + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
             for (y, r) in prof]
    return ring_mesh(rings, caps[0], caps[1])


def sweep(pts, w, h, caps=(True, True)):
    # Barra a sezione rettangolare (w in orizzontale, h in verticale) lungo una spezzata, con pieghe a spigolo.
    pts = [np.array(p, dtype=float) for p in pts]
    up = np.array([0.0, 1.0, 0.0])
    dirs = [(pts[i + 1] - pts[i]) / np.linalg.norm(pts[i + 1] - pts[i]) for i in range(len(pts) - 1)]
    rings = []
    for i, p in enumerate(pts):
        if i == 0:
            t = dirs[0]
        elif i == len(pts) - 1:
            t = dirs[-1]
        else:
            t = dirs[i - 1] + dirs[i]; t /= np.linalg.norm(t)
        s = np.cross(up, t); s /= np.linalg.norm(s)
        dseg = dirs[min(i, len(dirs) - 1)]
        sseg = np.cross(up, dseg); sseg /= np.linalg.norm(sseg)
        m = 1.0 / max(float(np.dot(s, sseg)), 0.3)
        a = s * (w / 2.0) * m
        b = up * (h / 2.0)
        rings.append([p - a - b, p + a - b, p + a + b, p - a + b])
    return ring_mesh(rings, caps[0], caps[1])


# ---- il modello: parti e pezzi -------------------------------------------------------------------------------
# Misure prese dal disegno frontale (1024 px, piedi a y=935, asse a x=512). Il sistema di lavoro e' in "px del
# disegno": Y verso l'alto (0 = suola), Z verso il fronte, X verso la SINISTRA del robot (destra di chi guarda).
# Zone di tex1: T = scafo, D = scuro, P = colore giocatore, A = accento, E = vetro cabina, B = bocca del cannone.

def R(x, y):          # punto del disegno sul lato destro del foglio (X positivo)
    return (x - 512.0, 935.0 - y)


def Lm(x, y):         # punto del lato sinistro del foglio, specchiato sul lato X positivo
    return (512.0 - x, 935.0 - y)


def poly(pts, f):     # profilo (lista di punti del disegno) -> coordinate di lavoro (x, y)
    return [f(x, y) for x, y in pts]


def zrings(secs, caps=(True, True)):
    # Sezioni piane a z costante, tutte con lo stesso numero di punti: (z, [(x, y), ...]).
    return ring_mesh([[(x, y, z) for x, y in pts] for z, pts in secs], caps[0], caps[1])


def build_parts():
    parts = []          # (pezzo, zona, vertici, facce)

    def add(piece, zone, shape):
        parts.append((piece, zone, shape[0], shape[1]))

    # -- base: bacino a esagono e piastra di vita
    add("base", "T", extrude(poly([(418, 447), (607, 447), (615, 505), (585, 577), (440, 577), (410, 505)], R), -75, 75, 0.90))
    add("base", "D", box((0, 935 - 441, 0), (165, 14, 100)))

    # -- torso: monoblocco largo con la parte bassa a V, placca del pettorale (colore giocatore)
    chest = [(350, 158), (672, 158), (688, 255), (688, 335), (650, 395), (597, 436), (427, 436), (374, 395), (335, 335), (335, 255)]
    add("torso", "T", extrude(poly(chest, R), -90, 95, 0.86))
    add("torso", "P", extrude(poly([(380, 335), (645, 335), (615, 392), (585, 415), (440, 415), (409, 392)], R), 93.5, 98.5))

    # -- head: cabina esagonale sporgente con due finestre
    add("head", "T", extrude(poly([(460, 120), (565, 120), (588, 235), (552, 308), (473, 308), (437, 235)], R), -10, 130, 0.85))
    add("head", "E", extrude(poly([(473, 182), (551, 182), (558, 224), (467, 224)], R), 128.5, 133.0))
    add("head", "E", extrude(poly([(483, 238), (542, 238), (539, 288), (486, 288)], R), 128.5, 133.0))

    # -- spalla + braccio (definiti a destra del foglio e specchiati): blocco squadrato smussato, braccio inclinato
    add("arm_l", "P", extrude(poly([(706, 172), (732, 148), (832, 148), (854, 170), (854, 290), (836, 307), (726, 307), (706, 300)], R), -75, 75, 0.90))
    add("arm_l", "D", box((R(698, 240)[0], 695, 0), (22, 100, 70)))                                   # attacco al busto
    add("arm_l", "T", extrude(poly([(750, 306), (842, 306), (868, 372), (778, 380)], R), -48, 48, 0.88))
    add("arm_l", "D", box((R(822, 384)[0], 935 - 384, 0), (96, 18, 84)))                              # gomito

    # -- avambraccio sinistro del robot: cannone ottagonale a nanoparticelle con presa laterale
    cx, cy = R(822, 452)
    add("fore_l", "T", cyl((cx, cy, -40), (cx, cy, 150), 67, n=8, caps=(True, False), phase=math.pi / 8))
    add("fore_l", "B", cyl((cx, cy, 150), (cx, cy, 155), 61, n=8, caps=(False, True), phase=math.pi / 8))
    add("fore_l", "A", box((R(897, 450)[0], 935 - 450, 65), (37, 76, 70)))                            # presa laterale
    add("fore_l", "D", cyl((cx, cy, 100), (cx, cy, 112), 72, n=8, caps=(True, True), phase=math.pi / 8))   # fascia
    nano = np.array([(cx - 3, cy, 158.0), (cx + 3, cy, 158.0), (cx, cy, 164.0)])
    parts.append(("nano", "D", nano, [[0, 2, 1]]))

    # -- avambraccio destro con pinza (mano)
    cxr, cyr = (203.0 - 512.0, 935.0 - 452.0)
    add("fore_r", "T", cyl((cxr, cyr, -40), (cxr, cyr, 105), 62, n=8, caps=(True, True), phase=math.pi / 8))
    add("fore_r", "D", cyl((cxr, cyr, 60), (cxr, cyr, 72), 67, n=8, caps=(True, True), phase=math.pi / 8))
    add("hand_r", "D", box((cxr, cyr, 117), (52, 58, 24)))                                           # nocca
    add("hand_r", "A", box((cxr, cyr + 24, 160), (30, 16, 70)))                                      # ganascia alta
    add("hand_r", "A", box((cxr, cyr - 24, 160), (30, 16, 70)))                                      # ganascia bassa

    # -- gamba (definita a sinistra del foglio e specchiata)
    add("leg_l", "T", extrude(poly([(292, 447), (410, 447), (403, 640), (318, 640)], Lm), -55, 55, 0.92))
    add("leg_l", "D", box((Lm(351, 650)[0], 935 - 652, -5), (112, 76, 58)))                           # protezione del ginocchio
    add("shin_l", "P", extrude(poly([(341, 632), (366, 632), (380, 668), (366, 715), (340, 715), (326, 668)], Lm), 18, 80, 0.85))   # ginocchio
    add("shin_l", "T", extrude(poly([(298, 700), (408, 700), (392, 830), (305, 830)], Lm), -50, 45, 0.90))
    add("shin_l", "D", box((Lm(348, 845)[0], 935 - 845, 0), (88, 40, 70)))                            # caviglia
    add("foot_l", "T", zrings([
        (-70, poly([(232, 935), (453, 935), (403, 883), (282, 883)], Lm)),
        (95, poly([(232, 935), (453, 935), (403, 883), (282, 883)], Lm)),
        (150, poly([(262, 935), (423, 935), (390, 905), (295, 905)], Lm)),
    ]))
    add("foot_l", "D", box((Lm(342, 870)[0], 935 - 872, 10), (116, 26, 110)))                         # blocco sopra il piede

    # specchi: arm, leg, shin, foot
    out = []
    for piece, zone, v, f in parts:
        out.append((piece, zone, v, f))
        if piece in ("arm_l", "leg_l", "shin_l", "foot_l"):
            out.append((piece[:-2] + "_r", zone, v * np.array([-1.0, 1.0, 1.0]), [list(x)[::-1] for x in f]))
    if P["mirror_x"]:
        out = [(p, z, v * np.array([-1.0, 1.0, 1.0]), [list(x)[::-1] for x in f]) for p, z, v, f in out]
    return out


# pezzo: (genitore, origine = giunto, nel sistema di lavoro)
def _o(f, x, y, z=0.0):
    p = f(x, y)
    return (p[0], p[1], z)


PIECES = {
    "base":   (None, (0.0, 425.0, 0.0)),
    "torso":  ("base", (0.0, 500.0, 0.0)),
    "head":   ("torso", (0.0, 690.0, 10.0)),
    "arm_l":  ("torso", _o(R, 780, 232)),
    "fore_l": ("arm_l", _o(R, 822, 385)),
    "nano":   ("fore_l", (R(822, 452)[0], 935.0 - 452.0, 158.0)),
    "arm_r":  ("torso", _o(R, 244, 232)),
    "fore_r": ("arm_r", _o(R, 203, 385)),
    "hand_r": ("fore_r", (203.0 - 512.0, 935.0 - 452.0, 105.0)),
    "leg_l":  ("base", _o(Lm, 352, 470)),
    "shin_l": ("leg_l", _o(Lm, 352, 668)),
    "foot_l": ("shin_l", _o(Lm, 352, 862)),
    "leg_r":  ("base", _o(R, 352, 470)),
    "shin_r": ("leg_r", _o(R, 352, 668)),
    "foot_r": ("shin_r", _o(R, 352, 862)),
}
ORDER = ["base", "torso", "head", "arm_l", "fore_l", "nano", "arm_r", "fore_r", "hand_r",
         "leg_l", "shin_l", "foot_l", "leg_r", "shin_r", "foot_r"]

ZONES = {   # rettangoli (u0, v0, u1, v1) di tex1, con v verso l'alto come in Blender
    "T": (0.0, 0.5, 0.5, 1.0),
    "D": (0.5, 0.5, 1.0, 1.0),
    "P": (0.0, 0.0, 0.5, 0.5),      # alpha alta = colore giocatore
    "A": (0.5, 0.0, 0.75, 0.5),
    "E": (0.75, 0.25, 1.0, 0.5),
    "B": (0.75, 0.0, 1.0, 0.25),
}
# palette Lambda della scheda: base #8A8F98, scuro #3B3F46, accento #5B4FA8
def to_blender(p):
    # Lavoro: Y su, fronte +Z. Blender: Z su, fronte -Y. Rotazione di 90 gradi attorno a X.
    return (p[0], -p[2], p[1])


def face_uvs(pts, zone, lo, hi):
    # Proiezione piana lungo l'asse dominante della faccia, dentro il rettangolo della zona.
    n = np.zeros(3)
    for i in range(len(pts)):
        n += np.cross(pts[i], pts[(i + 1) % len(pts)])
    ax = int(np.argmax(np.abs(n)))
    iu, iv = [(2, 1), (0, 2), (0, 1)][ax]      # facce laterali: v = altezza
    u0, v0, u1, v1 = ZONES[zone]
    m = 0.08
    out = []
    for p in pts:
        a = (p[iu] - lo[iu]) / max(hi[iu] - lo[iu], 1e-6)
        b = (p[iv] - lo[iv]) / max(hi[iv] - lo[iv], 1e-6)
        u = u0 + (m + a * (1 - 2 * m)) * (u1 - u0)
        v = v0 + (m + b * (1 - 2 * m)) * (v1 - v0)
        out.append((float(u), float(1.0 - v if P["flip_v"] else v)))
    return out


def assemble(target_height):
    # Ritorna (dimensioni X/Y/Z in unita' motore, scala, {pezzo: dati}). I vertici sono relativi all'origine del
    # pezzo, le facce sono triangoli e "uvs" ha una coppia per ogni angolo di triangolo.
    parts = build_parts()
    allp = np.vstack([v for _, _, v, _ in parts])
    lo, hi = allp.min(0), allp.max(0)
    k = target_height / (hi[1] - lo[1])

    def conv(p):
        return np.array(to_blender((p[0] * k, (p[1] - lo[1]) * k, p[2] * k)))

    sgn = -1.0 if P["mirror_x"] else 1.0
    origin = {n: conv(np.array((o[0] * sgn, o[1], o[2]), dtype=float)) for n, (_, o) in PIECES.items()}
    out = {n: {"parent": PIECES[n][0], "loc": tuple(origin[n] - (origin[PIECES[n][0]] if PIECES[n][0] else 0.0)),
               "verts": [], "polys": [], "uvs": []} for n in ORDER}
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


def triangulated(d):
    # Stessa geometria a soli triangoli (ventaglio: le facce sono convesse), con le UV per angolo.
    tris, uvs, li = [], [], 0
    for f in d["polys"]:
        for i in range(1, len(f) - 1):
            tris.append([f[0], f[i], f[i + 1]])
            uvs += [d["uvs"][li], d["uvs"][li + i], d["uvs"][li + i + 1]]
        li += len(f)
    return tris, uvs


def count(data):
    # Triangoli, vertici Blender e angoli di faccia. Con facce piatte il .s3o ripete un vertice per ogni angolo:
    # gli angoli delle facce sono la stima dei vertici del .s3o se l'esportatore lavora su quadrilateri e poligoni,
    # tre per triangolo se lavora su soli triangoli.
    tris = sum(len(f) - 2 for d in data.values() for f in d["polys"])
    bverts = sum(len(d["verts"]) for d in data.values())
    loops = sum(len(f) for d in data.values() for f in d["polys"])
    return tris, bverts, loops


# ---- texture ---------------------------------------------------------------------------------------------
# Zone: T scafo (grigio acciaio), D parti scure, P colore giocatore (alpha alta), A accento ocra,
# E vetro della cabina, B bocca del cannone (piastra con tre fori).
COLORS = {"T": (124, 132, 140), "D": (47, 53, 59), "P": (205, 205, 205), "A": (201, 138, 43)}


def make_tex1(n):
    img = np.zeros((n, n, 4), np.uint8)

    def rect(zone):
        u0, v0, u1, v1 = ZONES[zone]
        return int((1 - v1) * n), int((1 - v0) * n), int(u0 * n), int(u1 * n)      # righe (0 = alto), colonne

    for name in ("T", "D", "P", "A"):
        r0, r1, x0, x1 = rect(name)
        h, w = r1 - r0, x1 - x0
        t = np.linspace(1.0, 0.0, h)[:, None] * np.ones((1, w))                  # 1 in alto, 0 in basso
        ex = np.minimum(np.arange(w), np.arange(w)[::-1])[None, :] / (0.12 * w)
        ey = np.minimum(np.arange(h), np.arange(h)[::-1])[:, None] / (0.12 * h)
        edge = np.clip(np.minimum(ex, ey), 0.0, 1.0)
        shade = (0.74 + 0.26 * t) * (0.78 + 0.22 * edge)
        col = np.array(COLORS[name], dtype=float)[None, None, :] * shade[:, :, None]
        if name == "T":                                 # linee di pannello: due righe scure orizzontali
            for yy in (0.34, 0.68):
                line = np.abs(t - yy) < 0.012
                col[line] *= 0.55
        img[r0:r1, x0:x1, :3] = np.clip(col, 0, 255).astype(np.uint8)
        img[r0:r1, x0:x1, 3] = 255 if name == "P" else 0

    # vetro: sfumatura blu scuro con un riflesso chiaro in diagonale
    r0, r1, x0, x1 = rect("E")
    h, w = r1 - r0, x1 - x0
    yy, xx = np.mgrid[0:h, 0:w]
    g = np.zeros((h, w, 3)) + np.array((28, 52, 70)) * (0.7 + 0.5 * (1 - yy / float(h)))[:, :, None]
    diag = np.abs((xx / float(w)) - (yy / float(h)) * 0.6 - 0.45) < 0.07
    g[diag] = g[diag] * 0.4 + np.array((150, 200, 225)) * 0.6
    img[r0:r1, x0:x1, :3] = np.clip(g, 0, 255).astype(np.uint8)

    # bocca del cannone: cornice scura, disco grigio, tre fori (uno in alto, due in basso)
    r0, r1, x0, x1 = rect("B")
    h, w = r1 - r0, x1 - x0
    yy, xx = np.mgrid[0:h, 0:w]
    fx = xx / float(w); fy = 1.0 - yy / float(h)
    plate = np.zeros((h, w, 3)) + np.array((38, 42, 48))
    rr = np.hypot(fx - 0.5, fy - 0.5)
    plate[rr < 0.43] = (112, 118, 126)
    for cxh, cyh in ((0.50, 0.66), (0.37, 0.40), (0.63, 0.40)):
        d = np.hypot(fx - cxh, fy - cyh)
        plate[d < 0.095] = (26, 28, 32)
        plate[d < 0.060] = (8, 8, 10)
        plate[(d >= 0.095) & (d < 0.115)] = (70, 76, 84)
    img[r0:r1, x0:x1, :3] = plate.astype(np.uint8)
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


# ---- lettura di un .s3o (per misurare il modello attuale e ricontare quello esportato) -------------------

def read_s3o(path):
    # Ritorna None se il file non e' un .s3o leggibile, altrimenti un dizionario con pezzi, conteggi e ingombro.
    try:
        d = open(path, "rb").read()
        if d[:11] != b"Spring unit":
            return None
        ver, radius, height, mx, my, mz, root, coll, t1, t2 = struct.unpack_from("<i5f4i", d, 12)

        def cstr(o):
            return d[o:d.index(b"\0", o)].decode("latin1") if o > 0 else ""

        info = {"pieces": [], "verts": 0, "tris": 0, "lo": [1e9] * 3, "hi": [-1e9] * 3,
                "tex": (cstr(t1), cstr(t2)), "radius": radius, "height_field": height}

        def walk(off, ox, oy, oz):
            (nm, nch, ch, nv, vo, vtype, ptype, vts, vt, cd, x, y, z) = struct.unpack_from("<10i3f", d, off)
            ox, oy, oz = ox + x, oy + y, oz + z
            info["pieces"].append(cstr(nm))
            info["verts"] += nv
            info["tris"] += {0: vts // 3, 1: max(vts - 2, 0), 2: (vts // 4) * 2}.get(ptype, 0)
            if nv:
                vv = np.frombuffer(d, dtype="<f4", count=nv * 8, offset=vo).reshape(-1, 8)[:, :3]
                for i, o in enumerate((ox, oy, oz)):
                    info["lo"][i] = min(info["lo"][i], float(vv[:, i].min()) + o)
                    info["hi"][i] = max(info["hi"][i], float(vv[:, i].max()) + o)
            for i in range(nch):
                walk(struct.unpack_from("<i", d, ch + 4 * i)[0], ox, oy, oz)

        walk(root, 0.0, 0.0, 0.0)
        info["size"] = tuple(info["hi"][i] - info["lo"][i] for i in range(3))
        return info
    except Exception as e:           # file troncato o formato diverso: non blocca la generazione
        print("MECH lettura .s3o fallita (%s): %s" % (path, e))
        return None


# ---- dove sta l'unita' attuale -----------------------------------------------------------------------------

def def_value(text, key):
    m = re.search(r"\b" + key + r"\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|\[\[(.*?)\]\])", text, re.IGNORECASE)
    return next((g for g in m.groups() if g is not None), None) if m else None


def find_unit(gd, name):
    # Cerca la definizione dell'unita' sotto units/ e ne ricava i percorsi di modello e script.
    found = {"def": None, "model": None, "script": None, "notes": []}
    cands = []
    for root, _, files in os.walk(os.path.join(gd, "units")):
        for f in sorted(files):
            if not f.lower().endswith(".lua"):
                continue
            path = os.path.join(root, f)
            if f.lower() == name.lower() + ".lua":
                cands.insert(0, path)
            else:
                try:
                    with open(path, encoding="utf-8", errors="replace") as fh:
                        if re.search(r"\b" + re.escape(name) + r"\b", fh.read(), re.IGNORECASE):
                            cands.append(path)
                except OSError:
                    pass
    if not cands:
        return found
    found["def"] = cands[0]
    with open(cands[0], encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    obj = def_value(text, "objectname")
    scr = def_value(text, "script")
    if obj:
        stem, ext = os.path.splitext(obj)
        if ext.lower() not in ("", ".s3o"):
            found["notes"].append("ObjectName indica '%s': nella definizione va cambiato in '%s.s3o'" % (obj, stem))
        found["model"] = os.path.join(gd, "objects3d", stem + ".s3o")
    else:
        found["notes"].append("ObjectName non trovato nella definizione")
    if scr and scr.lower().endswith(".lua"):
        found["script"] = os.path.join(gd, "scripts", scr)
    else:
        found["script"] = os.path.join(gd, "scripts", name + ".lua")
        found["notes"].append("la definizione non indica uno script .lua (script = %r): il Lua va in scripts/%s.lua "
                              "e nella definizione serve script = \"%s.lua\"" % (scr, name, name))
    return found


LUA = r"""-- Generato da @FILE@ per l'unita' @NAME@ (mech Type-1). Non modificare a mano: viene riscritto.
-- Animazioni: camminata pesante con oscillazione del busto, costruzione con il cannone dell'avambraccio
-- sinistro, mira con lo stesso braccio se la definizione dell'unita' ha delle armi.
-- Pezzi: base (bacino), torso (busto), head (cabina), arm_l/r (spalla e braccio), fore_l (cannone),
--        nano (bocca del cannone), fore_r (avambraccio), hand_r (pinza), leg_l/r (coscia),
--        shin_l/r (ginocchio e stinco), foot_l/r (piede). l = sinistra del robot, r = destra.
--
-- CONVENZIONE DEL SEGNO: sull'asse x un angolo NEGATIVO porta il pezzo in avanti.
-- Se nel gioco gambe e braccia vanno al contrario, basta mettere FWD = 1.

local base, torso, head = piece('base', 'torso', 'head')
local arm_l, arm_r = piece('arm_l', 'arm_r')
local fore_l, fore_r = piece('fore_l', 'fore_r')
local hand_r, nano = piece('hand_r', 'nano')
local leg_l, leg_r = piece('leg_l', 'leg_r')
local shin_l, shin_r = piece('shin_l', 'shin_r')
local foot_l, foot_r = piece('foot_l', 'foot_r')

local FWD = -1                 -- segno di "avanti" sull'asse x
local rad = math.rad
local STEP = 330               -- millisecondi per fase del passo (4 fasi = un passo completo): mech pesante
local SPD = rad(110)           -- velocita' di rotazione durante il passo (radianti al secondo)
local AIM_SPD = rad(200)       -- velocita' di busto e braccio quando puntano
local REST_DELAY = 2500        -- dopo quanto tempo il braccio torna al riposo
local BOB = 0.35               -- quanto il bacino sale e scende ad ogni passo (unita' del motore)
local SWAY = 3                 -- oscillazione del busto in gradi

local SIG_WALK = 1
local SIG_ARM = 2
local SIG_REST = 4

local moving = false
local busy = false             -- il cannone sta puntando (costruzione o mira)
local building = false

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

-- Le braccia oscillano: il sinistro solo se non sta puntando. La pinza destra segue il braccio.
local function Arms(a_left, a_right)
  if not busy then X(arm_l, a_left) end
  X(arm_r, a_right)
end

local function Walk()
  SetSignalMask(SIG_WALK)
  while true do
    -- 1: sinistra avanti, destra indietro e appoggiata; il peso si sposta a sinistra
    Leg(leg_l, shin_l, foot_l, 18, 4)
    Leg(leg_r, shin_r, foot_r, -14, 8)
    Arms(-10, 10)
    if not busy then Turn(torso, y_axis, rad(SWAY), rad(30)) end
    Move(base, y_axis, 0, 1.5)
    Sleep(STEP)
    -- 2: passaggio, la destra si stacca e si piega; il bacino sale
    Leg(leg_l, shin_l, foot_l, 4, 0)
    Leg(leg_r, shin_r, foot_r, 8, 28)
    Arms(0, 0)
    Move(base, y_axis, BOB, 1.5)
    Sleep(STEP)
    -- 3: destra avanti, sinistra indietro e appoggiata
    Leg(leg_r, shin_r, foot_r, 18, 4)
    Leg(leg_l, shin_l, foot_l, -14, 8)
    Arms(10, -10)
    if not busy then Turn(torso, y_axis, rad(-SWAY), rad(30)) end
    Move(base, y_axis, 0, 1.5)
    Sleep(STEP)
    -- 4: passaggio, la sinistra si stacca e si piega
    Leg(leg_r, shin_r, foot_r, 4, 0)
    Leg(leg_l, shin_l, foot_l, 8, 28)
    Arms(0, 0)
    Move(base, y_axis, BOB, 1.5)
    Sleep(STEP)
  end
end

local function StandStill()
  for _, p in ipairs({ leg_l, leg_r, shin_l, shin_r, foot_l, foot_r }) do
    Turn(p, x_axis, 0, SPD)
  end
  Move(base, y_axis, 0, 1.5)
  if not busy then Turn(torso, y_axis, 0, rad(30)) end
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

-- ---- Cannone sinistro: costruzione e mira ----------------------------------------------------
-- A riposo il cannone punta in avanti. Per puntare, il busto gira verso il bersaglio (heading) e l'avambraccio
-- si inclina dell'angolo di mira (pitch): la canna resta sull'asse di mira.

local function PointArm(heading, pitch)
  Turn(torso, y_axis, heading, AIM_SPD)
  Turn(arm_l, x_axis, 0, AIM_SPD)
  Turn(fore_l, x_axis, FWD * pitch, AIM_SPD)
  WaitForTurn(torso, y_axis)
  WaitForTurn(fore_l, x_axis)
end

local function Rest()
  SetSignalMask(SIG_REST)
  Sleep(REST_DELAY)
  busy = false
  Turn(torso, y_axis, 0, AIM_SPD / 2)
  Turn(fore_l, x_axis, 0, AIM_SPD / 2)
end

function script.StartBuilding(heading, pitch)
  Signal(SIG_ARM)
  SetSignalMask(SIG_ARM)
  Signal(SIG_REST)
  busy = true
  building = true
  PointArm(heading or 0, pitch or 0)
  SetUnitValue(COB.INBUILDSTANCE, 1)
  return true
end

function script.StopBuilding()
  building = false
  SetUnitValue(COB.INBUILDSTANCE, 0)
  Signal(SIG_ARM)
  Signal(SIG_REST)
  StartThread(Rest)
  return true
end

-- Il motore chiede da quale pezzo esce il getto di costruzione. Il nome usato da BAR e' QueryNanoPiece;
-- in un test precedente era stato annotato QueryNanopiece: si definiscono entrambi.
local function NanoPiece()
  return nano
end
script.QueryNanoPiece = NanoPiece
script.QueryNanopiece = NanoPiece

function script.AimFromWeapon(n)
  return torso
end

function script.QueryWeapon(n)
  return nano
end

function script.AimWeapon(n, heading, pitch)
  if building then return false end
  Signal(SIG_ARM)
  SetSignalMask(SIG_ARM)
  Signal(SIG_REST)
  busy = true
  PointArm(heading, pitch)
  StartThread(Rest)
  return true
end

-- Rinculo: la spalla scatta indietro e torna.
function script.FireWeapon(n)
  Turn(arm_l, x_axis, -FWD * rad(6), rad(700))
  Sleep(80)
  Turn(arm_l, x_axis, 0, rad(180))
end

function script.Killed(recentDamage, maxHealth)
  return 1
end
""".replace("@NAME@", NAME).replace("@FILE@", os.path.basename(HERE))


# ---- parte Blender ---------------------------------------------------------------------------------------

def resolve_height(found):
    th = P["target_height"]
    if isinstance(th, (int, float)):
        return float(th)
    old = read_s3o(found["model"]) if found and found.get("model") and os.path.exists(found["model"]) else None
    if old:
        print("MECH modello attuale: %s | altezza %.1f, larghezza %.1f | %d pezzi %s | %d vertici, %d triangoli | texture %s" % (
            found["model"], old["size"][1], old["size"][0], len(old["pieces"]), old["pieces"][:20], old["verts"],
            old["tris"], old["tex"]))
        if old["size"][1] > 1.0:
            return float(old["size"][1])
    print("MECH altezza: modello attuale non trovato o non leggibile, uso fallback_height", P["fallback_height"])
    return float(P["fallback_height"])


def put(src, dst, backup_dir, gd):
    # Copia src su dst. Se dst esiste ed e' diverso, prima ne salva una copia.
    if os.path.exists(dst) and backup_dir:
        with open(src, "rb") as a, open(dst, "rb") as b:
            same = a.read() == b.read()
        if not same:
            bk = os.path.join(backup_dir, os.path.relpath(dst, gd))
            os.makedirs(os.path.dirname(bk), exist_ok=True)
            shutil.copyfile(dst, bk)
            print("DEPLOY copia di sicurezza:", bk)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)
    print("DEPLOY", dst, os.path.getsize(dst), "byte")


def run_blender():
    import bpy

    print("START", NAME, flush=True)
    os.makedirs(OUT, exist_ok=True)
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)

    gd = P["game_dir"]
    found = find_unit(gd, NAME) if os.path.isdir(gd) else {"def": None, "model": None, "script": None, "notes": []}
    print("MECH definizione attuale:", found["def"], "| modello:", found["model"], "| script:", found["script"])
    for note in found["notes"]:
        print("MECH ATTENZIONE:", note)

    # 1. Geometria: un oggetto Blender per pezzo, con genitore e posizione relativa
    size, k, data = assemble(resolve_height(found))
    tris, bverts, loops = count(data)
    print("MECH scala %.4f, dimensioni finali X/Y/Z %.1f %.1f %.1f" % ((k,) + size))
    print("MECH triangoli %d | vertici Blender %d | vertici .s3o attesi: circa %d con i poligoni, fino a %d con i triangoli" % (
        tris, bverts, loops, tris * 3))

    def make_mesh(name, as_triangles):
        d = data[name]
        polys, uvs = triangulated(d) if as_triangles else (d["polys"], d["uvs"])
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(d["verts"], [], polys)
        uv = mesh.uv_layers.new(name="UVMap")
        for li, uvc in enumerate(uvs):
            uv.data[li].uv = uvc
        mesh.update()
        for p in mesh.polygons:
            p.use_smooth = False
        return mesh

    objs = {}
    for name in ORDER:
        mesh = make_mesh(name, not P["export_polygons"])
        ob = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(ob)
        objs[name] = ob
    for name in ORDER:
        d = data[name]
        if d["parent"]:
            objs[name].parent = objs[d["parent"]]
        objs[name].location = d["loc"]
    obj = objs["base"]
    print("MECH pezzi:", len(objs), sorted(objs))

    # 2. Texture generate: tex1 a zone (alpha = colore giocatore nella zona P), tex2 piatta
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

    def export(label):
        # Esporta, rilegge il file e dice se pezzi e triangoli tornano con quelli generati.
        if os.path.exists(s3o):
            os.remove(s3o)
        try:
            print("S3O_ROOT export (%s):" % label, bpy.ops.s3o_tools.export_s3o("EXEC_DEFAULT", filepath=s3o),
                  s3o, os.path.getsize(s3o) if os.path.exists(s3o) else "NON CREATO")
        except Exception as e:
            print("S3O_ROOT export errore (%s):" % label, e)
        new = read_s3o(s3o) if os.path.exists(s3o) else None
        if not new:
            return False
        good = new["tris"] == tris and len(new["pieces"]) == len(ORDER)
        print("MECH .s3o riletto (%s): %d pezzi | %d VERTICI | %d triangoli | altezza %.1f, larghezza %.1f | texture %s | %s" % (
            label, len(new["pieces"]), new["verts"], new["tris"], new["size"][1], new["size"][0], new["tex"],
            "torna" if good else "NON torna: attesi %d pezzi e %d triangoli" % (len(ORDER), tris)))
        return good

    ok = export("poligoni" if P["export_polygons"] else "triangoli")
    if not ok and P["export_polygons"]:
        print("MECH ripiego: rifaccio le mesh a soli triangoli ed esporto di nuovo")
        for name in ORDER:
            old_mesh = objs[name].data
            objs[name].data = make_mesh(name, True)
            objs[name].data.materials.append(mat)
            bpy.data.meshes.remove(old_mesh)
        bpy.context.view_layer.update()
        ok = export("triangoli")
    if not ok:
        print("MECH ATTENZIONE: il .s3o esportato non torna con il modello generato; controllare prima di usarlo")
    lua_path = os.path.join(OUT, NAME + ".lua")
    with open(lua_path, "w", encoding="utf-8") as f:
        f.write(LUA)

    # 4. Consegna nel gioco, sui percorsi dell'unita' attuale
    if P["deploy"]:
        if not os.path.isdir(gd):
            print("DEPLOY saltato: cartella del gioco non trovata:", gd)
        elif not (os.path.exists(s3o) and os.path.getsize(s3o) > 0):
            print("DEPLOY saltato: il .s3o non e' stato creato")
        elif not found["def"] or not found["model"]:
            print("DEPLOY saltato: non trovo la definizione di", NAME, "sotto units/ (o non ha ObjectName).")
            print("DEPLOY    I file pronti sono in", OUT)
        else:
            bdir = os.path.join(gd, "easywar_work", "backup", NAME + "_" + time.strftime("%Y%m%d_%H%M%S")) if P["backup"] else None
            put(s3o, found["model"], bdir, gd)
            put(paths[0], os.path.join(gd, P["dir_textures"], names[0]), bdir, gd)
            put(paths[1], os.path.join(gd, P["dir_textures"], names[1]), bdir, gd)
            put(lua_path, found["script"], bdir, gd)
            print("DEPLOY definizione non toccata:", found["def"])

    blend = os.path.join(OUT, NAME + ".blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend)
    print("BLENDER_VERSION", bpy.app.version_string)
    print("TRIANGOLI", tris)
    print("SALVATO", blend)


if __name__ == "__main__":
    try:
        import bpy  # noqa
    except ImportError:
        bpy = None
    if bpy is not None:
        run_blender()
    else:
        size, k, data = assemble(float(P["target_height"]) if isinstance(P["target_height"], (int, float)) else P["fallback_height"])
        print("Fuori da Blender: solo conteggi. Triangoli %d, vertici Blender %d, angoli di faccia %d" % count(data))
        print("Per generare il modello: blender --background --python", HERE)