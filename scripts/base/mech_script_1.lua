-- Generato da mech_script_1.py per l'unita' mech_script_1. Non modificare a mano: viene riscritto.
-- Animazioni: camminata (gambe e braccia), mira e sparo con due armi (arma 1 = mano destra, arma 2 = mano sinistra).
-- Pezzi: base (torso), head, arm_l/r (spalla), fore_l/r (gomito), hand_l/r (pugno),
--        leg_l/r (anca), shin_l/r (ginocchio), foot_l/r (caviglia).
--
-- CONVENZIONE DEL SEGNO (dedotta dal test dell'engineer, dove un angolo positivo sull'asse x
-- ha portato il braccio indietro): sull'asse x un angolo NEGATIVO porta il pezzo in avanti.
-- Se nel gioco gambe e braccia vanno al contrario, basta mettere FWD = 1.

local base, head = piece('base', 'head')
local arm_l, arm_r = piece('arm_l', 'arm_r')
local fore_l, fore_r = piece('fore_l', 'fore_r')
local hand_l, hand_r = piece('hand_l', 'hand_r')
local leg_l, leg_r = piece('leg_l', 'leg_r')
local shin_l, shin_r = piece('shin_l', 'shin_r')
local foot_l, foot_r = piece('foot_l', 'foot_r')

local FWD = -1                 -- segno di "avanti" sull'asse x
local rad = math.rad
local STEP = 220               -- millisecondi per fase del passo (4 fasi = un passo completo)
local SPD = rad(170)           -- velocita' di rotazione durante il passo (radianti al secondo)
local AIM_SPD = rad(360)       -- velocita' del braccio quando mira
local REST_DELAY = 2500        -- dopo quanto tempo senza sparare le braccia tornano giu'

local SIG_WALK = 1
local SIG_AIM = { 2, 4 }       -- un segnale per arma
local SIG_REST = { 8, 16 }

local moving = false
local aiming = { false, false }    -- [1] = destra, [2] = sinistra
local ARM = { arm_r, arm_l }
local FORE = { fore_r, fore_l }
local HAND = { hand_r, hand_l }

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

-- Le braccia oscillano solo se quella mano non sta mirando.
local function Arms(a_right, a_left)
  if not aiming[1] then X(arm_r, a_right) end
  if not aiming[2] then X(arm_l, a_left) end
end

local function Walk()
  SetSignalMask(SIG_WALK)
  while true do
    -- 1: sinistra avanti, destra indietro e appoggiata
    Leg(leg_l, shin_l, foot_l, 25, 5)
    Leg(leg_r, shin_r, foot_r, -20, 10)
    Arms(18, -18)
    Sleep(STEP)
    -- 2: passaggio, la destra si stacca e si piega
    Leg(leg_l, shin_l, foot_l, 5, 0)
    Leg(leg_r, shin_r, foot_r, 10, 40)
    Arms(0, 0)
    Sleep(STEP)
    -- 3: destra avanti, sinistra indietro e appoggiata
    Leg(leg_r, shin_r, foot_r, 25, 5)
    Leg(leg_l, shin_l, foot_l, -20, 10)
    Arms(-18, 18)
    Sleep(STEP)
    -- 4: passaggio, la sinistra si stacca e si piega
    Leg(leg_r, shin_r, foot_r, 5, 0)
    Leg(leg_l, shin_l, foot_l, 10, 40)
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
  Spring.Echo('[easywar] mech_script_1 Create unitID=' .. tostring(unitID))
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

-- ---- Armi: 1 = mano destra, 2 = mano sinistra -----------------------------------
-- A riposo l'arma punta in basso. Per mirare la spalla gira verso il bersaglio (heading) e il gomito
-- alza l'avambraccio di 90 gradi piu' l'inclinazione (pitch): la canna resta sull'asse di mira.
-- Funziona solo se la definizione dell'unita' ha due armi.

local function Rest(n)
  SetSignalMask(SIG_REST[n])
  Sleep(REST_DELAY)
  aiming[n] = false
  Turn(ARM[n], y_axis, 0, AIM_SPD / 2)
  Turn(ARM[n], x_axis, 0, AIM_SPD / 2)
  Turn(FORE[n], x_axis, 0, AIM_SPD / 2)
end

function script.AimFromWeapon(n)
  return FORE[n]
end

function script.QueryWeapon(n)
  return HAND[n]
end

-- La spalla (con lo spallaccio) gira solo verso il bersaglio; e' il gomito che alza l'avambraccio e l'arma.
function script.AimWeapon(n, heading, pitch)
  Signal(SIG_AIM[n])
  SetSignalMask(SIG_AIM[n])
  Signal(SIG_REST[n])
  aiming[n] = true
  Turn(ARM[n], x_axis, 0, AIM_SPD)
  Turn(ARM[n], y_axis, heading, AIM_SPD)
  Turn(FORE[n], x_axis, FWD * (rad(90) + pitch), AIM_SPD)
  WaitForTurn(ARM[n], y_axis)
  WaitForTurn(FORE[n], x_axis)
  StartThread(Rest, n)
  return true
end

-- Rinculo: la mano con l'arma scatta indietro e torna.
function script.FireWeapon(n)
  Turn(HAND[n], x_axis, -FWD * rad(10), rad(900))
  Sleep(60)
  Turn(HAND[n], x_axis, 0, rad(240))
end

function script.Killed(recentDamage, maxHealth)
  return 1
end
