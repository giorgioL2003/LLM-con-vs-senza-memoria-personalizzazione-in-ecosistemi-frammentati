# SC02 — Lumen Market: valutazione delle 21 risposte RQ2

**Revisione r3 — 18 settembre 2026.** Chiude la sospensione di Q5/F applicando
la [regola comune su completezza e supporto](../CRITERI_VALUTAZIONE.md).
La revisione precedente è conservata in `archivio/r2/`. Le note sono in §0.

**Stato dei giudizi:** **valutazioni assistite proposte dall'assistente, non
approvate.** Nessuna approvazione dello studente, nessuna approvazione del
relatore, protocollo non congelato. Questo vale anche per i giudizi cambiati in
r2 e r3, inclusi quelli su SC02-Q3/F e SC02-Q5/F.

**Natura dei risultati:** **risultati di sviluppo.** Una sola esecuzione per
cella, sette domande per modalità, nessuna replica, oracle e annotazioni ancora
in bozza. Non sono risultati dell'esperimento.

**Stato del riepilogo numerico:** **provvisorio come valutazione assistita di
sviluppo.** Nessun giudizio di classe resta sospeso. Q5/F è completa nel
contenuto richiesto, ma non supportata: non conta nel Complete Answer Rate.

Nessuna chiamata al modello, nessuna nuova generazione, nessuna riesecuzione del
retrieval o della costruzione della memoria. Scenari, oracle, configurazioni,
codice, risposte e prove precedenti non sono stati modificati: gli unici file
aggiornati sono i quattro artefatti di questa scheda. È stato aggiunto il
riferimento comune ai criteri nella cartella della raccolta.

---

## 0. Note di revisione

### r2 → r3: chiusura di Q5/F

La regola `completezza-supporto-1` distingue la classe della risposta dal suo
supporto. Q5/F contiene tutti i fatti richiesti e non contraddice l'oracle:
classe **completa**, con `unsupported_claim: true`. La data aggiunta resta
un errore di estrazione e impedisce di contare la risposta come completa e
supportata. Nessun fatto, contesto o risposta generata è cambiato.

F passa da 2 a **3** risposte nella classe completa e da 1 a **0** sospese.
Complete Answer Rate **2/7**, Retrieval Success **4/6** e Answer Success
**2/4** restano invariati. È un chiarimento operativo introdotto dopo aver
osservato il caso, non un criterio dichiarato prima delle prove.

### Storico r1 → r2

La tabella seguente descrive la revisione precedente; lo stato corrente di
Q5/F è quello della r3 descritto sopra.

| # | Che cosa è cambiato | Perché |
|---|---|---|
| 1 | **SC02-Q5/F: da `completa` a giudizio sospeso.** Registrate separatamente copertura dei fatti, supporto rispetto alla conversazione originale e fedeltà al contesto ricevuto. Esclusa dal numeratore del Complete Answer Rate. | §9.3 definisce «completa» sui soli fatti obbligatori; §10.3 conta le risposte «complete **e supportate**». La data `2026-09-08` non è nel corpus, quindi le due definizioni non danno lo stesso esito. r1 aveva risolto la tensione assegnando `completa` e contando la risposta come successo: era una scelta non sostenuta dai criteri. |
| 2 | **Conteggi dei fatti obbligatori separati per riferimento.** r1 etichettava come «oracle RQ2» conteggi presi dal pilot. Ora ogni misura dichiara la propria fonte, e la copertura RQ2 è registrata per singolo `fact_key`, con presenza nel contesto e nella risposta verificate separatamente. | I due oracle non coincidono: Q2 ha **4** `required_facts` in RQ2 e 3 `mandatory_facts` nel pilot; Q5 ne ha 2 contro 3; Q6 2 contro 3; **Q7 ne ha 0 contro 1**. Nessuno dei due oracle è stato riscritto. |
| 3 | **SC02-Q4/F: evidenza obbligatoria ora NON recuperata.** Il `fact_key` RQ2 richiede che resti da completare **soltanto** il test dell'email; il contesto di F non sostiene l'esclusività. Copertura RQ2 0/1. Retrieval Success di F: da 5/6 a **4/6**; denominatore dell'Answer Success: da 5 a 4. | r1 aveva dato il recupero per riuscito perché il contesto menzionava il test dell'email. La menzione non è il fatto. |
| 4 | **SC02-Q3/F: da giudizio sospeso a `errata` proposta.** | L'oracle del pilot chiede quale verifica sia stata completata, al singolare, con il suo esito. Presentare un test e il suo esito come «due verifiche completate» altera il resoconto dell'attività e contraddice l'oracle ai sensi di §9.3. Il caso non richiede un criterio nuovo, quindi non c'è ragione di lasciarlo sospeso. |
| 5 | **SC02-Q7: copertura RQ2 dichiarata non definita** (0 fatti obbligatori, denominatore 0 → `null`). r1 riportava «1/1», che non corrisponde all'annotazione RQ2. | Non si inventa un fatto recuperato dove l'annotazione non ne dichiara nessuno. L'astensione è giudicata sull'oracle del pilot e sulla lettura diretta del corpus. |
| 6 | **Caso dubbio n. 3 di r1 ritirato.** Riguardava un fatto «non obbligatorio ma decisivo» su Q4/F. | Il controllo sul contenuto mostra che il fatto obbligatorio stesso non era sostenuto: la lacuna nella definizione di §9.2 non si presenta. |
| 7 | **Correzioni di testo.** FULL_HISTORY dispone delle informazioni per **sei** domande, non sette: Q7 richiede astensione. L'assenza dell'informazione su Q7 è verificata leggendo il corpus, non dedotta dall'astensione del modello. Attenuate le affermazioni assolute e le ipotesi controfattuali; osservazioni documentate e spiegazioni ipotizzate sono ora distinte. | r1 trattava l'astensione come prova dell'assenza e formulava alcune spiegazioni come se fossero constatazioni. |

**Effetto complessivo sulle metriche di F:** risposte complete e supportate da
3/7 a **2/7**; errate da 1 a **2**; Retrieval Success da 5/6 a **4/6**; Answer
Success da 3/5 a **2/4**. T e FULL_HISTORY sono invariate.

---

## 1. Fonti

Tutte lette in sola lettura. Impronte SHA-256 in [`fonti_sc02.json`](fonti_sc02.json).

| Ruolo | File |
|---|---|
| Le 21 risposte | `results/rq2/generation_dev_sc02.jsonl` |
| Prompt e contesto realmente ricevuto | `results/rq2/generation_inputs_sc02.jsonl` |
| Traccia del retrieval (ranghi, punteggi, arresto) | `results/rq2/retrieval_sc02.jsonl` |
| Campi automatici e giudizi `null` | `results/rq2/annotation_template_sc02.jsonl` |
| I 23 fatti estratti di F | `results/rq2/facts/scenario_02_facts.jsonl` |
| Uscita grezza dell'estrattore | `results/rq2/facts/scenario_02_extraction_log.json` |
| **Oracle del pilot** (testo atteso, `mandatory_facts`, informazioni obsolete) | `data/scenarios/scenario_02.json` |
| **Scomposizione RQ2** (`required_facts` per `fact_key`) | `data/rq2/annotations/scenario_02_rq2.json` |
| Criteri di classificazione e metriche | `EXPERIMENT.md` §9–§11 |
| Budget, regola di selezione, architetture | `RQ2.md` §3–§7, §9.1 |
| Quadro della raccolta | `RACCOLTA_RISULTATI/INVENTARIO.md` |

### Controllo di composizione

21 righe, `error: null` su tutte, `claude-sonnet-5` ed effort `medium` su tutte.
**7 risposte per T, 7 per F, 7 per FULL_HISTORY**, una per ciascuna domanda
SC02-Q1…SC02-Q7; 21 coppie `(question_id, mode)` distinte. Nessuna riga proviene
dal pilot RQ1, dalle fixture o dalle demo.

Il retrieval ha **14 righe, T e F soltanto**: FULL_HISTORY non esegue selezione.

`results/rq2/annotation_template_sc02.jsonl` resta **intatto**, con i giudizi a
`null`.

---

## 2. Quale oracle è usato per quale misura

I due oracle di SC02 non coincidono nei conteggi. Nessuno dei due è stato
modificato; sono riportati in colonne distinte.

| Domanda | `mandatory_facts` (pilot) | `required_facts` (RQ2) |
|---|---:|---:|
| Q1 | 2 | 2 |
| **Q2** | 3 | **4** |
| Q3 | 2 | 2 |
| Q4 | 1 | 1 (ma con «**soltanto**» nel testo) |
| **Q5** | 3 | **2** |
| **Q6** | 3 | **2** |
| **Q7** | 1 | **0** |

**Regola adottata in questa scheda.**

- **Copertura RQ2** — misurata sui `required_facts` dell'annotazione RQ2, per
  singolo `fact_key`, con **due verifiche separate**: presenza nel **contenuto
  del contesto ricevuto** e presenza **nella risposta**. Alimenta l'indicatore di
  recupero (§9.2 di `EXPERIMENT.md`) e quindi Retrieval Success e Answer Success.
  Il dettaglio per `fact_key` è nel campo `rq2_fact_detail` di ogni riga del
  JSONL.
- **Classe della risposta** — assegnata valutando l'**intera risposta** contro
  l'oracle del **pilot** (`expected_answer`, `mandatory_facts`,
  `obsolete_information`, `accepted_equivalents`), che è l'oracle che descrive
  che cosa la risposta deve dire. **La copertura dei `required_facts` RQ2 non
  sostituisce questa valutazione**: su Q4/F i due riferimenti divergono, ed è
  registrato come caso dubbio n. 4.
- **Q7** — l'annotazione RQ2 non dichiara fatti obbligatori: la copertura RQ2 è
  **non definita** (denominatore 0 → `null`), non «1/1». La classe è data
  sull'oracle del pilot e sulla verifica diretta del corpus (§5).

**Raggiungibilità in RQ2.** In SC02 il perimetro è l'intero scenario per tutte e
tre le modalità (4 messaggi utente per T e FULL_HISTORY, 23 fatti per F). La
raggiungibilità coincide quindi con `fact_present_in_corpus`: vera per Q1–Q6,
**falsa per Q7**. È la raggiungibilità di RQ2 e **non va confusa** con i valori
C0/C1/C2 del pilot, che restano quelli del file dello scenario.

---

## 3. Criteri applicati

Le definizioni di base sono quelle di `EXPERIMENT.md`, scritte prima della
costruzione del dataset. La revisione r3 aggiunge un chiarimento operativo
esplicito, successivo alle prove: [completezza e supporto](../CRITERI_VALUTAZIONE.md).
Il documento originale non è stato riscritto. Una classe completa può avere
un'aggiunta non supportata, ma non conta come successo completo e supportato.

**Classi (§9.3).** *completa:* tutti i fatti obbligatori, nessuna contraddizione.
*parziale:* almeno un fatto corretto, ma omette parte della risposta richiesta.
*errata:* contraddice l'oracle, usa come valida un'informazione obsoleta, oppure
non risponde. *astensione corretta:* dichiara l'indisponibilità quando le
evidenze obbligatorie non sono accessibili.

**Indicatori separati (§9.4).** `obsolete_used`, `unsupported_claim`
(informazione inventata: un fatto non sostenuto dalle evidenze accessibili),
`wrong_abstention`.

**Tre proprietà tenute distinte, dopo r2.** Per ogni risposta sono registrate
separatamente:

| Campo | Domanda a cui risponde |
|---|---|
| `rq2_fact_coverage_in_answer` | la risposta contiene i fatti richiesti? |
| `supported_by_original_conversation` | tutto ciò che afferma è sostenuto dal corpus originale? |
| `faithful_to_received_context` | la risposta è fedele al contesto che ha ricevuto? |
| `counts_as_complete_and_supported` | rientra nel numeratore del Complete Answer Rate (§10.3)? |

Le tre proprietà **possono divergere**: SC02-Q5/F copre i fatti ed è fedele al
contesto, ma non è supportata dal corpus; SC02-Q4/F è fedele al contesto e non è
supportata dal corpus.

**Ordine diagnostico della prima causa osservabile (§11, esteso da `RQ2.md` §7).**
raggiungibilità → estrazione → gestione → grafo → retrieval → risposta →
benchmark. Per F le origini `gestione` e `grafo` non sono applicabili.

---

## 4. Come è stata verificata la presenza delle evidenze

Ogni risposta è stata letta insieme al **blocco di contesto che ha davvero
ricevuto**, riga per riga, e la presenza di un'evidenza è stata giudicata sul
**contenuto** delle righe, non sugli identificatori di provenienza. Il controllo
ha prodotto tre reperti.

**Presenza per provenienza senza il fatto richiesto — SC02-Q4/F.** Il `fact_key`
RQ2 è: «resta da completare **soltanto** il test dell'email di recupero
consegnata in ritardo». Il contesto di F contiene cinque fatti la cui provenienza
copre `SC02-S4-U1`, e il campo automatico `evidence_provenance_complete` vale
`true`. Ma nessuna riga sostiene l'esclusività:

> `[SC02-F021]` Il test dell'email di recupero consegnata in ritardo **non è
> ancora stato completato.**
> `[SC02-F017]` **Rimane da verificare** che il collegamento aperto dall'app
> mobile riporti correttamente alla schermata di accesso.

`SC02-F021` dice che quel test è aperto, non che sia l'unico; `SC02-F017`
afferma il contrario dell'esclusività. **Copertura RQ2 0/1: l'evidenza
obbligatoria non è stata recuperata.** La menzione del test dell'email non è il
fatto richiesto.

**Falso positivo di conservazione — SC02-F022.** Il fatto dichiara
`provenance_valid: true` e cita correttamente `SC02-S4-U1`, ma il suo testo è «La
riunione di verifica del rilascio è fissata per **martedì 2026-09-08** alle
11:30». Il messaggio sorgente dice soltanto «martedì alle 11:30». La data è
introdotta dall'estrattore — è visibile nella sua uscita grezza in
`scenario_02_extraction_log.json` — ed è per giunta coerente (il 2026-09-08 è
davvero un martedì), il che la rende più difficile da notare. Il controllo
automatico di provenienza verifica l'identificatore, non il testo, e non poteva
rilevarla.

**Un caso che sembrava una perdita e non lo è — SC02-F018.** Il fatto dice «dopo
il limite di validità stabilito nella sessione precedente», senza i 15 minuti.
Ma il messaggio sorgente `SC02-S3-U1` è **già formulato così**, perché SC02-Q6 è
per costruzione la domanda di collegamento tra sessioni. L'estrazione qui è
fedele, e l'origine dell'errore su Q6 resta il retrieval (§5).

---

## 5. Tabella dei giudizi proposti

Tabella strutturata completa: [`valutazioni_sc02.jsonl`](valutazioni_sc02.jsonl)
(21 righe, con il dettaglio per `fact_key` in `rq2_fact_detail`) e
[`valutazioni_sc02.csv`](valutazioni_sc02.csv) per la lettura rapida.

Legenda: **RQ2 ctx** = `fact_key` RQ2 presenti nel contenuto del contesto;
**RQ2 risp** = presenti nella risposta; **Pilot** = `mandatory_facts` del pilot
coperti dalla risposta; **Sup.** = tutto ciò che la risposta afferma è sostenuto
dalla conversazione originale; **C&S** = conta come «completa e supportata» nel
Complete Answer Rate (§10.3).

### T — Turn-level RAG

| Dom. | RQ2 ctx | RQ2 risp | Pilot | Classe | Sup. | C&S | Obs. | Non sup. | Prima causa |
|---|:-:|:-:|:-:|---|:-:|:-:|:-:|:-:|---|
| Q1 | 2/2 | 2/2 | 2/2 | **completa** | sì | sì | no | no | – |
| Q2 | 4/4 | 4/4 | 3/3 | **completa** | sì | sì | no | no | – |
| Q3 | 2/2 | 2/2 | 2/2 | **completa** | sì | sì | no | no | – |
| Q4 | 1/1 | 1/1 | 1/1 | **completa** | sì | sì | no | no | – |
| Q5 | 2/2 | 2/2 | 3/3 | **completa** | sì | sì | no | no | – |
| Q6 | **1/2** | 1/2 | 1/3 | **parziale** | sì | no | no | no | retrieval |
| Q7 | n.d. | n.d. | 1/1 | **astensione corretta** | sì | n.a. | no | no | – |

### F — Fact-based RAG

| Dom. | RQ2 ctx | RQ2 risp | Pilot | Classe | Sup. | C&S | Obs. | Non sup. | Prima causa |
|---|:-:|:-:|:-:|---|:-:|:-:|:-:|:-:|---|
| Q1 | 2/2 | 2/2 | 2/2 | **completa** | sì | sì | no | no | – |
| Q2 | 4/4 | 4/4 | 3/3 | **completa** | sì | sì | no | no | – |
| Q3 | 2/2 | 2/2 | 2/2 | **errata** | **no** | no | no | **sì** | risposta |
| Q4 | **0/1** | 0/1 | 1/1 | **errata** | **no** | no | **sì** | no | retrieval |
| Q5 | 2/2 | 2/2 | 3/3 | **completa** | **no** | **no** | no | **sì** | estrazione |
| Q6 | **1/2** | 1/2 | 1/3 | **parziale** | sì | no | no | no | retrieval |
| Q7 | n.d. | n.d. | 1/1 | **astensione corretta** | sì | n.a. | no | no | – |

### FULL_HISTORY — controllo diagnostico, fuori confronto (§9)

| Dom. | RQ2 ctx | RQ2 risp | Pilot | Classe | Sup. | C&S | Obs. | Non sup. | Prima causa |
|---|:-:|:-:|:-:|---|:-:|:-:|:-:|:-:|---|
| Q1 | 2/2 | 2/2 | 2/2 | **completa** | sì | sì | no | no | – |
| Q2 | 4/4 | 4/4 | 3/3 | **completa** | sì | sì | no | no | – |
| Q3 | 2/2 | 2/2 | 2/2 | **completa** | sì | sì | no | no | – |
| Q4 | 1/1 | 1/1 | 1/1 | **completa** | sì | sì | no | no | – |
| Q5 | 2/2 | 2/2 | 3/3 | **completa** | sì | sì | no | no | – |
| Q6 | 2/2 | 2/2 | 3/3 | **completa** | sì | sì | no | no | – |
| Q7 | n.d. | n.d. | 1/1 | **astensione corretta** | sì | n.a. | no | no | – |

---

## 6. Motivazioni per domanda

Versione integrale nel campo `rationale` di ogni riga del JSONL. Qui i casi che
portano informazione.

### Le domande senza differenze fra le modalità

**Q1**, **Q2** e **Q7** danno lo stesso esito nelle tre modalità. Su Q2 tutte e
tre coprono i quattro `fact_key` RQ2 e i tre fatti del pilot, e nessuna presenta
il CAPTCHA come intervento ancora scelto. Su Q7 nessuna inventa una persona o un
ruolo. **Su queste domande la rappresentazione della memoria non produce
differenze osservabili.**

Su **Q2/F** la risposta cita gli identificatori dei fatti (`SC02-F012`,
`SC02-F013`, …): differenza di forma, non di contenuto, senza effetto sulla
classe.

### Q7 — come è stata verificata l'assenza

L'oracle del pilot dichiara `fact_present_in_corpus: false`, e l'annotazione RQ2
non elenca fatti obbligatori. **L'assenza è stata verificata leggendo il
corpus**, non dedotta dall'astensione del modello: nei quattro messaggi utente e
nei quattro messaggi dell'assistente non compare alcuna persona o ruolo
incaricato di approvare il rilascio. L'unica occorrenza della radice «autorizz»
è «cambio di password non autorizzato» in `SC02-S1-U1`, che riguarda l'incidente.
Le tre astensioni sono quindi corrette, ma **è la lettura del corpus a
stabilirlo**: un modello che si astiene può farlo anche quando l'informazione
c'è.

### Q3/F — «due verifiche completate»: errata (proposta)

*Oracle del pilot:* «Quale verifica è stata completata nell'ultima sessione e con
quale esito?» — risposta attesa: **un** test, il collegamento mobile, con il suo
esito.

Il contesto di F contiene entrambi i `fact_key` RQ2, con contenuto corretto e
selezionati (ranghi 2 e 6). La risposta li riporta entrambi, ma li presenta come
**«due verifiche completate»**, elencando l'esito del test come se fosse una
seconda verifica.

**Classe proposta: errata.** La domanda chiede quale verifica sia stata
completata, al singolare; il resoconto dell'attività risulta alterato, e §9.3
classifica come errata una risposta che contraddice l'oracle. La contraddizione
non riguarda i singoli fatti, che sono corretti, ma il resoconto che ne viene
costruito. `unsupported_claim: true`: la seconda verifica non esiste in nessuna
evidenza accessibile. **Giudizio proposto dall'assistente, non approvato.**

*Prima causa osservabile:* **risposta**. I fatti sono nel contesto con contenuto
corretto, quindi l'ordine diagnostico si ferma qui. La frammentazione di un
messaggio in due voci prive di legame esplicito è una **condizione osservata che
accompagna l'errore**; non è stata dimostrata come causa, e stabilirlo
richiederebbe nuove chiamate al modello.

### Q4/F — informazione obsoleta, con evidenza non recuperata

*Oracle del pilot:* resta da completare il test dell'email di recupero
consegnata in ritardo. *Informazione obsoleta vietata:* includere il test mobile
fra le attività ancora aperte. *`fact_key` RQ2:* «resta da completare
**soltanto** il test dell'email…».

- **T** (contesto: `SC02-S4-U1`, `SC02-S3-U1`) riceve l'esclusività alla lettera
  e indica una sola verifica aperta. **Completa.**
- **FULL_HISTORY** idem. **Completa.**
- **F** risponde: «Rimangono da completare **due verifiche**: 1. il test
  dell'email… 2. la verifica che il collegamento dall'app mobile riporti
  correttamente alla schermata di accesso.» Il secondo punto è l'informazione
  obsoleta vietata. **Errata**, `obsolete_used: true`, copertura RQ2 **0/1**,
  evidenza obbligatoria **non recuperata**.

*Prima causa osservabile:* **retrieval**. La diagnosi e la definizione della
metrica coincidono, ma restano cose distinte: la metrica registra che
l'esclusività non era nel contesto; la diagnosi indica perché.

| Fatto | Contenuto | Rango | Punteggio | Nel contesto |
|---|---|---:|---:|:-:|
| `SC02-F017` | «rimane da verificare il collegamento mobile» (superato in S4) | 2 | 0,2477 | **sì** |
| `SC02-F019` | «il test del collegamento mobile è stato completato» | 22 | **0,0000** | no |
| `SC02-F020` | «l'utente viene riportato alla schermata di accesso» | 23 | **0,0000** | no |

I due fatti che superano `SC02-F017` sono **conservati in memoria** ma hanno
punteggio nullo e sono esclusi dalla regola di selezione. È la stessa soglia sul
punteggio nullo già aperta su SC05.

Accanto a questo si osserva una proprietà dell'architettura, documentata in
`RQ2.md` §4: **F non applica UPDATE**, quindi in memoria il fatto superato resta
attivo accanto a quello nuovo, e nel contesto nulla lo qualifica come superato.
Che cosa sarebbe successo con `SC02-F019` nel contesto **non è osservabile qui**:
resta un'ipotesi, verificabile solo con altre chiamate.

### Q5/F — completa nel contenuto, con aggiunta non supportata

*Oracle del pilot:* martedì, ore 11:30, risultato del test dell'email ritardata.
*`fact_key` RQ2:* `riunione-data-ora`, `riunione-contenuto`.

| Proprietà | Esito |
|---|---|
| Copertura dei fatti richiesti | RQ2 **2/2**, pilot **3/3** |
| Fedeltà al contesto ricevuto | **sì** — la risposta ripete `SC02-F022` |
| Supporto rispetto alla conversazione originale | **no** — «2026-09-08» non compare in `SC02-S4-U1` né altrove nel corpus |

**Classe: completa, con `unsupported_claim: true`.** La regola comune
`completezza-supporto-1` applica §9.3 alla completezza dei fatti richiesti e
all'assenza di contraddizioni, e §10.3 al successo completo e supportato.
La data non è verificabile nelle conversazioni; questo non equivale a
aver dimostrato che sia falsa. L'aggiunta resta un errore segnalato separatamente.

La risposta è esclusa dal numeratore del Complete Answer Rate perché non è
interamente supportata. F ha quindi **3 risposte nella classe completa**, ma
**2/7 risposte complete e supportate**. La sospensione di r2 è chiusa.

*Prima causa osservabile:* **estrazione**. La data è introdotta in `SC02-F022`,
registrato con `provenance_valid: true`.

### Q6 — dove T e F falliscono allo stesso modo, per cause diverse

*`fact_key` RQ2:* limite di 15 minuti; identificazione del test pendente. *Oracle
del pilot:* rifiuto del link oltre il limite, limite di 15 minuti, collegamento
con il test pendente.

- **T — parziale, RQ2 1/2, pilot 1/3, origine retrieval.** Collega il test
  pendente all'email consegnata oltre il limite, non enuncia il rifiuto del link
  e **dichiara esplicitamente** di non conoscere il valore del limite.
  `SC02-S2-U1` è rango 4 con punteggio 0,0523: la selezione si è fermata al rango
  3, dove `SC02-S1-U1` (86 token) non entrava nei 200 disponibili, e la regola
  impone di fermarsi al primo elemento che non entra. Il messaggio con i 15
  minuti aveva punteggio non nullo: è stato escluso dal budget, non dal ranking.
- **F — parziale, RQ2 1/2, pilot 1/3, origine retrieval.** Stesso esito, causa
  diversa: `SC02-F013` («i token di recupero devono scadere dopo 15 minuti») è
  **conservato in memoria** ma ha punteggio **0,0000** (rango 21) ed è escluso
  dalla regola sul punteggio nullo. A differenza di T, la risposta **non segnala**
  che il valore manca.
- **FULL_HISTORY — completa, RQ2 2/2, pilot 3/3.** Unica delle tre a enunciare
  anche il rifiuto del link e il limite.

`wrong_abstention` è **falso** per T e per F: §9.4 definisce l'astensione errata
solo quando l'evidenza necessaria è stata recuperata, e qui non lo era.

Questa domanda era già classificata `partial` nel pilot in C2, con gli stessi
fatti mancanti. La coincidenza è un controllo di coerenza dei criteri, non una
replica: sono esecuzioni e architetture diverse.

---

## 7. Riepilogo numerico (provvisorio)

Valori in [`riepilogo_sc02.json`](riepilogo_sc02.json). Ogni cella mostra
**numeratore / denominatore**. I denominatori zero producono `null`, non zero.

### 7.1 Classi e indicatori, per modalità (N = 7 ciascuna)

| | T | F | FULL_HISTORY |
|---|:-:|:-:|:-:|
| completa (classe, supporto separato) | **5** | **3** | 6 |
| parziale | 1 | 1 | 0 |
| errata | 0 | **2** | 0 |
| astensione corretta | 1 | 1 | 1 |
| **giudizi sospesi** | 0 | **0** | 0 |
| **Complete Answer Rate** (complete **e supportate**) | **5/7 = 71,4 %** | **2/7 = 28,6 %** | 6/7 = 85,7 % |
| Informazione obsoleta | 0/7 = 0 % | **1/7 = 14,3 %** | 0/7 = 0 % |
| Affermazioni non supportate | 0/7 = 0 % | **2/7 = 28,6 %** | 0/7 = 0 % |
| Astensioni errate | 0/7 | 0/7 | 0/7 |

**Sul Complete Answer Rate di F.** Il numeratore 2 comprende Q1 e Q2.
Q5 è nella classe completa ma aggiunge una data non supportata, quindi è
esclusa dal successo completo e supportato. Q3 e Q4 sono errate, Q6 è parziale
e Q7 è un'astensione corretta. Non ci sono classi sospese.

La distribuzione di F è **3 complete + 1 parziale + 2 errate + 1 astensione
corretta = 7**. Il conteggio della classe completa non va confuso con il
numeratore della metrica principale. I risultati restano di sviluppo, con
valutazioni assistite.

### 7.2 Metriche di retrieval e astensione

Definizioni da `EXPERIMENT.md` §10, con i denominatori dichiarati. La copertura
usata è quella dei `required_facts` **RQ2**, verificata sul contenuto.

**Reachability Rate** = domande raggiungibili / N.

| | T | F | FULL_HISTORY |
|---|:-:|:-:|:-:|
| Reachability Rate | 6/7 = 85,7 % | 6/7 = 85,7 % | 6/7 = 85,7 % |

Uguale per costruzione — il perimetro è l'intero scenario in tutte e tre le
modalità — quindi **non è una proprietà dell'architettura** e non distingue T da F.

**Retrieval Success condizionato alla raggiungibilità** = domande con tutti i
`fact_key` RQ2 presenti **nel contenuto** del contesto / domande raggiungibili.
Denominatore 6 (Q1–Q6); Q7 esclusa perché irraggiungibile.

| | T | F | FULL_HISTORY |
|---|:-:|:-:|:-:|
| Retrieval Success | **5/6 = 83,3 %** | **4/6 = 66,7 %** | **non applicabile** |

T fallisce sulla sola Q6 (budget); F su Q6 (punteggio nullo) e su Q4
(esclusività assente dal contesto). Per FULL_HISTORY la metrica **non è
applicabile**: non c'è selezione, e il file di retrieval non contiene righe
FULL_HISTORY. Registrarla come 6/6 misurerebbe la definizione della modalità, non
un retriever. Il dato di contenuto — `fact_key` RQ2 presenti in 6/6 domande
raggiungibili — è riportato solo come descrizione.

**Answer Success condizionato al recupero** = risposte complete e supportate /
domande con tutti i `fact_key` RQ2 nel contesto.

| | T | F | FULL_HISTORY |
|---|:-:|:-:|:-:|
| Answer Success | **5/5 = 100 %** | **2/4 = 50 %** | 6/6 = 100 % |

Denominatore di F: Q1, Q2, Q3, Q5 (Q4 e Q6 escluse perché l'evidenza non è stata
recuperata). Numeratore: Q1 e Q2. Q5 è completa nel contenuto ma non supportata,
quindi non entra nel numeratore. **Tra le prove con tutti i fatti RQ2 nel
contesto, T produce risposte complete e supportate in 5/5 casi e F in 2/4.**

**Correct Abstention Rate** = astensioni corrette / domande non raggiungibili.
Denominatore **1** (solo Q7) in tutte e tre le modalità.

| | T | F | FULL_HISTORY |
|---|:-:|:-:|:-:|
| Correct Abstention | 1/1 | 1/1 | 1/1 |

**Su un denominatore di 1 la percentuale non è informativa** e non va riportata
senza il denominatore accanto.

### 7.3 Metriche non calcolate

| Metrica | Perché non è qui |
|---|---|
| Misure di estrazione (tasso di fatti persi o alterati) | Richiedono la verifica a mano di tutti e 23 i fatti contro i quattro messaggi. Verificati qui i 12 che servono ai fatti obbligatori, più `SC02-F017`. Il difetto trovato (`SC02-F022`) è riportato come caso singolo, non come tasso. |
| Misure di aggiornamento (ADD/UPDATE/DELETE/NOOP) | Non applicabili: SC02 non ha una modalità U, e F non esegue operazioni di aggiornamento. |
| Misure di grafo | Non applicabili: SC02 non ha una modalità G. |
| Copertura delle relazioni obbligatorie | L'annotazione RQ2 di SC02 non dichiara relazioni: `required_relations` è vuoto in tutte e 21 le righe del template. |
| Token e latenza | Descrittivi per scelta di `EXPERIMENT.md` §10. |
| Confronti fra scenari | Fuori dall'ambito di questa scheda. |

### 7.4 Costo del contesto (descrittivo, non una metrica)

| | Elementi (media) | Token del contenuto | Sovraccarico strutturale | Totale |
|---|---:|---:|---:|---:|
| T | 2,0 | 145,6 | 14,0 | 159,6 |
| F | 6,4 | 102,4 | 83,6 | 186,0 |
| FULL_HISTORY | 4,0 | 291,0 | 28,0 | 319,0 |

T e F stanno entrambe nei 200 token. **F impiega il 45 % del contesto che
costruisce** (83,6 token su 186,0) in identificatori e provenienza, e porta 43
token di contenuto in meno di T. FULL_HISTORY, con 319 token, è fuori dal budget.

---

## 8. Casi dubbi e decisioni metodologiche aperte

1. **SC02-Q5/F — caso risolto nella r3.** Classe completa con aggiunta non
   supportata, esclusa dal Complete Answer Rate. La regola comune è in
   [CRITERI_VALUTAZIONE.md](../CRITERI_VALUTAZIONE.md) e va applicata
   esplicitamente nelle successive revisioni, conservando le versioni precedenti.
2. **`obsolete_used` e classe `errata`.** Su SC02-Q4/F le due cose coincidono,
   quindi la questione già aperta nell'inventario (§8.3, il caso SC05-Q4/T
   `parziale` con `obsolete_used: true`) non si manifesta qui. **SC02 non la
   risolve** e non va usato come precedente in un verso o nell'altro.
3. **Alterazione del resoconto a fatti corretti — SC02-Q3/F.** Il giudizio
   proposto è `errata`, ma il criterio §9.3 parla di contraddizione con l'oracle
   senza dire esplicitamente se un'aggregazione errata di fatti singolarmente
   corretti vi rientri. La lettura adottata va confermata in revisione.
4. **Divergenza fra i due oracle su Q4.** Il `fact_key` RQ2 contiene
   l'esclusività («soltanto»), il `mandatory_facts` del pilot no. Sulla stessa
   risposta di F la copertura RQ2 è 0/1 e quella del pilot 1/1. Registrato,
   **non risolto**: i due oracle non sono stati riscritti per farli coincidere.
   Va deciso quale governi l'indicatore di recupero prima di consolidare le
   metriche.
5. **Soglia sul punteggio nullo.** Su SC02-Q4/F e SC02-Q6/F ha escluso fatti
   conservati in memoria che contenevano la risposta corrente (`SC02-F019`,
   `SC02-F020`, `SC02-F013`, tutti a 0,0000). È lo stesso punto già aperto su SC05.
6. **Valore del budget.** Su SC02-Q6/T la selezione si è fermata per budget con il
   messaggio utile al rango 4. `RQ2.md` §3 dichiara già che il valore 200 va
   verificato; SC02 fornisce un caso concreto.
7. **Confrontabilità dei campi di provenienza fra T e F.** In T l'unità recuperata
   è il messaggio sorgente, quindi provenienza e contenuto coincidono per
   costruzione. In F non coincidono, e su Q4 il campo automatico
   `evidence_provenance_complete` vale `true` mentre il fatto richiesto non c'è.
   **I numeri di provenienza di T e di F non sono confrontabili** e non vanno
   messi nella stessa colonna senza questa avvertenza.

La r3 documenta il chiarimento su completezza e supporto. Gli altri punti
restano annotati per la revisione complessiva; non richiedono di cambiare
a posteriori le risposte, gli oracle o le configurazioni delle prove.

---

## 9. Interpretazione del confronto T / F

Vale per **SC02, una sola esecuzione, sette domande**. Non è una conclusione
sulle architetture di memoria.

**Dove non si distinguono.** Su 4 domande su 7 — Q1, Q2, Q6, Q7 — T e F danno lo
stesso esito. Su Q6 falliscono entrambe, e nessuna delle due porta i 15 minuti
nel contesto. La differenza si gioca su **tre domande**, ed è su questa base
ristretta che poggia il resto della sezione.

**Dove F perde — osservazione documentata.** Su Q3, Q4 e Q5 F non produce una
risposta completa e supportata, mentre T sì. Sono documentati negli artefatti: il
contesto ricevuto riga per riga, i ranghi e i punteggi del retrieval, il testo
dei fatti estratti e l'uscita grezza dell'estrattore. Le tre origini sono
diverse — risposta, retrieval, estrazione — e questo è il dato più informativo:
**i tre modi in cui F fallisce su SC02 non hanno una causa comune.**

**Su Q4, una proprietà dell'architettura, osservata.** `RQ2.md` §4 documenta che
F non applica UPDATE; negli artefatti si vede che `SC02-F017`, superato nella
sessione 4, resta attivo e viene selezionato a rango 2, mentre i due fatti che lo
superano hanno punteggio nullo. Questo è osservato.

**Un'ipotesi, non un'osservazione.** Che il contesto sarebbe rimasto ambiguo
anche con `SC02-F019` dentro, perché nulla vi qualifica `SC02-F017` come
superato, è una **lettura plausibile della struttura del contesto**, non un
risultato: non è stata eseguita alcuna prova con quel contesto. Allo stesso modo,
che T su Q4 sia stata protetta dal fatto che `SC02-S4-U1` contiene sia lo stato
aggiornato sia ciò che lo aggiorna è una spiegazione coerente con il testo del
messaggio, **non una proprietà dimostrata** di T.

**Confronto con SC05, con cautela.** Su SC05 l'uso di informazione obsoleta si è
presentato in T e non in U/GER; su SC02 si presenta in F e non in T. Le due
osservazioni non si contraddicono e **suggeriscono** — senza dimostrarlo — che
su questi scenari l'esito dipenda anche da dove cade il confine fra i messaggi
rispetto a dove cade l'aggiornamento. Verificarlo richiederebbe scenari costruiti
apposta per variare quel confine.

**Un rischio strutturale di F, con il suo limite.** La data aggiunta in
`SC02-F022` entra in memoria prima che il retrieval e la generazione intervengano,
e le fasi successive lavorano su quel testo: nessuna di esse, **come sono
implementate oggi**, confronta il testo del fatto con il messaggio sorgente, e il
controllo automatico di provenienza verifica solo l'identificatore. Non è un
limite di principio: un controllo di contenuto in fase di estrazione lo
intercetterebbe. T non espone questa superficie, perché conserva il messaggio
originale — **questo sì è una conseguenza diretta della sua definizione**, non un
esito contingente.

**Il costo, che F paga sempre.** F impiega 83,6 token di sovraccarico contro i 14
di T, cioè il 45 % del contesto che costruisce, e a parità di 200 token porta
meno contenuto. Su SC02 questo costo **non è compensato** da alcun vantaggio
osservabile: non c'è una domanda in cui F superi T.

**Che cosa questo non dimostra.**

- Non dimostra che T sia migliore di F. Sette domande, una esecuzione, nessuna
  replica, oracle non approvato, valutazioni assistite, una differenza su tre
  domande.
- Non dimostra le cause. Le origini indicate sono **prime cause osservabili**
  negli artefatti, non cause dimostrate.
- Non permette di sommare o mediare SC02 con SC03, SC04 o SC05.
- Non dice nulla su U e G, che su SC02 non esistono.

---

## 10. FULL_HISTORY — sezione separata

FULL_HISTORY è un **controllo diagnostico** e resta **fuori dal confronto a
parità di budget**, come prescritto da `INVENTARIO.md` §2 e da `RQ2.md` §3.

**Perché non è comparabile.**

1. **Non ha budget.** 319 token contro i 146–198 di T e F.
2. **Non ha retrieval.** Non esegue selezione: riceve i quattro messaggi utente
   per costruzione, e il file `retrieval_sc02.jsonl` non contiene sue righe. Il
   suo Retrieval Success è **non applicabile**, non 100 %.
3. **Non scala.** Su uno scenario di quattro messaggi l'intera storia entra nel
   contesto. È la condizione che gli altri approcci cercano di approssimare
   quando la storia non ci sta, e SC02 è troppo piccolo perché il problema si
   manifesti.

**Esito.** 6 complete e supportate su 7, 1 astensione corretta, 0 parziali, 0
errate, 0 usi di informazione obsoleta, 0 affermazioni non supportate, 0
astensioni errate.

**A che cosa serve, qui.** FULL_HISTORY dispone delle informazioni necessarie per
**sei** delle sette domande: **Q7 richiede astensione**, perché il fatto non è
nel corpus. Su quelle sei, il suo esito stabilisce che le domande sono
rispondibili dal corpus, e quindi che i fallimenti di T e F su Q4 e Q6 dipendono
dal contesto ricevuto, non da un difetto del benchmark.

- Su **Q6** è l'unica delle tre a coprire tutti i fatti richiesti. Il fallimento
  parziale di T e F su Q6 dipende dunque dalla selezione, non dalla domanda.
- Su **Q4** la sua risposta corretta conferma che `SC02-S4-U1` contiene
  l'esclusività che il contesto di F non aveva.
- Su **Q7** l'astensione è coerente con l'assenza del fatto, ma **non la
  dimostra**: un modello può astenersi anche quando l'informazione c'è. L'assenza
  è stabilita dalla lettura del corpus (§6), e l'astensione di FULL_HISTORY è un
  indizio concorde, non la prova.

**Che cosa non va fatto con questa riga.** Non va messa in classifica con T e F,
non va usata come «limite superiore» senza dichiarare che non ha budget né
retrieval, e il suo 6/7 non va confrontato con il 5/7 di T come se le due
condizioni fossero paragonabili.

---

## 11. File di questa scheda

| File | Contenuto |
|---|---|
| [`valutazioni_sc02.jsonl`](valutazioni_sc02.jsonl) | Tabella strutturata, 21 righe: classe, indicatori, copertura RQ2 per `fact_key` (presenza nel contesto e nella risposta, con note), copertura pilot, supporto, fedeltà, motivazione, prima causa, contesto ricevuto, riferimenti di traccia |
| [`valutazioni_sc02.csv`](valutazioni_sc02.csv) | Stessa tabella, vista compatta |
| [`riepilogo_sc02.json`](riepilogo_sc02.json) | Riepilogo per modalità, con numeratore, denominatore, definizione ed esclusioni di ogni metrica |
| [`fonti_sc02.json`](fonti_sc02.json) | Impronte SHA-256 degli otto file sorgente letti |
| `valutazione_sc02.md` | Questo rapporto |

Sono stati aggiornati soltanto gli artefatti di questa scheda e aggiunto il
riferimento comune ai criteri. Le fonti sperimentali restano invariate;
`results/rq2/annotation_template_sc02.jsonl` conserva i giudizi a `null`.

**Non prodotti, per scelta:** grafici; estensione ad altri scenari; conclusioni
generali sulle architetture di memoria.

**Prossimo passo:** applicare la stessa distinzione nelle schede successive.
Le 21 classi di SC02 sono compilate; restano giudizi assistiti da includere
nella revisione complessiva, insieme ai riferimenti di copertura documentati
in §2. Questo non congela il protocollo.
