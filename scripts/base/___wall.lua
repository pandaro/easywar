-- ___wall: defensive wall segment, no moving parts and no threads. Canon: C4 ___wall.
local base = piece('base')               -- unused: fails loudly if the model lacks 'base'

local DEBUG = true                       -- set to false after the first test in game

function script.Create()
  if DEBUG then Spring.Echo('[easywar] ___wall Create unitID=' .. tostring(unitID)) end
end

function script.Killed(recentDamage, maxHealth)
  return 1
end
