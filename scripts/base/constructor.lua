-- Generato da constructor.py per l'unita' constructor. Non modificare a mano: viene riscritto.
local base, arm_base, arm, nano = piece('base', 'arm_base', 'arm', 'nano')

function script.Create()
  Spring.Echo('[easywar] constructor Create unitID=' .. tostring(unitID))
end

function script.StartBuilding(heading, pitch)
  Spring.Echo('[easywar] constructor StartBuilding heading=' .. tostring(heading) .. ' pitch=' .. tostring(pitch))
  SetUnitValue(COB.INBUILDSTANCE, 1)
  Turn(arm_base, y_axis, heading, math.rad(180))
  Turn(arm, x_axis, math.rad(-35), math.rad(90))
end

function script.StopBuilding()
  Spring.Echo('[easywar] constructor StopBuilding')
  SetUnitValue(COB.INBUILDSTANCE, 0)
  Turn(arm_base, y_axis, 0, math.rad(90))
  Turn(arm, x_axis, 0, math.rad(90))
end

-- Nome documentato: QueryNanopiece (p minuscola). Prima era scritto QueryNanoPiece e il motore non lo vedeva.
function script.QueryNanopiece()
  return nano
end

function script.Killed(recentDamage, maxHealth)
  return 1
end
