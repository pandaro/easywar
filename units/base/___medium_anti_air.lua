-- ___medium_anti_air: medium anti-air tower, shared base pool (canon C4: built by ___con, land only).
-- Canonical unitdef layout. Converted from units/legacy/LMT.lua (legacy name "lmt", multipurpose missile tower, kept).
-- PLACEHOLDER = value kept from the legacy def, no design meaning; balance starts later.

return {
	___medium_anti_air = {
		-- 1. Identity
		name        = "Medium Anti-Air Tower",
		description = "Medium anti-air missile tower",
		objectname  = "LMT.s3o",
		script      = "lmtscript.lua",
		buildpic    = "LMT.png",
		icontype    = "buildingaat", -- PLACEHOLDER: legacy icon was buildingfiresupport
		category    = "TANK SMALL NOTAIR NOTSUB", -- legacy, until categories are decided

		-- 2. Cost (ECO-11 / TST-02)
		energycost = 1000,
		metalcost  = 100,
		buildtime  = 1000,

		-- 3. Body and hitbox
		health                 = 575, -- PLACEHOLDER
		footprintx             = 3,
		footprintz             = 3,
		yardmap                = "ooooooooo",
		collisionvolumetype    = "box",
		collisionvolumescales  = "25 85 25",
		collisionvolumeoffsets = "0 25 0",
		sightdistance          = 600, -- PLACEHOLDER

		-- 4. Terrain (C4: land only)
		maxslope      = 33,
		maxwaterdepth = 0,

		-- 6. Abilities and flags
		idleautoheal   = 0, -- autoheal is Delta's trait only (C7)
		explodeas      = "MediumBuildingExplosion",
		selfdestructas = "MediumBuildingExplosion",
		corpse         = "lmt_dead",
		weapons = {
			{ name = "LMTMissle", onlytargetcategory = "AIR", turret = true },
		},

		-- 7. Game-side data
		customparams = {
			pool  = "base",
			role  = "defense_air",
			canon = "C4",
		},
	},
}