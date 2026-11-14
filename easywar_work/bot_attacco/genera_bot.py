# Easy War - test 1: generatore procedurale del bot d'attacco (stile neutro).
# Esegue in Blender (Python). Genera pezzi gerarchici con nomi unici, UV, due texture PNG
# e salva un .blend. NON esporta .s3o: l'export si fa dal menu di S3O Kit.
#
# Uso (esempio):
#   flatpak run org.blender.Blender --background --python /PERCORSO/genera_bot.py
# Variante con parametri (JSON dopo "--"):
#   flatpak run org.blender.Blender --background --python /PERCORSO/genera_bot.py -- '{"seed":2,"torso":[2.0,1.2,1.4],"barrel_len":2.4}'
import bpy, bmesh, json, math, os, random, shutil, sys
from mathutils import Vector, Matrix

P = {
    "seed": 1,
    "out_dir": os.path.expanduser("~/.spring/games/easywar.sdd/easywar_work/bot_attacco"),
    "bevel": 0.06,          # 0 = niente smusso (meno triangoli)
    "cyl_segments": 10,
    "pelvis": [1.2, 0.8, 0.5],
    "torso": [1.6, 1.0, 1.3],
    "head": [0.8, 0.7, 0.55],
    "leg_len": 1.2,
    "leg_w": 0.4,
    "hip_x": 0.55,
    "barrel_len": 1.8,
    "barrel_r": 0.12,
    "tex_size": 256,
    "model_name": "soldier",   # nome unita' predefinito; si cambia passando un nome dopo "--"
    # Consegna automatica nel gioco (tutto dentro game_dir). Con "deploy": false genera solo in out_dir.
    "deploy": True,
    "game_dir": os.path.expanduser("~/.spring/games/easywar.sdd"),
    "dir_model": "objects3d/base",       # NOME.s3o
    "dir_textures": "unittextures",      # NOME1.png e NOME2.png (il modello le richiama per nome semplice)
    "dir_script": "scripts/base",        # NOME.lua (animazione)
    "turret_spin": True,                 # prova: la torretta gira di continuo
    "walk": True,                        # camminata essenziale (gambe) su StartMoving/StopMoving
    "flip_v": True,        # ribalta V delle UV (il motore mostra le texture capovolte rispetto a Blender)
    "yaw_deg": 180.0,      # rotazione del fronte (0 = fronte verso -Y in Blender)
    "scale": 10.0,         # moltiplicatore globale del modello (1 = scala originale)
}
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
for _a in argv:
    # Un argomento che inizia con "{" e' JSON di parametri; qualunque altro e' il nome dell'unita'.
    if _a.strip().startswith("{"):
        P.update(json.loads(_a))
    else:
        P["model_name"] = _a.strip()
NAME = P["model_name"]   # nome unita': da' nome a .s3o, .blend, texture (NOME1.png, NOME2.png) e radice

# Rettangoli UV (u0, v0, u1, v1) per zona materiale, nell'atlante di tex1.
ZONES = {
    "armor":  (0.0, 0.5, 0.5, 1.0),
    "dark":   (0.5, 0.5, 1.0, 1.0),
    "team":   (0.0, 0.0, 0.5, 0.5),   # zona colore giocatore
    "accent": (0.5, 0.0, 1.0, 0.5),
}
COLORS = {
    "armor": (0.55, 0.57, 0.60), "dark": (0.18, 0.19, 0.21),
    "team": (0.80, 0.80, 0.80), "accent": (0.90, 0.60, 0.10),
}

print("START genera_bot", flush=True)
# Niente read_factory_settings: ricarica gli add-on e in modalita' --python puo' interrompere lo script in silenzio.
for _ob in list(bpy.data.objects):
    bpy.data.objects.remove(_ob, do_unlink=True)
rng = random.Random(P["seed"])
os.makedirs(P["out_dir"], exist_ok=True)


def zone_of(u, v):
    if u < 0.5:
        return "armor" if v >= 0.5 else "team"
    return "dark" if v >= 0.5 else "accent"


def write_png(path, n, px):
    import struct, zlib
    raw = bytearray()
    for y in range(n - 1, -1, -1):  # PNG parte dalla riga alta, i pixel di Blender dalla bassa
        raw.append(0)
        row = px[y * n * 4:(y + 1) * n * 4]
        raw += bytes(int(max(0.0, min(1.0, v)) * 255 + 0.5) for v in row)

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    data = (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", n, n, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(data)


def make_images():
    n = P["tex_size"]
    p1, p2 = [], []
    for y in range(n):
        for x in range(n):
            z = zone_of(x / n, y / n)
            c = COLORS[z]
            k = rng.uniform(-0.03, 0.03)
            # ASSUNZIONE da verificare: alpha di tex1 = maschera colore giocatore
            p1 += [c[0] + k, c[1] + k, c[2] + k, 1.0 if z == "team" else 0.0]
            # ASSUNZIONE da verificare: tex2 R=luminosita' propria, G=riflessione
            p2 += [0.6 if z == "accent" else 0.0, 0.3, 0.0, 1.0]
    # I PNG si scrivono a mano (RGBA 8 bit): il salvataggio di Blender azzera il colore dove alpha = 0.
    paths = []
    for name, px in ((NAME + "1", p1), (NAME + "2", p2)):
        path = os.path.join(P["out_dir"], name + ".png")
        write_png(path, n, px)
        paths.append(path)
    i1 = bpy.data.images.load(paths[0])
    i2 = bpy.data.images.load(paths[1])
    i1.alpha_mode = "CHANNEL_PACKED"   # in Blender l'alpha non modifica il colore mostrato
    i2.alpha_mode = "CHANNEL_PACKED"
    i2.colorspace_settings.name = "Non-Color"
    return i1, i2


img1, img2 = make_images()
mat = bpy.data.materials.new("mat_easywar_bot")
mat.use_nodes = True
nt = mat.node_tree
# I nomi dei nodi sono tradotti con Blender in italiano ("Generico BSDF"): si cerca per tipo, non per nome.
bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
assert bsdf is not None, "Nodo Principled non trovato"
t1 = nt.nodes.new("ShaderNodeTexImage"); t1.image = img1
t2 = nt.nodes.new("ShaderNodeTexImage"); t2.image = img2
t1.location = (-400, 200); t2.location = (-400, -100)
nt.links.new(t1.outputs["Color"], bsdf.inputs["Base Color"])
print("COLLEGAMENTI", len(nt.links), "(attesi 2: texture->Base Color e BSDF->uscita)")

coll = bpy.context.scene.collection
objs = {}


def box(size, off):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]; v.co.y *= size[1]; v.co.z *= size[2]
    return bm, off, min(size)


def cyl(radius, depth, axis, off):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=P["cyl_segments"],
                          radius1=radius, radius2=radius, depth=depth)
    if axis == "y":
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0),
                         matrix=Matrix.Rotation(math.radians(90), 3, "X"))
    return bm, off, None


def finish(bm, off, minsize, zone):
    for v in bm.verts:
        v.co += Vector(off)
    if minsize is not None and P["bevel"] > 0:
        b = min(P["bevel"], minsize * 0.3)
        bmesh.ops.bevel(bm, geom=list(bm.verts) + list(bm.edges), offset=b,
                        offset_type="OFFSET", segments=1, profile=0.5, affect="EDGES")
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.normal_update()
    uvl = bm.loops.layers.uv.verify()
    mn = [min(v.co[i] for v in bm.verts) for i in range(3)]
    mx = [max(v.co[i] for v in bm.verts) for i in range(3)]
    u0, v0, u1, v1 = ZONES[zone]
    m = 0.02
    for f in bm.faces:
        ax = max(range(3), key=lambda i: abs(f.normal[i]))
        a, b = ((1, 2), (0, 2), (0, 1))[ax]
        for l in f.loops:
            c = l.vert.co
            s = (c[a] - mn[a]) / max(mx[a] - mn[a], 1e-6)
            t = (c[b] - mn[b]) / max(mx[b] - mn[b], 1e-6)
            uu = u0 + m + s * (u1 - u0 - 2 * m)
            vv = v0 + m + t * (v1 - v0 - 2 * m)
            # Nel motore le texture risultano ribaltate in verticale rispetto all'anteprima di Blender
            # (dedotto dai colori osservati): si ribalta V. L'anteprima in Blender sara' quindi capovolta.
            l[uvl].uv = (uu, 1.0 - vv if P["flip_v"] else vv)
    return bm


def add(name, parent, loc, made, zone):
    assert name not in objs, "nome duplicato: " + name
    bm = finish(*made, zone)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    ob = bpy.data.objects.new(name, mesh)
    coll.objects.link(ob)
    ob.parent = objs.get(parent)
    ob.location = loc
    objs[name] = ob


pelvis, torso, head = P["pelvis"], P["torso"], P["head"]
L, W = P["leg_len"], P["leg_w"]
thigh = shin = L / 2

# Convenzione: Z su, fronte = -Y (da verificare nel motore dopo l'export).
add("base", None, (0, 0, 0), box(pelvis, (0, 0, L + pelvis[2] / 2)), "dark")
add("torso", "base", (0, 0, L + pelvis[2]), box(torso, (0, 0, torso[2] / 2)), "armor")
add("plate", "torso", (0, torso[1] / 2, torso[2] * 0.5),
    box((torso[0] * 0.6, 0.08, torso[2] * 0.6), (0, 0.04, 0)), "team")
add("head", "torso", (0, -torso[1] * 0.15, torso[2]), box(head, (0, 0, head[2] / 2)), "dark")
add("sensor", "head", (0, -head[1] / 2, head[2] * 0.5), box((0.25, 0.1, 0.12), (0, -0.05, 0)), "accent")
add("turret", "torso", (torso[0] / 2 + 0.15, -torso[1] * 0.1, torso[2] * 0.7),
    cyl(0.22, 0.35, "z", (0, 0, 0)), "armor")
add("barrel", "turret", (0, 0, 0),
    cyl(P["barrel_r"], P["barrel_len"], "y", (0, -P["barrel_len"] / 2, 0)), "dark")
for side, sx in (("l", -1), ("r", 1)):
    add("leg_" + side, "base", (sx * P["hip_x"], 0, L), box((W, W, thigh), (0, 0, -thigh / 2)), "armor")
    add("shin_" + side, "leg_" + side, (0, 0, -thigh),
        box((W * 0.8, W * 0.8, shin), (0, 0, -shin / 2)), "armor")
    add("foot_" + side, "shin_" + side, (0, 0, -shin),
        box((W * 1.3, W * 2.0, W * 0.4), (0, -W * 0.4, -W * 0.2)), "dark")

# --- Scala finale: tutto il modello (geometria e posizioni dei pezzi) viene moltiplicato per P["scale"].
S = P["scale"]
for _ob in objs.values():
    _ob.location = _ob.location * S
    _ob.data.transform(Matrix.Scale(S, 4))

# --- Fronte: nel motore il bot camminava all'indietro, quindi si ruota di 180 gradi attorno alla verticale.
objs["base"].rotation_euler = (0.0, 0.0, math.radians(P["yaw_deg"]))

# --- Radice S3O ---------------------------------------------------------------------------
# S3O Kit vuole un oggetto speciale "S3O Root" (pulsante "Add S3O Root"). Non conosco i nomi interni
# dell'operatore: lo cerco tra quelli installati per etichetta e stampo cosa trovo. Se non va, lo script
# NON si ferma: salva comunque il .blend e la radice si aggiunge a mano.
def find_s3o_root_operator():
    for mod in dir(bpy.ops):
        if mod.startswith("_"):
            continue
        try:
            m = getattr(bpy.ops, mod)
            names = dir(m)
        except Exception:
            continue
        for nm in names:
            if nm.startswith("_"):
                continue
            try:
                op = getattr(m, nm)
                rna = op.get_rna_type()
            except Exception:
                continue
            if "s3o" in nm.lower() and "root" in (rna.name + nm).lower():
                return op, mod + "." + nm, rna
    return None, None, None


root_obj = None
op, op_id, rna = find_s3o_root_operator()
if op is None:
    print("S3O_ROOT: operatore 'Add S3O Root' non trovato -> aggiungere la radice a mano")
else:
    props = [p.identifier for p in rna.properties if p.identifier != "rna_type"]
    print("S3O_ROOT operatore:", op_id, "| proprieta':", props)
    tex_names = (NAME + "1.png", NAME + "2.png")
    want = {}
    for ident in props:
        k = ident.lower()
        if k == "name" or k.endswith("_name") or k == "model_name":
            want[ident] = P["model_name"]
        elif k == "texture_name_1":
            want[ident] = tex_names[0]
        elif k == "texture_name_2":
            want[ident] = tex_names[1]
    before = set(bpy.data.objects.keys())
    try:
        res = op("EXEC_DEFAULT", **want)
        print("S3O_ROOT impostato:", want, "->", res)
    except Exception as e:
        print("S3O_ROOT errore con parametri, riprovo con i predefiniti:", e)
        try:
            print("S3O_ROOT ->", op("EXEC_DEFAULT"))
        except Exception as e2:
            print("S3O_ROOT errore:", e2)
    new = [bpy.data.objects[n] for n in bpy.data.objects.keys() if n not in before]
    print("S3O_ROOT oggetti creati:", [o.name for o in new])
    tops = [o for o in new if o.parent is None and o.type == "EMPTY"]
    if tops:
        root_obj = tops[0]
        bpy.context.view_layer.update()
        print("S3O_ROOT rotazione (rad):", tuple(root_obj.rotation_euler), "scala:", tuple(root_obj.scale))
        objs["base"].parent = root_obj
        # Compensa l'eventuale rotazione/scala del root: il bot resta dritto come costruito (Z su, fronte -Y).
        objs["base"].matrix_parent_inverse = root_obj.matrix_world.inverted()
        print("S3O_ROOT radice:", root_obj.name, "| base ora figlio della radice, orientamento compensato")
        for k, v in root_obj.items():
            print("  proprieta' personalizzata", k, "=", v)

active = root_obj or objs["base"]
bpy.context.view_layer.objects.active = active
for _o in bpy.data.objects:
    _o.select_set(_o is active)

# --- Export automatico .s3o (l'operatore esatto non lo conosco: lo cerco e stampo cosa trovo) ------
s3o_path = os.path.join(P["out_dir"], NAME + ".s3o")
try:
    ops_mod = bpy.ops.s3o_tools
    names = [n for n in dir(ops_mod) if not n.startswith("_")]
    print("S3O_ROOT operatori s3o_tools:", names)
    exp = next((getattr(ops_mod, n) for n in names if "export" in n.lower()), None)
    if exp is None:
        print("S3O_ROOT export: nessun operatore di export trovato")
    else:
        erna = exp.get_rna_type()
        eprops = [p.identifier for p in erna.properties if p.identifier != "rna_type"]
        print("S3O_ROOT export proprieta':", eprops)
        kw = {i: s3o_path for i in eprops if "filepath" in i.lower()}
        print("S3O_ROOT export risultato:", exp("EXEC_DEFAULT", **kw))
        print("S3O_ROOT file s3o:", s3o_path, os.path.getsize(s3o_path) if os.path.exists(s3o_path) else "NON CREATO")
except Exception as e:
    print("S3O_ROOT export errore:", e)

# --- Script di animazione (Lua) -------------------------------------------------------------
# ASSUNZIONI DA VERIFICARE: gadget degli script Lua attivo (funzionava col test del cannone), assi x_axis/y_axis,
# segno dei gradi. I pezzi sono nominati come gli oggetti di Blender.
def lua_text():
    L = []
    a = L.append
    a("-- Generato da genera_bot.py per l'unita' " + NAME + ". Non modificare a mano: viene riscritto.")
    a("local base, turret, leg_l, leg_r, shin_l, shin_r = piece('base', 'turret', 'leg_l', 'leg_r', 'shin_l', 'shin_r')")
    a("")
    a("local SIG_WALK = 1")
    a("")
    a("local function Walk()")
    a("  Signal(SIG_WALK)")
    a("  SetSignalMask(SIG_WALK)")
    a("  while true do")
    a("    Turn(leg_l, x_axis, math.rad(35), math.rad(160))")
    a("    Turn(leg_r, x_axis, math.rad(-35), math.rad(160))")
    a("    Turn(shin_l, x_axis, 0, math.rad(160))")
    a("    Turn(shin_r, x_axis, math.rad(40), math.rad(160))")
    a("    Sleep(220)")
    a("    Turn(leg_l, x_axis, math.rad(-35), math.rad(160))")
    a("    Turn(leg_r, x_axis, math.rad(35), math.rad(160))")
    a("    Turn(shin_l, x_axis, math.rad(40), math.rad(160))")
    a("    Turn(shin_r, x_axis, 0, math.rad(160))")
    a("    Sleep(220)")
    a("  end")
    a("end")
    a("")
    a("local function StopWalk()")
    a("  Signal(SIG_WALK)")
    a("  Turn(leg_l, x_axis, 0, math.rad(120))")
    a("  Turn(leg_r, x_axis, 0, math.rad(120))")
    a("  Turn(shin_l, x_axis, 0, math.rad(120))")
    a("  Turn(shin_r, x_axis, 0, math.rad(120))")
    a("end")
    a("")
    a("function script.Create()")
    if P["turret_spin"]:
        a("  Spin(turret, y_axis, math.rad(120))")
    else:
        a("  -- nessuna animazione iniziale")
    a("end")
    a("")
    if P["walk"]:
        a("function script.StartMoving()")
        a("  StartThread(Walk)")
        a("end")
        a("")
        a("function script.StopMoving()")
        a("  StopWalk()")
        a("end")
        a("")
    a("function script.Killed(recentDamage, maxHealth)")
    a("  return 1")
    a("end")
    return "\n".join(L) + "\n"


lua_path = os.path.join(P["out_dir"], NAME + ".lua")
with open(lua_path, "w", encoding="utf-8") as f:
    f.write(lua_text())
print("DEPLOY lua generato:", lua_path)

# --- Consegna nel gioco: sovrascrive SOLO questi file, tutti dentro game_dir ------------------
if P["deploy"]:
    gd = P["game_dir"]
    if not os.path.isdir(gd):
        print("DEPLOY saltato: cartella del gioco non trovata:", gd)
    elif not (os.path.exists(s3o_path) and os.path.getsize(s3o_path) > 0):
        print("DEPLOY saltato: il .s3o non e' stato creato, non copio nulla")
    else:
        jobs = [
            (s3o_path, os.path.join(gd, P["dir_model"], NAME + ".s3o")),
            (os.path.join(P["out_dir"], NAME + "1.png"), os.path.join(gd, P["dir_textures"], NAME + "1.png")),
            (os.path.join(P["out_dir"], NAME + "2.png"), os.path.join(gd, P["dir_textures"], NAME + "2.png")),
            (lua_path, os.path.join(gd, P["dir_script"], NAME + ".lua")),
        ]
        for src, dst in jobs:
            try:
                existed = os.path.exists(dst)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(src, dst)
                print("DEPLOY", "sovrascritto" if existed else "creato", dst, os.path.getsize(dst), "byte")
            except Exception as e:
                print("DEPLOY errore su", dst, ":", e)

tris = sum(len(o.data.polygons) for o in objs.values())
blend = os.path.join(P["out_dir"], NAME + ".blend")
bpy.ops.wm.save_as_mainfile(filepath=blend)
print("BLENDER_VERSION", bpy.app.version_string)
print("PEZZI", len(objs), sorted(objs))
print("TRIANGOLI", tris)
print("SALVATO", blend)
