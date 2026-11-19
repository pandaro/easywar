-- Generato da lllcom.py per l'unita' lllcom (Commander Lambda). Non modificare a mano: viene riscritto.
-- Animazioni: camminata, costruzione con il cannone dell'avambraccio sinistro, mira con lo stesso braccio
-- se la definizione dell'unita' ha delle armi.
-- Pezzi: base (bacino), torso (colonna, costole, sterno), head, arm_l/r (spalla), fore_l (gomito e cannone),
--        nano (bocca del cannone), fore_r (gomito e avambraccio), hand_r (mano), leg_l/r (anca),
--        shin_l/r (ginocchio), foot_l/r (caviglia). l = sinistra del robot, r = destra.
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
local STEP = 260               -- millisecondi per fase del passo (4 fasi = un passo completo)
local SPD = rad(140)           -- velocita' di rotazione durante il passo (radianti al secondo)
local AIM_SPD = rad(300)       -- velocita' di busto e braccio quando puntano
local REST_DELAY = 2500        -- dopo quanto tempo il braccio torna giu'

local SIG_WALK = 1
local SIG_ARM = 2
local SIG_REST = 4

local moving = false
local busy = false             -- il braccio sinistro sta puntando (costruzione o mira)
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

-- Le braccia oscillano; il sinistro solo se non sta puntando.
local function Arms(a_left, a_right)
  if not busy then X(arm_l, a_left) end
  X(arm_r, a_right)
end

local function Walk()
  SetSignalMask(SIG_WALK)
  while true do
    -- 1: sinistra avanti, destra indietro e appoggiata
    Leg(leg_l, shin_l, foot_l, 22, 5)
    Leg(leg_r, shin_r, foot_r, -18, 10)
    Arms(-14, 14)
    Sleep(STEP)
    -- 2: passaggio, la destra si stacca e si piega
    Leg(leg_l, shin_l, foot_l, 5, 0)
    Leg(leg_r, shin_r, foot_r, 10, 36)
    Arms(0, 0)
    Sleep(STEP)
    -- 3: destra avanti, sinistra indietro e appoggiata
    Leg(leg_r, shin_r, foot_r, 22, 5)
    Leg(leg_l, shin_l, foot_l, -18, 10)
    Arms(14, -14)
    Sleep(STEP)
    -- 4: passaggio, la sinistra si stacca e si piega
    Leg(leg_r, shin_r, foot_r, 5, 0)
    Leg(leg_l, shin_l, foot_l, 10, 36)
    Arms(0, 0)
    Sleep(STEP)
  end
end

local function StandStill()
  for _, p in ipairs({ leg_l, leg_r, shin_l, shin_r, foot_l, foot_r }) do
    Turn(p, x_axis, 0, SPD)
  end
  Arms(0, 0)
end

function script.Create()
  Spring.Echo('[easywar] lllcom Create unitID=' .. tostring(unitID))
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

-- ---- Braccio sinistro: costruzione e mira -----------------------------------------------
-- A riposo il cannone punta in basso. Per puntare, il busto gira verso il bersaglio (heading) e il gomito
-- alza l'avambraccio di 90 gradi piu' l'inclinazione (pitch): la canna resta sull'asse di mira.

local function PointArm(heading, pitch)
  Turn(torso, y_axis, heading, AIM_SPD)
  Turn(arm_l, x_axis, 0, AIM_SPD)
  Turn(fore_l, x_axis, FWD * (rad(90) + pitch), AIM_SPD)
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
  Turn(arm_l, x_axis, -FWD * rad(8), rad(900))
  Sleep(60)
  Turn(arm_l, x_axis, 0, rad(240))
end

function script.Killed(recentDamage, maxHealth)
  return 1
end
