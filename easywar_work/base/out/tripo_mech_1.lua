-- Generato da tripo_mech_1.py per l'unita' tripo_mech_1. Non modificare a mano: viene riscritto.
-- Animazioni: camminata (gambe e braccia), mira e sparo con il cannone del braccio destro (arma 1).
-- Pezzi: base (busto e bacino), head, arm_r/l (spalla con spallaccio), fore_r/l (gomito con avambraccio e mano),
--        muzzle_r (bocca del cannone), leg_r/l (anca), shin_r/l (ginocchio), foot_r (caviglia; la gamba sinistra
--        e' un piolo e non ha piede separato).
--
-- CONVENZIONE DEL SEGNO (dedotta dal test dell'engineer, dove un angolo positivo sull'asse x
-- ha portato il braccio indietro): sull'asse x un angolo NEGATIVO porta il pezzo in avanti.
-- Se nel gioco gambe e braccia vanno al contrario, basta mettere FWD = 1.

local base, head = piece('base', 'head')
local arm_l, arm_r = piece('arm_l', 'arm_r')
local fore_l, fore_r = piece('fore_l', 'fore_r')
local muzzle_r = piece('muzzle_r')
local leg_l, leg_r = piece('leg_l', 'leg_r')
local shin_l, shin_r = piece('shin_l', 'shin_r')
local foot_r = piece('foot_r')

local FWD = -1                 -- segno di "avanti" sull'asse x
local rad = math.rad
local STEP = 240               -- millisecondi per fase del passo (4 fasi = un passo completo)
local SPD = rad(150)           -- velocita' di rotazione durante il passo (radianti al secondo)
local AIM_SPD = rad(360)       -- velocita' del braccio quando mira
local REST_DELAY = 2500        -- dopo quanto tempo senza sparare il braccio torna giu'

local SIG_WALK = 1
local SIG_AIM = 2
local SIG_REST = 4

local moving = false
local aiming = false

-- Gira un pezzo sull'asse x: a > 0 = in avanti (il segno lo mette FWD).
local function X(p, a, spd)
  Turn(p, x_axis, FWD * rad(a), spd or SPD)
end

-- Una posa delle gambe: coscia, ginocchio (positivo = piegato) e, se c'e', piede tenuto piatto.
local function Leg(thigh, shin, foot, a_thigh, a_knee)
  X(thigh, a_thigh)
  X(shin, -a_knee)
  if foot then X(foot, a_knee - a_thigh) end
end

-- Il braccio del cannone oscilla solo se non sta mirando; quello con l'uncino oscilla sempre.
local function Arms(a_right, a_left)
  if not aiming then X(arm_r, a_right) end
  X(arm_l, a_left)
end

local function Walk()
  SetSignalMask(SIG_WALK)
  while true do
    -- 1: sinistra avanti, destra indietro e appoggiata
    Leg(leg_l, shin_l, nil, 20, 5)
    Leg(leg_r, shin_r, foot_r, -16, 8)
    Arms(12, -12)
    Sleep(STEP)
    -- 2: passaggio, la destra si stacca e si piega
    Leg(leg_l, shin_l, nil, 4, 0)
    Leg(leg_r, shin_r, foot_r, 8, 30)
    Arms(0, 0)
    Sleep(STEP)
    -- 3: destra avanti, sinistra indietro e appoggiata
    Leg(leg_r, shin_r, foot_r, 20, 5)
    Leg(leg_l, shin_l, nil, -16, 8)
    Arms(-12, 12)
    Sleep(STEP)
    -- 4: passaggio, la sinistra si stacca e si piega
    Leg(leg_r, shin_r, foot_r, 4, 0)
    Leg(leg_l, shin_l, nil, 8, 30)
    Arms(0, 0)
    Sleep(STEP)
  end
end

local function StandStill()
  for _, p in ipairs({ leg_l, leg_r, shin_l, shin_r, foot_r }) do
    Turn(p, x_axis, 0, SPD)
  end
  Arms(0, 0)
end

function script.Create()
  Spring.Echo('[easywar] tripo_mech_1 Create unitID=' .. tostring(unitID))
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

-- ---- Arma 1: cannone del braccio destro ---------------------------------------------
-- A riposo la canna punta in basso. Per mirare la spalla gira verso il bersaglio (heading) e il gomito
-- alza l'avambraccio di 90 gradi piu' l'inclinazione (pitch): la canna resta sull'asse di mira.

local function Rest()
  SetSignalMask(SIG_REST)
  Sleep(REST_DELAY)
  aiming = false
  Turn(arm_r, y_axis, 0, AIM_SPD / 2)
  Turn(arm_r, x_axis, 0, AIM_SPD / 2)
  Turn(fore_r, x_axis, 0, AIM_SPD / 2)
end

function script.AimFromWeapon(n)
  return fore_r
end

function script.QueryWeapon(n)
  return muzzle_r
end

function script.AimWeapon(n, heading, pitch)
  Signal(SIG_AIM)
  SetSignalMask(SIG_AIM)
  Signal(SIG_REST)
  aiming = true
  Turn(arm_r, x_axis, 0, AIM_SPD)
  Turn(arm_r, y_axis, heading, AIM_SPD)
  Turn(fore_r, x_axis, FWD * (rad(90) + pitch), AIM_SPD)
  WaitForTurn(arm_r, y_axis)
  WaitForTurn(fore_r, x_axis)
  StartThread(Rest)
  return true
end

-- Rinculo: la spalla scatta indietro e torna.
function script.FireWeapon(n)
  Turn(arm_r, x_axis, -FWD * rad(8), rad(900))
  Sleep(60)
  Turn(arm_r, x_axis, 0, rad(240))
end

function script.Killed(recentDamage, maxHealth)
  return 1
end
