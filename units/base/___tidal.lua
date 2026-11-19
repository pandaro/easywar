-- ___tidal: Tidal Generator, shared base pool (canon C4, ROS-01, ROS-03, ECO-05).
-- Canonical unitdef layout. Converted from units/economy/tidalgenerator.lua (legacy name "tidalgenerator").
-- PLACEHOLDER = value kept from the legacy def, no design meaning; balance starts later.

return {
	___tidal = {
		-- 1. Identity ---------------------------------------------------------------
		name        = "Tidal Generator",
		description = "Produces energy from tides. Water only",
		objectname  = "Tidal Generator.s3o",
		script      = "tidalgeneratorscript.lua",
		buildpic    = "Tidal Generator.png",
		icontype    = "buildingenergy",
		category    = "TANK SMALL NOTAIR NOTSUB", -- legacy targeting labels, kept until categories are decided

		-- 2. Cost (ECO-11 / TST-02) -------------------------------------------------
		energycost = 1000,
		metalcost  = 100,
		buildtime  = 1000,

		-- 3. Body and hitbox ---------------------------------------------------------
		health                 = 300, -- PLACEHOLDER
		footprintx             = 3,
		footprintz             = 3,
		yardmap                = "ooooooooo",
		collisionvolumetype    = "box",
		collisionvolumescales  = "50 30 43",
		collisionvolumeoffsets = "0 0 0",
		sightdistance          = 400, -- PLACEHOLDER

		-- 4. Terrain (ROS-01: water only, floats) ------------------------------------------------
		maxslope = 33,
		minwaterdepth = 5,
		floater       = true,

		-- 5. Economy -----------------------------------------------------------------
		tidalgenerator = 0.1, -- PLACEHOLDER

		-- 6. Abilities and flags ------------------------------------------------------
		idleautoheal   = 0, -- autoheal is Delta's trait only (C7)
		explodeas      = "MediumBuildingExplosion",
		selfdestructas = "MediumBuildingExplosion",
		corpse         = "tidalgenerator_dead", -- legacy feature, kept

		-- 7. Game-side data ------------------------------------------------------------
		customparams = {
			pool  = "base",
			role  = "energy",
			canon = "C4",
		},
	},
}
