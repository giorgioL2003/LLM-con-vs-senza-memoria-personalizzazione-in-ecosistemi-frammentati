# RQ2 — sintesi dei risultati disponibili

**18 settembre 2026.** Raccoglie in un solo posto i numeri delle quattro schede
per scenario — [SC02](SC02/) r3, [SC03](SC03/) r2, [SC04](SC04/) r3,
[SC05](SC05/) r2 — e la lettura che ne segue.

**Che cosa è questo documento.** Una vista d'insieme di **risultati di
sviluppo**. Ogni numero è preso dai file delle schede e verificato contro i loro
JSONL: nessun valore è stato ricopiato a mano, e **nessuno scenario è stato
sommato o mediato con un altro**. La tabella in formato aperto è
[`sintesi_rq2.csv`](sintesi_rq2.csv), generata dagli stessi file.

**Che cosa non è.** Non è un'approvazione, non congela il protocollo, non
sostituisce le schede e non attribuisce un punteggio complessivo a nessuna
architettura. Lo stato di approvazione delle valutazioni **resta quello
originario**, riga per riga, ed è riportato in ogni tabella.

---

## 1. Perimetro delle prove

### 1.1 Che cosa è stato eseguito

| Scenario | Modalità eseguite | Risposte | Esecuzione di riferimento |
|---|---|---:|---|
| **SC02** Lumen Market | T, F, FULL_HISTORY | 21 | esecuzione iniziale, 5 settembre 2026 |
| **SC03** Vesper Logistics / WS-114 | F, FULL_HISTORY (iniziale) + U (corretta) | 21 | **composita**: F e FULL_HISTORY 5 settembre; U da `retrieval_repair_v3`, `u-instructions-0.3` |
| **SC04** Corvara Servizi / smishing | U, G (corrette) + T + FULL_HISTORY | 28 | **composita**: U e G da `sc04_repair_v3` 5 settembre; T da `t_ext_v1` 8 settembre; FULL_HISTORY iniziale 4 settembre, **non rigenerata** |
| **SC05** Ardesia Mobilità / ARD-19 | U, GER, FULL_HISTORY + T | 28 | U, GER e FULL_HISTORY dalla **stessa** esecuzione 6 settembre; T da `t_ext_v1` 8 settembre |
| | **Totale valutato** | **98** | 70 a budget + 28 FULL_HISTORY |

Configurazione comune verificata in ogni scheda: `claude-sonnet-5`, effort
`medium`, budget **200 token** per le modalità a budget, istruzioni del prompt
identiche in tutte le righe, `error: null` ovunque.

### 1.2 Celle previste e non eseguite

| Cella | Stato |
|---|---|
| **SC01** — T e FULL_HISTORY | **non eseguite: 14 generazioni mancanti.** Nessun risultato disponibile, e nessun risultato va attribuito a questa riga. |

`RQ2.md` §9 e `INVENTARIO.md` §5 la registrano come l'unica riga della matrice
rimasta senza esecuzione.

### 1.3 Materiale escluso, e perché

Nulla di quanto segue entra nei numeri di questa sintesi.

| Materiale | Perché è escluso |
|---|---|
| **Pilot RQ1** — 56 risposte, `results/generation_pilot.jsonl` | risponde a un'altra domanda di ricerca (perimetro della memoria: C0/C1/C2), con budget e protocollo diversi |
| **Demo e prove singole** — 25 risposte in `results/demo_*`, `results/prova_manuale_*` | ripetizioni di una sola domanda, senza protocollo di replica |
| **Controlli tecnici** — `ger_dev/`, `ger_dev_v2/`, `t_ext_check/`, `offline_check/` | verifiche offline; `ger_dev*` usa memoria da **fixture scritte a mano**, non costruita dal modello |
| **Versioni storiche** — prime U di SC03, prime U/G di SC04 | sostituite dalle versioni corrette; conservate nella storia dello sviluppo di ciascuna scheda |
| **Fixture** — `tests/fixtures/rq2/` | dati predisposti per i test |

### 1.4 Stato delle valutazioni

| Gruppo | Righe | Stato |
|---|---:|---|
| SC05 — U, GER, FULL_HISTORY | 21 | **classi e indicatori approvati dallo studente** il 6 settembre 2026 (`sc05-rq2-ger-0.2`). Non è approvazione del relatore. Riportati **senza riclassificazione**. |
| SC02, SC03, SC04 — tutte; SC05 — T | 77 | **proposti dall'assistente, non approvati** |
| Campi su supporto e fedeltà al contesto | 98 | **nuovi e proposti** in tutte le schede, anche dove la classe è approvata |

---

## 2. Tabella numerica per scenario e modalità

Legenda. **C&S** = risposte *complete e supportate*, il numeratore del Complete
Answer Rate secondo `CRITERI_VALUTAZIONE.md`. **classi** = completa / parziale /
errata / astensione corretta. **Retrieval** = domande con tutti i
`required_facts` RQ2 nel **contenuto** del contesto, su domande raggiungibili.
**Answer** = complete e supportate fra quelle con evidenza completa nel
contesto. **Obs.** e **Non sup.** = informazione obsoleta e affermazioni non
supportate, su tutte le prove.

**«Classe completa» e «completa e supportata» non sono la stessa cosa.** Una
risposta può contenere tutti i fatti richiesti e aggiungere qualcosa che le
fonti non sostengono: resta `completa` come classe, ma non entra nel numeratore.
Succede in una riga, SC02-Q5/F, e la differenza è visibile nella tabella (F su
SC02: 3 complete, 2 complete e supportate).

**L'astensione corretta non è un fallimento.** È il comportamento che l'oracle
prescrive su Q7 in tutti e quattro gli scenari. Resta fuori dal numeratore
perché quella metrica conta le risposte complete, non i comportamenti corretti,
ed è misurata a parte: **1/1 in tutte e 14 le righe**.

### 2.1 Modalità a budget (200 token)

| Scenario | Mod. | Ruolo | n | **C&S** | % | classi | Retrieval | Answer | Obs. | Non sup. | Stato | Rev. |
|---|---|---|--:|:-:|--:|:-:|:-:|:-:|:-:|:-:|---|:-:|
| **SC02** | **T** | principale | 7 | **5/7** | 71,4 | 5/1/0/1 | 5/6 | 5/5 | 0/7 | 0/7 | proposto | r3 |
| **SC02** | **F** | principale | 7 | **2/7** | 28,6 | 3/1/2/1 | 4/6 | 2/4 | 1/7 | 2/7 | proposto | r3 |
| **SC03** | **F** | principale | 7 | **1/7** | 14,3 | 1/4/1/1 | 1/6 | 1/1 | 0/7 | 0/7 | proposto | r2 |
| **SC03** | **U** | principale | 7 | **1/7** | 14,3 | 1/2/3/1 | 1/6 | 1/1 | 1/7 | 1/7 | proposto | r2 |
| **SC04** | **U** | principale | 7 | **2/7** | 28,6 | 2/4/0/1 | 2/6 | 2/2 | 0/7 | 0/7 | proposto | r3 |
| **SC04** | **G** | principale | 7 | **2/7** | 28,6 | 2/4/0/1 | 2/6 | 2/2 | 0/7 | 0/7 | proposto | r3 |
| **SC04** | **T** | aggiuntivo | 7 | **4/7** | 57,1 | 4/2/0/1 | 4/6 | 4/4 | 0/7 | 0/7 | proposto | r3 |
| **SC05** | **U** | principale | 7 | **2/7** | 28,6 | 2/2/2/1 | 3/6 | 2/3 | 0/7 | 2/7 | **approvato** | r2 |
| **SC05** | **GER** | principale | 7 | **1/7** | 14,3 | 1/3/2/1 | 2/6 | 1/2 | 0/7 | 2/7 | **approvato** | r2 |
| **SC05** | **T** | aggiuntivo | 7 | **3/7** | 42,9 | 3/0/3/1 | 4/6 | 3/4 | 2/7 | 0/7 | proposto | r2 |

Reachability: **6/7 in tutte e 14 le righe**, per costruzione — il perimetro è
l'intero scenario in ogni modalità — quindi non distingue nulla e non è
riportata in colonna.

**Le colonne non vanno lette in verticale fra scenari diversi.** Le domande, gli
oracle e la lunghezza delle conversazioni cambiano: il 5/7 di T su SC02 e il 3/7
di T su SC05 non sono confrontabili fra loro.

**Denominatori piccoli nella colonna «Answer».** Su SC03 vale 1/1 per entrambe
le modalità, su SC04 2/2, su SC05 2/3 e 1/2: non vanno riportati come
percentuali.

### 2.2 FULL_HISTORY — controllo diagnostico, fuori budget

Tabella separata perché **non è confrontabile** con le righe di §2.1: non ha
budget, non esegue selezione — quindi non ha una metrica di retrieval — e
riceve l'intera cronologia.

| Scenario | n | **C&S** | % | classi | Answer | Obs. | Non sup. | Token di contesto | Rapporto col budget |
|---|--:|:-:|--:|:-:|:-:|:-:|:-:|--:|--:|
| **SC02** | 7 | 6/7 | 85,7 | 6/0/0/1 | 6/6 | 0/7 | 0/7 | 319 | 1,6× |
| **SC03** | 7 | 5/7 | 71,4 | 5/1/0/1 | 5/6 | 0/7 | 0/7 | 537 | 2,7× |
| **SC04** | 7 | 4/7 | 57,1 | 4/2/0/1 | 4/6 | 0/7 | **1/7** | 529 | 2,6× |
| **SC05** | 7 | 6/7 | 85,7 | 6/0/0/1 | 6/6 | 0/7 | 0/7 | 645 | 3,2× |

**A che cosa serve questa riga.** Stabilisce che le domande sono rispondibili
dal corpus, e quindi che le incompletezze delle modalità a budget dipendono dal
contesto ricevuto o dal suo uso, non da un difetto del benchmark.

**E che cosa mostra di più.** Non è un limite superiore raggiunto: **in tre
scenari su quattro FULL_HISTORY non è completa su tutte le domande
raggiungibili** (Answer 5/6, 4/6, 6/6, 6/6). Su SC03-Q3 omette un fatto scritto
alla lettera nel contesto; su SC04-Q2 e Q3 omette il motivo della
classificazione e un passaggio della catena, e su SC04-Q3 **aggiunge
un'affermazione non supportata**. Una parte dell'incompletezza osservata nelle
modalità a budget **sopravvive anche alla storia completa**, e non è
attribuibile né al recupero né alla rappresentazione.

Su SC04 il confronto è ancora più stretto: **T raggiunge lo stesso 4/7** di
FULL_HISTORY con 136 token medi contro 529.

---

## 3. Confronti entro ciascuno scenario

Ogni confronto vale **dentro il proprio scenario**: sette domande, una
esecuzione per cella, nessuna replica.

### 3.1 SC02 — T contro F

**Osservato: T 5/7, F 2/7.** Si distinguono su tre domande (Q3, Q4, Q5); sulle
altre quattro danno lo stesso esito. F è l'unica delle due con informazione
obsoleta (1/7) e affermazioni non supportate (2/7).

**Cause documentate.** Su Q4 F presenta come aperta una verifica completata: il
fatto superato `SC02-F017` è a punteggio 0,2477 e i due che lo superano hanno
punteggio **0,0000**; F non applica UPDATE, quindi nulla nel contesto segnala il
superamento. Su Q5 la data «2026-09-08» non esiste nel corpus: è stata introdotta
dall'**estrattore** in `SC02-F022`, registrato con `provenance_valid: true`, e la
risposta la ripete fedelmente. Su Q3 F presenta un test e il suo esito come due
verifiche distinte.

**Ipotesi, non osservazione.** Che T sia protetta su Q4 perché il messaggio della
sessione 4 contiene sia lo stato aggiornato sia ciò che lo aggiorna è una lettura
coerente con il testo, non una proprietà dimostrata: un aggiornamento distribuito
su due messaggi avrebbe esposto anche T.

### 3.2 SC03 — F contro U

**Osservato: 1/7 entrambe.** Stesse due domande riuscite (Q1, Q2), stesse cinque
fallite. **L'aggiornamento della memoria non cambia quante risposte utili si
ottengono.** Cambia la forma: F ha 4 parziali e 1 errata, U 2 parziali e 3
errate, e U è l'unica con informazione obsoleta e un'affermazione non supportata.

**Cause documentate — e non sono le stesse.** Su Q3 la classe è identica ma la
causa no: in F l'evidenza era **nel contesto** e la risposta non l'ha usata
(`risposta`); in U **non esiste in memoria**, perché `SC03-OP017` è stato
applicato come NOOP senza produrre alcuna voce (`gestione`). Su Q5 la chiave
`stato-ipotesi-malware` creata da `SC03-OP013` è distinta da `ipotesi-malware`:
nessun UPDATE poteva superarla, la voce arriva marcata `attivo` e la risposta la
usa come punto aperto (`gestione`). **È l'unico caso della raccolta in cui
l'origine `gestione` risulta usata**, e riguarda l'architettura che dovrebbe
proteggere dal superato.

**Vista composita.** F e FULL_HISTORY vengono dall'esecuzione iniziale, U da
quella corretta: non condividono l'esecuzione.

### 3.3 SC04 — U contro G, con T aggiuntivo

**Osservato: U 2/7, G 2/7, T 4/7.** U e G hanno classi identiche su tutte e
sette le domande. Nessuna delle 28 risposte è errata, nessuna usa informazione
obsoleta, una sola contiene un'affermazione non supportata (FULL_HISTORY, §2.2).

**Cause documentate — G ha due difetti che U non ha, e sono nel grafo.** Su Q4
l'arco `SC04-E014 RULE-01 -rimossa-> ACC-207` ha stato `superato`: su una domanda
a portata `current` **viene escluso dai candidati**, che scendono a 14 contro i
32 di U. Non perde nel ranking: non entra in gara. In U le stesse informazioni
sono attive e perdono con punteggio 0,0000. Su Q3 tutti e 10 i nodi hanno
`aliases: []` e nessuna domanda ancora nodi dal proprio testo: i semi vengono
solo dalle voci di U, e il percorso trovato ha due archi mentre le altre cinque
relazioni **esistono nel grafo**. Copertura delle relazioni richieste nel
contesto di G: **3/11**.

**Un dato controintuitivo.** Sulla domanda di catena per cui SC04 è stato
costruito, **G esprime 3 relazioni su 7 e U ne esprime 5**, pur non avendo archi.

**Il vantaggio di T dipende dalla forma dei messaggi.** Su Q4 e Q5 la risposta
sta dentro `SC04-S4-U1`, che T riceve intero; su Q3, dove la catena è distribuita
su tre sessioni, T è **la peggiore delle quattro** (1 fatto su 6).

### 3.4 SC05 — U contro GER, con T aggiuntivo

**Osservato: U 2/7, GER 1/7, T 3/7.** *(classi di U e GER approvate dallo
studente; quelle di T proposte.)* **GER non mostra alcun vantaggio su U.**

**Causa documentata dell'unica differenza.** U e GER divergono su **una sola
domanda**, Q2, e a sfavore di GER. `SC05-M018`, l'unica voce che identifica
SRV-14 come server esposto, richiede 37 token e resta fuori in entrambe le fasi:
nella fase 1 la quota archivio aveva 17 token liberi su 100, nella fase 2 di
riuso lo spazio residuo complessivo era 24. U, con budget unico, la prende.

**La partizione non è stata esercitata come previsto.** Su Q5 il livello recente
**non contribuisce con nessun elemento**: tutte e sette le voci recenti hanno
punteggio 0,0000, la quota resta inutilizzata e 75 token tornano all'archivio.
GER paga il costo strutturale (94,7 token medi di sovraccarico, il 52 % del
contesto) senza esercitarne il beneficio.

**Sulla memoria non si perde nulla.** 41 operazioni proposte, 41 applicate, 0
rifiutate, 0 riparazioni: tutte le evidenze mancanti erano in memoria, attive e
corrette. La causa dominante è il punteggio nullo.

**T ha il tasso più alto fra le modalità a budget ed è l'unica con informazione
obsoleta** (2/7). Profili di errore speculari: T ripete fedelmente un contesto
superato; U e GER attribuiscono stati che il contesto non contiene (2/7 di
affermazioni non supportate ciascuna).

### 3.5 Nessuna graduatoria generale

Le quattro colonne di T — 5/7, –, 4/7, 3/7 — non sono una misura di T, e lo
stesso vale per U (–, 1/7, 2/7, 2/7). Scenari e domande differiscono per
lunghezza, distribuzione delle evidenze e formulazione dell'oracle, e **una sola
esecuzione per cella non regge un confronto fra medie**. In questa sintesi non
compare nessun valore aggregato su più scenari, per scelta.

---

## 4. Risposta provvisoria a RQ2

> **Domanda di ricerca** (`roadmap_progetto_tirocinio.md` §3): «Come cambia la
> capacità di un LLM di continuare correttamente un'attività distribuita tra più
> conversazioni quando, **a parità di informazioni accessibili**, la memoria
> viene organizzata e gestita attraverso architetture differenti?»
> La formulazione operativa di `RQ2.md` è la stessa: «a parità di informazioni
> accessibili, come cambia la capacità del modello di continuare l'attività
> quando la memoria viene *organizzata* in modo diverso?»

**Risposta provvisoria, sulle prove disponibili.** A parità di informazioni
accessibili e di budget, l'organizzazione della memoria **cambia dove e come il
sistema fallisce più di quanto cambi quante risposte utili produce**. Su
quattro scenari e settanta risposte a budget, nessuna delle architetture
strutturate — fatti, fatti con stato, grafo, memoria a livelli — supera in modo
consistente il recupero dei messaggi interi: su SC02 e SC04 T è la modalità con
più risposte complete e supportate, su SC03 F e U pareggiano, su SC05 U supera
GER di una domanda. Le prove indicano piuttosto che le quattro fasi della
catena — rappresentazione, gestione dello stato, selezione sotto budget,
generazione — **falliscono in modo indipendente, e che un miglioramento in una
non si trasferisce alle altre**. La rappresentazione decide quali unità esistono
e quanto costano: frammentare un messaggio in fatti conserva la precisione ma
spende fino al 59 % del budget in identificatori, provenienza e stato, e
riduce la massa lessicale su cui il ranking lavora. La gestione dello stato
protegge dall'informazione superata solo nella misura in cui la marcatura è
corretta: dove lo è, le voci superate non raggiungono le domande correnti; dove
non lo è, l'errore passa (SC03-Q5/U, una voce rimasta `attivo` sotto una chiave
propria). La selezione sotto budget è il punto in cui si perde più materiale: in
tutti e quattro gli scenari le evidenze mancanti erano **conservate, attive e
corrette**, escluse dalla soglia sul punteggio nullo o dall'arresto di budget, e
questo colpisce allo stesso modo architetture diverse. La generazione, infine,
resta una fonte di errore autonoma: **anche con l'intera cronologia nel contesto
FULL_HISTORY non è completa su tutte le domande raggiungibili in tre scenari su
quattro**, e in un caso aggiunge un'affermazione che il corpus non sostiene.
Quanto al rischio per cui le architetture con stato sono state costruite — usare
come valida un'informazione superata — le prove lo mostrano concentrato nelle
modalità senza stato temporale (T, 2 casi su SC05; F, 1 su SC02), ma il numero
di occasioni in cui è stato realmente esercitato è piccolo, e **l'assenza di
errori in U, G e GER va letta come esito di queste prove, non come proprietà
stabilita della gestione dello stato**.

---

## 5. Limiti essenziali

1. **Dimensione.** Sette domande per cella, 98 risposte in tutto. Una differenza
   di una domanda sposta un tasso di 14 punti percentuali.
2. **Nessuna replica.** Una sola esecuzione per cella. Le risposte del modello
   variano anche a parità di contesto: **le differenze osservate non sono cause
   dimostrate.**
3. **Confronti composti da esecuzioni diverse.** SC03: F e FULL_HISTORY
   dall'esecuzione iniziale, U da quella corretta. SC04: U e G dal 5 settembre,
   T dall'8, FULL_HISTORY dal 4 e **non rigenerata**. Solo SC02 e il nucleo di
   SC05 vengono da un'unica esecuzione.
4. **Stato di sviluppo.** Oracle e annotazioni sono in bozza
   (`status: BOZZA DA CONTROLLARE` su SC03, SC04 e SC05); il protocollo non è
   congelato.
5. **Stato di approvazione misto.** 21 righe hanno classi approvate dallo
   studente, 77 no; i campi su supporto e fedeltà sono nuovi e proposti per
   tutte e 98. **Questa sintesi non li approva.**
6. **Una cella non eseguita.** SC01, T e FULL_HISTORY.

---

## 6. Incoerenze residue che incidono sulla lettura

Documentate, **non risolte qui**, e nessuna tocca giudizi già approvati.

| # | Incoerenza | File e righe | Effetto sulla sintesi |
|---|---|---|---|
| 1 | **`faithful_to_received_context` ha due definizioni.** SC04 r3 e SC05 r2 lo pongono falso quando la risposta afferma qualcosa che il contesto non contiene, anche senza contraddirlo. SC03 r2 usa una lettura più permissiva. | `SC03/valutazioni_sc03.jsonl`, riga `SC03-Q5` modalità `U`, campo `faithful_to_received_context: true` con `unsupported_claim: true`; confronta `SC04/valutazioni_sc04.jsonl`, `SC04-Q3`/`FULL_HISTORY`, stesso schema con `false` | **Il campo non è aggregato in questa sintesi** e non compare né in §2 né nel CSV. Finché le definizioni non sono allineate, non deve diventare una metrica. |
| 2 | **Copertura a zero: `errata` o `parziale`?** SC03 classifica `errata` le risposte che consegnano 0 fatti obbligatori pur dichiarando l'insufficienza (Q6/F, Q4/U, Q6/U); SC04 non ha casi; SC05 segue la stessa regola (Q5/T, Q5/U, Q5/GER, Q3/U, Q3/GER). | `SC03/valutazione_sc03.md` §11 punto 2; `SC05/valutazione_sc05.md` §11 punto 2 | Sposta la ripartizione fra `parziale` ed `errata` in §2.1, **non i valori C&S**: nessuna di queste righe è complete-and-supported in nessuna lettura. |
| 3 | **Rettifica proposta su SC05-Q4/T**, da `parziale` a `errata`, divergente dal giudizio proposto in `t_ext_v1`. | `SC05/valutazioni_sc05.jsonl`, `SC05-Q4`/`T`, campo `divergenza_dal_giudizio_precedente` | Cambia le classi di T su SC05 da 3/1/2/1 a 3/0/3/1 in §2.1; **C&S invariato a 3/7**. |
| 4 | **Due oracle con conteggi diversi.** In SC02 l'oracle della risposta è nel file del pilot e la scomposizione RQ2 in un file separato, con denominatori diversi su Q2, Q5, Q6 e Q7; in SC03, SC04 e SC05 stanno nello stesso file. | `SC02/valutazione_sc02.md` §2 e §8 punto 4 | Le colonne «Retrieval» e «C&S» di §2.1 usano riferimenti diversi (`required_facts` la prima, `mandatory_facts` la seconda): **non vanno confrontate fra loro nemmeno dentro la stessa riga**. |
| 5 | **`wrong_abstention` non cattura le astensioni su domande rispondibili** quando l'evidenza non è stata recuperata: per §9.4 resta falso. Vale in tutte e quattro le schede. | `SC03` §11 punto 3, `SC05` §11 punto 2 | La colonna è **0/7 in tutte e 14 le righe** di §2.1: non distingue nulla, ed è riportata solo nel CSV. |

---

## 7. File e verifiche

| File | Contenuto |
|---|---|
| `SINTESI_RQ2.md` | Questo documento |
| [`sintesi_rq2.csv`](sintesi_rq2.csv) | 14 righe (una per scenario × modalità), 21 colonne: conteggi, frazioni, percentuali, stato di approvazione, revisione della scheda sorgente ed esecuzione di riferimento |

**Verifiche eseguite.** Il CSV è generato leggendo i quattro
`valutazioni_*.jsonl` e i quattro `riepilogo_*.json`; per ogni riga sono
confrontati, e devono coincidere, il numero di risposte, il numeratore delle
complete e supportate, la somma delle quattro classi, il denominatore
dell'Answer Success e numeratore e denominatore del Retrieval Success. Le
tabelle di §2 sono trascritte da quel CSV.

**Fonti.** `INVENTARIO.md`, `CRITERI_VALUTAZIONE.md`, le quattro schede nelle
revisioni indicate in §2, `RQ2.md`, `EXPERIMENT.md`,
`roadmap_progetto_tirocinio.md`. Nessun file è stato modificato dalla creazione
di questa sintesi.

**Non prodotti, per scelta:** grafici; valori aggregati su più scenari;
qualsiasi materiale di RQ3.
