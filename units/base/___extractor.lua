-- ___extractor: Metal Extractor, shared base pool (canon C4, ROS-01, ROS-04, ECO-02).
-- Canonical unitdef layout. Converted from units/economy/extractor.lua (legacy name "extractor", kept for old build lists).
-- PLACEHOLDER = value kept from the legacy def, no design meaning; balance starts later.

return {
	___extractor = {
		-- 1. Identity
		name        = "Extractor",
		description = "Extracts metal",
		objectname  = "Extractor.s3o",
		script      = "extractorscript.lua",
		buildpic    = "Extractor.png",
		icontype    = "buildingextractor",
		category    = "TANK SMALL NOTAIR NOTSUB", -- legacy, until categories are decided

		-- 2. Cost (ECO-11 / TST-02)
		energycost = 1000,
		metalcost  = 100,
		buildtime  = 1000,

		-- 3. Body and hitbox
		health                 = 400, -- PLACEHOLDER
		footprintx             = 3,
		footprintz             = 3,
		yardmap                = "ooooooooo",
		collisionvolumetype    = "box",
		collisionvolumescales  = "30.5 100 30.5",
		collisionvolumeoffsets = "0 -35 0",
		sightdistance          = 400, -- PLACEHOLDER

		-- 4. Terrain (ROS-01: land and water; ROS-04: floats, extracts from the metal spot below)
		maxslope = 33,
		floater  = true,

		-- 5. Economy (extraction uses only x/z, so a floating extractor reads the metal map below it)
		extractsmetal = 0.001, -- PLACEHOLDER
		energyupkeep  = 0.6,   -- PLACEHOLDER (no metal while this upkeep cannot be paid)

		-- 6. Abilities and flags
		onoffable         = true,
		activatewhenbuilt = true,
		idleautoheal      = 0, -- autoheal is Delta's trait only (C7)
		explodeas         = "SmallBuildingExplosion",
		selfdestructas    = "SmallBuildingExplosion",
		corpse            = "extractor_dead", -- shared legacy wreck; its metal value is still on the old cost scale

		-- 7. Game-side data
		customparams = {
			pool  = "base",
			role  = "metal",
			canon = "C4",
		},
	},
}