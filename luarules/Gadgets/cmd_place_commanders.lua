-- cmd_place_commanders: debug command "/luarules place commanders [teamID]" spawns one of each faction Commander near the cursor (cheats only). Canon entry: none, test tool. SYNCED part: flag for review.

function gadget:GetInfo()
	return {
		name    = "Place Commanders (debug)",
		desc    = "/luarules place commanders [teamID]: spawns every faction Commander (cheats only)",
		author  = "easywar",
		date    = "2026-11-16",
		license = "GNU GPL, v2 or later",
		layer   = 0,
		enabled = true,
	}
end

-- Fixed list, update by hand when Commanders change.
local COMMANDERS = {
	"aaacom", "gggcom", "lllcom", "dddcom", "jjjcom",
	"tttcom", "zzzcom", "ssscom", "ooocom",
}

local MSG_PREFIX = "ew_place_commanders" -- no ':' on purpose: simple_evolution.lua parses "word:number"
local RADIUS     = 160                   -- elmos from the center
local LOG        = "[easywar] place commanders: "

if gadgetHandler:IsSyncedCode() then
--------------------------------------------------------------------------------
-- SYNCED
--------------------------------------------------------------------------------

function gadget:Initialize()
	Spring.Echo("[easywar] cmd_place_commanders loaded (synced)")
end

function gadget:RecvLuaMsg(msg, playerID)
	if msg:sub(1, #MSG_PREFIX) ~= MSG_PREFIX then
		return false
	end

	if not Spring.IsCheatingEnabled() then
		Spring.Echo(LOG .. "cheats are disabled, nothing done (type /cheat first)")
		return true
	end

	local teamArg, cx, cz = msg:match("^" .. MSG_PREFIX .. " (%-?%d+) (%-?[%d%.]+) (%-?[%d%.]+)$")
	teamArg, cx, cz = tonumber(teamArg), tonumber(cx), tonumber(cz)
	if not (teamArg and cx and cz) then
		Spring.Echo(LOG .. "malformed message: " .. msg)
		return true
	end

	local teamID
	if teamArg >= 0 then
		if Spring.GetTeamInfo(teamArg, false) == nil then
			Spring.Echo(LOG .. "invalid team " .. teamArg)
			return true
		end
		teamID = teamArg
	else
		local _, _, spectator, playerTeam = Spring.GetPlayerInfo(playerID, false)
		if spectator or playerTeam == nil then
			Spring.Echo(LOG .. "sender is a spectator: pass a team, e.g. /luarules place commanders 0")
			return true
		end
		teamID = playerTeam
	end

	local created = 0
	local count = #COMMANDERS
	for i = 1, count do
		local name = COMMANDERS[i]
		local angle = (i - 1) * 2 * math.pi / count
		local x = cx + RADIUS * math.cos(angle)
		local z = cz + RADIUS * math.sin(angle)
		local y = Spring.GetGroundHeight(x, z)

		if UnitDefNames[name] == nil then
			Spring.Echo(LOG .. "ERROR " .. name .. ": no such UnitDef (failed to load?)")
		else
			local unitID = Spring.CreateUnit(name, x, y, z, 0, teamID)
			if unitID then
				created = created + 1
			else
				Spring.Echo(LOG .. string.format("ERROR %s: CreateUnit returned nil at (%.0f, %.0f, %.0f)", name, x, y, z))
			end
		end
	end

	Spring.Echo(LOG .. string.format("created %d/%d for team %d", created, count, teamID))
	return true
end

else
--------------------------------------------------------------------------------
-- UNSYNCED
--------------------------------------------------------------------------------

-- Returns world x, z under the cursor, or the camera position as fallback.
local function GetCenter()
	local mx, my = Spring.GetMouseState()
	local _, pos = Spring.TraceScreenRay(mx, my, true)
	if type(pos) == "table" and pos[1] and pos[3] then
		return pos[1], pos[3], "cursor"
	end
	local x, _, z = Spring.GetCameraPosition()
	return x, z, "camera"
end

-- Called on every client (the chat line is broadcast); only the sender acts.
local function OnPlace(_, _, words, playerID)
	if words[1] ~= "commanders" then
		return false
	end
	if playerID ~= Spring.GetMyPlayerID() then
		return true
	end

	local teamArg = -1
	if words[2] then
		teamArg = tonumber(words[2])
		if teamArg == nil or teamArg < 0 or teamArg % 1 ~= 0 then
			Spring.Echo(LOG .. "team must be a non-negative integer, got '" .. words[2] .. "'")
			return true
		end
	end

	local x, z, source = GetCenter()
	Spring.Echo(LOG .. string.format("request sent, center from %s (%.0f, %.0f)", source, x, z))
	Spring.SendLuaRulesMsg(string.format("%s %d %.1f %.1f", MSG_PREFIX, teamArg, x, z))
	return true
end

function gadget:Initialize()
	gadgetHandler:AddChatAction("place", OnPlace, " commanders [teamID]: spawn every faction Commander (cheats only)")
	Spring.Echo("[easywar] cmd_place_commanders loaded (unsynced)")
end

end
