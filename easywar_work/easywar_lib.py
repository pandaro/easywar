# Easy War - libreria condivisa per generare unita' in Blender (Python).
# Va in easywar_work/easywar_lib.py. Non si lancia da sola: la usano gli script delle unita'
# (per esempio easywar_work/base/constructor.py). Solo ASCII.
import bpy, bmesh, json, math, os, random, shutil, struct, sys, zlib
from mathutils import Vector, Matrix

# Rettangoli UV (u0, v0, u1, v1) per zona materiale, nell'atlante di tex1.
ZONES = {
    "armor":  (0.0, 0.5, 0.5, 1.0),
    "dark":   (0.5, 0.5, 1.0, 1.0),
    "team":   (0.0, 0.0, 0.5, 0.5),   # zona colore giocatore (alpha alta nel motore = colore giocatore)
    "accent": (0.5, 0.0, 1.0, 0.5),
}
COLORS = {
    "armor": (0.55, 0.57, 0.60), "dark": (0.18, 0.19, 0.21),
    "team": (0.80, 0.80, 0.80), "accent": (0.90, 0.60, 0.10),
}

DEFAULTS = {
    "seed": 1,
    "out_dir": None,          # None = cartella "out" accanto allo script dell'unita'
    "bevel": 0.06,            # 0 = niente smusso (meno triangoli)
    "cyl_segments": 10,
    "tex_size": 256,
    "scale": 10.0,            # moltiplicatore globale del modello
    "yaw_deg": 180.0,         # rotazione del fronte (0 = fronte verso -Y in Blender)
    "flip_v": True,           # il motore mostra le texture capovolte rispetto a Blender
    # Consegna automatica nel gioco (tutto dentro game_dir). Con "deploy": false genera solo in out_dir.
    "deploy": True,
    "game_dir": os.path.expanduser("~/.spring/games/easywar.sdd"),
    "dir_model": "objects3d/base",       # NOME.s3o
    "dir_textures": "unittextures",      # NOME1.png e NOME2.png
    "dir_script": "scripts/base",        # NOME.lua
}


def write_png(path, n, px):
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


def zone_of(u, v):
    if u < 0.5:
        return "armor" if v >= 0.5 else "team"
    return "dark" if v >= 0.5 else "accent"


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


def box(size, off):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]; v.co.y *= size[1]; v.co.z *= size[2]
    return bm, off, min(size)


def cyl(radius, depth, axis, off, segments=10):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                          radius1=radius, radius2=radius, depth=depth)
    if axis == "y":
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0),
                         matrix=Matrix.Rotation(math.radians(90), 3, "X"))
    elif axis == "x":
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0),
                         matrix=Matrix.Rotation(math.radians(90), 3, "Y"))
    return bm, off, None


class Builder:
    def __init__(self, script_path, **defaults):
        self.P = dict(DEFAULTS)
        self.P.update(defaults)
        self.script_path = os.path.abspath(script_path)
        self.name = os.path.splitext(os.path.basename(self.script_path))[0]
        argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
        for a in argv:
            # Un argomento che inizia con "{" e' JSON di parametri; qualunque altro e' un nome unita' alternativo.
            if a.strip().startswith("{"):
                self.P.update(json.loads(a))
            else:
                self.name = a.strip()
        self.out_dir = self.P["out_dir"] or os.path.join(os.path.dirname(self.script_path), "out")
        os.makedirs(self.out_dir, exist_ok=True)
        print("START", self.name, flush=True)
        for ob in list(bpy.data.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        self.rng = random.Random(self.P["seed"])
        self.objs = {}
        self.coll = bpy.context.scene.collection
        self._make_material()

    # --- texture e materiale -----------------------------------------------------------------
    def _make_material(self):
        n = self.P["tex_size"]
        p1, p2 = [], []
        for y in range(n):
            for x in range(n):
                z = zone_of(x / n, y / n)
                c = COLORS[z]
                k = self.rng.uniform(-0.03, 0.03)
                # tex1: RGB colore, alpha = maschera colore giocatore (alpha alta -> colore giocatore nel motore)
                p1 += [c[0] + k, c[1] + k, c[2] + k, 1.0 if z == "team" else 0.0]
                # tex2: ASSUNZIONE da verificare: R = luminosita' propria, G = riflessione
                p2 += [0.6 if z == "accent" else 0.0, 0.3, 0.0, 1.0]
        self.tex_names = (self.name + "1.png", self.name + "2.png")
        self.tex_paths = [os.path.join(self.out_dir, t) for t in self.tex_names]
        write_png(self.tex_paths[0], n, p1)
        write_png(self.tex_paths[1], n, p2)
        i1 = bpy.data.images.load(self.tex_paths[0])
        i2 = bpy.data.images.load(self.tex_paths[1])
        i1.alpha_mode = "CHANNEL_PACKED"
        i2.alpha_mode = "CHANNEL_PACKED"
        i2.colorspace_settings.name = "Non-Color"
        mat = bpy.data.materials.new("mat_" + self.name)
        mat.use_nodes = True
        nt = mat.node_tree
        # I nomi dei nodi sono tradotti con Blender in italiano: si cerca per tipo, non per nome.
        bsdf = next((nd for nd in nt.nodes if nd.type == "BSDF_PRINCIPLED"), None)
        assert bsdf is not None, "Nodo Principled non trovato"
        t1 = nt.nodes.new("ShaderNodeTexImage"); t1.image = i1
        t2 = nt.nodes.new("ShaderNodeTexImage"); t2.image = i2
        t1.location = (-400, 200); t2.location = (-400, -100)
        nt.links.new(t1.outputs["Color"], bsdf.inputs["Base Color"])
        print("COLLEGAMENTI", len(nt.links), "(attesi 2)")
        self.mat = mat

    # --- pezzi ---------------------------------------------------------------------------------
    def box(self, size, off):
        return box(size, off)

    def cyl(self, radius, depth, axis, off):
        return cyl(radius, depth, axis, off, self.P["cyl_segments"])

    def _finish(self, bm, off, minsize, zone):
        P = self.P
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
                l[uvl].uv = (uu, 1.0 - vv if P["flip_v"] else vv)
        return bm

    def add(self, name, parent, loc, made, zone):
        assert name not in self.objs, "nome duplicato: " + name
        bm = self._finish(*made, zone)
        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()
        mesh.materials.append(self.mat)
        ob = bpy.data.objects.new(name, mesh)
        self.coll.objects.link(ob)
        ob.parent = self.objs.get(parent)
        ob.location = loc
        self.objs[name] = ob

    # --- chiusura: scala, radice S3O, export, consegna ------------------------------------------
    def finalize(self, lua_text):
        P, NAME = self.P, self.name
        tops = [o for o in self.objs.values() if o.parent is None]
        assert len(tops) == 1, "serve un solo pezzo radice, trovati: " + str([o.name for o in tops])
        piece_root = tops[0]

        S = P["scale"]
        for ob in self.objs.values():
            ob.location = ob.location * S
            ob.data.transform(Matrix.Scale(S, 4))
        piece_root.rotation_euler = (0.0, 0.0, math.radians(P["yaw_deg"]))

        root_obj = None
        op, op_id, rna = find_s3o_root_operator()
        if op is None:
            print("S3O_ROOT: operatore 'Add S3O Root' non trovato -> aggiungere la radice a mano")
        else:
            props = [p.identifier for p in rna.properties if p.identifier != "rna_type"]
            want = {}
            for ident in props:
                k = ident.lower()
                if k == "name":
                    want[ident] = NAME
                elif k == "texture_name_1":
                    want[ident] = self.tex_names[0]
                elif k == "texture_name_2":
                    want[ident] = self.tex_names[1]
            before = set(bpy.data.objects.keys())
            try:
                print("S3O_ROOT impostato:", want, "->", op("EXEC_DEFAULT", **want))
            except Exception as e:
                print("S3O_ROOT errore:", e)
            new = [bpy.data.objects[n] for n in bpy.data.objects.keys() if n not in before]
            tops_new = [o for o in new if o.parent is None and o.type == "EMPTY"]
            if tops_new:
                root_obj = tops_new[0]
                bpy.context.view_layer.update()
                piece_root.parent = root_obj
                # Compensa la rotazione del root: il modello resta dritto come costruito (Z su).
                piece_root.matrix_parent_inverse = root_obj.matrix_world.inverted()
                print("S3O_ROOT radice:", root_obj.name, "| pezzo radice:", piece_root.name)

        active = root_obj or piece_root
        bpy.context.view_layer.objects.active = active
        for o in bpy.data.objects:
            o.select_set(o is active)

        # Export .s3o con l'operatore di S3O Kit
        s3o_path = os.path.join(self.out_dir, NAME + ".s3o")
        try:
            res = bpy.ops.s3o_tools.export_s3o("EXEC_DEFAULT", filepath=s3o_path)
            size = os.path.getsize(s3o_path) if os.path.exists(s3o_path) else "NON CREATO"
            print("S3O_ROOT export:", res, s3o_path, size)
        except Exception as e:
            print("S3O_ROOT export errore:", e)

        # Nome del file Lua: di solito NOME.lua, ma deve coincidere col campo "script" della definizione dell'unita'.
        lua_file = P.get("lua_name") or (NAME + ".lua")
        lua_path = os.path.join(self.out_dir, lua_file)
        with open(lua_path, "w", encoding="utf-8") as f:
            f.write(lua_text)
        print("DEPLOY lua generato:", lua_path)

        if P["deploy"]:
            gd = P["game_dir"]
            if not os.path.isdir(gd):
                print("DEPLOY saltato: cartella del gioco non trovata:", gd)
            elif not (os.path.exists(s3o_path) and os.path.getsize(s3o_path) > 0):
                print("DEPLOY saltato: il .s3o non e' stato creato, non copio nulla")
            else:
                jobs = [
                    (s3o_path, os.path.join(gd, P["dir_model"], NAME + ".s3o")),
                    (self.tex_paths[0], os.path.join(gd, P["dir_textures"], self.tex_names[0])),
                    (self.tex_paths[1], os.path.join(gd, P["dir_textures"], self.tex_names[1])),
                    (lua_path, os.path.join(gd, P["dir_script"], lua_file)),
                ]
                for src, dst in jobs:
                    try:
                        existed = os.path.exists(dst)
                        os.makedirs(os.path.dirname(dst), exist_ok=True)
                        shutil.copyfile(src, dst)
                        print("DEPLOY", "sovrascritto" if existed else "creato", dst, os.path.getsize(dst), "byte")
                    except Exception as e:
                        print("DEPLOY errore su", dst, ":", e)

        tris = sum(len(o.data.polygons) for o in self.objs.values())
        blend = os.path.join(self.out_dir, NAME + ".blend")
        bpy.ops.wm.save_as_mainfile(filepath=blend)
        print("BLENDER_VERSION", bpy.app.version_string)
        print("PEZZI", len(self.objs), sorted(self.objs))
        print("TRIANGOLI", tris)
        print("SALVATO", blend)
