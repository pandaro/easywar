# Easy War: report toolchain modelli (stato al 14 novembre 2026)

Nov 14, 2026 · @bio

## Esito in sintesi

Sono state provate nel motore tre varianti di produzione, tutte con la stessa catena (generazione in Blender senza interfaccia, esportazione `.s3o`, texture, script Lua, consegna nei percorsi del gioco). La variante D, con il modello fornito da un generatore AI, è stata impostata ma non ancora eseguita in Blender. Nessuna è scartata: qui sotto pregi e difetti di ciascuna, senza una raccomandazione. La scelta spetta al responsabile.

| Variante | Pregi | Difetti | Unità provate |
| --- | --- | --- | --- |
| A. Script con libreria condivisa (easywar\_lib, primitive: scatole smussate) | Nessuna licenza esterna. Funzioni comuni scritte una sola volta (radice S3O, export, UV, zone texture, consegna). Colore squadra già gestito a zone | Forme limitate alle primitive della libreria, estetica semplice. Il soldier è un primo script autonomo che non la usa | soldier, constructor, engineer |
| B. Script puro autonomo con forme facettate (loft ed extrude) | Nessuna licenza esterna. Forme angolari ricavate da un disegno (sagoma frontale più profondità), fedeli al riferimento. Texture procedurale a 4 zone. 852 triangoli | Le forme si descrivono a coordinate dentro lo script, a ogni modello. Oggi non usa easywar\_lib, quindi duplica funzioni. Prima versione con braccia staccate, corretta e da confermare in partita. Texture molto semplice | mech\_script\_1 |
| C. Kit di parti Kaiser's Legos (ricetta di pezzi stirati a misura) | Texture dipinte a mano e forme già modellate. Resa migliore secondo le prove. Un mech da ricetta già pronta in circa 10 minuti di conversazione | Licenza non verificata (testo non visto). Alcune forme del kit sono gusci aperti o asimmetriche e vanno scelte con cura. Stile fissato dal kit: per nove fazioni servirebbe estenderlo o duplicarlo (fattibilità studiata, non decisa) | k116, plasma\_bot\_lego\_1, square\_bot\_lego\_1, mech\_lego\_1 |
| D. Modello da generatore AI (Tripo), da disegni di progetto, convertito in unità con uno script | Qualità visiva alta, con dettaglio dipinto nella texture (nell'anteprima fatta da noi). Il responsabile riferisce che il modello arriva texturizzato in poco tempo a partire da disegni progettuali e che si importa facilmente in Blender (dichiarato, non osservato) | Mesh unica da 5.370 triangoli, sopra il budget di 500–1000 e appena sopra il tetto di 5000 delle unità iconiche. Un solo pezzo: per animare va diviso (piccole crepe ai giunti in posa). Solo texture di colore: manca l'alpha del colore squadra e manca tex2. UV per faccia: ridurre i triangoli richiede una nuova UV e il rifacimento della texture. Costo del servizio e licenza dei modelli da definire | Un modello del responsabile (mech\_robot\_3d\_model) con lo script tripo\_mech\_1: lettura, divisione in pezzi, texture e anteprima provate fuori da Blender. Non eseguito in Blender né nel motore |

## Approcci e modelli collaudati

Sono stati collaudati due approcci su otto modelli, con tre varianti di produzione. Il generatore AI (approccio 6) è stato impostato su un modello e non è ancora stato eseguito in Blender. Gli altri approcci sono stati esclusi o rinviati dal responsabile.

| Approccio | Esito | Motivo o nota |
| --- | --- | --- |
| 1. Script Python in Blender (primitive con libreria; forme facettate autonome) | Collaudato, funziona | Pipeline completa senza interfaccia, vista nel motore |
| 2. Kit di parti riusabili (Kaiser's Legos) | Collaudato, funziona | Resa migliore. Licenza: il responsabile riferisce che il kit è usato da più giochi, testo non visto |
| 3. Risorse da terzi con licenza compatibile | Escluso dal responsabile | Darebbe una raccolta di modelli dallo stile incoerente |
| 4. Artista esterno | Escluso | Nessun budget |
| 5. Formati alternativi (glTF, Collada) | Rinviato | Il responsabile riferisce che il supporto nel motore è agli inizi |
| 6. Generatore AI esterno (Tripo) | Impostato, non eseguito in Blender | Il responsabile riferisce che Tripo dà un modello facilmente importabile in Blender, di ottima qualità e texturizzato in poco tempo a partire da disegni progettuali (dichiarato). In precedenza era escluso per costo. Costo del servizio e licenza dei modelli da definire |

**Modelli prodotti** (stile neutro, nessuna fazione, ordine cronologico):

| Unità | Approccio | Triangoli | Esito nel motore |
| --- | --- | --- | --- |
| soldier (bot d'attacco) | 1 | 556 | Visto. Scala, orientamento e colori giusti, torretta che gira. Camminata scadente |
| constructor (cingolato) | 1 | non misurato | Caricato, texturato, si muove. Chiamate di costruzione viste nel log. Costruzione effettiva non confermata |
| engineer (bipede costruttore) | 1 | circa 856, stima | Caricato. Piedi sotto il terreno, braccio di costruzione al contrario, camminata scadente |
| k116 (mech del kit com'è) | 2 | 1.280 | Visto. Piedi a terra, colore squadra sulle spalle. Nessuna animazione |
| plasma\_bot\_lego\_1 | 2 | 712 | Visto, "funziona". Design giudicato brutto |
| square\_bot\_lego\_1 (27 pezzi) | 2 | 388 | Visto. Camminata e mira giudicate "non brutte". Il più riuscito |
| mech\_lego\_1 (con due armi) | 2 | 512 | Visto, "ho visto di peggio". Due armi definite dentro la definizione dell'unità |
| mech\_script\_1 (script puro, da disegno) | 1 | 852 | Anteprima vista dal responsabile: braccia staccate dal corpo, resto ok. Correzione applicata, esito in partita da confermare. Due armi nella definizione dell'unità |
| tripo\_mech\_1 (modello Tripo del responsabile) | 6 | 5.371 | Script scritto. Lettura dell'FBX, divisione in pezzi, texture con colore squadra e anteprima provate fuori da Blender. Non eseguito in Blender né nel motore |

Il budget di 500–1000 triangoli è rispettato da tutti tranne k116, che ne ha 1.280 ed era un test di importazione, e tripo\_mech\_1, che ne ha 5.371 perché il modello Tripo non è stato ridotto.

## Scalabilità a cento modelli

Il metodo regge tecnicamente per cento modelli. Il collo di bottiglia è il tempo del responsabile per dare i riferimenti e giudicare le anteprime, non la tecnica.

**Costo misurato in questa sessione:**

- Un'unità dal disegno allo script con animazioni richiede 30–60 minuti di conversazione. Il square bot ha richiesto circa 40 minuti, il mech circa 10 minuti partendo dalla ricetta del square bot.
- Il consumo è di circa 1 milione di token equivalenti per unità. L'intera sessione, quattro giornate, ne ha consumati circa 10,4 milioni, la maggior parte per contesto riletto. I costi in euro dipendono dal piano e non sono stati verificati.
- Il lavoro richiesto al responsabile per unità è: un'immagine di riferimento, il giudizio su 1–3 anteprime, un comando da lanciare e una prova in partita.

**Proiezione per cento unità** (stima, non misura): 50–100 ore di conversazione e circa 100 milioni di token equivalenti. Si riduce se più unità condividono una ricetta, perché le varianti di una ricetta costano poco.

**Con modelli Tripo** (impostazione, nessuna misura): il responsabile riferisce che ogni modello arriva in poco tempo da disegni progettuali (dichiarato). Per ogni modello resta da fare la conversione: stimare i giunti per dividere la mesh in pezzi, adattare la maschera del colore squadra ai colori del modello e scrivere il Lua. La riduzione dei triangoli non è risolta. Tempo e token per modello non sono stati misurati; il costo del servizio non è stato indicato.

**Ripiego a cubi:** costa quasi zero: lo script delle primitive lo produce già. Il metodo a ricetta gli si avvicina, perché i pezzi del kit stirati a misura sono di fatto cubi texturati.

**Chi produce l'arte finale:** Claude, con script e ricetta, sui riferimenti del responsabile. Non c'è budget per un artista. Il responsabile indica Tripo, un generatore AI, come fonte possibile del modello a partire da suoi disegni progettuali, con la conversione in unità fatta da Claude con uno script; il costo del servizio non è stato indicato. Con le varianti A, B e C la qualità attesa è "da prototipo curato", non da gioco commerciale. Con Tripo il responsabile riferisce una qualità ottima (dichiarato); nell'anteprima il dettaglio dipinto è alto, ma l'aspetto nel motore e il rispetto del budget di triangoli non sono ancora verificati.

## Stato per strumento

Tutta la catena di produzione funziona senza aprire l'interfaccia di Blender. Livelli: **visto** = osservato nell'output o nel motore; **dichiarato** = riferito o scritto in una fonte, non osservato; **da provare** = non ancora tentato.

| Strumento | Stato | Livello |
| --- | --- | --- |
| Blender 5.2 Flatpak, senza interfaccia (`--background --python`) | Genera, esporta e salva il `.blend` | visto |
| S3O Kit 0.3.2: `s3o_tools.add_s3o_root` | Crea la radice S3O con i nomi delle due texture (`texture_name_1`, `texture_name_2`) | visto |
| S3O Kit 0.3.2: `s3o_tools.export_s3o` | Esporta il `.s3o` da script | visto |
| Recoil, script Lua delle unità | Create, StartMoving, StartBuilding, AimWeapon e altre chiamate funzionano | visto |
| Skeletor\_S3O | Esporta animazioni sia in BOS/COB sia in Lua (LUS, LUS Tween). Compatibile con Blender fino a 4.3 LTS. Fonte: README letto su un mirror del repository di Beherith | dichiarato |
| Skeletor\_S3O su Blender 5.x | Non necessario: le animazioni sono scritte direttamente in Lua | da provare |
| Visualizzatore di modelli senza partita | Non trovato. Il test si fa caricando l'unità in partita | da provare |
| `/debugcolvol` (volumi di collisione) | Comando citato per l'engineer | da provare |
| Importazione dell'FBX di Tripo in Blender | Il responsabile riferisce che è semplice. Non osservata: l'FBX è stato letto con un parser Python proprio, senza importatore di Blender | dichiarato |
| Parser FBX binario 7.4 negli script | Legge vertici, triangoli e UV di un FBX di Tripo e lo scrive in pezzi, con texture e anteprima. Provato fuori da Blender | visto |
| tripo\_mech\_1.py in Blender e nel motore | Non ancora eseguito: lettura della JPG, esportazione S3O, giunti e colore squadra da verificare | da provare |

Skeletor\_S3O non serve solo per COB/BOS: genera anche script Lua. Serve per animare con i fotogrammi chiave in Blender, cosa che il responsabile non intende fare a mano.

## Fatti tecnici acquisiti

Queste regole sono già dentro gli script e nel documento "Canone di modellazione Easy War su Recoil" ([link](https://claude.ai/artifact/MLTiWTVWoGrWMBu6xyCfBH)).

Base tecnica completa per gli agenti che convertono, texturizzano o scriptano modelli: [Recoil, S3O e Blender: base tecnica per agenti](https://claude.ai/artifact/4QCwpNBJxXibxuL1ye2fJf).

**Formato e orientamento**

- Il modello si costruisce in Blender con Z verso l'alto e il fronte verso −Y. Il pezzo radice viene poi ruotato di 180 gradi. La radice S3O è ruotata di suo, e il figlio la compensa con l'inversa del genitore. *Visto.*
- Scala: il soldier è alto circa 36 unità. I robot dal kit sono alti 30–34 unità. *Visto.*
- Ogni pezzo ha un nome unico. La gerarchia ha le origini sulle articolazioni, pronte per animare.

**Texture**

- Il motore mostra le texture capovolte in verticale rispetto a Blender, quindi la coordinata V delle UV va invertita. *Visto.*
- tex1: RGB per i colori. Il canale alpha **alto** fa comparire il colore del giocatore, non quello basso. *Visto.*
- Blender, se salva un PNG, azzera il colore dove l'alpha è 0. Per questo i PNG sono scritti a mano dallo script. *Visto.*
- tex2: secondo il responsabile gestisce le proprietà fisiche e luminose nei canali RGBA. Nell'atlas Arm di BAR il rosso ha macchie sparse (bagliore?) e il verde un grigio diffuso (riflessione?). Il significato preciso dei canali è *da verificare*.
- I nomi delle texture vanno scritti dentro il `.s3o`, e i file stanno in `unittextures/`. *Visto.*
- In BAR tex1 e tex2 sono atlas 4096×4096 DXT5 condivisi da tutta una fazione. Il formato lo consente anche a noi. *Visto nei file BAR.*

**Script Lua delle unità**

- Il campo `script` della definizione dell'unità deve coincidere con il nome del file Lua. Se non coincide, lo script non viene caricato e nel log non compare nessun errore. *Visto.*
- I costruttori devono impostare `SetUnitValue(COB.INBUILDSTANCE, 1)` in StartBuilding. Il nome corretto è `QueryNanopiece`, con la p minuscola. *Visto nel log.*
- Sull'asse x un angolo negativo porta il pezzo in avanti (costante `FWD = -1`). L'ho dedotto dall'engineer e la camminata del square bot lo conferma. *Visto.*
- Le armi possono stare dentro la definizione dell'unità (`weapondefs` + `weapons`). A riposo l'arma punta in basso, e quando mira il braccio si alza in avanti di 90 gradi più l'inclinazione del bersaglio, così la canna resta sull'asse di mira.

**Licenze**

- Kaiser's Legos: il responsabile lo considera usabile per i test perché è usato da più giochi. Il testo della licenza non è stato visto.
- BAR: le texture Arm sono CC-BY-SA 4.0 (Cremuss). Modelli, animazioni e il resto sono CC-BY-NC-ND (Beherith): non si possono riusare. *Visto nei file di licenza BAR.*
- Il codice di BAR è GPL v2, e il motore richiede codice dei giochi compatibile con la GPL. Gli script Lua ispirati a BAR sono quindi possibili, ma il gioco deve avere una licenza compatibile.

**Modelli da generatore AI (Tripo)**

- Il responsabile riferisce che Tripo dà un modello facilmente importabile in Blender, di ottima qualità e texturizzato in poco tempo a partire da disegni progettuali. *Dichiarato.*
- Il file ricevuto è un FBX binario 7.4 con una JPG di colore da 2048×2048: una mesh, 5.370 triangoli, un materiale, nessuno scheletro; Y su, fronte +Z, altezza 1. *Visto.*
- Quasi ogni vertice è su un bordo di UV (106 vertici su 2.757 con una sola UV): ridurre i triangoli richiede una nuova UV e il rifacimento della texture in Blender. *Non provato.*
- Mancano l'alpha del colore squadra e tex2. Una maschera ricavata dai pixel rossi copre circa il 5% della texture e in anteprima dà un colore squadra credibile; il comportamento nel motore non è osservato.
- Per animare, la mesh si divide in pezzi assegnando ogni triangolo all'osso più vicino. In anteprima i pezzi tengono, con piccole crepe all'anca in posa di passo. *Visto fuori da Blender.*
- La licenza dei modelli generati dipende dal piano del servizio: *da verificare.*

## Problemi incontrati e soluzioni

Tutti i problemi della pipeline sono stati risolti. Restano aperti solo quelli di animazione e di design.

| Problema | Causa | Soluzione |
| --- | --- | --- |
| Modello tutto bianco in Blender | Con Blender in italiano il nodo materiale si chiama "Generico BSDF", e la ricerca per nome inglese fallisce | Cercare il nodo per tipo (`BSDF_PRINCIPLED`) |
| Colori persi dove alpha = 0 | Blender azzera l'RGB salvando il PNG | PNG scritti a mano dallo script |
| Export `.s3o` grigio, non cliccabile | Manca la radice S3O | Creata da script con `add_s3o_root` |
| Modello sdraiato, poi al contrario | Rotazione della radice S3O e fronte invertito | Compensazione con l'inversa del genitore e rotazione di 180 gradi del pezzo radice |
| Modello minuscolo | Scala | Scala globale 10 (primitive) o altezza obiettivo (kit) |
| Texture non caricate | Nomi delle texture vuoti nel `.s3o` | Nomi esatti passati a `add_s3o_root` |
| Colori sbagliati nel motore | V capovolta, alpha alta = colore giocatore | Inversione della V |
| Costruttore che non costruisce | Il campo `script` della definizione non coincideva con il nome del file Lua, più un nome di chiamata sbagliato | Nomi coerenti, `QueryNanopiece`, `INBUILDSTANCE` |
| Pezzi del kit storti o con buchi | Alcuni pezzi sono gusci aperti o asimmetrici | Scelta su un foglio di anteprima ravvicinata dei pezzi, uso di forme simmetriche |
| Design brutto al primo tentativo | Ricetta inventata senza riferimento | Disegno di riferimento del responsabile + anteprima approvata prima dello script |
| Modello Tripo con troppi triangoli | Mesh unica da 5.370 triangoli, con UV per faccia: quasi ogni vertice è su un bordo di UV, quindi la decimazione strappa la texture | Aperto. Strada indicata: nuova UV e rifacimento della texture in Blender, non provata |
| Modello Tripo senza pezzi e senza colore squadra | Mesh unica e solo texture di colore | Divisione in pezzi per vicinanza a ossa e maschera dai pixel rossi, viste in anteprima fuori da Blender. Piccole crepe ai giunti in posa |

## Punti aperti

Il punto più importante è la licenza del kit Kaiser's Legos: senza il testo, il kit resta solo per i test.

- [ ] Licenza di Kaiser's Legos: ottenere il testo o la conferma scritta dell'autore
- [ ] Licenza del gioco compatibile con la GPL, se si riusano script ispirati a BAR
- [ ] Significato dei canali RGBA di tex2: verificarlo nelle fonti del motore
- [ ] Nove materiali in due texture e zone del colore squadra per fazione
- [ ] engineer: piedi sotto il terreno (forse il volume di collisione), braccio di costruzione al contrario, camminata scadente. Il responsabile ha chiesto di non correggerli per ora
- [ ] soldier: camminata da rifare (oggi due pose). Il soldier e mech\_script\_1 non usano la libreria condivisa (il responsabile voleva mech\_script\_1 su easywar\_lib)
- [ ] constructor: confermare in partita che costruisca davvero
- [ ] Raggio e altezza di collisione nella radice S3O, oggi ai valori predefiniti. Impronta 2×2 forse piccola per i robot larghi
- [ ] Armi: oggi definite dentro la definizione dell'unità come soluzione provvisoria. Mancano il generatore di esplosione e i suoni
- [ ] Un visualizzatore di modelli senza partita completa
- [ ] Approccio 5 (glTF, Collada): rivalutarlo quando il supporto nel motore sarà maturo
- [ ] Kit proprio o per fazione: studio di fattibilità fatto in conversazione e non ancora deciso. Fattibile come libreria di forme generate da script, con il rischio principale nel design
- [ ] Aggiungere `easywar_work/` al `.gitignore` del gioco
- [ ] Eseguire tripo\_mech\_1.py in Blender e nel motore: lettura della JPG, esportazione S3O, giunti, colore squadra
- [ ] Tripo: costo del servizio e licenza dei modelli generati, secondo il piano usato
- [ ] Modelli Tripo: ridurre i triangoli (nuova UV e rifacimento della texture) oppure accettare i 5.370 per le unità iconiche

## File e script prodotti

Ogni script porta il nome dell'unità e produce da solo `NOME.s3o`, `NOME1.png`, `NOME2.png`, `NOME.lua` e la definizione `units/base/NOME.lua` (solo se manca), poi li consegna nel gioco. La cartella di lavoro è `easywar.sdd/easywar_work/`.

| File | Posizione | Cosa fa |
| --- | --- | --- |
| `genera_bot.py` | `easywar_work/bot_attacco/` | soldier, primo script autonomo (approccio 1) |
| `easywar_lib.py` | `easywar_work/` | Libreria condivisa per le primitive: zone texture, smussi, UV, radice S3O, export, consegna |
| `constructor.py` | `easywar_work/base/` | Costruttore cingolato, usa la libreria |
| `engineer.py` | `easywar_work/base/` | Bipede costruttore, usa la libreria, crea la definizione |
| `k116.py` | `easywar_work/base/` | Importa il K116 dal kit (approccio 2) |
| `plasma_bot_lego_1.py` | `easywar_work/base/` | Robot da ricetta di pezzi del kit |
| `square_bot_lego_1.py` | `easywar_work/base/` | Robot da ricetta, 27 pezzi, camminata e mira con due armi |
| `mech_lego_1.py` | `easywar_work/base/` | Robot da ricetta con le due armi dentro la definizione |
| mech\_script\_1.py | easywar\_work/base/ | Mech da script puro (loft ed extrude), autonomo, due armi nella definizione |
| `kaiser_legos_catalogo.png` / `.json` | consegnati in conversazione | Catalogo delle 116 forme del kit: dimensioni, triangoli, nomi degli oggetti per skin |
| File originali del kit | `easywar_work/legos/` | `legosv2.obj` e `lego2skin2048_2-2.png` (atlas 2048) |
| tripo\_mech\_1.py | easywar\_work/base/ | Converte un FBX di Tripo in unità: pezzi, texture con colore squadra, Lua e definizione. Autonomo, non eseguito in Blender |
| File di Tripo del responsabile | easywar\_work/tripo/ | mech\_robot\_3d\_model.fbx e mech\_robot\_3d\_model.fbm/mech\_robot\_3d\_model\_basecolor.jpg |

Comando tipo: `flatpak run org.blender.Blender --background --python /home/p/.spring/games/easywar.sdd/easywar_work/base/NOME.py`

Documento di regole: "Canone di modellazione Easy War su Recoil" ([link](https://claude.ai/artifact/MLTiWTVWoGrWMBu6xyCfBH)). Va aggiornato con l'approccio a ricetta e con le armi.

## Proposte di correzione ai documenti (non applicate)

Le correzioni riguardano soprattutto il brief e il canone. Nessuna è stata applicata.

1. **Brief, punto 5 (vincoli s3o):** aggiungere quanto ora visto. L'alpha alta di tex1 fa comparire il colore del giocatore. La V delle UV va invertita. I nomi delle texture vanno dentro il `.s3o` e i file in `unittextures/`.
2. **Brief, punto 3:** Skeletor\_S3O esporta anche Lua, non solo BOS. Non è necessario finché le animazioni sono scritte da script.
3. **Brief, punto 6:** segnare come esclusi gli approcci 3 e 4 e come rinviato il 5, con i motivi del responsabile. L'approccio 6 (generatore AI) va riscritto: il responsabile indica Tripo come fonte possibile di modelli, con conversione in unità tramite script.
4. **Brief, punto 7:** l'abbinamento previsto "riutilizzo sulla nave" è stato collaudato invece su robot bipedi, perché il kit si prestava meglio.
5. **Canone di modellazione:** aggiungere l'approccio a ricetta (pezzi del kit stirati a misura), il ciclo disegno → anteprima → script, la convenzione `FWD = -1` e lo schema delle armi (a riposo canna in basso, mira con braccio o gomito).
6. **Roadmap:** la nota sul ripiego a cubi può dire che lo script delle primitive lo produce già a costo quasi nullo.
7. **Gioco:** aggiungere una riga `easywar_work/` al `.gitignore`.
