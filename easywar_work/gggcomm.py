# gggcomm.py - converts the Tripo FBX of the Gamma Commander into gggcomm.s3o, gggcomm1.png, gggcomm2.png and
# gggcomm.lua (walk, build with the left forearm, aim with the right claw arm). Realizes CMD-05..CMD-08 for Gamma.
# Method of the guide "Da modello Tripo a unita Recoil" (17 Nov 2026): FBX read in pure Python, Tripo UVs and
# texture kept, no triangle reduction by default. Deviation: this mesh has only 22 shells (head+torso+pelvis and each
# leg are one shell), so the body is cut at neck and waist and the legs at the knee, triangle by triangle.
# Optional: "claw_cell" > 0 simplifies the claw hand (83 % of the triangles) by vertex clustering.
#
# Place: easywar_work/gggcomm.py (commanders sit at the root, like units/gggcomm.lua). Files next to it: gggcomm.fbx (Tripo export, renamed) and its texture, either the ready-made
# gggcomm1.png / gggcomm2.png (preferred) or the Tripo *_basecolor.jpg (in the same folder or in its .fbm folder).
#
# Run in Blender:  flatpak run org.blender.Blender --background --python gggcomm.py | grep -E "GGG|S3O_ROOT|DEPLOY|TRIANGOLI|VERTICI"
# Params as JSON after "--":  ... gggcomm.py -- '{"target_height":44,"claw_cell":0.010}'
# Outside Blender (checks + preview only):  python3 -I gggcomm.py '{"preview":true}'

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

NAME = "gggcomm"          # fixed on purpose: every produced file carries this name

P = {
    "target_height": 44.0,   # engine units (vademecum: commander fallback height 44)
    "claw_cell": 0.0,        # 0 = no reduction (guide); e.g. 0.010 clusters the claw hand: 4048 -> 944 triangles
    "yaw_deg": 180.0,        # rotation of the root piece about Z (see technical base)
    "flip_v": True,          # the engine shows textures flipped vs Blender: v = 1 - v_up
    "tex_size": 1024,        # tex1 side; the 2048 Tripo texture is averaged 2x2
    "deploy": True,          # paste model, textures and Lua into the game (backup of replaced files first)
    "backup": True,
    "subdir": "",            # commanders live at level 0: objects3d/gggcomm.s3o, scripts/gggcomm.lua
    "preview": True,         # outside Blender: write the preview sheet
    "fbx": None,             # default: gggcomm.fbx next to the script, else the only .fbx there
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


def texture_path(fbx_path, root):
    """The texture named in the FBX (relative to the FBX), else a *basecolor* image next to the script."""
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
CX = -0.0095
JOINTS = {
    "base":   (None,     (CX, 0.620, 0.000)),
    "torso":  ("base",   (CX, 0.655, 0.000)),
    "head":   ("torso",  (CX, 0.870, 0.010)),
    "arm_l":  ("torso",  (0.125, 0.825, -0.035)),
    "fore_l": ("arm_l",  (0.172, 0.695, -0.050)),
    "nano":   ("fore_l", (0.226, 0.390, 0.048)),
    "arm_r":  ("torso",  (-0.145, 0.825, -0.035)),
    "fore_r": ("arm_r",  (-0.190, 0.695, -0.050)),
    "hand_r": ("fore_r", (-0.225, 0.485, 0.005)),
    "muzzle": ("hand_r", (-0.232, 0.380, 0.020)),
    "leg_l":  ("base",   (0.062, 0.610, 0.000)),
    "shin_l": ("leg_l",  (0.090, 0.340, 0.000)),
    "foot_l": ("shin_l", (0.122, 0.085, -0.020)),
    "leg_r":  ("base",   (-0.081, 0.610, 0.000)),
    "shin_r": ("leg_r",  (-0.109, 0.340, 0.000)),
    "foot_r": ("shin_r", (-0.141, 0.085, -0.020)),
}
ORDER = ["base", "torso", "head", "arm_l", "fore_l", "nano", "arm_r", "fore_r", "hand_r", "muzzle",
         "leg_l", "shin_l", "foot_l", "leg_r", "shin_r", "foot_r"]
MARKERS = ("nano", "muzzle")     # hidden triangles: build beam origin, weapon muzzle


def shells(nv, tris):
    par = list(range(nv))

    def f(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a
    for a, b, c in tris:
        for x, y in ((a, b), (b, c)):
            ra, rb = f(x), f(y)
            if ra != rb:
                par[ra] = rb
    return np.array([f(i) for i in range(nv)])


def assign(v, tris):
    """Piece name per triangle. Whole shells go to one piece; the body and the legs are cut by height."""
    lab = shells(len(v), tris)
    tl = lab[tris[:, 0]]
    cy = v[tris].mean(axis=1)[:, 1]
    out = np.empty(len(tris), object)
    rules = {}
    for s in sorted(set(tl.tolist())):
        m = tl == s
        vs = v[np.unique(tris[m])]
        y0, y1, dx = vs[:, 1].min(), vs[:, 1].max(), vs[:, 0].mean() - CX
        side = "_l" if dx > 0 else "_r"
        if y1 < 0.13:
            rule, out[m] = "piede", "foot" + side
        elif y1 > 0.95:
            rule = "corpo"
            out[m] = np.where(cy[m] > 0.870, "head", np.where(cy[m] > 0.655, "torso", "base"))
        elif y0 < 0.10 and y1 > 0.55:
            rule = "gamba"
            out[m] = np.where(cy[m] > 0.340, "leg" + side, "shin" + side)
        elif m.sum() <= 20 and 0.25 < vs[:, 1].mean() < 0.42:
            rule, out[m] = "ginocchio", "shin" + side
        elif y0 > 0.76:
            rule, out[m] = "spallaccio", "torso"
        elif y0 > 0.60:
            rule, out[m] = "omero", "arm" + side
        elif y1 > 0.70:
            rule, out[m] = "avambraccio", "fore" + side
        else:
            rule, out[m] = "artiglio", ("hand_r" if side == "_r" else "fore_l")
        rules[rule] = rules.get(rule, 0) + 1
    return out, rules


def cluster(v, tris, uvs, mask, cell):
    """Vertex clustering on the masked triangles: positions snapped to the cell mean, degenerate and duplicate
    triangles dropped. Every kept triangle keeps its own corner UVs. Deterministic (sorted ids, ordered dict)."""
    v = v.copy()
    ids = np.unique(tris[mask])
    groups = {}
    for i, key in zip(ids.tolist(), map(tuple, np.floor(v[ids] / cell).astype(np.int64).tolist())):
        groups.setdefault(key, []).append(i)
    rep = {}
    for g in groups.values():
        c = v[g].mean(axis=0)
        for i in g:
            rep[i] = g[0]
            v[i] = c
    keep = np.ones(len(tris), bool)
    t2 = tris.copy()
    seen = set()
    for r in np.where(mask)[0]:
        t2[r] = [rep[i] for i in tris[r]]
        key = tuple(sorted(t2[r].tolist()))
        if len(set(key)) < 3 or key in seen:
            keep[r] = False
        seen.add(key)
    return v, t2[keep], uvs[keep], keep


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
    claw = piece == "hand_r"
    n_claw = int(claw.sum())
    print("GGG FBX %d, %d triangoli e %d vertici in ingresso; gusci per regola: %s" % (ver, n_in, len(v), rules))
    if p["claw_cell"] > 0:
        v, tris, uvs, keep = cluster(v, tris, uvs, claw, p["claw_cell"])
        piece = piece[keep]
        print("GGG artiglio semplificato: %d -> %d triangoli (cella %.3f)" % (n_claw, int((piece == "hand_r").sum()), p["claw_cell"]))
    else:
        print("GGG nessuna riduzione dei triangoli (claw_cell = 0)")
    parts = {n: [] for n in ORDER}
    for t, (tri, uv) in enumerate(zip(tris, uvs)):
        parts[piece[t]].append((v[tri], uv))
    for m in MARKERS:          # hidden marker: UV on a dark texel
        parts[m].append((marker(JOINTS[m][1]), np.array([[0.02, 0.02]] * 3)))
    return parts, root


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


def make_textures(src, size):
    rgb = load_rgb(src)
    while rgb.shape[0] > size:                      # 2x2 average down to the target size
        h, w = rgb.shape[:2]
        rgb = rgb[:h // 2 * 2, :w // 2 * 2].reshape(h // 2, 2, w // 2, 2, 3).mean(axis=(1, 3))
    tex1 = np.zeros(rgb.shape[:2] + (4,), np.uint8)
    tex1[..., :3] = np.clip(rgb * 255 + 0.5, 0, 255).astype(np.uint8)
    tex1[..., 3] = np.clip(team_mask(rgb) * 255 + 0.5, 0, 255).astype(np.uint8)
    tex2 = np.zeros_like(tex1)
    tex2[:, :] = (0, 128, 0, 255)                   # R glow, G reflection: hypotheses; this value is accepted
    return tex1, tex2


# ---------------------------------------------------------------------------------------------
# Lua unit script
# ---------------------------------------------------------------------------------------------
LUA = """-- @NAME@: Gamma Commander. Generated by @NAME@.py: do not edit by hand.
-- Walk (4 phases), build with the left forearm (nano), aim weapons 1 and 2 with the right claw arm (muzzle).
local base, torso, head = piece('base', 'torso', 'head')
local arm_l, fore_l, nano = piece('arm_l', 'fore_l', 'nano')
local arm_r, fore_r, hand_r, muzzle = piece('arm_r', 'fore_r', 'hand_r', 'muzzle')
local leg_l, shin_l, foot_l = piece('leg_l', 'shin_l', 'foot_l')
local leg_r, shin_r, foot_r = piece('leg_r', 'shin_r', 'foot_r')

local FWD = -1                      -- x-axis sign that moves a piece forward (seen on other units); 1 if reversed
local rad = math.rad
local STEP, SPD = 220, rad(170)
local AIM_SPD, BUILD_SPD, REST_SPD = rad(240), rad(180), rad(90)
local SIG_WALK, SIG_AIM1, SIG_AIM2, SIG_BUILD, SIG_REST = 1, 2, 4, 8, 16

local aiming, building = false, false

local function X(p, a, s) Turn(p, x_axis, FWD * rad(a), s or SPD) end
local function Leg(thigh, shin, foot, a_thigh, a_knee)
  X(thigh, a_thigh); X(shin, -a_knee); X(foot, a_knee - a_thigh)
end
local function Arms(a)
  if not building then X(arm_l, a) end
  if not aiming then X(arm_r, -a) end
end

local function Walk()
  SetSignalMask(SIG_WALK)
  while true do
    Leg(leg_l, shin_l, foot_l, 25, 5);  Leg(leg_r, shin_r, foot_r, -20, 10); Arms(-12); Sleep(STEP)
    Leg(leg_l, shin_l, foot_l, 5, 0);   Leg(leg_r, shin_r, foot_r, 10, 40);  Arms(0);   Sleep(STEP)
    Leg(leg_r, shin_r, foot_r, 25, 5);  Leg(leg_l, shin_l, foot_l, -20, 10); Arms(12);  Sleep(STEP)
    Leg(leg_r, shin_r, foot_r, 5, 0);   Leg(leg_l, shin_l, foot_l, 10, 40);  Arms(0);   Sleep(STEP)
  end
end

local function StandStill()
  for _, p in ipairs({leg_l, shin_l, foot_l, leg_r, shin_r, foot_r}) do Turn(p, x_axis, 0, SPD) end
  if not building then Turn(arm_l, x_axis, 0, SPD) end
  if not aiming then Turn(arm_r, x_axis, 0, SPD) end
end

function script.Create()
  Spring.Echo('[easywar] @NAME@ Create unitID=' .. tostring(unitID))
end

function script.StartMoving() Signal(SIG_WALK); StartThread(Walk) end
function script.StopMoving()  Signal(SIG_WALK); StandStill() end

-- building: torso turns to the target, the left arm lifts the forearm cannon onto the line of sight
function script.StartBuilding(heading, pitch)
  Signal(SIG_BUILD); SetSignalMask(SIG_BUILD)
  building = true
  Turn(torso, y_axis, heading, BUILD_SPD)
  Turn(arm_l, x_axis, FWD * (rad(90) + pitch), BUILD_SPD)
  SetUnitValue(COB.INBUILDSTANCE, 1)
end

function script.StopBuilding()
  Signal(SIG_BUILD)
  building = false
  SetUnitValue(COB.INBUILDSTANCE, 0)
  Turn(arm_l, x_axis, 0, REST_SPD)
  if not aiming then Turn(torso, y_axis, 0, REST_SPD) end
end

function script.QueryNanopiece() return nano end
script.QueryNanoPiece = script.QueryNanopiece    -- alias; only the lower-case p spelling is known to work (seen)

-- weapons 1 and 2 (unit def): right arm with the claw; rest after 3 s without aiming
local function Rest()
  SetSignalMask(SIG_REST)
  Sleep(3000)
  aiming = false
  Turn(arm_r, x_axis, 0, REST_SPD)
  if not building then Turn(torso, y_axis, 0, REST_SPD) end
end

function script.AimFromWeapon(n) return fore_r end
function script.QueryWeapon(n) return muzzle end

function script.AimWeapon(n, heading, pitch)
  local sig = (n == 2) and SIG_AIM2 or SIG_AIM1
  Signal(sig); SetSignalMask(sig); Signal(SIG_REST)
  aiming = true
  Turn(torso, y_axis, heading, AIM_SPD)
  Turn(arm_r, x_axis, FWD * (rad(90) + pitch), AIM_SPD)
  WaitForTurn(torso, y_axis); WaitForTurn(arm_r, x_axis)
  StartThread(Rest)
  return true
end

function script.FireWeapon(n)
  Turn(fore_r, x_axis, -FWD * rad(10), rad(900)); Sleep(60); Turn(fore_r, x_axis, 0, rad(240))
end

function script.Killed(recentDamage, maxHealth) return 1 end
"""


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
    print("GGG definizione:", found)
    if not p["deploy"]:
        print("DEPLOY saltato: deploy=false (genera solo in out/)")
        return
    sub = (p["subdir"].strip("/") + "/") if p["subdir"] else ""
    obj_name, script = sub + NAME + ".s3o", sub + NAME + ".lua"
    if found:
        for label, val, own in (("ObjectName", found[1], obj_name), ("script", found[2], script)):
            if val and os.path.basename(val).lower() in SHARED:
                print("DEPLOY avviso: la definizione usa %s = \"%s\", file condiviso dai Commander: non lo tocco, "
                      "scrivo %s; la scheda va puntata li" % (label, val, own))
            elif val:
                if label == "ObjectName":
                    obj_name = val
                else:
                    script = val
    else:
        print("DEPLOY avviso: definizione %s.lua non trovata sotto units/; la scheda deve avere "
              "ObjectName = \"%s\" e script = \"%s\"" % (NAME, obj_name, script))
    targets = [
        (files["s3o"], os.path.join(game_dir, "objects3d", obj_name)),
        (files["tex1"], os.path.join(game_dir, "unittextures", NAME + "1.png")),
        (files["tex2"], os.path.join(game_dir, "unittextures", NAME + "2.png")),
        (files["lua"], os.path.join(game_dir, "scripts", script)),
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
            poly.use_smooth = False
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
    print("GGG triangoli Blender:", sum(len(o.data.polygons) for o in objs.values()),
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
            print("GGG parametri non validi, uso i predefiniti:", e)
    return P


def find_fbx(p):
    if p["fbx"]:
        return p["fbx"] if os.path.isabs(p["fbx"]) else os.path.join(HERE, p["fbx"])
    own = os.path.join(HERE, NAME + ".fbx")
    if os.path.exists(own):
        return own
    raise RuntimeError("metti %s.fbx accanto allo script, in %s" % (NAME, HERE))


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
    print("GGG FBX:", fbx)
    parts, root = build(fbx, p)
    pieces, k = assemble(parts, p["target_height"])
    ntri = sum(len(d["tris"]) for d in pieces.values())
    allv, _ = world_tris(pieces, k)
    allv = allv.reshape(-1, 3)
    ext = allv.max(axis=0) - allv.min(axis=0)
    print("GGG pezzi %d: %s" % (len(ORDER), ", ".join("%s %d" % (n, len(pieces[n]["tris"])) for n in ORDER)))
    print("GGG altezza %.2f, ingombro X %.2f Y %.2f Z %.2f" % (ext[1], ext[0], ext[1], ext[2]))
    print("GGG hitbox proposta (non verificata): collisionVolumeScales = \"%.1f %.1f %.1f\"" % (ext[0], ext[1], ext[2]))
    print("GGG stima vertici nel .s3o (3 per triangolo): %d" % (3 * ntri))
    print("TRIANGOLI", ntri)

    files = {"s3o": os.path.join(OUT, NAME + ".s3o"), "tex1": os.path.join(OUT, NAME + "1.png"),
             "tex2": os.path.join(OUT, NAME + "2.png"), "lua": os.path.join(OUT, NAME + ".lua")}
    ready = [os.path.join(HERE, NAME + s) for s in ("1.png", "2.png")]
    if all(os.path.exists(r) for r in ready):
        shutil.copy2(ready[0], files["tex1"])
        shutil.copy2(ready[1], files["tex2"])
        print("GGG texture: uso i PNG pronti accanto allo script")
        tex1 = None
    else:
        src = texture_path(fbx, root)
        if not src:
            raise RuntimeError("texture non trovata: servono %s1.png/%s2.png o il *_basecolor.jpg" % (NAME, NAME))
        tex1, tex2 = make_textures(src, p["tex_size"])
        write_png_rgba(files["tex1"], tex1)
        write_png_rgba(files["tex2"], tex2)
        print("GGG texture da %s: %dx%d, colore giocatore sul %.1f%% dei pixel" % (
            os.path.basename(src), tex1.shape[1], tex1.shape[0], 100.0 * (tex1[..., 3] > 127).mean()))
    with open(files["lua"], "w", encoding="utf-8") as fh:
        fh.write(LUA.replace("@NAME@", NAME))
    game_dir = find_game_dir(p)
    print("GGG gioco:", game_dir)

    if bpy is None:
        if p["preview"]:
            if tex1 is None:
                from PIL import Image
                tex1 = np.asarray(Image.open(files["tex1"]).convert("RGBA"))
            preview(pieces, k, tex1, os.path.join(OUT, NAME + "_preview.png"))
            print("GGG anteprima scritta in", os.path.join(OUT, NAME + "_preview.png"))
        print("GGG fuori da Blender: modello .s3o non generato")
        return
    run_blender(p, pieces, k, files)
    back = read_s3o(files["s3o"])
    ok = back["pieces"] == len(ORDER) and back["tris"] == ntri
    print("GGG .s3o riletto: pezzi %d, triangoli %d, texture %s -> %s" % (back["pieces"], back["tris"], back["tex"], "torna" if ok else "NON torna"))
    print("VERTICI nel .s3o:", back["verts"])
    deploy(p, game_dir, files)


if __name__ == "__main__":
    main()