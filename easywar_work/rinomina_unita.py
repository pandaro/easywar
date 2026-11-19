#!/usr/bin/env python3
"""Clona un'unita' esistente con un altro nome (modello .s3o, due texture, Lua, definizione).
Non serve Blender. Senza --apply stampa soltanto cosa farebbe.

  python3 rinomina_unita.py                      # prova a vuoto: tripo_mech_1 -> jjjcom
  python3 rinomina_unita.py --apply              # scrive
  python3 rinomina_unita.py --old X --new Y --def-dir units --apply

Regole: non cancella nulla e non modifica i file originali; se un file di destinazione
esiste gia' lo copia prima in easywar_work/backup/NEW_data/. La definizione nuova e' un
file nuovo (units/NEW.lua) ricavato dalla vecchia con i nomi sostituiti.
"""
import argparse, os, re, shutil, struct, sys, time

ap = argparse.ArgumentParser()
ap.add_argument("--game", default=os.path.expanduser("~/.spring/games/easywar.sdd"))
ap.add_argument("--old", default="tripo_mech_1")
ap.add_argument("--new", default="jjjcom")
ap.add_argument("--def-dir", default="units", help="cartella della nuova definizione (commander: units, livello 0)")
ap.add_argument("--apply", action="store_true")
a = ap.parse_args()
G, OLD, NEW = a.game, a.old, a.new
if not os.path.isdir(os.path.join(G, "units")):
    sys.exit("Non trovo %s/units" % G)

# 1. definizione vecchia (ricerca ricorsiva sotto units/)
old_def = None
for r, _, fs in os.walk(os.path.join(G, "units")):
    if OLD + ".lua" in fs:
        old_def = os.path.join(r, OLD + ".lua"); break
if not old_def: sys.exit("Definizione %s.lua non trovata sotto units/" % OLD)
dtxt = open(old_def, encoding="utf-8", errors="replace").read()
m_obj = re.search(r'objectname\s*=\s*["\']([^"\']+)["\']', dtxt, re.I)
m_scr = re.search(r'\bscript\s*=\s*["\']([^"\']+)["\']', dtxt, re.I)
if not m_obj: sys.exit("ObjectName non trovato in " + old_def)
old_obj = m_obj.group(1)                       # es. base/tripo_mech_1.s3o
old_scr = m_scr.group(1) if m_scr else None    # es. base/tripo_mech_1.lua
obj_dir = os.path.dirname(old_obj)
new_obj = (obj_dir + "/" if obj_dir else "") + NEW + ".s3o"
new_scr = None
if old_scr:
    sd = os.path.dirname(old_scr); new_scr = (sd + "/" if sd else "") + NEW + ".lua"

src_s3o = os.path.join(G, "objects3d", old_obj)
dst_s3o = os.path.join(G, "objects3d", new_obj)
src_lua = os.path.join(G, "scripts", old_scr) if old_scr else None
dst_lua = os.path.join(G, "scripts", new_scr) if new_scr else None
dst_def = os.path.join(G, a.def_dir, NEW + ".lua")
for p in [src_s3o] + ([src_lua] if src_lua else []):
    if not os.path.isfile(p): sys.exit("Manca " + p)

# 2. .s3o: nomi delle texture (header: 12 magic, u32 ver, 5 float, 4 u32 offset)
b = open(src_s3o, "rb").read()
if not b.startswith(b"Spring unit\0"): sys.exit("Non e' un .s3o")
OFF = 12 + 4 + 5 * 4        # inizio dei 4 offset: radice, collisione, tex1, tex2
root, coll, o1, o2 = struct.unpack_from("<4I", b, OFF)
def cstr(o): return b[o:b.index(b"\0", o)].decode("latin-1") if o else ""
t1, t2 = cstr(o1), cstr(o2)
ext = os.path.splitext(t1)[1] or ".png"
n1, n2 = NEW + "1" + ext, NEW + "2" + (os.path.splitext(t2)[1] or ext)
nb = bytearray(b)
p1 = len(nb); nb += n1.encode("latin-1") + b"\0"
p2 = len(nb); nb += n2.encode("latin-1") + b"\0"
struct.pack_into("<4I", nb, OFF, root, coll, p1, p2)   # le vecchie stringhe restano orfane, innocue

# 3. file texture
tex = []
for t, n in ((t1, n1), (t2, n2)):
    s = os.path.join(G, "unittextures", t)
    tex.append((s, os.path.join(G, "unittextures", n)))

# 4. definizione e Lua con i nomi sostituiti
name_re = re.compile(r'(?<![A-Za-z0-9_])' + re.escape(OLD) + r'(?![A-Za-z0-9_])')
ndef = name_re.sub(NEW, dtxt)
ndef = re.sub(r'(objectname\s*=\s*["\'])[^"\']+', lambda m: m.group(1) + new_obj, ndef, flags=re.I)
if new_scr: ndef = re.sub(r'(\bscript\s*=\s*["\'])[^"\']+', lambda m: m.group(1) + new_scr, ndef)
lua = open(src_lua, encoding="utf-8", errors="replace").read() if src_lua else None
nlua = name_re.sub(NEW, lua) if lua else None

# 5. piano
stamp = time.strftime("%Y%m%d_%H%M%S")
bk = os.path.join(G, "easywar_work", "backup", NEW + "_" + stamp)
def put(path, data):
    print(("SCRIVO " if a.apply else "SCRIVEREI ") + os.path.relpath(path, G) + ("  (esiste: copia in backup)" if os.path.exists(path) else ""))
    if not a.apply: return
    if os.path.exists(path):
        os.makedirs(bk, exist_ok=True); shutil.copy2(path, os.path.join(bk, os.path.basename(path)))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "wb").write(data if isinstance(data, (bytes, bytearray)) else data.encode("utf-8"))
print("definizione di origine:", os.path.relpath(old_def, G))
print("texture nel .s3o: %s, %s  ->  %s, %s" % (t1, t2, n1, n2))
put(dst_s3o, bytes(nb))
for s, d in tex:
    if not os.path.isfile(s): print("MANCA texture", s); continue
    put(d, open(s, "rb").read())
if dst_lua: put(dst_lua, nlua)
put(dst_def, ndef)
print("ObjectName ->", new_obj, "| script ->", new_scr)
print("Originali lasciati intatti (anche %s). Per toglierli: spostali a mano." % os.path.relpath(old_def, G))
if not a.apply: print("Prova a vuoto: aggiungi --apply per scrivere.")