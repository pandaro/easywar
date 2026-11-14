-- Generato da k116.py per l'unita' k116. Non modificare a mano: viene riscritto.
-- Primo test del kit: nessuna animazione, il modello e' un pezzo unico.
function script.Create()
  Spring.Echo('[easywar] k116 Create unitID=' .. tostring(unitID))
end

function script.Killed(recentDamage, maxHealth)
  return 1
end
