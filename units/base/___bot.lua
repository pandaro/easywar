-- ___bot: Infantry bot, shared base pool skirmisher (canon C4, ROS-05).
-- Canonical unitdef layout. Converted from units/base/soldier.lua (test unit "soldier", kept).
-- PLACEHOLDER = value kept from the old def, no design meaning; balance starts later.

return {
	___bot = {
		-- 1. Identity
		name        = "Bot",
		description = "Infantry robot",
		objectname  = "base/soldier.s3o",
		script      = "base/soldier.lua",
		icontype    = "raider", -- PLACEHOLDER until base icons are decided
		category    = "TANK SMALL NOTAIR NOTSUB", -- legacy, until categories are decided

		-- 2. Cost (ECO-11 / TST-02)
		energycost = 1000,
		metalcost  = 100,
		buildtime  = 1000,

		-- 3. Body and hitbox
		health                 = 100, -- PLACEHOLDER
		footprintx             = 2,   -- = movedef BOT1
		footprintz             = 2,
		collisionvolumetype    = "box", -- was the bare word box (nil in Lua: the hitbox was ignored)
		collisionvolumescales  = "17 30 17",
		collisionvolumeoffsets = "0 -1 0",
		collisionvolumetest    = 1,
		sightdistance          = 500, -- PLACEHOLDER
		seismicsignature       = 0,

		-- 4. Movement (slope and water depth come from the movedef)
		movementclass         = "BOT1",
		speed                 = 100,  -- PLACEHOLDER
		maxacc                = 0.5,  -- PLACEHOLDER
		maxdec                = 0.5,  -- PLACEHOLDER
		turnrate              = 1000, -- PLACEHOLDER
		turninplace           = true,
		turninplaceanglelimit = 90,   -- PLACEHOLDER
		turninplacespeedlimit = 2,    -- PLACEHOLDER
		upright               = true,

		-- 6. Abilities and flags
		canmove         = true,
		idleautoheal    = 0, -- autoheal is Delta's trait only (C7)
		nochasecategory = "AIR",
		explodeas       = "SmallExplosion",
		selfdestructas  = "SmallExplosion",
		-- no corpse: "aven_trooper_dead" does not exist in features/ (ECO-03, open)

		-- Weapon kept inline from soldier.lua until it moves to weapons/ (weapondefs guidelines).
		weapondefs = {
			emg = {
				areaofeffect       = 8,
				avoidfeature       = false,
				burst              = 3,
				burstrate          = 0.1,
				craterareaofeffect = 0,
				craterboost        = 0,
				cratermult         = 0,
				cylindertargeting  = 1,
				edgeeffectiveness  = 0.15,
				explosiongenerator = "custom:plasmahit-small",
				firestarter        = 100,
				impulsefactor      = 0.123,
				intensity          = 0.7,
				name               = "Rapid-fire close-quarters g2g plasma guns",
				noselfdamage       = true,
				range              = 180,
				reloadtime         = 0.3,
				rgbcolor           = "1 0.95 0.4",
				size               = 1.75,
				soundhitwet        = "splshbig",
				soundstart         = "flashemg",
				sprayangle         = 1180,
				tolerance          = 5000,
				turret             = true,
				weapontimer        = 0.1,
				weapontype         = "Cannon",
				weaponvelocity     = 500,
				damage = {
					default = 9,
				},
			},
		},
		weapons = {
			{
				def                = "EMG",
				badtargetcategory  = "AIR",
				onlytargetcategory = "NOTSUB",
			},
		},

		-- 7. Game-side data
		customparams = {
			pool         = "base",
			role         = "infantry",
			canon        = "C4",
			model_author = "raar", -- kept from soldier.lua: model origin to verify
		},
	},
}