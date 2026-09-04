# Dati dell'esperimento principale (RQ2)

Cartella separata da `data/scenarios/`, che resta la versione originale del
pilot di RQ1 e non viene modificata.

```
data/rq2/
  config/
    experiment_rq2.json          matrice, budget, conteggio dei token, regola di selezione
  scenarios/
    scenario_03.json             SOLO conversazioni: infezione su WS-114
    scenario_04.json             SOLO conversazioni: smishing su Corvara Servizi
  annotations/
    scenario_01_rq2.json         overlay sul pilot: fatti obbligatori con provenienza
    scenario_02_rq2.json         overlay sul pilot: fatti obbligatori con provenienza
    scenario_03_rq2.json         domande, oracle, operazioni attese, stato atteso
    scenario_04_rq2.json         domande, oracle, entità e relazioni attese
```

## Perché conversazioni e annotazioni stanno in file diversi

I file in `scenarios/` sono l'**unico input ammesso** per costruire la memoria
(T, F, U, G). I file in `annotations/` servono **soltanto alla valutazione** e
non devono mai entrare nell'estrazione, nel retrieval o nel prompt di risposta.

La separazione è strutturale, non solo una regola scritta: `load_scenario()` in
`scripts/rq2/rq2_common.py` restituisce le sole sessioni, e il validatore
rifiuta un file di conversazioni che contenga `questions`, `expected_answer`,
`expected_operations` o altri campi di oracle.

Per SC01 e SC02 le conversazioni restano nei file del pilot: l'overlay di RQ2
aggiunge soltanto la scomposizione dei `mandatory_facts` in fatti singoli con
messaggio sorgente e tipo, e il validatore verifica che la provenienza così
ricavata coincida con i `required_evidence_ids` già dichiarati nel pilot.

## Che cosa contiene un'annotazione

Per ogni domanda: risposta attesa, fatti obbligatori (`required_facts`, ognuno
con `fact_key`, testo, `source_message_ids`, `kind`, `negated`), informazioni
obsolete da non usare, equivalenze ammesse, comportamento atteso e
`fact_present_in_corpus`.

In più, per SC03: `expected_operations` (ADD / UPDATE / DELETE / NOOP con
`claim_key`, evidenze e operazione superata) ed `expected_state` (stato della
memoria dopo l'ultima sessione, con `attivo`, `superato`, `ritirato`).

Per SC04: `graph_annotation` con entità, relazioni ed evidenze sorgente, più
`required_relations` e `required_relation_chain` per le domande relazionali.

`required_relation_chain` è la **catena esplicativa** che una risposta deve
ricostruire: è connessa ma non è un percorso semplice e può ripassare da
un'entità già incontrata. Non va confusa con il percorso minimo che il retriever
di G cerca fra due nodi, che può essere una scorciatoia corretta ma insufficiente
a spiegare il caso. La copertura delle relazioni richieste si misura **dopo** il
retrieval, nel modello di annotazione.

## Artefatti prodotti dalla pipeline

Non stanno in `data/`, ma sotto `results/rq2/`, e sono tutti riproducibili dai
file di questa cartella:

```
results/rq2/
  facts/<scenario>_facts.jsonl          fatti candidati di F (li riusa anche U)
  facts/<scenario>_extraction_log.json  prompt, configurazione, uscita grezza
  memory/<scenario>_operations.jsonl    operazioni ADD/UPDATE/DELETE/NOOP di U
  memory/<scenario>_state.json          fatti attivi + archivio dei superati e ritirati
  memory/<scenario>_update_log.json     prompt e risposte del costruttore di U
  graph/<scenario>_graph.json           nodi e archi di G
  graph/<scenario>_graph_log.json       prompt e risposta del costruttore del grafo
  retrieval_rq2.jsonl                   una riga per scenario x domanda x modalità
  generation_inputs_rq2.jsonl           i prompt di risposta, 77 celle a matrice completa
  annotation_template_rq2.jsonl         modello di annotazione con i giudizi a null
  offline_check/                        gli stessi artefatti, ma da fixture
```

Una voce di stato (`memory/<scenario>_state.json`) contiene `entry_id`,
`claim_key`, valore, `status` (`attivo`, `superato`, `ritirato`), fatti e
messaggi sorgente, ordine temporale, operazione che l'ha creata e, per i fatti
non più validi, l'operazione e la voce che li hanno sostituiti.

## Stato

Tutte le annotazioni sono **bozze da controllare**: `frozen: false`,
`review_required: true`. Non sono state approvate né congelate.

Il protocollo non è congelato. Gli artefatti presenti in
`results/rq2/offline_check/` derivano da **fixture dichiarate**
(`tests/fixtures/rq2/`) e non sono risultati sperimentali. Nessuna generazione
finale è stata eseguita e nessuna chiamata reale a Claude è ancora stata fatta
per estrazione, aggiornamenti o grafo.

## Comandi

```bash
python3 scripts/rq2/validate_rq2.py
```

```bash
python3 scripts/rq2/run_offline_check.py
```

La verifica offline costruisce l'intera matrice (77 celle) senza chiamare il
modello. La descrizione completa — architetture U e G, budget, politica di
lettura, comandi delle prove reali e limiti — è in `RQ2.md`, nella radice del
progetto.
