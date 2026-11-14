# Easy War: Commander e fazioni, design allineato (draft 1)

Nov 14, 2026 · @bio

## Scopo e stato

Questo documento allinea il design dei nove Commander con l'identità delle nove fazioni di Easy War (RTS in stile Total Annihilation su Recoil Engine). È destinato all'agente coordinatore e al repository del progetto, e sostituisce come riferimento i due documenti di lavoro del 12-14 novembre 2026 (studio di silhouette e prompt per i generatori), che restano come storico.

**Stato: draft 1.** Ogni fazione ha una regola di forma decisa e un'immagine di riferimento in bianco e nero, vista frontale. Il responsabile accetta il set come prima bozza: alcuni modelli sono buoni, altri vanno rifatti. Nessuna immagine è definitiva.

**Fuori da questo documento:** armi (arriveranno con l'unfold), evoluzioni, viste laterali e posteriori, tutte le unità diverse dal Commander, schede di produzione 3D.

## Regole comuni dei Commander

Otto Commander sono androidi umanoidi bipedi; Omega è l'unico esapode. Le regole che seguono valgono per tutti, salvo dove la scheda di fazione dice altro.

| Regola | Valore |
| --- | --- |
| Taglia | 200 cm, elmo compreso |
| Proporzioni | Eroiche, circa 7-7,5 teste. Eccezioni volute: Sigma (grasso, arti corti) e Lambda (scheletro massiccio, 80 cm di spalle) |
| Volumi | Circa 24 solidi semplici: 2 piedi, 2 caviglie, 2 gambe inferiori, 2 ginocchia, 2 femori, 2 mani, 2 avambracci, 2 gomiti, 2 omeri, 2 spalle, 1 testa-elmo, 1 collo, 1 torace, 1 bacino. Polsi opzionali |
| Torace | Un solo monoblocco; la sua forma frontale è il segno della fazione e tutto il resto si innesta su di lui |
| Linee | Poche: ogni volume è un solido pulito, senza pannelli o incisioni interne |
| Braccio di costruzione | Cannone a nanoparticelle con batterie, integrato nell'avambraccio sinistro del robot (a destra di chi guarda), per tutte le fazioni; ha la forma dello stile di fazione |
| Colore del giocatore | Spallacci, cintura sul bacino, pettorale, gomiti, ginocchia. Omega da decidere (proposta: cornice della finestra e anelli alla radice dei tentacoli) |
| Armi | Nessuna sul Commander di base: arrivano con l'unfold |
| Materiale | Si legge da lontano da forma e palette; da vicino il dettaglio dà carattere |
| Produzione | Modello 3D da 500 a 1000 triangoli, due texture, generato con script Python per Blender |

La leggibilità si verifica così: la sagoma riempita di nero e ridotta a 60 px di altezza deve far capire la fazione senza colori né dettagli.

## Allineamento fazione e Commander

Ogni Commander deve raccontare con la sola sagoma il tratto di gioco della sua fazione. La colonna "Come lo racconta" è la proposta dell'agente designer per legare le due cose: va confermata dal coordinatore.

| Fazione | Tratto di gioco | Carattere | Commander | Come lo racconta | Pettorale |
| --- | --- | --- | --- | --- | --- |
| Alpha | Nessuno (baseline) | Il monolite: avanza senza trucchi | Il robot da guerra per antonomasia, nella tradizione dei grandi robot giapponesi | È il riferimento: tutti gli altri si misurano da lui | W larga e bassa |
| Gamma | Cloak | Imboscata e ricognizione | Snello, fatto di punte e angoli acuti | Sagoma sottile e tagliente, da predatore che non si vede | Triangolo, punta in basso |
| Lambda | Paralisi | Arma temibile a ogni scala | Scheletro portante di mecha in titanio, senza coperture | Il non morto meccanico: inquieta prima ancora di colpire | Gabbia toracica aperta su sterno pieno |
| Delta | Autoheal | Resistenza e attrito | Massiccio, solidi pieni ad angoli ottusi | Corazza densa, sagoma a triangolo rovesciato: incassa e resta in piedi | Pentagono |
| Joker | Resurrezione e cattura | L'anomalia: trasforma le perdite in risorse | Chimera di cliché: ogni parte è un luogo comune diverso | Sembra rimesso insieme con pezzi di recupero, come le unità che cattura e risveglia | Piastra anonima, l'unico pezzo normale |
| Theta | Terraforming | Il campo di battaglia è un'arma | Statua di blocchi: cubi e parallelepipedi a 90 gradi | Fatto della stessa materia del terreno che modella | Quadrato |
| Zeta | Self-reproducing | Espansione e inganno | Chimera di animali: un animale per zona del corpo | Organismo che cresce e si ricombina, mai uguale a sé stesso | Piastra liscia e larga |
| Sigma | Scudi | Controllo dello spazio | Lottatore di sumo: grasso e tondo, sfere ed ellissoidi | Occupa lo spazio e non si sposta: è lo scudo fatto corpo | Cerchio |
| Omega | Combat Constructor, Drain | Prima linea che si alimenta del nemico | Esapode: sfera con sfera interna sospesa e sei tentacoli | Polpo che afferra e prosciuga | Nessuno: finestra sulla sfera |

**Materiali e palette provvisorie** (base, scuro, accento; da verificare in gioco)

| Fazione | Materiale | Palette |
| --- | --- | --- |
| Alpha | Corten, ruggine | #8B4A2B, #3A2418, #C8C2B8 |
| Gamma | Fibra di carbonio: nero opaco con tessitura grigia sottilissima | #2B2D30, #121314, #6E7378 |
| Lambda | Titanio liscio, anodizzato blu-viola | #8A8F98, #3B3F46, #5B4FA8 |
| Delta | Alluminio mandorlato grigio satinato (rilievi a mandorla a spina di pesce, non rombi) | #B9BDC2, #5E6369, #E6E8EA |
| Joker | Plastica stampata, colori non troppo vivi | #F2D23C, #2A2A2A, #E8F0F5 |
| Theta | Granito grigio | #9E8E86, #4A4440, #D8CFC6 |
| Zeta | Organico di sintesi: rosso-rosa, umido, muscolare | #A8434E, #4A1C24, #E8B7A8 |
| Sigma | Fibra di vetro scura, nero lucidissimo con riflessi da ossidiana | #16141C, #050507, #5C3A7A |
| Omega | Fibra vegetale secca, verde-bruna, a corda | #6B6A3A, #3A3020, #A89A5E |

## Schede delle nove fazioni

Per ogni Commander: regola di forma, dettagli decisi, stato del modello di riferimento e cosa resta da fare.

### Alpha (aaa)

- **Regola di forma:** nessuna, per scelta. Deve solo essere il robot da guerra per eccellenza: figo, accattivante, inconfondibilmente robot.
- **Dettagli decisi:** elmo rotondo con antenna, due sensori auricolari, visore a W, pettorale a W. Direzione futura: cresta a V, ali sulle spalle, prese d'aria sul petto, posa eroica a gambe larghe. Nei prompt si descrivono gli elementi, non si nominano opere esistenti.
- **Modello:** versione Canva, valida ma "poco gundam-mazinga".
- **Da fare:** nuovo giro nella direzione dei grandi robot giapponesi.

### Gamma (ggg)

- **Regola di forma:** solidi derivati dal triangolo (piramidi, rombi, coni, cunei), angoli acuti, niente curve né blocchi squadrati.
- **Dettagli decisi:** elmo a piramide rovesciata con visore a fessura, spallacci a cuneo, gomiti e ginocchia a punta, piedi a cuneo.
- **Modello:** versione Canva, tenuta ma poco convincente.
- **Da fare:** valutare un nuovo giro.

### Lambda (lll)

- **Regola di forma:** scheletro portante di un mecha in titanio nudo, senza coperture. Si prende un robot massiccio come Delta e gli si tolgono le corazze. Ossa a barre dritte e sezione tonda, giunti meccanici, nessuna forma d'osso umano, nessun traliccio.
- **Dettagli decisi:** colonna vertebrale ad anelli (15 cm); costole con pieghe a spigolo chiuse su uno sterno pieno; bacino a telaio di barre; testa squadrata con un occhio centrale, bocca verticale, due orecchie, un'antenna; cannone tra due aste dell'avambraccio.
- **Modello:** scelto il 13 novembre, fatto da un generatore a partire da uno schema vettoriale dell'agente.
- **Da fare:** semplificare (testa squadrata invece del teschio tondo, spalle senza ruote dentate, meno linee su bacino e gambe).

### Delta (ddd)

- **Regola di forma:** solidi pieni ad angoli ottusi (pentagoni, esagoni, ottagoni). Sagoma a triangolo rovesciato: spalle larghe, vita più stretta.
- **Dettagli decisi:** elmo ottagonale con visore largo, spallacci esagonali, piedi a blocco esagonale.
- **Modello:** versione Canva, buona.
- **Da fare:** togliere linee e rifinire.

### Joker (jjj)

- **Regola di forma:** chimera di cliché. Ogni parte del corpo è un luogo comune diverso; asimmetrico, in plastica, ma sempre leggibile come robot da guerra.
- **Dettagli decisi:** uncino da pirata, gamba di legno con piede a pattino, spallaccio a groviera, occhio da ciclope, cresta punk, antenna, uno spallaccio corazzato normale.
- **Modello:** scelto; piace molto al responsabile.
- **Da fare:** ripulire. Sagoma vicina ad Alpha: rischio accettato per ora.

### Theta (ttt)

- **Regola di forma:** statua di blocchi di granito, solo cubi e parallelepipedi, angoli a 90 gradi.
- **Dettagli decisi:** elmo cubico con feritoia, arti a scatola, ugello a profilo quadrato.
- **Modello:** immagine OpenAI; fa anche da riferimento di stile del tratto per gli altri.
- **Da fare:** rifarla senza filigrana.

### Zeta (zzz)

- **Regola di forma:** chimera di animali, un animale per zona del corpo, su un corpo massiccio da toro, in volumi muscolari di sintesi.
- **Dettagli decisi:** muso da topo (appuntito, incisivi, niente orecchie), corna da toro corte e leggermente inclinate verso l'alto, spallacci a penne di armatura pesante, braccio da pesce (pinne e squame) solo sul lato della mano, piedi da rapace a tre artigli, cannone corto rivolto in basso.
- **Modello:** scelto come concept.
- **Da fare:** applicare le ultime modifiche (corna, spallacci, pinne, cannone).

### Sigma (sss)

- **Regola di forma:** lottatore di sumo. Grasso, non muscoloso, fatto solo di sfere, ellissoidi e loro sezioni. Sagoma a pera: la parte più larga è la pancia.
- **Dettagli decisi:** spalle piccole e cadenti, collo quasi assente, testa sferica piccola con visore a oblò, arti corti e grossi, cintura da sumo sul bacino (zona colore del giocatore), piedi a mezza sfera.
- **Modello:** scelto il 14 novembre, giudicato ottimo.
- **Da fare:** nulla per ora.

### Omega (ooo)

- **Regola di forma:** esapode, polpo meccanico. Sfera esterna grande come un torace, con una finestra; dentro, una sfera più piccola sospesa magneticamente fa da cervello.
- **Dettagli decisi:** sei tentacoli a catena, tre in basso come gambe e tre in alto (due ai lati, uno verso l'alto); sulla sfera due occhi, due sensori audio, sensori vari, un'antenna; la punta di un tentacolo è l'ugello di costruzione.
- **Modello:** si capisce l'idea, non definitivo.
- **Da fare:** finestra con sfera interna, togliere i crateri; decidere le zone del colore giocatore.

## Leggibilità del set

Con il nuovo Sigma, sette sagome su nove si riconoscono anche a 60 px; restano da staccare Alpha e Joker.

| Esito a 60 px | Fazioni | Perché |
| --- | --- | --- |
| Si riconosce subito | Gamma, Lambda, Zeta, Sigma, Omega | Punte a stella; spalle larghe e cannone lungo; ali e corna; pancia a pera; tentacoli |
| Si riconosce per la massa | Delta, Theta | I due più larghi tra gli umanoidi: Theta squadrato, Delta tondeggiante. Da allontanare ancora |
| Si confondono | Alpha, Joker | Stessa corporatura e stessa posa; di Joker restano uncino e gamba sottile |

Nota tecnica: nella versione nera gli spazi vuoti tra le costole di Lambda risultano anneriti, perché il riempimento chiude i buchi interni. La sagoma vera di Lambda è più traforata.

Le due tavole qui sotto sono il set del draft 1: prima le linee, poi le sagome nere con la stessa figura a 60 px.

&#91;image: I nove Commander del draft 1, in linea, alla stessa altezza\]

&#91;image: I nove Commander del draft 1 riempiti di nero, con la versione a 60 px sotto ciascuno\]

## Metodo di lavoro

Le immagini nascono da generatori gratuiti (Canva con Nano Banana, OpenAI, altri). Quello che ha funzionato:

1. Un prompt completo per fazione, in inglese, sotto i 1.500 caratteri: il campo di Canva tronca intorno a quella soglia. Un'intestazione comune con tabella a nove righe è stata provata e scartata.
2. Intestazione di stile fissa: line art nera uniforme su bianco, niente ombre né testo, aspetto low-poly, vista frontale ortogonale, quadrato 1:1, figura all'85% dell'altezza, "Original design".
3. Scrivere sempre "left forearm (on the viewer's right)": senza, i generatori sbagliano lato in circa metà dei casi.
4. Non nominare opere esistenti nei prompt; descriverne gli elementi.
5. Partire da un'immagine che piace e chiedere una o due modifiche per volta.
6. Quando il testo non basta, uno schema vettoriale pulito disegnato dall'agente guida il generatore (ha funzionato per Lambda). Gli schemi da soli, come immagine finale, sono stati scartati.

I prompt aggiornati sono nel documento di lavoro "Easy War: prompt per Nano Banana, Commander v0.1". Quelli di Sigma, Lambda, Zeta e Joker sono stati riscritti il 14 novembre; solo Sigma è stato provato.

## Punti aperti e prossimi passi

**Da decidere (coordinatore o responsabile)**

- [ ] Confermare la colonna "Come lo racconta" della tabella di allineamento.
- [ ] Aggiornare il canone del gioco con le regole di questo documento (umanoidi, 24 volumi, torace monoblocco, cannone a sinistra, Omega esapode, Lambda scheletro, le due chimere, Sigma sumo, Alpha senza regole di forma, materiali).
- [ ] Zone del colore giocatore per Omega.
- [ ] Riscrivere la colonna Carattere nel tono del gioco.

**Secondo giro dei modelli** (serve un generatore)

- [ ] Alpha nella direzione dei grandi robot giapponesi.
- [ ] Lambda semplificato.
- [ ] Zeta con le ultime modifiche.
- [ ] Omega con finestra e sfera interna.
- [ ] Delta con meno linee.
- [ ] Theta senza filigrana.
- [ ] Gamma da rivalutare.
- [ ] Tratto uniforme: rifare i nove con lo stesso generatore e lo stesso stile, con Theta come riferimento.

**Fase successiva**

- [ ] Viste laterale e posteriore dei Commander.
- [ ] Schede di produzione per Blender (500-1000 triangoli, due texture).
- [ ] Poi le altre unità, le evoluzioni e le armi (unfold).
