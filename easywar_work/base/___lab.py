# ___lab.py - generates the Easy War base lab as a fixed constructor tower: ___lab.s3o, ___lab1.png,
# ___lab2.png and ___lab.lua. Realizes canon C4, row ___lab (fixed constructor, proposal of 16 Nov 2026).
# Shapes are measured from the manager's drawing (side + top view, 1024 px sheet); depths come from the top view.
#
# Run in Blender:  flatpak run org.blender.Blender --background --python ___lab.py | grep -E "LAB|S3O_ROOT|DEPLOY|TRIANGOLI|VERTICI"
# Params as JSON after "--":  ... ___lab.py -- '{"deploy":true,"target_height":66}'
# Outside Blender (geometry check + preview PNG only):  python3 -I ___lab.py '{"target_height":66}'

import os
import sys
import json
import math
import re
import shutil
import struct
import zlib

import numpy as np

try:
    import bpy
except ImportError:
    bpy = None

NAME = "___lab"          # fixed on purpose: must equal units/**/___lab.lua (a name derived from the file broke a deploy once)

P = {
    "target_height": 66.0,   # engine units; 66 = base 16 wide if footprint 1x1 = 16 elmos [footprint unit: to verify]
    "yaw_deg": 180.0,        # rotation of the root piece about Z (see technical base)
    "flip_v": True,          # the engine shows textures flipped vs Blender: v = 1 - v_up
    "tex_size": 256,
    "deploy": True,          # paste model, textures and Lua into the game (backup of replaced files first)
    "backup": True,
    "preview": True,         # outside Blender: write the numpy preview sheet
    "game_dir": None,        # default: three levels above this script (<game>/easywar_work/base/)
}

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

# ---------------------------------------------------------------------------------------------
# Working system (same as the other scripts): X = robot left, Y = up, Z = front. Units = drawing pixels,
# then scaled once to target_height. Drawing: side view, front = image right, axis at x=265, sole at y=947.
# ---------------------------------------------------------------------------------------------
C8 = math.cos(math.pi / 8)

ZONES = {  # tex1 rectangles in pixels (x0, y0, x1, y1), rows from the top. P = team colour (alpha high)
    "T": (0, 0, 86, 128), "D": (86, 0, 171, 128), "P": (171, 0, 256, 128),
    "A": (0, 128, 86, 256), "E": (86, 128, 171, 256), "B": (171, 128, 256, 256),
}
ZONE_RGBA = {
    "T": (138, 150, 164, 0), "D": (34, 37, 44, 0), "P": (190, 190, 190, 255),
    "A": (230, 130, 30, 0), "E": (60, 140, 200, 0), "B": (150, 70, 160, 0),
}


def lathe(rings, n, phase=0.0, cap_bottom=False, cap_top=False, apothem=False):
    """Solid of revolution about Y. rings = [(radius, y), ...] bottom to top. Faces point outward.
    apothem=True: radius is the flat-to-centre distance (silhouette half width of a flat-facing polygon)."""
    verts, faces = [], []
    for r, y in rings:
        rr = r / math.cos(math.pi / n) if apothem else r
        for j in range(n):
            a = phase + 2 * math.pi * j / n
            verts.append((rr * math.cos(a), y, rr * math.sin(a)))
    for i in range(len(rings) - 1):
        for j in range(n):
            a, b = i * n + j, i * n + (j + 1) % n
            d, c = (i + 1) * n + j, (i + 1) * n + (j + 1) % n
            faces += [(a, d, c), (a, c, b)]
    if cap_bottom:
        faces += [(0, j, j + 1) for j in range(1, n - 1)]
    if cap_top:
        o = (len(rings) - 1) * n
        faces += [(o, o + j + 1, o + j) for j in range(1, n - 1)]
    return np.array(verts, float), faces


def along_z(shape, z0=0.0, y=0.0, x=0.0):
    """Turn a Y-axis solid so its axis runs along +Z, then move it (rotation (x,y,z)->(x,-z,y), proper)."""
    v, f = shape
    w = np.stack([v[:, 0], -v[:, 2], v[:, 1]], axis=1) + np.array([x, y, z0])
    return w, f


def moved(shape, dx, dy, dz):
    return shape[0] + np.array([dx, dy, dz]), shape[1]


def build_parts():
    """List of (piece, zone, verts, faces, ref). ref = a point inside the shape, used to check face direction."""
    parts = []

    def add(piece, zone, shape, ref=None):
        v = np.asarray(shape[0], float)
        parts.append((piece, zone, v, [tuple(f) for f in shape[1]], np.array(ref, float) if ref is not None else v.mean(axis=0)))

    # --- base: four floating drums (2x2), knobs on top, collar, cone, mast. y = 0 is the lowest point.
    for sx in (-55.0, 55.0):
        for sz in (-55.0, 55.0):
            add("base", "D", moved(lathe([(50, 0), (50, 139)], 12, 0.0, True, True), sx, 0, sz))
            add("base", "P", moved(lathe([(12, 139), (12, 152)], 8, math.pi / 8, False, True, True), sx, 0, sz))
    add("base", "D", lathe([(35, 139), (35, 162)], 8, math.pi / 8, False, False, True))
    add("base", "T", lathe([(35, 162), (15.5, 244)], 8, math.pi / 8, False, False, True))
    add("base", "T", lathe([(15.5, 244), (15.5, 754)], 8, math.pi / 8, False, False, True))

    # --- head: octagonal solid of revolution, flats facing front/back/left/right (drawing: octagon in both views)
    add("head", "T", lathe([(24.5, 755), (58, 789), (58, 838), (24.5, 871)], 8, math.pi / 8, True, True, True))

    # --- nozzle (pivot inside the head at z=50): straight tube, flared mouth (team colour), dark mouth disc
    add("nozzle", "T", along_z(lathe([(12, 0), (12, 50)], 8, math.pi / 8, False, False, True), 50, 813))
    add("nozzle", "P", along_z(lathe([(13.5, 0), (20.5, 28)], 8, math.pi / 8, False, False, True), 100, 813))
    disc = lathe([(20.5, 0), (20.5, 0)], 8, math.pi / 8, False, True, True)   # flat 8-gon, normal +Y before the turn
    add("nozzle", "D", along_z((disc[0][8:], [(0, j + 1, j) for j in range(1, 7)]), 128, 813), ref=(0, 813, 100))

    # --- nano: hidden marker triangle at the mouth, the point the build beam leaves from
    add("nano", "D", (np.array([(-2.0, 813, 127), (2.0, 813, 127), (0.0, 813, 129)]), [(0, 2, 1)]), ref=(0, 813, 100))
    return parts


JOINTS = {  # piece -> (parent, joint in working coordinates before scaling). Names are used by the Lua piece().
    "base": (None, (0.0, 0.0, 0.0)),
    "head": ("base", (0.0, 813.0, 0.0)),
    "nozzle": ("head", (0.0, 813.0, 50.0)),
    "nano": ("nozzle", (0.0, 813.0, 127.0)),
}
ORDER = ["base", "head", "nozzle", "nano"]


def fix_orientation(parts):
    """Flip faces whose normal points to the inside of the part (normal vs. face centre minus ref). Returns count."""
    flipped = 0
    for idx, (piece, zone, v, faces, ref) in enumerate(parts):
        nf = []
        for f in faces:
            a, b, c = v[f[0]], v[f[1]], v[f[2]]
            nrm = np.cross(b - a, c - a)
            if np.dot(nrm, (a + b + c) / 3.0 - ref) < 0:
                f = (f[0], f[2], f[1])
                flipped += 1
            nf.append(f)
        parts[idx] = (piece, zone, v, nf, ref)
    return flipped


def assemble(parts, target_height):
    """Scale once to target_height (k = h / (max y - min y)), make vertices relative to the piece joint."""
    allv = np.concatenate([p[2] for p in parts])
    k = target_height / (allv[:, 1].max() - allv[:, 1].min())
    pieces = {n: {"verts": [], "faces": [], "zones": []} for n in ORDER}
    for piece, zone, v, faces, _ in parts:
        d = pieces[piece]
        joint = np.array(JOINTS[piece][1]) * k
        base = len(d["verts"])
        d["verts"].extend((v * k - joint).tolist())
        d["faces"].extend([(base + f[0], base + f[1], base + f[2]) for f in faces])
        d["zones"].extend([zone] * len(faces))
    for d in pieces.values():
        d["verts"] = np.array(d["verts"], float)
    return pieces, k


def face_uvs(zone, tri, size, flip_v):
    """Planar projection of one triangle inside its tex1 zone (flat colours: kept in the middle 70 %)."""
    x0, y0, x1, y1 = ZONES[zone]
    a, b, c = tri
    nrm = np.cross(b - a, c - a)
    ln = np.linalg.norm(nrm)
    nrm = nrm / ln if ln > 1e-12 else np.array([0.0, 1.0, 0.0])
    t1 = np.cross(nrm, [0.0, 1.0, 0.0])
    if np.linalg.norm(t1) < 1e-6:
        t1 = np.cross(nrm, [1.0, 0.0, 0.0])
    t1 /= np.linalg.norm(t1)
    t2 = np.cross(nrm, t1)
    pts = [(np.dot(p - a, t1), np.dot(p - a, t2)) for p in tri]
    ext = max(max(abs(s), abs(t)) for s, t in pts) or 1.0
    cx, cy, hw, hh = (x0 + x1) / 2.0, (y0 + y1) / 2.0, (x1 - x0) * 0.35, (y1 - y0) * 0.35
    out = []
    for s, t in pts:
        px, py = cx + s / ext * hw, cy + t / ext * hh          # py = row from the top
        v_up = 1.0 - py / size
        out.append((px / size, (1.0 - v_up) if flip_v else v_up))
    return out


def write_png_rgba(path, arr):  # arr: uint8 (h, w, 4); written by hand because Blender zeroes RGB where alpha is 0
    h, w = arr.shape[:2]
    raw = np.zeros((h, w * 4 + 1), np.uint8)
    raw[:, 1:] = arr.reshape(h, w * 4)

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    data = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw.tobytes(), 6)) + chunk(b"IEND", b""))
    with open(path, "wb") as fh:
        fh.write(data)


def make_tex1(size):
    img = np.zeros((size, size, 4), np.uint8)
    for z, (x0, y0, x1, y1) in ZONES.items():
        img[y0:y1, x0:x1] = ZONE_RGBA[z]
    return img


def make_tex2(size):
    img = np.zeros((size, size, 4), np.uint8)
    img[:, :] = (0, 128, 0, 255)       # R = glow, G = reflection are hypotheses; this start value is accepted by the engine
    return img


LUA = """-- @NAME@: fixed constructor tower (Easy War base lab). Generated by @NAME@.py: do not edit by hand.
local base, head, nozzle, nano = piece('base', 'head', 'nozzle', 'nano')

local FWD = -1                                  -- x-axis sign that moves a piece forward (seen in game on other units)
local YAW_SPEED, PITCH_SPEED, REST_SPEED = math.rad(180), math.rad(120), math.rad(60)

function script.Create()
  Spring.Echo('[easywar] @NAME@ Create unitID=' .. tostring(unitID))
end

function script.StartBuilding(heading, pitch)
  SetUnitValue(COB.INBUILDSTANCE, 1)
  Turn(head, y_axis, heading, YAW_SPEED)
  Turn(nozzle, x_axis, FWD * pitch, PITCH_SPEED)
end

function script.StopBuilding()
  SetUnitValue(COB.INBUILDSTANCE, 0)
  Turn(head, y_axis, 0, REST_SPEED)
  Turn(nozzle, x_axis, 0, REST_SPEED)
end

function script.QueryNanopiece() return nano end
script.QueryNanoPiece = script.QueryNanopiece    -- alias; only the lower-case p spelling is known to work (seen)

function script.Killed(recentDamage, maxHealth) return 1 end
"""


# ---------------------------------------------------------------------------------------------
# S3O re-read (layout from memory of the S3O spec: to verify. A mismatch is reported, not hidden).
# ---------------------------------------------------------------------------------------------
def read_s3o(path):
    data = open(path, "rb").read()
    root = struct.unpack_from("<I", data, 12 + 4 + 20)[0]
    tex1, tex2 = struct.unpack_from("<II", data, 12 + 4 + 20 + 8)
    out = {"pieces": 0, "tris": 0, "verts": 0, "names": [],
           "tex": [data[o:data.index(b"\0", o)].decode() for o in (tex1, tex2)]}

    def walk(off):
        (name, nch, chofs, nv, vofs, vtype, ptype, vts, vtofs, coll) = struct.unpack_from("<10I", data, off)
        out["pieces"] += 1
        out["verts"] += nv
        out["names"].append(data[name:data.index(b"\0", name)].decode())
        out["tris"] += {0: vts // 3, 1: max(vts - 2, 0), 2: (vts // 4) * 2}.get(ptype, 0)
        for i in range(nch):
            walk(struct.unpack_from("<I", data, chofs + 4 * i)[0])
    walk(root)
    return out


# ---------------------------------------------------------------------------------------------
# Deploy
# ---------------------------------------------------------------------------------------------
def find_unit(game_dir):
    """Find units/**/<NAME>.lua and read ObjectName and script from it (never modified)."""
    for root, _, files in os.walk(os.path.join(game_dir, "units")):
        if NAME + ".lua" in files:
            path = os.path.join(root, NAME + ".lua")
            text = open(path, encoding="utf-8", errors="replace").read()
            m1 = re.search(r"objectname\s*=\s*[\"']([^\"']+)[\"']", text, re.I)
            m2 = re.search(r"\bscript\s*=\s*[\"']([^\"']+)[\"']", text, re.I)
            return path, (m1.group(1) if m1 else None), (m2.group(1) if m2 else None)
    return None


def deploy(p, game_dir, files):
    found = find_unit(game_dir)
    print("LAB definizione:", found)
    if not p["deploy"]:
        print("DEPLOY saltato: deploy=false (genera solo in out/)")
        return
    obj_name, script = (found[1], found[2]) if found else (None, None)
    if not found:
        print("DEPLOY avviso: definizione %s.lua non trovata sotto units/: uso i percorsi del canone; "
              "la scheda deve avere ObjectName = \"base/%s.s3o\" e script = \"base/%s.lua\"" % (NAME, NAME, NAME))
    if not obj_name:
        obj_name = "base/%s.s3o" % NAME
        if found:
            print("DEPLOY avviso: la definizione non ha ObjectName, uso", obj_name)
    if not script:
        script = "base/%s.lua" % NAME
        if found:
            print("DEPLOY avviso: la definizione non ha il campo script; aggiungere script = \"%s\"" % script)
    targets = [
        (files["s3o"], os.path.join(game_dir, "objects3d", obj_name)),
        (files["tex1"], os.path.join(game_dir, "unittextures", NAME + "1.png")),
        (files["tex2"], os.path.join(game_dir, "unittextures", NAME + "2.png")),
        (files["lua"], os.path.join(game_dir, "scripts", script)),
    ]
    bdir = os.path.join(game_dir, "easywar_work", "backup", NAME + "_data")
    for src, dst in targets:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        note = "creato"
        if os.path.exists(dst):
            note = "sostituito"
            if p["backup"]:
                os.makedirs(bdir, exist_ok=True)
                bak = os.path.join(bdir, os.path.basename(dst))
                n = 1
                while os.path.exists(bak):
                    bak = os.path.join(bdir, "%s.%d" % (os.path.basename(dst), n))
                    n += 1
                shutil.copy2(dst, bak)
                note += ", copia in " + bak
        shutil.copy2(src, dst)
        print("DEPLOY", dst, "(%s)" % note)


# ---------------------------------------------------------------------------------------------
# Preview without Blender: numpy z-buffer, three views plus the 60 px silhouette (canon ART-09)
# ---------------------------------------------------------------------------------------------
def render(parts, view, size, silhouette=False):
    tris, cols = [], []
    for piece, zone, v, faces, _ in parts:
        for f in faces:
            tris.append(v[list(f)])
            cols.append(ZONE_RGBA[zone][:3])
    tris = np.array(tris)
    if view == "front":
        sx, sy, dp = tris[..., 0], tris[..., 1], tris[..., 2]
    elif view == "side":      # viewer on -X, front (nozzle) to the right
        sx, sy, dp = tris[..., 2], tris[..., 1], -tris[..., 0]
    else:                     # top, front to the right, robot left up
        sx, sy, dp = tris[..., 2], tris[..., 0], tris[..., 1]
    sc = (size - 6) / 900.0
    px, py = size / 2.0 + sx * sc, size / 2.0 - (sy - 435.0) * sc if view != "top" else size / 2.0 - sy * sc
    img = np.full((size, size, 3), 255, np.uint8)
    zb = np.full((size, size), -1e18)
    light = np.array([0.4, 0.8, 0.45])
    light /= np.linalg.norm(light)
    for t in range(len(tris)):
        x, y, d = px[t], py[t], dp[t]
        den = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
        if abs(den) < 1e-9:
            continue
        x0, x1 = max(int(math.floor(x.min())), 0), min(int(math.ceil(x.max())), size - 1)
        y0, y1 = max(int(math.floor(y.min())), 0), min(int(math.ceil(y.max())), size - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        w0 = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / den
        w1 = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / den
        w2 = 1 - w0 - w1
        m = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        z = w0 * d[0] + w1 * d[1] + w2 * d[2]
        sub = zb[y0:y1 + 1, x0:x1 + 1]
        upd = m & (z > sub)
        nrm = np.cross(tris[t][1] - tris[t][0], tris[t][2] - tris[t][0])
        ln = np.linalg.norm(nrm)
        shade = 0.45 + 0.55 * max(0.0, float(np.dot(nrm / ln, light))) if ln > 1e-12 else 0.7
        col = (0, 0, 0) if silhouette else tuple(int(c * shade) for c in cols[t])
        sub[upd] = z[upd]
        img[y0:y1 + 1, x0:x1 + 1][upd] = col
    return img


def preview(parts, path):
    cells = [render(parts, v, 360) for v in ("front", "side", "top")]
    small = render(parts, "side", 60, silhouette=True)
    cell4 = np.full((360, 360, 3), 255, np.uint8)
    cell4[150:210, 150:210] = small
    sheet = np.concatenate(cells + [cell4], axis=1)
    alpha = np.full(sheet.shape[:2] + (1,), 255, np.uint8)
    write_png_rgba(path, np.concatenate([sheet, alpha], axis=2))


# ---------------------------------------------------------------------------------------------
# Blender part
# ---------------------------------------------------------------------------------------------
def s3o_op(kind):
    for mod in dir(bpy.ops):
        if "s3o" in mod.lower():
            m = getattr(bpy.ops, mod)
            for nm in dir(m):
                if kind in nm.lower():
                    return getattr(m, nm), mod + "." + nm
    raise RuntimeError("operatore S3O '%s' non trovato" % kind)


def to_blender(v):
    return (v[0], -v[2], v[1])


def run_blender(p, pieces, k, files):
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    objs = {}
    for name in ORDER:
        d = pieces[name]
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata([to_blender(v) for v in d["verts"].tolist()], [], [list(f) for f in d["faces"]])
        mesh.update()
        uv = mesh.uv_layers.new(name="UVMap")
        for pi, f in enumerate(d["faces"]):
            tri = [d["verts"][i] for i in f]
            for c, (u, v) in enumerate(face_uvs(d["zones"][pi], tri, p["tex_size"], p["flip_v"])):
                uv.data[3 * pi + c].uv = (u, v)
        for poly in mesh.polygons:
            poly.use_smooth = False
        ob = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(ob)
        objs[name] = ob
    for name in ORDER:                     # parents first, then positions relative to the parent
        parent = JOINTS[name][0]
        if parent:
            objs[name].parent = objs[parent]
            rel = (np.array(JOINTS[name][1]) - np.array(JOINTS[parent][1])) * k
            objs[name].location = to_blender(rel)
    objs["base"].rotation_euler = (0.0, 0.0, math.radians(p["yaw_deg"]))
    bpy.context.view_layer.update()

    add_root, add_name = s3o_op("root")
    for o in list(bpy.context.selected_objects):
        o.select_set(False)
    res = add_root("EXEC_DEFAULT", name=NAME, texture_name_1=NAME + "1.png", texture_name_2=NAME + "2.png")
    print("S3O_ROOT add", add_name, res)
    bpy.context.view_layer.update()
    root = bpy.data.objects.get(NAME)
    if root is None:
        cand = [o for o in bpy.data.objects if o.parent is None and o.name not in ORDER]
        root = cand[0] if cand else None
    if root is None:
        raise RuntimeError("radice S3O non trovata dopo add_s3o_root")
    objs["base"].parent = root
    objs["base"].matrix_parent_inverse = root.matrix_world.inverted()

    for o in list(bpy.context.selected_objects):
        o.select_set(False)
    bpy.context.view_layer.objects.active = root
    root.select_set(True)
    export, exp_name = s3o_op("export")
    res = export("EXEC_DEFAULT", filepath=files["s3o"])
    print("S3O_ROOT export", exp_name, res, os.path.getsize(files["s3o"]) if os.path.exists(files["s3o"]) else "file assente")
    print("LAB triangoli Blender:", sum(len(o.data.polygons) for n, o in objs.items()),
          "vertici Blender:", sum(len(o.data.vertices) for n, o in objs.items()))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, NAME + ".blend"))


def parse_params():
    if "--" in sys.argv:
        args = sys.argv[sys.argv.index("--") + 1:]
    elif bpy is None:
        args = sys.argv[1:]
    else:
        args = []            # inside Blender without "--": argv holds Blender options, not ours
    if args:
        try:
            P.update(json.loads(" ".join(args)))
        except ValueError as e:
            print("LAB parametri non validi, uso i predefiniti:", e)
    return P


def main():
    p = parse_params()
    os.makedirs(OUT, exist_ok=True)
    parts = build_parts()
    flipped = fix_orientation(parts)
    pieces, k = assemble(parts, p["target_height"])
    ntri = sum(len(d["faces"]) for d in pieces.values())
    allv = np.concatenate([d["verts"] + np.array(JOINTS[n][1]) * k for n, d in pieces.items()])
    ext = allv.max(axis=0) - allv.min(axis=0)
    print("LAB scala k=%.5f, altezza %.2f, pezzi %d, facce rovesciate corrette: %d" % (k, ext[1], len(pieces), flipped))
    print("LAB ingombro X %.2f  Y %.2f  Z %.2f; ugello sporge %.2f oltre l'asse" % (ext[0], ext[1], ext[2], allv[:, 2].max()))
    print("LAB hitbox proposta (non verificata): collisionVolumeScales = \"%.1f %.1f %.1f\"" % (ext[0], ext[1], ext[2]))
    print("LAB stima vertici nel .s3o (3 per triangolo): %d" % (3 * ntri))
    print("TRIANGOLI", ntri)

    files = {"s3o": os.path.join(OUT, NAME + ".s3o"), "tex1": os.path.join(OUT, NAME + "1.png"),
             "tex2": os.path.join(OUT, NAME + "2.png"), "lua": os.path.join(OUT, NAME + ".lua")}
    write_png_rgba(files["tex1"], make_tex1(p["tex_size"]))
    write_png_rgba(files["tex2"], make_tex2(p["tex_size"]))
    with open(files["lua"], "w", encoding="utf-8") as fh:
        fh.write(LUA.replace("@NAME@", NAME))
    game_dir = p["game_dir"] or os.path.dirname(os.path.dirname(HERE))

    if bpy is None:
        if p["preview"]:
            preview(parts, os.path.join(OUT, NAME + "_preview.png"))
            print("LAB anteprima scritta in", os.path.join(OUT, NAME + "_preview.png"))
        print("LAB fuori da Blender: modello .s3o non generato")
        return
    run_blender(p, pieces, k, files)
    back = read_s3o(files["s3o"])
    ok = back["pieces"] == len(ORDER) and back["tris"] == ntri
    print("LAB .s3o riletto: pezzi %d, triangoli %d, texture %s -> %s" % (back["pieces"], back["tris"], back["tex"], "torna" if ok else "NON torna"))
    print("VERTICI nel .s3o:", back["verts"])
    deploy(p, game_dir, files)


if __name__ == "__main__":
    main()
