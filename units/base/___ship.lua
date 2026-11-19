-- ___ship: light multipurpose ship, shared base pool (canon C4, ROS-05).
-- Canonical unitdef layout. Converted from units/base/riptide.lua (test unit "riptide", kept).
-- PLACEHOLDER = value kept from the old def, no design meaning; balance starts later.

return {
	___ship = {
		-- 1. Identity
		name        = "Ship",
		description = "Light multipurpose ship",
		objectname  = "base/Riptide.s3o",
		script      = "base/riptidescript.lua",
		buildpic    = "Riptide.png",
		icontype    = "shipraider",
		category    = "TANK SHIP SMALL NOTAIR NOTSUB", -- legacy, until categories are decided

		-- 2. Cost (ECO-11 / TST-02)
		energycost = 1000,
		metalcost  = 100,
		buildtime  = 1000,

		-- 3. Body and hitbox
		health                 = 400, -- PLACEHOLDER
		footprintx             = 2,   -- = movedef "Small Ship"
		footprintz             = 2,
		collisionvolumetype    = "ellipsoid",
		collisionvolumescales  = "32 28 58",
		collisionvolumeoffsets = "0 1 0",
		sightdistance          = 560, -- PLACEHOLDER
		sonardistance          = 560, -- PLACEHOLDER

		-- 4. Movement (water depth comes from the movedef)
		movementclass = "Small Ship",
		speed         = 88,    -- PLACEHOLDER
		maxacc        = 0.09,  -- PLACEHOLDER
		maxdec        = 0.108, -- PLACEHOLDER (old brakeRate)
		turnrate      = 900,   -- PLACEHOLDER
		turninplace   = false,

		-- 6. Abilities and flags
		canmove           = true,
		activatewhenbuilt = true,
		idleautoheal      = 0, -- autoheal is Delta's trait only (C7)
		nochasecategory   = "AIR",
		explodeas         = "SmallExplosion",
		selfdestructas    = "SmallExplosion",
		corpse            = "riptide_dead",
		-- C4 asks for a weak anti-air too: not added (design decision, open)
		weapons = {
			{ name = "RiptideAmphMissle", onlytargetcategory = "TANK" },
		},

		-- 7. Game-side data
		customparams = {
			pool  = "base",
			role  = "ship",
			canon = "C4",
		},
	},
}