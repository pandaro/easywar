-- ___share_unit: team resource sharing hub, shared base pool (canon C4 row ___share, ROS-11 hypothesis: built by ___con).
-- Canonical unitdef layout. New def for the model delivered by modelling (claude/report-modelli-strutture-base.md).
-- PLACEHOLDER = value with no design meaning yet; balance starts after the last faction.
-- The sharing mechanic is not here: it will be a gadget (open point).

return {
	___share_unit = {
		-- 1. Identity
		name        = "Share Unit",
		description = "Manages resource sharing within the team",
		objectname  = "base/___share_unit.s3o",
		script      = "base/___share_unit.lua",
		icontype    = "buildingstorage", -- PLACEHOLDER: no share icon in icontypes.lua
		category    = "TANK SMALL NOTAIR NOTSUB", -- legacy, until categories are decided

		-- 2. Cost (ECO-11 / TST-02)
		energycost = 1000,
		metalcost  = 100,
		buildtime  = 1000,

		-- 3. Body and hitbox (model 32 x 24.9 x 32 elmos, lowest point at 0)
		health                 = 500, -- PLACEHOLDER
		footprintx             = 2,   -- decision of 20 November
		footprintz             = 2,
		yardmap                = "oooo",
		collisionvolumetype    = "box",
		collisionvolumescales  = "32 24.9 32",
		collisionvolumeoffsets = "0 0 0", -- relative to the s3o mid point: check with /debugcolvol
		sightdistance          = 200, -- PLACEHOLDER

		-- 4. Terrain: land and water, sits on the seabed (decision of 20 November: no floater).
		-- No water depth limit (engine default).
		maxslope = 33, -- PLACEHOLDER

		-- 6. Abilities and flags
		canattack      = false,
		idleautoheal   = 0, -- autoheal is Delta's trait only (C7)
		explodeas      = "MediumBuildingExplosion",
		selfdestructas = "MediumBuildingExplosion",
		-- no corpse: no wreck model yet (ECO-03, open)

		-- 7. Game-side data
		customparams = {
			pool  = "base",
			role  = "share",
			canon = "C4",
		},
	},
}