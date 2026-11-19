-- ___estore: Energy Storage, shared base pool (canon C4, ROS-01, ECO-06).
-- Canonical unitdef layout. Converted from units/economy/storage.lua (legacy name "storage").
-- PLACEHOLDER = value kept from the legacy def, no design meaning; balance starts later.

return {
	___estore = {
		-- 1. Identity ---------------------------------------------------------------
		name        = "Energy Storage",
		description = "Stores energy",
		objectname  = "Storage.s3o",
		script      = "Storagescript.lua",
		buildpic    = "Storage.png",
		icontype    = "buildingstorage",
		category    = "TANK SMALL NOTAIR NOTSUB", -- legacy targeting labels, kept until categories are decided

		-- 2. Cost (ECO-11 / TST-02) -------------------------------------------------
		energycost = 1000,
		metalcost  = 100,
		buildtime  = 1000,

		-- 3. Body and hitbox ---------------------------------------------------------
		health                 = 500, -- PLACEHOLDER
		footprintx             = 3,
		footprintz             = 3,
		yardmap                = "ooooooooo",
		collisionvolumetype    = "box",
		collisionvolumescales  = "25 42 25",
		collisionvolumeoffsets = "0 15 0",
		sightdistance          = 600, -- PLACEHOLDER

		-- 4. Terrain (ROS-01: land and water, floats) ------------------------------------------------
		maxslope = 33,
		floater  = true,

		-- 5. Economy -----------------------------------------------------------------
		energystorage = 500, -- PLACEHOLDER (legacy storage held 500 of both)

		-- 6. Abilities and flags ------------------------------------------------------
		idleautoheal   = 0, -- autoheal is Delta's trait only (C7)
		explodeas      = "SmallBuildingExplosion",
		selfdestructas = "SmallBuildingExplosion",
		corpse         = "storage_dead", -- legacy feature, kept

		-- 7. Game-side data ------------------------------------------------------------
		customparams = {
			pool  = "base",
			role  = "storage",
			canon = "C4",
		},
	},
}
