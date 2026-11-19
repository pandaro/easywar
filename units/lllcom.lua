-- lllcom: Lambda Commander, base form (canon C6 CMD-01..09, ROS-02, ECO-07, VIT-01).
-- Canonical unitdef layout, reference: BAR armcom.lua (structure only, no values copied).
-- PLACEHOLDER = value with no design meaning yet; balance starts after the last faction.

return {
	lllcom = {
		-- 1. Identity -----------------------------------------------------------------
		name        = "Lambda Commander",
		description = "Commander. Lose it and you lose the game",
		objectname  = "lllcomm.s3o",
		script      = "lllcomm.lua",
		buildpic    = "filename.png",
		icontype    = "commander",
		category    = "COMMANDER AMPHIBIOUS", -- legacy targeting categories, kept

		-- 2. Cost (Commander is excluded from ECO-11) -------------------------------------
		energycost = 1000,  -- PLACEHOLDER
		metalcost  = 1000,  -- PLACEHOLDER
		buildtime  = 10000, -- PLACEHOLDER (sets resurrection time)

		-- 3. Body and hitbox ---------------------------------------------------------------
		health                 = 1000, -- PLACEHOLDER
		footprintx             = 2,    -- must equal movedef "Hover commander" (4x4)
		footprintz             = 2,
		collisionvolumetype    = "box",
		collisionvolumescales  = "46 33.5 60.5", -- PLACEHOLDER, from the old def
		collisionvolumeoffsets = "0 0 0",
		sightdistance          = 100,  -- PLACEHOLDER
		radardistance          = 200, -- CMD-01: well below 2250; 100 or 1000 still open
		sonardistance          = 200,  -- PLACEHOLDER

		-- 4. Movement (current movedef, unchanged) -----------------------------------------
		movementclass = "Hover commander",
		maxslope      = 45,  -- must equal the movedef
		speed         = 45,  -- elmo/second; same as the old maxVelocity 1.5 elmo/frame
		maxacc        = 0.1, -- PLACEHOLDER
		maxdec        = 0.1,  -- PLACEHOLDER (old brakeRate)
		turnrate      = 1000, -- PLACEHOLDER
		floater       = true,
		waterline     = 5,

		-- 5. Economy (ECO-07) -----------------------------------------------------------------
		energymake = 10,
		metalmake  = 1,

		-- 6. Abilities and flags ---------------------------------------------------------------
		builder        = true,
		workertime     = 100,   -- PLACEHOLDER (build power)
		builddistance  = 100,  -- PLACEHOLDER
		repairspeed    = 100,   -- PLACEHOLDER
		reclaimspeed   = 100,   -- PLACEHOLDER
		terraformspeed = 9001, -- common flattening only (C7 Theta)
		canmove        = true,
		canattack      = true, -- CMD-09: base weapon laser
		capturable     = false, -- C7 Joker: Commanders cannot be captured
		reclaimable    = false,
		showplayername = true,
		activatewhenbuilt = true,
		canManualFire = true,
		explodeas      = "CommanderExplosion",
		selfdestructas = "CommanderExplosion",
		corpse         = "commander_dead", -- shared wreck feature, kept from the old def

		-- ROS-02: the Commander builds these 7 base units
		buildoptions =
		{
		'___lab',
		'___solar',
		'___mex',
		'___mstore',
		'___estore',
		'___llt',
		'___aat',
		},

		-- 7. Game-side data ----------------------------------------------------------------------
		customparams = {
			pool        = "lll",
			role        = "commander",
			canon       = "C6",
			iscommander = true, -- VIT-01: read by our defeat gadget
		},

		-- Effects called by the unit script (nano spray)
		sfxtypes = {
			explosiongenerators = {
				"custom:buildermuzzleflash",
			},
		},
		--Weapons and related
        explodeAs = [[CommanderExplosion]],
        selfDestructAs = [[CommanderExplosion]],
        NoChaseCategory = "AIR",
        weapons = {
        [1]={name  = "RapidCommanderLaser",
            turret = true
            },
        [2]={name  = "CommanderTempDLaser",
            turret = true
            },
        },
	},
}
