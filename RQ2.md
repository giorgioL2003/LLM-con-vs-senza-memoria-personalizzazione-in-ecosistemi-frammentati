# Esperimento principale RQ2

**Stato:** dataset e pipeline **T / F / U / G / FULL_HISTORY** costruiti ed
eseguibili offline sull'intera matrice (77 celle). Protocollo **non congelato**,
annotazioni **non approvate**, nessuna generazione finale eseguita, nessuna
chiamata reale a Claude ancora effettuata per estrazione, aggiornamenti o grafo.

**Domanda:** a parità di informazioni accessibili, come cambia la capacità del
modello di continuare l'attività quando la memoria viene *organizzata* in modo
diverso?

Il riferimento è `roadmap_progetto_tirocinio.md` (4 settembre 2026).
`EXPERIMENT.md` e gli script nella radice di `scripts/` descrivono il **pilot**
di RQ1 e restano invariati.

## 1. Separazione dal pilot

| | Pilot (RQ1) | Esperimento principale (RQ2) |
|---|---|---|
| Scenari | `data/scenarios/` | `data/rq2/scenarios/` (SC03, SC04) |
| Oracle e annotazioni | dentro i file di `data/scenarios/` | `data/rq2/annotations/` |
| Configurazione | costanti in `scripts/` | `data/rq2/config/experiment_rq2.json` |
| Codice | `scripts/*.py` | `scripts/rq2/*.py` |
| Risultati | `results/*.jsonl` | `results/rq2/` |
| Test | `tests/test_*.py` | `tests/test_rq2_*.py` |

SC01 e SC02 vengono **riusati senza modifiche**: `scripts/rq2/rq2_common.py`
legge i file del pilot in sola lettura e ne estrae le sole sessioni. Le
annotazioni che RQ2 aggiunge stanno in file separati
(`data/rq2/annotations/scenario_01_rq2.json`, `..._02_rq2.json`) e il
validatore verifica che la provenienza ricavata da quelle annotazioni coincida
con le evidenze già dichiarate nel pilot.

I vincoli specifici del pilot non sono stati toccati: `validate_scenarios.py`
continua a cercare solo `data/scenarios/scenario_*.json` con la copertura attesa
0/14, 5/14, 12/14, e `summarize_evaluation.py` continua a lavorare sulle 56
righe di RQ1. RQ2 non aggiunge scenari a quella cartella e non scrive in
`results/`.

## 2. Dataset

| Scenario | Fenomeno | Sessioni | Messaggi utente | Domande |
|---|---|---:|---:|---:|
| SC01 Asteria Docs | continuità (pilot riusato) | 4 | 4 | 7 |
| SC02 Lumen Market | rappresentazione, confronto T/F (pilot riusato) | 4 | 4 | 7 |
| SC03 infezione su WS-114 | gestione degli aggiornamenti, confronto F/U | 4 | 8 | 7 |
| SC04 smishing su Corvara Servizi | relazioni distribuite, confronto U/G | 4 | 7 | 7 |

**SC03** contiene un'ipotesi iniziale (ransomware), una revisione basata su
evidenze positive (lettura del database credenziali, esfiltrazione di 240 MB),
una conferma di laboratorio (famiglia sintetica `Kelpie`, infostealer),
un'evidenza **ritirata senza sostituzione** (il file con richiesta di pagamento,
residuo di un'esercitazione interna), una **conferma ripetuta** che non cambia
nulla, un'attività che passa da aperta a completata, un punto dichiarato **non
determinato** (il vettore iniziale) e un vincolo locale sul rapporto. Servono a
esercitare ADD, UPDATE, DELETE e NOOP.

**SC04** contiene la catena `UT-207 → SMS-01 → URL-01 → pagina falsa` e
`UT-207 → ACC-207 → LOGIN-07 → RULE-01`, distribuita su tre sessioni, con una
valutazione iniziale superata (spam generico, nessun contatto con il link) e un
punto non determinato (come sia stato ottenuto il numero di telefono).

In entrambi l'ultima sessione **non riassume** la storia precedente, e ciascuno
ha una domanda su un'informazione mai fornita che richiede astensione.

## 3. Configurazione

`data/rq2/config/experiment_rq2.json` rende esplicita la matrice della roadmap:

| Scenario | T | F | U | G | FULL_HISTORY |
|---|:-:|:-:|:-:|:-:|:-:|
| SC01 | sì | – | – | – | sì |
| SC02 | sì | sì | – | – | sì |
| SC03 | – | sì | sì | – | sì |
| SC04 | – | – | sì | sì | sì |

`planned` è questa riga; `runnable_now` è il sottoinsieme davvero eseguibile
oggi, e da questo blocco **coincide con `planned`**: tutte e 77 le celle sono
costruibili. Il validatore confronta `planned` con la matrice della roadmap
scritta in `scripts/rq2/validate_rq2.py` e rifiuta una modalità dichiarata
eseguibile ma non implementata.

### Budget: 200 token sul contesto realmente formattato

Il budget è uguale per T, F, U e G; FULL_HISTORY ne resta fuori.

Si applica al **blocco di contesto come finisce nel prompt**, non al solo testo:
contano anche identificatori, provenienza, stato temporale e relazioni. Restano
fuori le istruzioni comuni e la domanda, identiche in tutte le modalità.

È una correzione rispetto alla versione precedente, che contava quasi solo il
testo. L'effetto misurato sulle fixture è consistente:

| Modalità | Overhead per elemento | Elementi nel contesto (media, budget 200) |
|---|---:|---:|
| T (messaggio) | ~7 token | 1,4–2,0 |
| F (fatto con provenienza) | ~13 token | 6,1–7,0 |
| U (fatto con stato) | ~15 token | 5,6–6,4 |
| G (arco con stato) | ~20 token | 6,1 |

Su SC02, F passava da ~10 elementi contati male a 6,1 contati bene: prima
riceveva circa il 40% di contesto in più del budget dichiarato.

Ogni riga di retrieval registra token del contenuto, token dell'overhead
strutturale, totale, elemento che ha causato l'arresto ed eventuale superamento
dovuto al primo elemento.

**Conteggio dei token:** espressione regolare locale (parole e numeri contano 1,
ogni segno di punteggiatura conta 1; gli spazi e gli a capo no, quindi i token
del blocco sono la somma dei token delle righe). È deterministico e senza
dipendenze, e **non** è il tokenizzatore del modello: serve a dare a tutte le
modalità lo stesso metro, non a stimare il costo reale in token dell'API. Un
identificatore come `SC02-S1-U1` vale 5 token con questo metodo.

**Regola di selezione (deterministica):** ranking TF-IDF/coseno; parità risolta
dall'ordine di comparsa nello scenario; esclusi gli elementi con punteggio
nullo; si aggiunge finché la riga formattata sta nel budget e ci si **ferma al
primo elemento che non entra**, così la selezione è sempre un prefisso del
ranking; se il primo elemento supera da solo il budget viene incluso e
segnalato; nessun elemento viene troncato.

Queste scelte sono di sviluppo, non un protocollo congelato. In particolare il
valore 200 era stato fissato prima di includere l'overhead: va verificato che
resti adeguato per F, U e G.

## 4. Architettura F

`scripts/rq2/extract_facts.py` legge **una sessione alla volta, in ordine
cronologico**. Il prompt della sessione *k* contiene le istruzioni di
estrazione, i fatti già estratti dalle sessioni precedenti e i soli messaggi
utente della sessione *k*. Non contiene domande, oracle, risposte attese,
sessioni future né messaggi dell'assistente.

Ogni fatto ha identificatore, testo, messaggi sorgente, ordine temporale, tipo
(`ipotesi`, `conferma`, `osservazione`, `decisione`, `stato`, `ritiro`) e
`negated`. F **non applica UPDATE né DELETE**: un fatto superato resta accanto a
quello nuovo. Gli stessi fatti candidati saranno l'ingresso di U.

Prompt, configurazione e uscita grezza del modello vengono salvati in
`results/rq2/facts/`. Gli errori dell'estrattore non vengono corretti a mano:
un fatto con provenienza non valida viene salvato con `provenance_valid: false`.

## 5. Architettura U

`scripts/rq2/build_memory_updates.py` **non riestrae nulla**: legge lo stesso
file di fatti candidati prodotto per F e, sessione per sessione in ordine
cronologico, decide per ogni fatto una fra **ADD**, **UPDATE**, **DELETE** e
**NOOP**.

Il costruttore vede i fatti della sessione in lavorazione, lo stato corrente
della memoria e l'archivio storico. Non vede mai domande, oracle, operazioni
attese, stato atteso, relazioni attese o sessioni future.

**Il modello propone, il codice applica o rifiuta.** L'aggiornamento dello stato
è implementato in `apply_operation()`: è lì che un UPDATE sposta il fatto
precedente in archivio con `superseded_by_entry` verso la nuova versione, e che
un DELETE lo marca `ritirato` senza sostituzione.

### Rifiuto atomico delle proposte non applicabili

Lo schema delle operazioni è verificato prima di toccare lo stato:

- **ADD** e **NOOP** devono avere `target_entry_id` uguale a `null`;
- **UPDATE** e **DELETE** devono indicare un `target_entry_id` che **esiste**, è
  ancora **attivo** e ha lo **stesso `claim_key`** dell'operazione.

Se una sola di queste condizioni manca, l'operazione è rifiutata in blocco:

- non si cerca un target sostitutivo con lo stesso `claim_key`;
- non si converte UPDATE o DELETE in ADD;
- stato e archivio restano identici, e le impronte `state_before_fingerprint` e
  `state_after_fingerprint` lo dimostrano.

Ogni operazione registra `proposed_operation`, `applied_operation` (`null` se
rifiutata), `applied`, `rejection_reason`, `target_entry_id`, le impronte dello
stato prima e dopo, il numero di fatti attivi prima e dopo, `raw_proposal` (la
proposta grezza del modello), `provenance_valid` e il riferimento alla risposta
grezza nel registro.

Le operazioni rifiutate **restano negli artefatti** e vanno contate come errori
di gestione della memoria, non come guasti dello script. Un rifiuto può
propagarsi: se un UPDATE viene rifiutato, la voce che avrebbe creato non esiste,
e un UPDATE successivo che la indicasse verrebbe rifiutato a sua volta.

Artefatti in `results/rq2/memory/`:

| File | Contenuto |
|---|---|
| `<scenario>_operations.jsonl` | una riga per operazione: `op_id`, `proposed_operation`, `applied_operation`, `applied`, `rejection_reason`, `claim_key`, valore, `target_entry_id`, fatti e messaggi sorgente, ordine temporale, fatto superato, motivazione del sistema, `raw_proposal`, modello, configurazione, validità della provenienza, impronte dello stato prima e dopo |
| `<scenario>_state.json` | `current` (fatti attivi) e `archive` (superati e ritirati, con `superseded_by_op` e `superseded_by_entry`) |
| `<scenario>_update_log.json` | prompt, istruzioni, configurazione e risposte grezze, sessione per sessione |

### Politica di lettura

Dichiarata in `question_scope()` e decisa **solo dal testo della domanda**:

- se compare un marcatore di cambiamento o di passato (`superat`, `inizial`,
  `precedent`, `ritirat`, `cambia`, `sostitu`, `è ancora`, `non è più`, …) la
  domanda è **storica** e la lettura comprende fatti attivi, superati e
  ritirati, ognuno con lo stato scritto nel contesto;
- altrimenti è una domanda sullo **stato corrente** e la lettura comprende solo
  i fatti attivi.

L'oracle non entra nella regola. Sulle 28 domande la regola classifica come
storiche SC01-Q2, SC01-Q3, SC02-Q2, SC03-Q2, SC03-Q3, SC03-Q6 e SC04-Q2.

Un fatto ritirato resta consultabile come storia con lo stato `ritirato`, ma non
è mai leggibile come valido nel presente.

## 6. Architettura G

`scripts/rq2/build_graph.py` parte **dagli stessi fatti candidati e dallo stesso
stato aggiornato di U** e aggiunge solo l'organizzazione relazionale. Il grafo è
un file JSON con liste di nodi e archi: nessun database.

- **nodo:** `node_id`, `type`, `label`, `aliases`, `source_fact_ids`,
  `source_message_ids`, validità della provenienza;
- **arco:** `edge_id`, soggetto, relazione, oggetto, `state` (`attivo`,
  `superato`, `ritirato`), `source_fact_ids`, `source_message_ids`, validità
  della provenienza.

La provenienza degli archi risale ai messaggi attraverso i fatti: un arco che
cita un fatto inesistente viene salvato con `provenance_valid: false`.

Il costruttore non vede domande, oracle, `required_relations` o `required_relation_chain`.

**Recupero relazionale**, deterministico e indipendente dall'oracle:

1. **nodi citati nella domanda**: i nodi il cui identificatore, alias o etichetta
   compare nel testo della domanda come sequenza contigua di parole;
2. **nodi dalle voci di memoria**: i nodi citati dalle prime `max_seed_items`
   voci di U per punteggio, o che ne condividono un fatto sorgente;
3. **percorsi minimi** fra tutte le coppie di nodi iniziali, con visita in
   ampiezza deterministica (vicini in ordine di identificatore dell'arco),
   limitati a `max_hops` collegamenti (default 3);
4. **priorità nel budget** agli archi dei percorsi, poi alle voci di memoria
   iniziali, poi agli altri archi pertinenti (incidenti a un nodo toccato), poi
   alle restanti voci;
5. **arresto** con la stessa regola di budget delle altre modalità.

Vengono salvati: nodi individuati nella domanda (con il nome che ha prodotto la
corrispondenza), nodi ottenuti dalle voci, coppie esaminate, percorsi trovati
(con gli archi che li compongono) e scartati (con il motivo), archi selezionati e
non selezionati con la ragione dell'esclusione, archi resi non leggibili dallo
stato temporale, token usati e limite di collegamenti applicato.

Se un percorso non entra per intero nel budget **non viene troncato né dato per
riuscito**: `topological_paths_complete_in_context` diventa `false` e il percorso elenca in
`missing_edge_ids` gli archi che mancano.

### Percorso topologico e catena esplicativa non sono la stessa cosa

Sono due nozioni diverse e il progetto le tiene separate.

Il **percorso topologico** è quello che trova il retriever: la sequenza più
breve di archi che collega due nodi iniziali. `topological_paths_complete_in_context`
dice soltanto che tutti gli archi di quei percorsi sono entrati nel budget.

La **catena esplicativa** è quella annotata nell'oracle in
`required_relation_chain`: la sequenza di relazioni che una risposta deve
ricostruire per spiegare il caso. Può ripassare da un'entità già incontrata e
quindi **non è un percorso semplice**. In SC04-Q3 la catena torna su `UT-207`
dopo `URL-01`.

Un grafo può collegare due nodi con una **scorciatoia corretta ma
insufficiente**: su SC04-Q3 il retriever chiude `UT-207 → ACC-207 → RULE-01`,
che è vero, ma salta `SMS-01 contiene URL-01` e `UT-207 ha aperto URL-01`, senza
cui la risposta non spiega come si sia arrivati alla regola di inoltro.

Perciò vanno distinti cinque livelli, in quest'ordine:

| # | Livello | Dove si misura |
|---|---|---|
| 1 | percorso topologico trovato | `topological_paths_found` nel retrieval |
| 2 | percorso topologico interamente nel contesto | `topological_paths_complete_in_context` |
| 3 | copertura delle relazioni richieste dall'oracle | `relations_present_by_provenance` nel modello di annotazione |
| 4 | correttezza semantica del contenuto recuperato | `relation_content_correct`, manuale |
| 5 | completezza della risposta | `answer_class`, manuale |

I livelli 1 e 2 sono proprietà del retriever, il 3 è automatico ma solo per
provenienza, il 4 e il 5 sono giudizi umani. **Un livello soddisfatto non implica
il successivo.**

Il retriever **non viene adattato** per far entrare nel contesto le relazioni che
l'oracle richiede: se non ci arriva, è un fallimento di retrieval e deve restare
osservabile come risultato. L'oracle interviene solo dopo, in fase di
valutazione.

### Politica temporale sugli archi

La regola corrente/storia di U vale anche per il grafo, e agisce **prima** della
ricerca dei percorsi: in una domanda sullo stato corrente un arco `superato` o
`ritirato` non è leggibile e non può nemmeno fare da ponte fra due nodi; in una
domanda storica entra con lo stato scritto nel contesto. La decisione dipende
solo dal testo della domanda.

**Limiti dichiarati:** una domanda che non nomina entità e le cui voci di memoria
non ne citano produce zero nodi iniziali, e in quel caso G si comporta come la
memoria di U su cui è costruito; i nodi iniziali dipendono dalla qualità di
identificatori, alias ed etichette prodotti dal costruttore del grafo; i percorsi
collegano i nodi iniziali fra loro, quindi un arco pertinente alla domanda ma
fuori da ogni percorso entra solo se avanza budget.

## 7. Valutazione

`scripts/rq2/build_annotation_template_rq2.py` produce una riga per prova con i
campi automatici già calcolati e i giudizi a `null`. Serve a distinguere:

| Caso | Come si riconosce |
|---|---|
| fatto perso o alterato nell'estrazione | `fact_in_memory_by_provenance: true` e `fact_preserved_in_memory: false` |
| fatto conservato ma non recuperato | `fact_preserved_in_memory: true` e `fact_in_context_by_provenance: false` |
| risposta errata nonostante l'evidenza | `fact_content_correct_in_context: true` e `answer_class` diversa da `completa` |

La memoria su cui si misura la prima riga dipende dalla modalità: i messaggi per
T e FULL_HISTORY, i fatti estratti per F, le voci di memoria (attive e in
archivio) per U, i nodi e gli archi per G. Le origini di errore ammesse sono
`raggiungibilita`, `estrazione`, `gestione`, `grafo`, `retrieval`, `risposta`,
`benchmark`.

### Traccia delle relazioni obbligatorie

Per le domande che dichiarano relazioni, il modello di annotazione aggiunge una
riga per relazione, calcolata **dopo** che il retrieval è finito:

| Campo | Origine |
|---|---|
| `relation_id`, `triple`, `source_message_ids` | annotazione |
| `selected_items_with_shared_provenance`, `selected_edges_with_shared_provenance` | automatico |
| `relation_present_by_provenance` | automatico |
| `relation_content_correct`, `relation_retrieved` | **manuali**, nascono `null` |

La provenienza condivisa **non** è prova che la relazione sia stata
rappresentata: un arco può citare lo stesso messaggio sorgente senza esprimere
quella relazione. Nelle fixture succede davvero — `SC04-E006` risulta condividere
la provenienza sia di `R06` sia di `R07`.

`evidence_complete` non diventa mai `true` da solo: vale `false` quando manca già
per provenienza almeno un fatto o una relazione obbligatoria (prova negativa
sufficiente) e resta `null` quando la provenienza c'è ma il contenuto non è
ancora stato verificato a mano.

Le annotazioni vengono lette **soltanto** qui e nel validatore. Non entrano nella
costruzione dei fatti, nella gestione di U, nella costruzione del grafo, nella
selezione dei nodi, nella ricerca dei percorsi, nel ranking o nel prompt di
risposta. Un test lo dimostra rieseguendo il retrieval con l'oracle sostituito da
valori finti e verificando che la selezione non cambi.

I campi `*_by_provenance` sono automatici e si basano sugli identificatori. **La
sola presenza del `message_id` sorgente non dimostra che il fatto sia stato
conservato correttamente**: per questo `fact_preserved_in_memory` e
`fact_content_correct_in_context` nascono `null` e vanno compilati leggendo il
testo. La fixture di SC02 contiene un caso apposito (`SC02-F009` perde la
scadenza dopo 15 minuti pur citando il messaggio giusto).

## 8. Comandi

### Verifica offline dell'intera matrice, senza chiamate al modello

```bash
python3 scripts/rq2/run_offline_check.py
```

Valida dataset e configurazione, costruisce i prompt di estrazione in dry run,
costruisce U su SC03 e SC04 e G su SC04 riproducendo **fixture dichiarate**,
mostra un'operazione applicata e le operazioni rifiutate (da una fixture
artificiale separata, con le impronte dello stato a dimostrare che nulla è
cambiato), esegue il retrieval di T, F, U e G, costruisce tutte e 77 le celle di
generazione, produce il modello di annotazione, mostra il confronto F/U su
SC03-Q5 e quello U/G su SC04-Q3 con nodi iniziali, percorsi topologici, archi
selezionati ed esclusi, copertura delle relazioni richieste dall'oracle,
`evidence_complete` e giudizi semantici ancora `null`, la politica
corrente/storia sugli archi, e verifica per impronta che nessun file del pilot
sia stato toccato.

Gli output finiscono in `results/rq2/offline_check/` e **non sono risultati
sperimentali**. Con le fixture attuali il controllo segnala che SC04-Q3 non
possiede tutta l'evidenza richiesta: è un esito diagnostico atteso e non fa
fallire la verifica.

### Test

```bash
python3 -m unittest discover -s tests -v
```

### Prime prove reali di sviluppo (consumano utilizzo)

Nessuna di queste è stata eseguita. Ogni scenario scrive su file propri, così una
prova non sovrascrive l'altra: `retrieval_scNN`, `generation_inputs_scNN`,
`generation_dev_scNN`, `annotation_template_scNN`.

**SC01 — T e FULL_HISTORY** (nessuna costruzione di memoria; 14 generazioni):

```bash
python3 scripts/rq2/run_retrieval_rq2.py --scenario scenario_01 --out results/rq2/retrieval_sc01.jsonl && python3 scripts/rq2/build_generation_inputs_rq2.py --scenario scenario_01 --retrieval results/rq2/retrieval_sc01.jsonl --out results/rq2/generation_inputs_sc01.jsonl && python3 scripts/run_generation.py --inputs results/rq2/generation_inputs_sc01.jsonl --out results/rq2/generation_dev_sc01.jsonl && python3 scripts/rq2/build_annotation_template_rq2.py --retrieval results/rq2/retrieval_sc01.jsonl --inputs results/rq2/generation_inputs_sc01.jsonl --out results/rq2/annotation_template_sc01.jsonl
```

**SC02 — T, F e FULL_HISTORY** (4 chiamate di estrazione + 21 generazioni):

```bash
python3 scripts/rq2/extract_facts.py --scenario scenario_02 && python3 scripts/rq2/run_retrieval_rq2.py --scenario scenario_02 --out results/rq2/retrieval_sc02.jsonl && python3 scripts/rq2/build_generation_inputs_rq2.py --scenario scenario_02 --retrieval results/rq2/retrieval_sc02.jsonl --out results/rq2/generation_inputs_sc02.jsonl && python3 scripts/run_generation.py --inputs results/rq2/generation_inputs_sc02.jsonl --out results/rq2/generation_dev_sc02.jsonl && python3 scripts/rq2/build_annotation_template_rq2.py --retrieval results/rq2/retrieval_sc02.jsonl --inputs results/rq2/generation_inputs_sc02.jsonl --out results/rq2/annotation_template_sc02.jsonl
```

**SC03 — F, U e FULL_HISTORY** (4 di estrazione + 4 di aggiornamento + 21 generazioni):

```bash
python3 scripts/rq2/extract_facts.py --scenario scenario_03 && python3 scripts/rq2/build_memory_updates.py --scenario scenario_03 && python3 scripts/rq2/run_retrieval_rq2.py --scenario scenario_03 --out results/rq2/retrieval_sc03.jsonl && python3 scripts/rq2/build_generation_inputs_rq2.py --scenario scenario_03 --retrieval results/rq2/retrieval_sc03.jsonl --out results/rq2/generation_inputs_sc03.jsonl && python3 scripts/run_generation.py --inputs results/rq2/generation_inputs_sc03.jsonl --out results/rq2/generation_dev_sc03.jsonl && python3 scripts/rq2/build_annotation_template_rq2.py --retrieval results/rq2/retrieval_sc03.jsonl --inputs results/rq2/generation_inputs_sc03.jsonl --out results/rq2/annotation_template_sc03.jsonl
```

**SC04 — U, G e FULL_HISTORY** (4 di estrazione + 4 di aggiornamento + 1 per il
grafo + 21 generazioni):

```bash
python3 scripts/rq2/extract_facts.py --scenario scenario_04 && python3 scripts/rq2/build_memory_updates.py --scenario scenario_04 && python3 scripts/rq2/build_graph.py --scenario scenario_04 && python3 scripts/rq2/run_retrieval_rq2.py --scenario scenario_04 --out results/rq2/retrieval_sc04.jsonl && python3 scripts/rq2/build_generation_inputs_rq2.py --scenario scenario_04 --retrieval results/rq2/retrieval_sc04.jsonl --out results/rq2/generation_inputs_sc04.jsonl && python3 scripts/run_generation.py --inputs results/rq2/generation_inputs_sc04.jsonl --out results/rq2/generation_dev_sc04.jsonl && python3 scripts/rq2/build_annotation_template_rq2.py --retrieval results/rq2/retrieval_sc04.jsonl --inputs results/rq2/generation_inputs_sc04.jsonl --out results/rq2/annotation_template_sc04.jsonl
```

In tutto sono 77 generazioni più 17 chiamate di costruzione della memoria.
`scripts/run_generation.py` è riprendibile: rilanciarlo sullo stesso file di
uscita salta le prove già completate. Ogni costruttore accetta `--dry-run` per
salvare soltanto il prompt senza chiamare il modello.

## 9. Cosa manca prima di congelare il protocollo

- **Prove reali:** estrazione, aggiornamenti e grafo non sono mai stati eseguiti
  con Claude. Finora esistono solo dry run e fixture. Le uscite vere possono
  essere peggiori delle fixture: fatti mal formati, `claim_key` incoerenti,
  UPDATE mancati, nodi inventati.
- **Controllo umano delle annotazioni:** oracle, operazioni attese, stato atteso,
  entità e relazioni di SC03 e SC04 sono ancora bozze non approvate.
- **Taratura del budget:** 200 token era stato scelto prima di contare
  l'overhead strutturale. Con l'overhead, F, U e G entrano con 6 elementi circa:
  va deciso se il valore resta adeguato.
- **Politica di lettura:** l'elenco dei marcatori di `question_scope()` è una
  prima proposta e va rivisto sulle 28 domande definitive.
- **Parametri di G:** `max_hops` (3), `max_seed_items` e `max_seed_nodes` (3) sono
  valori di sviluppo, tarati su grafi di una decina di archi.
- **Copertura relazionale:** i percorsi collegano fra loro i nodi iniziali. Un
  arco che la domanda richiede ma che sta fuori da ogni percorso minimo entra
  solo se avanza budget. Con le fixture attuali su SC04-Q3 restano fuori
  `SMS-01 contiene URL-01` e `UT-207 ha aperto URL-01`: G copre 5 relazioni su 7
  per provenienza, U ne copre 3, e `evidence_complete` è `false` per entrambe.
  È un **risultato diagnostico della fixture**, non un guasto: va deciso se
  serve una nozione di pertinenza più larga, ma la decisione non deve essere
  presa guardando questo caso per farlo passare.
- **Ancoraggio ai nodi:** dipende da identificatori, alias ed etichette prodotti
  dal costruttore del grafo. Con alias poveri, G trova meno nodi iniziali.
- **Metriche aggregate e analisi degli errori di RQ2**, cioè l'equivalente di
  `summarize_evaluation.py` e `build_error_analysis.py` per le nuove modalità,
  compresi i livelli scrittura, aggiornamento, grafo e retrieval.
- **Piano delle repliche**, se previste, da fissare prima delle esecuzioni finali.

Solo dopo questi passaggi ha senso congelare dataset, oracle, matrice, prompt,
parametri e codice ed eseguire le 77 generazioni.
