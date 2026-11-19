-- ___solar: Solar Collector, shared base pool (canon C4, ROS-01, ECO-05).
-- Canonical unitdef layout. Converted from units/economy/solarpanel.lua (legacy name "solarpanel").
-- PLACEHOLDER = value kept from the legacy def, no design meaning; balance starts later.

return {
	___solar = {
		-- 1. Identity ---------------------------------------------------------------
		name        = "Solar Collector",
		description = "Produces energy",
		objectname  = "Solar Pannel2.s3o",
		script      = "solarpanelscript.lua",
		buildpic    = "Solar Pannel.png",
		icontype    = "buildingenergy",
		category    = "TANK SMALL NOTAIR NOTSUB", -- legacy targeting labels, kept until categories are decided

		-- 2. Cost (ECO-11 / TST-02) -------------------------------------------------
		energycost = 1000,
		metalcost  = 100,
		buildtime  = 1000,

		-- 3. Body and hitbox ---------------------------------------------------------
		health                 = 500, -- PLACEHOLDER
		footprintx             = 4,
		footprintz             = 4,
		yardmap                = "oooo oooo oooo oooo",
		collisionvolumetype    = "box",
		collisionvolumescales  = "33 45 33",
		collisionvolumeoffsets = "0 0 0",
		sightdistance          = 400, -- PLACEHOLDER

		-- 4. Terrain (ROS-01: land and water, floats) ------------------------------------------------
		maxslope = 33,
		floater  = true, -- was maxWaterDepth = 4 (land only)

		-- 5. Economy -----------------------------------------------------------------
		energyupkeep = -20, -- PLACEHOLDER; negative upkeep = production while on

		-- 6. Abilities and flags ------------------------------------------------------
		idleautoheal   = 0, -- autoheal is Delta's trait only (C7)
		onoffable         = true,
		activatewhenbuilt = true,
		damagemodifier    = 0.25, -- PLACEHOLDER: armour when switched off
		explodeas      = "MediumBuildingExplosion",
		selfdestructas = "MediumBuildingExplosion",
		corpse         = "solarpanel_dead", -- legacy feature, kept

		-- 7. Game-side data ------------------------------------------------------------
		customparams = {
			pool  = "base",
			role  = "energy",
			canon = "C4",
		},
	},
}
