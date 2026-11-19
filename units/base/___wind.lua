-- ___wind: Wind Turbine, shared base pool (canon C4, ROS-01, ROS-03, ECO-05).
-- Canonical unitdef layout. Converted from units/economy/wind turbine.lua (legacy name "windturbine").
-- PLACEHOLDER = value kept from the legacy def, no design meaning; balance starts later.

return {
	___wind = {
		-- 1. Identity ---------------------------------------------------------------
		name        = "Wind Turbine",
		description = "Produces energy from wind. Land only",
		objectname  = "Wind Turbine.s3o",
		script      = "windturbinescript.lua",
		buildpic    = "Windturbine.png",
		icontype    = "buildingenergy",
		category    = "TANK SMALL NOTAIR NOTSUB", -- legacy targeting labels, kept until categories are decided

		-- 2. Cost (ECO-11 / TST-02) -------------------------------------------------
		energycost = 1000,
		metalcost  = 100,
		buildtime  = 1000,

		-- 3. Body and hitbox ---------------------------------------------------------
		health                 = 225, -- PLACEHOLDER
		footprintx             = 3,
		footprintz             = 3,
		yardmap                = "ooooooooo",
		collisionvolumetype    = "box",
		collisionvolumescales  = "20 68 20",
		collisionvolumeoffsets = "0 20 0",
		sightdistance          = 400, -- PLACEHOLDER

		-- 4. Terrain (ROS-01: land only) ------------------------------------------------
		maxslope = 50,
		maxwaterdepth = 0, -- was absent (default allowed any depth)

		-- 5. Economy -----------------------------------------------------------------
		windgenerator = 5, -- PLACEHOLDER

		-- 6. Abilities and flags ------------------------------------------------------
		idleautoheal   = 0, -- autoheal is Delta's trait only (C7)
		explodeas      = "MediumBuildingExplosion",
		selfdestructas = "MediumBuildingExplosion",
		corpse         = "windturbine_dead", -- legacy feature, kept

		-- 7. Game-side data ------------------------------------------------------------
		customparams = {
			pool  = "base",
			role  = "energy",
			canon = "C4",
			energymultiplier = 0.1, -- PLACEHOLDER, kept from legacy (read by game code)
		},
	},
}
