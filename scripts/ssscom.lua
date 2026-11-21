-- ssscom: Sigma Commander. Short waddling walk, build with the left forearm cannon (nano), aim weapons 1 and 2 with the right fist (muzzle). Canon: C6 (CMD-05, CMD-07).
-- Model: one skin cut per triangle (report-modello-ssscom): small joint angles, torso yaw limited, the rest of the yaw on the whole body (base) when standing.
-- Hand-written, not generated: edit this file. Piece offsets below come from claude/richiesta-animazione-ssscom.md.

local base, torso, head = piece("base", "torso", "head")
local arm_l, fore_l, nano = piece("arm_l", "fore_l", "nano")
local arm_r, fore_r, hand_r, muzzle = piece("arm_r", "fore_r", "hand_r", "muzzle")
local leg_l, shin_l, foot_l = piece("leg_l", "shin_l", "foot_l")
local leg_r, shin_r, foot_r = piece("leg_r", "shin_r", "foot_r")

--------------------------------------------------------------------------------
-- Constants (angles in radians, times in whole frames of 33 ms)
--------------------------------------------------------------------------------

local DEBUG = true                  -- first test only: set to false afterwards
local FWD   = -1                    -- x-axis sign that swings a piece forward (seen on gggcomm, same pipeline); 1 if reversed
local rad, abs, atan2, sin = math.rad, math.abs, math.atan2, math.sin

-- Rest directions measured on the model (offsets parent -> child, units of the model):
-- left forearm cannon fore_l -> nano  = (+2.0, -10.2, +8.9): 49 deg below horizontal
-- right forearm       fore_r -> hand_r = (-1.7, -10.3, +3.1): 73 deg below horizontal
local NANO_REST = atan2(10.2, 8.9)
local FIST_REST = atan2(10.3, 3.1)

-- Joint limits from the model report: waist cracks at about 30 deg of torso yaw, hips at about 25 deg
local TORSO_MAX  = rad(20)          -- torso yaw; the rest goes to base (whole body) when standing
local HEAD_MAX   = rad(40)          -- head is a sphere: it can follow the target further
local ARM_MIN, ARM_MAX = 0, rad(150)
local SHOULDER_SHARE = 0.3          -- part of the arm lift on the shoulder, the rest on the elbow (smaller crack per joint)

-- Walk: short legs (hip 12.3 above the feet), small angles
local LEG_LEN  = 12.3
local THIGH_F, THIGH_B = 12, 10     -- degrees forward / back
local KNEE_LIFT = 16                -- degrees, passing leg
local ARM_SWING = 5                 -- degrees, arms stay close to the body
local WADDLE    = 2.5               -- degrees of torso roll toward the stance leg (sign to check in game)
local BOB       = 0.4               -- base drop on double support, model units

local STEP_LEN = LEG_LEN * (sin(rad(THIGH_F)) + sin(rad(THIGH_B)))  -- ground covered per step
local unitSpeed = UnitDefs[unitDefID].speed or 0                    -- elmos per second
local stepFrames = 6
if unitSpeed > 0 then
	-- two phases per step; feet slide when the unit is faster than the legs (clamp)
	stepFrames = math.floor(STEP_LEN / unitSpeed * 30 / 2 + 0.5)
	if stepFrames < 4 then stepFrames = 4 elseif stepFrames > 8 then stepFrames = 8 end
end
local PHASE_MS = stepFrames * 33

local AIM_SPD, BUILD_SPD, REST_SPD = rad(240), rad(180), rad(90)
local RECOIL, RECOIL_SPD = rad(8), rad(600)
local REST_MS = 3003                -- 91 frames without aiming, then back to rest
local IDLE_MIN_FRAMES, IDLE_MAX_FRAMES = 60, 120 -- 2 to 4 s

local SIG_WALK, SIG_AIM1, SIG_AIM2, SIG_BUILD, SIG_REST, SIG_IDLE = 1, 2, 4, 8, 16, 32

--------------------------------------------------------------------------------
-- State
--------------------------------------------------------------------------------

local isMoving = false
local aimHeading = nil                  -- nil when not aiming
local buildHeading = nil                -- nil when not building
local foreAimR = 0                      -- current aim angle of fore_r, for the recoil
local cur = {}                          -- [piece] = last x-axis target set by the walk

--------------------------------------------------------------------------------
-- Helpers
--------------------------------------------------------------------------------

local function Clamp(v, lo, hi)
	if v < lo then return lo elseif v > hi then return hi end
	return v
end

-- Walk turn on x: speed computed so the piece arrives exactly at the end of the phase
local function TX(p, deg)
	local a = FWD * rad(deg)
	local d = abs(a - (cur[p] or 0))
	cur[p] = a
	if d > 0 then Turn(p, x_axis, a, d * 1000 / PHASE_MS) end -- d == 0: leave any running turn alone
end

-- thigh forward by aThigh, knee bent by aKnee, foot kept flat
local function Leg(thigh, shin, foot, aThigh, aKnee)
	TX(thigh, aThigh)
	TX(shin, -aKnee)
	TX(foot, aKnee - aThigh)
end

local function Arms(deg)
	if not buildHeading then TX(arm_l, deg) end
	if not aimHeading then TX(arm_r, -deg) end
end

-- Yaw toward the aim target, else the build target, else straight ahead.
-- Torso up to TORSO_MAX; when standing, the whole body (base) takes the rest; the head follows what is left.
local function ApplyYaw(speed)
	local h = aimHeading or buildHeading or 0
	local t = Clamp(h, -TORSO_MAX, TORSO_MAX)
	local b = isMoving and 0 or (h - t)
	Turn(torso, y_axis, t, speed)
	Turn(base, y_axis, b, speed)
	Turn(head, y_axis, Clamp(h - t - b, -HEAD_MAX, HEAD_MAX), speed)
end

-- Lift an arm chain so the forearm axis (rest angle restAngle below horizontal) points at pitch
local function LiftArm(upper, fore, restAngle, pitch, speed)
	local total = Clamp(restAngle + pitch, ARM_MIN, ARM_MAX)
	local shoulder = total * SHOULDER_SHARE
	Turn(upper, x_axis, FWD * shoulder, speed)
	Turn(fore, x_axis, FWD * (total - shoulder), speed)
	return FWD * (total - shoulder)
end

local function LowerArm(upper, fore, speed)
	Turn(upper, x_axis, 0, speed)
	Turn(fore, x_axis, 0, speed)
	cur[upper] = 0
end

--------------------------------------------------------------------------------
-- Threads
--------------------------------------------------------------------------------

local function Walk()
	Signal(SIG_WALK)
	SetSignalMask(SIG_WALK)
	while true do
		-- 1: left foot forward, double support
		Leg(leg_l, shin_l, foot_l, THIGH_F, 3);  Leg(leg_r, shin_r, foot_r, -THIGH_B, 6)
		Arms(-ARM_SWING); Turn(torso, z_axis, 0, rad(WADDLE) * 1000 / PHASE_MS); Move(base, y_axis, -BOB, BOB * 1000 / PHASE_MS)
		Sleep(PHASE_MS)
		-- 2: right leg passes, stance on the left
		Leg(leg_l, shin_l, foot_l, 4, 0);        Leg(leg_r, shin_r, foot_r, 6, KNEE_LIFT)
		Arms(0); Turn(torso, z_axis, rad(WADDLE), rad(WADDLE) * 1000 / PHASE_MS); Move(base, y_axis, 0, BOB * 1000 / PHASE_MS)
		Sleep(PHASE_MS)
		-- 3: right foot forward, double support
		Leg(leg_r, shin_r, foot_r, THIGH_F, 3);  Leg(leg_l, shin_l, foot_l, -THIGH_B, 6)
		Arms(ARM_SWING); Turn(torso, z_axis, 0, rad(WADDLE) * 1000 / PHASE_MS); Move(base, y_axis, -BOB, BOB * 1000 / PHASE_MS)
		Sleep(PHASE_MS)
		-- 4: left leg passes, stance on the right
		Leg(leg_r, shin_r, foot_r, 4, 0);        Leg(leg_l, shin_l, foot_l, 6, KNEE_LIFT)
		Arms(0); Turn(torso, z_axis, -rad(WADDLE), rad(WADDLE) * 1000 / PHASE_MS); Move(base, y_axis, 0, BOB * 1000 / PHASE_MS)
		Sleep(PHASE_MS)
	end
end

local LEGS = { leg_l, shin_l, foot_l, leg_r, shin_r, foot_r }

local function StandStill()
	for i = 1, #LEGS do
		Turn(LEGS[i], x_axis, 0, REST_SPD)
		cur[LEGS[i]] = 0
	end
	Turn(torso, z_axis, 0, REST_SPD)
	Move(base, y_axis, 0, 2)
	if not buildHeading then Turn(arm_l, x_axis, 0, REST_SPD); cur[arm_l] = 0 end
	if not aimHeading then Turn(arm_r, x_axis, 0, REST_SPD); cur[arm_r] = 0 end
end

-- Idle: the head looks around now and then (one thread per Commander, long sleeps)
local function Idle()
	Signal(SIG_IDLE)
	SetSignalMask(SIG_IDLE)
	while true do
		Sleep(33 * math.random(IDLE_MIN_FRAMES, IDLE_MAX_FRAMES)) -- synced random in unit scripts; unconditional yield
		if not (isMoving or aimHeading or buildHeading) then
			Turn(head, y_axis, rad(math.random(-25, 25)), REST_SPD)
		end
	end
end

local function Rest()
	SetSignalMask(SIG_REST)
	Sleep(REST_MS)
	aimHeading = nil
	LowerArm(arm_r, fore_r, REST_SPD)
	foreAimR = 0
	ApplyYaw(REST_SPD)
end

--------------------------------------------------------------------------------
-- Call-ins
--------------------------------------------------------------------------------

function script.Create()
	Spring.SetUnitNanoPieces(unitID, { nano })
	StartThread(Idle)
	if DEBUG then
		Spring.Echo("[easywar] ssscom Create unitID=" .. unitID .. " speed=" .. unitSpeed .. " phase=" .. PHASE_MS .. "ms")
	end
end

function script.StartMoving()
	isMoving = true
	ApplyYaw(REST_SPD) -- body back on the walking direction, torso keeps up to TORSO_MAX
	StartThread(Walk)
end

function script.StopMoving()
	isMoving = false
	Signal(SIG_WALK)
	StandStill()
	ApplyYaw(REST_SPD) -- standing: the body can face the target again
end

-- Build: the left forearm cannon goes on the line of sight; spray starts once it is there
function script.StartBuilding(heading, pitch)
	Signal(SIG_BUILD)
	SetSignalMask(SIG_BUILD)
	buildHeading = heading
	ApplyYaw(BUILD_SPD)
	LiftArm(arm_l, fore_l, NANO_REST, pitch, BUILD_SPD)
	WaitForTurn(fore_l, x_axis)
	SetUnitValue(COB.INBUILDSTANCE, 1)
end

function script.StopBuilding()
	Signal(SIG_BUILD)
	buildHeading = nil
	SetUnitValue(COB.INBUILDSTANCE, 0)
	LowerArm(arm_l, fore_l, REST_SPD)
	ApplyYaw(REST_SPD)
end

-- Fallback only: SetUnitNanoPieces in Create is what the engine uses. Exact name: capital P (LuaScriptNames.cpp).
function script.QueryNanoPiece() return nano end

-- Weapons 1 and 2 of the unit def: right fist. CMD-09 says the base Commander has none: harmless if removed.
function script.AimFromWeapon(n) return fore_r end
function script.QueryWeapon(n) return muzzle end

function script.AimWeapon(n, heading, pitch)
	local sig = (n == 2) and SIG_AIM2 or SIG_AIM1
	Signal(sig)
	SetSignalMask(sig)
	Signal(SIG_REST)
	aimHeading = heading
	ApplyYaw(AIM_SPD)
	foreAimR = LiftArm(arm_r, fore_r, FIST_REST, pitch, AIM_SPD)
	WaitForTurn(torso, y_axis)
	WaitForTurn(base, y_axis)
	WaitForTurn(fore_r, x_axis)
	StartThread(Rest)
	return true
end

function script.FireWeapon(n)
	-- fist kick: the forearm jumps up a little and comes back
	Turn(fore_r, x_axis, foreAimR + FWD * RECOIL, RECOIL_SPD)
	Sleep(66)
	Turn(fore_r, x_axis, foreAimR, AIM_SPD)
end

function script.Killed(recentDamage, maxHealth)
	return 1
end