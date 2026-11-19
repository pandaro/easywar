-- ___mex: Metal Extractor, shared base pool (canon C4, ROS-01, ROS-04, ECO-02).
-- Canonical unitdef layout. Converted from units/economy/extractor.lua (legacy name "extractor").
-- PLACEHOLDER = value kept from the legacy def, no design meaning; balance starts later.

return {
	___mex = {
		-- 1. Identity ---------------------------------------------------------------
		name        = "Metal Extractor",
		description = "Extracts metal",
		objectname  = "Extractor.s3o",
		script      = "extractorscript.lua",
		buildpic    = "Extractor.png",
		icontype    = "buildingextractor",
		category    = "TANK SMALL NOTAIR NOTSUB", -- legacy targeting labels, kept until categories are decided

		-- 2. Cost (ECO-11 / TST-02) -------------------------------------------------
		energycost = 1000,
		metalcost  = 100,
		buildtime  = 1000,

		-- 3. Body and hitbox ---------------------------------------------------------
		health                 = 400, -- PLACEHOLDER
		footprintx             = 3,
		footprintz             = 3,
		yardmap                = "ooooooooo",
		collisionvolumetype    = "box",
		collisionvolumescales  = "30.5 100 30.5",
		collisionvolumeoffsets = "0 -35 0",
		sightdistance          = 400, -- PLACEHOLDER

		-- 4. Terrain (ROS-01, ROS-04: land and water, floats) ------------------------------------------------
		maxslope = 33,
		floater  = true,

		-- 5. Economy -----------------------------------------------------------------
		extractsmetal = 0.001, -- PLACEHOLDER
		energyupkeep  = 0.6,   -- PLACEHOLDER (was energyUse)

		-- 6. Abilities and flags ------------------------------------------------------
		idleautoheal   = 0, -- autoheal is Delta's trait only (C7)
		onoffable         = true,
		activatewhenbuilt = true,
		explodeas      = "SmallBuildingExplosion",
		selfdestructas = "SmallBuildingExplosion",
		corpse         = "extractor_dead", -- legacy feature, kept

		-- 7. Game-side data ------------------------------------------------------------
		customparams = {
			pool  = "base",
			role  = "metal",
			canon = "C4",
		},
	},
}
