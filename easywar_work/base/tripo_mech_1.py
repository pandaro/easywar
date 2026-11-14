# Easy War - unita' "tripo_mech_1": conversione di un modello generato con Tripo (FBX + texture) in unita' Recoil.
# SCRIPT AUTONOMO: non usa easywar_lib.py ne' il kit di Kaiser. Legge direttamente l'FBX (parser interno, nessun
# importer di Blender), divide la mesh unica in pezzi animabili, prepara le due texture e consegna tutto nel gioco.
# Va in easywar_work/base/tripo_mech_1.py. Il nome del file e' il nome dell'unita'.
#
# Cosa serve (cartella easywar_work/tripo/, contenuto dello zip di Tripo):
#   mech_robot_3d_model.fbx
#   mech_robot_3d_model.fbm/mech_robot_3d_model_basecolor.jpg
#
# Cosa genera: tripo_mech_1.s3o, tripo_mech_11.png (tex1: colori + alpha = colore squadra), tripo_mech_12.png (tex2),
# tripo_mech_1.lua e la definizione unita' units/base/tripo_mech_1.lua (solo se manca). Poi consegna nel gioco.
#
# Uso:
#   flatpak run org.blender.Blender --background --python /home/p/.spring/games/easywar.sdd/easywar_work/base/tripo_mech_1.py | grep -E "TRIPO|S3O_ROOT|DEPLOY|TRIANGOLI"
# Con parametri (JSON dopo "--"), per esempio:
#   ... tripo_mech_1.py -- '{"tex_size":2048,"target_height":40,"deploy":false}'
#
# Il modello di Tripo e' una mesh unica di 5370 triangoli: lo script la taglia in pezzi assegnando ogni triangolo
# all'"osso" piu' vicino (testa, busto, spalla, avambraccio, anca, ginocchio, piede). NON riduce i triangoli.
# NON verificato nel motore: tagli ai giunti, resa del colore squadra, animazioni, canali di tex2.
import os, sys, re, json, math, struct, zlib, shutil
import numpy as np

HERE = None
try:
    HERE = os.path.abspath(__file__)
except NameError:
    if "--python" in sys.argv:
        HERE = os.path.abspath(sys.argv[sys.argv.index("--python") + 1])
    else:
        HERE = os.path.abspath("tripo_mech_1.py")

P = {
    "src_dir": None,            # None = cartella "tripo" accanto a "base" (easywar_work/tripo)
    "fbx": "mech_robot_3d_model.fbx",
    "texture": "mech_robot_3d_model.fbm/mech_robot_3d_model_basecolor.jpg",
    "target_height": 36.0,      # altezza in unita' del motore (soldier 36, mech_script_1 36)
    "yaw_deg": 180.0,           # come per le altre unita': Blender fronte -Y, poi 180 gradi
    "flip_v": True,             # il motore mostra le texture capovolte rispetto a Blender
    "tex_size": 1024,           # lato della tex1 (l'originale e' 2048); 2048 = piu' nitida e quattro volte piu' pesante
    "out_dir": None,            # None = cartella "out" accanto allo script
    "deploy": True,
    "weapon": "tripo_gun",      # nome dell'arma definita dentro la definizione dell'unita' (un solo cannone, braccio destro)
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
SRC = P["src_dir"] or os.path.join(os.path.dirname(os.path.dirname(HERE)), "tripo")


# ---- lettura dell'FBX binario (versione 7.x) ------------------------------------------------------------

def parse_fbx(path):
    d = open(path, "rb").read()
    if not d.startswith(b"Kaydara FBX Binary"):
        raise ValueError("FBX non binario: " + path)
    ver = struct.unpack("<I", d[23:27])[0]
    big = ver >= 7500

    def node(pos):
        if big:
            end, nprop, plen, nl = struct.unpack("<QQQB", d[pos:pos + 25]); h = 25
        else:
            end, nprop, plen, nl = struct.unpack("<IIIB", d[pos:pos + 13]); h = 13
        if end == 0:
            return None, pos + h
        name = d[pos + h:pos + h + nl].decode()
        p = pos + h + nl
        props = []
        for _ in range(nprop):
            t = chr(d[p]); p += 1
            if t in "YCFDIL":
                f = {"Y": "<h", "C": "<?", "F": "<f", "D": "<d", "I": "<i", "L": "<q"}[t]
                props.append(struct.unpack(f, d[p:p + struct.calcsize(f)])[0]); p += struct.calcsize(f)
            elif t in "fdilb":
                ln, enc, cl = struct.unpack("<III", d[p:p + 12]); p += 12
                raw = d[p:p + cl]; p += cl
                if enc:
                    raw = zlib.decompress(raw)
                dt = {"f": "<f4", "d": "<f8", "i": "<i4", "l": "<i8", "b": "?"}[t]
                props.append(np.frombuffer(raw, dtype=dt, count=ln))
            elif t in "SR":
                ln = struct.unpack("<I", d[p:p + 4])[0]; p += 4
                raw = d[p:p + ln]; p += ln
                props.append(raw.decode("latin1") if t == "S" else raw)
            else:
                raise ValueError("tipo di proprieta' FBX sconosciuto: " + t)
        children = []
        p = pos + h + nl + plen
        while p < end:
            c, p = node(p)
            if c is None:
                break
            children.append(c)
        return (name, props, children), end

    pos = 27
    roots = []
    while pos < len(d) - 40:
        n, pos = node(pos)
        if n is None:
            break
        roots.append(n)
    return roots


def fchild(n, name):
    return [c for c in n[2] if c[0] == name]


def load_fbx(path):
    # Ritorna vertici (N,3), triangoli (M,3) con indici di vertice, UV (K,2) e indici UV per angolo (M,3).
    roots = parse_fbx(path)
    obj = [x for x in roots if x[0] == "Objects"][0]
    g = [c for c in obj[2] if c[0] == "Geometry"][0]
    V = fchild(g, "Vertices")[0][1][0].reshape(-1, 3).astype(float)
    I = fchild(g, "PolygonVertexIndex")[0][1][0]
    le = fchild(g, "LayerElementUV")[0]
    UV = fchild(le, "UV")[0][1][0].reshape(-1, 2).astype(float)
    UVI = fchild(le, "UVIndex")[0][1][0]
    tris, uvt, poly = [], [], []
    for k, i in enumerate(I):
        poly.append(k)
        if i < 0:
            idx = [int(I[j]) if I[j] >= 0 else int(~I[j]) for j in poly]
            for a in range(1, len(poly) - 1):
                tris.append((idx[0], idx[a], idx[a + 1]))
                uvt.append((int(UVI[poly[0]]), int(UVI[poly[a]]), int(UVI[poly[a + 1]])))
            poly = []
    return V, np.array(tris), UV, np.array(uvt)


# ---- divisione in pezzi ---------------------------------------------------------------------------------
# Sistema del modello: Y su, fronte +Z, altezza 1.0 (dopo la normalizzazione qui sotto). X>0 = lato del cannone.
# Ogni osso e' una o piu' linee (x,y) -> (x,y) con un raggio; ogni triangolo va all'osso piu' vicino (distanza dal
# segmento meno il raggio, in vista frontale). Poi le parti staccate piccole seguono il pezzo che ha la maggioranza.

BONES = {
    "base":   [((0.02, 0.52), (0.02, 0.80), 0.105)],
    "head":   [((0.02, 0.87), (0.02, 0.97), 0.075)],
    "arm_r":  [((0.135, 0.80), (0.204, 0.606), 0.05)],
    "fore_r": [((0.204, 0.606), (0.245, 0.40), 0.05)],
    "arm_l":  [((-0.10, 0.79), (-0.178, 0.606), 0.05)],
    "fore_l": [((-0.178, 0.606), (-0.20, 0.52), 0.05), ((-0.20, 0.52), (-0.225, 0.38), 0.03)],
    "leg_r":  [((0.10, 0.50), (0.124, 0.322), 0.07)],
    "shin_r": [((0.124, 0.322), (0.165, 0.11), 0.07)],
    "foot_r": [((0.17, 0.075), (0.19, 0.03), 0.05)],
    "leg_l":  [((-0.06, 0.50), (-0.08, 0.33), 0.06)],
    "shin_l": [((-0.08, 0.33), (-0.142, 0.02), 0.03), ((-0.142, 0.02), (-0.14, 0.0), 0.07)],
}
# Origini dei pezzi (giunti) nel sistema del modello: (x, y). La z si ricava dai vertici vicini.
JOINTS = {
    "base": (0.02, 0.52), "head": (0.02, 0.86),
    "arm_r": (0.135, 0.80), "fore_r": (0.204, 0.606),
    "arm_l": (-0.10, 0.79), "fore_l": (-0.178, 0.606),
    "leg_r": (0.10, 0.50), "shin_r": (0.124, 0.322), "foot_r": (0.17, 0.075),
    "leg_l": (-0.06, 0.50), "shin_l": (-0.08, 0.33),
}
PARENT = {"base": None, "head": "base", "arm_r": "base", "fore_r": "arm_r", "muzzle_r": "fore_r",
          "arm_l": "base", "fore_l": "arm_l", "leg_r": "base", "shin_r": "leg_r", "foot_r": "shin_r",
          "leg_l": "base", "shin_l": "leg_l"}
ORDER = ["base", "head", "arm_r", "fore_r", "muzzle_r", "arm_l", "fore_l", "leg_r", "shin_r", "foot_r", "leg_l", "shin_l"]


def segdist(Pt, a, b):
    a = np.array(a); b = np.array(b); ab = b - a
    t = np.clip(((Pt - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(Pt - (a + t[:, None] * ab), axis=1)


def components(T, nv):
    # Parti connesse della mesh (union-find in Python puro: dentro Blender non c'e' scipy).
    parent = list(range(nv))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b, c in T.tolist():
        ra, rb, rc = find(a), find(b), find(c)
        parent[rb] = ra
        parent[find(rc)] = find(ra)
    roots = {}
    lab = np.array([roots.setdefault(find(i), len(roots)) for i in range(nv)])
    return len(roots), lab


def partition(V, T, min_comp=900):
    nc, lab = components(T, len(V))
    tl = lab[T[:, 0]]
    cen = V[T].mean(1)[:, :2]
    names = list(BONES)
    D = np.full((len(T), len(names)), 1e9)
    for j, n in enumerate(names):
        for (p, q, r) in BONES[n]:
            D[:, j] = np.minimum(D[:, j], segdist(cen, p, q) - r)
    out = np.array(names)[D.argmin(1)]
    for c in range(nc):
        m = tl == c
        if m.sum() < min_comp:
            vals, cnt = np.unique(out[m], return_counts=True)
            out[m] = vals[np.argmax(cnt)]
    return out


def to_blender(p):
    # Modello: Y su, fronte +Z. Blender: Z su, fronte -Y. Rotazione di 90 gradi attorno a X.
    return (p[0], -p[2], p[1])


def assemble():
    # Ritorna (dimensioni X/Y/Z in unita' motore, scala, {pezzo: dati}) con vertici relativi all'origine del pezzo.
    fbx = os.path.join(SRC, P["fbx"])
    if not os.path.exists(fbx):
        raise SystemExit("TRIPO ERRORE: manca " + fbx)
    V, T, UV, UT = load_fbx(fbx)
    lo, hi = V.min(0), V.max(0)
    height = hi[1] - lo[1]
    print("TRIPO FBX: %d vertici, %d triangoli, altezza %.3f, larghezza %.3f, profondita' %.3f" % (
        len(V), len(T), height, hi[0] - lo[0], hi[2] - lo[2]))
    V = (V - np.array([0.0, lo[1], 0.0])) / height          # altezza 1, piedi a y=0
    k = P["target_height"]
    names = partition(V, T)
    for n in ORDER:
        if n != "muzzle_r":
            print("TRIPO pezzo %-7s %5d triangoli" % (n, int((names == n).sum())))

    # origine di ogni pezzo: (x, y) del giunto, z = media dei vertici del pezzo vicini al giunto
    origin = {}
    for n in ORDER:
        if n == "muzzle_r":
            continue
        used = np.unique(T[names == n])
        pts = V[used]
        jx, jy = JOINTS[n]
        near = pts[np.linalg.norm(pts[:, :2] - np.array([jx, jy]), axis=1) < 0.06]
        z = float(near[:, 2].mean()) if len(near) else float(pts[:, 2].mean())
        origin[n] = np.array([jx, jy, z])
    # bocca del cannone: il punto piu' basso dell'avambraccio destro
    fr = V[np.unique(T[names == "fore_r"])]
    low = fr[fr[:, 1] <= fr[:, 1].min() + 0.01]
    origin["muzzle_r"] = np.array([float(low[:, 0].mean()), float(fr[:, 1].min()) + 0.005, float(low[:, 2].mean())])

    def conv(p):
        return np.array(to_blender(np.array(p) * k))

    org_b = {n: conv(o) for n, o in origin.items()}
    out = {}
    for n in ORDER:
        par = PARENT[n]
        out[n] = {"parent": par, "loc": tuple(org_b[n] - (org_b[par] if par else 0.0)), "verts": [], "polys": [], "uvs": []}
    for n in ORDER:
        if n == "muzzle_r":
            d = out[n]    # un triangolino nascosto dentro la canna: serve solo a far esistere il pezzo
            d["verts"] = [(0.0, 0.0, 0.0), (0.04, 0.0, 0.0), (0.0, 0.0, 0.04)]
            d["polys"] = [[0, 1, 2]]
            d["uvs"] = [(0.5, 0.5)] * 3
            continue
        sel = np.where(names == n)[0]
        used = sorted(set(T[sel].ravel().tolist()))
        remap = {v: i for i, v in enumerate(used)}
        d = out[n]
        d["verts"] = [tuple(conv(V[v]) - org_b[n]) for v in used]
        for t, u in zip(T[sel], UT[sel]):
            d["polys"].append([remap[int(t[0])], remap[int(t[1])], remap[int(t[2])]])
            for c in range(3):
                uu, vv = UV[u[c]]
                d["uvs"].append((float(uu), float(1.0 - vv) if P["flip_v"] else float(vv)))
    size = (float((hi[0] - lo[0]) / height * k), float((hi[2] - lo[2]) / height * k), float(k))
    return size, k, out


# ---- texture ---------------------------------------------------------------------------------------------

def team_mask(rgb):
    # Alpha alto = colore giocatore. Qui: i pixel di rosso saturo (spallaccio, occhio, scritte, placca dello stinco).
    f = rgb.astype(np.float32) / 255.0
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    mx = f.max(-1); mn = f.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1e-4)
    score = (np.clip((r - np.maximum(g, b) * 1.6) / 0.18, 0, 1)
             * np.clip((sat - 0.45) / 0.25, 0, 1) * np.clip((r - 0.22) / 0.15, 0, 1))
    return (score * 255).astype(np.uint8)


def load_rgb(path):
    try:
        from PIL import Image
        return np.asarray(Image.open(path).convert("RGB"))
    except ImportError:
        import bpy
        img = bpy.data.images.load(path)
        img.colorspace_settings.name = "Non-Color"      # nessuna conversione: byte / 255
        w, h = img.size
        buf = np.empty(w * h * 4, np.float32)
        img.pixels.foreach_get(buf)
        arr = buf.reshape(h, w, 4)[::-1, :, :3]            # Blender parte dal basso
        return (np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8)


def make_tex1(n):
    path = os.path.join(SRC, P["texture"])
    if not os.path.exists(path):
        raise SystemExit("TRIPO ERRORE: manca " + path)
    rgb = load_rgb(path)
    print("TRIPO texture originale %dx%d, media RGB %s" % (rgb.shape[1], rgb.shape[0], rgb.reshape(-1, 3).mean(0).round(1).tolist()))
    alpha = team_mask(rgb)
    img = np.dstack([rgb, alpha]).astype(np.float32)
    while img.shape[0] > n and img.shape[0] % 2 == 0:
        h, w = img.shape[:2]
        img = img.reshape(h // 2, 2, w // 2, 2, 4).mean(axis=(1, 3))
    out = np.clip(img + 0.5, 0, 255).astype(np.uint8)
    print("TRIPO tex1 %dx%d, pixel colore giocatore: %.1f%%" % (out.shape[1], out.shape[0], 100.0 * (out[:, :, 3] > 127).mean()))
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


# ---- definizione unita' ----------------------------------------------------------------------------------

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
            print("DEPLOY    (cancella il file e rilancia lo script: la ricrea con weapondefs e weapons)")
        return
    sx, sy, sz = size_xyz
    lines = [
        '-- Generata da tripo_mech_1.py. Da rivedere: valori non verificati nel motore (movementclass, categoria, immagine).',
        'local unitName  =  "' + name + '"',
        '',
        'local unitDef  =  {',
        '   BuildPic = "Constructor.png", -- segnaposto',
        '   Category = "' + cat + '",',
        '   ObjectName = "base/' + name + '.s3o",',
        '   name = "Tripo mech 1",',
        '   Side = "Vroomers",',
        '   UnitName = "Tripo mech 1",',
        '   script = "base/' + name + '.lua",',
        '   icontype = "builder",',
        '   Description = "Mech da modello Tripo: cannone sul braccio destro, uncino sul sinistro.",',
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
        '         name = "Tripo mech cannon",',
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


LUA = r"""-- Generato da tripo_mech_1.py per l'unita' @NAME@. Non modificare a mano: viene riscritto.
-- Animazioni: camminata (gambe e braccia), mira e sparo con il cannone del braccio destro (arma 1).
-- Pezzi: base (busto e bacino), head, arm_r/l (spalla con spallaccio), fore_r/l (gomito con avambraccio e mano),
--        muzzle_r (bocca del cannone), leg_r/l (anca), shin_r/l (ginocchio), foot_r (caviglia; la gamba sinistra
--        e' un piolo e non ha piede separato).
--
-- CONVENZIONE DEL SEGNO (dedotta dal test dell'engineer, dove un angolo positivo sull'asse x
-- ha portato il braccio indietro): sull'asse x un angolo NEGATIVO porta il pezzo in avanti.
-- Se nel gioco gambe e braccia vanno al contrario, basta mettere FWD = 1.

local base, head = piece('base', 'head')
local arm_l, arm_r = piece('arm_l', 'arm_r')
local fore_l, fore_r = piece('fore_l', 'fore_r')
local muzzle_r = piece('muzzle_r')
local leg_l, leg_r = piece('leg_l', 'leg_r')
local shin_l, shin_r = piece('shin_l', 'shin_r')
local foot_r = piece('foot_r')

local FWD = -1                 -- segno di "avanti" sull'asse x
local rad = math.rad
local STEP = 240               -- millisecondi per fase del passo (4 fasi = un passo completo)
local SPD = rad(150)           -- velocita' di rotazione durante il passo (radianti al secondo)
local AIM_SPD = rad(360)       -- velocita' del braccio quando mira
local REST_DELAY = 2500        -- dopo quanto tempo senza sparare il braccio torna giu'

local SIG_WALK = 1
local SIG_AIM = 2
local SIG_REST = 4

local moving = false
local aiming = false

-- Gira un pezzo sull'asse x: a > 0 = in avanti (il segno lo mette FWD).
local function X(p, a, spd)
  Turn(p, x_axis, FWD * rad(a), spd or SPD)
end

-- Una posa delle gambe: coscia, ginocchio (positivo = piegato) e, se c'e', piede tenuto piatto.
local function Leg(thigh, shin, foot, a_thigh, a_knee)
  X(thigh, a_thigh)
  X(shin, -a_knee)
  if foot then X(foot, a_knee - a_thigh) end
end

-- Il braccio del cannone oscilla solo se non sta mirando; quello con l'uncino oscilla sempre.
local function Arms(a_right, a_left)
  if not aiming then X(arm_r, a_right) end
  X(arm_l, a_left)
end

local function Walk()
  SetSignalMask(SIG_WALK)
  while true do
    -- 1: sinistra avanti, destra indietro e appoggiata
    Leg(leg_l, shin_l, nil, 20, 5)
    Leg(leg_r, shin_r, foot_r, -16, 8)
    Arms(12, -12)
    Sleep(STEP)
    -- 2: passaggio, la destra si stacca e si piega
    Leg(leg_l, shin_l, nil, 4, 0)
    Leg(leg_r, shin_r, foot_r, 8, 30)
    Arms(0, 0)
    Sleep(STEP)
    -- 3: destra avanti, sinistra indietro e appoggiata
    Leg(leg_r, shin_r, foot_r, 20, 5)
    Leg(leg_l, shin_l, nil, -16, 8)
    Arms(-12, 12)
    Sleep(STEP)
    -- 4: passaggio, la sinistra si stacca e si piega
    Leg(leg_r, shin_r, foot_r, 4, 0)
    Leg(leg_l, shin_l, nil, 8, 30)
    Arms(0, 0)
    Sleep(STEP)
  end
end

local function StandStill()
  for _, p in ipairs({ leg_l, leg_r, shin_l, shin_r, foot_r }) do
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

-- ---- Arma 1: cannone del braccio destro ---------------------------------------------
-- A riposo la canna punta in basso. Per mirare la spalla gira verso il bersaglio (heading) e il gomito
-- alza l'avambraccio di 90 gradi piu' l'inclinazione (pitch): la canna resta sull'asse di mira.

local function Rest()
  SetSignalMask(SIG_REST)
  Sleep(REST_DELAY)
  aiming = false
  Turn(arm_r, y_axis, 0, AIM_SPD / 2)
  Turn(arm_r, x_axis, 0, AIM_SPD / 2)
  Turn(fore_r, x_axis, 0, AIM_SPD / 2)
end

function script.AimFromWeapon(n)
  return fore_r
end

function script.QueryWeapon(n)
  return muzzle_r
end

function script.AimWeapon(n, heading, pitch)
  Signal(SIG_AIM)
  SetSignalMask(SIG_AIM)
  Signal(SIG_REST)
  aiming = true
  Turn(arm_r, x_axis, 0, AIM_SPD)
  Turn(arm_r, y_axis, heading, AIM_SPD)
  Turn(fore_r, x_axis, FWD * (rad(90) + pitch), AIM_SPD)
  WaitForTurn(arm_r, y_axis)
  WaitForTurn(fore_r, x_axis)
  StartThread(Rest)
  return true
end

-- Rinculo: la spalla scatta indietro e torna.
function script.FireWeapon(n)
  Turn(arm_r, x_axis, -FWD * rad(8), rad(900))
  Sleep(60)
  Turn(arm_r, x_axis, 0, rad(240))
end

function script.Killed(recentDamage, maxHealth)
  return 1
end
""".replace("@NAME@", NAME)


# ---- parte Blender ---------------------------------------------------------------------------------------

def run_blender():
    import bpy

    print("START", NAME, flush=True)
    os.makedirs(OUT, exist_ok=True)
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)

    # 1. Geometria: un oggetto Blender per pezzo, con genitore e posizione relativa
    size, k, data = assemble()
    print("TRIPO scala %.2f, dimensioni finali X/Y/Z %.1f %.1f %.1f" % ((k,) + size))
    objs = {}
    for name in ORDER:
        d = data[name]
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(d["verts"], [], d["polys"])
        uv = mesh.uv_layers.new(name="UVMap")
        for li, uvc in enumerate(d["uvs"]):
            uv.data[li].uv = uvc
        mesh.update()
        for p in mesh.polygons:
            p.use_smooth = False
        ob = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(ob)
        objs[name] = ob
    for name in ORDER:
        d = data[name]
        if d["parent"]:
            objs[name].parent = objs[d["parent"]]
        objs[name].location = d["loc"]
    obj = objs["base"]
    print("TRIPO pezzi:", len(objs), sorted(objs))

    # 2. Texture: tex1 dall'originale (+ alpha = colore giocatore), tex2 piatta
    tex1 = make_tex1(P["tex_size"])
    names = (NAME + "1.png", NAME + "2.png")
    paths = tuple(os.path.join(OUT, n) for n in names)
    write_png_rgba(paths[0], tex1)
    write_png_rgba(paths[1], make_tex2())
    print("TRIPO texture scritte:", paths)

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
