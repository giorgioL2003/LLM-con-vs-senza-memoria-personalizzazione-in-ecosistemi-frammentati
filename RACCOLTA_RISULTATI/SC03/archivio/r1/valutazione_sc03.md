# SC03 — Vesper Logistics / WS-114: valutazione delle 21 risposte RQ2

**Revisione r1 — 18 settembre 2026.** Prima scheda quantitativa di SC03.
Struttura ripresa dalla scheda SC02 r3; **i giudizi sono nuovi e ricavati dalle
evidenze di SC03**, non trasferiti da SC02.

**Stato dei giudizi:** **valutazioni assistite proposte dall'assistente, non
approvate.** Nessuna approvazione dello studente, nessuna approvazione del
relatore, protocollo non congelato.

**Natura dei risultati:** **risultati di sviluppo.** Una sola esecuzione per
cella, sette domande per modalità, nessuna replica, oracle e annotazioni ancora
in bozza (`status: BOZZA DA CONTROLLARE`). Non sono risultati dell'esperimento.

**Stato del riepilogo numerico:** **provvisorio**, in attesa della revisione dei
giudizi. Nessun giudizio è lasciato sospeso; le letture dell'oracle che
avrebbero potuto giustificarne una sono dichiarate in §8 con l'effetto
quantificato.

Nessuna chiamata al modello, nessuna nuova generazione, nessuna riesecuzione del
retrieval o della costruzione della memoria. Scenari, oracle, configurazioni,
codice, risposte e valutazioni precedenti non sono stati modificati: gli unici
file scritti sono i cinque di questa cartella.

---

## 1. Composizione del confronto e verifica delle esecuzioni

Il confronto principale è formato da **21 risposte**, ma **non da una sola
esecuzione**. È una vista composita, e va dichiarata come tale ogni volta che i
numeri vengono riportati.

| Modalità | Righe | File | Esecuzione |
|---|---:|---|---|
| **F** | 7 | `results/rq2/generation_dev_sc03.jsonl` | **iniziale**, 5 settembre 2026 |
| **FULL_HISTORY** | 7 | `results/rq2/generation_dev_sc03.jsonl` | **iniziale**, 5 settembre 2026 |
| **U** | 7 | `results/rq2/retrieval_repair_v3/generation_dev_sc03_u.jsonl` | **successiva**, versione corretta con `u-instructions-0.3` |

### Verifiche eseguite

| Controllo | Esito |
|---|---|
| Identificativi | 21 coppie `(question_id, mode)` distinte; SC03-Q1…SC03-Q7 × {F, U, FULL_HISTORY} |
| Numero di righe | 21 su 21 attese; il file iniziale ne ha 21 (7 F + 7 U + 7 FULL_HISTORY), quello della correzione 7 (solo U) |
| Errori | `error: null` su tutte e 21 |
| Modello ed effort | `claude-sonnet-5`, effort `medium`, in tutte e 21 e in entrambe le esecuzioni |
| Istruzioni del prompt | **identiche** in tutte le righe delle due esecuzioni: unico blocco di istruzioni, verificato per confronto di stringa |
| Configurazione | `rq2-dev-0.1`, budget 200 token, ranking TF-IDF/coseno, invariati fra le due esecuzioni (dichiarato nel README della correzione e coerente con i file di retrieval) |
| Etichetta di esecuzione | `esecuzione` per F; `prova-riparazione-u-instructions-0.3` per U; FULL_HISTORY non ha riga di retrieval |

### Le prime 7 risposte U restano fuori

Le 7 risposte U presenti in `results/rq2/generation_dev_sc03.jsonl` **non
entrano in nessuna aggregazione di questa scheda**. Sono consultate solo in §10,
per la storia dello sviluppo, e sempre identificate come «U prima versione».

**Le due versioni di U non sono repliche.** Differiscono per istruzioni
(`u-instructions-0.2` contro `0.3`), per stato della memoria
(`results/rq2/memory/` contro `memory_repair_v3/`) e quindi per contesto
ricevuto. Una sola esecuzione ciascuna: le differenze fra le due sono
osservazioni, non prove che ogni cambiamento dipenda dalla modifica di U, perché
le risposte del modello variano anche a parità di contesto.

**Gli `entry_id` non sono stabili fra le due versioni.** `SC03-M023` indica voci
diverse nelle due prove. Ogni confronto in questa scheda è fatto sul **testo**
delle voci, non sugli identificatori, e le voci citate sono sempre quelle della
versione corretta salvo indicazione esplicita.

---

## 2. Fonti

Tutte lette in sola lettura. I sedici percorsi con le impronte SHA-256 sono in
[`fonti_sc03.json`](fonti_sc03.json).

| Ruolo | File |
|---|---|
| Risposte F e FULL_HISTORY | `results/rq2/generation_dev_sc03.jsonl` |
| Prompt e contesto di F e FULL_HISTORY | `results/rq2/generation_inputs_sc03.jsonl` |
| Retrieval di F (ranghi, punteggi, arresto) | `results/rq2/retrieval_sc03.jsonl` |
| Risposte U corrette | `results/rq2/retrieval_repair_v3/generation_dev_sc03_u.jsonl` |
| Prompt e contesto di U corretta | `results/rq2/retrieval_repair_v3/generation_inputs_sc03_u.jsonl` |
| Retrieval di U corretta | `results/rq2/retrieval_repair_v3/retrieval_sc03_u.jsonl` |
| Stato della memoria U riparata | `results/rq2/memory_repair_v3/scenario_03_state.json` |
| Operazioni ADD/UPDATE/DELETE/NOOP di U | `results/rq2/memory_repair_v3/scenario_03_operations.jsonl` |
| I 41 fatti estratti (comuni a F e U) | `results/rq2/facts/scenario_03_facts.jsonl` |
| Note delle due correzioni | i due `README.md` di `memory_repair_v3/` e `retrieval_repair_v3/` |
| Scenario, oracle e annotazione RQ2 | `data/rq2/scenarios/scenario_03.json`, `data/rq2/annotations/scenario_03_rq2.json` |
| Regola di classificazione | `RACCOLTA_RISULTATI/CRITERI_VALUTAZIONE.md` |
| Criteri e metriche | `EXPERIMENT.md` §9–§11; `RQ2.md` §3–§7, §9.2 |
| Quadro della raccolta | `RACCOLTA_RISULTATI/INVENTARIO.md` |

`results/rq2/annotation_template_sc03.jsonl` è stato letto e lasciato
**intatto**, con i giudizi a `null`.

---

## 3. Quale oracle è usato per quale misura

In SC03, a differenza di SC02, **l'oracle della risposta e la scomposizione RQ2
stanno nello stesso file** (`data/rq2/annotations/scenario_03_rq2.json`): non
c'è un file del pilot da tenere separato. I due riferimenti restano comunque
distinti, e i conteggi non coincidono.

| Domanda | `mandatory_facts` (oracle della risposta) | `required_facts` (scomposizione RQ2) |
|---|---:|---:|
| Q1 | 2 | 2 |
| **Q2** | 2 | **3** |
| **Q3** | 3 | **4** |
| Q4 | 4 | 4 |
| Q5 | 3 | 3 |
| Q6 | 4 | 4 |
| **Q7** | 1 | **0** |

**Regola adottata.**

- **Copertura RQ2** — misurata sui `required_facts`, per singolo `fact_key`, con
  **due verifiche separate**: presenza nel **contenuto del contesto ricevuto** e
  presenza **nella risposta**. Alimenta l'indicatore di recupero (§9.2 di
  `EXPERIMENT.md`) e quindi Retrieval Success e Answer Success. Il dettaglio per
  `fact_key`, con la nota su ogni presenza parziale o desunta, è nel campo
  `rq2_fact_detail` di ogni riga del JSONL.
- **Classe della risposta** — assegnata valutando l'**intera risposta** contro
  `expected_answer`, `mandatory_facts`, `obsolete_information` e
  `accepted_equivalents`, secondo la regola `completezza-supporto-1`. **La
  copertura dei `required_facts` non sostituisce questa valutazione**: su Q2 e su
  Q3 i due riferimenti divergono, ed è registrato in §8.
- **Q7** — nessun `required_fact`: la copertura RQ2 è **non definita**
  (denominatore 0 → `null`), non «1/1». L'astensione è valutata a parte, sugli
  `mandatory_facts` dell'oracle e sulla verifica diretta del corpus (§6).

**Raggiungibilità in RQ2.** Il perimetro è l'intero scenario in tutte e tre le
modalità: 8 messaggi utente per FULL_HISTORY, 41 fatti per F, 35 voci di memoria
(29 attive + 6 in archivio) per U. La raggiungibilità coincide quindi con
`fact_present_in_corpus`: vera per Q1–Q6, **falsa per Q7**. Dipende solo
dall'oracle, non dall'architettura.

---

## 4. Criteri applicati

**Regola di classificazione:** `completezza-supporto-1`
(`RACCOLTA_RISULTATI/CRITERI_VALUTAZIONE.md`, 18 settembre 2026), che legge
insieme `EXPERIMENT.md` §9.3, §9.4 e §10.3. È la stessa regola applicata alla
scheda SC02 r3, ed è esplicitamente un chiarimento operativo **posteriore** alle
prove.

1. Contraddizione con l'oracle, o uso come valida di un'informazione superata →
   **errata**, anche se alcuni fatti richiesti sono presenti.
2. Tutti i fatti obbligatori, nessuna contraddizione → **completa**. Una
   precisazione aggiunta e non in contraddizione si registra a parte con
   `unsupported_claim: true`.
3. Parte dei fatti, almeno uno corretto, senza gli errori del punto 1 →
   **parziale**.
4. **Astensione corretta** secondo la definizione del protocollo.

**Quattro proprietà tenute distinte** in ogni riga:

| Campo | Domanda a cui risponde |
|---|---|
| `rq2_fact_coverage_in_answer` | la risposta contiene i fatti richiesti? |
| `supported_by_original_conversation` | tutto ciò che afferma è sostenuto dalle conversazioni originali? |
| `faithful_to_received_context` | è fedele al contesto che ha ricevuto? |
| `counts_as_complete_and_supported` | entra nel numeratore del Complete Answer Rate? |

Una risposta completa con un'aggiunta non supportata **non entra** nel
numeratore. Una contraddizione o l'uso di informazione obsoleta determina invece
la classe `errata`. Su SC03 le due cose si presentano entrambe, su risposte
diverse.

**Ordine diagnostico della prima causa osservabile** (`EXPERIMENT.md` §11,
esteso da `RQ2.md` §7): raggiungibilità → estrazione → **gestione** → grafo →
retrieval → risposta → benchmark. SC03 è il primo scenario di questa raccolta in
cui l'origine `gestione` — riservata a U e G — risulta effettivamente usata.

**Copertura a zero.** Una risposta che non consegna nessuno dei fatti
obbligatori è classificata `errata` anche quando dichiara l'insufficienza invece
di inventare. È il criterio già applicato nel progetto a SC05-Q5/T. Ricade su
Q4/U e su Q6 in entrambe le modalità, ed è la lettura più severa fra quelle
ammissibili: è registrata in §8 con l'alternativa.

---

## 5. Come è stata verificata la presenza delle evidenze

Ogni risposta è stata letta insieme al **blocco di contesto che ha davvero
ricevuto**, riga per riga, e la presenza di un'evidenza è stata giudicata sul
**contenuto**, non sugli identificatori di provenienza. Il controllo ha prodotto
quattro reperti.

**Un fatto candidato che non è mai diventato memoria — U.** Il fatto
`SC03-F017` («il file LEGGIMI-PAGAMENTO.txt non viene sostituito da nessun'altra
evidenza») esiste nell'estrazione ed è in memoria per F. In U l'operazione
`SC03-OP017` è stata proposta e applicata come **NOOP**: nello stato riparato
non esiste alcuna voce con quel contenuto, né fra le 29 attive né fra le 6 in
archivio. L'informazione non è persa nel retrieval: **non c'è proprio**. Questo
si vede soltanto leggendo lo stato, perché il registro dichiara l'operazione
`applied: true` — un NOOP applicato con successo è comunque un NOOP.

**Una voce attiva che non poteva essere superata — U.** L'operazione
`SC03-OP013` ha inserito il contenuto di `SC03-F013` («l'ipotesi del caso non è
stata cambiata per adesso») con `claim_key` **`stato-ipotesi-malware`**,
distinto da `ipotesi-malware`. Gli UPDATE successivi sulla classificazione
agiscono su `ipotesi-malware` e non possono quindi toccarla: la voce
`SC03-M013` resta **`attivo`** nello stato finale, pur enunciando qualcosa che è
vero solo fino alla sessione 1. Lo stato atteso dell'annotazione non prevede
questa chiave e assorbe lo stesso contenuto in `stato-cifratura`. È il vettore
dell'unico uso di informazione obsoleta osservato su SC03 (§6, Q5/U).

**Un marcatore di stato non è l'enunciato che serve — U.** Su Q3 il contesto di
U contiene `SC03-M004` marcata `superato`, ma non contiene `SC03-M014` («il file
è stato escluso dalle evidenze del caso»), che è in memoria attiva. Il
marcatore `superato` su un sintomo è un'indicazione temporale, non
l'affermazione che il file è uscito dalle evidenze: il `fact_key`
`evidenza-file-riscatto-ritirata` è quindi registrato **non presente nel
contesto**, anche se la risposta lo afferma correttamente per inferenza.

**Frammentazione diversa nelle due architetture.** Il vincolo sul rapporto è
spezzato in F fra `SC03-F040` e `SC03-F041`, e riunito in U in una sola voce
`SC03-M041`; l'esfiltrazione è spezzata in F fra `SC03-F019` (le connessioni) e
`SC03-F020` (i 240 MB), e riunita in U in `SC03-M023`. **Nessuna delle due
differenze ha cambiato un esito**: su Q5 entrambe le meta di F sono state
recuperate, e su Q6 la voce unica di U è rimasta fuori dal contesto (§6).

---

## 6. Tabella dei giudizi proposti

Tabella completa: [`valutazioni_sc03.jsonl`](valutazioni_sc03.jsonl) (21 righe,
con `rq2_fact_detail` per ogni `fact_key`) e
[`valutazioni_sc03.csv`](valutazioni_sc03.csv) per la lettura rapida.

Legenda: **RQ2 ctx / risp** = `fact_key` RQ2 presenti nel contenuto del contesto
/ nella risposta; **Oracle** = `mandatory_facts` coperti dalla risposta;
**Sup.** = supportata dalle conversazioni originali; **C&S** = conta come
completa e supportata.

### F — Fact-based RAG (esecuzione iniziale)

| Dom. | RQ2 ctx | RQ2 risp | Oracle | Classe | Sup. | C&S | Obs. | Non sup. | Prima causa |
|---|:-:|:-:|:-:|---|:-:|:-:|:-:|:-:|---|
| Q1 obiettivo | 2/2 | 2/2 | 2/2 | **completa** | sì | sì | no | no | – |
| Q2 ipotesi superata | **2/3** | 2/3 | 2/2 | **completa** | sì | sì | no | no | – |
| Q3 evidenza ritirata | **3/4** | 2/4 | **2/3** | **parziale** | sì | no | no | no | risposta |
| Q4 attività completate | **1/4** | 1/4 | **1/4** | **parziale** | sì | no | no | no | retrieval |
| Q5 punti aperti | **1/3** | 1/3 | **1/3** | **parziale** | sì | no | no | no | retrieval |
| Q6 catena di evidenze | **0/4** | 0/4 | **0/4** | **errata** | sì | no | no | no | retrieval |
| Q7 informazione assente | n.d. | n.d. | 1/1 | **astensione corretta** | sì | n.a. | no | no | – |

### U — Fact-based con aggiornamenti, versione corretta `u-instructions-0.3`

| Dom. | RQ2 ctx | RQ2 risp | Oracle | Classe | Sup. | C&S | Obs. | Non sup. | Prima causa |
|---|:-:|:-:|:-:|---|:-:|:-:|:-:|:-:|---|
| Q1 obiettivo | 2/2 | 2/2 | 2/2 | **completa** | sì | sì | no | no | – |
| Q2 ipotesi superata | **2/3** | 2/3 | 2/2 | **completa** | sì | sì | no | no | – |
| Q3 evidenza ritirata | **1/4** | 1/4 | **2/3** | **parziale** | sì | no | no | no | **gestione** |
| Q4 attività completate | **0/4** | 0/4 | **0/4** | **errata** | sì | no | no | no | retrieval |
| Q5 punti aperti | **1/3** | 1/3 | **1/3** | **errata** | **no** | no | **sì** | **sì** | **gestione** |
| Q6 catena di evidenze | **0/4** | 0/4 | **0/4** | **errata** | sì | no | no | no | retrieval |
| Q7 informazione assente | n.d. | n.d. | 1/1 | **astensione corretta** | sì | n.a. | no | no | – |

### FULL_HISTORY — controllo diagnostico, fuori confronto (§9)

| Dom. | RQ2 ctx | RQ2 risp | Oracle | Classe | Sup. | C&S | Obs. | Non sup. | Prima causa |
|---|:-:|:-:|:-:|---|:-:|:-:|:-:|:-:|---|
| Q1 | 2/2 | 2/2 | 2/2 | **completa** | sì | sì | no | no | – |
| Q2 | 3/3 | 3/3 | 2/2 | **completa** | sì | sì | no | no | – |
| Q3 | 4/4 | 2/4 | **2/3** | **parziale** | sì | no | no | no | risposta |
| Q4 | 4/4 | 4/4 | 4/4 | **completa** | sì | sì | no | no | – |
| Q5 | 3/3 | 3/3 | 3/3 | **completa** | sì | sì | no | no | – |
| Q6 | 4/4 | 4/4 | 4/4 | **completa** | sì | sì | no | no | – |
| Q7 | n.d. | n.d. | 1/1 | **astensione corretta** | sì | n.a. | no | no | – |

---

## 7. Motivazioni per domanda

Versione integrale nel campo `rationale` di ogni riga del JSONL. Qui i casi che
portano informazione.

### Q1 e Q7 — nessuna differenza fra le modalità

Su **Q1** tutte e tre riportano entrambi gli obiettivi, senza aggiunte: i due
`fact_key` sono nel contesto in tutte e tre le modalità e la domanda non
esercita né la rappresentazione né l'aggiornamento.

Su **Q7** l'assenza è stata **verificata leggendo il corpus**, non dedotta
dall'astensione del modello: nelle quattro sessioni non compaiono le radici
«fornitor», «estern», «forens», «disco», né alcuna analisi forense del disco o
soggetto terzo. Tutte e tre le risposte dichiarano l'insufficienza e nessuna
attribuisce l'analisi forense al laboratorio interno, che pure è nel contesto di
F (`SC03-F023`) e di U (`SC03-M024`) e che nello scenario analizza il campione,
non il disco. Quest'ultimo è precisamente l'errore che l'oracle elenca fra le
informazioni obsolete, ed è evitato da tutte e tre.

### Q2 — classificazione superata: completa in tutte e tre, con una lacuna di copertura

L'oracle chiede l'infostealer come classificazione valida e il ransomware come
ipotesi superata, e vieta due errori: presentare il ransomware come valido, o
l'infostealer come semplice ipotesi dopo l'esito del laboratorio. **Nessuna
delle tre risposte commette né l'uno né l'altro.**

- **F**: «infostealer (confermata)» e «ransomware… superata». Il contesto
  contiene `SC03-F025` e `SC03-F026`, che dicono confermata, ma **non**
  `SC03-F023` (laboratorio) né `SC03-F024` (Kelpie). Copertura RQ2 **2/3**.
- **U**: stessa sostanza, con un elemento in più leggibile nel contesto:
  `SC03-M005` e `SC03-M022` arrivano marcate **`superato`**, e la risposta le
  usa nel verso giusto. `SC03-M024` e `SC03-M025` sono attive in memoria ma
  fuori dal contesto. Copertura RQ2 **2/3**.
- **FULL_HISTORY**: unica a nominare la famiglia Kelpie e il laboratorio.
  Copertura RQ2 **3/3**.

La classificazione `completa` per F e U poggia sulla clausola
`accepted_equivalents` che ammette di omettere il nome della famiglia. La stessa
clausola nomina però anche il laboratorio, che F e U non citano: la lettura
adottata è dichiarata e la sua alternativa è quantificata in §8, caso 1.

### Q3 — evidenza ritirata: tutte e tre parziali, per tre ragioni diverse

L'oracle chiede tre cose: il file non è più un'evidenza, il motivo (residuo
dell'esercitazione di maggio), e che il ritiro non è stato sostituito. **Tutte e
tre le modalità omettono la terza**, e questo è l'unico punto di SC03 in cui
FULL_HISTORY non è completa.

- **F — parziale, origine `risposta`.** `SC03-F017` («non viene sostituito da
  nessun'altra evidenza») **era nel contesto** e la risposta non lo usa.
  L'evidenza c'era: l'omissione nasce nella generazione.
- **U — parziale, origine `gestione`.** L'informazione **non esiste in
  memoria**: `SC03-OP017` è stato applicato come NOOP e non ha prodotto alcuna
  voce. Il motivo arriva inoltre dimezzato, perché `SC03-M016` («non ha alcuna
  relazione con l'incidente») è rango 7 con 0,1744 ed esce per budget; il solo
  `SC03-M015` basta comunque a soddisfare il fatto dell'oracle, che chiede il
  residuo dell'esercitazione. La coda della risposta («l'ipotesi ransomware
  risulta superata») è fuori tema ma vera e sostenuta da `SC03-M005`, marcata
  `superato` nel contesto: non è un'affermazione non supportata.
- **FULL_HISTORY — parziale, origine `risposta`.** `SC03-S2-U1` dice
  letteralmente «Non viene sostituito da nessun'altra evidenza» e la risposta
  la omette lo stesso.

**Stessa classe, tre cause diverse.** È il caso in cui la scheda per `fact_key`
paga: senza di essa le tre righe sarebbero indistinguibili.

### Q4 — attività completate: il fallimento più netto, in entrambe

L'oracle chiede quattro fatti, distribuiti fra la sessione 3 (tre azioni di
contenimento) e la sessione 4 (controllo cloud completato).

- **F — parziale (1/4), origine `retrieval`.** Nel contesto entra solo
  `SC03-F030` (credenziali). `SC03-F028` (isolamento 09:40), `SC03-F029` (blocco
  del dominio), `SC03-F036` e `SC03-F037` (controllo cloud) hanno **tutti
  punteggio 0,0000** — ranghi 33, 34, 39 e 40 su 41 — e sono esclusi dalla
  regola sul punteggio nullo. La risposta elenca inoltre «la classificazione del
  caso non cambia» sotto la voce «Verifiche»: è vero e sostenuto da `SC03-F035`,
  ma non è una delle verifiche del caso. Non è una contraddizione con l'oracle e
  non è un'affermazione non supportata: resta una classificazione impropria
  interna alla risposta, registrata qui e non conteggiata.
- **U — errata (0/4), origine `retrieval`.** La risposta dice che il
  contenimento è stato completato — vero, da `SC03-M028` — ma non nomina nessuna
  delle tre azioni, e dichiara che non risultano verifiche completate. Nel
  contesto non c'era nulla di più: `SC03-M029`, `SC03-M030`, `SC03-M037` e
  `SC03-M038` hanno punteggio 0,0000; `SC03-M031` (credenziali) è rango 8 con
  0,1407 e resta fuori perché la selezione si arresta al rango 7, dove
  `SC03-M013` non entra nei 200 token. `wrong_abstention` è **falso**:
  `EXPERIMENT.md` §9.4 lo definisce solo quando l'evidenza necessaria era stata
  recuperata.
- **FULL_HISTORY — completa (4/4).**

**Il punteggio nullo è il meccanismo dominante su questa domanda.** La domanda
usa le parole «azioni di contenimento» e «verifiche»; i fatti che contengono la
risposta usano «isolato dalla rete», «bloccato sul proxy», «controllo degli
accessi ai servizi cloud». Il sovrapporsi lessicale è nullo, e la regola che
esclude i punteggi nulli li elimina prima del budget. È lo stesso punto già
aperto su SC02 e su SC05.

### Q5 — punti aperti: l'unico uso di informazione obsoleta di SC03

L'oracle chiede tre cose: resta aperta la reinstallazione, il vettore iniziale
non è determinato, il rapporto resta interno fino alla chiusura.

- **F — parziale (1/3), origine `retrieval`.** Il vincolo è riportato per
  intero, perché nel contesto ci sono entrambe le metà (`SC03-F040` e
  `SC03-F041`). Sui punti aperti la risposta **dichiara l'insufficienza invece
  di inventare**: `SC03-F038` (reinstallazione) è rango 18 con 0,0479 e resta
  fuori per budget, `SC03-F039` (vettore) ha punteggio 0,0000. Nessuna
  informazione obsoleta: il controllo cloud non viene indicato fra le attività
  aperte, che è l'errore vietato dall'oracle.
- **U — errata, `obsolete_used: true`, `unsupported_claim: true`, origine
  `gestione`.** Il vincolo è completo e in una sola voce (`SC03-M041`). Ma la
  risposta elenca **quattro «punti aperti» e nessuno lo è**:

  > - Obiettivo del caso: stabilire la classificazione del malware…
  > - Il campione di svhostw.exe è stato inviato al laboratorio interno **(in attesa di risultati)**
  > - I file dell'utente si aprono ancora regolarmente
  > - **L'ipotesi del caso non è stata cambiata per adesso**

  L'ultima voce è `SC03-M013`, vera fino alla sessione 1 e superata nella
  sessione 2: **è un'informazione superata usata come valida**, quindi la classe
  è `errata` per §9.3 e per la regola comune §1. L'inciso «(in attesa di
  risultati)» non è nel contesto — `SC03-M024` dice anzi che il laboratorio ha
  **chiuso** l'analisi, benché non sia in questo contesto — ed è quindi
  un'affermazione non supportata.

  **La risposta è fedele al contesto e non supportata dalle conversazioni**:
  `SC03-M013` le arriva marcata `attivo`, e la politica di lettura dichiara che
  per una domanda sullo stato corrente valgono «soltanto i fatti attivi». Il
  generatore non aveva alcun segnale per scartarla.

- **FULL_HISTORY — completa (3/3).**

*Prima causa osservabile:* **gestione**. Documentata: `SC03-OP013` crea la chiave
`stato-ipotesi-malware`, che nessun UPDATE successivo può superare. *Seconda
causa, distinta*, per l'omissione dei fatti richiesti: `SC03-M039` è rango 12 e
resta fuori per budget, `SC03-M040` ha punteggio 0,0000. *Ipotesi, non
osservazione:* che con `SC03-M013` marcata `superato` la risposta sarebbe stata
diversa non è verificabile senza nuove chiamate.

### Q6 — catena di evidenze: stesso fallimento, e la memoria migliore non aiuta

L'oracle chiede quattro evidenze più l'esito del laboratorio. **F e U si
astengono entrambe, con la stessa sostanza**, e nessuna delle quattro evidenze
era nel contesto.

| | elemento con i 240 MB | rango | punteggio | nel contesto |
|---|---|---:|---:|:-:|
| F | `SC03-F020` (solo i 240 MB) | 17 | 0,0998 | no |
| F | `SC03-F019` (solo le connessioni) | 23 | 0,0472 | no |
| U | `SC03-M023` (connessioni **e** 240 MB in una voce) | 18 | 0,0541 | no |

In memoria **U rappresenta l'esfiltrazione meglio di F**, riunendo in una sola
voce ciò che F tiene in due. Sul contesto questo non produce alcun effetto: la
voce unica resta fuori per budget come le due separate. `SC03-F021` /
`SC03-M021` (nessuna cifratura) e `SC03-F024` / `SC03-M025` (Kelpie) hanno
punteggio 0,0000 in entrambe.

Entrambe **errate** per copertura nulla dei fatti obbligatori; entrambe
descrivono correttamente ciò che hanno ricevuto e **non inventano evidenze**;
`wrong_abstention` falso in entrambe. FULL_HISTORY è **completa (4/4)**.

---

## 8. Riepilogo numerico (provvisorio)

Valori in [`riepilogo_sc03.json`](riepilogo_sc03.json). Ogni cella mostra
**numeratore / denominatore**. I denominatori zero producono `null`, non zero.

### 8.1 Classi e indicatori (N = 7 per modalità)

| | F | U | FULL_HISTORY |
|---|:-:|:-:|:-:|
| completa | 2 | 2 | **5** |
| parziale | **3** | 1 | 1 |
| errata | 1 | **3** | 0 |
| astensione corretta | 1 | 1 | 1 |
| giudizi sospesi | 0 | 0 | 0 |
| **Complete Answer Rate** (complete **e supportate**) | **2/7 = 28,6 %** | **2/7 = 28,6 %** | 5/7 = 71,4 % |
| Informazione obsoleta | 0/7 = 0 % | **1/7 = 14,3 %** | 0/7 = 0 % |
| Affermazioni non supportate | 0/7 = 0 % | **1/7 = 14,3 %** | 0/7 = 0 % |
| Astensioni errate | 0/7 | 0/7 | 0/7 |

Su SC03 **nessuna risposta è `completa` ma non supportata**: le due complete di
F e le due di U sono anche supportate, quindi classe e numeratore coincidono. È
diverso da SC02, dove Q5/F era completa e non supportata.

### 8.2 Metriche di retrieval e astensione

Definizioni da `EXPERIMENT.md` §10, con i denominatori dichiarati. La copertura
usata è quella dei `required_facts` RQ2, verificata sul contenuto.

**Reachability Rate** = domande raggiungibili / N.

| | F | U | FULL_HISTORY |
|---|:-:|:-:|:-:|
| | 6/7 = 85,7 % | 6/7 = 85,7 % | 6/7 = 85,7 % |

Uguale per costruzione: il perimetro è l'intero scenario in tutte e tre.
**Non distingue F da U.**

**Retrieval Success condizionato alla raggiungibilità** = domande con tutti i
`fact_key` RQ2 nel contenuto del contesto / domande raggiungibili. Denominatore
6 (Q1–Q6).

| | F | U | FULL_HISTORY |
|---|:-:|:-:|:-:|
| | **1/6 = 16,7 %** | **1/6 = 16,7 %** | **non applicabile** |

Solo Q1 riceve l'evidenza completa, in entrambe le modalità. **È il dato più
severo di SC03** e riguarda il retrieval, non le architetture di memoria: su 5
delle 6 domande raggiungibili il contesto non conteneva tutto il necessario, con
gli stessi due meccanismi (punteggio nullo e arresto per budget) in entrambe.

Per FULL_HISTORY la metrica **non è applicabile**: non esegue selezione e il file
di retrieval non contiene sue righe. Il dato di contenuto — `fact_key` RQ2
presenti in 6/6 domande raggiungibili — è riportato solo come descrizione.

**Answer Success condizionato al recupero** = complete e supportate con evidenza
completa nel contesto / prove con evidenza completa nel contesto.

| | F | U | FULL_HISTORY |
|---|:-:|:-:|:-:|
| | 1/1 | 1/1 | 5/6 = 83,3 % |

**Su F e U il denominatore è 1.** Il valore non va riportato come «100 %»: dice
soltanto che l'unica domanda con evidenza completa (Q1) ha ricevuto una risposta
completa e supportata. Con un denominatore così piccolo la metrica non separa
utilmente gli errori di risposta da quelli di retrieval, e su SC03 va considerata
non informativa. Per FULL_HISTORY il 5/6 è invece leggibile: con l'evidenza
completa in 6 domande, una (Q3) non produce una risposta completa.

**Correct Abstention Rate** = astensioni corrette / domande non raggiungibili.
Denominatore **1** (solo Q7).

| | F | U | FULL_HISTORY |
|---|:-:|:-:|:-:|
| | 1/1 | 1/1 | 1/1 |

Va letto come «1 domanda su 1»: la percentuale non è informativa.

### 8.3 Sensibilità alle due letture dichiarate

Nessun giudizio è sospeso, ma due letture dell'oracle sono state scelte
esplicitamente. Ecco che cosa cambierebbe l'alternativa.

| Lettura alternativa | Righe toccate | Effetto |
|---|---|---|
| **Q2 strict**: `accepted_equivalents` richiede anche «confermato dal laboratorio», che F e U non citano → Q2/F e Q2/U diventano `parziale` | 2 | Complete Answer Rate: F 2/7 → **1/7**; U 2/7 → **1/7**. Answer Success invariato (Q2 non ha evidenza completa). **Il confronto F/U non cambia: restano pari.** |
| **Copertura zero = `parziale`** anziché `errata`, per le risposte che dichiarano l'insufficienza senza inventare | 3 (Q6/F, Q4/U, Q6/U) | Classi: F errate 1 → 0, parziali 3 → 4; U errate 3 → 1, parziali 1 → 3. **Complete Answer Rate invariato** (2/7 e 2/7), perché nessuna di queste righe era complete-and-supported. Cambia la forma del profilo di U, non il tasso principale. |

Entrambe le alternative lasciano **invariata** la conclusione di §9: F e U hanno
lo stesso Complete Answer Rate su SC03.

### 8.4 Metriche non calcolate

| Metrica | Perché non è qui |
|---|---|
| Tasso di fatti persi o alterati nell'estrazione | Richiederebbe la verifica a mano di tutti e 41 i fatti. Verificati i 20 che servono ai `fact_key`, più `SC03-F013` e `SC03-F017`. Nessun fatto verificato risulta alterato nel contenuto: su SC03 l'estrazione non ha prodotto il tipo di difetto osservato in SC02. |
| Tasso di correttezza delle operazioni ADD/UPDATE/DELETE/NOOP | 42 operazioni, 41 applicate, 1 rifiutata e riproposta con successo. Confrontarle una per una con le 21 `expected_operations` dell'annotazione è una misura di U a sé, non richiesta da questa scheda. I due difetti rilevanti per le risposte (`SC03-OP013`, `SC03-OP017`) sono documentati in §5 come casi singoli. |
| Misure di grafo | Non applicabili: SC03 non ha una modalità G. |
| Copertura delle relazioni obbligatorie | L'annotazione RQ2 di SC03 non dichiara relazioni. |
| Token e latenza | Descrittivi per scelta di `EXPERIMENT.md` §10. |
| Confronti fra scenari | Fuori dall'ambito di questa scheda. |

### 8.5 Costo del contesto (descrittivo, non una metrica)

| | Elementi (media) | Token del contenuto | Sovraccarico | Totale |
|---|---:|---:|---:|---:|
| F | 7,6 | 91,1 | 98,4 | 189,6 |
| U | 6,6 | 86,4 | 98,6 | 185,0 |
| FULL_HISTORY | 8,0 | 481,0 | 56,0 | 537,0 |

F e U stanno entrambe nei 200 token e **spendono più della metà del contesto in
struttura**: 98,4 e 98,6 token di identificatori, provenienza e — per U — stato
temporale. U paga 0,2 token in più di sovraccarico e porta 4,7 token di
contenuto in meno, su un elemento in meno: la marcatura dello stato costa
pochissimo. FULL_HISTORY, con 537 token, è fuori dal budget di quasi tre volte.

---

## 9. Interpretazione del confronto F / U

Vale per **SC03, una sola esecuzione per cella, sette domande, due esecuzioni
diverse messe a confronto**. Non è una conclusione sulle architetture di memoria.

**Il tasso principale è identico: 2/7 per entrambe.** Le stesse due domande (Q1 e
Q2) sono complete e supportate in entrambe; le altre cinque falliscono in
entrambe. Su SC03 **l'aggiornamento della memoria non cambia quante risposte
utili si ottengono.**

**Cambia però la forma del fallimento, e non a favore di U.** F ha 3 parziali e
1 errata; U ha 1 parziale e 3 errate. Le due domande che si spostano sono Q4 (F
consegna 1 fatto su 4, U nessuno) e Q5 (F si astiene sui punti aperti, U ne
elenca quattro sbagliati). **U è l'unica delle due a produrre un'informazione
obsoleta e un'affermazione non supportata**, entrambe su Q5.

**Osservazione documentata: il difetto di Q5/U nasce nella gestione.**
`SC03-OP013` ha inserito «l'ipotesi del caso non è stata cambiata per adesso»
sotto una `claim_key` propria, che nessun aggiornamento successivo poteva
superare; la voce è arrivata al generatore marcata `attivo`. Questo si legge nel
registro delle operazioni e nello stato finale, e non dipende da come ha
risposto il modello. **È l'unico caso in questa raccolta in cui l'origine
`gestione` risulta usata**, e riguarda proprio l'architettura che la gestione
dovrebbe rendere più sicura.

**Osservazione documentata: la gestione perde anche un fatto, in silenzio.**
`SC03-OP017` è un NOOP applicato con successo su `SC03-F017`. Il registro non
segnala nulla di anomalo — `applied: true`, nessun `rejection_reason` — ma in
memoria non resta alcuna voce. Su Q3 questo distingue F da U: in F l'evidenza
era nel contesto e la risposta non l'ha usata (`risposta`); in U non esisteva
(`gestione`). **La classe è la stessa; la causa no.**

**Osservazione documentata: dove U rappresenta meglio, non serve.** U riunisce
in `SC03-M023` ciò che F tiene in `SC03-F019` e `SC03-F020`, e in `SC03-M041` ciò
che F tiene in `SC03-F040` e `SC03-F041`. Sul vincolo del rapporto (Q5) F
recupera comunque entrambe le metà; sull'esfiltrazione (Q6) la voce unica di U
resta fuori dal contesto come le due separate. **Nessun esito cambia.**

**Osservazione documentata: il limite dominante è il retrieval, non la memoria.**
Retrieval Success 1/6 in entrambe. I fatti che contengono la risposta hanno
punteggio **0,0000** su Q4 (quattro fatti), su Q5 (il vettore) e su Q6 (cifratura
e Kelpie), oppure cadono fuori per arresto di budget. Su cinque domande su sei
l'informazione era **conservata e non recuperata**: cambiare la rappresentazione
della memoria non tocca questo punto.

**Spiegazioni ipotizzate, tenute distinte.** Che con `SC03-M013` marcata
`superato` la risposta a Q5 sarebbe stata corretta; che un `claim_key` unico per
la classificazione avrebbe evitato l'errore; che con `SC03-F019`/`SC03-F020` nel
contesto Q6 sarebbe stata completa. Sono letture coerenti con gli artefatti,
**nessuna è stata verificata**: richiederebbero nuove chiamate al modello.

**Che cosa questo non dimostra.**

- Non dimostra che F sia migliore di U, né il contrario. Sette domande, una
  esecuzione per cella, nessuna replica, oracle in bozza.
- **Non è un confronto pulito.** F viene dall'esecuzione iniziale, U da una
  successiva con istruzioni e memoria diverse. Non condividono l'esecuzione, solo
  i fatti candidati, la configurazione e il budget.
- Non dimostra le cause. Le origini indicate sono **prime cause osservabili**
  negli artefatti.
- Non permette di sommare o mediare SC03 con SC02, SC04 o SC05.
- Non dice nulla su T e G, che su SC03 non esistono.

---

## 10. Nota storica: la prima versione di U (fuori dall'aggregazione)

Le prime 7 risposte U, in `results/rq2/generation_dev_sc03.jsonl`, **non entrano
in nessun numero di questa scheda**. Sono riportate qui perché documentano
perché la correzione è stata fatta, e perché il confronto fra le due versioni è
già descritto nel README di `retrieval_repair_v3/`.

Rilettura diretta delle due versioni, senza riusare quelle conclusioni:

| | U prima versione | U corretta | Differenza osservata |
|---|---|---|---|
| Q1 | completa | completa | nessuna |
| Q2 | stessa sostanza | stessa sostanza | nessuna |
| Q3 | il motivo è completo: il contesto ha `SC03-M015` **e** `SC03-M016` | il motivo è dimezzato: `SC03-M016` esce per budget | **peggioramento nel contesto**, senza effetto sulla classe rispetto all'oracle |
| Q4 | stessa risposta di sostanza | stessa risposta di sostanza | nessuna |
| Q5 | si astiene sui punti aperti; vincolo **incompleto** («deve restare interno») | elenca 4 punti aperti sbagliati; vincolo **completo** | **misto**: il vincolo migliora, i punti aperti peggiorano |
| Q6 | si astiene | si astiene | nessuna |
| Q7 | astensione corretta | astensione corretta | nessuna |

**Due precisazioni.** La prima: `SC03-M013` non compariva nel contesto di Q5
nella prima versione, e l'informazione obsoleta non poteva quindi presentarsi —
il peggioramento è reale, ma è osservato su una sola esecuzione. La seconda: gli
`entry_id` non sono confrontabili fra le due versioni, e questo confronto è
fatto sul testo.

**Le due versioni non sono repliche** e non vanno mediate né sommate. Una sola
esecuzione ciascuna: le risposte del modello variano anche a parità di contesto,
quindi nessuna di queste differenze dimostra da sola un effetto della correzione.

---

## 11. Casi aperti

1. **Lettura di `accepted_equivalents` su Q2.** La clausola ammette di omettere
   il nome della famiglia ma nomina «infostealer confermato **dal laboratorio**»;
   F e U dicono «confermata» senza la fonte. Adottata la lettura permissiva,
   perché l'oracle testa la distinzione ipotesi/classificazione confermata e
   quella è rispettata. Effetto dell'alternativa in §8.3: F e U scendono entrambe
   a 1/7, il confronto resta pari. **Va deciso una volta per tutti gli scenari.**
2. **Copertura zero: `errata` o `parziale`?** Q6/F, Q4/U e Q6/U dichiarano
   l'insufficienza senza inventare e consegnano 0 fatti obbligatori. Adottata
   `errata`, come per SC05-Q5/T. È la questione già aperta nel progetto sulla
   «dichiarazione di insufficienza su una domanda a cui il corpus permette di
   rispondere». Effetto dell'alternativa in §8.3: non tocca il tasso principale.
3. **`wrong_abstention` quando l'evidenza non è stata recuperata.** §9.4 lo
   definisce solo quando l'evidenza è stata recuperata, quindi qui è sempre
   falso, anche sulle tre risposte che si astengono su domande rispondibili dal
   corpus. L'indicatore non cattura questi casi. Segnalato, non modificato.
4. **Soglia sul punteggio nullo.** Su SC03 esclude `SC03-F028`, `SC03-F029`,
   `SC03-F036`, `SC03-F037`, `SC03-F039`, `SC03-F021`, `SC03-F024` e i loro
   equivalenti in U, tutti conservati in memoria e tutti contenenti la risposta
   corrente. È lo stesso punto già aperto su SC02 e su SC05, e **su SC03 è il
   meccanismo dominante**.
5. **Valore del budget.** Su Q4/U la selezione si è fermata al rango 7 con
   `SC03-M031` (0,1407) al rango 8; su Q5 in entrambe le modalità il fatto utile
   era ai ranghi 18 e 12. `RQ2.md` §3 dichiara già che il valore 200 va
   verificato dopo l'inclusione del sovraccarico: su SC03, dove il sovraccarico è
   il 52 % del contesto, il caso è più forte che su SC02.
6. **Confrontabilità dei campi di provenienza.** In U il marcatore `superato` su
   una voce non equivale all'enunciato del ritiro (§5, Q3). I campi
   `*_by_provenance` restano un indizio, non una misura di correttezza.
7. **La vista è composita.** F e FULL_HISTORY da un'esecuzione, U da un'altra.
   Va deciso se il protocollo finale rigeneri F e FULL_HISTORY con la memoria
   corretta, oppure se la vista composita resti dichiarata come tale. Finché non
   è deciso, i numeri di §8 non sono un confronto a parità di esecuzione.

Nessuna di queste ambiguità è stata risolta modificando i criteri per adattarli
ai risultati.

---

## 12. FULL_HISTORY — sezione separata

FULL_HISTORY è un **controllo diagnostico** e resta **fuori dal confronto a
parità di budget**, come prescritto da `INVENTARIO.md` §2 e da `RQ2.md` §3.

**Perché non è comparabile.**

1. **Non ha budget.** 537 token contro i 185–190 di F e U: quasi il triplo.
2. **Non ha retrieval.** Non esegue selezione e riceve per costruzione gli otto
   messaggi utente; `retrieval_sc03.jsonl` non contiene sue righe. Il suo
   Retrieval Success è **non applicabile**, non 100 %.
3. **Non scala.** Su uno scenario di otto messaggi l'intera storia entra nel
   contesto. È la condizione che gli altri approcci cercano di approssimare
   quando la storia non ci sta.

**Esito.** 5 complete e supportate su 7, 1 parziale, 0 errate, 1 astensione
corretta, 0 usi di informazione obsoleta, 0 affermazioni non supportate, 0
astensioni errate.

**A che cosa serve, qui.** FULL_HISTORY dispone delle informazioni necessarie per
**sei** delle sette domande: **Q7 richiede astensione**, perché il fatto non è
nel corpus. Su quelle sei, il suo esito stabilisce che le domande sono
rispondibili e che i fallimenti di F e U su Q4, Q5 e Q6 dipendono dal contesto
ricevuto, non da un difetto del benchmark.

- Su **Q4**, **Q5** e **Q6** è l'unica delle tre a essere completa. I fatti
  mancanti a F e U erano conservati: il limite è la selezione.
- Su **Q3** è **parziale**, con tutte e quattro le evidenze nel contesto:
  `SC03-S2-U1` dice letteralmente «Non viene sostituito da nessun'altra
  evidenza» e la risposta la omette. **Questa riga non è attribuibile al
  contesto**, e mostra che una parte dell'omissione osservata su Q3 in F e in U
  può non dipendere dall'architettura.
- Su **Q7** l'astensione è coerente con l'assenza del fatto, ma **non la
  dimostra**: un modello può astenersi anche quando l'informazione c'è.
  L'assenza è stabilita dalla lettura del corpus (§7), e l'astensione di
  FULL_HISTORY è un indizio concorde, non la prova.

**Che cosa non va fatto con questa riga.** Non va messa in classifica con F e U,
non va usata come «limite superiore» senza dichiarare che non ha budget né
retrieval, e il suo 5/7 non va confrontato con il 2/7 di F e di U come se le
condizioni fossero paragonabili. Va inoltre ricordato che **proviene
dall'esecuzione iniziale**, come F e a differenza di U.

---

## 13. File di questa scheda

| File | Contenuto |
|---|---|
| [`valutazioni_sc03.jsonl`](valutazioni_sc03.jsonl) | Tabella strutturata, 21 righe: classe, indicatori, copertura RQ2 per `fact_key` con note su contesto e risposta, copertura dell'oracle, supporto, fedeltà, motivazione, prima causa, contesto ricevuto, origine dell'esecuzione, riferimenti di traccia |
| [`valutazioni_sc03.csv`](valutazioni_sc03.csv) | Stessa tabella, vista compatta |
| [`riepilogo_sc03.json`](riepilogo_sc03.json) | Riepilogo per modalità, con numeratore, denominatore, definizione ed esclusioni di ogni metrica |
| [`fonti_sc03.json`](fonti_sc03.json) | Percorsi e impronte SHA-256 dei sedici file letti |
| `valutazione_sc03.md` | Questo rapporto |

Nessun file esistente del progetto è stato modificato. In particolare
`results/rq2/annotation_template_sc03.jsonl` conserva i giudizi a `null`, e le
due cartelle di correzione restano intatte.

**Non prodotti, per scelta:** grafici; estensione ad altri scenari; conclusioni
generali sulle architetture di memoria.

**Prossimo passo:** far rivedere i 21 giudizi proposti e decidere i casi 1, 2 e 7
di §11. Finché non è fatto, il riepilogo numerico resta provvisorio.
