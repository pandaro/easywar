-- ___medium_anti_submarine_launcher: medium naval tower, also hits submerged units (canon C4, ROS-09: built by ___con, water only).
-- Canonical unitdef layout. Converted from units/legacy/TP.lua (legacy name "tp", kept).
-- PLACEHOLDER = value kept from the legacy def, no design meaning; balance starts later.

return {
	___medium_anti_submarine_launcher = {
		-- 1. Identity
		name        = "Medium Anti-Submarine Launcher",
		description = "Naval tower, hits submerged units",
		objectname  = "TP.s3o",
		script      = "tpscript.lua",
		buildpic    = "Torpedo Platform.png",
		icontype    = "buildingantisub",
		category    = "TANK SMALL NOTAIR NOTSUB", -- legacy, until categories are decided

		-- 2. Cost (ECO-11 / TST-02)
		energycost = 1000,
		metalcost  = 100,
		buildtime  = 1000,

		-- 3. Body and hitbox
		health                 = 1000, -- PLACEHOLDER
		footprintx             = 3,
		footprintz             = 3,
		yardmap                = "ooooooooo",
		collisionvolumetype    = "box",
		collisionvolumescales  = "36 18 36",
		collisionvolumeoffsets = "0 0 0",
		sightdistance          = 600,  -- PLACEHOLDER
		sonardistance          = 1000, -- PLACEHOLDER

		-- 4. Terrain (C4: water only, floats)
		maxslope      = 33,
		floater       = true,
		minwaterdepth = 15, -- PLACEHOLDER

		-- 6. Abilities and flags
		activatewhenbuilt = true,
		idleautoheal      = 0, -- autoheal is Delta's trait only (C7)
		explodeas         = "MediumBuildingExplosion",
		selfdestructas    = "MediumBuildingExplosion",
		corpse            = "tp_dead", -- feature exists in features/; the legacy def had no corpse (ECO-03)
		-- Hits every unit in water (submarines, ships, hovers and amphibious units over water), never on land:
		-- a TorpedoLauncher only fires at targets in water (TorpedoLauncher.cpp TestTarget).
		weapons = {
			{ name = "TPTorpedo", onlytargetcategory = "NOTAIR" },
		},

		-- 7. Game-side data
		customparams = {
			pool  = "base",
			role  = "defense_naval",
			canon = "C4",
		},
	},
}
