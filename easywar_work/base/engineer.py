# Easy War - unita' "engineer" (costruttore bipede, stile neutro).
# Va in easywar_work/base/engineer.py. Il nome del file e' il nome dell'unita':
# genera engineer.s3o, engineer1.png, engineer2.png, engineer.lua e (se manca) units/base/engineer.lua.
#
# Uso:
#   flatpak run org.blender.Blender --background --python /home/p/.spring/games/easywar.sdd/easywar_work/base/engineer.py | grep -E "S3O_ROOT|DEPLOY|TRIANGOLI"
# Con parametri (JSON dopo "--"), per esempio:
#   ... engineer.py -- '{"scale":9,"deploy":false}'
import os, re, sys

try:
    _ME = os.path.abspath(__file__)
except NameError:
    _ME = os.path.abspath(sys.argv[sys.argv.index("--python") + 1])
sys.path.insert(0, os.path.dirname(os.path.dirname(_ME)))   # cartella easywar_work, dove sta easywar_lib.py
import easywar_lib

# Misure prima della scala globale (Z su, fronte verso -Y). Scala 8: altezza finale circa 41.
B = easywar_lib.Builder(_ME, scale=8.0)
box, cyl, add = B.box, B.cyl, B.add

L, W = 2.0, 0.4            # altezza dell'anca da terra, larghezza delle gambe
thigh = shin = L / 2
HIP_X = 0.35

# Bacino e gambe
add("base", None, (0, 0, 0), box((1.1, 0.7, 0.4), (0, 0, L + 0.2)), "dark")
for side, sx in (("l", -1), ("r", 1)):
    add("leg_" + side, "base", (sx * HIP_X, 0, L), box((W, W, thigh), (0, 0, -thigh / 2)), "armor")
    add("shin_" + side, "leg_" + side, (0, 0, -thigh), box((W * 0.8, W * 0.8, shin), (0, 0, -shin / 2)), "armor")
    add("foot_" + side, "shin_" + side, (0, 0, -shin),
        box((W * 1.3, W * 2.0, W * 0.4), (0, -W * 0.4, -W * 0.2)), "dark")

# Busto: vita del colore giocatore, torace, testa con visore, antenna
add("belly", "base", (0, 0, L + 0.4), box((1.2, 0.8, 0.7), (0, 0, 0.35)), "team")
add("torso", "belly", (0, 0, 0.7), box((1.6, 0.95, 0.9), (0, 0, 0.45)), "armor")
add("head", "torso", (0, -0.05, 0.9), box((0.8, 0.7, 0.6), (0, 0, 0.3)), "dark")
add("sensor", "head", (0, -0.35, 0.3), box((0.6, 0.08, 0.2), (0, -0.04, 0)), "accent")
add("antenna", "head", (0.25, 0.1, 0.6), cyl(0.05, 0.5, "z", (0, 0, 0.25)), "dark")

# Braccia: spalla (perno), braccio nel colore giocatore, avambraccio; mano a sinistra, utensile (nano) a destra
for side, sx in (("l", -1), ("r", 1)):
    add("shoulder_" + side, "torso", (sx * 1.0, 0, 0.65), cyl(0.3, 0.45, "x", (0, 0, 0)), "dark")
    add("arm_" + side, "shoulder_" + side, (0, 0, 0), box((0.35, 0.35, 0.9), (0, 0, -0.45)), "team")
    add("forearm_" + side, "arm_" + side, (0, 0, -0.9), box((0.3, 0.3, 0.8), (0, 0, -0.4)), "armor")
add("hand_l", "forearm_l", (0, 0, -0.8), box((0.3, 0.3, 0.25), (0, 0, -0.12)), "dark")
add("nano", "forearm_r", (0, 0, -0.8), box((0.35, 0.35, 0.3), (0, 0, -0.15)), "accent")

# --- Animazione (Lua) ---------------------------------------------------------------------------
# ASSUNZIONI DA VERIFICARE nel motore: segno dei gradi (FWD), asse x delle gambe e delle spalle, pose.
# Positivo = in avanti per le gambe e per le braccia; il ginocchio si piega con segno negativo.
LUA = "\n".join([
    "-- Generato da engineer.py per l'unita' " + B.name + ". Non modificare a mano: viene riscritto.",
    "local base, torso, shoulder_l, shoulder_r = piece('base', 'torso', 'shoulder_l', 'shoulder_r')",
    "local leg_l, leg_r, shin_l, shin_r, foot_l, foot_r, nano = piece('leg_l', 'leg_r', 'shin_l', 'shin_r', 'foot_l', 'foot_r', 'nano')",
    "",
    "-- Verso dei gradi: se il bot cammina con le gambe al contrario, mettere -1.",
    "local FWD = 1",
    "local function a(deg) return math.rad(FWD * deg) end",
    "",
    "local SIG_WALK = 1",
    "local SPD = math.rad(420)",
    "local STEP = 150",
    "",
    "local function Pose(lt, ls, lf, rt, rs, rf, al, ar, tw)",
    "  Turn(leg_l, x_axis, a(lt), SPD)",
    "  Turn(shin_l, x_axis, a(ls), SPD)",
    "  Turn(foot_l, x_axis, a(lf), SPD)",
    "  Turn(leg_r, x_axis, a(rt), SPD)",
    "  Turn(shin_r, x_axis, a(rs), SPD)",
    "  Turn(foot_r, x_axis, a(rf), SPD)",
    "  Turn(shoulder_l, x_axis, a(al), SPD / 2)",
    "  Turn(shoulder_r, x_axis, a(ar), SPD / 2)",
    "  Turn(torso, y_axis, math.rad(tw), SPD / 4)",
    "  Sleep(STEP)",
    "end",
    "",
    "local function Walk()",
    "  Signal(SIG_WALK)",
    "  SetSignalMask(SIG_WALK)",
    "  while true do",
    "    Pose(30, -5, -25,   -25, -40, 35,   -25, 25,   4)",
    "    Pose(5, -5, 0,      10, -60, 50,    0, 0,      0)",
    "    Pose(-25, -40, 35,  30, -5, -25,    25, -25,  -4)",
    "    Pose(10, -60, 50,   5, -5, 0,       0, 0,      0)",
    "  end",
    "end",
    "",
    "local function StopWalk()",
    "  Signal(SIG_WALK)",
    "  local s = math.rad(200)",
    "  Turn(leg_l, x_axis, 0, s)",
    "  Turn(shin_l, x_axis, 0, s)",
    "  Turn(foot_l, x_axis, 0, s)",
    "  Turn(leg_r, x_axis, 0, s)",
    "  Turn(shin_r, x_axis, 0, s)",
    "  Turn(foot_r, x_axis, 0, s)",
    "  Turn(shoulder_l, x_axis, 0, s)",
    "  Turn(shoulder_r, x_axis, 0, s)",
    "  Turn(torso, y_axis, 0, s)",
    "end",
    "",
    "function script.Create()",
    "  Spring.Echo('[easywar] " + B.name + " Create unitID=' .. tostring(unitID))",
    "end",
    "",
    "function script.StartMoving()",
    "  StartThread(Walk)",
    "end",
    "",
    "function script.StopMoving()",
    "  StopWalk()",
    "end",
    "",
    "function script.StartBuilding(heading, pitch)",
    "  Spring.Echo('[easywar] " + B.name + " StartBuilding heading=' .. tostring(heading))",
    "  SetUnitValue(COB.INBUILDSTANCE, 1)",
    "  Turn(torso, y_axis, heading, math.rad(240))",
    "  Turn(shoulder_r, x_axis, a(80), math.rad(200))",
    "end",
    "",
    "function script.StopBuilding()",
    "  SetUnitValue(COB.INBUILDSTANCE, 0)",
    "  Turn(torso, y_axis, 0, math.rad(120))",
    "  Turn(shoulder_r, x_axis, 0, math.rad(120))",
    "end",
    "",
    "-- Nome documentato: QueryNanopiece (p minuscola).",
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


# --- Definizione dell'unita' (units/base/engineer.lua): creata solo se non esiste, mai sovrascritta ------
def write_unitdef():
    if not B.P["deploy"]:
        return
    name = B.name
    gd = B.P["game_dir"]
    target = os.path.join(gd, "units", "base", name + ".lua")
    if os.path.exists(target):
        print("DEPLOY unitdef gia' presente, non sovrascritta:", target)
        return

    def grab(path, key, default):
        try:
            with open(path, encoding="utf-8") as f:
                m = re.search(key + r'\s*=\s*"([^"]+)"', f.read(), re.IGNORECASE)
            return m.group(1) if m else default
        except OSError:
            return default

    soldier = os.path.join(gd, "units", "base", "soldier.lua")
    move = grab(soldier, "movementclass", None)
    cat = grab(soldier, "category", None)
    note = []
    if move is None:
        move = "Small Vechicle"
        note.append("MovementClass copiata dal costruttore a cingoli: da cambiare con quella dei bot")
    if cat is None:
        cat = "TANK SMALL NOTAIR NOTSUB"
        note.append("Category copiata dal costruttore: da cambiare con quella dei bot")
    lines = [
        '-- Generata da engineer.py. Da rivedere: ' + ("; ".join(note) if note else "valori dei campi non verificati nel motore."),
        'local unitName  =  "' + name + '"',
        '',
        'local unitDef  =  {',
        '   BuildPic = "Constructor.png", -- segnaposto: manca l\'immagine di ' + name,
        '   Category = "' + cat + '",',
        '   ObjectName = "base/' + name + '.s3o",',
        '   name = "Engineer",',
        '   Side = "Vroomers",',
        '   UnitName = "Engineer",',
        '   script = "base/' + name + '.lua",',
        '   icontype = "constructor",',
        '   Description = "Bipedal builder.",',
        '   MaxDamage = 500,',
        '   idleTime = 300,',
        '   idleAutoHeal = 0,',
        '   RadarDistance = 0,',
        '   SightDistance = 500,',
        '   SoundCategory = "TANK",',
        '   Upright = 1,',
        '   corpse = [[constructor_dead]],',
        '   BuildCostEnergy = 80,',
        '   BuildCostMetal = 80,',
        '   Buildtime = 80,',
        '   maxAcc = 0.35,',
        '   BrakeRate = 0.1,',
        '   FootprintX = 2,',
        '   FootprintZ = 2,',
        '   MaxSlope = 45,',
        '   MaxVelocity = 1.6,',
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
        '   Builder = true,',
        '   ShowNanoSpray = true,',
        '   CanBeAssisted = true,',
        '   workerTime = 5,',
        '   repairSpeed = 3.3,',
        '   reclaimSpeed = 5,',
        '   buildDistance = 120,',
        '   terraformSpeed = 9001,',
        '   buildoptions = {',
    ]
    for o in ("extractor", "windturbine", "solarpanel", "tidalgenerator", "geothermalgenerator", "fusionreactor",
              "storage", "groundfactory", "hoverfactory", "airfactory", "navalfactory", "llt", "lmt", "aat",
              "hlt", "tp", "geothermalplasmacannon", "radartower", "caretaker", "bb", "volcano", "alpha"):
        lines.append("      [[" + o + "]],")
    lines += [
        '   },',
        '   collisionVolumeType = "box",',
        '   collisionVolumeOffsets = "0 0 0",',
        '   collisionVolumeScales = "20 41 8",',
        '   BadTargetCategory = "NOTAIR",',
        '   explodeAs = [[MediumExplosion]],',
        '   selfDestructAs = [[MediumExplosion]],',
        '   NoChaseCategory = "AIR",',
        '}',
        '',
        'return lowerkeys({ [unitName]  =  unitDef })',
        '',
    ]
    try:
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print("DEPLOY unitdef creata:", target, "| movementclass:", move, "| category:", cat)
        for n in note:
            print("DEPLOY ATTENZIONE:", n)
    except OSError as e:
        print("DEPLOY errore unitdef:", e)


write_unitdef()