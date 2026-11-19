-- ___llt: Light Laser Tower, shared base pool (canon C4, ROS-01).
-- Canonical unitdef layout. Converted from units/economy/LLT.lua (legacy name "llt").
-- PLACEHOLDER = value kept from the legacy def, no design meaning; balance starts later.

return {
	___llt = {
		-- 1. Identity ---------------------------------------------------------------
		name        = "Light Laser Tower",
		description = "Light laser tower against surface units",
		objectname  = "LLT.s3o",
		script      = "lltscript.lua",
		buildpic    = "LLT.png",
		icontype    = "buildingllt",
		category    = "TANK SMALL NOTAIR NOTSUB", -- legacy targeting labels, kept until categories are decided

		-- 2. Cost (ECO-11 / TST-02) -------------------------------------------------
		energycost = 1000,
		metalcost  = 100,
		buildtime  = 1000,

		-- 3. Body and hitbox ---------------------------------------------------------
		health                 = 850, -- PLACEHOLDER
		footprintx             = 3,
		footprintz             = 3,
		yardmap                = "ooooooooo",
		collisionvolumetype    = "box",
		collisionvolumescales  = "25 85 25",
		collisionvolumeoffsets = "0 25 0",
		sightdistance          = 600, -- PLACEHOLDER

		-- 4. Terrain (ROS-01: land and water, floats) ------------------------------------------------
		maxslope = 33,
		floater  = true,

		-- 5. Economy -----------------------------------------------------------------
		-- none

		-- 6. Abilities and flags ------------------------------------------------------
		idleautoheal   = 0, -- autoheal is Delta's trait only (C7)
		explodeas      = "MediumBuildingExplosion",
		selfdestructas = "MediumBuildingExplosion",
		corpse         = "llt_dead", -- legacy feature, kept

		-- Weapons (defined in weapons/)
		weapons = {
			{ name = "LightLaser", onlytargetcategory = "NOTAIR" }, -- target filter added
		},

		-- 7. Game-side data ------------------------------------------------------------
		customparams = {
			pool  = "base",
			role  = "defense_surface",
			canon = "C4",
		},
	},
}
