# Recoil, S3O e Blender: base tecnica per agenti

Nov 14, 2026 · @bio

Questo documento raccoglie solo i fatti tecnici su modelli S3O, Blender e motore Recoil, ciascuno con il suo livello di prova, perché un agente possa convertire, texturizzare, ridimensionare o scriptare modelli senza ripartire da zero.

## Come usare questo documento

Chi legge è un agente che deve produrre o convertire un modello per Recoil, texturizzarlo, ridimensionarlo o scrivere lo script che lo anima. Ogni affermazione porta un livello di prova:

- **visto**: osservato in un output di Blender, nel log del motore o nel gioco in esecuzione.
- **dichiarato**: riferito dal responsabile o scritto in una fonte (README, documentazione), non osservato.
- **da provare**: non ancora tentato. Non darlo per buono.

Quando un fatto qui non basta, si cerca nelle fonti, in quest'ordine: documentazione ufficiale di Recoil e README degli strumenti, codice di giochi di riferimento come Beyond All Reason (BAR), conoscenza generale solo come ipotesi marcata "da verificare". Non si inventano nomi di funzioni, parametri o opzioni.

**Regole operative**

- Il responsabile non modella a mano. Ogni passo si fa con uno script che lancia con un solo comando.
- Non aprire né stampare file che possono contenere credenziali (`~/.spring/script.txt`, configurazioni di SkyLobby e della lobby).
- Non toccare nulla in `~/.spring` fuori da `games/easywar.sdd`. Non cancellare file senza richiesta. Nessun commit o push senza richiesta.
- Prima di scrivere nel repository del gioco, chiedere conferma. Gli script consegnano i file nelle cartelle del gioco solo con `deploy` attivo.
- Dichiarare sempre il conteggio reale dei triangoli del modello consegnato.

## Catena di produzione in sintesi

L'intera catena gira senza interfaccia: un file Python lanciato con Blender produce modello, texture, script Lua e definizione dell'unità, poi li consegna nel gioco (visto, più unità collaudate nel motore).

1. **Forme.** Lo script crea in Blender un oggetto per pezzo, con genitore e posizione relativa (origine del pezzo = giunto), UV per angolo e triangoli.
2. **Texture.** Si scrivono due PNG: tex1 (colori + alpha del colore giocatore) e tex2 (proprietà del materiale). I nomi dei due file vanno passati alla radice S3O.
3. **Orientamento.** Il pezzo radice si ruota di 180° attorno a Z, poi si crea la radice S3O e si compensa la sua rotazione con l'inversa del genitore.
4. **Esportazione.** `s3o_tools.export_s3o` scrive il `.s3o` dalla radice attiva.
5. **Lua.** Si genera lo script dell'unità (camminata, mira, sparo, costruzione) con il nome del file uguale al campo `script` della definizione.
6. **Definizione.** Si crea `units/base/NOME.lua` se manca, con `ObjectName`, `script`, armi e volume di collisione.
7. **Consegna.** Si copiano `.s3o`, due PNG e `.lua` nelle cartelle del gioco (percorsi nella sezione sulla definizione dell'unità).
8. **Verifica.** Si carica l'unità in partita e si legge `~/.spring/infolog.txt`. Un visualizzatore di modelli senza partita completa non è stato trovato (da provare).

## Formato S3O e vincoli

I vincoli del formato `.s3o` (dichiarati dal brief; l'esportazione di modelli che li rispettano è vista):

- Gerarchia di pezzi con **nomi unici**. Il Lua chiama i pezzi per nome con `piece('nome')`, quindi nome nel modello e nome nello script devono coincidere.
- **Esattamente due texture** per modello (tex1 e tex2).
- **Una sola mappa UV**. Niente colori per vertice.
- Mesh **triangolata** all'esportazione. Conviene triangolare prima, così il conteggio dei triangoli è quello reale: somma di `len(mesh.polygons)` di tutti i pezzi.

**Pezzi e giunti** (visto)

- Ogni pezzo è un oggetto Blender con un genitore. La posizione dell'oggetto rispetto al genitore è l'**origine del pezzo**, che deve stare sul giunto: le rotazioni e gli spostamenti del Lua avvengono attorno a quel punto.
- I vertici di un pezzo sono espressi relativamente alla sua origine, non al mondo.
- Tipica gerarchia di un bipede: `base` (busto) con figli `head`, `arm_l/r`, `leg_l/r`; sotto le braccia `fore_l/r`, sotto le gambe `shin_l/r` (e se serve `foot_l/r`).
- Un pezzo senza geometria non è stato provato. Per un punto di tiro o di costruzione si è usato un triangolino nascosto dentro la canna (da provare nel motore).
- Il punto più basso del modello va a quota 0 rispetto alla radice, così i piedi stanno a terra (visto con modelli costruiti in questo modo; un caso di piedi sotto il terreno è rimasto irrisolto, vedi la diagnosi).

**Dimensioni e collisione**

- Le unità sono quelle del motore. Un bipede umano d'attacco è alto circa 36 unità, i robot di prova 30–36 (visto).
- Si è usata un'impronta 2×2. Per robot larghi potrebbe essere piccola (aperto).
- Il volume di collisione della radice S3O resta ai valori predefiniti; nella definizione dell'unità si può impostare `collisionVolumeType = "box"` con `collisionVolumeScales` in ordine larghezza, altezza, profondità (usato negli script, non verificato). Il comando `/debugcolvol` mostra i volumi (da provare).
- Shading: tutti gli script usano facce piatte. L'effetto di normali lisce non è stato provato.

**Budget di triangoli** (dichiarato dal responsabile in base alla sua esperienza di Recoil e BAR; si corregge in corso d'opera)

| Categoria | Triangoli |
| --- | --- |
| Unità di spam, le più numerose | circa 500 |
| Unità di basso livello | meno di 1000 |
| Unità di rango medio | 1000–2000 |
| Unità enormi e iconiche, poche in campo | fino a 5000 |
| Primi test | 500–1000 |

Obiettivo di prestazioni: circa 2000 unità per giocatore, fino a 16 giocatori. Ipotesi da verificare: l'S3O ripete un vertice per ogni combinazione diversa di posizione, UV e normale, quindi UV per angolo (una mesh dove quasi ogni vertice è su un bordo di UV) gonfiano il numero di vertici caricati.

## Texture

Ogni modello ha due texture e una sola mappa UV. I canali, nei fatti osservati:

| Texture | Canali | Significato | Prova |
| --- | --- | --- | --- |
| tex1 | RGB | colori del modello | visto |
| tex1 | A (alpha) | **alpha alto = colore del giocatore**, alpha basso = colore dipinto | visto nel motore e nell'atlas `Arm_color` di BAR |
| tex2 | R, G, B, A | proprietà fisiche e luminose del materiale | dichiarato dal responsabile |
| tex2 | R, G, A di `Arm_other` (BAR) | R: macchie sparse (bagliore?). G: grigio diffuso (riflessione?). A: circa 255 | visto nel file, significato da verificare |

Il valore usato per tex2 negli script (R 0, G 128, B 0, A 255) viene accettato dal motore senza errori (visto). L'assegnazione esatta dei canali va verificata nelle fonti del motore prima di dipingere bagliori o riflessi.

**Capovolgimento della V** (visto). Il motore mostra le texture capovolte in verticale rispetto a Blender. Con il PNG salvato normalmente (riga 0 in alto) e `v_su` = coordinata V con l'origine in basso, come in Blender, FBX e OBJ, nelle UV del modello si scrive `v = 1 - v_su`. In pratica la riga letta dal motore, contando dall'alto, è `v · altezza`. Gli script hanno un parametro `flip_v` per questo.

**Nomi e posizioni** (visto)

- I nomi delle due texture si passano a `add_s3o_root` come `texture_name_1` e `texture_name_2` e finiscono dentro il `.s3o`. Se sono vuoti o sbagliati le texture non vengono caricate.
- Convenzione degli script: `NOME1.png` e `NOME2.png`, nella cartella `unittextures/` del gioco.

**Scrivere i PNG a mano** (visto). Se Blender salva un PNG, azzera il colore dove l'alpha è 0, e il colore sotto l'alpha serve. Gli script scrivono quindi il PNG RGBA a 8 bit con `struct` e `zlib`, senza passare da Blender:

```python
def write_png_rgba(path, arr):          # arr: numpy uint8, forma (h, w, 4)
    h, w = arr.shape[:2]
    raw = np.zeros((h, w * 4 + 1), np.uint8)   # primo byte di ogni riga = filtro 0
    raw[:, 1:] = arr.reshape(h, w * 4)
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    data = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw.tobytes(), 6)) + chunk(b"IEND", b""))
    open(path, "wb").write(data)
```

**Formati e dimensioni**

- Il motore ha caricato PNG (visto). BAR usa DDS DXT5 (`Arm_color.dds`, `Arm_other.dds`), atlas 4096×4096 condivisi da tutte le unità di una fazione (visto nei file BAR). Il formato S3O consente atlas condivisi. La conversione in DDS non è stata provata.
- Una texture dipinta a 1024×1024 con alpha pesa circa 2,4 MB come PNG (misurato). In memoria 2048×2048 RGBA a 8 bit sono 16 MB non compressi, quattro volte più di 1024.

**Più materiali in due texture** (aperto). Rischio già noto: nove materiali di fazione in due sole texture. Una tecnica provata con forme semplici è l'atlas a zone: tex1 divisa in rettangoli (corazza, parti scure, colore giocatore con alpha alta, dettagli), e ogni faccia proiettata con le UV dentro la zona del suo materiale. Non è stata provata con più di quattro zone.

## Assi, orientamento e scala

L'orientamento è la causa più comune di modelli sdraiati o girati al contrario. I sistemi in gioco:

| Sistema | Su | Fronte del modello | Nota |
| --- | --- | --- | --- |
| Blender, lavoro degli script | Z | −Y | prova: visto |
| Editor e file esterni (Wings 3D, FBX) | Y | +Z | i file osservati; il fronte si è verificato guardando il modello, non dal campo `FrontAxis` |
| Radice S3O creata dall'operatore | — | — | ruotata di suo di (90°, 180°, 0): va compensata |

**Conversione dal sistema Y-su/fronte +Z a Blender** (visto): `(x, y, z) → (x, −z, y)`, cioè una rotazione di 90° attorno a X. Mantiene l'orientamento delle facce, quindi l'ordine dei vertici resta valido.

**Sequenza che dà un modello in piedi e rivolto nel verso giusto** (visto nel motore)

1. Costruire i pezzi con Z su e fronte −Y.
2. Ruotare il pezzo radice del modello di 180° attorno a Z (`rotation_euler = (0, 0, radians(180))`). I figli seguono.
3. Creare la radice S3O con `s3o_tools.add_s3o_root`.
4. Agganciare il pezzo radice alla radice S3O compensando la sua rotazione:

```python
obj.parent = root
obj.matrix_parent_inverse = root.matrix_world.inverted()
```

5. Selezionare solo la radice S3O e renderla attiva, poi esportare.

**Scala**

- Si porta l'altezza all'altezza voluta (parametro `target_height`) moltiplicando le coordinate dei vertici e le posizioni dei giunti prima di creare gli oggetti, così ogni oggetto ha scala 1. La scala applicata sugli oggetti non è stata provata con l'esportatore.
- Un'unità Blender corrisponde a un'unità del motore. Altezze usate: soldier 36, robot 30–36.
- Dopo la scala il punto più basso va portato a quota 0.

**Destra e sinistra.** I pezzi `_r` si sono costruiti a X positivo del sistema di lavoro. Quale lato appaia «destra» in gioco dipende dalla sequenza sopra (yaw di 180°). L'assegnazione di `_r` e `_l` alle armi 1 e 2 non conta per il motore, ma va controllata a vista quando una mano sola ha l'arma.

## Blender: ambiente, S3O Kit e script senza interfaccia

**Ambiente** (dichiarato dal setup di novembre 2026, import ed export `.s3o` visti)

- Blender 5.2.0 LTS come Flatpak. Non è nel PATH: si lancia con `flatpak run org.blender.Blender`. La versione si legge da `bpy.app.version_string`; non assumere versioni, ricavarle dall'output.
- Addon S3O Kit 0.3.2, con import ed export di `.s3o`.
- Il motore è in `~/.spring/engine/`, una cartella per versione; in uso `recoil_2026.07.04_amd64-linux`. Log: `~/.spring/infolog.txt`.
- Trappola: nello zip di S3O Kit il file `SpringModelingTemplate.blend` è un puntatore Git LFS di 134 byte. Il file vero pesa 285.633.681 byte (sha256 `662d6f380ddfe265cd31f6953479f0af3c0e8e2dfd97034f21c46b19d7afbaea`) ed è già al suo posto. Reinstallando dallo zip il problema ritorna (visto).

**Lancio senza interfaccia** (visto)

```
flatpak run org.blender.Blender --background --python /percorso/NOME.py | grep -E "MARCATORI|S3O_ROOT|DEPLOY|TRIANGOLI"
```

I parametri si passano dopo `--`, per esempio un oggetto JSON: `... NOME.py -- '{"target_height":40,"deploy":false}'`. Gli script stampano righe con un prefisso fisso per poterle filtrare con `grep`. Conviene proteggere la parte Blender con `try: import bpy`, così la geometria e le texture si provano anche fuori da Blender.

**Operatori di S3O Kit** (visti)

- `bpy.ops.s3o_tools.add_s3o_root(name=..., texture_name_1=..., texture_name_2=...)` crea la radice S3O e scrive i nomi delle due texture.
- `bpy.ops.s3o_tools.export_s3o(filepath=...)` esporta a partire dall'oggetto radice **attivo e selezionato**. Se non c'è una radice S3O il comando di esportazione è grigio e non cliccabile.
- Da script si chiamano con `"EXEC_DEFAULT"` come primo argomento. Gli script cercano l'operatore scorrendo `dir(bpy.ops)` per i nomi che contengono `s3o` e `root`, per reggere eventuali rinomine.

**API di Blender usate con successo** (viste)

- Mesh da dati: `mesh.from_pydata(vertici, [], poligoni)`, poi `mesh.uv_layers.new(name="UVMap")` e `uv.data[i].uv = (u, v)`, dove `i` è l'indice dell'angolo (loop) nell'ordine dei poligoni. Con triangoli: angolo `3*p + c` per il poligono `p`, angolo `c`.
- Facce piatte: `p.use_smooth = False` per ogni poligono.
- Gerarchia: `obj.parent = genitore` e `obj.location = posizione relativa`. Impostare il genitore prima di ruotare la radice.
- Pulizia iniziale: rimuovere tutti gli oggetti con `bpy.data.objects.remove(ob, do_unlink=True)`.
- Salvataggio: `bpy.ops.wm.save_as_mainfile(filepath=...)`.
- Un materiale con la texture serve solo all'anteprima in Blender: il motore usa i PNG. Con Blender in italiano i nodi hanno nomi tradotti («Generico BSDF»): trovare il nodo per tipo, `n.type == "BSDF_PRINCIPLED"`, mai per nome inglese.

**Python incluso in Blender.** Ha `numpy` (usato). Non si deve contare su `PIL` né `scipy`: sono assenti dall'installazione standard di Blender (noto, non verificato qui). Per leggere un'immagine senza PIL: `bpy.data.images.load(percorso)`, impostare `img.colorspace_settings.name = "Non-Color"`, poi `img.pixels.foreach_get(buf)` con `buf` array float32 di `w*h*4`. Le righe partono dal basso e vanno capovolte (da provare). Le parti connesse di una mesh si calcolano con un union-find in Python puro.

**Animazione in Blender.** Skeletor\_S3O, addon di Beherith, esporta animazioni in BOS, LUS e LUS Tween. Dal README (letto su un mirror) risulta compatibile con Blender 2.80–4.3 LTS (dichiarato); su Blender 5.x è da provare. Non serve se le animazioni si scrivono direttamente in Lua, come si è fatto finora.

**Formati alternativi.** glTF e Collada (via Assimp) sono citati dalla documentazione come sperimentali. Il responsabile riferisce che il supporto nel motore è agli inizi. Non provati.

## Definizione dell'unità e percorsi nel gioco

Il gioco sta in `~/.spring/games/easywar.sdd` e coincide con il repository `pandaro/easywar` (visto). Un'unità di nome `NOME` usa quattro file più le due texture:

| File | Percorso nel gioco | Note |
| --- | --- | --- |
| Modello | `objects3d/base/NOME.s3o` | `ObjectName` lo indica come `base/NOME.s3o` |
| Texture | `unittextures/NOME1.png`, `NOME2.png` | nomi scritti dentro il `.s3o` |
| Script Lua | `scripts/base/NOME.lua` | `script = "base/NOME.lua"` nella definizione |
| Definizione | `units/base/NOME.lua` | finisce con `return lowerkeys({ [unitName] = unitDef })` |
| Area di lavoro | `easywar_work/` | non va nel repository: aggiungere la riga al `.gitignore` |

**Il campo `script` deve coincidere con il nome del file Lua.** Se non coincide, lo script non viene caricato e nel log non compare alcun errore (visto). Per accorgersi che lo script è attivo, mettere un `Spring.Echo('[easywar] NOME Create unitID=' .. tostring(unitID))` in `script.Create` e cercarlo in `infolog.txt`.

**Campi della definizione usati negli script** (visti in funzione salvo dove indicato)

| Campo | Valore usato | Nota |
| --- | --- | --- |
| `ObjectName` | `base/NOME.s3o` | percorso relativo a `objects3d/` |
| `script` | `base/NOME.lua` | vedi sopra |
| `Category` | quella dell'unità base esistente | copiata da `soldier.lua` |
| `MovementClass` | quella dell'unità base esistente | copiata da `soldier.lua` |
| `FootprintX`, `FootprintZ` | 2, 2 | forse piccola per i robot larghi |
| `MaxDamage`, `MaxVelocity` | 500, 1.4 | segnaposto, non bilanciati |
| `BuildPic`, `corpse`, `explodeAs` | `Constructor.png`, `constructor_dead`, `MediumExplosion` | segnaposto, non verificati |
| `collisionVolumeType`, `collisionVolumeOffsets`, `collisionVolumeScales` | `box`, `0 0 0`, larghezza altezza profondità | non verificati nel motore |
| `CanAttack`, `CanMove`, `CanGuard`, `CanPatrol`, `CanStop` | 1 |  |

Gli script creano la definizione solo se il file manca, e non la sovrascrivono mai: se esiste ma non ha `weapons`, avvisano che la mira non partirà.

**Armi** (viste in gioco; soluzione provvisoria concordata col responsabile). `weapondefs` e `weapons` stanno dentro la definizione dell'unità, non in file separati. L'indice in `weapons` è il numero `n` che il motore passa alle funzioni Lua della mira.

```lua
weapondefs = {
   mech_gun = {
      areaofeffect = 8, burst = 3, burstrate = 0.1,
      range = 180, reloadtime = 0.3, weaponvelocity = 500,
      weapontype = "Cannon", turret = true, tolerance = 5000, sprayangle = 1180,
      rgbcolor = "1 0.95 0.4", size = 1.75, noselfdamage = true,
      damage = { default = 9 },
   },
},
weapons = {
   [1] = { def = "mech_gun", onlytargetcategory = "NOTSUB" },
},
```

Sono stati lasciati fuori di proposito l'`explosiongenerator`, i suoni e il danno `vtol` dell'esempio di partenza (`emg2`): sono file e definizioni di un altro gioco che qui potrebbero non esistere. Vanno aggiunti quando ci sono i file giusti.

L'unità non può mirare se `weapons` manca, anche se il Lua definisce `AimWeapon`.

## Script Lua delle unità

I pezzi si animano da `scripts/base/NOME.lua`: non serve Skeletor\_S3O. Le chiamate e le funzioni di seguito hanno funzionato nel motore (viste), salvo dove è detto.

**Chiamate disponibili**

| Chiamata | Uso |
| --- | --- |
| `piece('a', 'b')` | restituisce i pezzi per nome, che devono coincidere con quelli del modello |
| `Turn(pezzo, x_axis \| y_axis \| z_axis, angolo, velocità)` | ruota attorno all'origine del pezzo; angolo e velocità in radianti |
| `WaitForTurn(pezzo, asse)`, `Sleep(ms)` | attese |
| `StartThread(f)`, `Signal(maschera)`, `SetSignalMask(maschera)` | thread e segnali; le maschere sono bit (1, 2, 4, 8, 16) |
| `SetUnitValue(COB.INBUILDSTANCE, 1)` | segnala al motore che il costruttore sta costruendo |
| `Spring.Echo(testo)` | scrive nel log del motore |

**Funzioni che il motore richiama**

| Funzione | Cosa deve fare |
| --- | --- |
| `script.Create()` | inizializzazione; utile per un `Spring.Echo` di controllo |
| `script.StartMoving()`, `script.StopMoving()` | avvio e arresto della camminata |
| `script.AimFromWeapon(n)` | restituisce il pezzo da cui parte la mira dell'arma `n` |
| `script.QueryWeapon(n)` | restituisce il pezzo da cui esce il colpo dell'arma `n` |
| `script.AimWeapon(n, heading, pitch)` | gira verso il bersaglio e restituisce `true` quando ha finito |
| `script.FireWeapon(n)` | animazione dello sparo, per esempio il rinculo |
| `script.Killed(recentDamage, maxHealth)` | restituisce `1` |
| `script.StartBuilding()`, `script.QueryNanopiece()` | costruttori: il nome giusto ha la «p» minuscola; senza `INBUILDSTANCE` impostato non costruisce |

Un nome di chiamata sbagliato non dà errore evidente: controllare `infolog.txt`. L'arresto della costruzione non è stato osservato (da verificare).

**Segno delle rotazioni** (visto). Sull'asse x un angolo **negativo** porta il pezzo in avanti. Gli script usano una costante `FWD = -1` e moltiplicano per essa; se gambe e braccia vanno al contrario, si imposta `FWD = 1`. Il segno sugli altri assi non è stato verificato in modo sistematico.

**Camminata a quattro fasi** (vista, giudicata accettabile su un robot con gambe e braccia): un thread con maschera di segnale, che alterna le due gambe passando per una posa di passaggio, e braccia in controfase. Il piede si tiene piatto con l'angolo `a_ginocchio - a_coscia`.

```lua
local FWD, rad, STEP, SPD = -1, math.rad, 220, math.rad(170)
local function X(p, a) Turn(p, x_axis, FWD * rad(a), SPD) end
local function Leg(thigh, shin, foot, a_thigh, a_knee)
  X(thigh, a_thigh); X(shin, -a_knee); X(foot, a_knee - a_thigh)
end
local function Walk()
  SetSignalMask(1)
  while true do
    Leg(leg_l, shin_l, foot_l, 25, 5);  Leg(leg_r, shin_r, foot_r, -20, 10); Sleep(STEP)
    Leg(leg_l, shin_l, foot_l, 5, 0);   Leg(leg_r, shin_r, foot_r, 10, 40);  Sleep(STEP)
    Leg(leg_r, shin_r, foot_r, 25, 5);  Leg(leg_l, shin_l, foot_l, -20, 10); Sleep(STEP)
    Leg(leg_r, shin_r, foot_r, 5, 0);   Leg(leg_l, shin_l, foot_l, 10, 40);  Sleep(STEP)
  end
end
function script.StartMoving() Signal(1); StartThread(Walk) end
function script.StopMoving()  Signal(1); --[[ riportare i pezzi a 0 ]] end
```

**Mira con braccio e gomito** (vista). A riposo la canna punta in basso. La spalla gira sull'asse y di `heading`, il gomito alza l'avambraccio di 90° più `pitch`, così la canna resta sull'asse di mira. Un thread di riposo, con un proprio segnale, riporta il braccio giù dopo qualche secondo senza sparare.

```lua
function script.AimFromWeapon(n) return fore_r end   -- da dove parte la mira
function script.QueryWeapon(n)  return muzzle_r end  -- da dove esce il colpo
function script.AimWeapon(n, heading, pitch)
  Signal(SIG_AIM); SetSignalMask(SIG_AIM); Signal(SIG_REST)
  Turn(arm_r, x_axis, 0, AIM_SPD)
  Turn(arm_r, y_axis, heading, AIM_SPD)
  Turn(fore_r, x_axis, FWD * (rad(90) + pitch), AIM_SPD)
  WaitForTurn(arm_r, y_axis); WaitForTurn(fore_r, x_axis)
  StartThread(Rest); return true
end
function script.FireWeapon(n)   -- rinculo
  Turn(arm_r, x_axis, -FWD * rad(8), rad(900)); Sleep(60); Turn(arm_r, x_axis, 0, rad(240))
end
```

Con due armi (indici 1 e 2 in `weapons`) servono due coppie di segnali, una per arma, e le braccia non oscillano nella camminata finché stanno mirando. Il punto di tiro può essere un pezzo dedicato nella canna.

## Conversione di modelli esterni (FBX, OBJ)

Un modello fatto altrove (generatore AI, editor, scaricato) non è importabile in Recoil com'è. Le trasformazioni necessarie, con quanto è stato provato.

**Lettura dell'FBX binario 7.x** (visto: un parser in Python puro ha letto un FBX 7.4 con `struct`, `zlib` e `numpy`, senza importatore di Blender)

- Intestazione `Kaydara FBX Binary`, versione come intero a 4 byte all'offset 23.
- Nodi annidati. Per versioni sotto 7500 l'intestazione del nodo è di 13 byte (fine, numero di proprietà, lunghezza proprietà come interi a 4 byte, lunghezza del nome a 1 byte); da 7500 è di 25 byte con interi a 8 byte. Un nodo con fine 0 chiude la lista.
- Proprietà scalari `Y C F D I L`, array `f d i l b` (lunghezza, codifica, lunghezza compressa; zlib se la codifica è 1), stringhe `S`, dati grezzi `R`.
- Geometria in `Objects > Geometry`: `Vertices` (double, tre per vertice), `PolygonVertexIndex` (l'ultimo indice di ogni poligono è negato come `~i`), `LayerElementUV` con `UV` (coppie) e `UVIndex` (uno per angolo, `ByPolygonVertex` / `IndexToDirect`), `LayerElementNormal`, `LayerElementMaterial`. Il legame oggetti, materiali e texture sta in `Connections`.
- Per triangolare un poligono a più lati: ventaglio `(0, k, k+1)` sugli angoli, portandosi dietro gli indici UV dello stesso angolo.
- `GlobalSettings` dà `UpAxis`, `FrontAxis`, `UnitScaleFactor` (osservato 100). Non fidarsene per il fronte: guardare un'anteprima.
- OBJ: righe `v`, `vt`, `f v/vt/vn` con indici da 1, `vt` con origine in basso; un `o` per ogni oggetto. Valgono le stesse conversioni degli assi e della V.

**Controlli da fare subito sul file** (visti utili): numero di vertici e triangoli, ingombro in X Y Z, quante parti connesse, quanti vertici hanno una sola UV, quanta superficie UV è usata, quali texture esistono. Senza Blender, un renderer con z-buffer in `numpy` che campiona la texture con la stessa regola del motore (riga dall'alto = `v` × altezza, dopo il capovolgimento) mostra se UV e orientamento sono giusti prima di lanciare Blender.

**Cosa manca tipicamente a un modello da generatore AI** (visto su un caso: una mesh unica da 5370 triangoli, un materiale, una sola texture di colore da 2048×2048, nessuno scheletro)

| Problema | Perché | Strada |
| --- | --- | --- |
| Troppi triangoli | il budget va da 500 a 5000 | decimare non basta: quasi ogni vertice è su un bordo di UV (106 vertici su 2757 con una sola UV), quindi il collasso degli spigoli strappa la texture. Serve una nuova UV e il rifacimento (bake) della texture dall'alto al basso numero di poligoni in Blender. Non provato |
| Un solo pezzo | senza pezzi il Lua non può animare nulla | dividere la mesh in pezzi con un'origine su ogni giunto (sotto) |
| Nessun colore giocatore | il modello ha solo colori dipinti | ricavare l'alpha di tex1 dai pixel del colore da sostituire (sotto) |
| Nessuna tex2 | il motore ne vuole due | scrivere una tex2 neutra (R 0, G 128, B 0, A 255) |
| Texture troppo pesante | 2048² = 16 MB in memoria | media a blocchi 2×2 con `numpy`; 1024×1024 usato nelle prove |

**Dividere una mesh unica in pezzi** (provato fuori da Blender, visto in anteprima). Si stimano a mano i giunti da una vista frontale quadrettata. Ogni osso è uno o più segmenti `(x, y) → (x, y)` con un raggio. Ogni triangolo va all'osso per cui `distanza(centro del triangolo, segmento) − raggio` è minima, in proiezione frontale. Le parti staccate piccole (sotto circa 900 triangoli) prendono il pezzo di maggioranza, così uno spallaccio non si spezza. La z di ogni origine si ricava come media dei vertici del pezzo vicini al giunto. Limiti: assegnare per triangolo lascia il bordo frastagliato, e con rotazioni di oltre 15–20° compaiono piccole crepe (viste all'anca). Mesh non separate per le articolazioni vanno controllate in posa.

**Maschera del colore giocatore da una texture dipinta** (provata in anteprima, non nel motore). Si cerca il colore da rendere variabile, per esempio un rosso saturo:

```python
score = clip((r - max(g, b) * 1.6) / 0.18, 0, 1) \
      * clip((sat - 0.45) / 0.25, 0, 1) * clip((r - 0.22) / 0.15, 0, 1)
alpha = score * 255          # sat = (max - min) / max, canali in 0..1
```

Su un caso ha coperto circa il 5% della texture (spallaccio, occhio, scritte, una placca) e l'anteprima con il colore squadra applicato è risultata credibile. Per altri colori vanno adattate le soglie. Come il motore mescola il colore giocatore con il colore dipinto dove l'alpha è intermedio non è stato osservato.

## Diagnosi: sintomo, causa, soluzione

Problemi incontrati nella catena e come si sono risolti. Le righe senza soluzione sono ancora aperte.

| Sintomo | Causa | Soluzione |
| --- | --- | --- |
| Modello tutto bianco in Blender | con Blender in italiano il nodo materiale si chiama «Generico BSDF» e la ricerca per nome inglese fallisce | cercare il nodo per tipo, `BSDF_PRINCIPLED` (visto) |
| Colori persi dove l'alpha è 0 | Blender azzera l'RGB quando salva un PNG con alpha | scrivere i PNG a mano con `struct` e `zlib` (visto) |
| Comando di esportazione grigio, non cliccabile | manca la radice S3O | crearla con `add_s3o_root` e renderla attiva (visto) |
| Modello sdraiato, poi al contrario | rotazione della radice S3O e fronte invertito | yaw di 180° sul pezzo radice e `matrix_parent_inverse` (visto) |
| Modello minuscolo | scala | scalare le coordinate fino a `target_height` prima di creare gli oggetti (visto) |
| Texture non caricate | nomi delle texture vuoti nel `.s3o` | passare i nomi esatti a `add_s3o_root` (visto) |
| Colori capovolti nel motore | il motore mostra le texture capovolte rispetto a Blender | `v = 1 − v_su` nelle UV (visto) |
| Colore giocatore sulle zone sbagliate | si credeva alpha bassa = colore giocatore | alpha **alta** = colore giocatore (visto) |
| Costruttore che non costruisce | `script` diverso dal nome del file Lua, nome di chiamata sbagliato, `INBUILDSTANCE` non impostato | nomi coerenti, `QueryNanopiece` con la p minuscola, `SetUnitValue(COB.INBUILDSTANCE, 1)` in `StartBuilding` (visto nel log). Costruzione effettiva non confermata |
| Script che non parte, nessun errore nel log | `script` della definizione ≠ nome del file | farli coincidere; verificarlo con un `Spring.Echo` in `Create` (visto) |
| L'unità non spara né mira | la definizione non ha `weapons` | aggiungere `weapondefs` e `weapons`; `AimWeapon` deve restituire `true` (visto) |
| Gambe e braccia vanno al contrario | segno sull'asse x | `FWD = -1`, oppure `1` se serve (visto) |
| Camminata a due pose, poco credibile | poche fasi | quattro fasi con posa di passaggio e ginocchio che si piega (vista, giudicata accettabile) |
| Braccia o pezzi staccati dal corpo | le parti non si sovrappongono ai giunti | avvicinare la catena del braccio al busto e aggiungere un pezzo di giunto, nel pezzo che ruota (visto in anteprima) |
| Crepe ai giunti quando i pezzi ruotano | divisione per triangolo con bordo frastagliato | ridurre le ampiezze, sovrapporre le parti, o tagliare su un piano (visto in anteprima) |
| Pezzo che sembra vuoto o interno | ordine dei vertici invertito | orientare ogni faccia verso l'esterno con la normale di Newell rispetto al centro del pezzo (prassi usata; il motore potrebbe non disegnare le facce rovesciate, da verificare) |
| `SyntaxError` nello script generato | un apostrofo dentro una stringa tra apici | non usare apostrofi nei testi inseriti nel codice generato (visto) |
| Piedi sotto il terreno | non accertata: forse volume di collisione o origine della radice | aperto: provare `/debugcolvol` e portare il punto più basso a quota 0 |
| Braccio di costruzione al contrario, camminata scadente | non accertata | aperto |

## Licenze, prestazioni e punti aperti

**Licenze**

- Il motore Recoil è GPL v2 (dichiarato). Il codice dei giochi deve essere compatibile con la GPL.
- Il codice di BAR è GPL v2: gli script Lua ispirati a BAR si possono riusare (il responsabile l'ha autorizzato), ma il gioco deve avere una licenza compatibile con la GPL. Punto aperto per il progetto.
- Le texture `Arm_*` di BAR sono CC-BY-SA 4.0 (autore: Cremuss). Modelli, animazioni e il resto sono CC-BY-NC-ND (autore: Beherith): **non si riusano** (visto nei file di licenza di BAR).
- Per ogni risorsa esterna (kit di parti, modello scaricato, texture) segnalare la licenza e chiedere conferma prima di riusarla. «Usato da più giochi» non è una licenza: serve il testo.
- I modelli prodotti da generatori AI hanno condizioni che dipendono dal piano del servizio usato: da verificare caso per caso.

**Prestazioni.** Il budget di triangoli e l'obiettivo di unità sono nella sezione sul formato. Per i primi test il modello sta tra 500 e 1000 triangoli; sopra questo limite, dichiarare il conteggio reale e chiedere prima di consegnare.

**Punti aperti da verificare**

- [ ] Significato esatto dei quattro canali di tex2, nelle fonti del motore.
- [ ] Come il motore mescola il colore giocatore con il colore dipinto dove l'alpha di tex1 è intermedia.
- [ ] Nove materiali di fazione in due sole texture, e zone del colore giocatore per fazione.
- [ ] Raggio e altezza di collisione della radice S3O (oggi ai valori predefiniti); impronta 2×2 adeguata ai robot larghi.
- [ ] Piedi sotto il terreno e braccio di costruzione al contrario su un bipede costruttore; costruzione effettiva di un costruttore cingolato.
- [ ] Uno strumento per vedere un modello senza partita completa.
- [ ] Skeletor\_S3O su Blender 5.x; glTF e Collada nel motore.
- [ ] Conversione delle texture in DDS DXT5 e uso di atlas condivisi per fazione.
- [ ] Normali lisce al posto delle facce piatte; pezzi senza geometria.
- [ ] Lettura di una JPG con `bpy.data.images` dentro Blender; presenza di `PIL` e `scipy` nel suo Python.
- [ ] Esplosioni e suoni delle armi: file e definizioni che mancano.
- [ ] Riduzione del numero di triangoli di una mesh con UV per faccia, con rifacimento della texture.
