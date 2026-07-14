function widget:GetInfo()
  return { name = "SimpleUpgradeUI", layer = 0, enabled = true }
end

local showMenu = false
local selectedUnitID = nil
local hasUpgrade = false
local hasMorph = false
local vsx, vsy = Spring.GetViewGeometry()

function widget:ViewResize(new_vsx, new_vsy)
  vsx, vsy = Spring.GetViewGeometry()
end

-- Rileva la selezione e costruisce il menu dinamicamente
-- Frammento logica pulsanti dinamici nel Widget
function widget:SelectionChanged(selectedUnits)
  -- ... reset variabili ...
  local ud = UnitDefs[Spring.GetUnitDefID(unitID)]

  -- Genera lista Evoluzioni
  if ud.customParams.can_evolve_to then
    for targetName in string.gmatch(ud.customParams.can_evolve_to, '([^,]+)') do
        -- Aggiungi a una tabella per disegnare i pulsanti morph
    end
  end

  -- Genera lista Upgrade
  if ud.customParams.upgrade_types then
    for uType in string.gmatch(ud.customParams.upgrade_types, '([^,]+)') do
        -- Aggiungi a una tabella per disegnare i pulsanti buff
    end
  end
end

function widget:DrawScreen()
  if not showMenu then return end
  local cx, cy = vsx * 0.5, vsy * 0.5

  -- Sfondo dinamico (si stringe se c'è solo un'opzione)
  local height = (hasUpgrade and hasMorph) and 100 or 60
  gl.Color(0, 0, 0, 0.8)
  gl.Rect(cx - 150, cy - height, cx + 150, cy + height)

  -- Pulsante UPGRADE (Mostra solo se ha upgrade_health)
  if hasUpgrade then
    local yOff = hasMorph and 10 or -25
    gl.Color(0.2, 0.5, 0.2, 1)
    gl.Rect(cx - 100, cy + yOff, cx + 100, cy + yOff + 50)
    gl.Color(1, 1, 1, 1)
    gl.Text("POTENZIA VITA", cx, cy + yOff + 20, 18, "oc")
  end

  -- Pulsante MORPH (Mostra solo se ha can_evolve_to)
  if hasMorph then
    local yOff = hasUpgrade and -60 or -25
    gl.Color(0.5, 0.2, 0.2, 1)
    gl.Rect(cx - 100, cy + yOff, cx + 100, cy + yOff + 50)
    gl.Color(1, 1, 1, 1)
    gl.Text("EVOLVI UNITA'", cx, cy + yOff + 20, 18, "oc")
  end
end

function widget:MousePress(x, y, button)
  if not showMenu or button ~= 1 or not selectedUnitID then return false end
  local cx, cy = vsx * 0.5, vsy * 0.5

  -- Logica click dinamica
  if hasUpgrade then
    local yOff = hasMorph and 10 or -25
    if x > cx - 100 and x < cx + 100 and y > cy + yOff and y < cy + yOff + 50 then
      Spring.SendLuaRulesMsg("upgrade_exec:" .. selectedUnitID)
      return true
    end
  end

  if hasMorph then
    local yOff = hasUpgrade and -60 or -25
    if x > cx - 100 and x < cx + 100 and y > cy + yOff and y < cy + yOff + 50 then
      Spring.SendLuaRulesMsg("morph_exec:" .. selectedUnitID)
      return true
    end
  end
end
