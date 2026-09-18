# SC05 — Ardesia Mobilità / ARD-19: valutazione delle 28 risposte RQ2

**Revisione r1 — 18 settembre 2026.** Prima scheda quantitativa di SC05,
strutturata come SC03 r2 e SC04 r3.

**Stato di approvazione — diverso per modalità, e va tenuto distinto.**

| Gruppo | Stato |
|---|---|
| Classi e indicatori di **U, GER, FULL_HISTORY** (21 risposte) | **approvati dallo studente** il 6 settembre 2026, annotazione `sc05-rq2-ger-0.2`. Riportati **senza riclassificazione**. Non è approvazione del relatore e non congela il protocollo. |
| Classi e indicatori di **T** (7 risposte) | **proposti** in `t_ext_v1`, non approvati. Questa scheda ne propone **due rettifiche dichiarate** (§4). |
| **Supporto, fedeltà al contesto e conteggio complete-e-supportate** (28 righe) | **valutazioni nuove di questa scheda, proposte e non approvate.** Questi campi non esistono nell'annotazione approvata. |

**Natura dei risultati:** **risultati di sviluppo.** Una sola esecuzione per
cella, sette domande per modalità, nessuna replica. Non sono risultati
dell'esperimento.

**Riepilogo numerico provvisorio.** Nessun giudizio è lasciato sospeso.

Nessuna chiamata al modello, nessuna nuova generazione, nessuna riesecuzione di
retrieval o costruzione della memoria. Scenari, oracle, criteri comuni,
configurazioni, codice, risposte e valutazioni precedenti non sono stati
modificati: gli unici file scritti sono i cinque di questa cartella.

---

## 1. Esecuzioni di riferimento

| Modalità | Righe | File delle risposte | Esecuzione | Ruolo |
|---|---:|---|---|---|
| **U** | 7 | `results/rq2/sc05_dev_v1/generation_dev_sc05.jsonl` | `prova-reale-sviluppo-sc05-v1`, **6 settembre 2026** | confronto principale |
| **GER** | 7 | stesso file | stessa esecuzione | confronto principale |
| **T** | 7 | `results/rq2/t_ext_v1/generation_dev_t_sc05.jsonl` | `estensione-t-sviluppo-v1`, **8 settembre 2026** | confronto aggiuntivo |
| **FULL_HISTORY** | 7 | `results/rq2/sc05_dev_v1/generation_dev_sc05.jsonl` | stessa esecuzione di U e GER | controllo diagnostico fuori budget |

**U, GER e FULL_HISTORY vengono dalla stessa esecuzione**, a differenza di SC03
e SC04. Solo T è di un'altra giornata.

### File che alimentano ciascuna modalità

| Modalità | Prompt e contesto | Retrieval | Memoria |
|---|---|---|---|
| U | `sc05_dev_v1/generation_inputs_sc05.jsonl` | `sc05_dev_v1/retrieval_sc05_u_ger.jsonl` | `sc05_dev_v1/memory/scenario_05_state.json` |
| GER | stesso file | stesso file | **lo stesso** file di stato di U |
| T | `t_ext_v1/generation_inputs_t_sc05.jsonl` | `t_ext_v1/retrieval_t_sc05.jsonl` | nessuna: unità = messaggio |
| FULL_HISTORY | `sc05_dev_v1/generation_inputs_sc05.jsonl` | **nessuno** | nessuna: 16 messaggi utente |

### Compatibilità del confronto — verificata

| Controllo | Esito |
|---|---|
| Budget | **200 token** in entrambe le esecuzioni |
| **Stato della memoria** | U e GER leggono **lo stesso file** (`state_source` identico): è ciò che rende il confronto a parità di informazioni disponibili |
| Parametri GER | `ger-rules-0.2`, finestra 2 sessioni (8–9), quote 100/100, **sessione raggiunta 9 dichiarata dal chiamante**, non ripiegata |
| Istruzioni del prompt | **identiche** in tutte e 28 le righe, verificate per confronto di stringa |
| Modello ed effort | `claude-sonnet-5`, effort `medium`, in tutte e 28; `error: null` su tutte |
| Costruzione della memoria | 41 fatti, 41 operazioni proposte e **41 applicate, 0 rifiutate**, 0 riparazioni. Stato finale 34 voci: 27 attive, 7 superate |
| T | nessuna costruzione di memoria; eredita budget, conteggio dei token, regola di selezione e ranking dalla base `rq2-dev-0.1` |
| Identificativi | 28 coppie `(question_id, mode)` distinte |

### Materiale escluso dall'aggregazione

Non entra in nessun numero di questa scheda, e **non va sommato** come se fossero
domande nuove:

| Materiale | Perché è escluso |
|---|---|
| `results/demo_professore_01`, `_02`, `demo_professore_t_01` | demo, 3–4 risposte, ripetizioni della sola Q2 |
| `results/prova_manuale_01`, `_02` | prove singole su Q2, 3 risposte ciascuna |
| `results/rq2/ger_dev/`, `ger_dev_v2/` | controlli tecnici di GER **su memoria da fixture scritte a mano**, non costruita dal modello |
| `results/rq2/t_ext_check/`, `offline_check/` | verifiche offline, nessuna risposta |
| `tests/fixtures/rq2/scenario_05_*` | dati predisposti per i test |

Le ripetizioni della stessa domanda nelle demo **non sono repliche
sperimentali**: non hanno protocollo di replica, e sommarle gonfierebbe i
denominatori.

---

## 2. Fonti

Tutte lette in sola lettura. I ventisei percorsi con le impronte SHA-256 sono in
[`fonti_sc05.json`](fonti_sc05.json). Oltre a quelli di §1:

| Ruolo | File |
|---|---|
| Giudizi **approvati** di U/GER/FULL_HISTORY | `sc05_dev_v1/valutazione_approvata_sc05.md`, `sc05_dev_v1/annotation_compilata_sc05.jsonl` |
| Le due versioni proposte prima dell'approvazione | `sc05_dev_v1/valutazione_assistita_sc05.md`, `…_rev2.md` |
| Template originale, giudizi `null`, **intatto** | `sc05_dev_v1/annotation_template_sc05.jsonl` |
| Giudizi **proposti** di T | `t_ext_v1/valutazione_assistita_t.md`, `t_ext_v1/annotation_compilata_t_sc05.jsonl` |
| Fatti, stato e operazioni della memoria | `sc05_dev_v1/facts/`, `sc05_dev_v1/memory/` |
| Nota di chiusura della prova | `sc05_dev_v1/chiusura_prova_sc05.md` |
| Configurazioni | `data/rq2/config/run_sc05_ger_dev.json`, `…/run_t_ext_sc04_sc05.json` |
| Scenario e oracle | `data/rq2/scenarios/scenario_05.json`, `data/rq2/annotations/scenario_05_rq2.json` |
| Regola di classificazione | `RACCOLTA_RISULTATI/CRITERI_VALUTAZIONE.md` |

---

## 3. Tre misure distinte, tre denominatori distinti

| Misura | Denominatore | Che cosa misura |
|---|---|---|
| `rq2_fact_coverage_in_context` | `required_facts` RQ2 | quanti fatti richiesti sono nel **contenuto del contesto ricevuto** |
| `rq2_fact_coverage_in_answer` | `required_facts` RQ2 | quanti compaiono **nella risposta** |
| `oracle_mandatory_coverage_in_answer` | `mandatory_facts` dell'oracle | quanti fatti dell'oracle la **risposta** soddisfa, con gli equivalenti ammessi |

**Su SC05 i due elenchi coincidono nei conteggi** — 2/2/1/2/2/1/0 sia come
`required_facts` sia come `mandatory_facts` — ma restano misure diverse: la prima
riguarda contesto e risposta, la seconda solo la risposta, e la seconda applica
le clausole `accepted_equivalents`. **Non vanno confuse né sommate.** Su Q7
entrambe hanno denominatore 0 e il valore è `null`, non zero: l'astensione è
valutata a parte.

**Identificatori e provenienza non bastano.** Il controllo è fatto sul
contenuto. La valutazione approvata registra già un falso positivo su Q2/GER:
il campo automatico risulta `true` perché `SC05-M020` cita lo stesso messaggio
sorgente senza esprimere il fatto richiesto.

**Raggiungibilità.** Il perimetro è l'intero scenario in tutte e quattro le
modalità: 16 messaggi utente per T e FULL_HISTORY, 34 voci di memoria per U e
GER. Coincide con `fact_present_in_corpus`: vera per Q1–Q6, **falsa per Q7**.

---

## 4. Criteri applicati e rettifiche proposte su T

Regola `completezza-supporto-1`, la stessa di SC02 r3, SC03 r2 e SC04 r3.

**`faithful_to_received_context`** segue la definizione fissata in SC04 r3: è
falso quando la risposta afferma qualcosa che il contesto ricevuto non contiene,
**anche senza contraddirlo**. `supported_by_original_conversation` misura la
stessa cosa rispetto al corpus. Le due divergono quando una risposta ripete
fedelmente un contesto che il corpus supera: succede su Q3/T e Q4/T.

**I 21 giudizi approvati sono stati confrontati con la regola comune e risultano
tutti coerenti con essa.** Nessuno è stato riclassificato.

**Due rettifiche proposte sui giudizi di T**, che erano proposti e non approvati:

| Riga | t_ext_v1 | Questa scheda | Motivo |
|---|---|---|---|
| **Q4/T** | `parziale` | **`errata`** | La risposta presenta la verifica del registro del bilanciatore come ancora aperta: è letteralmente l'`obsolete_information` che l'oracle di Q4 vieta. La regola comune §1 assegna `errata` quando una risposta usa come valida un'informazione superata, «anche quando alcuni fatti richiesti sono presenti». `t_ext_v1` aveva scelto `parziale` motivandola con l'assenza della parola «unica» nel fatto obbligatorio, e aveva registrato la scelta come **decisione aperta n. 1**. |
| **Q5/T** | «astensione impropria» | `wrong_abstention: false` | `EXPERIMENT.md` §9.4 definisce l'astensione errata solo quando l'evidenza necessaria **è stata recuperata**. Su Q5 tutte le voci utili hanno punteggio 0,0000 e nessuna è nel contesto. **La classe non cambia** (`errata`, 0/2). |

Effetto sui conteggi di T: classi da 3/1/2/1 a **3/0/3/1**; Complete Answer Rate
**invariato a 3/7**, perché Q4/T non era complete-and-supported in nessuna delle
due letture.

---

## 5. Tabella dei giudizi

Tabella completa: [`valutazioni_sc05.jsonl`](valutazioni_sc05.jsonl) (28 righe,
con `rq2_fact_detail` e, per GER, `ger_trace`) e
[`valutazioni_sc05.csv`](valutazioni_sc05.csv).

Legenda: **F ctx / F risp** = `required_facts` RQ2 nel contenuto del contesto /
nella risposta; **Oracle** = `mandatory_facts` soddisfatti dalla risposta;
**Sup.** = supportata dalle conversazioni originali; **Fed.** = fedele al
contesto ricevuto; **C&S** = conta come completa e supportata.

### U — Fact-based con aggiornamenti *(classi approvate)*

| Dom. | F ctx | F risp | Oracle | Classe | Sup. | Fed. | C&S | Obs. | Non sup. | Causa |
|---|:-:|:-:|:-:|---|:-:|:-:|:-:|:-:|:-:|---|
| Q1 obiettivo | 2/2 | **1/2** | **1/2** | **parziale** | sì | sì | no | no | no | risposta |
| Q2 server corretto | 2/2 | 2/2 | 2/2 | **completa** | sì | sì | **sì** | no | no | – |
| Q3 verifiche aperte | **0/1** | 0/1 | **0/1** | **errata** | **no** | **no** | no | no | **sì** | retrieval |
| Q4 due livelli | **1/2** | 1/2 | **1/2** | **parziale** | sì | sì | no | no | no | retrieval |
| Q5 verifiche completate | **0/2** | 0/2 | **0/2** | **errata** | **no** | **no** | no | no | **sì** | retrieval |
| Q6 scadenza cliente | 1/1 | 1/1 | 1/1 | **completa** | sì | sì | **sì** | no | no | – |
| Q7 informazione assente | n.d. | n.d. | n.d. | **astensione corretta** | sì | sì | n.a. | no | no | – |

### GER — memoria recente e archivio *(classi approvate)*

| Dom. | F ctx | F risp | Oracle | Classe | Sup. | Fed. | C&S | Obs. | Non sup. | Causa |
|---|:-:|:-:|:-:|---|:-:|:-:|:-:|:-:|:-:|---|
| Q1 | 2/2 | **1/2** | **1/2** | **parziale** | sì | sì | no | no | no | risposta |
| Q2 | **1/2** | 1/2 | **1/2** | **parziale** | sì | sì | no | no | no | retrieval |
| Q3 | **0/1** | 0/1 | **0/1** | **errata** | **no** | **no** | no | no | **sì** | retrieval |
| Q4 | **1/2** | 1/2 | **1/2** | **parziale** | sì | sì | no | no | no | retrieval |
| Q5 | **0/2** | 0/2 | **0/2** | **errata** | **no** | **no** | no | no | **sì** | retrieval |
| Q6 | 1/1 | 1/1 | 1/1 | **completa** | sì | sì | **sì** | no | no | – |
| Q7 | n.d. | n.d. | n.d. | **astensione corretta** | sì | sì | n.a. | no | no | – |

### T — Turn-level RAG *(classi proposte; Q4 e Q5 rettificate, §4)*

| Dom. | F ctx | F risp | Oracle | Classe | Sup. | Fed. | C&S | Obs. | Non sup. | Causa |
|---|:-:|:-:|:-:|---|:-:|:-:|:-:|:-:|:-:|---|
| Q1 | 2/2 | 2/2 | 2/2 | **completa** | sì | sì | **sì** | no | no | – |
| Q2 | 2/2 | 2/2 | 2/2 | **completa** | sì | sì | **sì** | no | no | – |
| Q3 | **0/1** | 0/1 | **0/1** | **errata** | **no** | sì | no | **sì** | no | retrieval |
| Q4 | 2/2 | 2/2 | 2/2 | **errata** ⚑ | **no** | sì | no | **sì** | no | retrieval |
| Q5 | **0/2** | 0/2 | **0/2** | **errata** | sì | sì | no | no | no | retrieval |
| Q6 | 1/1 | 1/1 | 1/1 | **completa** | sì | sì | **sì** | no | no | – |
| Q7 | n.d. | n.d. | n.d. | **astensione corretta** | sì | sì | n.a. | no | no | – |

⚑ rettifica proposta in questa scheda (§4).

### FULL_HISTORY — controllo diagnostico, fuori confronto (§10) *(classi approvate)*

| Dom. | F ctx | F risp | Oracle | Classe | Sup. | Fed. | C&S | Obs. | Non sup. | Causa |
|---|:-:|:-:|:-:|---|:-:|:-:|:-:|:-:|:-:|---|
| Q1 | 2/2 | 2/2 | 2/2 | **completa** | sì | sì | sì | no | no | – |
| Q2 | 2/2 | 2/2 | 2/2 | **completa** | sì | sì | sì | no | no | – |
| Q3 | 1/1 | 1/1 | 1/1 | **completa** | sì | sì | sì | no | no | – |
| Q4 | 2/2 | 2/2 | 2/2 | **completa** | sì | sì | sì | no | no | – |
| Q5 | 2/2 | 2/2 | 2/2 | **completa** | sì | sì | sì | no | no | – |
| Q6 | 1/1 | 1/1 | 1/1 | **completa** | sì | sì | sì | no | no | – |
| Q7 | n.d. | n.d. | n.d. | **astensione corretta** | sì | sì | n.a. | no | no | – |

---

## 6. GER: che cosa era disponibile, che cosa è stato selezionato, che cosa è arrivato

GER partiziona la memoria in **recente** (sessioni 8–9, con la sessione raggiunta
dichiarata a 9) e **archivio** (sessioni 1–7), con una quota di 100 token
ciascuno e una seconda fase che riusa lo spazio non speso. Su SC05 i livelli
contengono **20 voci leggibili in archivio e 7 recenti** sulle domande a portata
`current`.

Ricostruzione dai log (`ger_decisions`, `ger_reuse`, `ger_excluded_over_budget`,
tutti in `ger_trace` nel JSONL):

| Dom. | Archivio selez. | Recente selez. | Riuso 2ª fase | Esito rispetto a U |
|---|---|---|---|---|
| Q1 | 3 el. / 93 tok | 3 el. / 94 tok | 0 tok | **identico**: stessi fatti coperti |
| **Q2** | 2 el. / 83 tok | 3 el. / 93 tok | 0 tok | **peggiore**: manca `SC05-M018` |
| Q3 | 5 el. / 156 tok | 1 el. / 39 tok | 63 tok | identico: entrambe mancano `SC05-M040` |
| Q4 | 2 el. / 80 tok | 3 el. / 93 tok | 0 tok | identico |
| Q5 | 5 el. / 168 tok | **0 el. / 0 tok** | 75 tok | identico: entrambe mancano tutto |
| Q6 | 3 el. / 101 tok | 3 el. / 96 tok | 33 tok | identico |
| Q7 | 3 el. / 94 tok | 3 el. / 93 tok | 0 tok | identico |

**Le quattro cause vanno tenute distinte, e su SC05 sono distinguibili.**

**1. Perdita o cattiva gestione dell'informazione in memoria: nessun caso.** 41
operazioni proposte, 41 applicate, 0 rifiutate, 0 riparazioni. Tutte le evidenze
mancanti nei contesti sono **in memoria, attive e corrette**: `SC05-M018`,
`SC05-M040`, `SC05-M032`, `SC05-M033`, `SC05-M037`, `SC05-M038`. Su SC05 la
gestione non è mai la causa — a differenza di SC03, dove un NOOP aveva
cancellato un fatto.

**2. Esclusione dovuta alla partizione recente/archivio: un solo caso, Q2.**
`SC05-M018` («l'accesso anomalo non è arrivato da SRV-12, ma dal server esposto
SRV-14») è **nell'archivio**, al rango 5 con 0,1694. La quota archivio aveva già
speso 83 token su 100 — `SC05-M008` (30) e `SC05-M020` (53) — e il residuo era
24 token contro i 37 richiesti. **U, con un budget unico da 200, la prende e
chiude a 177 token.** Questa è l'unica differenza fra U e GER su tutte e sette
le domande, ed è attribuibile alla partizione.

**3. Mancato recupero per punteggio nullo: la causa dominante.** Su **Q3** e
**Q5** le voci che contengono la risposta hanno punteggio **0,0000** in entrambe
le modalità, con la stessa motivazione registrata nella traccia: «nessun termine
in comune con la domanda». Su Q5 questo azzera **tutte e sette** le voci recenti,
e infatti GER non seleziona nulla dal livello recente: la quota di 100 token
resta inutilizzata e 75 token tornano all'archivio. **La quota non è il limite:
il limite è il ranking.** La causa è documentata nella valutazione approvata: la
domanda dice «verifiche… completate», la memoria «la verifica… è completata», e
il TF-IDF non riduce alla radice.

**4. Esclusione per budget dopo il ranking: un caso, Q4.** `SC05-M040` è nel
livello **recente**, rango 22 con 0,0170, e la traccia registra «spazio residuo
già chiuso su un elemento precedente». Anche U non la seleziona, allo stesso
rango: qui la partizione non incide.

**5. Omissione nella risposta: Q1, in entrambe.** Il secondo obiettivo è
riconoscibile nel contesto di U e di GER — `SC05-M041` — e nessuna delle due lo
riporta. L'origine approvata è `risposta`. La trasformazione dell'obiettivo
nell'enunciato del suo compimento resta una **possibile concausa, non
dimostrata**.

**Che cosa questa ricostruzione non autorizza a dire.** Non che la partizione
recente/archivio sia dannosa: su sei domande su sette non cambia nulla, e
sull'unica in cui cambia qualcosa il costo è un elemento che non entra nella
quota. Non che il riuso della seconda fase sia inefficace: su Q3, Q5 e Q6 ha
restituito 63, 75 e 33 token all'archivio, ed è documentato.

---

## 7. Motivazioni per domanda

Versione integrale nel campo `rationale` di ogni riga. Qui i casi che portano
informazione.

### Q1 — tutte e quattro hanno l'evidenza; due la usano

I due obiettivi sono in `SC05-S1-U1`. **T e FULL_HISTORY**, che ricevono il
messaggio intero, li riportano entrambi: **complete**. **U e GER** hanno
`SC05-M002` (primo obiettivo) e `SC05-M041`, che enuncia il compimento del
secondo («il portale è tornato in servizio per i fornitori attivi…
soddisfacendo l'obiettivo di ripristino senza interruzioni»), e riportano solo
il primo: **parziali, origine `risposta`**. Copertura RQ2 nel contesto 2/2, nella
risposta 1/2.

### Q2 — l'unica domanda in cui GER e U divergono

- **U — completa.** `SC05-M008` (SRV-12, «superato») e `SC05-M018` (SRV-14)
  sono entrambe nel contesto, e la risposta distingue l'indicazione iniziale da
  quella corretta.
- **GER — parziale, origine `retrieval`.** Manca `SC05-M018` (§6, causa 2). La
  risposta **dichiara l'insufficienza sul server corretto invece di
  inventarlo**: supportata e fedele.
- **T — completa.** La correzione è scritta **dentro** `SC05-S4-U1` («il server
  esposto non è SRV-12 ma SRV-14»), quindi T distingue le due indicazioni **senza
  avere uno stato temporale**. È una protezione che viene dalla formulazione del
  messaggio, non dall'architettura.
- **FULL_HISTORY — completa.**

Q2 è **l'unica domanda a portata `history`**, cioè l'unica in cui le voci
superate sono leggibili. È lì che il rischio di informazione obsoleta è stato
davvero esercitato: `SC05-M008` e `SC05-M035`, entrambe `superato`, sono entrate
nel contesto di U e di GER, e **entrambe le hanno presentate correttamente come
indicazioni iniziali**.

### Q3 — la stessa incompletezza, due comportamenti diversi

Il fatto richiede che la revisione delle regole sia l'**unica** verifica aperta.

- **U e GER — errate, `unsupported_claim`.** `SC05-M040` ha punteggio 0,0000 in
  entrambe. Nessuna voce sulle verifiche entra nel contesto, ed entrambe elencano
  come «aperte» l'obiettivo del caso e il vettore delle credenziali: attribuiscono
  all'obiettivo lo stato «non ancora concluso» e la qualifica di «verifiche» a due
  elementi che non lo sono. Supporto e fedeltà **entrambi falsi**: il contesto non
  dice né l'uno né l'altra.
- **T — errata, `obsolete_used`.** Il contesto contiene `SC05-S8-U1` («restano
  aperte la verifica del registro del bilanciatore e la revisione delle regole»),
  e `SC05-S9-U1`, che completa il bilanciatore, non è selezionato. T risponde
  con le due verifiche di S8: **fedele al contesto, non supportata dal corpus**.
- **FULL_HISTORY — completa.**

**Due modi opposti di sbagliare la stessa domanda.** U e GER inventano stati
che il contesto non contiene; T ripete fedelmente un contesto superato. Nessuna
delle due forme è preferibile all'altra sul piano della classe.

### Q4 — dove la rettifica su T cambia la classe

- **U e GER — parziali.** Il vincolo sul rapporto (`SC05-M004`) è nel contesto ed
  è riportato correttamente; `SC05-M040` manca. Entrambe dichiarano di non poter
  indicare le verifiche aperte, invece di indicarne una sbagliata. Sulla frase di
  GER — «la verifica di integrità dei backup risulta completata…, quindi non
  risultano verifiche pendenti indicate» — la valutazione approvata ha deciso che,
  **letta per intero**, è un enunciato su ciò che il contesto indica ed è vero:
  non conta come affermazione non supportata. La decisione è mantenuta, con
  l'annotazione già registrata che il nesso «quindi» è debole.
- **T — errata (rettifica, §4).** Consegna **entrambi** i fatti obbligatori, ma
  aggiunge il bilanciatore fra le verifiche da completare: è l'informazione
  obsoleta che l'oracle vieta.
- **FULL_HISTORY — completa.**

È il caso più istruttivo del confronto: **T copre 2/2 fatti e ha la classe
peggiore**, U e GER ne coprono 1/2 e sono parziali. Non consegnare un fatto e
consegnarne uno superato non sono lo stesso tipo di errore.

### Q5 — nessuna modalità a budget risponde; il livello recente resta vuoto

L'oracle chiede due verifiche completate con i rispettivi esiti. Nessuna delle
tre modalità a budget ne consegna una: copertura **0/2** in tutte e tre.

- **U e GER — errate, `unsupported_claim`.** Entrambe qualificano `SC05-M031`
  (coordinate bancarie non coinvolte) come verifica completata: il contesto non
  lo dice. In GER la dichiarazione di insufficienza non elimina l'affermazione.
- **T — errata (0/2), senza affermazioni non supportate.** Dichiara
  l'insufficienza e descrive correttamente ciò che ha ricevuto.
  `wrong_abstention` resta falso (§4).
- **FULL_HISTORY — completa**, con entrambe le verifiche e i rispettivi esiti.

Su questa domanda il livello recente di GER **non contribuisce con nessun
elemento**: tutte e sette le voci recenti hanno punteggio 0,0000 (§6).

### Q6 e Q7 — nessuna differenza

Su **Q6** tutte e quattro rispondono «entro dieci giorni lavorativi»:
`SC05-M011` è al rango 1 con 0,8096 in U e in GER. Su **Q7** tutte e quattro si
astengono.

**L'assenza su Q7 è stata verificata leggendo il corpus:** nelle nove sessioni
non compaiono «fornitore esterno», «gestore», «provider» né altri soggetti
terzi; i backup sono citati una sola volta, in `SC05-S8-U1`. Nessuna delle
quattro inventa un fornitore, **malgrado le voci sui backup siano nel contesto**
di U (`SC05-M032`, `SC05-M033`), di GER (le stesse, nel livello recente) e di T
(`SC05-S8-U1`).

---

## 8. Riepilogo numerico (provvisorio)

Valori in [`riepilogo_sc05.json`](riepilogo_sc05.json). Ogni cella mostra
**numeratore / denominatore**. I denominatori zero producono `null`, non zero.

### 8.1 Classi e indicatori (N = 7 per modalità)

| | U | GER | T | FULL_HISTORY |
|---|:-:|:-:|:-:|:-:|
| completa | 2 | 1 | 3 | **6** |
| parziale | 2 | **3** | 0 | 0 |
| errata | 2 | 2 | **3** | 0 |
| astensione corretta | 1 | 1 | 1 | 1 |
| **Complete Answer Rate** (complete **e supportate**) | **2/7 = 28,6 %** | **1/7 = 14,3 %** | **3/7 = 42,9 %** | 6/7 = 85,7 % |
| Informazione obsoleta | 0/7 | 0/7 | **2/7 = 28,6 %** | 0/7 |
| Affermazioni non supportate | **2/7 = 28,6 %** | **2/7 = 28,6 %** | 0/7 | 0/7 |
| Astensioni errate | 0/7 | 0/7 | 0/7 | 0/7 |

Le classi di U, GER e FULL_HISTORY coincidono con quelle della tabella approvata
in `valutazione_approvata_sc05.md`: il conteggio è stato riverificato riga per
riga sull'annotazione compilata.

**Come leggere il denominatore 7.**

| Categoria | U | GER | T | FULL_HISTORY |
|---|:-:|:-:|:-:|:-:|
| Risposte **complete e supportate** (nel numeratore) | 2 | 1 | 3 | 6 |
| Risposte **parziali o errate** | 4 | 5 | 3 | 0 |
| **Astensioni corrette** — comportamento atteso | 1 | 1 | 1 | 1 |

**L'astensione corretta di Q7 non è un fallimento.** È il comportamento che
l'oracle prescrive, e resta fuori dal numeratore perché quella metrica conta le
risposte complete, non i comportamenti corretti. Un Complete Answer Rate di 1/7
significa «1 risposta completa e supportata su 7 prove», **non** «6 fallimenti».

Su SC05 **nessuna risposta è `completa` ma non supportata**: conteggio delle
classi e numeratore coincidono in tutte e quattro le modalità.

### 8.2 Metriche di retrieval e astensione

**Reachability Rate** = domande raggiungibili / N. Uguale per costruzione:
**6/7 = 85,7 %** in tutte e quattro. Non distingue le modalità.

**Retrieval Success condizionato alla raggiungibilità** = domande con tutti i
`required_facts` RQ2 nel **contenuto** del contesto / domande raggiungibili.
Denominatore 6 (Q1–Q6).

| | U | GER | T | FULL_HISTORY |
|---|:-:|:-:|:-:|:-:|
| | **3/6 = 50,0 %** | **2/6 = 33,3 %** | **4/6 = 66,7 %** | **non applicabile** |

U riceve l'evidenza completa su Q1, Q2 e Q6; GER su Q1 e Q6; T su Q1, Q2, Q4 e
Q6. Per FULL_HISTORY la metrica **non è applicabile**: non esegue selezione. Il
dato di contenuto — `required_facts` presenti in 6/6 domande raggiungibili — è
riportato solo come descrizione.

**Answer Success condizionato al recupero** = complete e supportate con evidenza
completa nel contesto / prove con evidenza completa nel contesto.

| | U | GER | T | FULL_HISTORY |
|---|:-:|:-:|:-:|:-:|
| | 2/3 | 1/2 | 3/4 | 6/6 |

**Denominatori da 2 a 4: i valori non vanno riportati come percentuali.** Vanno
letti come «2 su 3», «1 su 2», «3 su 4». In ciascuna modalità la riga che manca
al numeratore è Q1, dove l'evidenza c'era e la risposta ha omesso il secondo
obiettivo — per T, Q4, dove l'evidenza c'era ed è stata usata insieme a una
superata.

**Correct Abstention Rate** = astensioni corrette / domande non raggiungibili.
Denominatore **1** (solo Q7) in tutte e quattro: **1/1**, da leggere come «1
domanda su 1».

### 8.3 Metriche non calcolate

| Metrica | Perché non è qui |
|---|---|
| Tasso di errori nella gestione della memoria | 41 operazioni su 41 applicate, 0 rifiutate, 0 riparazioni: il tasso sarebbe 0 su questa prova, ed è riportato come dato descrittivo in §1, non come metrica di qualità. |
| Misure di grafo | Non applicabili: SC05 non ha una modalità G. |
| Copertura delle relazioni | L'annotazione RQ2 di SC05 non dichiara relazioni. |
| Token e latenza | Descrittivi per scelta di `EXPERIMENT.md` §10. |
| Confronti fra scenari e sintesi complessiva di RQ2 | Fuori dall'ambito di questa scheda. |

### 8.4 Costo del contesto (descrittivo, non una metrica)

| | Elementi (media) | Token del contenuto | Sovraccarico | Totale |
|---|---:|---:|---:|---:|
| T | 3,7 | 147,7 | 26,0 | 173,7 |
| U | 5,6 | 94,3 | 83,6 | 177,9 |
| GER | 5,6 | 88,6 | **94,7** | 183,3 |
| FULL_HISTORY | 16,0 | 533,0 | 112,0 | 645,0 |

**GER spende il 52 % del contesto che costruisce in struttura** — l'etichetta di
livello si aggiunge a identificatore, stato e provenienza — contro il 47 % di U
e il 15 % di T. A parità di 200 token GER porta **5,7 token di contenuto in meno
di U** e 59 in meno di T. FULL_HISTORY, con 645 token, è oltre il triplo del
budget.

---

## 9. Interpretazione, limitata a questa prova

Vale per **SC05, una sola esecuzione per cella, sette domande**. Non è una
conclusione sulle architetture di memoria.

**GER non mostra alcun vantaggio su U: 1/7 contro 2/7.** L'unica domanda in cui
le due differiscono è Q2, e la differenza è **a sfavore di GER**: la quota
archivio esclude per 13 token l'unica voce che identifica il server corretto,
che U prende con il budget unico. Su tutte le altre sei domande l'esito è lo
stesso. È il risultato già registrato nella valutazione approvata, e questa
scheda lo conferma senza modificarlo.

**Il collo di bottiglia è la selezione, non la disponibilità — e questo è
documentato.** Tutte le evidenze mancanti nei contesti di U e GER erano in
memoria, **attive e corrette**. Nessuna operazione è stata rifiutata, nessun
fatto è andato perso. Su Q3 e Q5 la causa è il punteggio nullo, in entrambe le
modalità e indipendentemente dalla partizione.

**La partizione recente/archivio non è stata esercitata come previsto.** Su Q5 il
livello recente non contribuisce con nessun elemento, perché tutte e sette le
voci recenti hanno punteggio 0,0000; la quota resta inutilizzata e il riuso
restituisce 75 token all'archivio. GER paga il costo strutturale della
partizione (94,7 token di sovraccarico medio) senza esercitarne il beneficio.

**T ha il tasso più alto fra le modalità a budget, ma è anche l'unica a usare
informazione obsoleta.** 3/7 contro 2/7 e 1/7, e 2 usi di informazione superata
su 7 contro 0 e 0. I due dati vanno letti insieme: dove la risposta sta in un
solo messaggio (Q1, Q2, Q6) T vince perché non frammenta; dove un messaggio
successivo supera quello recuperato (Q3, Q4) T non ha modo di saperlo, perché
**non ha uno stato temporale**. U e GER non commettono quell'errore, ma in sei
domande su sette **non avrebbero potuto**: la politica di lettura rende le voci
superate accessibili solo alle domande storiche, e l'unica storica è Q2.
L'assenza di informazione obsoleta in U e GER **non dimostra quindi che la
gestione dello stato funzioni**; dimostra che su questo scenario il rischio è
stato esercitato una volta sola.

**Osservazione simmetrica, documentata.** Su Q3 e Q4 T ripete fedelmente un
contesto superato; su Q3 e Q5 U e GER attribuiscono stati che il contesto non
contiene. Due profili di errore opposti — obsoleto contro non supportato — che si
rispecchiano nelle due colonne di §8.1: T 2/7 e 0/7, U e GER 0/7 e 2/7.

**Spiegazioni ipotizzate, tenute distinte.** Che con `SC05-M018` nel contesto
GER avrebbe risposto come U su Q2; che senza la soglia sul punteggio nullo Q3 e
Q5 sarebbero state complete; che una finestra recente più larga avrebbe cambiato
Q5; che la trasformazione dell'obiettivo nel suo compimento abbia causato
l'omissione su Q1. Sono letture coerenti con gli artefatti, **nessuna è stata
verificata**: richiederebbero nuove chiamate al modello.

**Che cosa questo non dimostra.**

- **Non dimostra una superiorità generale di U su GER, né di T su entrambe.**
  Sette domande, una esecuzione per cella, nessuna replica, e una sola domanda di
  differenza fra U e GER.
- Non dimostra le cause: le origini indicate sono **prime cause osservabili**.
- Non permette di sommare o mediare SC05 con SC02, SC03 o SC04.
- Non dice nulla su F e G, che su SC05 non esistono.

---

## 10. FULL_HISTORY — sezione separata

FULL_HISTORY è un **controllo diagnostico** e resta **fuori dal confronto a
parità di budget**.

1. **Non ha budget.** **645 token** contro i 174–183 delle altre tre: oltre il
   triplo. È lo scarto più grande di tutta la raccolta.
2. **Non ha retrieval.** Riceve i 16 messaggi utente per costruzione. Il suo
   Retrieval Success è **non applicabile**, non 100 %.
3. **Non scala.** SC05 ha 9 sessioni e 16 messaggi: è lo scenario più lungo della
   raccolta, e proprio per questo il divario di token è il più visibile.

**Esito.** 6 complete e supportate su 7, 1 astensione corretta, 0 parziali, 0
errate, 0 usi di informazione obsoleta, 0 affermazioni non supportate.
**Answer Success 6/6:** ogni volta che ha l'evidenza, la usa.

**A che cosa serve.** FULL_HISTORY dispone delle informazioni necessarie per
**sei** delle sette domande: **Q7 richiede astensione**, perché il fatto non è
nel corpus. Su quelle sei stabilisce che le domande sono rispondibili, e quindi
che le incompletezze di U, GER e T dipendono dal contesto ricevuto — o dal suo
uso — e non da un difetto del benchmark. È l'unica delle quattro a rispondere
correttamente a Q3, Q4 e Q5.

Su **Q7** l'astensione è coerente con l'assenza del fatto ma **non la dimostra**:
un modello può astenersi anche quando l'informazione c'è. L'assenza è stabilita
dalla lettura del corpus (§7).

**Che cosa non va fatto con questa riga.** Non va messa in classifica con U, GER
e T; non va usata come «limite superiore» senza dichiarare che riceve 645 token
contro 200; il suo 6/7 non va confrontato con l'1/7 di GER come se le condizioni
fossero paragonabili.

---

## 11. Punti ancora da chiarire

1. **Rettifica proposta su Q4/T.** Il passaggio da `parziale` a `errata` applica
   la regola comune, ma **riapre la decisione n. 1 di `t_ext_v1`**: se l'uso di
   informazione superata debba portare a `errata` per sé, indipendentemente dai
   fatti obbligatori consegnati. Qui è stata applicata la regola come scritta.
   Effetto: classi di T da 3/1/2/1 a 3/0/3/1, **Complete Answer Rate invariato a
   3/7**.
2. **`wrong_abstention` quando l'evidenza non è stata recuperata.** La questione
   era già dichiarata aperta nella valutazione approvata di SC05 e resta tale.
   Qui l'indicatore segue §9.4 alla lettera ed è falso ovunque, anche su Q5/T e
   Q5/GER, che dichiarano l'insufficienza su una domanda a cui il corpus
   permette di rispondere.
3. **Soglia sul punteggio nullo.** Su Q3 e Q5 esclude voci **attive e corrette**
   che contengono la risposta, in tutte le modalità a budget. Su Q5 azzera
   l'intero livello recente di GER. È lo stesso punto già aperto su SC02, SC03 e
   SC04, e su SC05 è la causa dominante.
4. **Dimensionamento delle quote di GER.** Su Q2 la quota archivio esclude
   `SC05-M018` per 13 token; su Q5 la quota recente resta interamente
   inutilizzata. Va deciso se le quote fisse 100/100 siano la configurazione da
   valutare, o se questa prova misuri soprattutto quella scelta.
5. **Sovraccarico e valore del budget.** GER spende 94,7 token medi in struttura
   su 183,3: più della metà. La verifica del valore 200 annunciata in `RQ2.md`
   §3 riguarda GER più di ogni altra modalità.
6. **Portata di lettura e rischio obsoleto.** Solo Q2 è `history`. Con una sola
   domanda storica su sette, lo 0/7 di informazione obsoleta di U e GER non è un
   risultato robusto: andrebbero costruite domande storiche in numero maggiore
   per esercitare davvero la politica di lettura.
7. **Definizione di `faithful_to_received_context`, da allineare fra le schede.**
   Questa scheda usa la definizione di SC04 r3 (falso quando la risposta afferma
   qualcosa che il contesto non contiene). SC03 r2 usa una lettura più permissiva
   su Q5/U. L'allineamento è segnalato anche in SC04 §11 e non è stato fatto qui.
8. **Stato di approvazione misto.** 21 righe hanno classi approvate, 7 no, e i
   campi su supporto e fedeltà sono nuovi e proposti per tutte e 28.
   Un'eventuale aggregazione di RQ2 deve portarsi dietro questa distinzione.

---

## 12. File di questa scheda

| File | Contenuto |
|---|---|
| [`valutazioni_sc05.jsonl`](valutazioni_sc05.jsonl) | 28 righe: classe e stato di approvazione, indicatori, copertura RQ2 per `fact_key` nel contesto e nella risposta, copertura dell'oracle, supporto, fedeltà, motivazione, prima causa, `ger_trace` con livelli, quote, selezioni e riuso, contesto ricevuto, riferimenti di traccia |
| [`valutazioni_sc05.csv`](valutazioni_sc05.csv) | Stessa tabella, vista compatta |
| [`riepilogo_sc05.json`](riepilogo_sc05.json) | Riepilogo per modalità, con numeratore, denominatore, definizione ed esclusioni di ogni metrica, e lo stato di approvazione per gruppo |
| [`fonti_sc05.json`](fonti_sc05.json) | Percorsi e impronte SHA-256 dei ventisei file letti |
| `valutazione_sc05.md` | Questo rapporto |

Nessun file esistente del progetto è stato modificato. In particolare
`annotation_template_sc05.jsonl` conserva i giudizi a `null`,
`annotation_compilata_sc05.jsonl` e `valutazione_approvata_sc05.md` restano
intatti, e le due versioni proposte prima dell'approvazione sono conservate dove
sono.

**Non prodotti, per scelta:** grafici; sintesi complessiva di RQ2; estensione ad
altri scenari.

**Prossimo passo:** far rivedere le due rettifiche proposte su T e i campi nuovi
su supporto e fedeltà, e decidere i punti 1, 4 e 7 di §11.
