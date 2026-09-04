# Fixture per le verifiche offline di RQ2

**Questi file non sono risultati sperimentali.** Sono dati finti, scritti a
mano, che servono a un solo scopo: far girare l'intera matrice
T / F / U / G / FULL_HISTORY senza chiamare nessun modello, così da poter
controllare selezione, budget, provenienza, stato della memoria e formato delle
tracce.

| File | Che cosa simula |
|---|---|
| `scenario_02_facts_fixture.jsonl` | l'uscita che l'estrattore di F *potrebbe* produrre su SC02 |
| `scenario_03_facts_fixture.jsonl` | la stessa cosa su SC03 (30 fatti candidati) |
| `scenario_04_facts_fixture.jsonl` | la stessa cosa su SC04 (23 fatti candidati) |
| `scenario_03_update_answers_fixture.json` | le risposte che il costruttore di U *potrebbe* dare su SC03, una per sessione |
| `scenario_04_update_answers_fixture.json` | la stessa cosa su SC04 |
| `scenario_04_graph_answer_fixture.json` | la risposta che il costruttore del grafo *potrebbe* dare su SC04 |
| `scenario_03_update_answers_rejected_fixture.json` | **fixture artificiale**: due proposte volutamente sbagliate, per mostrare il rifiuto |

I file `*_answers_fixture.json` contengono **risposte finte del modello**, non
stati o grafi già pronti: operazioni, stato, archivio e grafo vengono prodotti
dal codice vero (`build_memory_updates.py`, `build_graph.py`) leggendo queste
risposte al posto di una chiamata a Claude, tramite
`scripts/rq2/fixture_replay.py`. Così la verifica offline esercita davvero
l'applicazione delle operazioni e la costruzione del grafo, non solo la lettura
di un file.

Ogni file si dichiara con `"fixture": true`: `fixture_replay` rifiuta un file
che non lo dichiara.

## Difetto inserito apposta

Nella fixture di SC02 il fatto `SC02-F009` conserva soltanto *«token validi una
sola volta»* e **perde la scadenza dopo 15 minuti**, che nel messaggio
`SC02-S2-U1` è presente.

È voluto. Serve a verificare che le tracce sappiano distinguere i casi che la
roadmap chiede di non confondere:

1. **fatto perso o alterato nell'estrazione** — è il caso di `SC02-F009`: il
   messaggio sorgente è quello giusto, la provenienza risulta valida, ma il
   contenuto obbligatorio non c'è più. Nessun controllo automatico basato sugli
   identificatori può accorgersene: per questo `fact_preserved_in_memory` resta
   `null` e va annotato a mano;
2. **fatto conservato ma non recuperato** — il fatto esiste in memoria ma non
   entra nel contesto entro il budget;
3. **risposta errata nonostante l'evidenza disponibile** — il fatto è nel
   contesto e la risposta è comunque sbagliata.

Su SC03 e SC04 le fixture sono invece coerenti con i messaggi: servono a
esercitare ADD / UPDATE / DELETE / NOOP, l'archivio dei fatti superati e il
recupero relazionale, non a simulare un errore di estrazione.

## La fixture artificiale del rifiuto

`scenario_03_update_answers_rejected_fixture.json` è **tenuta separata** da
`scenario_03_update_answers_fixture.json` e si dichiara con `"artificial": true`.

Contiene due proposte volutamente non applicabili — un UPDATE verso una voce
inesistente e un UPDATE verso una voce con `claim_key` diverso — e serve a un
solo scopo: mostrare che vengono rifiutate senza toccare stato e archivio. Il
rifiuto del primo UPDATE ne provoca un terzo a cascata, perché la voce che
avrebbe creato non esiste.

**Non rappresenta il comportamento atteso del modello** e non va usata per
nessuna metrica. La fixture normale di SC03 non produce nessun rifiuto, e un
test lo verifica.

## Cosa non fare con queste fixture

- non copiarle in `results/rq2/facts/`, `results/rq2/memory/` o
  `results/rq2/graph/`, che sono i percorsi degli artefatti veri;
- non usarle per calcolare metriche;
- non presentarle come uscite del modello.

I fatti veri devono venire da `scripts/rq2/extract_facts.py`, le operazioni da
`scripts/rq2/build_memory_updates.py` e il grafo da `scripts/rq2/build_graph.py`,
tutti eseguiti senza `--dry-run` e senza runner di fixture.
