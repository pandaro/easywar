-- ___con: Constructor, shared base pool amphibious land vehicle (canon C4, ROS-02, ROS-03, ROS-12).
-- Canonical unitdef layout. Converted from units/base/constructor.lua (test unit "constructor", kept).
-- PLACEHOLDER = value kept from the legacy def, no design meaning; balance starts later.

return {
	___con = {
		-- 1. Identity
		name        = "Constructor",
		description = "Builds the support structures",
		objectname  = "base/constructor.s3o",
		script      = "base/constructor.lua",
		buildpic    = "Constructor.png",
		icontype    = "hoverconstructor", -- PLACEHOLDER: "constructor" is not in icontypes.lua
		category    = "TANK SMALL NOTAIR NOTSUB", -- legacy, until categories are decided

		-- 2. Cost (ECO-11 / TST-02)
		energycost = 1000,
		metalcost  = 100,
		buildtime  = 1000,

		-- 3. Body and hitbox
		health                 = 500, -- PLACEHOLDER
		footprintx             = 3,   -- = movedef Tank_Amph_3x3
		footprintz             = 3,
		collisionvolumetype    = "box",
		collisionvolumescales  = "26 20.5 34.5",
		collisionvolumeoffsets = "0 0 -1.5",
		sightdistance          = 500, -- PLACEHOLDER

		-- 4. Movement (ROS-12: amphibious land vehicle; slope and water depth come from the movedef)
		movementclass = "Tank_Amph_3x3", -- test class name, final name from the movedef agent
		speed         = 48,   -- PLACEHOLDER (old maxVelocity 1.6 elmo/frame)
		maxacc        = 0.35, -- PLACEHOLDER
		maxdec        = 0.1,  -- PLACEHOLDER (old brakeRate)
		turnrate      = 1000, -- PLACEHOLDER

		-- 6. Abilities and flags
		builder        = true,
		workertime     = 5,    -- PLACEHOLDER (build power)
		repairspeed    = 3.3,  -- PLACEHOLDER
		reclaimspeed   = 5,    -- PLACEHOLDER
		builddistance  = 120,  -- PLACEHOLDER
		terraformspeed = 9001, -- common flattening only (C7 Theta)
		canmove        = true,
		idleautoheal   = 0, -- autoheal is Delta's trait only (C7)
		nochasecategory = "AIR",
		explodeas      = "MediumExplosion",
		selfdestructas = "MediumExplosion",
		corpse         = "constructor_dead",

		-- ROS-02 / ROS-03: the 11 base units built by ___con (missing defs are dropped by the engine with a warning)
		buildoptions = {
			"___wind",
			"___tidal",
			"___estore",
			"___mstore",
			"___conv",
			"___cam",
			"___mt",
			"___mat",
			"___sublt",
			"___geo",
			"___share",
		},

		-- 7. Game-side data
		customparams = {
			pool  = "base",
			role  = "builder",
			canon = "C4",
		},

		-- Effects called by the unit script (nano spray)
		sfxtypes = {
			explosiongenerators = {
				"custom:buildermuzzleflash",
			},
		},
	},
}