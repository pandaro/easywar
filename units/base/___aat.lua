-- ___aat: Anti-Air Tower, shared base pool (canon C4, ROS-01).
-- Canonical unitdef layout. Converted from units/economy/AAT.lua (legacy name "aat").
-- PLACEHOLDER = value kept from the legacy def, no design meaning; balance starts later.

return {
	___aat = {
		-- 1. Identity ---------------------------------------------------------------
		name        = "Anti-Air Tower",
		description = "Light anti-air tower",
		objectname  = "AAT.s3o",
		script      = "aatscript.lua",
		buildpic    = "AAT.png",
		icontype    = "buildingaat",
		category    = "TANK SMALL NOTAIR NOTSUB", -- legacy targeting labels, kept until categories are decided

		-- 2. Cost (ECO-11 / TST-02) -------------------------------------------------
		energycost = 1000,
		metalcost  = 100,
		buildtime  = 1000,

		-- 3. Body and hitbox ---------------------------------------------------------
		health                 = 1000, -- PLACEHOLDER
		footprintx             = 3,
		footprintz             = 3,
		yardmap                = "ooooooooo",
		collisionvolumetype    = "box",
		collisionvolumescales  = "25 75 25",
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
		corpse         = "aat_dead", -- legacy feature, kept

		-- Weapons (defined in weapons/)
		weapons = {
			{ name = "AATMissle", onlytargetcategory = "AIR" },
		},

		-- 7. Game-side data ------------------------------------------------------------
		customparams = {
			pool  = "base",
			role  = "defense_air",
			canon = "C4",
		},
	},
}
