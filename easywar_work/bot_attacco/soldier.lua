-- Generato da genera_bot.py per l'unita' soldier. Non modificare a mano: viene riscritto.
local base, turret, leg_l, leg_r, shin_l, shin_r = piece('base', 'turret', 'leg_l', 'leg_r', 'shin_l', 'shin_r')

local SIG_WALK = 1

local function Walk()
  Signal(SIG_WALK)
  SetSignalMask(SIG_WALK)
  while true do
    Turn(leg_l, x_axis, math.rad(35), math.rad(160))
    Turn(leg_r, x_axis, math.rad(-35), math.rad(160))
    Turn(shin_l, x_axis, 0, math.rad(160))
    Turn(shin_r, x_axis, math.rad(40), math.rad(160))
    Sleep(220)
    Turn(leg_l, x_axis, math.rad(-35), math.rad(160))
    Turn(leg_r, x_axis, math.rad(35), math.rad(160))
    Turn(shin_l, x_axis, math.rad(40), math.rad(160))
    Turn(shin_r, x_axis, 0, math.rad(160))
    Sleep(220)
  end
end

local function StopWalk()
  Signal(SIG_WALK)
  Turn(leg_l, x_axis, 0, math.rad(120))
  Turn(leg_r, x_axis, 0, math.rad(120))
  Turn(shin_l, x_axis, 0, math.rad(120))
  Turn(shin_r, x_axis, 0, math.rad(120))
end

function script.Create()
  Spin(turret, y_axis, math.rad(120))
end

function script.StartMoving()
  StartThread(Walk)
end

function script.StopMoving()
  StopWalk()
end

function script.Killed(recentDamage, maxHealth)
  return 1
end
