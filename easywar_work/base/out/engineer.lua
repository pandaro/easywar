-- Generato da engineer.py per l'unita' engineer. Non modificare a mano: viene riscritto.
local base, torso, shoulder_l, shoulder_r = piece('base', 'torso', 'shoulder_l', 'shoulder_r')
local leg_l, leg_r, shin_l, shin_r, foot_l, foot_r, nano = piece('leg_l', 'leg_r', 'shin_l', 'shin_r', 'foot_l', 'foot_r', 'nano')

-- Verso dei gradi: se il bot cammina con le gambe al contrario, mettere -1.
local FWD = 1
local function a(deg) return math.rad(FWD * deg) end

local SIG_WALK = 1
local SPD = math.rad(420)
local STEP = 150

local function Pose(lt, ls, lf, rt, rs, rf, al, ar, tw)
  Turn(leg_l, x_axis, a(lt), SPD)
  Turn(shin_l, x_axis, a(ls), SPD)
  Turn(foot_l, x_axis, a(lf), SPD)
  Turn(leg_r, x_axis, a(rt), SPD)
  Turn(shin_r, x_axis, a(rs), SPD)
  Turn(foot_r, x_axis, a(rf), SPD)
  Turn(shoulder_l, x_axis, a(al), SPD / 2)
  Turn(shoulder_r, x_axis, a(ar), SPD / 2)
  Turn(torso, y_axis, math.rad(tw), SPD / 4)
  Sleep(STEP)
end

local function Walk()
  Signal(SIG_WALK)
  SetSignalMask(SIG_WALK)
  while true do
    Pose(30, -5, -25,   -25, -40, 35,   -25, 25,   4)
    Pose(5, -5, 0,      10, -60, 50,    0, 0,      0)
    Pose(-25, -40, 35,  30, -5, -25,    25, -25,  -4)
    Pose(10, -60, 50,   5, -5, 0,       0, 0,      0)
  end
end

local function StopWalk()
  Signal(SIG_WALK)
  local s = math.rad(200)
  Turn(leg_l, x_axis, 0, s)
  Turn(shin_l, x_axis, 0, s)
  Turn(foot_l, x_axis, 0, s)
  Turn(leg_r, x_axis, 0, s)
  Turn(shin_r, x_axis, 0, s)
  Turn(foot_r, x_axis, 0, s)
  Turn(shoulder_l, x_axis, 0, s)
  Turn(shoulder_r, x_axis, 0, s)
  Turn(torso, y_axis, 0, s)
end

function script.Create()
  Spring.Echo('[easywar] engineer Create unitID=' .. tostring(unitID))
end

function script.StartMoving()
  StartThread(Walk)
end

function script.StopMoving()
  StopWalk()
end

function script.StartBuilding(heading, pitch)
  Spring.Echo('[easywar] engineer StartBuilding heading=' .. tostring(heading))
  SetUnitValue(COB.INBUILDSTANCE, 1)
  Turn(torso, y_axis, heading, math.rad(240))
  Turn(shoulder_r, x_axis, a(80), math.rad(200))
end

function script.StopBuilding()
  SetUnitValue(COB.INBUILDSTANCE, 0)
  Turn(torso, y_axis, 0, math.rad(120))
  Turn(shoulder_r, x_axis, 0, math.rad(120))
end

-- Nome documentato: QueryNanopiece (p minuscola).
function script.QueryNanopiece()
  return nano
end

function script.Killed(recentDamage, maxHealth)
  return 1
end
