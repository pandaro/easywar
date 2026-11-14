# Easy War - unita' "k116": il mech K116 del kit "Kaiser's Legos", importato cosi' com'e'.
# SCRIPT AUTONOMO: non usa easywar_lib.py. Serve a confrontare questo approccio (kit di pezzi pronti)
# con quello a generazione procedurale (soldier, constructor, engineer).
# Va in easywar_work/base/k116.py. Il nome del file e' il nome dell'unita'.
#
# Cosa serve in easywar_work/kit/ (i file originali del kit):
#   legosv2.obj
#   lego2skin2048_2.png     (atlas 2048x2048; l'atlas da 8192 non serve per il test)
#
# Cosa genera, secondo il canone dei nomi: k116.s3o, k1161.png, k1162.png, k116.lua e la definizione
# unita' units/base/k116.lua (solo se manca). Poi consegna tutto nel gioco.
#
# Uso:
#   flatpak run org.blender.Blender --background --python /home/p/.spring/games/easywar.sdd/easywar_work/base/k116.py | grep -E "K116|S3O_ROOT|DEPLOY|TRIANGOLI"
# Con parametri (JSON dopo "--"), per esempio:
#   ... k116.py -- '{"target_height":50,"team_mode":"none","deploy":false}'
#
# Fatti verificati sul file originale (analisi fuori da Blender): l'oggetto del K116 e' "Object383",
# 598 facce (quadrilateri) = 1280 triangoli, alto 10.25 unita' del kit, asse Y verso l'alto, fronte verso +Z
# (si vedono i due lanciamissili sulle spalle). Le sue UV coprono tutto l'atlas (usa tutte e tre le skin).
# NON verificato: orientamento nel motore, resa del colore squadra, canali di tex2.
import os, sys, re, json, math, struct, zlib, shutil
import numpy as np

HERE = None
try:
    HERE = os.path.abspath(__file__)
except NameError:
    if "--python" in sys.argv:
        HERE = os.path.abspath(sys.argv[sys.argv.index("--python") + 1])
    else:
        HERE = os.path.abspath("k116.py")

P = {
    "kit_dir": None,            # None = easywar_work/kit (cartella sopra "base")
    "obj": "legosv2.obj",
    "atlas": "lego2skin2048_2-2.png",
    "object": "Object383",      # K116 nel catalogo
    "target_height": 40.0,      # altezza in unita' del motore (il soldato e' 36, l'engineer 41)
    "yaw_deg": 180.0,           # come per le altre unita': Blender fronte -Y, poi 180 gradi
    "flip_v": True,             # il motore mostra le texture capovolte rispetto a Blender
    "tex_size": 2048,           # 2048 = atlas intero; 1024 = ridotto a meta' (meno memoria)
    # "red" = la parte rossa del kit diventa colore giocatore (alpha alta); "none" = nessun colore squadra
    "team_mode": "red",
    "out_dir": None,            # None = cartella "out" accanto allo script
    "deploy": True,
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


# ---- parti senza Blender (si possono provare anche fuori) -------------------------------------

def parse_obj(path, object_name):
    # Legge solo i vertici e le facce dell'oggetto richiesto. Gli indici di v/vt sono globali nel file.
    v, vt, cur, faces = [], [], None, []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("v "):
                v.append(tuple(float(x) for x in line.split()[1:4]))
            elif line.startswith("vt "):
                vt.append(tuple(float(x) for x in line.split()[1:3]))
            elif line.startswith("o "):
                cur = line[2:].strip()
            elif line.startswith("f ") and cur == object_name:
                faces.append([tuple(int(x) - 1 for x in t.split("/")[:2]) for t in line.split()[1:]])
    return v, vt, faces


def wings_to_blender(p):
    # Wings: Y su, fronte +Z. Blender: Z su, fronte -Y. E' una rotazione di 90 gradi attorno a X (verso preservato).
    return (p[0], -p[2], p[1])


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
        return
    sx, sy, sz = size_xyz
    lines = [
        '-- Generata da k116.py. Da rivedere: valori non verificati nel motore (movementclass, categoria, immagine).',
        'local unitName  =  "' + name + '"',
        '',
        'local unitDef  =  {',
        '   BuildPic = "Constructor.png", -- segnaposto',
        '   Category = "' + cat + '",',
        '   ObjectName = "base/' + name + '.s3o",',
        '   name = "K116 test",',
        '   Side = "Vroomers",',
        '   UnitName = "K116 test",',
        '   script = "base/' + name + '.lua",',
        '   icontype = "builder",',
        '   Description = "Mech di test dal kit Kaiser.",',
        '   MaxDamage = 800,',
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


LUA = "\n".join([
    "-- Generato da k116.py per l'unita' " + NAME + ". Non modificare a mano: viene riscritto.",
    "-- Primo test del kit: nessuna animazione, il modello e' un pezzo unico.",
    "function script.Create()",
    "  Spring.Echo('[easywar] " + NAME + " Create unitID=' .. tostring(unitID))",
    "end",
    "",
    "function script.Killed(recentDamage, maxHealth)",
    "  return 1",
    "end",
    "",
])


# ---- parte Blender ------------------------------------------------------------------------------

def run_blender():
    import bpy, bmesh
    from mathutils import Matrix

    print("START", NAME, flush=True)
    os.makedirs(OUT, exist_ok=True)
    obj_path = os.path.join(P["kit_dir"], P["obj"])
    atlas_path = os.path.join(P["kit_dir"], P["atlas"])
    for p in (obj_path, atlas_path):
        if not os.path.exists(p):
            print("K116 ERRORE: file del kit non trovato:", p)
            print("K116 metti legosv2.obj e lego2skin2048_2.png in", P["kit_dir"])
            return

    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)

    # 1. Geometria dell'oggetto K116
    v, vt, faces = parse_obj(obj_path, P["object"])
    if not faces:
        print("K116 ERRORE: oggetto", P["object"], "non trovato nell'obj")
        return
    used = sorted({vi for f in faces for vi, _ in f})
    remap = {old: new for new, old in enumerate(used)}
    pts = [wings_to_blender(v[i]) for i in used]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; zs = [p[2] for p in pts]
    height = max(zs) - min(zs)
    k = P["target_height"] / height
    cx, cy, z0 = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, min(zs)
    pts = [((x - cx) * k, (y - cy) * k, (z - z0) * k) for x, y, z in pts]
    size = ((max(xs) - min(xs)) * k, (max(ys) - min(ys)) * k, height * k)
    print("K116 altezza kit %.3f, scala %.4f, dimensioni finali X/Y/Z %.1f %.1f %.1f" % ((height, k) + size))

    mesh = bpy.data.meshes.new(NAME)
    polys = [[remap[vi] for vi, _ in f] for f in faces]
    mesh.from_pydata(pts, [], polys)
    uv = mesh.uv_layers.new(name="UVMap")
    li = 0
    for f in faces:
        for _, ti in f:
            u, w = vt[ti]
            uv.data[li].uv = (u, 1.0 - w if P["flip_v"] else w)
            li += 1
    mesh.update()
    obj = bpy.data.objects.new("base", mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    bm = bmesh.new(); bm.from_mesh(mesh)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(mesh); bm.free()
    for p in mesh.polygons:
        p.use_smooth = False

    # 2. Texture: atlas -> tex1 (con maschera colore giocatore) e tex2 piatta
    img = bpy.data.images.load(atlas_path)
    img.colorspace_settings.name = "Non-Color"
    w, h = img.size
    buf = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(buf)
    rgb = (buf.reshape(h, w, 4)[:, :, :3] * 255 + 0.5).astype(np.uint8)[::-1]   # riga 0 = alto
    print("K116 atlas letto", w, "x", h, "| media RGB terzo sinistro:", rgb[:, :w // 3].reshape(-1, 3).mean(0).round(),
          "(attesa circa 240 78 78 se la lettura e' corretta)")
    tex1 = make_tex1(rgb, P["team_mode"], P["tex_size"])
    names = (NAME + "1.png", NAME + "2.png")
    paths = tuple(os.path.join(OUT, n) for n in names)
    write_png_rgba(paths[0], tex1)
    write_png_rgba(paths[1], make_tex2())
    print("K116 texture scritte:", paths, "| pixel colore giocatore:", int((tex1[:, :, 3] > 127).sum()))

    # Materiale solo per l'anteprima in Blender (il motore usa i PNG)
    mat = bpy.data.materials.new(NAME)
    mat.use_nodes = True
    bsdf = [n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"][0]
    tn = mat.node_tree.nodes.new("ShaderNodeTexImage")
    tn.image = bpy.data.images.load(paths[0])
    mat.node_tree.links.new(tn.outputs["Color"], bsdf.inputs["Base Color"])
    mesh.materials.append(mat)

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
    print("TRIANGOLI", len(mesh.polygons))
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
