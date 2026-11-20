-- ___cam: perimeter camera, mainly line of sight, shared base pool (canon C4, ROS-10 "in doubt": built by ___con, amphibious).
-- Canonical unitdef layout. New def for the model delivered on 20 November (claude/report-modelli-strutture-base.md).
-- PLACEHOLDER = value with no design meaning yet; balance starts after the last faction.

return {
	___cam = {
		-- 1. Identity
		name        = "Camera",
		description = "Perimeter camera, gives line of sight",
		objectname  = "base/___cam.s3o",
		script      = "base/___cam.lua",
		icontype    = "buildingradar", -- PLACEHOLDER: no camera icon in icontypes.lua
		category    = "TANK SMALL NOTAIR NOTSUB", -- legacy, until categories are decided

		-- 2. Cost (ECO-11 / TST-02)
		energycost = 1000,
		metalcost  = 100,
		buildtime  = 1000,

		-- 3. Body and hitbox (model 14 x 32.5 x 14.6 elmos, lowest point at 0)
		health                 = 200, -- PLACEHOLDER
		footprintx             = 1,   -- proposed by modelling, to confirm
		footprintz             = 1,
		yardmap                = "o",
		collisionvolumetype    = "box",
		collisionvolumescales  = "14 32.5 14.6",
		collisionvolumeoffsets = "0 0 0", -- relative to the s3o mid point: check with /debugcolvol
		sightdistance          = 900, -- PLACEHOLDER (ROS-10: the camera's job)
		sightemitheight        = 30,  -- sight from the head of the model, not from the default 20 elmos

		-- 4. Terrain (C4: amphibious, floats)
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
			role  = "scout_static",
			canon = "C4",
		},
	},
}