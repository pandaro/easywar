-- ___lab: base pool lab, built as a static builder that places units in an area (canon C4, ROS-01, ROS-05, ROS-07).
-- Canonical unitdef layout. New def (no legacy source). No yardmap on purpose: with a yardmap the engine makes it a factory.
-- PLACEHOLDER = value with no design meaning yet; balance starts after the last faction.

return {
	___lab = {
		-- 1. Identity
		name        = "Lab",
		description = "Builds the base units within its range",
		objectname  = "base/___lab.s3o",
		script      = "base/___lab.lua",
		buildpic    = "Factory.png",         -- PLACEHOLDER picture until ___lab has its own
		icontype    = "buildinglandfactory",
		category    = "TANK SMALL NOTAIR NOTSUB", -- legacy, until categories are decided

		-- 2. Cost (ECO-11 / TST-02)
		energycost = 1000,
		metalcost  = 100,
		buildtime  = 1000,

		-- 3. Body and hitbox
		health        = 3500, -- PLACEHOLDER
		footprintx    = 1,
		footprintz    = 1,
		-- no yardmap: static builder, not a factory (UnitDef.h IsBuildingUnit / IsFactoryUnit)
		-- collisionvolume*: TODO, from the ___lab model (narrow and tall)
		sightdistance = 600,  -- PLACEHOLDER
		leavesghost   = true, -- not a building for the engine, so the ghost is forced

		-- 4. Terrain (ROS-01: land and water, floats). No movementclass, no speed: immobile.
		maxslope = 33, -- PLACEHOLDER
		floater  = true,

		-- 6. Abilities and flags
		builder       = true,
		workertime    = 10,  -- PLACEHOLDER (build power)
		builddistance = 200, -- PLACEHOLDER (build area radius)
		canmove       = false,
		-- production only: no repair, reclaim, assist, terrain restore, guard or patrol
		canrepair     = false,
		canreclaim    = false,
		canassist     = false,
		canrestore    = false,
		canguard      = false,
		canpatrol     = false,
		idleautoheal  = 0, -- autoheal is Delta's trait only (C7)
		explodeas      = "FactoryExplosion",
		selfdestructas = "FactoryExplosion",
		-- no corpse: no wreck model yet (ECO-03 exception, open)

		-- ROS-05: the lab produces these 5 units (missing defs are dropped by the engine with a warning)
		buildoptions = {
			"___con",
			"___bot",
			"___fighter",
			"___ship",
			"___tank",
		},

		-- 7. Game-side data
		customparams = {
			pool  = "base",
			role  = "factory",
			canon = "C4",
		},
	},
}