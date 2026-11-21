# ssscom.py - converts the Tripo FBX of the Sigma Commander into ssscom.s3o, ssscom1.png and ssscom2.png.
# Realizes CMD-05..CMD-08 for Sigma. Model and textures only: no animation script and no unit def are written
# (the animation agent and the unit def agent do those). Piece names and hierarchy are the same as ssscom, so
# the Commander walk/build Lua can be reused: base, torso, head, arm_l (build forearm), arm_r (fist).
# Method of the guide "Da modello Tripo a unita Recoil": FBX read in pure Python, Tripo UVs and texture kept,
# no triangle reduction. This mesh is ONE connected shell (arms and legs are welded to the body), so every
# triangle is assigned to the nearest bone in the front view (distance to the bone segment minus its radius).
#
# Place: easywar_work/ssscom.py (commanders sit at the root). Next to it: ssscom.fbx (or baymax.fbx as exported by
# Tripo) plus its texture: ssscom1.png / ssscom2.png (preferred), or the *_basecolor.jpg named inside the FBX
# (baymax.fbm/baymax_basecolor.jpg, relative to the FBX), or the file given with the "texture" param.
#
# Run in Blender:  flatpak run org.blender.Blender --background --python ssscom.py | grep -E "SSS|S3O_ROOT|DEPLOY|TRIANGOLI|VERTICI"
# Params as JSON after "--":  ... ssscom.py -- '{"target_height":44,"deploy":false}'
# Outside Blender (checks + preview only):  python3 -I ssscom.py '{"preview":true}'

import os
import sys
import glob
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

NAME = "ssscom"          # fixed on purpose: every produced file carries this name

P = {
    "target_height": 44.0,   # engine units (vademecum: commander fallback height 44)
    "yaw_deg": 180.0,        # rotation of the root piece about Z (see technical base)
    "flip_v": True,          # the engine shows textures flipped vs Blender: v = 1 - v_up
    "smooth": True,          # smooth normals (the Tripo mesh is round); False = flat faces like the other scripts
    "tex_size": 1024,        # tex1 side; the 2048 Tripo texture is averaged 2x2
    "deploy": True,          # paste model and textures into the game (backup of replaced files first); no Lua, no unit def
    "backup": True,
    "subdir": "",            # commanders live at level 0: objects3d/ssscom.s3o, unittextures/ssscom1.png
    "team_mask": "zones",    # "zones" (CMD-08 by geometry), "red" (saturated red of the texture) or "both"
    "preview": True,         # outside Blender: write the preview sheet
    "fbx": None,             # default: ssscom.fbx next to the script, else baymax.fbx (Tripo name)
    "texture": None,         # optional explicit path of the Tripo *_basecolor.jpg
    "game_dir": None,        # default: the first folder above this script that contains units/
}

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
SHARED = ("commander.s3o", "commanderscript.lua")   # files shared by all commander defs: never overwritten

# ---------------------------------------------------------------------------------------------
# Binary FBX 7.x reader (seen working on Tripo exports, version 7400)
# ---------------------------------------------------------------------------------------------
class Node:
    def __init__(self, name, props, children):
        self.name, self.props, self.children = name, props, children

    def find(self, name):
        return [c for c in self.children if c.name == name]

    def first(self, name):
        r = self.find(name)
        return r[0] if r else None


ARR = {b"f": "<f4", b"d": "<f8", b"i": "<i4", b"l": "<i8", b"b": "<i1"}


def _prop(data, o):
    t = data[o:o + 1]
    o += 1
    simple = {b"Y": ("<h", 2), b"I": ("<i", 4), b"F": ("<f", 4), b"D": ("<d", 8), b"L": ("<q", 8)}
    if t in simple:
        fmt, n = simple[t]
        return struct.unpack_from(fmt, data, o)[0], o + n
    if t == b"C":
        return data[o] != 0, o + 1
    if t in ARR:
        n, enc, clen = struct.unpack_from("<III", data, o)
        raw = data[o + 12:o + 12 + clen]
        if enc == 1:
            raw = zlib.decompress(raw)
        return np.frombuffer(raw, dtype=np.dtype(ARR[t])).copy()[:n], o + 12 + clen
    if t in (b"S", b"R"):
        n = struct.unpack_from("<I", data, o)[0]
        v = data[o + 4:o + 4 + n]
        return (v.decode("utf-8", "replace") if t == b"S" else v), o + 4 + n
    raise ValueError("FBX: tipo di proprieta sconosciuto %r" % t)


def read_fbx(path):
    data = open(path, "rb").read()
    if data[:18] != b"Kaydara FBX Binary":
        raise ValueError("non e un FBX binario: " + path)
    ver = struct.unpack_from("<I", data, 23)[0]
    wide = ver >= 7500
    hdr = 25 if wide else 13

    def node(o):
        end, nprop, _ = struct.unpack_from("<QQQ" if wide else "<III", data, o)
        nlen = data[o + hdr - 1]
        if end == 0:
            return None, o + hdr
        name = data[o + hdr:o + hdr + nlen].decode()
        p = o + hdr + nlen
        props = []
        for _ in range(nprop):
            v, p = _prop(data, p)
            props.append(v)
        kids = []
        while p < end:
            k, p = node(p)
            if k is None:
                break
            kids.append(k)
        return Node(name, props, kids), end

    top, o = [], 27
    while o < len(data) - hdr:
        n, o = node(o)
        if n is None:
            break
        top.append(n)
    return ver, Node("root", [], top)


def fbx_mesh(root):
    """All geometries merged: verts (N,3), tris (M,3), tri_uv (M,3,2) with v measured from the bottom."""
    V, T, UV = [], [], []
    base = 0
    for g in root.first("Objects").find("Geometry"):
        v = g.first("Vertices").props[0].reshape(-1, 3).astype(float)
        pvi = g.first("PolygonVertexIndex").props[0].astype(np.int64)
        uvl = g.first("LayerElementUV")
        uv = uvl.first("UV").props[0].reshape(-1, 2).astype(float)
        mapping = uvl.first("MappingInformationType").props[0]
        direct = uvl.first("ReferenceInformationType").props[0] == "IndexToDirect"
        uvi = uvl.first("UVIndex").props[0].astype(np.int64) if direct else None
        poly, corners = [], []
        for ci, idx in enumerate(pvi):
            last = idx < 0
            poly.append(~idx if last else idx)
            corners.append(ci)
            if last:
                for k in range(1, len(poly) - 1):
                    tri = (poly[0], poly[k], poly[k + 1])
                    if mapping == "ByPolygonVertex":
                        cs = (corners[0], corners[k], corners[k + 1])
                    else:
                        cs = tri
                    ix = [uvi[c] for c in cs] if direct else list(cs)
                    T.append(tuple(i + base for i in tri))
                    UV.append(uv[ix])
                poly, corners = [], []
        V.append(v)
        base += len(v)
    return np.concatenate(V), np.array(T, np.int64), np.array(UV, float)


def texture_path(fbx_path, root, p):
    """The "texture" param, else the texture named in the FBX (relative to the FBX), else a *basecolor* image next to the script."""
    if p.get("texture"):
        return p["texture"] if os.path.isabs(p["texture"]) else os.path.join(HERE, p["texture"])
    for t in root.first("Objects").find("Texture") + root.first("Objects").find("Video"):
        for k in t.children:
            if k.name in ("RelativeFilename", "FileName") and k.props and isinstance(k.props[0], str):
                cand = os.path.join(os.path.dirname(fbx_path), k.props[0].replace("\\", "/"))
                if os.path.exists(cand):
                    return cand
    stem = os.path.splitext(os.path.basename(fbx_path))[0]   # shared folder: only this unit's texture
    found = sorted(glob.glob(os.path.join(HERE, NAME + "*basecolor*")) + glob.glob(os.path.join(HERE, stem + "*basecolor*"))
                   + glob.glob(os.path.join(HERE, stem + ".fbm", "*basecolor*")))
    return found[0] if found else None


# ---------------------------------------------------------------------------------------------
# Pieces. Working system = FBX system (seen in the preview): Y up, Z front, X robot left (viewer right).
# Model height 1, sole at y = 0, centre line at x = CX. Joints measured on the shells, in FBX units.
# ---------------------------------------------------------------------------------------------
CX = 0.0
JOINTS = {
    "base":   (None,     (CX, 0.300, 0.030)),
    "torso":  ("base",   (CX, 0.400, 0.000)),
    "head":   ("torso",  (CX, 0.840, 0.050)),
    "arm_l":  ("torso",  (0.240, 0.770, 0.020)),
    "fore_l": ("arm_l",  (0.370, 0.600, 0.000)),
    "nano":   ("fore_l", (0.416, 0.368, 0.203)),
    "arm_r":  ("torso",  (-0.240, 0.770, 0.020)),
    "fore_r": ("arm_r",  (-0.370, 0.600, 0.000)),
    "hand_r": ("fore_r", (-0.410, 0.365, 0.070)),
    "muzzle": ("hand_r", (-0.410, 0.310, 0.190)),
    "leg_l":  ("base",   (0.140, 0.280, 0.035)),
    "shin_l": ("leg_l",  (0.210, 0.190, 0.049)),
    "foot_l": ("shin_l", (0.224, 0.075, 0.027)),
    "leg_r":  ("base",   (-0.140, 0.280, 0.035)),
    "shin_r": ("leg_r",  (-0.210, 0.190, 0.049)),
    "foot_r": ("shin_r", (-0.224, 0.075, 0.027)),
}
ORDER = ["base", "torso", "head", "arm_l", "fore_l", "nano", "arm_r", "fore_r", "hand_r", "muzzle",
         "leg_l", "shin_l", "foot_l", "leg_r", "shin_r", "foot_r"]
MARKERS = ("nano", "muzzle")     # hidden triangles: build beam origin (left forearm nozzle), weapon muzzle (right fist)

# Assignment bones, front view (x, y), robot-left side (x > 0); the right side is mirrored. (segment, radius).
# Measured on the mesh (height 1): the body, the arms and the legs are all welded in one shell.
UPPER_ARM = ((0.240, 0.770), (0.370, 0.620), 0.070)
FOREARM = ((0.370, 0.600), (0.410, 0.330), 0.095)
THIGH = ((0.140, 0.280), (0.210, 0.190), 0.110)
SHIN = ((0.210, 0.190), (0.224, 0.075), 0.085)
FIST_Y = 0.365          # right arm only: below this height the forearm ellipsoid ends and the fist begins
FOOT_Y = 0.070          # centroids below this height belong to the foot
WAIST_Y = 0.375         # belt: the whole belt turns with the torso
HEAD_C = (0.0, 0.915, 0.070)   # head sphere centre; the collar behind and under the head stays on the torso
HEAD_R = 0.135
TORSO_W = ((0.375, 0.290), (0.450, 0.295), (0.550, 0.290), (0.650, 0.270), (0.720, 0.220), (0.800, 0.170), (0.840, 0.120))
BASE_W = ((0.180, 0.000), (0.220, 0.100), (0.280, 0.200), (0.330, 0.280), (0.375, 0.290))


def seg_dist(p, a, b):
    a, b = np.array(a), np.array(b)
    ab = b - a
    t = np.clip(((p - a) @ ab) / (ab @ ab), 0.0, 1.0)
    return np.linalg.norm(p - (a + t[:, None] * ab), axis=1)


def profile(y, table):
    return np.interp(y, [t[0] for t in table], [t[1] for t in table])


def assign(v, tris):
    """Piece name per triangle: the lowest score wins; score = distance to a bone segment minus its radius (inside < 0).
    Torso and base use a half-width profile in the front view instead of a radius."""
    c = v[tris].mean(axis=1)
    a, y = np.abs(c[:, 0]), c[:, 1]
    side = np.where(c[:, 0] > CX, "_l", "_r")
    q = np.stack([a, y], axis=1)                       # mirror the right side onto the left bones
    names = ["head", "torso", "base", "arm", "fore", "leg", "shin"]
    big = 9.0
    S = {
        "torso": np.where(y >= WAIST_Y, a - profile(y, TORSO_W), big),
        "base": np.where(y < WAIST_Y, a - profile(y, BASE_W), big),
        "arm": seg_dist(q, UPPER_ARM[0], UPPER_ARM[1]) - UPPER_ARM[2],
        "fore": seg_dist(q, FOREARM[0], FOREARM[1]) - FOREARM[2],
        "leg": np.where(y < WAIST_Y, seg_dist(q, THIGH[0], THIGH[1]) - THIGH[2], big),
        "shin": np.where(y < WAIST_Y, seg_dist(q, SHIN[0], SHIN[1]) - SHIN[2], big),
    }
    best = np.array(["torso", "base", "arm", "fore", "leg", "shin"])[np.argmin(np.stack([S[k] for k in ("torso", "base", "arm", "fore", "leg", "shin")]), axis=0)]
    out = np.empty(len(tris), object)
    rules = {}
    for i in range(len(tris)):
        s_ = side[i]
        b = best[i]
        if y[i] > 0.80 and np.linalg.norm(c[i] - np.array(HEAD_C)) < HEAD_R:
            piece = "head"
        elif y[i] < FOOT_Y and a[i] > 0.05:
            piece = "foot" + s_
        elif b in ("torso", "base"):
            piece = b
        elif b == "fore" and s_ == "_r" and y[i] < FIST_Y:
            piece = "hand_r"
        else:
            piece = b + s_
        piece = str(piece)
        out[i] = piece
        rules[piece] = rules.get(piece, 0) + 1
    return out, rules


# Team colour zones (CMD-08: shoulder pads, belt, chest plate, elbows, knees), found by geometry because the Tripo
# texture has no colour to key on. Model height 1, +x = robot left, +z = front. (centre x, y, z), radius.
SHOULDERS = ((0.240, 0.770, 0.020), 0.100)
ELBOWS = ((0.370, 0.600, 0.000), 0.060)
KNEES = ((0.230, 0.205, 0.100), 0.050)         # the small guard ball on the front of the knee, z > 0.06
CHEST = ((0.000, 0.727, 0.240), 0.075)         # round plate on the front of the torso, z > 0.12
BELT_Y = (WAIST_Y, 0.485)


def team_zones(v, tris, piece):
    """Boolean per triangle: True where the team colour goes. A triangle counts only if all three vertices are inside
    the zone, so the edges follow the mesh rows instead of cutting triangles by their centre."""
    V = v[tris].copy()                     # (n, 3, 3)
    V[..., 0] = np.abs(V[..., 0])          # mirror the right side onto the left
    m = np.zeros(len(tris), bool)
    for (ctr, r) in (SHOULDERS, ELBOWS):
        m |= (np.linalg.norm(V - np.array(ctr), axis=2) < r).all(axis=1)
    m |= ((np.linalg.norm(V[..., :2] - np.array(KNEES[0][:2]), axis=2) < KNEES[1]) & (V[..., 2] > 0.06)).all(axis=1)
    W = v[tris]
    m |= ((np.linalg.norm(W[..., :2] - np.array(CHEST[0][:2]), axis=2) < CHEST[1]) & (W[..., 2] > 0.12)).all(axis=1)
    belt = ((W[..., 1] >= BELT_Y[0] - 0.01) & (W[..., 1] <= BELT_Y[1] + 0.01)).all(axis=1)
    m |= belt & (piece == "torso") & (np.hypot(W[..., 0], W[..., 2]).min(axis=1) > 0.22)
    return m


def raster_uv(tris_uv, size, v_up=True):
    """Pixels covered by UV triangles (n,3,2) on a size x size texture; row from the top = (1 - v) * size."""
    cov = np.zeros((size, size), bool)
    for t in tris_uv:
        x = t[:, 0] * size
        y = (1.0 - t[:, 1]) * size if v_up else t[:, 1] * size
        x0, x1 = int(max(np.floor(x.min()), 0)), int(min(np.ceil(x.max()), size - 1))
        y0, y1 = int(max(np.floor(y.min()), 0)), int(min(np.ceil(y.max()), size - 1))
        den = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
        if abs(den) < 1e-12:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
        w0 = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / den
        w1 = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / den
        w2 = 1 - w0 - w1
        cov[y0:y1 + 1, x0:x1 + 1] |= (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
    return cov


def zone_alpha(sel_uv, other_uv, size):
    """Alpha 0..1 on the texture: pixels of the selected UV triangles, grown by 1 pixel where no other triangle lives."""
    a = raster_uv(sel_uv, size)
    o = raster_uv(other_uv, size)
    g = a.copy()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        g |= np.roll(np.roll(a, dy, 0), dx, 1)
    return (a | (g & ~o)).astype(float)


def marker(point, size=0.004):
    x, y, z = point
    return np.array([(x - size, y, z - size), (x + size, y, z - size), (x, y, z + size)])


def build(fbx_path, p):
    ver, root = read_fbx(fbx_path)
    v, tris, uvs = fbx_mesh(root)
    v = v - np.array([0.0, v[:, 1].min(), 0.0])
    v = v / (v[:, 1].max())                       # height 1, sole at 0 (Tripo exports are already like this)
    n_in = len(tris)
    piece, rules = assign(v, tris)
    print("SSS FBX %d, %d triangoli e %d vertici in ingresso; triangoli per pezzo: %s" % (ver, n_in, len(v), rules))
    print("SSS nessuna riduzione dei triangoli")
    zone = team_zones(v, tris, piece)
    print("SSS zone colore giocatore (CMD-08): %d triangoli su %d" % (int(zone.sum()), n_in))
    zone_uv = (uvs[zone], uvs[~zone])
    parts = {n: [] for n in ORDER}
    for t, (tri, uv) in enumerate(zip(tris, uvs)):
        parts[piece[t]].append((v[tri], uv))
    for m in MARKERS:          # hidden marker: UV on a dark texel
        parts[m].append((marker(JOINTS[m][1]), np.array([[0.02, 0.02]] * 3)))
    return parts, root, zone_uv


def assemble(parts, target_height):
    """Scale once (k = h / extent in y), vertices relative to each piece joint. Returns per piece arrays."""
    k = float(target_height)          # model height is 1 after build()
    out = {}
    for name in ORDER:
        joint = np.array(JOINTS[name][1]) * k
        tri = [t * k - joint for t, _ in parts[name]]
        out[name] = {"tris": np.array(tri).reshape(-1, 3, 3), "uv": np.array([u for _, u in parts[name]]).reshape(-1, 3, 2)}
    return out, k


# ---------------------------------------------------------------------------------------------
# Textures
# ---------------------------------------------------------------------------------------------
def write_png_rgba(path, arr):  # arr: uint8 (h, w, 4); by hand because Blender zeroes RGB where alpha is 0
    h, w = arr.shape[:2]
    raw = np.zeros((h, w * 4 + 1), np.uint8)
    raw[:, 1:] = arr.reshape(h, w * 4)

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    data = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw.tobytes(), 6)) + chunk(b"IEND", b""))
    with open(path, "wb") as fh:
        fh.write(data)


def load_rgb(path):
    """Image rows from the top, float 0..1. Inside Blender via bpy (rows come from the bottom), else PIL."""
    if bpy is not None:
        img = bpy.data.images.load(path)
        img.colorspace_settings.name = "Non-Color"
        w, h = img.size
        buf = np.empty(w * h * 4, np.float32)
        img.pixels.foreach_get(buf)
        return buf.reshape(h, w, 4)[::-1, :, :3].astype(float)
    from PIL import Image
    return np.asarray(Image.open(path).convert("RGB"), float) / 255.0


def team_mask(rgb):
    """Alpha for the team colour from the saturated red of the Tripo texture (method of the technical base)."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx, mn = rgb.max(axis=2), rgb.min(axis=2)
    sat = np.where(mx > 1e-6, (mx - mn) / np.maximum(mx, 1e-6), 0.0)
    score = (np.clip((r - np.maximum(g, b) * 1.6) / 0.18, 0, 1) * np.clip((sat - 0.45) / 0.25, 0, 1)
             * np.clip((r - 0.22) / 0.15, 0, 1))
    return score


def make_textures(src, size, zone_uv=None, mode="zones"):
    rgb = load_rgb(src)
    while rgb.shape[0] > size:                      # 2x2 average down to the target size
        h, w = rgb.shape[:2]
        rgb = rgb[:h // 2 * 2, :w // 2 * 2].reshape(h // 2, 2, w // 2, 2, 3).mean(axis=(1, 3))
    tex1 = np.zeros(rgb.shape[:2] + (4,), np.uint8)
    tex1[..., :3] = np.clip(rgb * 255 + 0.5, 0, 255).astype(np.uint8)
    alpha = np.zeros(rgb.shape[:2])
    if mode in ("red", "both"):
        alpha = np.maximum(alpha, team_mask(rgb))
    if mode in ("zones", "both") and zone_uv is not None:
        alpha = np.maximum(alpha, zone_alpha(zone_uv[0], zone_uv[1], rgb.shape[0]))
    tex1[..., 3] = np.clip(alpha * 255 + 0.5, 0, 255).astype(np.uint8)
    tex2 = np.zeros_like(tex1)
    tex2[:, :] = (0, 128, 0, 255)                   # R glow, G reflection: hypotheses; this value is accepted
    return tex1, tex2


# ---------------------------------------------------------------------------------------------
# S3O re-read (layout from the S3O spec as remembered; agreed with the real exporter on ___lab, 16 Nov)
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
    print("SSS definizione:", found)
    if not p["deploy"]:
        print("DEPLOY saltato: deploy=false (genera solo in out/)")
        return
    sub = (p["subdir"].strip("/") + "/") if p["subdir"] else ""
    obj_name = sub + NAME + ".s3o"
    if found:
        val = found[1]
        if val and os.path.basename(val).lower() in SHARED:
            print("DEPLOY avviso: la scheda usa ObjectName = \"%s\", file condiviso dai Commander: non lo tocco, "
                  "scrivo %s; la scheda va puntata li" % (val, obj_name))
        elif val:
            obj_name = val
    else:
        print("DEPLOY avviso: scheda %s.lua non trovata sotto units/; deve avere ObjectName = \"%s\" "
              "(la scheda non la scrive questo script)" % (NAME, obj_name))
    targets = [
        (files["s3o"], os.path.join(game_dir, "objects3d", obj_name)),
        (files["tex1"], os.path.join(game_dir, "unittextures", NAME + "1.png")),
        (files["tex2"], os.path.join(game_dir, "unittextures", NAME + "2.png")),
    ]
    bdir = os.path.join(game_dir, "easywar_work", "backup", NAME + "_data")
    for src, dst in targets:
        if os.path.basename(dst).lower() in SHARED:
            print("DEPLOY saltato per", dst, "(file condiviso dai Commander)")
            continue
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
# Preview without Blender: numpy z-buffer with the texture, team colour shown as green
# ---------------------------------------------------------------------------------------------
def world_tris(pieces, k, pose=None):
    """Triangles in world coordinates; pose = {piece: [(axis, degrees), ...]} rotations about the joint."""
    pose = pose or {}
    mats = {}

    def rot(axis, deg):
        a = math.radians(deg)
        c, s = math.cos(a), math.sin(a)
        if axis == "x":
            return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    for name in ORDER:
        parent, j = JOINTS[name]
        R = np.eye(3)
        for axis, deg in pose.get(name, []):
            R = R @ rot(axis, deg)
        jw = np.array(j) * k
        if parent is None:
            mats[name] = (R, jw)
        else:
            PR, Pt = mats[parent]
            mats[name] = (PR @ R, PR @ (jw - np.array(JOINTS[parent][1]) * k) + Pt)
    out, uv = [], []
    for name in ORDER:
        R, t = mats[name]
        out.append(pieces[name]["tris"] @ R.T + t)
        uv.append(pieces[name]["uv"])
    return np.concatenate(out), np.concatenate(uv)


def render(tris, uvs, tex, view, size, k, silhouette=False):
    if view == "front":
        sx, sy, d = tris[..., 0], tris[..., 1], tris[..., 2]
    elif view == "side":
        sx, sy, d = -tris[..., 2], tris[..., 1], tris[..., 0]
    else:
        sx, sy, d = -tris[..., 0], tris[..., 1], -tris[..., 2]
    sc = (size - 8) / (1.1 * k)
    px, py = size / 2 + sx * sc, size - 4 - sy * sc
    img = np.full((size, size, 3), 255, np.uint8)
    zb = np.full((size, size), -1e18)
    th, tw = tex.shape[:2]
    L = np.array([0.3, 0.5, 0.8]); L /= np.linalg.norm(L)
    team = np.array([40, 200, 60], float)
    for i in range(len(tris)):
        x, y, z = px[i], py[i], d[i]
        den = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
        if abs(den) < 1e-12:
            continue
        x0, x1 = max(int(x.min()), 0), min(int(x.max()) + 1, size - 1)
        y0, y1 = max(int(y.min()), 0), min(int(y.max()) + 1, size - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
        w0 = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / den
        w1 = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / den
        w2 = 1 - w0 - w1
        m = (w0 >= -1e-4) & (w1 >= -1e-4) & (w2 >= -1e-4)
        zz = w0 * z[0] + w1 * z[1] + w2 * z[2]
        sub = zb[y0:y1 + 1, x0:x1 + 1]
        up = m & (zz > sub)
        if not up.any():
            continue
        sub[up] = zz[up]
        if silhouette:
            img[y0:y1 + 1, x0:x1 + 1][up] = 0
            continue
        n = np.cross(tris[i][1] - tris[i][0], tris[i][2] - tris[i][0]); ln = np.linalg.norm(n)
        sh = 0.55 + 0.45 * abs(np.dot(n / ln, L)) if ln > 0 else 0.8
        u = w0 * uvs[i, 0, 0] + w1 * uvs[i, 1, 0] + w2 * uvs[i, 2, 0]
        vv = w0 * uvs[i, 0, 1] + w1 * uvs[i, 1, 1] + w2 * uvs[i, 2, 1]
        cx = np.clip((u % 1) * tw, 0, tw - 1).astype(int)
        cy = np.clip((1 - vv % 1) * th, 0, th - 1).astype(int)   # v_up: row from the top = (1 - v) * h
        px_ = tex[cy, cx].astype(float)
        a = px_[..., 3:4] / 255.0
        col = (px_[..., :3] * (1 - a) + team * a) * sh
        img[y0:y1 + 1, x0:x1 + 1][up] = np.clip(col, 0, 255).astype(np.uint8)[up]
    return img


def preview(pieces, k, tex1, path):
    rest, ruv = world_tris(pieces, k)
    walk, wuv = world_tris(pieces, k, {"leg_l": [("x", -25)], "shin_l": [("x", 5)], "foot_l": [("x", 20)],
                                       "leg_r": [("x", 20)], "shin_r": [("x", 10)], "foot_r": [("x", -30)],
                                       "arm_l": [("x", 12)], "arm_r": [("x", -12)]})
    build, buv = world_tris(pieces, k, {"torso": [("y", 30)], "arm_l": [("x", -90)], "arm_r": [("x", -90)]})
    size = 420
    cells = [render(rest, ruv, tex1, "front", size, k), render(rest, ruv, tex1, "side", size, k),
             render(rest, ruv, tex1, "back", size, k), render(walk, wuv, tex1, "side", size, k),
             render(build, buv, tex1, "side", size, k)]
    sil = render(rest, ruv, tex1, "front", 60, k, silhouette=True)
    cell = np.full((size, size, 3), 255, np.uint8)
    cell[180:240, 180:240] = sil
    sheet = np.concatenate(cells + [cell], axis=1)
    write_png_rgba(path, np.concatenate([sheet, np.full(sheet.shape[:2] + (1,), 255, np.uint8)], axis=2))


# ---------------------------------------------------------------------------------------------
# Blender part (same sequence as ___lab.py, seen working on 16 Nov 2026)
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
        tri = pieces[name]["tris"]
        uvs = pieces[name]["uv"]
        verts, faces, index = [], [], {}
        for t3 in tri.tolist():              # shared corners stay shared (Blender vertex count = real count)
            f = []
            for c in t3:
                key = (round(c[0], 5), round(c[1], 5), round(c[2], 5))
                if key not in index:
                    index[key] = len(verts)
                    verts.append(to_blender(c))
                f.append(index[key])
            faces.append(tuple(f))
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        uv = mesh.uv_layers.new(name="UVMap")
        for i in range(len(tri)):
            for c in range(3):
                u, vu = uvs[i, c]
                uv.data[3 * i + c].uv = (u, (1.0 - vu) if p["flip_v"] else vu)
        for poly in mesh.polygons:
            poly.use_smooth = bool(p["smooth"])
        ob = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(ob)
        objs[name] = ob
    for name in ORDER:
        parent = JOINTS[name][0]
        if parent:
            objs[name].parent = objs[parent]
            rel = (np.array(JOINTS[name][1]) - np.array(JOINTS[parent][1])) * k
            objs[name].location = to_blender(rel)
    objs["base"].location = to_blender(np.array(JOINTS["base"][1]) * k)
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
    print("SSS triangoli Blender:", sum(len(o.data.polygons) for o in objs.values()),
          "vertici Blender:", sum(len(o.data.vertices) for o in objs.values()))
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
            print("SSS parametri non validi, uso i predefiniti:", e)
    return P


def find_fbx(p):
    if p["fbx"]:
        return p["fbx"] if os.path.isabs(p["fbx"]) else os.path.join(HERE, p["fbx"])
    for fname in (NAME + ".fbx", "baymax.fbx"):       # the Tripo export keeps its own name; never "the first .fbx found"
        own = os.path.join(HERE, fname)
        if os.path.exists(own):
            return own
    raise RuntimeError("metti %s.fbx (o baymax.fbx) accanto allo script, in %s" % (NAME, HERE))


def find_game_dir(p):
    if p["game_dir"]:
        return p["game_dir"]
    d = HERE
    while True:
        if os.path.isdir(os.path.join(d, "units")):
            return d
        up = os.path.dirname(d)
        if up == d:
            raise RuntimeError("cartella del gioco non trovata sopra " + HERE)
        d = up


def main():
    p = parse_params()
    os.makedirs(OUT, exist_ok=True)
    fbx = find_fbx(p)
    print("SSS FBX:", fbx)
    parts, root, zone_uv = build(fbx, p)
    pieces, k = assemble(parts, p["target_height"])
    ntri = sum(len(d["tris"]) for d in pieces.values())
    allv, _ = world_tris(pieces, k)
    allv = allv.reshape(-1, 3)
    ext = allv.max(axis=0) - allv.min(axis=0)
    print("SSS pezzi %d: %s" % (len(ORDER), ", ".join("%s %d" % (n, len(pieces[n]["tris"])) for n in ORDER)))
    print("SSS altezza %.2f, ingombro X %.2f Y %.2f Z %.2f" % (ext[1], ext[0], ext[1], ext[2]))
    print("SSS hitbox proposta (non verificata): collisionVolumeScales = \"%.1f %.1f %.1f\"" % (ext[0], ext[1], ext[2]))
    nvb = sum(len({tuple(np.round(c, 5)) for t3 in d["tris"] for c in t3}) for d in pieces.values())
    print("SSS vertici Blender (stima, angoli condivisi per posizione): %d; nel .s3o circa 2,6-3 per triangolo: %d-%d"
          % (nvb, int(2.6 * ntri), 3 * ntri))
    print("TRIANGOLI", ntri)

    files = {"s3o": os.path.join(OUT, NAME + ".s3o"), "tex1": os.path.join(OUT, NAME + "1.png"),
             "tex2": os.path.join(OUT, NAME + "2.png")}
    ready = [os.path.join(HERE, NAME + s) for s in ("1.png", "2.png")]
    if all(os.path.exists(r) for r in ready):
        shutil.copy2(ready[0], files["tex1"])
        shutil.copy2(ready[1], files["tex2"])
        print("SSS texture: uso i PNG pronti accanto allo script")
        tex1 = None
    else:
        src = texture_path(fbx, root, p)
        if not src:
            raise RuntimeError("texture non trovata: servono %s1.png/%s2.png o il *_basecolor.jpg" % (NAME, NAME))
        tex1, tex2 = make_textures(src, p["tex_size"], zone_uv, p["team_mask"])
        write_png_rgba(files["tex1"], tex1)
        write_png_rgba(files["tex2"], tex2)
        print("SSS texture da %s: %dx%d, colore giocatore sul %.1f%% dei pixel" % (
            os.path.basename(src), tex1.shape[1], tex1.shape[0], 100.0 * (tex1[..., 3] > 127).mean()))
    game_dir = find_game_dir(p)
    print("SSS gioco:", game_dir)

    if bpy is None:
        if p["preview"]:
            if tex1 is None:
                from PIL import Image
                tex1 = np.asarray(Image.open(files["tex1"]).convert("RGBA"))
            preview(pieces, k, tex1, os.path.join(OUT, NAME + "_preview.png"))
            print("SSS anteprima scritta in", os.path.join(OUT, NAME + "_preview.png"))
        print("SSS fuori da Blender: modello .s3o non generato")
        return
    run_blender(p, pieces, k, files)
    back = read_s3o(files["s3o"])
    ok = back["pieces"] == len(ORDER) and back["tris"] == ntri
    print("SSS .s3o riletto: pezzi %d, triangoli %d, texture %s -> %s" % (back["pieces"], back["tris"], back["tex"], "torna" if ok else "NON torna"))
    print("VERTICI nel .s3o:", back["verts"])
    deploy(p, game_dir, files)


if __name__ == "__main__":
    main()
