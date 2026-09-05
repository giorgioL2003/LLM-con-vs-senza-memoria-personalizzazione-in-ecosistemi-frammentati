# Esperimento principale RQ2

**Stato:** dataset e pipeline **T / F / U / G / FULL_HISTORY** costruiti ed
eseguibili offline sull'intera matrice (77 celle). Protocollo **non congelato**,
annotazioni **non approvate**, nessuna generazione finale eseguita.

**Primo giro di prove reali completato su SC02, SC03 e SC04** (63 risposte su
77). Estrazione, aggiornamenti, grafo, retrieval e generazione sono stati
prodotti con chiamate vere a Claude Sonnet 5. Sono **risultati di sviluppo: una
sola esecuzione per scenario, senza repliche**, non risultati dell'esperimento.
**Manca SC01** (T e FULL_HISTORY, 14 generazioni). Il dettaglio è nella sezione 9.

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
proposta grezza del modello), `provenance_valid`, `attempt`, `retry_of`,
`instructions_version` e il riferimento alla risposta grezza nel registro.

### Riferimenti e passata di riparazione (istruzioni `u-instructions-0.3`)

La prima prova reale su SC03 aveva prodotto tre rifiuti con una perdita di
contenuto (sezione 9.2). Due cause distinte, entrambe affrontate:

- **riferimenti confusi.** Il prompt chiedeva in `target_entry_id` «il fatto in
  memoria», e la parola «fatto» designava sia i candidati `F…` sia le voci `M…`.
  Ora le istruzioni dichiarano i due elenchi come spazi separati: gli
  identificatori sotto «Fatti nuovi da valutare» valgono solo per `fact_id`,
  quelli sotto «Stato corrente della memoria» e «Archivio» solo per
  `target_entry_id`, e un fatto senza voce in memoria non può essere bersaglio di
  un UPDATE.
- **stato che evolve dentro la sessione.** Il prompt mostra lo stato all'inizio
  della sessione, ma le operazioni vengono applicate una alla volta: una voce
  appena superata non è più un bersaglio valido. Le istruzioni ora lo dicono, e
  in più `--repair-attempts` (predefinito 1) rimanda al modello **le sole
  proposte rifiutate**, con lo stato aggiornato, cioè quello su cui verrebbero
  davvero applicate.

La riparazione **non è una correzione automatica**: il modello ridecide, e la
riproposta viene applicata o rifiutata con le stesse regole. La proposta
rifiutata resta negli artefatti con il proprio esito, collegata alla riproposta
da `retried_by` e `retry_of`. Il rifiuto atomico, il divieto di cercare un target
sostitutivo e il divieto di convertire UPDATE in ADD restano invariati.

Costo: **una chiamata in più per sessione, solo quando ci sono rifiuti**. Su SC03
le chiamate passano da 4 a 5.

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

**Eseguite SC02, SC03 e SC04** (sezione 9); **manca SC01**. Ogni scenario scrive
su file propri, così una prova non sovrascrive l'altra: `retrieval_scNN`, `generation_inputs_scNN`,
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

## 9. Prove reali di sviluppo eseguite

| Scenario | Modalità | Chiamate di costruzione | Generazioni | Errori |
|---|---|---:|---:|:-:|
| SC01 | T, FULL_HISTORY | 0 | **non eseguito** | – |
| SC02 | T, F, FULL_HISTORY | 4 estrazione | 21 | 0 |
| SC03 | F, U, FULL_HISTORY | 4 estrazione + 4 aggiornamento | 21 | 0 |
| SC04 | U, G, FULL_HISTORY | 4 + 4 + 1 grafo | 21 | 0 |

Tutte con `claude-sonnet-5`, effort `medium`, configurazione `rq2-dev-0.1`,
budget 200 token. **Nessun errore di esecuzione, nessun errore di parsing,
nessuna correzione di codice necessaria.** Su tutti e tre gli scenari è stato
verificato che nei prompt di estrazione e aggiornamento non compaiano domande,
risposte attese, chiavi dell'oracle né messaggi dell'assistente.

### 9.1 SC02 — T / F / FULL_HISTORY

23 fatti, tutti con provenienza e tipo validi. Contesto medio: T 2,0 elementi
(145,6 token di contenuto, 14 di sovraccarico); F 6,4 elementi (102,4 + 83,6).

**F conserva l'obsoleto, e su una domanda sbaglia dove T è corretto.** Su
SC02-Q4 («quale verifica rimane da completare?») F recupera `SC02-F017`
(«rimane da verificare che il collegamento dell'app mobile riporti alla
schermata di accesso», sessione 3) e risponde che restano **due** verifiche
aperte. Quella verifica è stata completata nella sessione 4 (`SC02-F019`,
`SC02-F020`), che il retrieval non ha selezionato. T, lavorando sul messaggio
intero della sessione 4, risponde correttamente. È esattamente il fenomeno per
cui SC02 è stato costruito: **F non applica UPDATE e il fatto superato resta
accanto a quello nuovo.**

Su SC02-Q6 né T né F recuperano il limite dei «15 minuti»; FULL_HISTORY sì.

### 9.2 SC03 — F / U / FULL_HISTORY

41 fatti, tutti con provenienza e tipo validi. **Verificato che F e U usano gli
stessi fatti:** identici e nello stesso ordine, e le operazioni citano
esattamente quei `fact_id`. Contesto medio: F 7,6 elementi (91,1 + 98,4); U 6,6
(84,4 + 98,6).

41 operazioni proposte: 28 ADD, 8 UPDATE, 5 NOOP, **0 DELETE**. Applicate 38,
**rifiutate 3**. Stato finale: 28 attivi, 5 superati, 0 ritirati.

**Aggiornamento riuscito:** `SC03-OP022` supera l'ipotesi ransomware
(`SC03-M005`) con «l'ipotesi è stata aggiornata da ransomware a infostealer», e
`SC03-OP025` la supera a sua volta con la conferma. La catena
`M005 → M022 → M025` è tracciabile nell'archivio.

**Conferma senza modifica:** cinque NOOP, fra cui `SC03-OP034` («la ripetizione
della verifica conferma lo stesso esito, famiglia Kelpie») con motivazione
«conferma equivalente di un fatto già presente in memoria».

**Ritiro senza sostituzione: non esercitato come DELETE.** Il file
`LEGGIMI-PAGAMENTO.txt`, che lo scenario ritira come residuo di un'esercitazione
interna, è stato trattato con un **UPDATE** (`SC03-M004 → SC03-M014`): finisce in
archivio come `superato`, non come `ritirato`. Lo stato corrente risultante è
corretto — dice che il file è stato escluso dalle evidenze — ma il fenomeno che
SC03 doveva esercitare non è stato esercitato, e `DELETE` resta senza copertura
sperimentale.

**Tre operazioni rifiutate, con una perdita dimostrata.** Due (`SC03-OP013`,
`SC03-OP020`) indicano in `target_entry_id` un **identificatore di fatto**
(`SC03-F005`, `SC03-F019`) invece di una voce di memoria; una (`SC03-OP026`)
punta a `SC03-M022`, già superata poche operazioni prima nella stessa sessione.
In tutti e tre i casi le impronte dello stato prima e dopo coincidono: il rifiuto
è stato atomico come previsto. Ma il rifiuto di `SC03-OP020` ha **cancellato da U
il volume dell'esfiltrazione**: «caricamento complessivo di 240 MB» esiste in F
(`SC03-F020`) e **non compare da nessuna parte** nello stato di U, né fra gli
attivi né in archivio. È la prima differenza di contenuto F/U osservata, ed è un
errore di gestione, non un guasto dello script.

#### Seconda prova di U su SC03, dopo la chiarificazione delle istruzioni

Rieseguita **sugli stessi fatti candidati**, senza rigenerare le 21 risposte.
Artefatti in `results/rq2/memory_repair_v3/` (e `memory_repair_v2/`, che conserva
un difetto intermedio); la prima prova resta immutata in `results/rq2/memory/`.

| | prima prova | seconda prova |
|---|---|---|
| istruzioni | `u-instructions-0.1` | `u-instructions-0.3` |
| chiamate al modello | 4 | 5 |
| operazioni | 41 | 42 |
| rifiutate | **3** | **1**, poi riproposta e applicata |
| target che non sono voci di memoria | 2 (`SC03-F005`, `SC03-F019`) | **nessuno** |
| informazione «240 MB» | **assente dallo stato** | **presente** (`SC03-M023`) |
| fatti candidati senza alcuna operazione applicata | 3 | **nessuno** |
| stato finale | 28 attivi, 5 superati | 29 attivi, 6 superati |

Le catene di supersessione sono integre in entrambe: nessuna voce superata senza
successore, nessun `superseded_by_entry` che punti fuori dallo stato. `DELETE`
resta a zero anche nella seconda prova: non è stato forzato.

**Difetto intermedio, registrato e corretto.** Con le istruzioni `0.2` la
riparazione della sessione 4 ha ricevuto un oggetto JSON singolo invece di un
array, che il parser scarta: un fatto è andato perso. La causa era
un'ambiguità del prompt di riparazione quando il fatto da rivalutare è uno solo.
`0.3` lo dice esplicitamente e la perdita non si ripresenta.

**Rifiuto residuo.** `SC03-OP020` propone ancora un UPDATE senza
`target_entry_id`: la riparazione lo recupera indicando `SC03-M019`. La
chiarificazione non ha eliminato l'errore alla prima passata, l'ha reso
recuperabile.

#### Il retrieval sulla memoria riparata (nessuna chiamata al modello)

Retrieval delle 7 domande di SC03 in modalità U sul nuovo stato, con `--state`
(parametro già esistente: **nessuna modifica al retrieval**), stessi fatti,
stesso budget, stesso ranking. Prompt costruiti e **non inviati**. Artefatti in
`results/rq2/retrieval_repair_v3/`. Verificato che senza `--state` il
comportamento predefinito resta identico alla prima prova.

**Attenzione al confronto:** gli `entry_id` sono posizionali e cambiano fra una
prova e l'altra — lo stesso `SC03-M023` indica voci diverse nelle due
esecuzioni. Il confronto va fatto sul testo.

Che cosa cambia nei contesti:

- **Q5 migliora davvero.** Il vincolo sul rapporto ora è una voce sola e
  completa («deve restare interno **e non può essere diffuso fuori dal gruppo di
  risposta prima della chiusura**») e viene recuperata: la copertura testuale del
  fatto obbligatorio passa da un terzo a intera.
- **Q6 non cambia.** L'informazione sui 240 MB, che prima mancava dalla memoria,
  ora c'è ma **non entra nel contesto proprio dove servirebbe**: sulla domanda
  che chiede quali evidenze hanno portato al cambio di classificazione è al rango
  18 con punteggio 0,054, molto oltre l'arresto per budget. Non è la soglia sul
  punteggio nullo: è il ranking, che mette davanti voci generiche su
  «classificazione» e «caso».
- **Q3 peggiora.** La stessa voce sui 240 MB entra invece dove non serve (rango
  6 sulla domanda sull'evidenza ritirata) e spinge fuori dal budget «il file non
  ha alcuna relazione con l'incidente», che era parte della risposta attesa.
- Nessuna perdita rispetto ai vecchi contesti è dovuta alla memoria: ogni testo
  che prima entrava e ora no è ancora nello stato, spostato solo dal ranking.

Un rischio nuovo, introdotto proprio dal recupero: il fatto «l'ipotesi del caso
non è stata cambiata per adesso», della prima sessione, ora esiste come voce
**attiva** con un `claim_key` diverso dalla catena delle ipotesi, quindi la
supersessione `ransomware → infostealer → confermata` non lo tocca. Entra in 5
contesti su 7, compreso quello sulla classificazione superata. Prima era assente
perché l'operazione era stata rifiutata: ora è presente e leggibile come
attuale, benché sia vero solo fino alla sessione 2. È di nuovo la questione
aperta «eventi o stati» (sezione 10), non un difetto della riparazione.

**Quarta conferma del falso positivo di provenienza:** su Q3, Q4 e Q6
`evidence_provenance_complete` vale `true` mentre la copertura testuale dei fatti
obbligatori sta fra 0% e 25%.

Budget rispettato in tutte e 7 le domande (170–200 token, nessun superamento
per primo elemento) e provenienza tracciata su ogni elemento selezionato.

#### Le 7 risposte U sulla memoria riparata

Generate dai prompt già pronti, stessi parametri della prima prova SC03
(`claude-sonnet-5`, effort `medium`), 7 chiamate, 0 errori. Artefatti in
`results/rq2/retrieval_repair_v3/generation_dev_sc03_u.jsonl`; le risposte
precedenti restano immutate. **Una sola esecuzione: le differenze sono
osservazioni, non prove che ogni cambiamento dipenda dalla modifica a U.**

Quattro domande invariate (Q1, Q2, Q4, Q7), Q6 invariata con astensione in
entrambe le prove, Q3 lievemente peggiorata, Q5 divisa in due:

- **il miglioramento** è su Q5: il vincolo sul rapporto ora è completo, dove
  prima la risposta si fermava a «deve restare interno». È l'effetto diretto
  della voce di memoria più completa prodotta dalla riparazione;
- **il peggioramento** è sulla stessa Q5: prima il modello si asteneva sui punti
  aperti, ora ne elenca quattro e nessuno lo è. Fra questi compare «l'ipotesi del
  caso non è stata cambiata per adesso», la voce recuperata dalla riparazione,
  vera solo fino alla sessione 2 e rimasta `attivo` fuori dalla catena di
  supersessione: **è informazione obsoleta finita in una risposta**, e nella prima
  prova non poteva accadere perché la voce non esisteva. La stessa risposta
  aggiunge «(in attesa di risultati)», che il contesto non dice;
- **Q3** perde metà del motivo: «non ha alcuna relazione con l'incidente» esce dal
  contesto, spinto fuori dai 240 MB che con quella domanda non c'entrano.

**Esito della verifica di U.** La modifica fa quello per cui è stata fatta —
nessuna operazione perde più contenuto — ma su queste 7 domande **non migliora
le risposte**. Il collo di bottiglia si è spostato dalla memoria al ranking, e la
questione «eventi o stati» è passata da difetto silenzioso a difetto visibile:
recuperare un enunciato legato al tempo, senza un modo per dichiararlo scaduto,
lo rende leggibile come attuale. Nessun problema tecnico bloccante.

### 9.6 SC04 ricostruito con le istruzioni aggiornate

U ricostruito sui fatti già estratti, G costruito **sullo stesso nuovo stato di
U**, retrieval e 14 risposte U/G. FULL_HISTORY non rigenerata: resta come
riferimento diagnostico. Artefatti in `results/rq2/sc04_repair_v3/`, con input,
versione delle istruzioni, impronta del codice e configurazione registrati nel
README. **21 chiamate**: 6 per U (4 sessioni + 2 riparazioni), 1 per G, 14 per le
risposte. Nessun errore, nessuna risposta vuota.

**Operazioni:** 41 proposte, 38 applicate, **3 rifiutate e tutte recuperate**
dalla riparazione; nessun rifiuto per `fact_id` usato come voce; nessun fatto
candidato resta senza operazione. In un caso il modello ha ridecidiso davvero,
non solo corretto il riferimento: un UPDATE invalido è tornato come NOOP.

**Il caso RULE-01 non cambia:** la rimozione resta un ADD separato accanto alla
creazione ancora attiva, senza collegamento. Le istruzioni nuove non toccano
questo comportamento — conferma che è la questione aperta «eventi o stati», non
un difetto delle istruzioni.

**Grafo:** 10 nodi e 16 archi; compare l'arco `RULE-01 configurata_su ACC-207`,
cioè la relazione `SC04-R08` che nel grafo precedente **mancava**. Restano 4
archi con provenienza non valida per oggetto letterale, **gli alias sono ancora
vuoti su tutti i nodi**, e l'ancoraggio peggiora: ora **nessuna** delle 7 domande
trova nodi dal proprio testo (prima una). Nuovo difetto: l'arco che registra la
rimozione di RULE-01 porta stato `superato`, che dice che è superato l'arco, non
che la regola è stata rimossa.

**Risposte** (una sola esecuzione: differenze osservate, non cause dimostrate):
Q2 in G migliora e stavolta **è sostenuta dal contesto** — l'arco «valutato
inizialmente come spam generico», stato `superato`, entra perché Q2 è storica;
Q3 in U perde il ponte inventato «da questa segnalazione risulta LOGIN-07»; Q5 in
U non afferma più che l'attività aperta sia il riepilogo. In cambio Q3 in G
smette di dichiarare la propria insufficienza pur restando incompleta. Q1, Q4,
Q6 e Q7 invariati. FULL_HISTORY resta molto sopra su Q3, Q4 e Q5.

**Riferimento di sviluppo.** Senza problemi bloccanti, questa è la versione di
riferimento da cui partire per una futura estensione gerarchica, con i limiti
dichiarati: ancoraggio ai nodi a zero, alias vuoti, archi con oggetti letterali,
«eventi o stati» aperta, ranking come collo di bottiglia principale. **Non è una
validazione del sistema e il protocollo resta non congelato.**

### 9.3 SC04 — U / G / FULL_HISTORY

Eseguita con `claude-sonnet-5`, effort `medium`, configurazione `rq2-dev-0.1`.
Comprende 4 chiamate di estrazione, 4 di aggiornamento, 1 per il grafo e 21
generazioni. Nessun errore di esecuzione, nessun errore di parsing.

Sono **risultati di sviluppo**: un solo scenario, 7 domande per modalità, una
sola esecuzione, nessuna replica, oracle non approvato, protocollo non
congelato. Non sono risultati dell'esperimento e non vanno riportati come tali.

**Valutazione assistita da rivedere:** `results/rq2/evaluation_dev_sc04.md`
(revisione 2, criteri consolidati). I giudizi lì dentro sono proposte; i campi
manuali di `results/rq2/annotation_template_sc04.jsonl` restano `null` e vanno
compilati a mano. Dove un giudizio dipende da una scelta metodologica ancora
aperta, la valutazione è data due volte: secondo l'oracle attualmente salvato e
secondo il criterio alternativo proposto.

### Che cosa è stato prodotto

| Fase | Esito |
|---|---|
| Estrazione | 38 fatti, tutti con provenienza valida, 4 sessioni tutte eseguite |
| Aggiornamenti | 38 operazioni, 38 applicate, **0 rifiutate**; stato finale 34 voci attive + 2 in archivio |
| Grafo | 14 nodi, 21 archi; **5 archi con `provenance_valid: false`** (oggetto non dichiarato come nodo) |
| Retrieval | 14 righe (7 domande × U e G), tutte entro il budget di 200 token |
| Generazione | 21 risposte (7 × U, G, FULL_HISTORY), nessun errore |

Isolamento verificato per ispezione: nei prompt di estrazione, aggiornamento e
grafo non compaiono domande, oracle o relazioni attese, e i messaggi
dell'assistente non entrano nell'estrazione. G parte davvero dagli stessi fatti
e dallo stesso stato di U (`facts_source` e `state_source` lo dichiarano).

### Esito delle risposte (valutazione assistita, non approvata)

| | completa | parziale | astensione corretta | uso di informazione obsoleta | affermazioni non supportate |
|---|:-:|:-:|:-:|:-:|:-:|
| U | 2 | 4 | 1 | 0 | 2 |
| G | 2 | 4 | 1 | 0 | 0 |
| FULL_HISTORY | 5 | 1 | 1 | 0 | 1 (lieve) |

**Nessuna delle 21 risposte ha usato informazione obsoleta.**

I conteggi sono quelli dell'**oracle attualmente salvato**. Con il criterio
alternativo proposto per SC04-Q2 (l'oracle si contraddice: `mandatory_facts`
pretende anche il motivo della classificazione, `accepted_equivalents` dichiara
sufficiente la risposta senza) cambia una sola cella: FULL_HISTORY passa a 6
complete. U e G restano invariate, quindi il confronto fra le architetture in
esame non dipende da questa scelta.

Il risultato più netto non è U contro G, che pareggiano nel conteggio: è che
**FULL_HISTORY sta molto sopra entrambe** a parità di modello e di istruzioni.
Con 529 token di cronologia integrale il modello risponde quasi sempre; con 200
token selezionati no. Su SC04 il collo di bottiglia non è la disponibilità
dell'informazione, è la selezione.

U e G pareggiano nel punteggio ma **falliscono in modo diverso**: U colma i vuoti
(due affermazioni non supportate, su Q3 e Q5), G li dichiara e non inventa mai.
Su 7 domande e una sola esecuzione è un'ipotesi, non un risultato.

### Guasti osservati, con la prima causa

- **Retrieval, causa dominante.** La soglia sul punteggio nullo ha escluso quattro
  voci decisive in tre domande: `SC04-M010` e `SC04-M018` (la valutazione «spam
  generico» e il suo superamento) su Q2, `SC04-M031` e `SC04-M032` (RULE-01
  rimossa, password reimpostata) su Q4. Le informazioni erano in memoria: non
  sono entrate nel contesto.
- **Provenienza completa su evidenza assente.** Su Q4 il retrieval dichiara
  `evidence_provenance_complete: true` perché due voci condividono il messaggio
  sorgente `SC04-S4-U1` con i fatti richiesti **senza esprimerli**. È la conferma
  su dati reali di quanto la sezione 7 già avvertiva: i campi `*_by_provenance`
  non misurano il contenuto.
- **Due falsi positivi di relazione.** Su Q2 le relazioni `SC04-R02` e `SC04-R03`
  risultano presenti grazie a `SC04-M017` («il caso è classificato come
  smishing»), che non le esprime. Su Q3 in G la relazione `SC04-R08` risulta
  presente grazie all'arco `SC04-E014` (`LOGIN-07 ha_originato RULE-01`), mentre
  il grafo **non contiene** alcun arco fra `ACC-207` e `RULE-01`.
- **Ancoraggio ai nodi di G guasto.** `graph_question_node_ids` è **vuoto in 6
  domande su 7**: le domande sono in lingua naturale e **tutti i nodi hanno
  `aliases: []`**. I nodi iniziali sono venuti solo dalle voci di U.
- **Percorso topologico ≠ catena esplicativa, osservato davvero.** Su SC04-Q3 il
  retriever dichiara `topological_paths_complete_in_context: true`, ma il percorso
  è `RIEPILOGO-01 →riguarda→ CASE-01 →riguarda→ UT-207 →usa_account→ ACC-207`:
  due archi su tre sono una relazione generica verso nodi contenitore che l'oracle
  non prevede. `SMS-01` e `URL-01`, i due nodi di cui la domanda parla, non sono
  mai stati nodi iniziali. Livelli 1 e 2 soddisfatti, livello 3 no.
- **Meccanismo del consumo di budget in G.** Gli archi di percorso ricevono un
  punteggio di priorità `1 + 1/posizione` (2.0, 1.5, 1.33…), sempre superiore a
  qualunque coseno TF-IDF. Entrano prima di ogni voce di contenuto. Misurato: U
  spende 75–90 token di sovraccarico e 84–111 di contenuto, G spende 98–127 di
  sovraccarico e **59–96 di contenuto**. A 200 token G riceve sistematicamente
  meno contenuto di U.
- **Eventi contro stati: un'ambiguità del modello di memoria, non un errore.**
  L'oracle prevede che «RULE-01 rimossa» superi «RULE-01 creata»; il modello ha
  usato un ADD con `claim_key` nuovo. Il riesame **non conferma** che sia un
  UPDATE mancato: `SC04-M028` («è stata creata») e `SC04-M031` («è stata
  rimossa») sono due enunciati al passato su eventi distinti, entrambi veri e
  compatibili, e `status: attivo` qualifica la **voce**, non il fatto del mondo.
  Le istruzioni del costruttore definiscono UPDATE come sostituzione «dello
  stesso oggetto e ambito» senza dire se un evento e la sua cessazione lo siano.
  Resta un difetto reale di **tracciabilità**: fra le due voci non c'è alcun
  collegamento, e ricostruire che la regola non è più in vigore richiede di
  recuperarle entrambe. Il rischio corrispondente — presentare la regola come in
  essere — **non si è realizzato in nessuna delle 21 risposte**.
- **L'archivio si popola solo sui ritiri espliciti.** 34 ADD, 2 UPDATE, 2 NOOP,
  0 DELETE; i due soli UPDATE cadono dove il messaggio dell'utente ritratta a
  parole («Correzione della valutazione iniziale…», «non è più valida»). Con
  `claim_key` per evento la politica corrente/storia non discrimina nulla, perché
  gli eventi restano tutti `attivo`: su tutto il resto U si comporta come F con
  etichette in più. È l'osservazione più rilevante sulla gestione, e riguarda U
  in generale, non SC04. **0 operazioni rifiutate su 38 non significa gestione
  corretta:** significa che il controllo di validità non aveva nulla da
  segnalare.

### 9.4 Osservazioni comuni ai tre scenari

**Il falso positivo di provenienza è sistematico.** Si ripresenta identico in
SC04-Q4 (U e G) e in SC03-Q6 (F e U): `evidence_provenance_complete` vale `true`
mentre nessuna delle evidenze richieste è nel contesto, perché una voce che
condivide il `message_id` sorgente «copre» fatti che non esprime. Su SC03-Q6
tutte e tre le evidenze del cambio di classificazione risultano coperte da
`SC03-F022`/`SC03-M022` («l'ipotesi è stata aggiornata da ransomware a
infostealer»), e sia F sia U si astengono. **L'indicatore automatico dichiara
completa un'evidenza assente, su scenari e modalità diversi.**

**La soglia sul punteggio nullo continua a escludere evidenze decisive.** Su
SC03-Q6 «famiglia Kelpie» (`SC03-F024`/`SC03-M024`) ha punteggio 0,0 perché la
domanda non contiene quel termine, come già `SC04-M031` e `SC04-M032` su SC04-Q4.

**Tre ambiguità delle istruzioni, ora documentate da uscite reali.** (i) Il
prompt di aggiornamento chiede in `target_entry_id` «il fatto in memoria», e la
parola «fatto» designa sia i candidati `F…` sia le voci `M…`: due rifiuti su tre
nascono da qui. (ii) Il prompt mostra lo stato **all'inizio** della sessione e
chiede in un colpo solo le operazioni di tutta la sessione, quindi una catena di
aggiornamenti interna alla sessione si rompe: è il caso di `SC03-OP026`.
(iii) Resta aperto il significato di `negated`, che in `SC03-F013` e `SC02-F021`
marca la presenza di una negazione nella frase, non il ritiro dell'affermazione.

### 9.5 Che cosa il confronto U/G sostiene e che cosa no

Il budget è **uguale** per U e per G. Che G spenda più token in identificatori,
stati e relazioni **è un costo dell'architettura**, non un confondente: è
esattamente ciò che un confronto a parità di budget deve far emergere, come già
diceva la sezione 3. Vanno però tenute distinte due affermazioni.

**Sostenuta dagli artefatti:** su SC04, con questo budget e questa
implementazione, G non ha fatto meglio di U e ha fallito in modo diverso. Stessi
fatti, stesso stato, stesso budget, stesso modello, stesse istruzioni,
isolamento verificato.

**Non sostenuta:** che la rappresentazione a grafo *in quanto tale* renda meno
della memoria a fatti aggiornati. «G come implementato» comprende tre contributi
non separati: l'unità di rappresentazione, la qualità del grafo costruito (alias
vuoti, nodi hub, archi mancanti) e la politica di recupero relazionale (priorità
`1 + 1/posizione`, semi dalle prime 3 voci, `max_hops` 3). Alias vuoti e
ancoraggio debole sono **risultati di G**, non scuse — il costruttore fa parte
dell'architettura in esame — ma attribuire l'esito alla sola rappresentazione
richiederebbe un'ablazione che non è stata eseguita.

Il limite vero resta la potenza: 7 domande, uno scenario, una esecuzione,
nessuna replica. Il confronto sostiene diagnosi, non conclusioni.

## 10. Cosa manca prima di congelare il protocollo

- **Prove reali:** manca **SC01** (T e FULL_HISTORY, 14 generazioni). SC02, SC03
  e SC04 sono stati eseguiti (sezione 9) e hanno mostrato che le uscite vere sono
  peggiori delle fixture: archi con oggetti non dichiarati come nodi, alias
  vuoti, tre operazioni rifiutate con una perdita di contenuto, `DELETE` mai
  usato, nodi contenitore non previsti dall'oracle.
- **Indicatore di evidenza da correggere prima di annotare:** in SC02, SC03 e
  SC04 `evidence_provenance_complete` e i campi `*_by_provenance` hanno
  dichiarato presente un'evidenza assente dal contesto. Riguardano il **metro**,
  non il sistema in esame, e finché restano così ogni diagnosi delle 63 risposte
  è inaffidabile.
- ~~**Istruzioni di U da disambiguare**~~: fatto. Istruzioni `u-instructions-0.3`
  e passata di riparazione (sezione 5). **SC03 andrà rieseguito per intero** con
  le nuove istruzioni prima di qualunque conteggio, e va deciso se rieseguire
  anche SC04: la prova attuale di SC04 usa le istruzioni vecchie, quindi oggi U
  non è costruito allo stesso modo nei due scenari.
- **`DELETE` senza copertura:** l'unico ritiro senza sostituzione del dataset è
  stato trattato come UPDATE. Va deciso se il fenomeno va riformulato nello
  scenario, nelle istruzioni, o accettato come esito.
- **Controllo umano delle annotazioni:** oracle, operazioni attese, stato atteso,
  entità e relazioni di SC03 e SC04 sono ancora bozze non approvate.
- **Taratura del budget:** 200 token era stato scelto prima di contare
  l'overhead strutturale. Con l'overhead, F, U e G entrano con 6 elementi circa:
  va deciso se il valore resta adeguato. La prova reale su SC04 dà la misura: G
  scende a 59–96 token di contenuto contro gli 84–111 di U.
- **Soglia sul punteggio nullo:** su SC04 ha escluso quattro voci decisive in tre
  domande diverse (sezione 9). È la singola regola che ha prodotto più
  fallimenti: va riesaminata.
- **Politica di lettura:** l'elenco dei marcatori di `question_scope()` è una
  prima proposta e va rivisto sulle 28 domande definitive.
- **Parametri di G:** `max_hops` (3), `max_seed_items` e `max_seed_nodes` (3) sono
  valori di sviluppo, tarati su grafi di una decina di archi.
- **Copertura relazionale:** i percorsi collegano fra loro i nodi iniziali. Un
  arco che la domanda richiede ma che sta fuori da ogni percorso minimo entra
  solo se avanza budget. Sulla **prova reale** di SC04-Q3 restano fuori
  `SMS-01 contiene URL-01` e `UT-207 ha aperto URL-01`: G copre 5 relazioni su 7
  per provenienza — in realtà 4, perché `SC04-R08` è un falso positivo — U ne
  copre 5, e `evidence_complete` è `false` per entrambe. È un **risultato
  diagnostico**, non un guasto: va deciso se serve una nozione di pertinenza più
  larga, ma la decisione non deve essere presa guardando questo caso per farlo
  passare.
- **Ancoraggio ai nodi:** dipende da identificatori, alias ed etichette prodotti
  dal costruttore del grafo. Con alias poveri, G trova meno nodi iniziali. Sulla
  prova reale di SC04 il costruttore ha prodotto **alias vuoti su tutti e 14 i
  nodi** e l'ancoraggio alla domanda ha fallito in 6 casi su 7: va affrontato
  prima di qualunque misura su G.
- **Controllo dell'oracle di SC04:** su **Q2** l'incoerenza è interna
  all'annotazione, non solo fra domanda e oracle: `mandatory_facts` chiede quattro
  elementi compreso il motivo della classificazione, mentre
  `accepted_equivalents` ne dichiara sufficienti tre senza il motivo. Vanno
  allineati, e la scelta va messa a verbale prima di annotare. Su **Q3** restano
  `R05` fra i fatti obbligatori ma non fra le relazioni richieste, e `R03` nella
  risposta attesa ma in nessuno dei due elenchi; l'ordine `R09`/`R08` nella
  catena è invece **ammissibile** per la definizione dichiarata. Su **Q4** la
  relazione `R08` è difendibile — la risposta attesa nomina RULE-01 come regola
  sull'account — ma resta che `evidence_complete` è `false` per la sua assenza,
  mentre la lacuna reale, il contenuto di `SC04-M031` e `SC04-M032`, è invisibile
  all'indicatore: esito giusto per la ragione sbagliata. Vedi
  `results/rq2/evaluation_dev_sc04.md`.
- **Operazioni attese di SC04:** `expected_operations` è annotato su `claim_key`
  che il modello non ha usato, e l'annotazione dichiara già di essere parziale.
  **Non va adattato alle chiavi generate dal modello:** sarebbe adattare il metro
  al risultato. Va invece espresso come **requisiti di significato** —
  conservazione degli eventi, correttezza dello stato corrente, ritiro delle
  affermazioni non più valide, tracciabilità della sostituzione — verificabili
  sulla lettura che lo stato consente, quali che siano `claim_key` ed
  `entry_id`. Equivalenza semantica e coincidenza di identificatori sono cose
  diverse. Con questi criteri, sulle 7 operazioni attese di SC04 cinque
  risultano soddisfatte, una parziale (la catena di supersessione della
  classificazione porta al ritiro dell'ipotesi iniziale, non alla nuova
  classificazione) e una divergente ma non erronea (RULE-01). Il campo
  `required_state_keys` del modello di annotazione esiste già ed è vuoto in tutte
  e 21 le righe: è il posto naturale per questi requisiti, se lo si decide.
- **Voci di U: eventi o stati?** È la decisione a monte di tutte le altre su U.
  Da come si definisce `claim_key`, da che cosa significa `status` e dal fatto
  che il modello dati non preveda collegamenti fra eventi correlati dipendono il
  popolamento dell'archivio, l'utilità della politica corrente/storia e il senso
  stesso del confronto F/U.
- **Metriche aggregate e analisi degli errori di RQ2**, cioè l'equivalente di
  `summarize_evaluation.py` e `build_error_analysis.py` per le nuove modalità,
  compresi i livelli scrittura, aggiornamento, grafo e retrieval.
- **Piano delle repliche**, se previste, da fissare prima delle esecuzioni finali.

Solo dopo questi passaggi ha senso congelare dataset, oracle, matrice, prompt,
parametri e codice ed eseguire le 77 generazioni.
