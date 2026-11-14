# Easy War - unita' "constructor" (costruttore di base, stile neutro).
# Va in easywar_work/base/constructor.py. Il nome del file e' il nome dell'unita':
# genera constructor.s3o, constructor1.png, constructor2.png, constructor.lua e li consegna nel gioco.
#
# Uso:
#   flatpak run org.blender.Blender --background --python /home/p/.spring/games/easywar.sdd/easywar_work/base/constructor.py | grep -E "S3O_ROOT|DEPLOY|TRIANGOLI"
# Con parametri (JSON dopo "--"), per esempio:
#   ... constructor.py -- '{"scale":12,"deploy":false}'
import os, sys

try:
    _ME = os.path.abspath(__file__)
except NameError:
    _ME = os.path.abspath(sys.argv[sys.argv.index("--python") + 1])
sys.path.insert(0, os.path.dirname(os.path.dirname(_ME)))   # cartella easywar_work, dove sta easywar_lib.py
import easywar_lib

# Misure prima della scala globale (Z su, fronte verso -Y).
# Regola del canone: tutto porta il nome dell'unita'. Il Lua si chiama constructor.lua e la definizione
# dell'unita' (units/base/constructor.lua) deve dire script = "base/constructor.lua".
B = easywar_lib.Builder(_ME)
box, cyl, add = B.box, B.cyl, B.add

# Telaio e cingoli (zone scure)
add("base", None, (0, 0, 0), box((2.4, 3.2, 0.5), (0, 0, 0.55)), "dark")
add("track_l", "base", (-1.5, 0, 0), box((0.6, 3.4, 0.8), (0, 0, 0.4)), "dark")
add("track_r", "base", (1.5, 0, 0), box((0.6, 3.4, 0.8), (0, 0, 0.4)), "dark")
add("blade", "base", (0, -1.7, 0.3), box((2.6, 0.25, 0.6), (0, 0, 0.3)), "dark")

# Corpo, cabina, targhe del colore giocatore, fanali, ciminiera
add("body", "base", (0, 0, 0.8), box((2.2, 2.6, 0.7), (0, 0.2, 0.35)), "armor")
add("cab", "body", (0, -0.9, 0.7), box((1.5, 1.0, 0.7), (0, 0, 0.35)), "armor")
add("plate_l", "body", (-1.12, 0.2, 0.35), box((0.06, 1.6, 0.4), (-0.03, 0, 0)), "team")
add("plate_r", "body", (1.12, 0.2, 0.35), box((0.06, 1.6, 0.4), (0.03, 0, 0)), "team")
add("light_l", "cab", (-0.5, -0.5, 0.35), box((0.3, 0.1, 0.18), (0, -0.05, 0)), "accent")
add("light_r", "cab", (0.5, -0.5, 0.35), box((0.3, 0.1, 0.18), (0, -0.05, 0)), "accent")
add("stack", "body", (-0.7, 1.0, 0.7), cyl(0.15, 0.8, "z", (0, 0, 0.4)), "dark")

# Braccio da costruttore: base girevole, braccio, punta (nano) con emettitore
add("arm_base", "body", (0, 0.9, 0.7), cyl(0.35, 0.3, "z", (0, 0, 0.15)), "armor")
add("arm", "arm_base", (0, 0, 0.3), box((0.25, 1.6, 0.25), (0, -0.8, 0.12)), "dark")
add("nano", "arm", (0, -1.6, 0.1), box((0.35, 0.35, 0.35), (0, -0.1, 0)), "accent")

# Animazione: durante la costruzione il braccio si orienta verso il cantiere e si alza.
# ASSUNZIONI DA VERIFICARE nel motore: StartBuilding(heading, pitch)/StopBuilding/QueryNanoPiece come funzioni
# script.*, heading in radianti, WaitForTurn, e SetUnitValue(COB.INBUILDSTANCE, 1): senza "posizione di
# costruzione" attiva il costruttore potrebbe non iniziare a costruire.
LUA = "\n".join([
    "-- Generato da constructor.py per l'unita' " + B.name + ". Non modificare a mano: viene riscritto.",
    "local base, arm_base, arm, nano = piece('base', 'arm_base', 'arm', 'nano')",
    "",
    "function script.Create()",
    "  Spring.Echo('[easywar] constructor Create unitID=' .. tostring(unitID))",
    "end",
    "",
    "function script.StartBuilding(heading, pitch)",
    "  Spring.Echo('[easywar] constructor StartBuilding heading=' .. tostring(heading) .. ' pitch=' .. tostring(pitch))",
    "  SetUnitValue(COB.INBUILDSTANCE, 1)",
    "  Turn(arm_base, y_axis, heading, math.rad(180))",
    "  Turn(arm, x_axis, math.rad(-35), math.rad(90))",
    "end",
    "",
    "function script.StopBuilding()",
    "  Spring.Echo('[easywar] constructor StopBuilding')",
    "  SetUnitValue(COB.INBUILDSTANCE, 0)",
    "  Turn(arm_base, y_axis, 0, math.rad(90))",
    "  Turn(arm, x_axis, 0, math.rad(90))",
    "end",
    "",
    "-- Nome documentato: QueryNanopiece (p minuscola). Prima era scritto QueryNanoPiece e il motore non lo vedeva.",
    "function script.QueryNanopiece()",
    "  return nano",
    "end",
    "",
    "function script.Killed(recentDamage, maxHealth)",
    "  return 1",
    "end",
    "",
])

B.finalize(LUA)
