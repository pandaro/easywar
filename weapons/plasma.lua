-- Plasma cannons shared by all factions.
-- Implements: C4 ___tank (plasma, does not fire underwater), COM-05 (trans-faction weapons).
-- No effects or sounds yet: none verified in the repository.
local weaponDefs = {}

-- Small plasma cannon, ground targets only. Does not fire underwater:
-- no waterweapon, and fireSubmersed is explicitly false.
weaponDefs.small_plasma_1_ground = {
	name = "Small plasma cannon",
	weapontype = "Cannon",
	turret = true,
	fireSubmersed = false,
	range = 300,            -- PLACEHOLDER
	reloadtime = 2,         -- PLACEHOLDER
	weaponvelocity = 400,   -- PLACEHOLDER
	areaofeffect = 32,      -- PLACEHOLDER
	edgeeffectiveness = 0.15,
	craterareaofeffect = 0,
	craterboost = 0,
	cratermult = 0,
	noselfdamage = true,
	tolerance = 5000,
	rgbcolor = "0.4 0.8 1",
	size = 3,
	damage = {
		default = 100,      -- PLACEHOLDER
	},
}

return lowerkeys(weaponDefs)
