-- ___fighter: air-to-air fighter, shared base pool (canon C4, ROS-05).
-- Canonical unitdef layout. Converted from units/base/___hawk.lua (kept).
-- PLACEHOLDER = value kept from the old def, no design meaning; balance starts later.

return {
	___fighter = {
		-- 1. Identity
		name        = "Fighter",
		description = "Fast anti-air fighter",
		objectname  = "base/Hawk.s3o",
		script      = "base/hawkscript.lua",
		buildpic    = "Hawk.png",
		icontype    = "airantiair",
		category    = "AIR SMALL NOTSUB", -- legacy, until categories are decided

		-- 2. Cost (ECO-11 / TST-02)
		energycost = 1000,
		metalcost  = 100,
		buildtime  = 1000,

		-- 3. Body and hitbox
		health                 = 300, -- PLACEHOLDER
		footprintx             = 2,
		footprintz             = 2,
		collisionvolumetype    = "box",
		collisionvolumescales  = "10 9.5 25",
		collisionvolumeoffsets = "0 0 0",
		sightdistance          = 560, -- PLACEHOLDER

		-- 4. Movement: aircraft, no movementclass.
		-- floater: without it an aircraft cannot be placed over water (GameHelper.cpp, CheckTerrainConstraints)
		floater           = true,
		canfly            = true,
		speed             = 164,   -- PLACEHOLDER
		maxacc            = 0.4,   -- PLACEHOLDER
		maxdec            = 0.1,   -- PLACEHOLDER (old brakeRate)
		turnrate          = 2250,  -- PLACEHOLDER
		cruisealtitude    = 325,   -- PLACEHOLDER (old cruiseAlt)
		hoverattack       = false,
		canloopbackattack = true,
		maxrudder         = 0.008, -- PLACEHOLDER
		maxelevator       = 0.02,  -- PLACEHOLDER
		turnradius        = 20,    -- PLACEHOLDER

		-- 6. Abilities and flags
		canmove           = true,
		idleautoheal      = 0, -- autoheal is Delta's trait only (C7)
		badtargetcategory = "TANK",
		nochasecategory   = "TANK",
		explodeas         = "SmallAirExplosion",
		selfdestructas    = "SmallAirExplosion",
		corpse            = "hawk_dead",
		weapons = {
			{ name = "AALaserblatser", onlytargetcategory = "AIR", maindir = "0 0 1", maxangledif = 55 },
		},

		-- 7. Game-side data
		customparams = {
			pool  = "base",
			role  = "fighter",
			canon = "C4",
		},
	},
}