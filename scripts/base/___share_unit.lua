-- ___share_unit: resource sharing shrine, the floating orb tumbles in random directions and bobs.
-- Canon: C4 ___share, ROS-11 (hypothesis). Purely cosmetic. The pedestal (base) never moves.
local base, orb = piece('base', 'orb')

local DEBUG = true                       -- set to false after the first test in game

local spGetUnitIsStunned = Spring.GetUnitIsStunned
local random = math.random               -- synced RNG in synced Lua (seen in engine source)
local rad = math.rad

local FRAME_MS = 33                      -- Sleep rounds down to whole frames: always use multiples
local CHECK_FRAMES = 30                  -- 1 s between checks while built, stunned or transported
local TICK_FRAMES = 60                   -- one wake every 2 s drives both bob and spin
local TICK_MS = TICK_FRAMES * FRAME_MS

local BOB_HEIGHT = 1                     -- elmos above rest; never lower, keeps the 1 elmo gap
local BOB_SPEED = BOB_HEIGHT * 30 / TICK_FRAMES            -- elmos/s: each leg lasts one tick

local SPIN_MIN_DEG, SPIN_MAX_DEG = 200,600                   -- random top speed, degrees/s
local HOLD_MIN_TICKS, HOLD_MAX_TICKS = 2, 4                -- 2-6 s at top speed after the ramp
local AXES = { x_axis, y_axis, z_axis }

-- Spin cycle: ACCEL (1 tick) -> HOLD (random ticks) -> DECEL (1 tick, down to zero)
-- -> REST (1 tick at zero) -> new random axis and sign.
-- Accel/decel are speed change per frame, sized so each ramp takes exactly one tick.
local ACCEL, HOLD, DECEL = 1, 2, 3

local function Animate()
  local active = false
  local up = true
  local phase, ticksLeft = ACCEL, 0
  local axis, speed = y_axis, 0
  while true do
    -- First value: stunned (EMP/paralysis), transported or still being built.
    if spGetUnitIsStunned(unitID) then
      if active then
        StopSpin(orb, axis, math.abs(speed) / 15)   -- quick stop, about 0.5 s
        Move(orb, y_axis, 0, BOB_SPEED)             -- settle back to rest
        active, up, phase = false, true, ACCEL
      end
      Sleep(CHECK_FRAMES * FRAME_MS)
    else
      if not active and DEBUG then
        Spring.Echo('[easywar] ___share_unit orb start unitID=' .. tostring(unitID))
      end
      active = true

      -- Bob: one leg per tick.
      Move(orb, y_axis, up and BOB_HEIGHT or 0, BOB_SPEED)
      up = not up

      -- Spin cycle.
      if phase == ACCEL then
        axis = AXES[random(3)]
        speed = rad(random(SPIN_MIN_DEG, SPIN_MAX_DEG)) * (random(2) == 1 and 1 or -1)
        Spin(orb, axis, speed, math.abs(speed) / TICK_FRAMES)
        phase, ticksLeft = HOLD, random(HOLD_MIN_TICKS, HOLD_MAX_TICKS)
      elseif phase == HOLD then
        ticksLeft = ticksLeft - 1
        if ticksLeft <= 0 then
          StopSpin(orb, axis, math.abs(speed) / TICK_FRAMES)
          phase = DECEL
        end
      else                               -- DECEL done: orb at zero speed, rest one tick
        phase = ACCEL
      end

      Sleep(TICK_MS)                     -- unconditional yield, matches move and ramp times
    end
  end
end

function script.Create()
  if DEBUG then Spring.Echo('[easywar] ___share_unit Create unitID=' .. tostring(unitID)) end
  StartThread(Animate)
end

function script.Killed(recentDamage, maxHealth)
  return 1
end
