function gadget:GetInfo()
  return {
    name = "UpgradeLogic",
    layer = 0,
    enabled = true
  }
end

if (gadgetHandler:IsSyncedCode()) then
  -- Riceve l'ordine dal Widget e lo esegue
  function gadget:RecvLuaMsg(msg, playerID)
    local action, unitID = msg:match("([^:]+):(%d+)")
    if not action or not unitID then return end
    unitID = tonumber(unitID)

    local unitDefID = Spring.GetUnitDefID(unitID)
    if not unitDefID then return end
    local ud = UnitDefs[unitDefID]

    -- ESECUZIONE POTENZIAMENTO VITA (Ex simple_upgrade.lua)
    if action == "upgrade_exec" then
      local upgradeAmount = tonumber(ud.customParams.upgrade_health)
      if upgradeAmount then
        local hp, maxHp = Spring.GetUnitHealth(unitID)
        local multiplier = 1 + (upgradeAmount / 100)
        local newMax = maxHp * multiplier

        Spring.SetUnitMaxHealth(unitID, newMax)

        -- Calcolo bonus per mantenere la barra della vita coerente
        local bonus = newMax - maxHp
        Spring.SetUnitHealth(unitID, hp + bonus)

        Spring.Echo("Logica: Vita potenziata del " .. upgradeAmount .. "% | Nuova Max: " .. math.floor(newMax))
      end

    -- ESECUZIONE EVOLUZIONE / MORPH (Ex simple_morph.lua)
    elseif action == "morph_exec" then
      local targetName = ud.customParams.can_evolve_to
      if targetName then
        local x, y, z = Spring.GetUnitPosition(unitID)
        local facing = Spring.GetUnitBuildFacing(unitID)
        local hp, maxHp = Spring.GetUnitHealth(unitID)
        local team = Spring.GetUnitTeam(unitID)

        -- Creiamo la nuova unità
        local newUnitID = Spring.CreateUnit(targetName, x, y, z, facing, team)

        if newUnitID then
          -- Trasferimento proporzionale della salute (se era al 50%, resta al 50%)
          local healthPercent = hp / maxHp
          local _, newMaxHp = Spring.GetUnitHealth(newUnitID)
          Spring.SetUnitHealth(newUnitID, newMaxHp * healthPercent)

          -- Effetto visivo e distruzione vecchia unità
          Spring.SpawnCEG("white_fountain", x, y, z)
          Spring.DestroyUnit(unitID, false, true)
          Spring.Echo("Logica: Unità evoluta con successo in " .. targetName)
        end
      end
    end
  end
end
