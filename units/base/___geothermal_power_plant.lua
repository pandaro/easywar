-- ___geothermal_power_plant: geothermal energy, shared base pool (canon C4, ECO-05: built by ___con, amphibious).
-- Canonical unitdef layout. Converted from units/legacy/geothermalgenerator.lua (legacy name "geothermalgenerator", kept).
-- PLACEHOLDER = value kept from the legacy def, no design meaning; balance starts later.

return {
	___geothermal_power_plant = {
		-- 1. Identity
		name        = "Geothermal Power Plant",
		description = "Energy generator, must be placed on a geothermal vent",
		objectname  = "Geothermal Generator.s3o",
		script      = "geothermalgeneratorscript.lua",
		buildpic    = "Geothermal Generator.png",
		icontype    = "buildinggeo",
		category    = "TANK SMALL NOTAIR NOTSUB", -- legacy, until categories are decided

		-- 2. Cost (ECO-11 / TST-02)
		energycost = 1000,
		metalcost  = 100,
		buildtime  = 1000,

		-- 3. Body and hitbox
		health                 = 2500, -- PLACEHOLDER
		footprintx             = 6,
		footprintz             = 6,
		-- 'g' squares: the engine requires a geothermal feature under them (needGeo)
		yardmap                = "oooooo oggggo oggggo oggggo oggggo oooooo",
		collisionvolumetype    = "box",
		collisionvolumescales  = "60 70 60",
		collisionvolumeoffsets = "0 10 0",
		sightdistance          = 475, -- PLACEHOLDER

		-- 4. Terrain (C4: amphibious, floats)
		maxslope = 33,
		floater  = true,

		-- 5. Economy
		energymake = 25, -- PLACEHOLDER (no metal: removed on 20 November, ECO-02)

		-- 6. Abilities and flags
		onoffable         = true,
		activatewhenbuilt = true,
		idleautoheal      = 0, -- autoheal is Delta's trait only (C7)
		explodeas         = "GeothermalExplosion",
		selfdestructas    = "GeothermalExplosion",
		corpse            = "geothermalgenerator_dead",

		-- 7. Game-side data
		customparams = {
			pool  = "base",
			role  = "energy",
			canon = "C4",
		},
	},
}