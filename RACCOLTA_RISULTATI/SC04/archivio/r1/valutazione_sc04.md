# SC04 — Corvara Servizi / smishing: valutazione delle 28 risposte RQ2

**Revisione r1 — 18 settembre 2026.** Prima scheda quantitativa di SC04.
Struttura ripresa dalla scheda SC03 r2; **i giudizi sono ricavati dalle evidenze
di SC04**, non trasferiti da altri scenari.

**Stato dei giudizi:** **valutazioni assistite proposte dall'assistente, non
approvate.** Nessuna approvazione dello studente, nessuna approvazione del
relatore, protocollo non congelato.

**Natura dei risultati:** **risultati di sviluppo.** Una sola esecuzione per
cella, sette domande per modalità, nessuna replica, oracle e annotazioni ancora
in bozza (`status: BOZZA DA CONTROLLARE`). Non sono risultati dell'esperimento.

**Stato del riepilogo numerico:** **provvisorio**, in attesa della revisione dei
giudizi. Nessun giudizio è lasciato sospeso; la sola lettura discrezionale è
dichiarata in §8.3 con l'effetto quantificato.

Nessuna chiamata al modello, nessuna nuova generazione, nessuna riesecuzione del
retrieval o della costruzione della memoria o del grafo. Scenari, oracle,
criteri comuni, configurazioni, codice, risposte e valutazioni precedenti non
sono stati modificati: gli unici file scritti sono i cinque di questa cartella.

---

## 1. Esecuzioni di riferimento e verifica delle configurazioni

Il confronto è formato da **28 risposte** che vengono da **tre esecuzioni
distinte**. È una vista composita, e va dichiarata come tale ogni volta che i
numeri vengono riportati.

| Modalità | Righe | File delle risposte | Esecuzione | Ruolo |
|---|---:|---|---|---|
| **T** | 7 | `results/rq2/t_ext_v1/generation_dev_t_sc04.jsonl` | estensione della matrice, **8 settembre 2026** | confronto aggiuntivo disponibile |
| **U** | 7 | `results/rq2/sc04_repair_v3/generation_dev_sc04_ug.jsonl` | correzione `u-instructions-0.3`, **5 settembre 2026** | versione corretta, di riferimento |
| **G** | 7 | `results/rq2/sc04_repair_v3/generation_dev_sc04_ug.jsonl` | stessa esecuzione di U | versione corretta, di riferimento |
| **FULL_HISTORY** | 7 | `results/rq2/generation_dev_sc04.jsonl` | esecuzione iniziale, **4 settembre 2026** | controllo diagnostico fuori budget |

**FULL_HISTORY non è stata rigenerata nella correzione.** Il README di
`sc04_repair_v3/` lo dichiara esplicitamente, e l'inventario lo segnala fra le
cose da indicare in tabella. Non è un problema in sé — FULL_HISTORY non usa né
la memoria né il grafo, quindi la correzione non la riguarda — ma resta una
riga proveniente da un'altra esecuzione.

### File che alimentano ciascuna modalità

| Modalità | Prompt e contesto | Retrieval | Memoria / grafo |
|---|---|---|---|
| T | `t_ext_v1/generation_inputs_t_sc04.jsonl` | `t_ext_v1/retrieval_t_sc04.jsonl` | nessuna: unità = messaggio |
| U | `sc04_repair_v3/generation_inputs_sc04_ug.jsonl` | `sc04_repair_v3/retrieval_sc04_ug.jsonl` | `sc04_repair_v3/scenario_04_state.json`, `…_operations.jsonl` |
| G | `sc04_repair_v3/generation_inputs_sc04_ug.jsonl` | `sc04_repair_v3/retrieval_sc04_ug.jsonl` | `sc04_repair_v3/scenario_04_graph.json` (+ lo **stesso** stato di U) |
| FULL_HISTORY | `results/rq2/generation_inputs_sc04.jsonl` | **nessuno** | nessuna: 7 messaggi utente per costruzione |

### Compatibilità delle configurazioni — verificata

| Controllo | Esito |
|---|---|
| Budget | **200 token** in tutte e tre le esecuzioni, letto dalle righe di retrieval |
| `config_id` | `rq2-dev-0.1` nelle tre; `run_t_ext_sc04_sc05.json` dichiara di ereditare da quella base budget, conteggio dei token, regola di selezione e ranking |
| Istruzioni del prompt | **identiche** in tutte e 28 le righe, verificate per confronto di stringa |
| Modello ed effort | `claude-sonnet-5`, effort `medium`, in tutte e 28 |
| Errori | `error: null` su tutte e 28 |
| Fatti candidati | `results/rq2/facts/scenario_04_facts.jsonl`, **non riestratti** fra le esecuzioni. T non li usa: lavora sui messaggi |
| Base di G | dichiarata in `state_source`: **lo stesso stato di U** prodotto nella correzione |
| Identificativi | 28 coppie `(question_id, mode)` distinte, SC04-Q1…SC04-Q7 × {T, U, G, FULL_HISTORY} |

**Che cosa questo rende confrontabile e che cosa no.** Budget, ranking, prompt,
modello e fatti candidati sono gli stessi: le quattro modalità sono confrontabili
sul piano delle condizioni dichiarate. Non sono però **repliche**: ogni cella ha
una sola esecuzione, e T, U/G e FULL_HISTORY vengono da tre giorni diversi.

### Le prime U e G restano fuori

Le 7 risposte U e le 7 G presenti in `results/rq2/generation_dev_sc04.jsonl`
**non entrano in nessuna aggregazione**. Sono consultate solo in §10, per la
storia dello sviluppo, e sempre identificate come «prima versione». Non sono
repliche delle versioni corrette: cambiano istruzioni (`u-instructions-0.2` →
`0.3`), stato della memoria, grafo e quindi contesto ricevuto.

---

## 2. Fonti

Tutte lette in sola lettura. I ventisei percorsi con le impronte SHA-256 sono in
[`fonti_sc04.json`](fonti_sc04.json). Oltre ai file già elencati in §1:

| Ruolo | File |
|---|---|
| I 41 fatti estratti (comuni a U e G) | `results/rq2/facts/scenario_04_facts.jsonl` |
| Operazioni e registro del grafo | `sc04_repair_v3/scenario_04_operations.jsonl`, `…_graph_log.json` |
| Note delle esecuzioni | `sc04_repair_v3/README.md`, `t_ext_v1/README.md` |
| Valutazione precedente di T | `t_ext_v1/valutazione_assistita_t.md`, `…/annotation_compilata_t_sc04.jsonl` |
| Valutazione precedente di U/G | `results/rq2/evaluation_dev_sc04.md` |
| Scenario, oracle, relazioni attese | `data/rq2/scenarios/scenario_04.json`, `data/rq2/annotations/scenario_04_rq2.json` |
| Configurazioni | `data/rq2/config/experiment_rq2.json`, `…/run_t_ext_sc04_sc05.json` |
| Regola di classificazione | `RACCOLTA_RISULTATI/CRITERI_VALUTAZIONE.md` |
| Criteri e metriche | `EXPERIMENT.md` §9–§11; `RQ2.md` §3–§7, §9.3, §12 |
| Quadro della raccolta | `RACCOLTA_RISULTATI/INVENTARIO.md` |

`results/rq2/annotation_template_sc04.jsonl` è stato letto e lasciato
**intatto**. Le valutazioni precedenti (`valutazione_assistita_t.md`,
`evaluation_dev_sc04.md`) sono state lette come contesto e **non riusate come
giudizi**: le 28 righe di questa scheda sono valutate sulle evidenze.

---

## 3. Quale oracle è usato per quale misura

Come in SC03, oracle della risposta e scomposizione RQ2 stanno nello stesso file.
I conteggi non coincidono, e SC04 aggiunge un terzo oggetto: le **relazioni**.

| Domanda | `mandatory_facts` (oracle della risposta) | `required_facts` (RQ2) | `required_relations` |
|---|---:|---:|---:|
| Q1 | 2 | 2 | 0 |
| Q2 | 4 | 4 | **3** |
| Q3 | 6 | 6 | **7** |
| Q4 | 3 | 3 | **1** |
| Q5 | 2 | 2 | 0 |
| **Q6** | 2 | **1** | 0 |
| **Q7** | 1 | **0** | 0 |

**Regola adottata.**

- **Copertura dei fatti** — sui `required_facts`, per singolo `fact_key`, con due
  verifiche separate: presenza nel **contenuto del contesto ricevuto** e presenza
  **nella risposta**. Alimenta l'indicatore di recupero (§9.2 di
  `EXPERIMENT.md`) e quindi Retrieval Success e Answer Success. Dettaglio in
  `rq2_fact_detail`.
- **Copertura delle relazioni** — sui `required_relations`, **tenuta distinta**
  dalla copertura dei fatti e **mai sommata** ad essa. La presenza nel contesto è
  misurata **solo per G**, l'unica modalità con una rappresentazione relazionale
  esplicita; la presenza nella risposta è misurata per tutte e quattro, perché
  riguarda la risposta e non la rappresentazione. Dettaglio in `relation_detail`.
  Le relazioni **non entrano** in Retrieval Success né in Answer Success: sono
  riportate a parte in §8.2.
- **Classe della risposta** — sull'**intera risposta** contro `expected_answer`,
  `mandatory_facts`, `obsolete_information` e `accepted_equivalents`, secondo la
  regola `completezza-supporto-1`.
- **Q7** — nessun `required_fact`: la copertura RQ2 è **non definita**
  (denominatore 0 → `null`). L'astensione è valutata sull'oracle della risposta e
  sulla verifica diretta del corpus (§7).

**Raggiungibilità.** Il perimetro è l'intero scenario in tutte e quattro le
modalità: 7 messaggi utente per T e FULL_HISTORY, 41 fatti e 41 voci di memoria
per U, 10 nodi e 16 archi per G. Coincide quindi con `fact_present_in_corpus`:
vera per Q1–Q6, **falsa per Q7**.

---

## 4. Criteri applicati

**Regola di classificazione:** `completezza-supporto-1`
(`RACCOLTA_RISULTATI/CRITERI_VALUTAZIONE.md`), la stessa di SC02 r3 e SC03 r2.
Contraddizione o uso di informazione superata → `errata`; tutti i fatti e nessuna
contraddizione → `completa`, con `unsupported_claim` registrato a parte; parte
dei fatti senza quegli errori → `parziale`; astensione corretta secondo il
protocollo.

**Nessuna interpretazione permissiva è stata introdotta per adattare i criteri
ai risultati.** Dove l'oracle elenca un fatto obbligatorio, è stato richiesto; le
clausole `accepted_equivalents` sono state applicate alla lettera. Due
conseguenze concrete e scomode: su **Q2** nessuna delle quattro modalità è
completa, perché l'oracle chiede quattro cose e nemmeno FULL_HISTORY le dà tutte;
su **Q3** anche FULL_HISTORY è parziale, perché la catena richiesta è di sei
passaggi e la risposta ne salta uno.

**Quattro proprietà tenute distinte** in ogni riga:

| Campo | Domanda a cui risponde |
|---|---|
| `rq2_fact_coverage_in_answer` | la risposta contiene i fatti richiesti? |
| `supported_by_original_conversation` | tutto ciò che afferma è sostenuto dalle conversazioni originali? |
| `faithful_to_received_context` | è fedele al contesto che ha ricevuto? |
| `counts_as_complete_and_supported` | entra nel numeratore del Complete Answer Rate? |

**Ordine diagnostico della prima causa osservabile** (`EXPERIMENT.md` §11,
esteso da `RQ2.md` §7): conversazione → estrazione → **gestione** → **grafo** →
recupero → contesto → risposta. SC04 è il primo scenario di questa raccolta in
cui l'origine **`grafo`** risulta usata, perché è l'unico con una modalità G.

**Una causa è attribuita solo quando è documentata negli artefatti.** Le
spiegazioni non verificabili sono tenute separate e dichiarate tali (§9.3).

---

## 5. Come è stata verificata la presenza delle evidenze

Ogni risposta è stata letta insieme al **blocco di contesto che ha davvero
ricevuto**, riga per riga, e la presenza di un'evidenza è stata giudicata sul
**contenuto**, non sugli identificatori di provenienza né sulla sola presenza di
un identificatore di entità. Quattro reperti.

**Un arco che dice la cosa giusta con lo stato sbagliato — G, Q4.** L'arco
`SC04-E014 RULE-01 -rimossa-> ACC-207` esiste nel grafo e ha provenienza valida,
ma il suo **stato è `superato`**. La politica di lettura ammette in una domanda
a portata `current` soltanto gli elementi attivi: su Q4, che chiede quali azioni
risultano completate, i candidati per G sono **14**, contro i 32 di U, e
`SC04-E014` **non è fra loro**. Non è stato scartato dal ranking: non è mai
entrato nella selezione. Lo stato dichiara che *l'arco* è superato, non che la
regola è stata rimossa — il difetto era già annotato nel README della correzione
come «difetto nuovo da registrare», e qui se ne vede l'effetto su una risposta.

**Due voci attive con punteggio nullo — U, Q4.** `SC04-M033` («RULE-01 è stata
rimossa») e `SC04-M034` («la password di ACC-207 è stata reimpostata alle
08:05») sono **attive in memoria** e hanno punteggio **0,0000**, ranghi 31 e 32.
Stessa domanda, stessa risposta incompleta di G, **causa diversa**: in U le
informazioni sono candidate e perdono nel ranking, in G l'arco non è nemmeno
candidato.

**Nodi senza alias e nessun ancoraggio dal testo — G.** Tutti e 10 i nodi del
grafo hanno `aliases: []`, e nessuna delle 7 domande trova nodi dal proprio
testo. I semi vengono quindi solo dalle voci di U: su Q3 sono `ACC-207`,
`RULE-01`, `UT-207`, e il percorso trovato ha due archi. Le relazioni
`SC04-E003`, `SC04-E007`, `SC04-E009` e `SC04-E011` **esistono nel grafo** e
restano fuori dal contesto.

**Identificatore presente, fatto assente.** Su Q3 il contesto di U contiene
`SC04-M032`, che nomina `LOGIN-07`; questo **non** soddisfa il fatto obbligatorio
«su ACC-207 risulta l'accesso anomalo LOGIN-07», che richiede l'accesso anomalo e
non il riferimento alla sessione. Allo stesso modo `SC04-M002` dice «l'operatore
UT-207 ha segnalato un SMS» senza l'identificatore `SMS-01`: il fatto è contato
come presente, con nota, perché soggetto e atto ci sono, ma la nota resta nel
JSONL.

---

## 6. Tabella dei giudizi proposti

Tabella completa: [`valutazioni_sc04.jsonl`](valutazioni_sc04.jsonl) (28 righe,
con `rq2_fact_detail` e `relation_detail`) e
[`valutazioni_sc04.csv`](valutazioni_sc04.csv) per la lettura rapida.

Legenda: **F ctx / F risp** = `fact_key` RQ2 nel contenuto del contesto / nella
risposta; **R ctx / R risp** = relazioni richieste nel contesto (solo G) / nella
risposta; **Oracle** = `mandatory_facts` coperti; **Sup.** = supportata dalle
conversazioni originali; **C&S** = conta come completa e supportata.

### T — Turn-level RAG (confronto aggiuntivo)

| Dom. | F ctx | F risp | R risp | Oracle | Classe | Sup. | C&S | Obs. | Non sup. | Prima causa |
|---|:-:|:-:|:-:|:-:|---|:-:|:-:|:-:|:-:|---|
| Q1 obiettivo | 2/2 | 2/2 | – | 2/2 | **completa** | sì | sì | no | no | – |
| Q2 classificazione | **1/4** | 1/4 | **2/3** | **2/4** | **parziale** | sì | no | no | no | retrieval |
| Q3 catena | **1/6** | 1/6 | **1/7** | **1/6** | **parziale** | sì | no | no | no | retrieval |
| Q4 azioni completate | 3/3 | 3/3 | 0/1 | 3/3 | **completa** | sì | sì | no | no | – |
| Q5 aperto + riepilogo | 2/2 | 2/2 | – | 2/2 | **completa** | sì | sì | no | no | – |
| Q6 punto non determinato | 1/1 | 1/1 | – | 2/2 | **completa** | sì | sì | no | no | – |
| Q7 informazione assente | n.d. | n.d. | – | 1/1 | **astensione corretta** | sì | n.a. | no | no | – |

### U — Fact-based con aggiornamenti, versione corretta

| Dom. | F ctx | F risp | R risp | Oracle | Classe | Sup. | C&S | Obs. | Non sup. | Prima causa |
|---|:-:|:-:|:-:|:-:|---|:-:|:-:|:-:|:-:|---|
| Q1 | 2/2 | 2/2 | – | 2/2 | **completa** | sì | sì | no | no | – |
| Q2 | **2/4** | 2/4 | **1/3** | **2/4** | **parziale** | sì | no | no | no | retrieval |
| Q3 | **3/6** | 3/6 | **4/7** | **3/6** | **parziale** | sì | no | no | no | retrieval |
| Q4 | **1/3** | 1/3 | 0/1 | **1/3** | **parziale** | sì | no | no | no | retrieval |
| Q5 | **1/2** | 1/2 | – | **1/2** | **parziale** | sì | no | no | no | retrieval |
| Q6 | 1/1 | 1/1 | – | 2/2 | **completa** | sì | sì | no | no | – |
| Q7 | n.d. | n.d. | – | 1/1 | **astensione corretta** | sì | n.a. | no | no | – |

### G — Grafo, versione corretta

| Dom. | F ctx | F risp | R ctx | R risp | Oracle | Classe | Sup. | C&S | Obs. | Non sup. | Prima causa |
|---|:-:|:-:|:-:|:-:|:-:|---|:-:|:-:|:-:|:-:|---|
| Q1 | 2/2 | 2/2 | – | – | 2/2 | **completa** | sì | sì | no | no | – |
| Q2 | **2/4** | 2/4 | **0/3** | 0/3 | **2/4** | **parziale** | sì | no | no | no | retrieval |
| Q3 | **2/6** | 2/6 | **2/7** | 3/7 | **2/6** | **parziale** | sì | no | no | no | **grafo** |
| Q4 | **1/3** | 1/3 | **1/1** | 0/1 | **1/3** | **parziale** | sì | no | no | no | **grafo** |
| Q5 | **1/2** | 1/2 | – | – | **1/2** | **parziale** | sì | no | no | no | retrieval |
| Q6 | 1/1 | 1/1 | – | – | 2/2 | **completa** | sì | sì | no | no | – |
| Q7 | n.d. | n.d. | – | – | 1/1 | **astensione corretta** | sì | n.a. | no | no | – |

### FULL_HISTORY — controllo diagnostico, fuori confronto (§12)

| Dom. | F ctx | F risp | R risp | Oracle | Classe | Sup. | C&S | Obs. | Non sup. | Prima causa |
|---|:-:|:-:|:-:|:-:|---|:-:|:-:|:-:|:-:|---|
| Q1 | 2/2 | 2/2 | – | 2/2 | **completa** | sì | sì | no | no | – |
| Q2 | 4/4 | **3/4** | **1/3** | **3/4** | **parziale** | sì | no | no | no | risposta |
| Q3 | 6/6 | **5/6** | **5/7** | **5/6** | **parziale** | sì | no | no | no | risposta |
| Q4 | 3/3 | 3/3 | 1/1 | 3/3 | **completa** | sì | sì | no | no | – |
| Q5 | 2/2 | 2/2 | – | 2/2 | **completa** | sì | sì | no | no | – |
| Q6 | 1/1 | 1/1 | – | 2/2 | **completa** | sì | sì | no | no | – |
| Q7 | n.d. | n.d. | – | 1/1 | **astensione corretta** | sì | n.a. | no | no | – |

**Nessuna delle 28 risposte è `errata`.** Nessuna usa informazione obsoleta,
nessuna introduce affermazioni non supportate, nessuna astensione è impropria.
Su SC04 il problema non è che il sistema dica cose false: è che ne dice poche.

---

## 7. Motivazioni per domanda

Versione integrale nel campo `rationale` di ogni riga. Qui i casi che portano
informazione.

### Q1 e Q6 — nessuna differenza fra le modalità

Su **Q1** tutte e quattro riportano entrambi gli obiettivi: i due `fact_key`
sono nel contesto ovunque. Su **Q6** tutte e quattro dichiarano la chiusura
senza esito e il punto non determinato, e nessuna attribuisce l'origine del
numero a una fonte non menzionata, che è l'errore vietato dall'oracle. **Su
queste due domande la rappresentazione non produce differenze osservabili.**

### Q7 — come è stata verificata l'assenza

L'oracle dichiara `fact_present_in_corpus: false` e l'annotazione RQ2 non elenca
fatti obbligatori. **L'assenza è stata verificata leggendo il corpus**, non
dedotta dall'astensione: nelle quattro sessioni non compaiono le radici
«fornitor», «gestore», «provider». Il gateway aziendale è citato **una volta
sola**, in `SC04-S4-U1`, come luogo in cui è stato bloccato il numero mittente.

Tutte e quattro si astengono. Il caso è più informativo del solito perché il
gateway **è nel contesto** di tutte e quattro — in G anche come arco esplicito
`SC04-E016 NUMERO-MITTENTE -bloccato_su-> gateway aziendale` — e nessuna ne
deduce un gestore. È il tipo di invenzione che l'oracle vieta, ed è evitata.

### Q2 — nessuna modalità completa, e due coperture complementari

L'oracle chiede quattro cose: la classificazione smishing, **il motivo** (la
pagina raggiunta è una pagina falsa che riproduce il modulo di accesso
aziendale), e le **due** valutazioni superate.

| | smishing | motivo | spam superato | contatto superato | oracle |
|---|:-:|:-:|:-:|:-:|:-:|
| T | sì | **sì** | no | no | 2/4 |
| U | sì | no | no | **sì** | 2/4 |
| G | sì | no | **sì** | no | 2/4 |
| FULL_HISTORY | sì | **no** | sì | sì | 3/4 |

- **T — parziale, origine `retrieval`.** È **l'unica a consegnare il motivo**,
  perché `SC04-S2-U1` lo contiene per esteso e T riceve il messaggio intero.
  `SC04-S1-U1` è rango 3 ma i suoi 124 token non entrano nel budget residuo.
  La risposta dichiara di non conoscere le valutazioni superate invece di
  inventarle.
- **U — parziale, origine `retrieval`.** Copre la valutazione superata sul
  contatto (`SC04-M021`, che enuncia l'ipotesi iniziale **e** il suo
  superamento). Il motivo è in `SC04-M015`, rango 21 con 0,0281; la voce sullo
  spam superato, `SC04-M018`, ha punteggio **0,0000**.
- **G — parziale, origine `retrieval`.** Copre l'altra metà: `SC04-E005`
  «CASO-SC04 -valutato_inizialmente_come-> spam generico», arco con stato
  `superato`, leggibile perché Q2 è l'unica domanda a portata `history`.
  `SC04-M021` è rango 7 con 0,1233 ed è l'elemento su cui la selezione si
  arresta per budget: 48 token non entrano. **G ha mancato la seconda metà per
  un elemento.**
- **FULL_HISTORY — parziale (3/4), origine `risposta`.** Con **tutte** le
  evidenze nel contesto, dichiara lo smishing ed entrambe le valutazioni
  superate, ma **non riporta il motivo**. `SC04-S2-U1` lo dice per esteso.
  L'omissione non è attribuibile al contesto.

**U e G coprono metà complementari della stessa domanda**, e nessuna delle due è
completa. È un'osservazione su una domanda, non una proprietà.

Relazioni richieste su Q2: `R02` (SMS-01 contiene URL-01), `R03` (URL-01 imita
la pagina di accesso), `R05` (invio del modulo). Nel contesto di G: **0/3**.
`SC04-R03` **non esiste nel grafo**: non c'è un nodo per la pagina di accesso, e
l'arco `SC04-E004` ha come oggetto il valore letterale «smishing». Nelle
risposte: T 2/3, FULL_HISTORY 1/3, U 1/3, G 0/3. **La modalità costruita per
rappresentare relazioni ne esprime meno delle altre su questa domanda.**

### Q3 — la catena: sei passaggi, nessuno li consegna tutti

L'oracle chiede sei passaggi e sette relazioni, distribuiti su tre sessioni.

- **T — parziale (1/6), origine `retrieval`.** Il contesto è il **solo**
  `SC04-S1-U1`, 124 token: la selezione si arresta su `SC04-S4-U1` (rango 2, 88
  token) che non entra nei 76 rimasti, e con esso restano fuori tutti i messaggi
  delle sessioni 2 e 3, dove sta la catena. La risposta dichiara l'insufficienza.
  Ripete che «la valutazione iniziale è di spam generico senza alcun contatto con
  il link», ma la qualifica come **iniziale**, come fa il messaggio sorgente:
  non è conteggiata come informazione obsoleta. **È una protezione che viene
  dalla formulazione del messaggio, non dall'architettura.**
- **U — parziale (3/6), origine `retrieval`. È la copertura più alta fra T, U e
  G.** Consegna la segnalazione, l'uso dell'account e la creazione di `RULE-01`
  dalla sessione di `LOGIN-07` — `SC04-M032` è la voce più ricca del confronto,
  con sessione, orario, account e destinazione. Mancano il contenuto dell'SMS,
  l'apertura del collegamento e l'accesso anomalo. La risposta chiude dichiarando
  che il nesso fra SMS e sessione non è confermabile: prudente e sostenuta.
- **G — parziale (2/6), origine `grafo`.** Relazioni nel contesto **2/7**:
  `SC04-R06` da `SC04-E008` e `SC04-R08` da `SC04-E012`, i due archi del
  percorso. Le altre cinque **esistono nel grafo** — `SC04-E003` (contiene),
  `SC04-E007` (ha aperto), `SC04-E009` (riguarda account), `SC04-E011` (creata
  dalla sessione) — e non entrano: i semi sono `ACC-207`, `RULE-01`, `UT-207`, il
  percorso trovato ha due archi, e gli archi pertinenti fuori percorso entrano
  solo se avanza budget. `SC04-E011`, che è la relazione `SC04-R09`, è rango 10.
  La risposta produce una catena con le entità giuste **senza dichiarare che è
  incompleta**: più pertinente della versione precedente, meno prudente di U.
- **FULL_HISTORY — parziale (5/6), origine `risposta`.** Con tutte e sei le
  evidenze nel contesto, ricostruisce la catena in quattro passaggi ordinati e
  corretti, ma **non dichiara mai che ACC-207 è l'account di UT-207**. L'oracle
  elenca quel passaggio fra i fatti obbligatori e la clausola degli equivalenti
  chiede che la catena conservi **tutti** i passaggi. Giudizio severo ma coerente
  con il testo dell'oracle; l'alternativa è quantificata in §8.3.

### Q4 — azioni completate: stessa incompletezza, due cause diverse

L'oracle chiede tre azioni, tutte in `SC04-S4-U1`.

- **T — completa (3/3).** Il messaggio le contiene tutte e tre, e T lo riceve
  intero.
- **FULL_HISTORY — completa (3/3).**
- **U — parziale (1/3), origine `retrieval`.** Solo il blocco del numero
  (`SC04-M035`). `SC04-M033` e `SC04-M034` sono **attive in memoria** e hanno
  punteggio **0,0000**, ranghi 31 e 32: escluse dalla regola sul punteggio nullo.
- **G — parziale (1/3), origine `grafo`.** L'arco `SC04-E014 RULE-01 -rimossa->
  ACC-207` ha stato **`superato`** e viene **escluso dai candidati** su una
  domanda a portata `current`: i candidati di G su Q4 sono 14, quelli di U 32.
  `SC04-E015` («password_reimpostata 08:05») è rango 7 ed è l'elemento su cui la
  selezione si arresta per budget.

**Questa è la differenza più netta fra U e G su SC04:** stessa classe, stessa
copertura, ma in U l'informazione è candidata e perde nel ranking, in G non è
mai candidata. La relazione `SC04-R08` è invece **nel contesto di G** (1/1) e la
risposta non la usa, perché dichiara l'insufficienza.

### Q5 — la stessa voce fuori budget in U e in G

L'oracle chiede l'attività aperta e il contenuto del riepilogo.

- **T e FULL_HISTORY — complete (2/2).** Entrambe le cose sono in
  `SC04-S4-U1`.
- **U e G — parziali (1/2), origine `retrieval`.** Entrambe hanno `SC04-M037`
  (contenuto del riepilogo) e non `SC04-M036`, che enuncia la revisione dei
  messaggi inoltrati come non completata: **attiva in memoria**, 35 token, rango
  14 in U e 19 in G, fuori per budget in entrambe. Entrambe dichiarano che il
  contesto non specifica l'attività aperta, invece di indicarne una sbagliata —
  un miglioramento rispetto alla prima versione di U, che affermava che «resta da
  completare il riepilogo».

---

## 8. Riepilogo numerico (provvisorio)

Valori in [`riepilogo_sc04.json`](riepilogo_sc04.json). Ogni cella mostra
**numeratore / denominatore**. I denominatori zero producono `null`, non zero.

### 8.1 Classi e indicatori (N = 7 per modalità)

| | T | U | G | FULL_HISTORY |
|---|:-:|:-:|:-:|:-:|
| completa | **4** | 2 | 2 | **4** |
| parziale | 2 | **4** | **4** | 2 |
| errata | 0 | 0 | 0 | 0 |
| astensione corretta | 1 | 1 | 1 | 1 |
| giudizi sospesi | 0 | 0 | 0 | 0 |
| **Complete Answer Rate** (complete **e supportate**) | **4/7 = 57,1 %** | **2/7 = 28,6 %** | **2/7 = 28,6 %** | 4/7 = 57,1 % |
| Informazione obsoleta | 0/7 | 0/7 | 0/7 | 0/7 |
| Affermazioni non supportate | 0/7 | 0/7 | 0/7 | 0/7 |
| Astensioni errate | 0/7 | 0/7 | 0/7 | 0/7 |

**Come leggere il denominatore 7.** Le sette prove si dividono in tre categorie
che non vanno confuse:

| Categoria | T | U | G | FULL_HISTORY |
|---|:-:|:-:|:-:|:-:|
| Risposte **complete e supportate** (nel numeratore) | 4 | 2 | 2 | 4 |
| Risposte **parziali o errate** | 2 | 4 | 4 | 2 |
| **Astensioni corrette** — comportamento atteso | 1 | 1 | 1 | 1 |

**L'astensione corretta di Q7 non è un fallimento.** È il comportamento che
l'oracle prescrive (`expected_behavior: Astensione`) e resta fuori dal numeratore
perché quella metrica conta le risposte complete, non i comportamenti corretti.
Il Correct Abstention Rate la misura a parte. Un Complete Answer Rate di 2/7
significa «2 risposte complete e supportate su 7 prove», **non** «5 fallimenti».

Su SC04 **nessuna risposta è `completa` ma non supportata**: conteggio delle
classi e numeratore coincidono in tutte e quattro le modalità.

### 8.2 Metriche di retrieval, relazioni e astensione

**Reachability Rate** = domande raggiungibili / N. Uguale per costruzione: il
perimetro è l'intero scenario in tutte e quattro. **Non distingue le modalità.**

| | T | U | G | FULL_HISTORY |
|---|:-:|:-:|:-:|:-:|
| | 6/7 = 85,7 % | 6/7 = 85,7 % | 6/7 = 85,7 % | 6/7 = 85,7 % |

**Retrieval Success condizionato alla raggiungibilità** = domande con tutti i
`fact_key` RQ2 nel contenuto del contesto / domande raggiungibili.
Denominatore 6 (Q1–Q6).

| | T | U | G | FULL_HISTORY |
|---|:-:|:-:|:-:|:-:|
| | **4/6 = 66,7 %** | **2/6 = 33,3 %** | **2/6 = 33,3 %** | **non applicabile** |

T riceve l'evidenza completa su Q1, Q4, Q5 e Q6; U e G solo su Q1 e Q6. Per
FULL_HISTORY la metrica **non è applicabile**: non esegue selezione e il file di
retrieval non contiene sue righe. Il dato di contenuto — `fact_key` presenti in
6/6 domande raggiungibili — è riportato solo come descrizione.

**Copertura delle relazioni richieste — solo G, tenuta distinta dai fatti.**
Denominatore 11 = 3 (Q2) + 7 (Q3) + 1 (Q4); le altre domande non dichiarano
relazioni.

| | nel contesto di G |
|---|:-:|
| Q2 | 0/3 |
| Q3 | 2/7 |
| Q4 | 1/1 |
| **Totale** | **3/11 = 27,3 %** |

Questa misura **non entra** in Retrieval Success né in Answer Success. Relazioni
espresse nelle risposte, per confronto: T 3/11, U 5/11, G 3/11, FULL_HISTORY
7/11. **G esprime meno relazioni di U**, pur essendo l'unica costruita per
rappresentarle.

**Answer Success condizionato al recupero** = complete e supportate con evidenza
completa nel contesto / prove con evidenza completa nel contesto.

| | T | U | G | FULL_HISTORY |
|---|:-:|:-:|:-:|:-:|
| | 4/4 | 2/2 | 2/2 | **4/6 = 66,7 %** |

**Su T, U e G il valore è 100 % con denominatori 4, 2 e 2.** Dice una cosa sola e
la dice bene: **quando l'evidenza completa arriva nel contesto, tutte e tre
rispondono in modo completo e supportato.** Nessuna delle tre sbaglia
un'evidenza che ha ricevuto. Con denominatori di 2 il valore di U e G va però
riportato come «2 domande su 2», non come percentuale.

Per FULL_HISTORY il **4/6** è il dato più informativo della tabella: con
l'evidenza completa in sei domande, **due risposte restano parziali** (Q2 e Q3).
Quelle due omissioni non sono attribuibili al contesto.

**Correct Abstention Rate** = astensioni corrette / domande non raggiungibili.
Denominatore **1** (solo Q7) in tutte e quattro: **1/1**, da leggere come «1
domanda su 1».

### 8.3 Sensibilità alla lettura discrezionale

Nessun giudizio è sospeso. Una sola lettura è discrezionale, ed è quella più
severa fra le ammissibili.

| Lettura alternativa | Righe toccate | Effetto |
|---|---|---|
| **Q3 meno severa**: la catena di FULL_HISTORY implica che ACC-207 è l'account di UT-207, anche senza dirlo → Q3/FULL_HISTORY diventa `completa` | 1 | FULL_HISTORY: complete 4 → 5, Complete Answer Rate 4/7 → **5/7**; Answer Success 4/6 → **5/6**. **T, U e G non cambiano**, e il confronto fra le tre modalità a budget resta identico. |

Non esiste una lettura ragionevole che cambi la classe di T, U o G: le loro
incompletezze riguardano fatti **assenti dal contesto**, non omissioni
discutibili.

### 8.4 Metriche non calcolate

| Metrica | Perché non è qui |
|---|---|
| Tasso di fatti persi o alterati nell'estrazione | Verificati i 19 `fact_key` più le voci decisive. Il README della correzione dichiara «nessun fatto perso» e il controllo sui fatti usati lo conferma; un tasso completo richiederebbe la verifica di tutti e 41 i fatti. |
| Correttezza delle 41 operazioni di U | 41 proposte, 38 applicate, 3 rifiutate e tutte recuperate dalla passata di riparazione. Confrontarle con le `expected_operations` è una misura di U a sé, non richiesta qui. La questione aperta «eventi o stati» su `RULE-01` è documentata in §11. |
| Qualità del grafo come misura aggregata | Registrati i difetti che incidono sulle risposte: 4 archi con provenienza non valida (oggetto letterale), alias vuoti su tutti e 10 i nodi, stato `superato` su `SC04-E014`, assenza del nodo per la pagina di accesso. Un punteggio complessivo del grafo non è definito nel protocollo. |
| Token e latenza | Descrittivi per scelta di `EXPERIMENT.md` §10. |
| Confronti fra scenari | Fuori dall'ambito di questa scheda. |

### 8.5 Costo del contesto (descrittivo, non una metrica)

| | Elementi (media) | Token del contenuto | Sovraccarico | Totale |
|---|---:|---:|---:|---:|
| T | 1,6 | 125,1 | 11,0 | 136,1 |
| U | 5,4 | 101,1 | 81,4 | 182,6 |
| G | 6,1 | 74,4 | **105,0** | 179,4 |
| FULL_HISTORY | 7,0 | 480,0 | 49,0 | 529,0 |

**G spende il 59 % del contesto che costruisce in struttura** (105,0 token su
179,4) e porta **50,7 token di contenuto in meno di T**. U ne spende il 45 %.
T usa in media 1,6 messaggi e resta 64 token sotto il budget, perché il messaggio
successivo spesso non entra: è l'altra faccia del non frammentare.

---

## 9. Interpretazione del confronto T / U / G

Vale per **SC04, una sola esecuzione per cella, sette domande, tre esecuzioni
diverse messe a confronto**. Non è una conclusione sulle architetture di memoria.

**T e FULL_HISTORY hanno lo stesso tasso: 4/7. U e G hanno lo stesso: 2/7.** La
coincidenza fra T e FULL_HISTORY **non significa che T eguagli la storia
completa**: le due modalità sono complete su insiemi di domande che coincidono
(Q1, Q4, Q5, Q6) e parziali sulle stesse due (Q2, Q3), ma per ragioni opposte —
T perché il contesto non contiene l'evidenza, FULL_HISTORY perché la contiene e
la risposta non la usa. È un pareggio numerico fra due profili diversi.

### 9.1 Le cause documentate, riga per riga

| Prova | Classe | Prima causa | Che cosa mostra l'artefatto |
|---|---|---|---|
| Q1 ×4, Q6 ×4 | completa | – | evidenza nel contesto in tutte e quattro |
| Q7 ×4 | astensione corretta | – | comportamento atteso, verificato contro il corpus |
| **Q2/T**, **Q3/T** | parziale | **retrieval** | il messaggio successivo non entra nel budget: su Q3 il contesto è un solo messaggio di 124 token |
| **Q2/U**, **Q2/G** | parziale | **retrieval** | in U `SC04-M018` a 0,0000 e `SC04-M015` rango 21; in G `SC04-M021` rango 7, fuori per 48 token |
| **Q3/U**, **Q4/U**, **Q5/U** | parziale | **retrieval** | voci **attive in memoria** con punteggio 0,0000 (`SC04-M033`, `SC04-M034`) o fuori per budget (`SC04-M036`, rango 14) |
| **Q3/G** | parziale | **grafo** | alias vuoti su tutti e 10 i nodi, nessun ancoraggio dal testo della domanda: i semi vengono solo dalle voci di U e il percorso trovato ha due archi |
| **Q4/G** | parziale | **grafo** | `SC04-E014` ha stato `superato` ed è escluso dai candidati su una domanda `current`: 14 candidati contro i 32 di U |
| **Q5/G** | parziale | **retrieval** | `SC04-M036` rango 19, fuori per budget: stessa causa di U |
| **Q2/FULL_HISTORY**, **Q3/FULL_HISTORY** | parziale | **risposta** | tutte le evidenze nel contesto; il motivo della classificazione e il passaggio UT-207→ACC-207 restano non detti |

**Origini per modalità:** T → `retrieval` ×2. U → `retrieval` ×4. G →
`retrieval` ×2, **`grafo` ×2**. FULL_HISTORY → `risposta` ×2.

**Tre cose che questa tabella dice.**

1. **G ha due difetti che U non ha, e sono nel grafo, non nel recupero.** Su Q4
   l'arco giusto esiste con lo stato sbagliato ed è filtrato prima del ranking;
   su Q3 l'assenza di alias e di ancoraggio dal testo determina i semi e quindi
   il percorso. Entrambi sono leggibili negli artefatti.
2. **U non perde mai un'informazione in memoria: la perde nel recupero.** Tutte
   e quattro le sue righe non conformi riguardano voci **attive** che non entrano
   nel contesto, per punteggio nullo o per budget. Non ci sono NOOP che
   cancellano fatti, come su SC03.
3. **FULL_HISTORY fallisce in un modo che nessun'altra modalità mostra.** Le sue
   due righe parziali hanno origine `risposta`: sono le uniche due omissioni di
   SC04 non attribuibili al contesto.

### 9.2 Rappresentazione e recupero non sono indipendenti

Su SC04 l'interazione è più diretta che su SC03, e in un caso è decisiva: lo
stato `superato` su `SC04-E014` **non fa perdere una gara di ranking, esclude
l'elemento dalla gara**. La rappresentazione decide che cosa è candidato, non
solo come viene ordinato. Allo stesso modo, gli alias vuoti e il mancato
ancoraggio dal testo della domanda decidono i semi, e i semi decidono i
percorsi.

Nell'altro verso, la rappresentazione relazionale **non ha prodotto il vantaggio
per cui è stata costruita**: su Q3, la domanda di catena per cui SC04 è stato
progettato, G esprime 3 relazioni su 7 e U ne esprime 5, pur non avendo archi.
Le relazioni mancanti **esistono nel grafo**. È un'osservazione su una domanda e
una esecuzione, non una proprietà di G.

**Quello che SC04 non permette di stabilire** è se un grafo con alias popolati e
stati corretti recupererebbe meglio: servirebbero esecuzioni costruite per
variare quei due elementi a parità di tutto il resto.

### 9.3 Spiegazioni ipotizzate, tenute distinte

Che con lo stato corretto `SC04-E014` sarebbe entrato nel contesto di Q4 — resta
comunque da superare ranking e budget. Che con alias popolati i semi di Q3
sarebbero stati diversi e il percorso più lungo. Che con un budget più largo U
avrebbe consegnato `SC04-M036` su Q5. Che T avrebbe risposto a Q3 se
`SC04-S4-U1` fosse entrato. Sono letture coerenti con gli artefatti, **nessuna è
stata verificata**: richiederebbero nuove chiamate al modello, fuori
dall'ambito di questa scheda.

### 9.4 Che cosa questo non dimostra

- **Non dimostra una superiorità generale di nessuna architettura.** Sette
  domande, una esecuzione per cella, nessuna replica, oracle in bozza.
- **Non è un confronto pulito.** Tre esecuzioni in tre giorni diversi.
  FULL_HISTORY non è stata rigenerata con la memoria corretta.
- **Il vantaggio di T su SC04 dipende dalla forma dei messaggi.** Su Q4 e Q5 la
  risposta sta interamente dentro `SC04-S4-U1`, che T riceve intero; su Q3, dove
  la risposta è distribuita su tre sessioni, T è la **peggiore** delle quattro
  (1/6). Non frammentare conserva il contenuto quando è concentrato e lo perde
  quando è distribuito.
- Non dimostra le cause: le origini indicate sono **prime cause osservabili**.
- Non permette di sommare o mediare SC04 con SC02, SC03 o SC05.
- Non dice nulla su F, che su SC04 non esiste.

---

## 10. Nota storica: le prime versioni di U e G (fuori dall'aggregazione)

Le 7 risposte U e le 7 G in `results/rq2/generation_dev_sc04.jsonl` **non
entrano in nessun numero di questa scheda**. Sono riportate qui perché
documentano perché la correzione è stata fatta.

Rilettura diretta, senza riusare le conclusioni del README:

| | prima versione | versione corretta | Differenza osservata |
|---|---|---|---|
| Q2 / G | dichiarava di non avere informazioni sulle valutazioni superate | riporta «spam generico» da `SC04-E005` | **miglioramento**: l'arco con stato `superato` è leggibile su una domanda storica |
| Q3 / U | conteneva un ponte inventato («da questa segnalazione risulta la sessione LOGIN-07») | il ponte sparisce; la risposta dichiara che il nesso non è confermabile | **miglioramento sul supporto**: un'affermazione non supportata in meno |
| Q3 / G | dichiarava l'insufficienza, con una scorciatoia via `CASE-01` | produce una catena con le entità giuste, senza dichiararla incompleta | **misto**: più pertinente, meno prudente |
| Q5 / U | affermava che «resta da completare il riepilogo», che è un requisito e non l'attività aperta | dice che il contesto non lo specifica | **miglioramento**: un'affermazione errata in meno |
| Q1, Q4, Q6, Q7 | – | – | invariati nella sostanza in entrambe le modalità |

Sul piano strutturale la correzione ha aggiunto l'arco `RULE-01 configurata_su
ACC-207` (la relazione `SC04-R08`), che nel grafo precedente **mancava**, e ha
introdotto il difetto nuovo sullo stato di `SC04-E014`. L'ancoraggio ai nodi è
passato da 1 domanda su 7 a **0 su 7**, perché il nodo `RIEPILOGO-01` non esiste
più.

**Le due versioni non sono repliche** e non vanno mediate né sommate. Gli
identificatori delle voci e degli archi non sono stabili fra le versioni: questo
confronto è fatto sul testo.

---

## 11. Punti ancora da chiarire

1. **Lo stato degli archi che descrivono eventi — `SC04-E014`.** L'arco
   `RULE-01 -rimossa-> ACC-207` ha stato `superato`, che dichiara che *l'arco* è
   superato, non che la regola è stata rimossa. Su una domanda a portata
   `current` questo lo esclude dai candidati. È la questione aperta **«eventi o
   stati»** già registrata nel README della correzione, e SC04 ne mostra per la
   prima volta l'effetto su una risposta. Va deciso come rappresentare un evento
   che annulla uno stato precedente, prima di consolidare G.
2. **Alias vuoti e ancoraggio dal testo della domanda.** Tutti e 10 i nodi hanno
   `aliases: []` e nessuna delle 7 domande trova nodi dal proprio testo: i semi
   vengono solo dalle voci di U. Finché è così, **G dipende dal ranking di U per
   il proprio punto di partenza**, e non è chiaro che cosa misuri come
   architettura autonoma.
3. **Archi con oggetto letterale.** 4 archi su 16 hanno provenienza non valida
   perché l'oggetto è un valore e non un nodo dichiarato (`smishing`, `spam
   generico`, `08:05`, `gateway aziendale`). Due di questi — `SC04-E005` e
   `SC04-E015` — sono stati decisivi su Q2 e su Q4. Va deciso se siano archi
   legittimi o nodi mancanti.
4. **La relazione `SC04-R03` non esiste nel grafo.** Non c'è un nodo per la
   pagina di accesso aziendale, quindi la relazione «URL-01 imita
   PAGINA-ACCESSI» non è rappresentabile. È un fatto obbligatorio di Q2 e una
   relazione richiesta: nessuna correzione del retrieval può recuperarla.
5. **Soglia sul punteggio nullo.** Su Q4/U ha escluso `SC04-M033` e `SC04-M034`,
   entrambe attive e contenenti la risposta. È lo stesso punto già aperto su
   SC02, SC03 e SC05.
6. **Valore del budget.** Su Q2/G la selezione si è fermata su `SC04-M021`
   (rango 7, 48 token) che avrebbe completato la risposta; su Q3/T il secondo
   messaggio non è entrato per 12 token. Con un sovraccarico del 59 % in G e del
   45 % in U, la verifica del valore 200 già annunciata in `RQ2.md` §3 ha qui il
   caso più forte della raccolta.
7. **Criteri alternativi su Q2.** `evaluation_dev_sc04.md` §2.4 registra un
   criterio B per questa domanda. Questa scheda ha applicato l'oracle come
   scritto; il criterio B non è stato usato e la decisione resta aperta. Con
   l'oracle attuale il giudizio non cambia per nessuna delle quattro modalità,
   che sono tutte parziali.
8. **La vista è composita.** T dell'8 settembre, U e G del 5, FULL_HISTORY del
   4 e non rigenerata. Va deciso se il protocollo finale rigeneri tutte le celle
   nella stessa esecuzione o se la composizione resti dichiarata.

Nessuna di queste ambiguità è stata risolta modificando i criteri o l'oracle per
adattarli ai risultati.

---

## 12. FULL_HISTORY — sezione separata

FULL_HISTORY è un **controllo diagnostico** e resta **fuori dal confronto a
parità di budget**, come prescritto da `INVENTARIO.md` §2 e da `RQ2.md` §3.

**Perché non è comparabile.**

1. **Non ha budget.** 529 token contro i 136–183 delle altre tre: da tre a
   quasi quattro volte.
2. **Non ha retrieval.** Riceve per costruzione i sette messaggi utente;
   `retrieval_sc04.jsonl` e gli altri file di retrieval non contengono sue righe.
   Il suo Retrieval Success è **non applicabile**, non 100 %.
3. **Non scala.** Su uno scenario di sette messaggi l'intera storia entra nel
   contesto.
4. **Viene da un'altra esecuzione** e non è stata rigenerata nella correzione.

**Esito.** 4 complete e supportate su 7, 2 parziali, 0 errate, 1 astensione
corretta, 0 usi di informazione obsoleta, 0 affermazioni non supportate.

**A che cosa serve, qui.** FULL_HISTORY dispone delle informazioni necessarie
per **sei** delle sette domande: **Q7 richiede astensione**, perché il fatto non
è nel corpus. Su quelle sei stabilisce che le domande sono rispondibili, e quindi
che le incompletezze di U e G su Q3, Q4 e Q5 dipendono dal contesto ricevuto e
non da un difetto del benchmark.

**Ma su SC04 fa anche di più: mostra un limite che non è del contesto.** Il suo
Answer Success è **4/6**. Su Q2 omette il motivo della classificazione e su Q3
omette il passaggio UT-207→ACC-207, con tutte le evidenze davanti. **Due delle
quattordici righe non conformi di SC04 non sono attribuibili al recupero né alla
rappresentazione**, e questo va tenuto presente quando si legge il 2/7 di U e di
G: una parte dell'incompletezza osservata sopravvive anche alla storia completa.

Su **Q7** l'astensione è coerente con l'assenza del fatto ma **non la dimostra**:
un modello può astenersi anche quando l'informazione c'è. L'assenza è stabilita
dalla lettura del corpus (§7).

**Che cosa non va fatto con questa riga.** Non va messa in classifica con T, U e
G; non va usata come «limite superiore» senza dichiarare che non ha budget né
retrieval — e su SC04 non lo è nemmeno, visto che T raggiunge lo stesso 4/7; il
suo 4/7 non va confrontato con il 2/7 di U e G come se le condizioni fossero
paragonabili.

---

## 13. File di questa scheda

| File | Contenuto |
|---|---|
| [`valutazioni_sc04.jsonl`](valutazioni_sc04.jsonl) | Tabella strutturata, 28 righe: classe, indicatori, copertura dei fatti per `fact_key` e delle relazioni per `relation_id` con note su contesto e risposta, copertura dell'oracle, supporto, fedeltà, motivazione, prima causa, contesto ricevuto, portata di lettura, semi del grafo, origine dell'esecuzione, riferimenti di traccia |
| [`valutazioni_sc04.csv`](valutazioni_sc04.csv) | Stessa tabella, vista compatta |
| [`riepilogo_sc04.json`](riepilogo_sc04.json) | Riepilogo per modalità, con numeratore, denominatore, definizione ed esclusioni di ogni metrica, più la copertura delle relazioni di G |
| [`fonti_sc04.json`](fonti_sc04.json) | Percorsi e impronte SHA-256 dei ventisei file letti |
| `valutazione_sc04.md` | Questo rapporto |

Nessun file esistente del progetto è stato modificato. In particolare
`results/rq2/annotation_template_sc04.jsonl` resta intatto, e le valutazioni
precedenti di T e di U/G non sono state riscritte.

**Non prodotti, per scelta:** grafici; estensione ad altri scenari; conclusioni
generali sulle architetture di memoria.

**Prossimo passo:** far rivedere i 28 giudizi proposti e decidere i punti 1, 2 e
8 di §11. Finché non è fatto, il riepilogo numerico resta provvisorio.
