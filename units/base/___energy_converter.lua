-- ___energy_converter: energy to metal converter, shared base pool (canon C4 row ___conv, ECO-04: built by ___con, amphibious).
-- Canonical unitdef layout. New def for the model delivered on 20 November (claude/report-modelli-strutture-base.md).
-- PLACEHOLDER = value with no design meaning yet; balance starts after the last faction.

return {
	___energy_converter = {
		-- 1. Identity
		name        = "Energy Converter",
		description = "Converts energy into metal while switched on",
		objectname  = "base/___energy_converter.s3o",
		script      = "base/___energy_converter.lua",
		icontype    = "buildingextractor", -- PLACEHOLDER: no converter icon in icontypes.lua
		category    = "TANK SMALL NOTAIR NOTSUB", -- legacy, until categories are decided

		-- 2. Cost (ECO-11 / TST-02)
		energycost = 1000,
		metalcost  = 100,
		buildtime  = 1000,

		-- 3. Body and hitbox (base 32 x 21 x 32 elmos; cable and funnel stick out and stay outside the hitbox)
		health                 = 500, -- PLACEHOLDER
		footprintx             = 2,   -- proposed by modelling, to confirm
		footprintz             = 2,
		yardmap                = "oooo",
		collisionvolumetype    = "box",
		collisionvolumescales  = "32 21 32",
		collisionvolumeoffsets = "0 0 0", -- relative to the s3o mid point: check with /debugcolvol
		sightdistance          = 200, -- PLACEHOLDER

		-- 4. Terrain (C4: amphibious, floats)
		maxslope = 33, -- PLACEHOLDER
		floater  = true,

		-- 5. Economy: while on and while the energy upkeep is paid, the engine adds makesmetal (Unit.cpp SlowUpdate)
		energyupkeep = 60, -- PLACEHOLDER (energy per second)
		makesmetal   = 1,  -- PLACEHOLDER (metal per second)

		-- 6. Abilities and flags
		onoffable         = true,
		activatewhenbuilt = true,
		canattack         = false,
		idleautoheal      = 0, -- autoheal is Delta's trait only (C7)
		explodeas         = "MediumBuildingExplosion",
		selfdestructas    = "MediumBuildingExplosion",
		-- no corpse: no wreck model yet (ECO-03, open)

		-- 7. Game-side data
		customparams = {
			pool  = "base",
			role  = "converter",
			canon = "C4",
		},
	},
}