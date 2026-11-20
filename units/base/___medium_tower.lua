-- ___medium_tower: medium tower against surface units, shared base pool (canon C4: built by ___con, land only).
-- Canonical unitdef layout. Converted from units/legacy/HLT.lua (legacy name "hlt", kept).
-- PLACEHOLDER = value kept from the legacy def, no design meaning; balance starts later.

return {
	___medium_tower = {
		-- 1. Identity
		name        = "Medium Tower",
		description = "Medium laser tower against surface units",
		objectname  = "HLT.s3o",
		script      = "hltscript.lua",
		buildpic    = "HLT.png",
		icontype    = "buildinghlt",
		category    = "TANK SMALL NOTAIR NOTSUB", -- legacy, until categories are decided

		-- 2. Cost (ECO-11 / TST-02)
		energycost = 1000,
		metalcost  = 100,
		buildtime  = 1000,

		-- 3. Body and hitbox
		health                 = 1800, -- PLACEHOLDER
		footprintx             = 4,
		footprintz             = 4,
		yardmap                = "oooo oooo oooo oooo",
		collisionvolumetype    = "box",
		collisionvolumescales  = "30 116 30",
		collisionvolumeoffsets = "0 32.5 0",
		sightdistance          = 600, -- PLACEHOLDER

		-- 4. Terrain (C4: land only, like the wind turbine in the guidelines)
		maxslope      = 33,
		maxwaterdepth = 0,

		-- 6. Abilities and flags
		idleautoheal   = 0, -- autoheal is Delta's trait only (C7)
		explodeas      = "MediumBuildingExplosion",
		selfdestructas = "MediumBuildingExplosion",
		corpse         = "hlt_dead",
		weapons = {
			{ name = "HeavyLaser", onlytargetcategory = "NOTAIR", turret = true },
		},

		-- 7. Game-side data
		customparams = {
			pool  = "base",
			role  = "defense_surface",
			canon = "C4",
		},
	},
}