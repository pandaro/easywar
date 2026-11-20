-- ___wall: defensive wall, shared base pool (canon C4, ROS-01: built by the Commander and ___con, land and water).
-- Canonical unitdef layout. New def for the model delivered on 20 November (claude/report-modelli-strutture-base.md).
-- PLACEHOLDER = value with no design meaning yet; balance starts after the last faction.

return {
	___wall = {
		-- 1. Identity
		name        = "Wall",
		description = "Defensive wall",
		objectname  = "base/___wall.s3o",
		script      = "base/___wall.lua",
		icontype    = "buildingstorage", -- PLACEHOLDER: no wall icon in icontypes.lua
		category    = "TANK SMALL NOTAIR NOTSUB", -- legacy, until categories are decided

		-- 2. Cost (ECO-11 / TST-02)
		energycost = 1000,
		metalcost  = 100,
		buildtime  = 1000,

		-- 3. Body and hitbox (model 16 x 14 x 16 elmos, lowest point at 0)
		health                 = 2000, -- PLACEHOLDER
		footprintx             = 1,    -- decision of 20 November; 1 footprint square = 16 elmos
		footprintz             = 1,
		yardmap                = "o",
		collisionvolumetype    = "box",
		collisionvolumescales  = "16.0 14.2 16.0",
		collisionvolumeoffsets = "0 0 0", -- relative to the s3o mid point: check with /debugcolvol
		sightdistance          = 100, -- PLACEHOLDER

		-- 4. Terrain (ROS-01: land and water, floats)
		maxslope = 33, -- PLACEHOLDER
		floater  = true,

		-- 6. Abilities and flags
		canattack      = false,
		idleautoheal   = 0, -- autoheal is Delta's trait only (C7)
		explodeas      = "SmallExplosion",
		selfdestructas = "SmallExplosion",
		-- no corpse: no wreck model yet (ECO-03, open)

		-- 7. Game-side data
		customparams = {
			pool  = "base",
			role  = "wall",
			canon = "C4",
		},
	},
}