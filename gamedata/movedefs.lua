local moveDefs 	=	 {

	----------------------------------------------------------------------
	-- TEST CLASSES (request "constructor amphibious / submarine", rev. 3).
	-- Owner: movedef agent. Context: movement_definition.md
	-- Values are test values, NOT balance. Not verified in the engine.
	-- Remove after the responsible picks variant A or B.
	----------------------------------------------------------------------

	-- Variant A: ground class (Tank) that walks on the seabed.
	-- maxWaterDepth very high; linearCoeff = 0 removes the depth slowdown
	-- so the test is not confused by speed (canon COM-02 wants a slowdown: open).
	{
		name = "Tank_Amph_3x3",
		speedModClass = 0,
		footprintX = 3,
		footprintZ = 3,
		maxSlope = 45,
		maxWaterDepth = 10000,
		depthModParams = { linearCoeff = 0 },
	},

	-- Variant B: ship-type class, submarine, minWaterDepth 0.
	-- Open question: can a ship-type class leave the water? (to test)
	-- The engine source only documents a negative minWaterDepth for that.
	{
		name = "Ship_Sub_3x3",
		speedModClass = 3,
		footprintX = 3,
		footprintZ = 3,
		minWaterDepth = -1000,
		subMarine = true,
	},

	----------------------------------------------------------------------
	-- LEGACY (unchanged below this line)
	----------------------------------------------------------------------

	{
		name =	"Small Vechicle",
		footprintX =	2,
		footprintZ =	2,
		maxWaterDepth =	20,
		maxSlope =	40,
	},
	{
		name =	"Large Vechicle",
		footprintX =	3,
		footprintZ =	3,
		maxWaterDepth =	20,
		maxSlope =	40,
	},
		{
		name =	"Ultimate Vechicle",
		footprintX =	5,
		footprintZ =	5,
		maxWaterDepth =	200000000,
		maxSlope =	45,
	},
	{
		name =	"Hover commander",
		footprintX =	4,
		footprintZ =	4,
		maxSlope =	40,
		speedModClass = 2,
	},

	{
		name =  "Large Hover",
		footprintX =	3,
		footprintZ =	3,
		maxSlope =	28,
		speedModClass = 2,
	},
	{
		name =	"Small Hover",
		footprintX =	2,
		footprintZ =	2,
		speedModClass = 2,
	},
	{
		name =	"Small Ship",
		footprintX =	2,
		footprintZ =	2,
		minWaterDepth =	3,
		speedModClass = 3,
	},
	{
		name =	"Medium Ship",
		footprintX =	3,
		footprintZ =	3,
		minWaterDepth =	3,
		speedModClass = 3,
	},
	{
		name =	"Large Ship",
		footprintX =	4,
		footprintZ =	4,
		minWaterDepth =	5,
		speedModClass = 3,
	},
	{
		name =	"Small Sub",
		footprintX =	2,
		footprintZ =	2,
		minWaterDepth =	30,
		speedModClass = 3,
		waterline = 30,
		Submarine = 1,
	},
	{
		name = "BOT1",
		crushstrength = 15,
		footprintx = 2,
		footprintz = 2,
		maxslope = 36,
		maxwaterdepth = 22,
		depthModParams = {
			minHeight = 4,
			linearCoeff = 0.03,
			maxValue = 0.7,
		}
	},
}

return moveDefs
