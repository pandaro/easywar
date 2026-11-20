-- ___energy_converter: energy to metal converter, no moving parts and no threads. Canon: C4 ___conv.
-- Conversion is done by the engine (makesmetal + energyupkeep in the unit def), not by this script.
local base = piece('base')               -- unused: fails loudly if the model lacks 'base'

local DEBUG = true                       -- set to false after the first test in game

function script.Create()
  if DEBUG then Spring.Echo('[easywar] ___energy_converter Create unitID=' .. tostring(unitID)) end
end

function script.Killed(recentDamage, maxHealth)
  return 1
end
