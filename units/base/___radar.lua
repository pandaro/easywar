-- ___radar: Radar Tower, shared base pool (canon C4, ROS-01).
-- Canonical unitdef layout. Converted from units/economy/radartower.lua (legacy name "radartower").
-- PLACEHOLDER = value kept from the legacy def, no design meaning; balance starts later.

return {
	___radar = {
		-- 1. Identity ---------------------------------------------------------------
		name        = "Radar Tower",
		description = "Long range early warning",
		objectname  = "Radar Tower.s3o",
		script      = "radartowerscript.lua",
		buildpic    = "Radar Tower.png",
		icontype    = "buildingradar",
		category    = "TANK SMALL NOTAIR NOTSUB", -- legacy targeting labels, kept until categories are decided

		-- 2. Cost (ECO-11 / TST-02) -------------------------------------------------
		energycost = 1000,
		metalcost  = 100,
		buildtime  = 1000,

		-- 3. Body and hitbox ---------------------------------------------------------
		health                 = 400, -- PLACEHOLDER
		footprintx             = 3,
		footprintz             = 3,
		collisionvolumetype    = "box",
		collisionvolumescales  = "25 85 25",
		collisionvolumeoffsets = "0 25 0",
		sightdistance          = 600, -- PLACEHOLDER
		radardistance          = 2000, -- PLACEHOLDER
		radaremitheight        = 60,   -- was radarHeight

		-- 4. Terrain (ROS-01: land and water, floats) ------------------------------------------------
		maxslope = 33,
		floater  = true,

		-- 5. Economy -----------------------------------------------------------------
		energyupkeep = 5, -- PLACEHOLDER (was energyUse)

		-- 6. Abilities and flags ------------------------------------------------------
		idleautoheal   = 0, -- autoheal is Delta's trait only (C7)
		onoffable         = true,
		activatewhenbuilt = true,
		explodeas      = "MediumBuildingExplosion",
		selfdestructas = "MediumBuildingExplosion",

		-- 7. Game-side data ------------------------------------------------------------
		customparams = {
			pool  = "base",
			role  = "radar",
			canon = "C4",
		},
	},
}
