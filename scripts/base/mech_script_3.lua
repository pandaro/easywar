-- Generato da mech_script_3.py per l'unita' mech_script_3. Non modificare a mano: viene riscritto.
-- Animazioni: camminata, mira e sparo con due armi (1 = gatling destra, 2 = cannone sinistro).
-- Pezzi: base, head, arm_l/r, fore_l/r, gatling (destra), cannon (sinistra), leg_l/r, shin_l/r, foot_l/r.
--
-- CONVENZIONE DEL SEGNO: sull'asse x un angolo NEGATIVO porta il pezzo in avanti (FWD = -1).

local base, head = piece('base', 'head')
local arm_l, arm_r = piece('arm_l', 'arm_r')
local fore_l, fore_r = piece('fore_l', 'fore_r')
local gatling, cannon = piece('gatling', 'cannon')
local leg_l, leg_r = piece('leg_l', 'leg_r')
local shin_l, shin_r = piece('shin_l', 'shin_r')
local foot_l, foot_r = piece('foot_l', 'foot_r')

local FWD = -1
local rad = math.rad
local STEP = 220
local SPD = rad(170)
local AIM_SPD = rad(360)
local REST_DELAY = 2500

local SIG_WALK = 1
local SIG_AIM = { 2, 4 }
local SIG_REST = { 8, 16 }

local moving = false
local aiming = { false, false }
local ARM = { arm_r, arm_l }
local FORE = { fore_r, fore_l }
local HAND = { gatling, cannon }

local function X(p, a, spd)
  Turn(p, x_axis, FWD * rad(a), spd or SPD)
end

local function Leg(thigh, shin, foot, a_thigh, a_knee)
  X(thigh, a_thigh)
  X(shin, -a_knee)
  X(foot, a_knee - a_thigh)
end

local function Arms(a_right, a_left)
  if not aiming[1] then X(arm_r, a_right) end
  if not aiming[2] then X(arm_l, a_left) end
end

local function Walk()
  SetSignalMask(SIG_WALK)
  while true do
    Leg(leg_l, shin_l, foot_l, 25, 5)
    Leg(leg_r, shin_r, foot_r, -20, 10)
    Arms(18, -18)
    Sleep(STEP)
    Leg(leg_l, shin_l, foot_l, 5, 0)
    Leg(leg_r, shin_r, foot_r, 10, 40)
    Arms(0, 0)
    Sleep(STEP)
    Leg(leg_r, shin_r, foot_r, 25, 5)
    Leg(leg_l, shin_l, foot_l, -20, 10)
    Arms(-18, 18)
    Sleep(STEP)
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
  Spring.Echo('[easywar] mech_script_3 Create unitID=' .. tostring(unitID))
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

function script.FireWeapon(n)
  Turn(HAND[n], x_axis, -FWD * rad(10), rad(900))
  Sleep(60)
  Turn(HAND[n], x_axis, 0, rad(240))
end

function script.Killed(recentDamage, maxHealth)
  return 1
end
