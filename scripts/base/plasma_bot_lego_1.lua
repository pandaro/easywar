-- Generato da plasma_bot_lego_1.py per l'unita' plasma_bot_lego_1. Non modificare a mano: viene riscritto.
-- Primo test: nessuna animazione. I pezzi (base, torso, head, arm_l/r, cannon, leg_l/r, shin_l/r, foot_l/r) ci sono
-- gia' con gerarchia e origini sulle articolazioni, pronti per l'animazione.
function script.Create()
  Spring.Echo('[easywar] plasma_bot_lego_1 Create unitID=' .. tostring(unitID))
end

function script.Killed(recentDamage, maxHealth)
  return 1
end
