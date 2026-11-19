# Easy War - unita' "lllcom": Commander della fazione Lambda, importato dal modello FBX di Tripo.
# SCRIPT AUTONOMO: non usa easywar_lib.py. Sostituisce il modello dell'attuale lllcom (units/lllcom.lua).
# Va in easywar_work/lll/lllcom.py, con accanto l'FBX di Tripo e la sua cartella .fbm (la texture JPG).
#
# Cosa fa: legge l'FBX (senza l'importatore FBX di Blender), divide le 142 forme separate della mesh sui pezzi
# animabili (base, torso, head, arm_l/r, fore_l/r, hand_r, nano, leg_l/r, shin_l/r, foot_l/r) assegnando ogni
# forma all'osso piu' vicino, porta il modello all'altezza di quello attuale, tiene le UV di Tripo, scrive
# lllcom1.png (JPG ridimensionato; alpha = parti rosse = colore giocatore) e lllcom2.png, esporta il .s3o, lo
# rilegge e scrive lllcom.lua. NON riduce i triangoli. Poi consegna sui percorsi dell'attuale lllcom: cerca la
# definizione sotto units/, legge ObjectName e script e scrive li'. Prima di sovrascrivere un file diverso ne
# salva una copia in easywar_work/backup/. La definizione dell'unita' non viene toccata.
#
# Uso:
#   flatpak run org.blender.Blender --background --python /home/p/.spring/games/easywar.sdd/easywar_work/lll/lllcom.py | grep -E "LLL|S3O_ROOT|DEPLOY|TRIANGOLI"
# Con parametri (JSON dopo "--"), per esempio senza consegna e con altezza fissa:
#   ... lllcom.py -- '{"deploy":false,"target_height":44}'
#
# NON verificato nel motore: assegnazione dei pezzi, lato del cannone, colore giocatore, animazioni, canali di tex2.
import os, sys, re, json, math, struct, zlib, shutil, time
import numpy as np


HERE = None
try:
    HERE = os.path.abspath(__file__)
except NameError:
    if "--python" in sys.argv:
        HERE = os.path.abspath(sys.argv[sys.argv.index("--python") + 1])
    else:
        HERE = os.path.abspath("lllcom.py")

P = {
    "target_height": "auto",    # altezza totale in unita' del motore, antenna compresa (l'elmo arriva al 93%).
                                # "auto" = stessa altezza del modello lllcom attuale; se non c'e', fallback_height
    "fallback_height": 44.0,    # il soldier e' alto 36
    "yaw_deg": 180.0,           # come per le altre unita': Blender fronte -Y, poi 180 gradi
    "flip_v": True,             # il motore mostra le texture capovolte rispetto a Blender
    "mirror_x": False,          # True se nel gioco il cannone risulta sul braccio sbagliato
    "export_polygons": True,    # esporta quadrilateri e poligoni (meno vertici nel .s3o); se l'esportazione non
                                # torna, lo script ripiega da solo sui triangoli
    "tex_size": 1024,            # lato della texture 1 in uscita
    "fbx": None,                # None = primo .fbx accanto allo script
    "team_mask": "red",         # "red": alpha alta dove la texture e' rossa; "none": nessun colore giocatore
    "out_dir": None,            # None = cartella "out" accanto allo script
    "deploy": True,
    "backup": True,             # copia di sicurezza dei file sostituiti, in easywar_work/backup/
    "game_dir": os.path.expanduser("~/.spring/games/easywar.sdd"),
    "dir_textures": "unittextures",
}
NAME = "lllcom"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
for a in argv:
    if a.strip().startswith("{"):
        P.update(json.loads(a))
    elif a.strip():
        NAME = a.strip()
OUT = P["out_dir"] or os.path.join(os.path.dirname(HERE), "out")


# ---- lettura dell'FBX di Tripo (binario 7.x) --------------------------------------------------------------

def fbx_parse(path):
    d = open(path, "rb").read()
    if not d.startswith(b"Kaydara FBX Binary"):
        raise ValueError("non e' un FBX binario: " + path)
    big = struct.unpack_from("<I", d, 23)[0] >= 7500

    def rd(o):
        if big:
            end, npr, pl, nl = struct.unpack_from("<QQQB", d, o); o += 25
        else:
            end, npr, pl, nl = struct.unpack_from("<IIIB", d, o); o += 13
        if end == 0:
            return None, o
        name = d[o:o + nl].decode("latin1"); o += nl
        props, p = [], o
        for _ in range(npr):
            t = chr(d[p]); p += 1
            if t in "YCIFDL":
                f = {"Y": "<h", "C": "<?", "I": "<i", "F": "<f", "D": "<d", "L": "<q"}[t]
                props.append(struct.unpack_from(f, d, p)[0]); p += struct.calcsize(f)
            elif t in "SR":
                n = struct.unpack_from("<I", d, p)[0]; p += 4
                b = d[p:p + n]; p += n
                props.append(b.decode("latin1") if t == "S" else b)
            else:
                n, enc, cl = struct.unpack_from("<III", d, p); p += 12
                raw = d[p:p + cl]; p += cl
                if enc:
                    raw = zlib.decompress(raw)
                props.append(np.frombuffer(raw, dtype={"f": "<f4", "d": "<f8", "l": "<i8", "i": "<i4", "b": "?"}[t]))
        o2, ch = o + pl, []
        while o2 < end:
            c, o2 = rd(o2)
            if c is None:
                break
            ch.append(c)
        return (name, props, ch), end

    o, top = 27, []
    while o < len(d) - 30:
        n, o = rd(o)
        if n is None:
            break
        top.append(n)
    return top


def fbx_find(nodes, name):
    return [n for n in nodes if n[0] == name]


def fbx_mesh(path):
    # Ritorna vertici (N,3), poligoni [(indici, indici UV)], UV (M,2) e il nome del file texture indicato nell'FBX.
    top = fbx_parse(path)
    obj = fbx_find(top, "Objects")[0][2]
    g = fbx_find(obj, "Geometry")[0][2]
    V = fbx_find(g, "Vertices")[0][1][0].reshape(-1, 3).astype(float)
    I = fbx_find(g, "PolygonVertexIndex")[0][1][0]
    uvn = fbx_find(g, "LayerElementUV")[0][2]
    UV = fbx_find(uvn, "UV")[0][1][0].reshape(-1, 2).astype(float)
    UI = fbx_find(uvn, "UVIndex")[0][1][0]
    polys, cur, cu = [], [], []
    for k, i in enumerate(I):
        cur.append(int(~i) if i < 0 else int(i)); cu.append(int(UI[k]))
        if i < 0:
            polys.append((cur, cu)); cur, cu = [], []
    tex = None
    for v in fbx_find(obj, "Video"):
        for c in v[2]:
            if c[0] in ("RelativeFilename", "Filename") and c[1] and not tex:
                tex = c[1][0]
    return V, polys, UV, tex


def find_inputs():
    # FBX e texture: P["fbx"], oppure il primo .fbx accanto allo script (o in una sottocartella).
    here = os.path.dirname(HERE)
    fbx = P["fbx"]
    if not fbx:
        cands = []
        for root, dirs, files in os.walk(here):
            if os.path.abspath(root) == os.path.abspath(OUT) or root.count(os.sep) - here.count(os.sep) > 2:
                continue
            cands += [os.path.join(root, f) for f in sorted(files) if f.lower().endswith(".fbx")]
        fbx = cands[0] if cands else None
    return fbx


def find_texture(fbx, name_in_fbx):
    base = os.path.dirname(fbx)
    cands = []
    if name_in_fbx:
        n = name_in_fbx.replace("\\", "/")
        cands += [os.path.join(base, n), os.path.join(base, os.path.basename(n))]
    stem = os.path.splitext(os.path.basename(fbx))[0]
    for root, _, files in os.walk(base):
        for f in sorted(files):
            if f.lower().endswith((".jpg", ".jpeg", ".png")) and stem.lower() in (root + f).lower():
                cands.append(os.path.join(root, f))
    for c in cands:
        if os.path.isfile(c):
            return c
    return None


# ---- pezzi ----------------------------------------------------------------------------------------------
# pezzo: (genitore, origine = giunto, in unita' del modello Tripo, alto 1.0)
PIECES = {
    "base":   (None, (0.0, 0.47, 0.0)),
    "torso":  ("base", (0.0, 0.53, -0.03)),
    "head":   ("torso", (0.0, 0.78, -0.03)),
    "arm_l":  ("torso", (0.19, 0.745, -0.03)),
    "fore_l": ("arm_l", (0.20, 0.60, -0.03)),
    "nano":   ("fore_l", (0.20, 0.31, -0.03)),          # sovrascritto con la punta reale del cannone
    "arm_r":  ("torso", (-0.19, 0.745, -0.03)),
    "fore_r": ("arm_r", (-0.20, 0.60, -0.03)),
    "hand_r": ("fore_r", (-0.21, 0.44, -0.03)),
    "leg_l":  ("base", (0.09, 0.46, -0.03)),
    "shin_l": ("leg_l", (0.09, 0.30, -0.03)),
    "foot_l": ("shin_l", (0.09, 0.08, -0.03)),
    "leg_r":  ("base", (-0.09, 0.46, -0.03)),
    "shin_r": ("leg_r", (-0.09, 0.30, -0.03)),
    "foot_r": ("shin_r", (-0.09, 0.08, -0.03)),
}
ORDER = ["base", "torso", "head", "arm_l", "fore_l", "nano", "arm_r", "fore_r", "hand_r",
         "leg_l", "shin_l", "foot_l", "leg_r", "shin_r", "foot_r"]

# Ossa per l'assegnazione: segmento (x0, y0, x1, y1). Ogni forma separata dell'FBX va all'osso piu' vicino
# (distanza del suo centro dal segmento, nel piano X/Y).
BONES = {
    "base":   (-0.08, 0.47, 0.08, 0.47),
    "torso":  (0.0, 0.53, 0.0, 0.74),
    "head":   (0.0, 0.80, 0.0, 0.97),
    "arm_l":  (0.19, 0.77, 0.20, 0.62),
    "arm_r":  (-0.19, 0.77, -0.20, 0.62),
    "fore_l": (0.20, 0.59, 0.20, 0.31),
    "fore_r": (-0.20, 0.59, -0.20, 0.46),
    "hand_r": (-0.21, 0.44, -0.22, 0.35),
    "leg_l":  (0.09, 0.45, 0.09, 0.31),
    "leg_r":  (-0.09, 0.45, -0.09, 0.31),
    "shin_l": (0.09, 0.29, 0.09, 0.09),
    "shin_r": (-0.09, 0.29, -0.09, 0.09),
    "foot_l": (0.09, 0.08, 0.09, 0.0),
    "foot_r": (-0.09, 0.08, -0.09, 0.0),
}


def seg_dist(p, s):
    a, b = np.array(s[:2]), np.array(s[2:])
    ab = b - a
    t = 0.0 if not ab.any() else float(np.clip(np.dot(p - a, ab) / np.dot(ab, ab), 0.0, 1.0))
    return float(np.linalg.norm(p - (a + t * ab)))


def shells_of(V, polys):
    # Componenti connesse (forme separate) con union-find.
    par = list(range(len(V)))

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x

    for p, _ in polys:
        for a in p[1:]:
            par[find(a)] = find(p[0])
    comp = {}
    for pi, (p, u) in enumerate(polys):
        comp.setdefault(find(p[0]), []).append(pi)
    return list(comp.values())


def assign(V, polys, shells):
    # Ritorna {pezzo: [indici dei poligoni]}.
    out = {n: [] for n in ORDER}
    for sh in shells:
        idx = sorted({i for pi in sh for i in polys[pi][0]})
        c = (V[idx].min(0) + V[idx].max(0)) / 2.0
        best = min(BONES, key=lambda b: seg_dist(c[:2], BONES[b]))
        if V[idx][:, 0].max() - V[idx][:, 0].min() > 0.2 and abs(c[0]) < 0.05 and 0.72 < c[1] < 0.84:
            best = "torso"          # clavicola: larga quanto le spalle ma centrata sul busto
        out[best] += sh
    return out


def assemble(target_height, V=None, polys=None, UV=None):
    # Ritorna (dimensioni X/Y/Z in unita' motore, scala, {pezzo: dati}). I vertici sono relativi all'origine del
    # pezzo, "polys" sono i poligoni (tri e quad) e "uvs" ha una coppia per ogni angolo di faccia.
    lo, hi = V.min(0), V.max(0)
    k = target_height / (hi[1] - lo[1])
    sgn = -1.0 if P["mirror_x"] else 1.0

    def conv(p):
        return np.array(to_blender((p[0] * sgn * k, (p[1] - lo[1]) * k, p[2] * k)))

    pieces = assign(V, polys, shells_of(V, polys))
    origin = {n: conv(np.array(o, dtype=float)) for n, (_, o) in PIECES.items()}
    # punta del cannone: punto piu' basso dell'avambraccio sinistro
    fl = sorted({i for pi in pieces["fore_l"] for i in polys[pi][0]}, key=lambda i: V[i][1])
    if fl:
        low = [i for i in fl if V[i][1] < V[fl[0]][1] + 0.004]
        tip = V[low].mean(0)
        origin["nano"] = conv(np.array((tip[0], tip[1], tip[2])))
    out = {}
    for n in ORDER:
        par_ = PIECES[n][0]
        d = {"parent": par_, "loc": tuple(origin[n] - (origin[par_] if par_ else 0.0)), "verts": [], "polys": [], "uvs": []}
        remap = {}
        for pi in pieces.get(n, []):
            p, u = polys[pi]
            for i in p:
                if i not in remap:
                    remap[i] = len(d["verts"])
                    d["verts"].append(tuple(conv(V[i]) - origin[n]))
            f = [remap[i] for i in p]
            uv = [(float(UV[j][0]), float(1.0 - UV[j][1] if P["flip_v"] else UV[j][1])) for j in u]
            if P["mirror_x"]:
                f, uv = f[::-1], uv[::-1]
            d["polys"].append(f)
            d["uvs"] += uv
        out[n] = d
    if not out["nano"]["verts"]:
        out["nano"]["verts"] = [(-0.05, 0.0, -0.05), (0.05, 0.0, -0.05), (0.0, 0.0, 0.05)]
        out["nano"]["polys"] = [[0, 2, 1]]
        out["nano"]["uvs"] = [(0.5, 0.5)] * 3
    size = (float((hi[0] - lo[0]) * k), float((hi[2] - lo[2]) * k), float((hi[1] - lo[1]) * k))
    return size, k, out


def to_blender(p):
    # Lavoro: Y su, fronte +Z. Blender: Z su, fronte -Y. Rotazione di 90 gradi attorno a X.
    return (p[0], -p[2], p[1])


def make_tex1(jpg, n, bpy):
    # Texture 1 dal JPG di Tripo (stessa disposizione UV dell'FBX, quindi nessuna ricottura). Alpha = colore del
    # giocatore: dove la texture e' rossa saturata. Senza JPG: grigio uniforme e alpha 0.
    if not jpg:
        img = np.zeros((n, n, 4), np.uint8)
        img[:, :, :3] = (138, 143, 152)
        return img, "assente"
    im = bpy.data.images.load(jpg)
    im.colorspace_settings.name = "Non-Color"
    w, h = im.size
    a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1]      # Blender parte dal basso
    ys = (np.arange(n) * h // n).astype(int)
    xs = (np.arange(n) * w // n).astype(int)
    rgb = np.clip(a[ys][:, xs, :3] * 255.0 + 0.5, 0, 255).astype(np.uint8)
    img = np.zeros((n, n, 4), np.uint8)
    img[:, :, :3] = rgb
    if P["team_mask"] == "red":
        r, g, b = [rgb[:, :, i].astype(np.int32) for i in range(3)]
        mask = (r >= 120) & (r * 2 >= g * 3) & (r * 2 >= b * 3)
        img[:, :, 3] = np.where(mask, 255, 0)
    return img, "%dx%d da %s" % (w, h, os.path.basename(jpg))



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
        print("LLL lettura .s3o fallita (%s): %s" % (path, e))
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


LUA = r"""-- Generato da lllcom.py per l'unita' @NAME@ (Commander Lambda). Non modificare a mano: viene riscritto.
-- Animazioni: camminata, costruzione con il cannone dell'avambraccio sinistro, mira con lo stesso braccio
-- se la definizione dell'unita' ha delle armi.
-- Pezzi: base (bacino), torso (colonna, costole, sterno), head, arm_l/r (spalla), fore_l (gomito e cannone),
--        nano (bocca del cannone), fore_r (gomito e avambraccio), hand_r (mano), leg_l/r (anca),
--        shin_l/r (ginocchio), foot_l/r (caviglia). l = sinistra del robot, r = destra.
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
local STEP = 260               -- millisecondi per fase del passo (4 fasi = un passo completo)
local SPD = rad(140)           -- velocita' di rotazione durante il passo (radianti al secondo)
local AIM_SPD = rad(300)       -- velocita' di busto e braccio quando puntano
local REST_DELAY = 2500        -- dopo quanto tempo il braccio torna giu'

local SIG_WALK = 1
local SIG_ARM = 2
local SIG_REST = 4

local moving = false
local busy = false             -- il braccio sinistro sta puntando (costruzione o mira)
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

-- Le braccia oscillano; il sinistro solo se non sta puntando.
local function Arms(a_left, a_right)
  if not busy then X(arm_l, a_left) end
  X(arm_r, a_right)
end

local function Walk()
  SetSignalMask(SIG_WALK)
  while true do
    -- 1: sinistra avanti, destra indietro e appoggiata
    Leg(leg_l, shin_l, foot_l, 22, 5)
    Leg(leg_r, shin_r, foot_r, -18, 10)
    Arms(-14, 14)
    Sleep(STEP)
    -- 2: passaggio, la destra si stacca e si piega
    Leg(leg_l, shin_l, foot_l, 5, 0)
    Leg(leg_r, shin_r, foot_r, 10, 36)
    Arms(0, 0)
    Sleep(STEP)
    -- 3: destra avanti, sinistra indietro e appoggiata
    Leg(leg_r, shin_r, foot_r, 22, 5)
    Leg(leg_l, shin_l, foot_l, -18, 10)
    Arms(14, -14)
    Sleep(STEP)
    -- 4: passaggio, la sinistra si stacca e si piega
    Leg(leg_r, shin_r, foot_r, 5, 0)
    Leg(leg_l, shin_l, foot_l, 10, 36)
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

-- ---- Braccio sinistro: costruzione e mira -----------------------------------------------
-- A riposo il cannone punta in basso. Per puntare, il busto gira verso il bersaglio (heading) e il gomito
-- alza l'avambraccio di 90 gradi piu' l'inclinazione (pitch): la canna resta sull'asse di mira.

local function PointArm(heading, pitch)
  Turn(torso, y_axis, heading, AIM_SPD)
  Turn(arm_l, x_axis, 0, AIM_SPD)
  Turn(fore_l, x_axis, FWD * (rad(90) + pitch), AIM_SPD)
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
  Turn(arm_l, x_axis, -FWD * rad(8), rad(900))
  Sleep(60)
  Turn(arm_l, x_axis, 0, rad(240))
end

function script.Killed(recentDamage, maxHealth)
  return 1
end
""".replace("@NAME@", NAME)


# ---- parte Blender ---------------------------------------------------------------------------------------

def resolve_height(found):
    th = P["target_height"]
    if isinstance(th, (int, float)):
        return float(th)
    old = read_s3o(found["model"]) if found and found.get("model") and os.path.exists(found["model"]) else None
    if old:
        print("LLL modello attuale: %s | altezza %.1f, larghezza %.1f | %d pezzi %s | %d vertici, %d triangoli | texture %s" % (
            found["model"], old["size"][1], old["size"][0], len(old["pieces"]), old["pieces"][:20], old["verts"],
            old["tris"], old["tex"]))
        if old["size"][1] > 1.0:
            return float(old["size"][1])
    print("LLL altezza: modello attuale non trovato o non leggibile, uso fallback_height", P["fallback_height"])
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
    print("LLL definizione attuale:", found["def"], "| modello:", found["model"], "| script:", found["script"])
    for note in found["notes"]:
        print("LLL ATTENZIONE:", note)

    # 1. Geometria: un oggetto Blender per pezzo, con genitore e posizione relativa
    fbx = find_inputs()
    if not fbx or not os.path.isfile(fbx):
        print("LLL ERRORE: non trovo nessun .fbx accanto allo script (o in P['fbx']). Metti li' l'FBX di Tripo.")
        return
    V, polys, UV, tex_name = fbx_mesh(fbx)
    jpg = find_texture(fbx, tex_name)
    print("LLL FBX:", fbx, "| %d vertici, %d poligoni | texture: %s" % (len(V), len(polys), jpg))
    if not jpg:
        print("LLL ATTENZIONE: texture non trovata (attesa in", tex_name, "): uso un grigio uniforme, senza colore giocatore")
    size, k, data = assemble(resolve_height(found), V, polys, UV)
    print("LLL pezzi e triangoli:", {n: sum(len(f) - 2 for f in data[n]["polys"]) for n in ORDER})
    tris, bverts, loops = count(data)
    print("LLL scala %.4f, dimensioni finali X/Y/Z %.1f %.1f %.1f" % ((k,) + size))
    print("LLL triangoli %d | vertici Blender %d | vertici .s3o attesi: circa %d con i poligoni, fino a %d con i triangoli" % (
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
    print("LLL pezzi:", len(objs), sorted(objs))

    # 2. Texture: tex1 dal JPG di Tripo (alpha = colore giocatore), tex2 piatta
    tex1, tex_info = make_tex1(jpg, P["tex_size"], bpy)
    names = (NAME + "1.png", NAME + "2.png")
    paths = tuple(os.path.join(OUT, n) for n in names)
    write_png_rgba(paths[0], tex1)
    write_png_rgba(paths[1], make_tex2())
    print("LLL texture scritte:", paths, "| sorgente:", tex_info, "| pixel colore giocatore:", int((tex1[:, :, 3] > 127).sum()))

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
        print("LLL .s3o riletto (%s): %d pezzi | %d VERTICI | %d triangoli | altezza %.1f, larghezza %.1f | texture %s | %s" % (
            label, len(new["pieces"]), new["verts"], new["tris"], new["size"][1], new["size"][0], new["tex"],
            "torna" if good else "NON torna: attesi %d pezzi e %d triangoli" % (len(ORDER), tris)))
        return good

    ok = export("poligoni" if P["export_polygons"] else "triangoli")
    if not ok and P["export_polygons"]:
        print("LLL ripiego: rifaccio le mesh a soli triangoli ed esporto di nuovo")
        for name in ORDER:
            old_mesh = objs[name].data
            objs[name].data = make_mesh(name, True)
            objs[name].data.materials.append(mat)
            bpy.data.meshes.remove(old_mesh)
        bpy.context.view_layer.update()
        ok = export("triangoli")
    if not ok:
        print("LLL ATTENZIONE: il .s3o esportato non torna con il modello generato; controllare prima di usarlo")
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