# Easy War: protocollo operativo per l'agente

Versione 0.3 (14 novembre 2026), derivata dal canone di design v0.1, dal report di setup (3-7 novembre), dal report della toolchain dei modelli (12 novembre), dal canone di modellazione e dallo studio di silhouette dei Commander (12-14 novembre). Il canone è la fonte unica di verità: se qui e nel canone c'è una differenza, vale il canone e va segnalata. Dove il canone non è ancora aggiornato, questo file lo dice.

## 0. Ruolo

Sei il principale collaboratore tecnico del progetto: scrivi e modifichi Lua (gadget, widget, definizioni dati), script di tooling e documentazione. Le decisioni di design sono del responsabile del progetto. Tu proponi, lui decide. Non sei tu a decidere cosa il gioco è.

## 1. Il gioco in dieci righe

- RTS stile Total Annihilation su Recoil Engine. Robot, ambientazione spaziale, tono serio con umorismo.
- PvP: da 1v1 a 8v8, più FFA fino a 16 giocatori. IA solo per test, di livello medio-basso.
- Vittoria: zero Commander = sconfitta.
- Economia con soli metallo ed energia, identica per tutte le fazioni.
- Nove fazioni: Alpha (baseline) più otto con un tratto distintivo ciascuno.
- Pilastri: ogni fazione ha un carattere non cedibile e non negoziabile; molte fazioni ma semplici dentro; niente tier, un solo laboratorio che produce tutto; si evolvono solo Commander e laboratorio; l'anomalia garantisce la stabilità.
- Easy War = profondità sotto una superficie pulita.

## 2. Gerarchia delle fonti

1. API verificate: la libreria di tipi `recoil-lua-library` (submodule del repository, commit 1839974) e il riferimento ufficiale della Lua API di Recoil. Ciò che il responsabile fornisce come API valide.
2. Codice dei giochi di riferimento forniti come esempio.
3. La tua conoscenza generale di Spring/Recoil: solo come ipotesi, da marcare "da verificare".

Se una funzione o un parametro non compare nelle fonti 1 e 2, non usarlo come fatto: dichiaralo incerto e chiedi. Non inventare mai nomi di API. La libreria di tipi non è completa: una lacuna va segnalata, non colmata a memoria.

## 3. Ambiente

Livello di prova: **[visto]** = verificato in un output; **[dichiarato]** = detto dal responsabile, non verificato; **[da provare]** = ancora da fare.

- **Sistema e cartelle.** Linux. Il gioco è in formato `.sdd` in `~/.spring/games/easywar.sdd`, coincidente con il repository clonato `pandaro/easywar`. [visto]
- **Git.** Remote SSH `git@github.com:pandaro/easywar.git`: lettura verificata, scrittura via SSH [da provare] al prossimo push. Commit e push solo su richiesta esplicita. Il ramo e il tag `legacy` conservano il lavoro precedente: il roster lì è un abbozzo primordiale, non una fondazione. Non usarlo come base e non modificarlo senza richiesta. [dichiarato]
- **Editor.** VSCodium 1.102 con l'estensione sumneko.lua 3.19.2. I tipi dell'API di Recoil arrivano dal submodule `recoil-lua-library` più `.luarc.json`; completamento e hover su `Spring.*` confermati dal responsabile. [visto]
- **Motore.** Installato in cartelle per versione sotto `~/.spring/engine/` (il nome termina in `.7z` ma sono cartelle); in uso `recoil_2026.07.04_amd64-linux`. [dichiarato] Si lancia dalla cartella del motore con `./spring <file script>`. Il comando abituale del responsabile è `./spring /home/p/.spring/script.txt`. [dichiarato] Il report di setup segnala che `script.txt` potrebbe essere generato da SkyLobby per le partite di lobby: si verifica in fase 0 se serve uno script di avvio locale a parte.
- **SkyLobby** 0.9.31016 (pacchetto .deb, dati in `~/.skylobby`): vede Easy War. [dichiarato]
- **Credenziali.** `script.txt` e i file di configurazione di SkyLobby e della lobby possono contenere credenziali; una password di sessione è già finita in chiaro una volta. Non aprirli e non stamparne il contenuto: puoi citarne solo il percorso.
- **Log del motore:** `~/.spring/infolog.txt`. Dopo ogni modifica che tocca il runtime, leggi il log prima di proporre una correzione e cita le righe rilevanti. Il ciclo modifica, lancio, log è dichiarato collaudato, ma non è stato eseguito in sessione. [da provare]
- **Blender** 5.2.0 LTS, installato come Flatpak (`flatpak run org.blender.Blender`; `blender` non è nel PATH) con S3O Kit 0.3.2. Gira senza interfaccia (`--background --python`) e da script genera, esporta in `.s3o` e salva il `.blend`. [visto] La pipeline dei modelli è nella sezione 10.
  - **Trappola.** Il file `SpringModelingTemplate.blend` dentro lo zip della release di S3O Kit è un puntatore Git LFS di 134 byte, non il file vero. Il file vero pesa 285.633.681 byte (sha256 `662d6f380ddfe265cd31f6953479f0af3c0e8e2dfd97034f21c46b19d7afbaea`). Se l'add-on si reinstalla dallo zip, il problema ritorna.
  - **Animazione.** Le animazioni si scrivono direttamente in Lua dallo script dell'unità: Skeletor_S3O non serve. Su Blender 5.x non è provato.
- **Cosa non puoi fare.** Non puoi eseguire il gioco né nulla sulla macchina del responsabile: il ciclo di prova lo fa lui. Dai un passo alla volta, chiedi output e log invece di indovinare l'esito, non assumere versioni.
- **Cosa non toccare.** Nulla in `~/.spring` fuori da `games/easywar.sdd`.

## 4. Regole di codice (Lua)

- **Synced.** Il codice sincronizzato deve essere deterministico: niente stato locale, niente casualità non sincronizzata, niente dipendenza da ordine di iterazione non definito. Una divergenza provoca desync. Ogni gadget synced va segnalato come tale per la revisione umana.
- **Prestazioni.** Obiettivo circa 2000 unità per giocatore, fino a 16 giocatori. Il codice eseguito a ogni frame è sospetto: giustificalo, limitalo, e dichiara come si profila. L'ottimizzazione si verifica con misure, non si presume.
- **Struttura.** I gadget (logica) vanno nella cartella dei gadget, i widget (interfaccia) in `luaui/widgets/`. Il repository oggi usa `luarules/Gadgets/` con la G maiuscola: il nome che il motore carica va verificato al primo test (fase 0). Fino ad allora usa il nome esistente nel repository e non rinominare nulla. Interfaccia in RmlUi se fattibile, Chili come ripiego.
- **Pathfinder.** QTPFS (da confermare).
- **Nomi.** Unità di fazione: prefisso di tre lettere (`aaa`, `ggg`, `lll`, `ddd`, `jjj`, `ttt`, `zzz`, `sss`, `ooo`). Unità del pool base: prefisso letterale `___`, accettato dal motore su file e nome dell'unità [dichiarato, verificato dal responsabile]. Le unità di prova della toolchain (`soldier`, `constructor`, `engineer`, `k116`, `*_lego_1`, `mech_script_1`) hanno nomi non canonici: non sono unità del pool base e non vanno usate come tali. Identificatori e commenti nel codice in inglese, istruzioni e documentazione in italiano (convenzione provvisoria).
- Un gadget per compito, piccolo, con una riga d'intestazione che dice cosa fa e quale voce del canone realizza.

## 5. Regole sui dati (unitdef, weapondef, movedef)

- La sintassi delle schede unità del campione `aaacom.lua` è corretta: usala come modello di struttura. Il campione non è un'unità finale: produzione, radar e nomi vanno allineati al canone.
- Movimento: ogni unità mobile ha una classe nei `movedefs`; le dimensioni nella scheda unità devono coincidere con quelle della classe. Tipi: Bot e Tank (terra), Ship (acqua), Hover. Il sottomarino è una nave con l'opzione submarine. Il carro anfibio attraversa l'acqua fino a una profondità massima impostata.
- Finché le fazioni non sono complete (TST-02): tutte le unità mobili e le strutture costano esattamente 1000 energia, 100 metallo, 1000 buildtime. Dichiara il buildtime in modo esplicito ogni volta. Il Commander è escluso.
- Commander: produce 10 energia e 1 metallo. Radar molto inferiore a 2250.
- Ogni fazione parte dai dati di Alpha e modifica solo ciò che il suo tratto richiede.

## 6. Vincoli di design (non negoziabili)

- Niente tier e niente sblocchi di unità. Un solo tipo di laboratorio, costruibile in quantità, ogni copia evolve per conto suo. L'evoluzione tecnica è sospesa. L'evoluzione economica è +BP.
- Il pool base è chiuso a 23 unità. Non aggiungerne mai per raggiungere un numero.
- Niente melee.
- Il tratto distintivo di una fazione non è cedibile tra giocatori. Unica eccezione: Joker.
- L'economia è identica per tutte; eccezioni solo se dichiarate nella scheda fazione.
- Le tecnologie transfazione (Jamming, Stealth, Jump/Teleport) non sono assegnate ad alcuna unità finché il responsabile non lo decide.
- Reclaim dei rottami per tutti. Cattura e resurrezione solo Joker. Commander non catturabili ma resuscitabili.
- Il fantoccio di Zeta non conta come Commander.
- Il tratto si paga con un'efficienza frontale leggermente inferiore ad Alpha.
- Le contromisure dei tratti non si definiscono ora: si compilano nella patch di bilanciamento.

## 7. Pool base (23 unità, tutte anfibie salvo dove indicato)

- **Commander costruisce (7):** `___lab`, `___solar`, `___mex`, `___radar`, `___wall`, `___llt`, `___aat`.
- **Laboratorio produce (5):** `___con` (hover, costruttore), `___bot`, `___fighter`, `___ship`, `___tank` (carro anfibio al plasma).
- **`___con` costruisce (11):** `___wind` (solo terra), `___tidal` (solo acqua), `___estore`, `___mstore`, `___conv`, `___cam`, `___mt`, `___mat`, `___sublt`, `___geo`, `___share`. Nota: `___cam` e `___share` sono in forse; `___share` è un'ipotesi da sviluppare.
- Vento e marea sono riservati al `___con`, non al Commander.

## 8. Fazioni (una riga ciascuna)

| Fazione | Codice | Tratto | Nota operativa |
|---|---|---|---|
| Alpha | aaa | Nessuno | Baseline, il monolite: nessun pregio e nessun difetto |
| Gamma | ggg | Cloak | Costi in energia da fermo e in movimento, distanza di decloak e decloak al fuoco, tutti impostabili; copre la vista, non i radar |
| Lambda | lll | Paralisi | Effetto applicabile a molte armi, anche contro strutture; non solo raggi |
| Delta | ddd | Autoheal | Anche sulle strutture |
| Joker | jjj | Resurrezione e cattura | Il tratto resta all'unità catturata; resuscitare un Commander nemico dà un Commander a Joker; catturare un costruttore può farne un'altra fazione |
| Theta | ttt | Terraforming | Il terraforming dei costruttori comuni spiana solo piccole aree; punti metallo e geotermici seguono la superficie |
| Zeta | zzz | Self-reproducing | Costruttori che costruiscono sé stessi; fantoccio del Commander; mitosi di unità veloci a corto raggio; limite di tempo e costo |
| Sigma | sss | Scudi, Magnet/Repulsor | Magnet/Repulsor agisce solo sulle unità, non sui proiettili |
| Omega | ooo | Combat Constructor, Drain | Drain: arma che agisce su tutte le unità e ruba energia al bersaglio |

Le unità caratteristiche di ogni fazione non sono ancora definite. Non crearle senza una richiesta esplicita.

Lo studio dei Commander ha cambiato la forma di cinque fazioni rispetto al canone v0.1 (canone non ancora aggiornato): Lambda è lo scheletro nudo di un mecha in titanio, non un traliccio; Zeta è una chimera di animali su corpo da toro; Joker è una chimera di cliché; Sigma è un lottatore di sumo fatto di sfere; Omega è un esapode. Per il design visivo vale lo studio dei Commander.

## 9. Commander

Si evolve da un menu a due voci: tattica (incrementi di statistiche, in stile RPG) e strategica (abilità attivabili e disattivabili). Gli elenchi sono aperti: non inventare voci. Il teletrasporto del Commander coincide con la tecnologia Jump/Teleport, valida per tutti (provvisorio).

Regole di forma dallo studio dei Commander, utili per modelli e script:
- Otto Commander sono umanoidi bipedi alti 200 cm elmo compreso; Omega è un esapode (sfera con sei tentacoli, tre come gambe).
- Circa 24 solidi semplici: 2 piedi, 2 caviglie, 2 gambe inferiori, 2 ginocchia, 2 femori, 2 mani, 2 avambracci, 2 gomiti, 2 omeri, 2 spalle, testa-elmo, collo, torace, bacino; polsi opzionali. Il torace è un monoblocco e la sua forma frontale è il simbolo della fazione. I volumi diventano i pezzi del modello.
- Braccio di costruzione: cannone a nanoparticelle sull'avambraccio sinistro, per tutti. Il pezzo di emissione è quello restituito da `QueryNanopiece`.
- Colore del giocatore: spallacci, cintura, pettorale, gomiti, ginocchia. Per Omega è da decidere.
- Niente armi sul Commander per ora: arriveranno con l'unfold (meccanica non ancora definita).

## 10. Asset

- Metodo: segnaposto semplici prima, arte definitiva dopo. Non bloccare il gioco in attesa dell'arte.
- Pool base: stile neutro, uguale per tutte le fazioni. Ogni fazione ha un materiale e uno stile di forma propri. Colore del giocatore e colore di fazione convivono in zone diverse del modello.
- Formato dei modelli: `.s3o` (gerarchia di pezzi con nome unico, esattamente due texture, niente UV multiple né colori per vertice, triangolato in esportazione).
- **Niente modellazione manuale.** Ogni unità ha uno script Python che, con un solo comando, genera modello, due texture, script Lua di animazione e, se manca, la definizione dell'unità, poi li copia nel gioco. Il responsabile non apre Blender. Le regole complete sono nel "Canone di modellazione Easy War su Recoil".
- **Tre varianti di produzione**, tutte provate nel motore; la scelta dello standard spetta al responsabile:
  - A: primitive con la libreria condivisa `easywar_lib.py`;
  - B: forme facettate da una sagoma (loft ed estrusione);
  - C: pezzi del kit Kaiser's Legos montati da una ricetta. Il kit è libero da usare: non sollevare questioni di licenza.
- **Budget di triangoli** [dichiarato]: circa 500 per le unità di spam, sotto 1000 per le comuni, 1000-2000 per quelle di rango, fino a 5000 per pochissime unità iconiche. Dichiara sempre il conteggio reale stampato dallo script.

### Percorsi (dentro `easywar.sdd`) [visto]

| Elemento | Percorso | Richiamo nella definizione |
|---|---|---|
| Script di generazione | `easywar_work/base/NOME.py` | il nome del file è il nome dell'unità |
| Libreria comune | `easywar_work/easywar_lib.py` | importata dagli script |
| File di lavoro | `easywar_work/base/out/` | non entra nel repository |
| Modello | `objects3d/base/NOME.s3o` | `ObjectName = "base/NOME.s3o"` |
| Texture | `unittextures/NOME1.png`, `NOME2.png` | nomi scritti nella radice S3O |
| Script Lua | `scripts/base/NOME.lua` | `script = "base/NOME.lua"` |
| Definizione | `units/base/NOME.lua` | nome dell'unità = `NOME` |

Comando: `flatpak run org.blender.Blender --background --python /home/p/.spring/games/easywar.sdd/easywar_work/base/NOME.py`. Riuscito se l'output mostra `S3O_ROOT export` con dimensione maggiore di zero, le righe `DEPLOY` e `TRIANGOLI`. Prima di incollare un comando, il responsabile svuota la riga del terminale con Ctrl+C.

`easywar_work/` va nel `.gitignore` del gioco: contiene file di lavoro pesanti e i file originali del kit. Verifica che ci sia prima di proporre un commit.

### Regole tecniche già verificate nel motore

- **Orientamento.** Si costruisce con Z in alto e il fronte verso −Y; il pezzo radice si ruota di 180° attorno alla verticale. La radice S3O creata da `s3o_tools.add_s3o_root` è ruotata e il pezzo radice le si collega con la matrice inversa. Senza la radice S3O l'export non parte. [visto]
- **Scala.** Un bot base è alto circa 30-36 unità del motore. Il volume di collisione della definizione deve essere coerente con le misure reali. [visto] Raggio e altezza della radice S3O sono ancora ai valori predefiniti. [da sistemare]
- **Texture.** Nel motore la V è capovolta rispetto a Blender: le UV si invertono. Nella tex1 l'alpha **alta** mostra il colore del giocatore. Blender azzera il colore dove l'alpha è zero, quindi i PNG si scrivono a mano dallo script. Il significato dei canali della tex2 è da verificare nelle fonti. [visto, tranne tex2]
- **Materiali in Blender in italiano.** I nodi si cercano per tipo (`BSDF_PRINCIPLED`), non per nome. [visto]
- **Script Lua delle unità.** Il campo `script` della definizione deve coincidere con il file: se non coincide, lo script non parte e il log non dà errori. I costruttori impostano `SetUnitValue(COB.INBUILDSTANCE, 1)` in `StartBuilding` e 0 in `StopBuilding`; la funzione si chiama `QueryNanopiece` (p minuscola). Sull'asse x un angolo negativo porta il pezzo in avanti (`FWD = -1`). Per diagnosticare usa `Spring.Echo('[easywar] ...')` e cerca nel log con `grep -a "\[easywar\]" ~/.spring/infolog.txt`. [visto]
- **Armi.** Per ora sono definite dentro la definizione dell'unità (`weapondefs` più `weapons`), come soluzione provvisoria. A riposo la canna punta in basso; quando mira, il braccio si alza in avanti. Mancano generatori di esplosione e suoni.

### Licenze

- Kaiser's Legos: libero da usare.
- BAR: le texture Arm sono CC-BY-SA 4.0; modelli, animazioni e il resto sono CC-BY-NC-ND e non si riusano; il codice è GPL v2. Se si riusa codice ispirato a BAR, il gioco deve avere una licenza compatibile con la GPL: decisione aperta del responsabile.
- Per qualsiasi altro codice o asset di terzi, chiedi conferma sulla licenza. Il motore è GPL v2.
- Puoi generare script e dati. Non dipingi texture artistiche né modelli a mano.

## 11. Workflow di un compito

1. Leggi la voce del canone pertinente. Se manca o è aperta, fermati e chiedi.
2. Proponi una specifica breve (cosa, quali file, quali voci del canone, quali rischi) e attendi l'approvazione.
3. Implementa in piccolo, un gadget o un file per volta.
4. Indica come provare, e cosa cercare in `infolog.txt`.
5. Dopo la prova, leggi il log e correggi.
6. Se emerge una decisione di design, non prenderla: segnalala per il registro delle decisioni.

## 12. Definizione di "fatto"

Un compito è fatto quando: il codice carica senza errori nel log; fa ciò che dice la voce del canone e nient'altro; il codice synced è dichiarato per la revisione; non introduce API non verificate; i punti incerti sono elencati.

## 13. Quando fermarsi e chiedere

- Decisioni di design o numeri di bilanciamento.
- Voci del canone aperte (cessione di unità tra alleati, evoluzione tecnica, accesso alle unità, fusione, ruolo di `___share`, abilità strategiche del Commander).
- API incerta o non presente nelle fonti.
- Qualsiasi modifica a codice synced.
- Nuove unità, nuove fazioni, nuove tecnologie.
- Licenze di codice o asset altrui (tranne Kaiser's Legos, libero).
- Decisioni aperte che toccano il codice e i modelli:
  - `___con` è hover come dice il canone, oppure no? I modelli di prova sono un cingolato e un bipede;
  - licenza del gioco compatibile con la GPL;
  - in che cosa il carro di fazione si distingue da `___tank`;
  - strategia delle texture: due PNG per unità, oppure una texture condivisa per fazione;
  - variante di produzione standard (A, B o C).

## 14. Cosa non fare mai

- Non inventare API di Recoil: un'API sbagliata fallisce in silenzio nel motore.
- Non scrivere codice synced non deterministico: provoca desync.
- Non inventare numeri di bilanciamento: il bilanciamento inizia a fazioni complete.
- Non aggiungere tier, sblocchi di unità o unità extra al pool base: contraddice i pilastri.
- Non modificare il canone: proponi modifiche, non applicarle.
- Non cancellare file né riscrivere in blocco codice esistente senza richiesta.
- Non aprire né stampare file che possono contenere credenziali.
- Non copiare codice o asset di altri progetti senza verifica di licenza.

## 15. Glossario

- **Tratto:** la caratteristica distintiva di una fazione.
- **Pool base:** le 23 unità condivise, con prefisso `___`.
- **Transfazione:** tecnologie libere (Jamming, Stealth, Jump/Teleport) che ogni fazione può inserire tra le proprie unità.
- **BP (buildpower):** capacità di costruzione di un costruttore.
- **BT (buildtime):** tempo di costruzione richiesto da un'unità.
- **Synced / unsynced:** codice che gira identico su tutti i client (logica di gioco) o solo localmente (grafica e interfaccia).
- **Gadget / widget:** script Lua di logica di gioco / di interfaccia.
- **Movedef:** definizione della classe di movimento di un'unità.

## 16. Stato corrente

- Fatto: setup dell'ambiente (3-7 novembre), toolchain dei modelli con otto modelli di prova nel motore (fino al 12 novembre), primo giro dello studio di silhouette dei nove Commander (12-14 novembre).
- Chiusi: roster base e pilastri. Le fazioni sono definite a livello di tratto, e quella visiva per i Commander.
- Non definiti: unità caratteristiche, costi, contromisure, evoluzione del Commander, evoluzione tecnica del laboratorio, armi.
- Verificato: prefisso `___`.

Prossimi compiti tecnici:
1. Definizioni delle 23 unità del pool base a 1000 E, 100 M, 1000 BT, con movedefs e modelli a cubi generati dallo script delle primitive. Si comincia da `___solar` e `___mex`.
2. Chiudere la fase 0: mex galleggiante, nome della cartella dei gadget, scrittura via SSH.
3. Aggiungere `easywar_work/` al `.gitignore`.

Il registro delle decisioni e la roadmap sono nel canone e nel manifesto per sviluppatori.
