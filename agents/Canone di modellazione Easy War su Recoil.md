# Canone di modellazione Easy War su Recoil

Nov 10, 2026 · @bio

## Scopo e regole d'oro

Questo canone fissa come si produce un'unità di Easy War su Recoil: un solo nome, uno script, nessun lavoro a mano in Blender. Ogni punto porta il suo livello di prova: **visto** (in un output o nel motore), **dichiarato** (dal responsabile), **da provare**.

1. **Un'unità, un nome.** Lo stesso nome vale per lo script Python, il modello, le due texture, lo script Lua e la definizione dell'unità.
2. **Niente modellazione manuale.** Forme, texture, root S3O, export e consegna nel gioco sono prodotti dallo script. Il responsabile non apre Blender.
3. **Il motore è il giudice.** Ciò che si vede in Blender non basta: le texture risultano capovolte e il fronte opposto rispetto al motore.
4. **Si dichiara il conteggio reale** dei triangoli di ogni modello, e il livello di prova di ogni affermazione.

## Nomi e percorsi

Ogni file dell'unità `NOME` ha un posto fisso dentro `easywar.sdd` e porta lo stesso nome. I percorsi nella definizione sono relativi alle cartelle del motore.

| Elemento | Percorso in `easywar.sdd` | Come lo richiama il resto | Prova |
| --- | --- | --- | --- |
| Script di generazione | `easywar_work/base/NOME.py` | il nome del file è il nome dell'unità | visto |
| Libreria comune | `easywar_work/easywar_lib.py` | importata dagli script delle unità | visto |
| File di lavoro (`.blend`, copie) | `easywar_work/base/out/` | non entra nel repository | visto |
| Modello | `objects3d/base/NOME.s3o` | `ObjectName = "base/NOME.s3o"` | visto |
| Texture | `unittextures/NOME1.png`, `NOME2.png` | nome semplice scritto nel root S3O | visto |
| Script di animazione | `scripts/base/NOME.lua` | `script = "base/NOME.lua"` | visto |
| Definizione unità | `units/base/NOME.lua` | nome dell'unità = `NOME` | visto |

Se il campo `script` della definizione non coincide col file Lua, il motore non carica lo script e l'animazione non parte, senza errori nel log \[visto: era la causa del costruttore che non costruiva\]. Va in `.gitignore` solo `easywar_work/`.

Il `NOME` delle unità del pool base porta il prefisso `___` (per esempio `___bot`), accettato dal motore sia nel file sia nel nome dell'unità \[visto dal responsabile\]. I modelli di prova (`soldier`, `constructor`, `engineer`, `k116`, `plasma_bot_lego_1`, `square_bot_lego_1`, `mech_lego_1`, `mech_script_1`) hanno nomi non canonici: quando diventano unità vere si rigenerano con il nome del pool base.

## Pipeline di generazione

Un solo comando genera, esporta e consegna: Blender gira da riga di comando e non va aperto. Blender 5.2.0 LTS (Flatpak) con S3O Kit 0.3.2 \[visto\].

1. Lo script `NOME.py` costruisce i pezzi con `easywar_lib.Builder`: forme in coordinate Blender, UV per zona, due texture PNG, materiale.
2. La libreria applica la scala globale e la rotazione del fronte, crea la radice S3O con l'operatore `s3o_tools.add_s3o_root` e collega i pezzi.
3. Esporta con `s3o_tools.export_s3o` in `easywar_work/base/out/`.
4. Scrive il Lua e copia i quattro file (modello, due texture, Lua) nelle cartelle del gioco. Per ciascuno stampa `creato` o `sovrascritto`.

Comando, in una riga sola (svuotare prima la riga del terminale con Ctrl+C):

```
flatpak run org.blender.Blender --background --python /home/p/.spring/games/easywar.sdd/easywar_work/base/NOME.py | grep -E "S3O_ROOT|DEPLOY|TRIANGOLI"
```

**Riuscito** se compaiono `COLLEGAMENTI 2`, `S3O_ROOT export` con una dimensione maggiore di zero, quattro righe `DEPLOY` e `TRIANGOLI` con il conteggio reale.

Parametri opzionali come JSON dopo `--` (per esempio `-- '{"scale":12,"deploy":false}'`): `scale`, `yaw_deg`, `flip_v`, `bevel`, `cyl_segments`, `deploy`, `dir_model`, `dir_textures`, `dir_script`. Con `deploy: false` genera solo in `out/`.

Il bot `soldier` usa ancora la prima versione dello script (`genera_bot.py`, con il nome come parametro dopo `--`): da migrare alla libreria.

## Varianti di produzione

Tre varianti, tutte arrivate nel motore con la stessa catena (script, export, texture, Lua, consegna). La scelta della variante standard spetta al responsabile.

| Variante | Fonte delle forme | Unità provate | Prova |
| --- | --- | --- | --- |
| A. Primitive con libreria | Scatole smussate e cilindri costruiti da `easywar_lib.Builder`, atlante a quattro zone | `soldier` (prima versione autonoma), `constructor`, `engineer` | visto |
| B. Forme facettate da una sagoma | Profilo frontale più profondità, con loft ed estrusione; coordinate scritte nello script, fedeli al disegno. Oggi non usa `easywar_lib` e duplica le funzioni comuni | `mech_script_1` | anteprima vista, partita da confermare |
| C. Ricetta di pezzi del kit | Pezzi del kit Kaiser's Legos (`easywar_work/legos/legosv2.obj`, atlas dipinto `lego2skin2048_2-2.png`) scelti, stirati a misura e montati da una ricetta | `k116`, `plasma_bot_lego_1`, `square_bot_lego_1`, `mech_lego_1` | visto |

Kaiser's Legos è libero da usare. Il catalogo delle 116 forme del kit (dimensioni, triangoli, nomi degli oggetti) è in `kaiser_legos_catalogo.png` e `.json`.

**Ciclo di lavoro per unità:** disegno di riferimento del responsabile, poi da una a tre anteprime da approvare, poi lo script, poi la prova in partita. Senza riferimento la ricetta esce brutta \[visto\]. Una variante di una ricetta già fatta costa poco: `mech_lego_1` ha richiesto circa 10 minuti partendo da `square_bot_lego_1`.

## Orientamento, scala e pezzi

Il modello si costruisce dritto in Blender e la libreria applica due correzioni fisse, confermate nel motore.

- **Verso alto e fronte.** Si disegna con Z in alto e il fronte verso -Y. La libreria ruota il pezzo radice di 180° attorno alla verticale (`yaw_deg`): senza, il bot camminava all'indietro \[visto nel motore\].
- **Radice S3O.** L'operatore `s3o_tools.add_s3o_root` crea una radice ruotata di (90°, 180°, 0) e due vuoti (`.height`, `.midpoint_and_collision_radius`). Il pezzo radice diventa suo figlio con la matrice inversa, che annulla la rotazione: senza, il modello appariva sdraiato a faccia in giù \[visto in Blender e nel motore\].
- **Scala.** Moltiplicatore globale 10 (`scale`): il bot soldato misura circa 36 unità d'altezza e la dimensione è giudicata buona \[dichiarato\]. La definizione dell'unità deve avere un volume di collisione coerente (il costruttore, largo circa 26 e lungo circa 34, ha `collisionVolumeScales = "26 20.5 34.5"`) \[visto\]. Il raggio e l'altezza del root S3O sono ancora ai valori predefiniti (20 e 40).
- **Gerarchia.** Un solo pezzo radice, nomi unici in minuscolo, suffissi `_l` e `_r` per i lati, origine di ogni pezzo nel suo punto di rotazione (anca, ginocchio, base della torretta) \[da provare nelle camminate\].

Nomi standard dei pezzi (proposta): `base`, `torso`, `head`, `turret`, `barrel`, `leg_l`/`leg_r`, `shin_l`/`shin_r`, `foot_l`/`foot_r`, `track_l`/`track_r`, `arm_base`, `arm`, `nano`, `plate_l`/`plate_r` (zona colore squadra), `sensor`, `light_l`/`light_r`, `stack`. Gli stessi nomi si usano in `piece('...')` nel Lua.

## Texture

Ogni unità ha esattamente due texture PNG, `NOME1.png` (colore) e `NOME2.png` (dati), in 256 × 256 pixel, generate dallo script senza dipingere nulla.

- **tex1: colore e alpha.** L'alpha è la maschera del colore giocatore: dove l'alpha è alta il motore mette il colore della squadra, dove è zero resta il colore della texture \[visto nel motore: la targa sul dorso diventa rossa\].
- **Atlante a quattro zone**, una per quadrante: `armor` (grigio azzurro), `dark` (quasi nero), `team` (alpha alta, colore giocatore), `accent` (arancio). Ogni pezzo usa una sola zona. Il colore giocatore e il colore di fazione convivono in zone diverse \[visto\].
- **V capovolta.** Nel motore le texture appaiono ribaltate in verticale rispetto a Blender, quindi le UV si ribaltano (`flip_v`): l'anteprima in Blender risulta capovolta e fa fede il motore \[visto: con le UV non ribaltate il rosso finiva su torso e gambe\].
- **tex2: dati.** Ipotesi: canale R luminosità propria, G riflessione \[da verificare nelle fonti\]. Per ora la zona `accent` ha luminosità propria 0,6.
- **Nomi nel modello.** I nomi `NOME1.png` e `NOME2.png` sono scritti nei campi `texture_name_1` e `texture_name_2` del root S3O; i file stanno in `unittextures/` e il motore li trova per nome semplice \[visto\].
- **Come si scrivono i PNG.** A mano, byte per byte: il salvataggio di Blender azzera il colore dove l'alpha è zero e la tex1 usciva quasi tutta bianca \[visto\].

**Nove materiali in due texture** (uno per fazione) resta aperto: si propone di tenere lo stesso atlante a quattro zone e variare la palette per fazione, ma non è deciso né provato.

## Animazione e script Lua

Le animazioni sono script Lua per unità, generati dallo stesso script Python dell'unità, così i nomi dei pezzi non possono divergere. Il gadget degli script Lua è caricato dal gioco \[visto nel log: `Lua unit script framework`\].

- **Funzioni del motore** (wiki di Recoil): `script.Create`, `script.StartMoving`, `script.StopMoving`, `script.StartBuilding(heading, pitch)`, `script.StopBuilding`, `script.QueryNanopiece` (p minuscola) \[wiki\]. Il costruttore deve impostare `SetUnitValue(COB.INBUILDSTANCE, 1)` in `StartBuilding` e 0 in `StopBuilding`, altrimenti non inizia a costruire \[wiki\].
- **Convenzioni.** Angoli in radianti. Assi numerici 1 = x, 2 = y (verticale), 3 = z; negli script di BAR il segno sull'asse 3 è invertito \[visto in `armcom`\]. Le gambe ruotano sull'asse x, con il ginocchio in verso opposto alla coscia e il piede che compensa \[visto in `armcom`, `armmar`\].
- **Collegamento.** Il campo `script` della definizione deve coincidere col file in `scripts/base/`. Per diagnosi, il Lua può scrivere nel log con `Spring.Echo('[easywar] ...')` e si cerca con `grep -a "\[easywar\]" ~/.spring/infolog.txt`.
- **Avanti.** Sull'asse x un angolo negativo porta il pezzo in avanti (costante `FWD = -1`) \[visto nella camminata di `square_bot_lego_1`\].
- **Armi.** Per ora stanno dentro la definizione dell'unità (`weapondefs` più `weapons`), come soluzione provvisoria. A riposo la canna punta in basso; quando mira, il braccio o il gomito si alza in avanti di 90° più l'inclinazione del bersaglio, così la canna resta sull'asse di mira \[visto in `square_bot_lego_1` e `mech_lego_1`\]. Mancano generatori di esplosione e suoni.

Stato delle animazioni:

| Unità | Animazione | Esito |
| --- | --- | --- |
| `soldier` | torretta che gira di continuo | funziona \[dichiarato\] |
| `soldier` | camminata a due pose | ondeggia male \[dichiarato\]; va riscritta con più pose, pelvi e piedi |
| `constructor` | braccio che si alza e ruota durante la costruzione | chiamate di costruzione viste nel log; costruzione effettiva da confermare in partita |

## Budget di poligoni e stato dei test

Il budget indicato dal responsabile, non verificato \[dichiarato\]: unità di spam circa 500 triangoli, unità di basso livello meno di 1000, di rango 1000-2000, enormi e iconiche fino a 5000. Per i primi test il modello sta tra 500 e 1000. Il conteggio dichiarato è sempre quello reale stampato dallo script.

| Unità | Approccio | Triangoli | Nel motore | Animazione |
| --- | --- | --- | --- | --- |
| `soldier` (bot d'attacco) | script Python procedurale | 556 \[visto\] | visibile, scala giusta, colori corretti, fronte corretto \[dichiarato\] | torretta ok, camminata da rifare |
| `constructor` (veicolo a cingoli) | stesso approccio, libreria condivisa | non misurato | visibile, texturato, si muove \[dichiarato\] | costruzione da provare |
| engineer (bipede costruttore) | A, libreria condivisa | circa 856, stima | caricato; piedi sotto il terreno, braccio di costruzione al contrario \[dichiarato\] | camminata scadente; correzioni rinviate dal responsabile |
| k116 (mech del kit com'è) | C, kit importato | 1.280 (test di importazione, fuori budget) | visto: piedi a terra, colore squadra sulle spalle | nessuna |
| plasma\_bot\_lego\_1 | C, ricetta | 712 | visto, funziona; design giudicato brutto | non valutata |
| square\_bot\_lego\_1 (27 pezzi) | C, ricetta | 388 | visto; il più riuscito | camminata e mira con due armi giudicate "non brutte" |
| mech\_lego\_1 | C, ricetta | 512 | visto, "ho visto di peggio" | due armi nella definizione |
| mech\_script\_1 | B, sagoma facettata | 852 | anteprima vista; braccia staccate corrette, partita da confermare | due armi nella definizione |

Il budget è rispettato da tutti i modelli tranne `k116`. Costo misurato (report della toolchain, 12 novembre): dal disegno allo script con animazioni servono 30-60 minuti di conversazione e circa 1 milione di token equivalenti per unità. Il collo di bottiglia è il tempo del responsabile per riferimenti e anteprime, non la tecnica.

## Trappole note

Problemi incontrati davvero, con la soluzione adottata. Chi scrive un nuovo script li controlla prima.

- **S3O Kit da zip.** Il file `SpringModelingTemplate.blend` nello zip è un puntatore Git LFS di 134 byte; il file vero pesa 285.633.681 byte e reinstallando dallo zip il problema ritorna \[dichiarato\].
- **Il root S3O è obbligatorio.** Senza l'oggetto creato da "Add S3O Root" l'export è grigio e non parte. Lo script lo crea e lo collega da solo \[visto\].
- **Blender in italiano.** I nodi dei materiali hanno nomi tradotti ("Generico BSDF"): si cercano per tipo, non per nome. Cercare "Principled BSDF" non trovava il nodo e il modello restava bianco \[visto nel file\].
- **PNG con alpha a zero.** Il salvataggio di Blender azzera il colore dove l'alpha è zero: i PNG si scrivono a mano \[visto\].
- **Script Lua con nome diverso dal campo `script`.** L'unità parte senza animazioni e senza errori nel log \[visto\].
- **Riga di comando sporca.** Incollando un comando sopra del testo già presente nel terminale, la shell esegue un miscuglio. Prima di incollare si preme Ctrl+C \[visto\].
- **File vecchi.** Se l'output manca di righe che la versione nuova stampa sempre (per esempio `DEPLOY`), si sta eseguendo lo script vecchio: si controlla con `grep -c DEPLOY` sul file \[visto\].
- **Blender non è nel PATH.** Si usa sempre `flatpak run org.blender.Blender` \[visto\].
- **Pezzi del kit difettosi.** Alcune forme di Kaiser's Legos sono gusci aperti o asimmetriche: si scelgono su un foglio di anteprima ravvicinata e si preferiscono le simmetriche \[visto\].
- **Ricetta senza riferimento.** Inventata senza un disegno del responsabile, la ricetta esce brutta: prima il riferimento e l'anteprima approvata, poi lo script \[visto\].

## Punti aperti e decisioni

Decisioni che spettano al responsabile e verifiche ancora da fare; il canone si aggiorna quando si chiudono.

- [ ] **Nove materiali in due texture.** Tenere l'atlante a quattro zone e variare la palette per fazione, oppure un atlante più grande. Rischi di stile già noti: sfere di Sigma contro Omega, esagoni di Delta contro Lambda, angoli di Gamma, Delta e Theta da lontano, reticoli di Lambda.
- [ ] **Canali di tex2.** Confermare nelle fonti il significato di R e G (luminosità propria, riflessione).
- [ ] **Costruzione.** Verificare che il costruttore costruisca e animi il braccio dopo la correzione del nome dello script; se il motore ha cambiato comportamento dalla versione in uso (`recoil_2026.07.04`), serve un controllo nelle note di rilascio.
- [ ] **Camminata.** Riscrivere quella del soldato con più pose, pelvi e piedi, tarando asse e segno nel motore.
- [ ] **Collisione.** Adattare raggio, altezza e punto medio del root S3O alle misure reali di ogni modello (ora ai valori predefiniti).
- [ ] **Costruttore e canone di design.** Il canone di design definisce `___con` come hover; i modelli di prova sono un cingolato (`constructor`) e un bipede (`engineer`). Decide il responsabile.
- [ ] **Migrazione del soldato** alla libreria condivisa.
- [ ] **Licenza.** Se si riusa codice dai Lua di BAR (GPL), il gioco deve avere una licenza compatibile con la GPL. Il responsabile ha dato il via libera; resta da annotare nel report.
- [ ] **Variante standard.** Scegliere tra A, B (da portare dentro `easywar_lib`) e C, o una loro combinazione. Kaiser's Legos è libero da usare; artisti esterni, risorse di terzi e generatori a pagamento sono esclusi, glTF e Collada rinviati.
- [ ] **`.gitignore`.** Aggiungere `easywar_work/` al repository del gioco.
- [ ] **Strategia delle texture.** Due PNG da 256 per unità, oppure una texture condivisa per fazione come gli atlas 4096 di BAR: da decidere prima della produzione in serie, perché incide sulle prestazioni e sui nove materiali.
- [ ] **Nomi canonici.** Rigenerare con il prefisso `___` le unità di prova che diventano unità del pool base.
