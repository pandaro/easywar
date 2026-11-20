-- ___tank: amphibious tank, shared base pool (canon C4, ROS-05): land and seabed, does not fire underwater.
-- Canonical unitdef layout. Converted from units/legacy/skeeter.lua (legacy name "skeeter").
-- PLACEHOLDER = value kept from the legacy def, no design meaning; balance starts later.

return {
	___tank = {
		-- 1. Identity
		name        = "Tank",
		description = "Amphibious tank, cannot fire underwater",
		objectname  = "Skeeter.s3o",
		script      = "skeeterscript.lua",
		buildpic    = "Skeeter.png",
		icontype    = "hoverraider", -- PLACEHOLDER until base icons are decided
		category    = "TANK SMALL NOTAIR NOTSUB", -- legacy, until categories are decided (HOVER removed)

		-- 2. Cost (ECO-11 / TST-02)
		energycost = 1000,
		metalcost  = 100,
		buildtime  = 1000,

		-- 3. Body and hitbox
		health                 = 270, -- PLACEHOLDER
		footprintx             = 2,   -- = movedef Tank_Amph_2x2
		footprintz             = 2,
		collisionvolumetype    = "box",
		collisionvolumescales  = "15 15 24",
		collisionvolumeoffsets = "0 1.5 0.5",
		sightdistance          = 560, -- PLACEHOLDER
		sonardistance          = 560, -- PLACEHOLDER

		-- 4. Movement (amphibious land vehicle on the seabed; slope and water depth come from the movedef)
		movementclass = "Tank_Amph_2x2",
		speed         = 104,  -- PLACEHOLDER
		maxacc        = 0.35, -- PLACEHOLDER
		maxdec        = 0.1,  -- PLACEHOLDER (old brakeRate)
		turnrate      = 2750, -- PLACEHOLDER

		-- 6. Abilities and flags
		canmove           = true,
		activatewhenbuilt = true,
		idleautoheal      = 0, -- autoheal is Delta's trait only (C7)
		nochasecategory   = "AIR",
		explodeas         = "SmallExplosion",
		selfdestructas    = "SmallExplosion",
		corpse            = "skeeter_dead",
		-- Shotgun has no waterweapon: fireSubmersed is false, so it does not fire from underwater (C4)
		weapons = {
                { name = "small_plasma_1_ground", onlytargetcategory = "NOTAIR", turret = true },
		},

		-- 7. Game-side data
		customparams = {
			pool  = "base",
			role  = "tank",
			canon = "C4",
		},

		-- Effects called by the unit script (muzzle flash)
		sfxtypes = {
			explosiongenerators = {
				"custom:skeetermuzzleflash",
			},
		},
	},
}
