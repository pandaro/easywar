# Easy War – Canone di design (v0.1)

Nov 3, 2026 · @bio

## Premessa

Questo canone raccoglie le decisioni di design di Easy War, un RTS in stile Total Annihilation su Recoil Engine, ed è la fonte unica da cui derivano sia il manifesto per gli sviluppatori sia il `CLAUDE.md` operativo per l'agente. Contiene decisioni e perimetro del gioco, non schede unità, numeri o codice.

**Legenda degli stati**

| Stato | Significato |
| --- | --- |
| Deciso | Scelta confermata dal responsabile del progetto |
| Provvisorio | Vale finché i test non dicono altro |
| Principio | Orientamento di design, da validare nel gioco |
| Bozza / Idea | Direzione indicata, dettagli non fissati |
| Aperto | Volutamente non deciso |

**Convenzioni**

- Ogni decisione ha un ID (es. `ECO-07`) e vive in un solo posto; gli altri documenti rimandano all'ID.
- Le voci aperte restano visibili: chi lavora sul progetto non deve improvvisare dove il canone tace.
- Le note sul motore Recoil non verificate sono segnate "da verificare".

## C0 · Pilastri

Quattro principi orientano ogni scelta di design: fazioni con carattere, semplicità interna, gioco centrato su laboratorio e Commander, e anomalia come garanzia di stabilità.

| ID | Decisione | Stato |
| --- | --- | --- |
| PIL-01 | Ogni fazione ha un carattere che può esprimersi in più caratteristiche combinate. Il tratto distintivo è non commerciabile: non è cedibile tra giocatori e non è negoziabile nel design | Deciso |
| PIL-02 | Molte fazioni, ciascuna semplice. Niente tier 1/2/3, nessuno stacco netto nell'evoluzione delle unità. Tutte le unità sono raggiungibili da un solo laboratorio. Meno unità per fazione che in BAR, accesso più fluido | Deciso (meccanismo di accesso aperto) |
| PIL-03 | Si evolvono solo il Commander e il laboratorio. Esiste un solo tipo di laboratorio che produce tutto. Il gioco è lab-centrico tanto quanto comm-centrico. Evoluzione economica (+BP) sì; evoluzione tecnica (nuove unità) sospesa | Deciso |
| PIL-04 | Principio dell'anomalia: in un sistema prevedibile l'anomalia garantisce la stabilità. Alpha, senza tratto, è essa stessa il carattere: l'assenza di anomalia è la sua anomalia. Ogni tratto si misura come scostamento da Alpha | Deciso |

## C1 · Ambientazione e tono

I robot nati per aiutare l'uomo lo hanno sterminato; Alpha, il Commander originario, ha colonizzato l'universo, e la distanza ha generato le altre fazioni.

| ID | Decisione | Stato |
| --- | --- | --- |
| AMB-01 | Origine: i robot, creati per aiutare l'umanità, la sterminano (del tutto o con qualche superstite). L'epoca esatta è aperta: dopo una rivolta contro le macchine in stile Jihad Butleriana, oppure poco dopo il regno di Claude Sonnet 5.5 il Magnanimo | Idea (epoca aperta) |
| AMB-02 | Esaurite le risorse della Terra, il Commander Alpha invade lo spazio e, grazie alla capacità di colonizzazione, colonizza pianeta dopo pianeta, galassia dopo galassia | Deciso |
| AMB-03 | Speciazione meccanica: con le distanze fisiche e temporali il codice che distingue Alpha si altera (selezione artificiale). Nascono altri otto Commander, caratterizzati da otto tecnologie uniche: le otto fazioni oltre ad Alpha | Deciso |
| AMB-04 | Movente del conflitto: le risorse. Si combatte dove c'è metallo o energia, o dove le fazioni si incontrano per caso. Altri motivi (genetica umana) esistono ma sono rimandati | Deciso |
| AMB-05 | Tono: serio, ma con umorismo. Regola dell'autore: se vuoi dire qualcosa di serio, falli ridere | Deciso |
| AMB-06 | Quantità di narrativa: a discrezione dell'autore, senza obblighi. Quanto scritto qui basta per ora | Deciso |

**Domande narrative lasciate aperte (non vincolanti):** chi ha superato Alpha, tutti o nessuno? Esiste ancora un uomo vivo? Alpha ha portato via codice genetico dalla Terra? Qualcuno ha riprodotto degli esseri umani?

**Da tenere d'occhio:** i riferimenti a opere esistenti (Dune, e il nome di un prodotto reale) vanno bene come ispirazione interna, ma nel gioco e nel materiale pubblico conviene usare termini propri, per non incorrere in problemi di diritti.

## C2 · Regole di base

Easy War è un gioco PvP da 1v1 a 8v8 e FFA a 16, con vittoria per eliminazione del Commander.

| ID | Decisione | Stato |
| --- | --- | --- |
| MOD-01 | Il gioco è focalizzato sul PvP | Deciso |
| MOD-02 | Formati a squadre da 1v1 a 8v8, più FFA fino a 16 giocatori | Deciso |
| MOD-03 | IA skirmish di livello medio-basso solo per test; può usare una sola fazione | Deciso |
| MOD-04 | Nessuna campagna né modalità cooperativa contro IA | Deciso |
| DUR-01 | 1v1: 10-20 minuti | Deciso |
| DUR-02 | 8v8: 40-50 minuti | Deciso |
| DUR-03 | Gli altri formati si interpolano; la durata è un obiettivo di bilanciamento, nessun timer di fine partita | Deciso |
| VIT-01 | Zero Commander = sconfitta. Resa e disconnessione sono gestite dal motore | Deciso |
| VIT-02 | La squadra perde quando tutti i suoi giocatori sono sconfitti; in FFA vince l'ultimo rimasto | Deciso |
| GIO-01 | Scelta della fazione libera, duplicati ammessi anche nella stessa squadra | Deciso |
| GIO-02 | Alpha è una scelta valida a tutti gli effetti | Deciso |
| GIO-03 | Nessuna limitazione di fazione per mappa o formato | Deciso |
| SQU-01 | Gli alleati condividono visuale e risorse (da verificare nel motore; vedi ROS-11) | Deciso |
| SQU-02 | Il tratto distintivo di una fazione non è cedibile ad altri giocatori. Eccezione dichiarata: Joker | Deciso |
| SQU-03 | Trasferimento di unità tra alleati | **Aperto** |
| SQU-04 | Alleanze dinamiche in FFA ammesse come opzione di partita | Deciso |
| AVV-01 | Ogni giocatore parte con un Commander e risorse iniziali uguali per tutti | Deciso |
| AVV-02 | Il valore delle risorse iniziali si definisce in C3 | Deciso |
| AVV-03 | I giocatori scelgono liberamente dove partire, entro zone assegnate alla squadra | Deciso |
| INF-01 | Nebbia di guerra, LOS e radar: gestiti secondo ciò che il motore permette | Deciso (a cura del responsabile tecnico) |
| INF-02 | Gli spettatori hanno visuale completa della mappa | Deciso |
| TST-01 | In fase di test tutte le unità sono disponibili da subito (nessuna evoluzione tecnica) | Provvisorio |
| TST-02 | Finché le fazioni non sono complete, tutte le unità mobili e le strutture hanno costo e buildtime identici (Commander escluso). Il bilanciamento inizia dopo | Deciso |

## C3 · Economia

L'economia è di tipo Total Annihilation, con soli metallo ed energia, identica per tutte le fazioni; i valori numerici restano provvisori fino ai test.

| ID | Decisione | Stato |
| --- | --- | --- |
| ECO-01 | Solo due risorse: metallo ed energia. Nessuna risorsa extra, nemmeno per singole fazioni | Deciso |
| ECO-02 | Il metallo si ottiene con estrattori classici | Deciso |
| ECO-03 | Il reclaim dei rottami è disponibile a tutte le fazioni | Deciso |
| ECO-04 | Esiste la conversione energia → metallo | Deciso |
| ECO-05 | Generatori: solare, vento, marea nel roster base; geotermico a stadi più avanzati. La fusione non ha ancora collocazione | Deciso (dettagli aperti) |
| ECO-06 | Lo stoccaggio (storage) è una meccanica standard | Deciso (dettagli aperti) |
| ECO-07 | Il Commander produce una piccola quantità di risorse, come gli altri costruttori: indicativamente 10 energia e 1 metallo. Evita stalli totali e partite ingiocabili | Deciso (valore indicativo) |
| ECO-08 | L'esaurimento delle risorse è gestito dal motore con priorità automatiche, modificabili via gadget o widget | Deciso |
| ECO-09 | Economia identica per tutte le fazioni. Eccezioni solo da un tratto di fazione, dichiarate nella scheda | Deciso |
| ECO-10 | Joker aggiunge, oltre al reclaim comune, la cattura di unità e la resurrezione dei rottami | Deciso |
| ECO-11 | Scala provvisoria per ogni unità e struttura (Commander escluso): 1000 energia, 100 metallo, 1000 buildtime | Provvisorio |
| ECO-12 | Nessun tier, ma una progressione economica: un costruttore pesante presente nel laboratorio va sostenuto, e usarlo troppo presto è un errore del giocatore | Principio (da validare coi test) |

**Da definire coi test:** assistenza alla costruzione e torri costruttrici statiche, livelli e costo dell'evoluzione economica, forma definitiva dei costi per tipo di unità, dettagli dello storage.

## C4 · Roster base

Il pool base condiviso è chiuso a 23 unità, con prefisso neutro `___`; i posti restanti fino al limite per fazione vanno alle unità caratteristiche.

**Regole**

| ID | Decisione | Stato |
| --- | --- | --- |
| NOM-01 | Le unità di fazione hanno prefisso di tre lettere (es. `aaacom`) | Deciso |
| NOM-02 | Le unità di base condivise hanno il prefisso letterale `___` (es. `___extractor`), senza vincolo di lunghezza | Deciso (verificato nel motore) |
| ROS-01 | Tutte le strutture base sono anfibie, lab incluso ("uno e trino, fa tutto ovunque"), tranne vento (solo terra) e marea (solo acqua) | Deciso |
| ROS-02 | Il Commander costruisce 7 unità; il resto del pool lo costruisce il `___con` o esce dal lab | Deciso |
| ROS-03 | Vento e marea sono riservati al `___con` | Deciso |
| ROS-04 | Un mex galleggiante può stare ovunque ed estrae dal punto metallo sotto di sé | Deciso (da verificare) |
| ROS-05 | Il lab produce 5 unità | Deciso |
| ROS-06 | Le unità anfibie hanno un basso rapporto spesa/resa: una torre base ne neutralizza più di una | Principio |
| ROS-07 | Si possono costruire quanti lab si vuole: un solo tipo, ogni copia evolve in modo indipendente | Deciso |
| ROS-08 | Il pool base è completo così; non si aggiungono unità per raggiungere quota 30 | Deciso |
| ROS-09 | `___sublt` colpisce sia unità sommerse sia di superficie | Deciso |
| ROS-10 | `___cam` dà principalmente LOS | Deciso (unità in forse) |
| ROS-11 | `___share` gestisce lo scambio di risorse nel team: senza di essa non si dona né si riceve | Ipotesi |

**Costruite dal Commander (7)**

| Nome | Ruolo | Territorio |
| --- | --- | --- |
| `___lab` | Fabbrica unica | Anfibio |
| `___solar` | Energia base | Terra e acqua (galleggia) |
| `___mex` | Estrattore di metallo | Terra e acqua |
| `___radar` | Rilevamento (può avere sonar) | Terra e acqua |
| `___wall` | Muro difensivo | Terra e acqua |
| `___llt` | Torre leggera laser contro unità di superficie | Terra e acqua |
| `___aat` | Torre antiaerea leggera | Terra e acqua |

**Prodotte dal laboratorio (5)**

| Nome | Ruolo | Territorio |
| --- | --- | --- |
| `___con` | Costruttore, hovercraft | Ovunque |
| `___bot` | Fante di schermaglia, difesa e offesa, bipede | Terra |
| `___fighter` | Caccia aria-aria, ricognizione scarsa | Aria |
| `___ship` | Multiuso leggero, sottomedio in tutto, antiaerea debole | Acqua |
| `___tank` | Carro anfibio al plasma, non spara sott'acqua, può emergere alle spalle del nemico | Terra e fondale |

**Costruite dal `___con` (11)**

| Nome | Ruolo | Territorio |
| --- | --- | --- |
| `___wind` | Energia | Solo terra |
| `___tidal` | Energia | Solo acqua |
| `___estore` | Magazzino energia | Anfibio |
| `___mstore` | Magazzino metallo | Anfibio |
| `___conv` | Convertitore energia → metallo | Anfibio |
| `___cam` | Videocamera perimetrale (LOS) | Anfibio (in forse) |
| `___mt` | Torre media contro unità di superficie | Terra |
| `___mat` | Torre antiaerea media | Terra |
| `___sublt` | Torre marina media con missili, colpisce anche i sommersi | Acqua |
| `___geo` | Energia geotermica | Anfibio |
| `___share` | Gestione dei flussi economici nel team | Anfibio (ipotesi) |

I nomi sono esemplificativi. Il `___con` costruisce anche tutte le unità del Commander.

## C5 · Combattimento

I domini di movimento sono quattro più il sottomarino, e il movimento si definisce con i movedefs; armi e armature restano da decidere.

| ID | Decisione | Stato |
| --- | --- | --- |
| COM-01 | Domini ufficiali: terra, acqua, aria, hover/anfibio. I sottomarini sono un dominio a parte | Deciso |
| COM-02 | Il movimento delle unità mobili si definisce nei `movedefs` (Gamedata). Le classi sono di quattro tipi: Bot e Tank (terra), Ship (acqua), Hover. Il sottomarino è una nave con l'opzione submarine. Un'unità di terra può attraversare l'acqua entro una profondità massima impostabile, e rallenta in proporzione alla profondità: è la base del carro anfibio | Deciso come principio (fonte: wiki Spring, da verificare su Recoil) |
| COM-03 | Niente combattimento corpo a corpo (melee) | Deciso |
| COM-04 | Classi di armatura, tipi di danno, fuoco amico, ritmo degli scontri | **Aperto** (a dopo i test) |

**Note dal motore (da verificare su Recoil):** la classe di movimento e le dimensioni nella scheda unità devono coincidere per un comportamento corretto; un'unità hover attraversa l'acqua a qualsiasi profondità senza rallentare, e ha una pendenza massima predefinita bassa; una nave richiede una profondità minima d'acqua. Questo spiega il problema già noto del laboratorio anfibio: un'unità prodotta su un terreno che la sua classe non può percorrere resta bloccata. Le mappe possono anche impostare moltiplicatori di velocità per tipo di terreno.

## C6 · Commander

Il Commander si evolve da un menu a due voci, tattica e strategica, in stile RPG; gli elenchi di potenziamenti restano aperti.

| ID | Decisione | Stato |
| --- | --- | --- |
| CMD-01 | Il radar del Commander è molto inferiore a 2250 (valore da definire, 100 o 1000) | Deciso come limite |
| CMD-02 | L'evoluzione avviene da un menu simile a quello delle costruzioni, con due voci: tattica e strategica | Bozza |
| CMD-03 | Tattica: potenziamenti di statistiche a incrementi, scelti singolarmente (es. +10% HP, +10% BP, gittata arma, radar, LOS, velocità, accelerazione, frenata) | Bozza, elenco aperto |
| CMD-04 | Strategica: un numero contenuto di abilità extra, attivabili e disattivabili (es. volo, camminata all-terrain, teletrasporto, arma antiaerea aggiuntiva, plasma a lungo raggio) | Bozza, elenco aperto |
| CMD-05 | Otto Commander sono androidi umanoidi bipedi alti 200 cm, elmo compreso, con proporzioni eroiche (circa 7-7,5 teste). Fa eccezione Omega, che è un esapode | Deciso |
| CMD-06 | Ogni Commander umanoide è fatto di circa 24 solidi semplici: piedi, caviglie, gambe inferiori, ginocchia, femori, mani, avambracci, gomiti, omeri, spalle (due di ciascuno), testa-elmo, collo, torace, bacino; polsi opzionali. Il torace è un monoblocco e la sua forma frontale è il simbolo della fazione | Deciso |
| CMD-07 | Braccio di costruzione: cannone a nanoparticelle con batterie, integrato nell'avambraccio sinistro, per tutte le fazioni, nella forma dello stile di fazione | Deciso |
| CMD-08 | Colore del giocatore su spallacci, cintura sul bacino, pettorale, gomiti e ginocchia | Deciso (Omega da decidere) |
| CMD-09 | Il Commander di base non porta armi: le armi arrivano con l'unfold | Deciso (meccanica dell'unfold da definire) |

**Da tenere d'occhio:** le abilità strategiche si sovrappongono alle tecnologie transfazione (il teletrasporto è la stessa tecnologia, TEC-03); volo e teletrasporto rendono il Commander difficile da eliminare, quindi il bilanciamento dovrà guardare costo, ricarica o condizioni d'uso; se attivare e disattivare ha un costo resta da decidere. Il file `aaacom.lua` è un campione di struttura e andrà allineato (produzione 10 E / 1 M, radar, nomi).

## C7 · Fazioni

Nove fazioni, ciascuna con un tratto distintivo; Alpha è la baseline senza tratto. Le schede descrivono il tratto, non i numeri. Le unità caratteristiche, i costi e le contromisure sono rimandati di proposito.

| # | Nome | Codice | Tratto primario | Secondario | Sintesi |
| --- | --- | --- | --- | --- | --- |
| F1 | Alpha | aaa | Nessuno (baseline) | - | Il monolite: nessun pregio, nessun difetto, nessuno la supera nello scontro diretto |
| F2 | Gamma | ggg | Cloak | - | Invisibilità alla vista, con costi da fermo e in movimento, distanza di decloak e decloak al fuoco impostabili |
| F3 | Lambda | lll | Paralisi | - | Effetto su molte armi (plasma, bombe, gas, mine, artiglieria, droni), anche contro strutture ed economia |
| F4 | Delta | ddd | Autoheal | - | Rigenerazione rapida di unità e strutture; vince lo scontro lungo |
| F5 | Joker | jjj | Resurrezione + Cattura | - | Cattura unità (Commander esclusi), resuscita rottami (anche Commander); catturando un costruttore può diventare un'altra fazione |
| F6 | Theta | ttt | Terraforming | - | Trasforma il territorio; punti metallo e geotermici seguono la superficie |
| F7 | Zeta | zzz | Self-reproducing | - | Costruttori che costruiscono sé stessi, fantoccio del Commander, mitosi di alcune unità |
| F8 | Sigma | sss | Shields | Magnet/Repulsor | Scudi, più attrazione e repulsione solo sulle unità |
| F9 | Omega | ooo | Combat Constructor | Drain | Costruttori mobili armati; arma Drain che ruba energia al bersaglio |

**Regola comune (BAL-02):** il tratto di una fazione si paga con un'efficienza frontale leggermente inferiore ad Alpha. Il compenso è il tratto, non una statistica superiore.

### Alpha (`aaa`)

- **Tratto:** nessuno. L'assenza di anomalia è il suo carattere (PIL-04).
- **Cosa fa:** è la fazione di riferimento, con statistiche bilanciate su tutto; nessuna abilità speciale.
- **Carattere:** il monolite che avanza senza fermarsi e senza trucchi. Le sue unità non hanno pregi perché non hanno difetti; nello scontro diretto nessuno la supera, sono gli altri a cercare escamotage per tenerle testa.
- **Dipendenze:** PIL-04, GIO-02, TST-02, BAL-01.
- **Unità caratteristiche:** pool completo come le altre fazioni, nel limite di ROS-08.

### Gamma (`ggg`)

- **Tratto:** cloak. Le unità si rendono invisibili.
- **Cosa fa:** un'unità in cloak non è visibile né bersagliabile. Copre la vista, non i radar (differenza da Stealth). Il cloak ha un costo in energia a unità ferma e uno diverso in movimento, entrambi impostabili; ogni unità ha una distanza di decloak impostabile e può uscire dal cloak quando spara.
- **Carattere:** imboscata e ricognizione.
- **Dipendenze:** PIL-01 e PIL-04 (distinzione netta da Stealth); ECO-09 (il costo di mantenimento è interno al tratto); BAL-01 (contromisure); INF-01.

### Lambda (`lll`)

- **Tratto:** paralisi. Le armi possono immobilizzare il bersaglio.
- **Cosa fa:** la paralisi è un effetto applicabile a quasi tutto il pool di armi (plasma, bombe, gas, mine, artiglieria, droni), non un solo raggio. Il bersaglio resta fermo per qualche secondo e non agisce, ma è vivo e colpibile. Vale anche contro le strutture, quindi contro l'economia.
- **Carattere:** arma temibile a ogni scala: droni che bloccano interi eserciti, artiglierie e torri a lungo raggio che paralizzano economie a distanze enormi, mine che fermano incursioni e possono rendere impossibile un blitz di Gamma.
- **Dipendenze:** PIL-01 e PIL-04 (distinzione da Magnet/Repulsor di Sigma: fermare contro spostare); ECO-09 (nessuna eccezione economica); BAL-01.

### Delta (`ddd`)

- **Tratto:** autoheal. Rigenerazione rapida senza costruttori.
- **Cosa fa:** unità e strutture recuperano punti vita nel tempo, più rapidamente del normale. Meccanica già presente nel motore (da verificare).
- **Carattere:** resistenza e attrito: un esercito che si ritira e torna poco dopo. Vince lo scontro lungo, non quello rapido.
- **Dipendenze:** PIL-01 e PIL-04 (famiglia della resistenza con Sigma: gli scudi assorbono prima, l'autoheal ripara dopo); ECO-09; BAL-01.

### Joker (`jjj`)

- **Tratto:** resurrezione e cattura.
- **Cosa fa:** una sua unità converte un'unità nemica; un'altra rianima i rottami. Il reclaim resta per tutti (ECO-03). I Commander non sono catturabili ma sono resuscitabili, e un Commander nemico resuscitato conta come Commander di Joker (VIT-01). Il tratto resta con l'unità catturata: un drone paralizzante catturato paralizza ancora.
- **Carattere:** l'anomalia più potente del gioco, ed è voluto. Catturando un costruttore o un lab può costruire le unità di un'altra fazione, tratto incluso, cioè diventare un'altra fazione. Trasforma le perdite in risorse; chi gioca contro Joker deve ripulire i rottami dal campo.
- **Dipendenze:** SQU-02 (eccezione dichiarata); SQU-03 (aperto); ECO-03 e ECO-10; BAL-01.

### Theta (`ttt`)

- **Tratto:** terraforming. Modifica il terreno durante la partita via Lua.
- **Cosa fa:** alza, abbassa e spiana il territorio. Il terraforming comune dei costruttori è limitato a spianare una piccola area, entro certi limiti, per costruire dove c'era un avvallamento; quello di Theta trasforma il territorio. I punti metallo e geotermici si muovono con la superficie: se il terreno resta pianeggiante, si può costruire ancora.
- **Carattere:** il campo di battaglia è un'arma; si combatte su una mappa che si trasforma.
- **Dipendenze:** C11 (pathfinding e prestazioni); ECO-02 e `___geo`; BAL-01. Zero-K fa ampio uso di terraforming ed è un riferimento (licenza da verificare se si riusa codice).

### Zeta (`zzz`)

- **Tratto:** self-reproducing, in tre forme.
- **Cosa fa:** (1) tutti i costruttori hanno sé stessi nella lista di costruzione; (2) il Commander costruisce un fantoccio di sé con pochissimi punti vita, come diversivo, che non conta come Commander per la sconfitta; (3) alcune unità, tipicamente veloci e a corto raggio, si dividono per mitosi creando sciami. Il fattore limitante è il tempo, oltre al costo.
- **Carattere:** espansione e inganno; il nemico non sa quale copia è quella vera.
- **Dipendenze:** PIL-03 (un costruttore che costruisce costruttori aggira il lab: va dichiarato cosa può fare la copia); VIT-01; ECO-09; C11 (crescita esponenziale, limite da stabilire coi test); BAL-01.

### Sigma (`sss`)

- **Tratto:** shields. Secondario: Magnet/Repulsor.
- **Cosa fa:** gli scudi assorbono il danno prima che arrivi; il motore li supporta molto bene. Magnet/Repulsor attrae o respinge le unità senza fare danno, solo sulle unità e non sui proiettili; richiede Lua.
- **Carattere:** controllo dello spazio: Sigma decide dove arrivano il danno e le unità nemiche.
- **Dipendenze:** PIL-01 e PIL-04 (distinzione da Delta e da Lambda); C11 (pathfinding); BAL-01.

### Omega (`ooo`)

- **Tratto:** Combat Constructor. Secondario: Drain.
- **Cosa fa:** costruttori mobili che costruiscono come un costruttore normale e in più hanno armi proprie. Drain è un'arma che agisce su tutte le unità: invece di consumare energia la procura, rubandola al bersaglio. L'unità colpita perde HP a ritmo costante, in proporzione all'energia del suo costo di costruzione, e il giocatore la riceve nel magazzino. Esempio: 100 E/s su un'unità da 1000 E e 2000 HP la uccide in 10 secondi (200 HP/s); i numeri sono rimandati.
- **Carattere:** prima linea che si alimenta del nemico; costruisce sul campo mentre combatte.
- **Dipendenze:** PIL-03 (costruzione sul fronte); ECO-09 (Drain è un'eccezione economica); distinzione da reclaim e da Joker; BAL-01.

## C8 · Tecnologie e bilanciamento

Il pool tecnologico è interamente assegnato: quattro tecnologie sono tratti di fazione, tre sono libere per tutte.

| Tecnologia | Meccanica | Supporto Recoil | Assegnazione |
| --- | --- | --- | --- |
| Magnet/Repulsor | Attrazione/repulsione senza danno | Via Lua | Sigma (secondario) |
| Drain | Assorbimento: ruba energia al bersaglio | Via Lua | Omega (secondario) |
| Combat Constructor | Unità ibride, costruzione + combattimento | Via Lua | Omega (primario) |
| Jamming | Oscuramento radar | Nativo (`radarDistanceJam`) | Transfazione |
| Stealth | Non rilevabile da radar | Nativo (`stealth = true`) | Transfazione |
| Jump/Teleport | Balzo/teletrasporto a costo | Via Lua | Transfazione |
| Self-repair | Riparazione automatica | Nativo (`autoHeal`) | Rimosso: è il tratto di Delta |

| ID | Decisione | Stato |
| --- | --- | --- |
| TEC-01 | Jamming, Stealth e Jump/Teleport sono tecnologie libere: ogni fazione può inserirle tra le proprie unità caratteristiche. Il pool base non cambia | Deciso |
| TEC-02 | Self-repair esce dal pool perché coincide con il tratto di Delta | Deciso |
| TEC-03 | Jump/Teleport coincide con l'abilità strategica del Commander, valida per tutti | Provvisorio |
| TEC-04 | Nessuna tecnologia transfazione è assegnata ad alcuna unità per ora | Deciso |
| BAL-01 | La matrice delle contromisure resta vuota di proposito: si compila nella patch di bilanciamento, dopo l'ultima unità di fazione | Deciso |
| BAL-02 | Il tratto di una fazione si paga con un'efficienza frontale leggermente inferiore ad Alpha | Deciso |

Le sette proposte iniziali (Mirage, Quake, Anchor, Void, Nexus, Pulse, Silo) sono cancellate dal canone e restano da rivedere in futuro.

## C10 · Direzione artistica

Ogni fazione si riconosce a colpo d'occhio da due assi: materiale e stile di forma per la fazione, e silhouette per il ruolo dell'unità.

| ID | Decisione | Stato |
| --- | --- | --- |
| ART-01 | Tutti robot. Le forme organiche sono solo estetiche | Deciso |
| ART-02 | Leggibilità orizzontale: ogni fazione si distingue per materiale e per stile di forma, che fa da marchio di fabbrica | Deciso |
| ART-03 | Leggibilità longitudinale: il ruolo di ogni unità si riconosce al primo colpo dalla silhouette (vedi tabella dei ruoli) | Deciso |
| ART-04 | Le unità del pool base hanno uno stile neutro, uguale per tutte le fazioni | Deciso |
| ART-05 | Colore: il colore del giocatore e quello di fazione convivono in zone diverse del modello, cioè la livrea dell'unità e zone dedicate che portano il colore di fazione | Deciso |
| ART-06 | Metodo di produzione: prima segnaposto semplici per testare il gioco, arte definitiva dopo | Deciso |
| ART-07 | Produzione dei modelli: uno script Python per unità, eseguito in Blender senza interfaccia, genera modello, texture e animazioni con un solo comando. Niente modellazione manuale. Varianti provate nel motore: primitive con libreria condivisa, forme facettate da una sagoma, pezzi del kit Kaiser's Legos (libero da usare). Le regole sono nel Canone di modellazione | Deciso (variante standard aperta) |
| ART-08 | Budget di triangoli: circa 500 per le unità di spam, meno di 1000 per le comuni, 1000-2000 per quelle di rango, fino a 5000 per le poche unità enormi e iconiche | Riferimento, da validare coi test |
| ART-09 | Riferimenti visivi: immagini da generatori gratuiti, partendo da prompt o da schemi dell'agente. Una silhouette è buona se si riconosce riempita di nero e ridotta a 60 pixel | Metodo |

**Stile di forma per fazione**

| Fazione | Stile | Materiale |
| --- | --- | --- |
| Alpha | Nessuna regola di forma: il robot da guerra per antonomasia, nella tradizione dei grandi robot giapponesi (cresta a V, ali sulle spalle, prese d'aria sul petto, posa eroica). Pettorale a W | Acciaio corten, con ruggine |
| Gamma | Triangolare: solidi da triangoli (piramidi, rombi, coni), angoli acuti minori di 90°. Pettorale a triangolo con punta in basso | Fibra di carbonio: nero opaco con tessitura grigia sottilissima |
| Lambda | Scheletro portante di un mecha, senza coperture: barre dritte a sezione tonda, giunti meccanici, colonna ad anelli, gabbia toracica a spigoli chiusa su uno sterno pieno; testa squadrata con un occhio centrale e bocca verticale. Non è un traliccio | Titanio liscio anodizzato blu-viola; il nido d'ape esagonale resta solo come motivo del materiale |
| Delta | Solidi pieni ad angoli ottusi, maggiori di 90°: pentagoni, esagoni, ottagoni. Pettorale a pentagono, sagoma a triangolo rovesciato | Alluminio mandorlato grigio satinato (rilievi a mandorla a spina di pesce) |
| Zeta | Chimera di animali, un animale per zona del corpo su un corpo massiccio da toro: corna da toro, muso da topo, spallacci a penne corazzate, braccio da pesce, piedi da rapace | Materiale organico di sintesi: rosso-rosa, umido, muscolare |
| Theta | Quadrato: angoli a 90°, cubi e parallelepipedi; anche le canne dei cannoni hanno profilo esterno quadrangolare con foro cilindrico | Granito grigio |
| Joker | Chimera di cliché: ogni parte del corpo è un luogo comune diverso, asimmetrico, ma sempre leggibile come robot da guerra | Plastica scadente, colori non troppo vivi |
| Sigma | Sfere, ellissoidi di rotazione e loro sezioni, in armonia con gli scudi sferici. Il Commander è un lottatore di sumo: sagoma a pera, pancia larga, spalle piccole | Fibra di vetro scura: nero lucidissimo con riflessi da ossidiana |
| Omega | Pseudo-alieno: tentacoli, protuberanze strane. Il Commander è un esapode | Fibre vegetali secche, verde-bruno, a corda |

Forme e materiali sono stati decisi nello studio di silhouette dei Commander (12-14 novembre 2026), dove si trovano anche le palette provvisorie, da verificare in gioco, e le immagini di riferimento.

**Commander di Omega:** esapode. Una sfera esterna grande come il torace degli altri Commander, con una finestra; al suo interno, in sospensione elettromagnetica, una seconda sfera indipendente che fa da cervello. Sei tentacoli a catena: tre in basso fanno da gambe, tre stanno in alto (due ai lati, uno verso l'alto). Sulla sfera ci sono due occhi, due sensori audio e un'antenna. Le zone del colore giocatore sono da decidere (proposta: cornice della finestra e anelli alla radice dei tentacoli).

**Silhouette per ruolo**

| Ruolo | Aspetto |
| --- | --- |
| Artiglieria | Cannone molto lungo, carrozzeria più goffa, a volte asimmetrica, poco adatta alla velocità |
| Caccia | Linee affusolate |
| Bombardiere | Più ampio, con inserzioni ortogonali |
| Bot raider | Compatto |
| Carro (tank) | Tarchiato |
| Esploratore | Leggero, sottile, basso, aerodinamico |
| Costruttore | Strano, asimmetrico, goffo |

**Da tenere d'occhio**

- L'esagono resta in Delta come forma dei solidi; in Lambda è solo il motivo del materiale e un piccolo richiamo. I due restano distinti anche perché Lambda è uno scheletro aperto e Delta un volume pieno.
- Le collisioni del modello scheletrico di Lambda le gestisce Recoil: nessuna regola a parte (decisione del responsabile).
- Con migliaia di unità in campo, forme semplici e silhouette nette pesano meno sulle prestazioni e leggono meglio: coerente con ART-03.
- Il carico di asset resta quello dichiarato in ROS-08 (pool base condiviso e unità caratteristiche per fazione); lo stile neutro del pool base (ART-04) lo contiene.

## C11 · Vincoli tecnici

Il gioco gira sull'ultima release stabile di Recoil, con interfaccia in RmlUi e un obiettivo di prestazioni alto, sul modello di BAR.

| ID | Decisione | Stato |
| --- | --- | --- |
| ENG-01 | Motore: Recoil, repository ufficiale `beyond-all-reason/RecoilEngine`, branch principale, sull'ultima release stabile di volta in volta | Deciso |
| ENG-02 | Interfaccia: RmlUi, se riusciamo; Chili (legacy) come ripiego | Preferenza |
| ENG-03 | Pathfinder: QTPFS invece di quello predefinito, per eserciti grandi | Da confermare (risposta "sì" a una domanda a due opzioni) |
| ENG-04 | Obiettivo di prestazioni: circa 2000 unità per giocatore, come BAR, su hardware buono. Con 16 giocatori l'ordine di grandezza è decine di migliaia di unità | Obiettivo, da validare coi test |
| ENG-05 | Il codice sincronizzato (synced) deve essere deterministico: niente stato locale né casualità non sincronizzata. Una divergenza provoca desync tra i giocatori | Vincolo |
| ENG-06 | Il codice generato va profilato nel motore: l'ottimizzazione si verifica con misure, non si presume | Vincolo di processo |

**Da verificare nel motore**

- Un mex galleggiante estrae dal punto metallo sotto di sé.
- Sonar contro carro sommerso, e se un carro spara sott'acqua.
- Scambio di risorse tra alleati e ruolo di `___share`.
- Unità prodotte su un terreno che la loro classe di movimento non può percorrere (lab anfibio).
- Prestazioni di mitosi (Zeta), terraforming (Theta), Magnet/Repulsor (Sigma) e di ogni codice eseguito a ogni frame.

**Per chi crea le mappe:** punti metallo anche in acqua, zone di partenza per squadra, supporto a 16 giocatori.

**Interfaccia:** il menu di evoluzione del Commander (CMD-02) richiede un'interfaccia dedicata; RmlUi è nuovo e documentato in modo incompleto.

**Licenze:** il motore è GPL v2. Codice e asset presi da BAR, Zero-K, Metal Factions e altri vanno verificati caso per caso. BAR: modelli e animazioni sono CC-BY-NC-ND e non si riusano, le texture Arm sono CC-BY-SA 4.0, il codice è GPL v2. Il kit Kaiser's Legos è libero da usare.

### Ambiente di sviluppo

| ID | Decisione | Stato |
| --- | --- | --- |
| ENV-01 | Sistema: Linux | Deciso |
| ENV-02 | Il gioco vive come cartella in formato `.sdd` in `~/.spring/games/easywar.sdd` | Deciso |
| ENV-03 | Editor: VSCodium, con la cartella del gioco aperta | Deciso |
| ENV-04 | Test: si lancia una partita da SkyLobby o da riga di comando | Deciso (comando esatto da definire) |
| ENV-05 | Diagnostica: il log del motore è `infolog.txt` in `~/.spring` | Deciso |

**Precisazioni:** il motore è installato in cartelle per versione sotto `~/.spring/engine/`; in uso `recoil_2026.07.04_amd64-linux`. La cartella `.sdd` coincide con il repository clonato `pandaro/easywar`, usato come cartella di sviluppo. Il comando di lancio da riga di comando, eseguito dalla cartella del motore, è `./spring /home/p/.spring/script.txt`; se quel file è generato da SkyLobby, la fase 0 verifica se serve uno script di avvio locale a parte.

**Strumenti installati** (setup del 3-7 novembre 2026). Visto in output: VSCodium 1.102 con sumneko.lua 3.19.2; tipi dell'API dal submodule `recoil-lua-library` (commit 1839974) più `.luarc.json`; Blender 5.2.0 LTS come Flatpak con S3O Kit 0.3.2, export `.s3o` funzionante. Dichiarato, non verificato: motore, SkyLobby 0.9.31016, ciclo modifica-lancio-log. Da provare: scrittura via SSH e Skeletor\_S3O su Blender 5.x. Il file `SpringModelingTemplate.blend` nello zip di S3O Kit è un puntatore Git LFS: va usato il file vero (285.633.681 byte). Il ramo e il tag `legacy` conservano un roster primordiale, non una fondazione. Il nome della cartella dei gadget si verifica nella fase 0.

## Punti aperti

Undici decisioni di design restano da prendere; le questioni tecniche le verifica il responsabile del motore.

**Da decidere nel canone**

1. SQU-03: cessione di unità tra alleati.
2. ROS-11 e SQU-01: se `___share` è necessaria per scambiare risorse, SQU-01 va riformulato.
3. Evoluzione tecnica del laboratorio (sospesa) e meccanismo di accesso alle unità (PIL-02).
4. Collocazione della fusione (ECO-05).
5. Drain contro il Commander: Drain agisce su tutte le unità, quindi anche sul Commander; da confermare se va limitato.
6. CMD-04: elenco delle abilità strategiche e regola di accesso, in relazione a TEC-03.
7. `___con`: hover come in C4, oppure bipede o cingolato come nei modelli di prova.
8. Licenza del gioco: deve essere compatibile con la GPL se si riusa codice ispirato a BAR.
9. Carro di fazione: in che cosa si distingue da `___tank`.
10. Modelli: variante di produzione standard e strategia delle texture (due PNG per unità oppure una texture condivisa per fazione).
11. Contromisure dei tratti: rimandate a BAL-01.

**Tecnici (da verificare nel motore)**

- Lab anfibio e unità bloccate (una nave su terra, un bot in acqua profonda): risolto "in qualche modo", da realizzare.
- Carro sommerso contro sonar e `___sublt`.
- Prestazioni di mitosi, terraforming e Magnet/Repulsor.
- Allineare `aaacom.lua` al canone.

**Rimandati di proposito**

- Costi e statistiche (bilanciamento dopo l'ultima fazione).
- Unità caratteristiche delle fazioni.
- Assistenza alla costruzione, livelli dell'evoluzione economica, dettagli dello storage.

## Sezioni ancora da scrivere

Nessuna è bloccante per i due manifesti.

| Sezione | Contenuto previsto |
| --- | --- |
| C1 Ambientazione | Scritta (v0.1): vedi C1 |
| C5 Combattimento | Parziale (v0.1): domini e movedefs scritti; restano armi e armature |
| C9 Accesso alle unità | Meccanismo di accesso, collegato a PIL-02 |
| C10 Direzione artistica | Scritta (v0.1): vedi C10 |
| C11 Vincoli tecnici | Scritta (v0.1): vedi C11 |
| C12 Metodo di bilanciamento | Metriche e processo, non i numeri |
| C13 Glossario | Termini ufficiali del progetto |
| C14 Registro delle decisioni | Storico e motivazioni |
