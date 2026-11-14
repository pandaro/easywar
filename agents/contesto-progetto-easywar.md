# Easy War: contesto e stato del progetto

Aggiornato al 14 novembre 2026. Questo file riassume dove si trova il progetto e quali documenti contano. Quando questo riassunto e un documento si contraddicono, vale il documento più recente; per il design vale sempre il canone.

## Documenti di riferimento

| Documento | Cosa contiene | Stato |
|---|---|---|
| Canone di design v0.1 | Pilastri, ambientazione, regole, economia, roster base, combattimento, Commander, fazioni, tecnologie, direzione artistica, vincoli tecnici | Fonte di verità. Da aggiornare con le novità sotto |
| Manifesto per sviluppatori v0.1 | Sintesi del canone per chi sviluppa, ambiente | Derivato dal canone |
| CLAUDE.md v0.2 | Protocollo operativo per l'agente nel repository | Da portare a v0.3 |
| Analisi di fattibilità v0.1 | Verdetto, rischi, fasi di lavoro | Il nodo degli asset è stato affrontato (vedi report toolchain) |
| Canone di modellazione | Regole per produrre un'unità: nomi, percorsi, pipeline, orientamento, texture, animazioni, trappole | Fermo al 10 novembre: mancano le varianti B e C |
| Report toolchain modelli (12 novembre) | Tre varianti di produzione provate nel motore, otto modelli, costi, problemi risolti | Ultimo report di modellazione |
| Commander, studio di silhouette v0.1 | Schede e silhouette dei nove Commander, prove di generazione immagini, modelli di riferimento, decisioni | Ultimo report di design |

## Fasi

1. Canone e manifesti: fatto.
2. Setup dell'ambiente (3-7 novembre): fatto. VSCodium con i tipi dell'API di Recoil, Git via SSH, SkyLobby, motore Recoil, Blender 5.2 Flatpak con S3O Kit.
3. Toolchain dei modelli (fino al 12 novembre): fatto. Modelli generati da script Python in Blender senza interfaccia, con un comando per unità.
4. Design delle fazioni: in corso. Fatto lo studio di silhouette dei nove Commander. Restano carro, aereo e nave di ogni fazione.
5. Fase 0 sul gioco: in corso. Prefisso `___` verificato valido. Restano mex galleggiante, nome della cartella dei gadget, push via SSH.
6. Pool base giocabile (23 unità, anche a cubi), poi unità di fazione, poi bilanciamento: da fare.

## Decisioni recenti (da riportare nel canone)

- Il prefisso `___` per il pool base è accettato dal motore. [visto dal responsabile]
- La modellazione manuale è esclusa. I modelli si producono con script, con tre varianti possibili:
  - A: primitive con libreria condivisa `easywar_lib`;
  - B: forme facettate da una sagoma;
  - C: kit Kaiser's Legos.
- Kaiser's Legos è libero da usare: la questione della licenza è chiusa.
- Esclusi: artisti esterni, risorse di terzi, generatori AI a pagamento. Rinviati: glTF e Collada.
- Budget di triangoli: circa 500 per le unità di spam, sotto 1000 per le unità comuni, 1000-2000 per quelle di rango, fino a 5000 per le poche unità iconiche.
- Capacità produttiva stimata: 2-3 unità al giorno di qualità base con l'abbonamento attuale.
- Il ramo `legacy` del repository è un abbozzo primordiale, non una fondazione.

## Decisioni aperte (del responsabile)

- `___con`: hover come dice il canone, o bipede o cingolato come nei modelli di prova?
- Licenza del gioco: serve una licenza compatibile con la GPL se si riusa codice ispirato a BAR.
- Carro di fazione: in che cosa si distingue dal `___tank` del pool base?
- Texture: due PNG per unità, oppure una grande texture condivisa per fazione come in BAR? Va deciso prima della produzione in serie.
- Variante di produzione da adottare come standard.
- Nove materiali in due texture.

## Prossimi lavori senza immagini

1. Aggiornare il canone con le decisioni recenti.
2. Chiudere le decisioni aperte.
3. Scrivere il CLAUDE.md v0.3.
4. Fare le schede testuali di carro, aereo e nave per fazione, con la scheda di produzione.
5. Scrivere le definizioni delle 23 unità del pool base e i movedefs, con modelli a cubi.
6. Chiudere la fase 0.
7. Scrivere le sezioni ancora vuote del canone (C9, C12, C13, C14).
