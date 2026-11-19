-- Generato da soldier.py per l'unita' soldier (mech Type-1). Non modificare a mano: viene riscritto.
-- Animazioni: camminata pesante con oscillazione del busto, costruzione con il cannone dell'avambraccio
-- sinistro, mira con lo stesso braccio se la definizione dell'unita' ha delle armi.
-- Pezzi: base (bacino), torso (busto), head (cabina), arm_l/r (spalla e braccio), fore_l (cannone),
--        nano (bocca del cannone), fore_r (avambraccio), hand_r (pinza), leg_l/r (coscia),
--        shin_l/r (ginocchio e stinco), foot_l/r (piede). l = sinistra del robot, r = destra.
--
-- CONVENZIONE DEL SEGNO: sull'asse x un angolo NEGATIVO porta il pezzo in avanti.
-- Se nel gioco gambe e braccia vanno al contrario, basta mettere FWD = 1.

local base, torso, head = piece('base', 'torso', 'head')
local arm_l, arm_r = piece('arm_l', 'arm_r')
local fore_l, fore_r = piece('fore_l', 'fore_r')
local hand_r, nano = piece('hand_r', 'nano')
local leg_l, leg_r = piece('leg_l', 'leg_r')
local shin_l, shin_r = piece('shin_l', 'shin_r')
local foot_l, foot_r = piece('foot_l', 'foot_r')

local FWD = -1                 -- segno di "avanti" sull'asse x
local rad = math.rad
local STEP = 330               -- millisecondi per fase del passo (4 fasi = un passo completo): mech pesante
local SPD = rad(110)           -- velocita' di rotazione durante il passo (radianti al secondo)
local AIM_SPD = rad(200)       -- velocita' di busto e braccio quando puntano
local REST_DELAY = 2500        -- dopo quanto tempo il braccio torna al riposo
local BOB = 0.35               -- quanto il bacino sale e scende ad ogni passo (unita' del motore)
local SWAY = 3                 -- oscillazione del busto in gradi

local SIG_WALK = 1
local SIG_ARM = 2
local SIG_REST = 4

local moving = false
local busy = false             -- il cannone sta puntando (costruzione o mira)
local building = false

-- Gira un pezzo sull'asse x: a > 0 = in avanti (il segno lo mette FWD).
local function X(p, a, spd)
  Turn(p, x_axis, FWD * rad(a), spd or SPD)
end

-- Una posa delle gambe: coscia, ginocchio (positivo = piegato) e piede tenuto piatto.
local function Leg(thigh, shin, foot, a_thigh, a_knee)
  X(thigh, a_thigh)
  X(shin, -a_knee)
  X(foot, a_knee - a_thigh)
end

-- Le braccia oscillano: il sinistro solo se non sta puntando. La pinza destra segue il braccio.
local function Arms(a_left, a_right)
  if not busy then X(arm_l, a_left) end
  X(arm_r, a_right)
end

local function Walk()
  SetSignalMask(SIG_WALK)
  while true do
    -- 1: sinistra avanti, destra indietro e appoggiata; il peso si sposta a sinistra
    Leg(leg_l, shin_l, foot_l, 18, 4)
    Leg(leg_r, shin_r, foot_r, -14, 8)
    Arms(-10, 10)
    if not busy then Turn(torso, y_axis, rad(SWAY), rad(30)) end
    Move(base, y_axis, 0, 1.5)
    Sleep(STEP)
    -- 2: passaggio, la destra si stacca e si piega; il bacino sale
    Leg(leg_l, shin_l, foot_l, 4, 0)
    Leg(leg_r, shin_r, foot_r, 8, 28)
    Arms(0, 0)
    Move(base, y_axis, BOB, 1.5)
    Sleep(STEP)
    -- 3: destra avanti, sinistra indietro e appoggiata
    Leg(leg_r, shin_r, foot_r, 18, 4)
    Leg(leg_l, shin_l, foot_l, -14, 8)
    Arms(10, -10)
    if not busy then Turn(torso, y_axis, rad(-SWAY), rad(30)) end
    Move(base, y_axis, 0, 1.5)
    Sleep(STEP)
    -- 4: passaggio, la sinistra si stacca e si piega
    Leg(leg_r, shin_r, foot_r, 4, 0)
    Leg(leg_l, shin_l, foot_l, 8, 28)
    Arms(0, 0)
    Move(base, y_axis, BOB, 1.5)
    Sleep(STEP)
  end
end

local function StandStill()
  for _, p in ipairs({ leg_l, leg_r, shin_l, shin_r, foot_l, foot_r }) do
    Turn(p, x_axis, 0, SPD)
  end
  Move(base, y_axis, 0, 1.5)
  if not busy then Turn(torso, y_axis, 0, rad(30)) end
  Arms(0, 0)
end

function script.Create()
  Spring.Echo('[easywar] soldier Create unitID=' .. tostring(unitID))
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

-- ---- Cannone sinistro: costruzione e mira ----------------------------------------------------
-- A riposo il cannone punta in avanti. Per puntare, il busto gira verso il bersaglio (heading) e l'avambraccio
-- si inclina dell'angolo di mira (pitch): la canna resta sull'asse di mira.

local function PointArm(heading, pitch)
  Turn(torso, y_axis, heading, AIM_SPD)
  Turn(arm_l, x_axis, 0, AIM_SPD)
  Turn(fore_l, x_axis, FWD * pitch, AIM_SPD)
  WaitForTurn(torso, y_axis)
  WaitForTurn(fore_l, x_axis)
end

local function Rest()
  SetSignalMask(SIG_REST)
  Sleep(REST_DELAY)
  busy = false
  Turn(torso, y_axis, 0, AIM_SPD / 2)
  Turn(fore_l, x_axis, 0, AIM_SPD / 2)
end

function script.StartBuilding(heading, pitch)
  Signal(SIG_ARM)
  SetSignalMask(SIG_ARM)
  Signal(SIG_REST)
  busy = true
  building = true
  PointArm(heading or 0, pitch or 0)
  SetUnitValue(COB.INBUILDSTANCE, 1)
  return true
end

function script.StopBuilding()
  building = false
  SetUnitValue(COB.INBUILDSTANCE, 0)
  Signal(SIG_ARM)
  Signal(SIG_REST)
  StartThread(Rest)
  return true
end

-- Il motore chiede da quale pezzo esce il getto di costruzione. Il nome usato da BAR e' QueryNanoPiece;
-- in un test precedente era stato annotato QueryNanopiece: si definiscono entrambi.
local function NanoPiece()
  return nano
end
script.QueryNanoPiece = NanoPiece
script.QueryNanopiece = NanoPiece

function script.AimFromWeapon(n)
  return torso
end

function script.QueryWeapon(n)
  return nano
end

function script.AimWeapon(n, heading, pitch)
  if building then return false end
  Signal(SIG_ARM)
  SetSignalMask(SIG_ARM)
  Signal(SIG_REST)
  busy = true
  PointArm(heading, pitch)
  StartThread(Rest)
  return true
end

-- Rinculo: la spalla scatta indietro e torna.
function script.FireWeapon(n)
  Turn(arm_l, x_axis, -FWD * rad(6), rad(700))
  Sleep(80)
  Turn(arm_l, x_axis, 0, rad(180))
end

function script.Killed(recentDamage, maxHealth)
  return 1
end
