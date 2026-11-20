-- ___cam: perimeter camera, the head spins 360 degrees non-stop. Canon: C4 ___cam, ROS-10 (LOS only).
-- Purely cosmetic: engine line of sight is circular and does not depend on where the head points.
local base, head = piece('base', 'head')

local DEBUG = true                       -- set to false after the first test in game

local spGetUnitIsStunned = Spring.GetUnitIsStunned

local FRAME_MS = 33                      -- Sleep rounds down to whole frames: always use multiples
local CHECK_FRAMES = 30                  -- 1 s between state checks
local SPIN_SPEED = math.rad(30)          -- rad/s: one turn every 12 s
local SPIN_ACCEL = SPIN_SPEED / 30       -- speed change per frame: about 1 s to start or stop

-- The engine animates the spin by itself; this thread only starts and stops it.
-- It wakes once per second per camera and does no per-frame work.
local function Watch()
  local spinning = false
  while true do
    -- First value: stunned (EMP/paralysis), transported or still being built.
    local disabled = spGetUnitIsStunned(unitID)
    if disabled and spinning then
      StopSpin(head, y_axis, SPIN_ACCEL)
      spinning = false
    elseif not disabled and not spinning then
      if DEBUG then
        Spring.Echo('[easywar] ___cam spin start unitID=' .. tostring(unitID)
          .. ': positive speed on y (note: clockwise or counter-clockwise seen from above?)')
      end
      Spin(head, y_axis, SPIN_SPEED, SPIN_ACCEL)
      spinning = true
    end
    Sleep(CHECK_FRAMES * FRAME_MS)       -- unconditional yield: the loop can never spin
  end
end

function script.Create()
  if DEBUG then Spring.Echo('[easywar] ___cam Create unitID=' .. tostring(unitID)) end
  StartThread(Watch)
end

function script.Killed(recentDamage, maxHealth)
  return 1
end
