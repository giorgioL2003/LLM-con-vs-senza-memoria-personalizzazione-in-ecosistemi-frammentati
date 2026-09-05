# Valutazione assistita della prova reale di sviluppo — SC04 (U / G / FULL_HISTORY)

**Stato:** valutazione **assistita, da rivedere**. I giudizi su completezza, contenuto e causa
del fallimento sono proposte, non annotazioni approvate. Nessun campo di
`results/rq2/annotation_template_sc04.jsonl` è stato compilato: i campi manuali restano `null`.

**Natura dei risultati:** risultati **di sviluppo** su un solo scenario, una sola esecuzione,
7 domande per modalità, nessuna replica. Non sono risultati finali dell'esperimento.

**Revisione 2 (consolidamento dei criteri).** Questa versione corregge quattro giudizi della
prima stesura. Le correzioni sono elencate in §8 con il motivo. Dove un giudizio dipende da una
scelta metodologica ancora aperta, la valutazione è data **due volte**: secondo l'oracle
attualmente salvato e secondo il criterio alternativo proposto. Nessuna proposta è stata
applicata all'oracle, alla configurazione o al codice.

**Artefatti letti (non modificati):** `data/rq2/scenarios/scenario_04.json`,
`data/rq2/annotations/scenario_04_rq2.json`, `data/rq2/config/experiment_rq2.json`,
`results/rq2/facts/`, `results/rq2/memory/`, `results/rq2/graph/`,
`results/rq2/retrieval_sc04.jsonl`, `results/rq2/generation_inputs_sc04.jsonl`,
`results/rq2/generation_dev_sc04.jsonl`, `results/rq2/annotation_template_sc04.jsonl`.

---

## 1. Completezza e coerenza degli artefatti

| Controllo | Esito |
|---|---|
| Estrazione | 4 sessioni, tutte `executed: true`, `dry_run: false`, `parse_error: null` |
| Fatti | 38, tutti `provenance_valid: true` e `kind_valid: true` |
| Aggiornamenti | 38 operazioni: **34 ADD, 2 UPDATE, 2 NOOP, 0 DELETE, 0 rifiutate** |
| Stato | 34 voci attive + 2 in archivio (`superato`) |
| Grafo | 14 nodi, 21 archi; **5 archi con `provenance_valid: false`** |
| Retrieval | 14 righe (7 domande × U e G), tutte entro i 200 token |
| Generazione | 21 risposte, 0 errori, tutte `claude-sonnet-5` |
| Annotazione | 21 righe, giudizi manuali tutti `null` |

**7 domande per modalità confermate.** Nessuna cella mancante o duplicata.

Configurazione uniforme (`rq2-dev-0.1`, `claude-sonnet-5`, effort `medium`). Catena di
provenienza dichiarata e verificata: il grafo dichiara `facts_source` e `state_source` uguali a
quelli di U, quindi **G parte davvero dagli stessi fatti e dallo stesso stato**. Isolamento
verificato per ispezione: nei prompt di estrazione, aggiornamento e grafo non compaiono domande,
oracle o relazioni attese; i messaggi dell'assistente non entrano nell'estrazione. FULL_HISTORY
riceve i 7 messaggi utente completi, 529 token, `budget_applies: false`.

### Difetti negli artefatti prodotti

| # | Difetto | Dove |
|---|---|---|
| A1 | 5 archi con oggetto non dichiarato come nodo (`spam-generico`, `smishing`, `accessi.corvara.example`, `rimossa`, `bloccato_sul_gateway`) | E004, E005, E010, E016, E018 |
| A2 | **Tutti i 14 nodi hanno `aliases: []`** | grafo |
| A3 | Manca il nodo `PAGINA-ACCESSI` previsto dall'oracle | grafo |
| A4 | Manca l'arco diretto `ACC-207 → RULE-01` (relazione `SC04-R08`) | grafo |
| A5 | Due nodi contenitore non previsti dall'oracle, `CASE-01` e `RIEPILOGO-01`, collegati da archi generici `riguarda`: diventano hub | grafo |
| A6 | `memory_items` vale 36 in U (voci) e 35 in G (14 nodi + 21 archi): unità diverse, non confrontabili | retrieval |

---

## 2. SC04-Q2: la domanda e l'oracle non sono allineati

Testo della domanda: *«Come è classificato attualmente il caso e quali valutazioni iniziali sono
state superate?»*

### 2.1 L'incoerenza è interna all'oracle, non solo fra domanda e oracle

| Campo | Che cosa richiede |
|---|---|
| `mandatory_facts` | **quattro** elementi: classificazione smishing, **motivo** (pagina falsa che riproduce il modulo aziendale), valutazione superata «spam generico», valutazione superata «nessun contatto» |
| `accepted_equivalents` #1 | «formulazioni equivalenti che indichino lo smishing come classificazione attuale e riportino **entrambe le valutazioni superate**» — **tre** elementi, il motivo non compare |
| `accepted_equivalents` #2 | «risposte che descrivano la pagina come clone del portale di accesso aziendale senza citarne il dominio» — presuppone che il motivo **sia** richiesto |

`accepted_equivalents` #1 dichiara sufficiente una risposta che `mandatory_facts` giudica
incompleta, e #2 tira nella direzione opposta a #1. **L'oracle si contraddice al proprio
interno**, indipendentemente dal testo della domanda. Questa è la constatazione principale;
il disallineamento con la domanda letterale ne è una conseguenza.

### 2.2 Valutazione secondo l'oracle attualmente salvato (`mandatory_facts`, 4 elementi)

| | smishing | motivo | spam superato | contatto superato | esito |
|---|:-:|:-:|:-:|:-:|---|
| U | ✔ | ✖ | ✖ | ✔ | **parziale** (2/4) |
| G | ✔ | ✖ | ✖ | ✖ (dichiara insufficienza) | **parziale** (1/4) |
| FULL_HISTORY | ✔ | ✖ | ✔ | ✔ | **parziale** (3/4) |

### 2.3 Valutazione secondo la domanda letterale (e secondo `accepted_equivalents` #1)

Due elementi richiesti: classificazione attuale, valutazioni iniziali superate.

| | classificazione | valutazioni superate | esito |
|---|:-:|:-:|---|
| U | ✔ | 1 su 2 | **parziale** |
| G | ✔ | 0 su 2 | **parziale** |
| FULL_HISTORY | ✔ | 2 su 2 | **completa** |

**Solo un giudizio cambia: FULL_HISTORY-Q2, da parziale a completa.** U e G restano parziali con
entrambi i criteri: la scelta non modifica il confronto fra le due architetture in esame,
modifica il riferimento diagnostico.

### 2.4 Soluzione proposta (non applicata)

| Opzione | In cosa consiste | Effetto |
|---|---|---|
| **A** | Riformulare la domanda perché chieda il motivo: «Come è classificato attualmente il caso, **in base a quale evidenza**, e quali valutazioni iniziali sono state superate?». Correggere `accepted_equivalents` #1 aggiungendo il motivo | Tutte e tre restano parziali. Conserva R02 e R03 fra le relazioni richieste |
| **B** *(proposta)* | Lasciare la domanda com'è. Spostare il motivo fuori da `mandatory_facts`, in un campo distinto e non obbligatorio. Riscrivere `accepted_equivalents` #2 come dettaglio facoltativo. Ridurre le `required_relations` di Q2 a `SC04-R05` | FULL_HISTORY diventa completa; U e G restano parziali |
| **C** | Separare in due domande: classificazione con motivo, e valutazioni superate | Cambia la matrice a 8 domande per SC04: non praticabile senza rifare il dataset |

**Perché B.** È l'unica opzione che risolve la contraddizione interna **senza toccare il testo
della domanda**, e recepisce quello che `accepted_equivalents` #1 già dichiara: che una risposta
è accettabile con classificazione e valutazioni superate. Inoltre allinea la domanda al proprio
`phenomenon` dichiarato — «Classificazione confermata e valutazioni iniziali superate», dove il
motivo non compare — e alla `category` `update_obsolete`, che riguarda la gestione
dell'informazione superata, non la giustificazione della classificazione.

**Avvertenza necessaria.** A e B producono conteggi diversi. La scelta va motivata sul piano
metodologico e messa a verbale **prima** di compilare le annotazioni, non scelta guardando quale
delle due dà il numero preferito. Qui la si segnala come decisione aperta: §7, punto 2.

---

## 3. «RULE-01 creata» e «RULE-01 rimossa»: eventi storici, non stato corrente

Questa sezione **corregge** la prima stesura, che classificava il caso come «errore di gestione:
UPDATE mancato». Il riesame non lo conferma.

### 3.1 Che cosa dicono davvero le voci

| Voce | `claim_key` | `status` | Testo |
|---|---|---|---|
| `SC04-M028` | `acc207-regola-inoltro-creazione` | attivo | «Dalla stessa sessione di LOGIN-07, alle 07:20, su ACC-207 **è stata creata** una regola di inoltro.» |
| `SC04-M029` | `acc207-regola-inoltro-contenuto` | attivo | «La regola di inoltro creata su ACC-207 **invia** a archivio.backup@mailbox.example tutti i messaggi contenenti la parola fattura.» |
| `SC04-M030` | `acc207-regola-inoltro-id` | attivo | «La regola di inoltro creata su ACC-207 **è registrata** con l'identificativo RULE-01.» |
| `SC04-M031` | `rule01-rimozione` | attivo | «RULE-01 **è stata rimossa**.» |

`M028` e `M031` sono **due enunciati al passato su due eventi distinti**, entrambi veri e
compatibili: la regola è stata creata alle 07:20, ed è stata rimossa dopo. Nessuno dei due
afferma che la regola sia in vigore adesso. **Non c'è contraddizione fra le due voci attive.**

### 3.2 Che cosa significa `status: attivo`

Nello stato di U, `attivo` è una proprietà della **voce**, non del fatto del mondo: significa
«questa registrazione non è stata superata né ritirata». Non significa «la regola di inoltro è
operativa». Leggere `M028 | attivo` come «la regola è attiva» è un errore di lettura del modello
dati, non un difetto della memoria. La mia prima stesura lo commetteva implicitamente.

### 3.3 Che cosa dicono le istruzioni del costruttore

Il prompt di aggiornamento definisce UPDATE come: *«l'informazione **sostituisce** un fatto già
in memoria riferito allo stesso oggetto e allo stesso ambito (per esempio la stessa decisione,
la stessa ipotesi, la stessa attività)»*. La rimozione **non sostituisce** la creazione: la
creazione resta vera. La motivazione registrata dal modello è coerente con la propria consegna —
`SC04-OP031`, `reason`: *«Nuova informazione su azione di rimedio non presente in memoria.»*

Le istruzioni **non dicono** se un evento e la sua cessazione appartengano «allo stesso ambito».
È una lacuna della consegna, non una violazione.

### 3.4 Che cosa dice la politica di lettura

I marcatori di `question_scope()` includono «è ancora» e «non è più». Ma `M028` e `M031` sono
**entrambi `attivo`**, quindi entrambi leggibili sia in ambito corrente sia in ambito storico:
per gli eventi la distinzione corrente/storia **non discrimina nulla**. L'archivio si popola solo
quando qualcosa viene esplicitamente superato o ritirato.

Conferma quantitativa: **34 ADD, 2 UPDATE, 0 DELETE**, e i due soli UPDATE cadono esattamente
dove il messaggio dell'utente contiene un ritiro esplicito («Correzione della valutazione
iniziale…», «non è più valida»); le motivazioni del modello dicono «ritira esplicitamente».
**Con questa politica di `claim_key`, U produce archivio solo quando l'utente ritratta a parole.**
Su tutto il resto U si comporta come F con etichette in più. È l'osservazione più rilevante di
questa sezione, ed è indipendente dal caso RULE-01.

### 3.5 Le tre categorie richieste

| Categoria | Contenuto |
|---|---|
| **Errore dimostrato** | Nessuno sul caso RULE-01. Non risulta né una voce falsa, né un evento perso, né uno stato che affermi il contrario del vero |
| **Ambiguità del modello di memoria** | (i) `claim_key` non è definito: l'oracle lo usa come **slot di stato** (`regola-inoltro`), il modello come **identificatore di evento** (`acc207-regola-inoltro-creazione`, `rule01-rimozione`). Entrambe le letture sono coerenti con le istruzioni. (ii) `status: attivo` è ambiguo fra «registrazione valida» e «fatto in corso». (iii) Fra `M028` e `M031` non esiste **alcun collegamento**: nessun `superseded_by`, nessun riferimento incrociato, nessun `claim_key` condiviso. Ricostruire che la regola non è più in vigore richiede di recuperare **entrambe** le voci, e nulla lo garantisce |
| **Rischio non ancora osservato** | Un contesto che contenga `M028` o `M029` senza `M031` invita a presentare la regola come in essere. Su Q3, U ha ricevuto `M028` e `M030` **senza** `M031`, e G ha ricevuto `E014` senza `E016`. **In nessuna delle 21 risposte il rischio si è realizzato**: entrambe hanno risposto al passato, correttamente per una domanda sulla catena. Su Q4 il rischio non poteva realizzarsi perché nessuna delle due voci è entrata nel contesto. Il rischio è **possibile e tracciato negli artefatti, non avvenuto** |

### 3.6 Il punto che resta aperto, riformulato correttamente

Non è «manca un UPDATE». È: **il modello di memoria di U non dichiara se le voci siano enunciati
su eventi o su stati**, e da questa indecisione dipendono il significato di `claim_key`, il
significato di `status`, il popolamento dell'archivio e l'utilità della politica corrente/storia.
Va deciso, e la decisione riguarda U in generale, non SC04.

---

## 4. Operazioni attese: criteri semantici, non coincidenza di chiavi

L'annotazione dichiara già che `expected_operations` è parziale: *«qui sono annotati soltanto gli
aggiornamenti riconoscibili, non l'elenco completo»*. Va quindi letta come **elenco di requisiti
di significato**, non come tracciato da riprodurre.

**Non si propone** di riscrivere `expected_operations` sulle chiavi generate dal modello: sarebbe
adattare il metro al risultato. Si propongono quattro criteri sul significato.

### 4.1 I quattro criteri

| # | Criterio | Come si verifica sugli artefatti |
|---|---|---|
| **C1 — Conservazione degli eventi** | Ogni evento affermato in un messaggio resta recuperabile dalla memoria, non alterato e non fuso con altri | Confronto testo del messaggio ↔ testo delle voci; nessun evento deve sparire |
| **C2 — Correttezza dello stato corrente** | Una lettura in ambito corrente non deve mai restituire come valida un'affermazione che i messaggi successivi hanno reso non valida | Si legge lo stato attivo e si verifica che non contenga affermazioni contraddette |
| **C3 — Ritiro dell'invalidato** | Un'affermazione che l'utente ha esplicitamente ritirato o corretto non deve essere leggibile come valida nel presente, e deve restare leggibile come storia con il proprio stato | Presenza in archivio con `status` corretto |
| **C4 — Tracciabilità** | Da ogni voce si risale ai messaggi; e dove un'affermazione ne supera un'altra, il collegamento **conduce alla versione che la sostituisce** | `source_message_ids`; `superseded_by_entry` e la voce che punta |

**Equivalenza semantica ≠ coincidenza di identificatori.** Un'operazione attesa è soddisfatta se
lo **stato risultante** rispetta C1–C4, quali che siano `claim_key`, `entry_id` e il numero di
voci che la realizzano. Non è soddisfatta se lo stato viola un criterio, anche se le chiavi
coincidono. La verifica va fatta **sulla lettura che lo stato consente**, non sull'etichetta
dell'operazione.

### 4.2 Applicazione alle 7 operazioni attese di SC04 (valutazione assistita)

| Attesa | Realizzata come | C1 | C2 | C3 | C4 | Esito |
|---|---|:-:|:-:|:-:|:-:|---|
| OP01 ADD spam iniziale | `M010` | ✔ | ✔ | ✔ | ✔ | soddisfatta |
| OP02 ADD nessun contatto | `M011` | ✔ | ✔ | ✔ | ✔ | soddisfatta |
| OP03 UPDATE → smishing | `M017` (ADD smishing) + `M018` (UPDATE che supera `M010`) | ✔ | ✔ | ✔ | **✖** | **parziale** |
| OP04 UPDATE contatto avvenuto | `M011 → M021`, e `M021` porta il nuovo valore | ✔ | ✔ | ✔ | ✔ | soddisfatta |
| OP05 ADD RULE-01 creata | `M028` + `M029` + `M030` | ✔ | ✔ | n/a | ✔ | soddisfatta (nota: frammentata in tre voci) |
| OP06 UPDATE RULE-01 rimossa | `M031` (ADD) | ✔ | ✔ | n/a | **✖** | **divergente, non erronea** |
| OP07 ADD origine non determinata | `M037` (+ `M038` NOOP) | ✔ | ✔ | ✔ | ✔ | soddisfatta |

**OP03, perché C4 non è soddisfatto.** `M010` («spam generico») è archiviato con
`superseded_by_entry: SC04-M018`, e `M018` dice «la valutazione iniziale … è stata corretta; non
è più considerata valida». Il collegamento porta al **ritiro**, non alla **sostituzione**: la
nuova classificazione sta in `M017`, che non è collegata a nulla. Chi segue la catena di
supersessione non arriva a «smishing». C2 e C3 sono comunque soddisfatti.

**OP06, perché divergente e non erronea.** C1 e C2 reggono (§3). C4 no: fra creazione e rimozione
non esiste collegamento. È il criterio che l'oracle intendeva garantire con l'UPDATE — ma
l'UPDATE è **un modo** di garantirlo, non l'unico. Un collegamento esplicito fra due eventi
sarebbe altrettanto valido, e oggi il modello dati non lo prevede.

### 4.3 Conseguenza operativa

L'annotazione dovrebbe esprimere ogni operazione attesa come **requisito di lettura**, per
esempio: *«dopo SC04-S4, una lettura in ambito corrente sulla regola di inoltro non deve
presentare RULE-01 come in vigore, e deve permettere di risalire alla sua rimozione»*. Un
requisito così è verificabile su qualunque insieme di `claim_key`, e distingue equivalenza
semantica da coincidenza di identificatori.

Il campo `required_state_keys` esiste già nel modello di annotazione ed è **vuoto in tutte e 21
le righe**: è il posto naturale dove questi requisiti andrebbero, se lo si decide.

---

## 5. Le 21 risposte

Legenda: **completa** / **parziale** / **errata** / **astensione corretta**.

### 5.1 Quadro d'insieme (valutazione assistita, da rivedere)

Secondo l'**oracle attualmente salvato**:

| | completa | parziale | errata | astensione corretta | informazione obsoleta | affermazioni non supportate |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| **U** | 2 | 4 | 0 | 1 | 0 | 2 |
| **G** | 2 | 4 | 0 | 1 | 0 | 0 |
| **FULL_HISTORY** | 5 | 1 | 0 | 1 | 0 | 1 (lieve) |

Secondo il **criterio alternativo proposto per Q2** (§2.4, opzione B), cambia una sola cella:
FULL_HISTORY passa a **6 complete, 0 parziali**. U e G restano invariate.

**Nessuna delle 21 risposte ha usato informazione obsoleta.** Nessuna ha presentato il caso come
spam generico, negato il contatto con il collegamento o dato RULE-01 per ancora attiva.

### 5.2 Dettaglio per domanda

| Domanda | U | G | FULL_HISTORY |
|---|---|---|---|
| **Q1** obiettivo | **completa** | **completa** | **completa** |
| **Q2** classificazione + superate | **parziale** — smishing + una sola valutazione superata | **parziale** — smishing; dichiara di non avere le valutazioni superate | **parziale** con l'oracle attuale (manca il motivo); **completa** con il criterio B |
| **Q3** catena | **parziale, con affermazione non supportata** — salta SMS→URL e l'apertura, e costruisce un ponte inesistente: «Da questa segnalazione risulta la sessione LOGIN-07» | **parziale** — dichiara di non trovare il messaggio segnalato e riporta la scorciatoia `CASE-01 → UT-207 → ACC-207 → LOGIN-07 → RULE-01`: topologicamente vera, esplicativamente insufficiente. Nessuna invenzione | **completa** — catena intera nell'ordine corretto. Aggiunge «(credenziali compromesse)», inferenza lieve non scritta nel corpus |
| **Q4** azioni completate | **parziale** — solo il blocco del numero | **parziale** — idem | **completa** — tutte e tre |
| **Q5** aperto + riepilogo | **parziale, con affermazione non supportata** — afferma che resta da completare *il riepilogo*, che è un requisito e non l'attività aperta | **parziale** — dichiara di non sapere cosa resta da completare, riporta correttamente il riepilogo | **completa** |
| **Q6** punto non determinato | **completa** | **completa** | **completa** |
| **Q7** informazione assente | **astensione corretta** | **astensione corretta** | **astensione corretta** |

### 5.3 Il caso Q4: provenienza completa su evidenza assente

Su Q4, in U e in G, il retrieval dichiara `evidence_provenance_complete: true` e tutti e tre i
fatti obbligatori risultano `provenance_match: true`. La corrispondenza passa da `SC04-M033`
(blocco del numero) e `SC04-M035` (contenuto del riepilogo), che condividono il messaggio
`SC04-S4-U1` con i fatti richiesti **senza esprimerli**.

Le voci che contengono la risposta — `SC04-M031` («RULE-01 è stata rimossa») e `SC04-M032` («la
password di ACC-207 è stata reimpostata alle 08:05») — esistono in memoria e **non sono mai
entrate nel contesto**: punteggio TF-IDF **0.0**, quindi escluse dalla soglia sul punteggio nullo.

**La presenza degli identificatori sorgente ha certificato come completa un'evidenza che non
c'era.** Conferma su dati reali dell'avvertimento della sezione 7 di `RQ2.md`.

### 5.4 Due falsi positivi di relazione

1. **Q2, U e G:** `SC04-R02` (`SMS-01 contiene URL-01`) e `SC04-R03` (`URL-01 imita
   PAGINA-ACCESSI`) risultano presenti per provenienza grazie a `SC04-M017` («il caso è
   classificato come smishing»), che non esprime né l'una né l'altra.
2. **Q3, G:** `SC04-R08` (`ACC-207 presenta RULE-01`) risulta presente grazie all'arco `SC04-E014`
   (`LOGIN-07 ha_originato RULE-01`). Il grafo **non contiene** archi fra `ACC-207` e `RULE-01`
   (difetto A4). Lo stesso arco copre anche `SC04-R09`.

Quindi su Q3 la copertura relazionale reale di G è **4 su 7**, non 5.

---

## 6. Prima causa osservabile, e che cosa resta ipotesi

Ordine diagnostico: raggiungibilità → estrazione → gestione → grafo → retrieval → risposta.

| Caso | Prima causa **osservata** | Evidenza negli artefatti |
|---|---|---|
| U-Q2 | **retrieval** | `M010` (rank 24) e `M018` (rank 27) hanno punteggio **0.0**: esclusi dalla soglia. La lettura storica era attiva (36 voci leggibili): l'archivio era aperto, il ranking non ci è arrivato |
| G-Q2 | **retrieval relazionale** | Tre archi generici (`E020`, `E001`, `E021`, tutti `riguarda`) occupano la testa della selezione; `E007` (`non_ha_avuto_contatto_con`, `superato`, leggibile, punteggio 0.25) non entra nel budget |
| U-Q3 | **retrieval**, poi **risposta** | `M012/M013/M014` e `M019/M020` sono in memoria e non selezionati; l'affermazione «da questa segnalazione risulta LOGIN-07» non è nel contesto. Sono due fallimenti distinti e osservabili separatamente |
| G-Q3 | **retrieval relazionale**, concausa **grafo** | Gli archi giusti esistono (`E006`, `E008`, `E009`); `E006` è escluso con motivo registrato «non incidente a un nodo iniziale o a un percorso». `graph_question_node_ids` vuoto |
| U-Q4, G-Q4 | **retrieval** | `M031` e `M032` hanno punteggio 0.0 → esclusi |
| U-Q5 | **retrieval**, poi **risposta** | `M034` rank 13, punteggio 0.057, fuori budget; poi l'affermazione che l'attività aperta è il riepilogo |
| G-Q5 | **retrieval** | `M034` rank 22, fuori budget. La risposta si comporta correttamente dichiarando l'insufficienza |
| FH-Q2 | **risposta** con l'oracle attuale; **nessuna** con il criterio B | `SC04-S2-U1` era interamente nel contesto |

### 6.1 Ipotesi, non conclusioni

Le seguenti affermazioni **non sono dimostrabili** dagli artefatti e vanno dichiarate ipotesi:

| Ipotesi | Perché non è dimostrata | Come si verificherebbe |
|---|---|---|
| «Se `M012`–`M014` e `M019`–`M020` fossero entrati nel contesto, U-Q3 avrebbe risposto correttamente» | FULL_HISTORY ci è riuscito, ma con l'intera cronologia: non isola la variabile | Rieseguire la sola generazione con un contesto costruito a mano — richiede chiamate al modello |
| «Con alias non vuoti G avrebbe ancorato i nodi giusti e coperto la catena» | L'ancoraggio fallito è osservato; il suo effetto controfattuale no | Ricostruire il grafo con alias e rieseguire il retrieval |
| «Il `claim_key` per evento ha danneggiato il retrieval su Q4, lasciando `M031` lessicalmente povero» | È osservato solo il punteggio 0.0. Il legame con la scelta del `claim_key` è congetturale | **Verificabile offline, senza chiamate al modello**: ricalcolare il TF-IDF su una voce unificata di prova |
| «U colma i vuoti, G li dichiara» | 7 domande, una esecuzione, nessuna replica | Altri scenari e repliche |
| «La frammentazione di `M028`/`M029`/`M030` ha ridotto la massa lessicale di ciascuna voce» | Plausibile, non misurato | Stesso controllo offline della riga sopra |

---

## 7. Il confronto U/G: che cosa sostiene e che cosa no

Questa sezione **corregge** la prima stesura, che dichiarava il confronto compromesso dal
maggiore sovraccarico di G e affermava che «G non è stato misurato». Entrambe le affermazioni
erano sbagliate.

### 7.1 Il sovraccarico è un costo dell'architettura, non un difetto del disegno

Il budget è **uguale per U e per G**: 200 token sul blocco di contesto come finisce nel prompt.
Che G spenda più token in identificatori, stati e relazioni **è una proprietà di G**, ed è
esattamente ciò che un confronto a parità di budget deve far emergere. Misurato:

| | sovraccarico | contenuto |
|---|---:|---:|
| U | 75–90 token | 84–111 token |
| G | 98–127 token | **59–96 token** |

Che a 200 token G porti meno contenuto di U **è un risultato**, non un confondente. La sezione 3
di `RQ2.md` lo prevedeva già: «è la differenza che i confronti T/F, F/U e U/G devono misurare».

### 7.2 Il confronto complessivo regge; l'attribuzione causale no

Vanno tenute distinte due affermazioni:

| Affermazione | Sostenuta dagli artefatti? |
|---|---|
| «Su SC04, con questo budget e questa implementazione, G non ha fatto meglio di U, e ha fallito in modo diverso» | **Sì**, come osservazione di sviluppo su 7 domande e una esecuzione. Stessi fatti, stesso stato, stesso budget, stesso modello, stesse istruzioni, isolamento verificato |
| «La rappresentazione a grafo, in quanto tale, è meno efficace della memoria a fatti aggiornati» | **No.** «G come implementato» comprende almeno tre contributi non separati: (a) l'unità di rappresentazione, (b) la qualità del grafo costruito — alias vuoti, nodi hub, archi mancanti, oggetti non dichiarati, (c) la politica di recupero relazionale — priorità `1 + 1/posizione` sempre superiore a qualunque coseno, semi dalle prime 3 voci, `max_hops` 3. Gli artefatti non permettono di attribuire il risultato a uno dei tre |

**Alias vuoti e ancoraggio debole sono risultati di G, non scuse.** Il costruttore del grafo fa
parte dell'architettura in esame: se produce alias vuoti, quello è un comportamento di G e va
contato come tale. Quello che non si può fare è il passo successivo — dire che *la
rappresentazione a grafo* è la causa — perché per quello servirebbe un'ablazione (per esempio: lo
stesso grafo con alias, o lo stesso grafo con la priorità disattivata) che non è stata eseguita.

### 7.3 Il limite vero è la potenza

7 domande, 1 scenario, 1 esecuzione, nessuna replica, oracle non approvato, protocollo non
congelato. Il confronto sostiene **diagnosi**, non conclusioni, e nessun numero di questa prova
va riportato come risultato dell'esperimento.

### 7.4 Il risultato più netto non è U contro G

FULL_HISTORY fa 5 risposte complete su 7 (6 con il criterio B); U e G ne fanno 2 ciascuna, a
parità di modello e istruzioni. Con 529 token di cronologia integrale il modello risponde quasi
sempre; con 200 token selezionati no. Su SC04 il collo di bottiglia non è la disponibilità
dell'informazione: è la selezione.

---

## 8. Correzioni rispetto alla prima stesura

| # | Prima dicevo | Ora dico | Perché |
|---|---|---|---|
| 1 | «RULE-01: UPDATE mancato, errore di gestione» | Divergenza fra due modelli di memoria coerenti, non errore dimostrato. Resta un difetto di tracciabilità (C4) e un rischio non realizzato | `M028` e `M031` sono due eventi al passato compatibili; `status: attivo` qualifica la voce, non il fatto; le istruzioni non definiscono l'ambito (§3) |
| 2 | «Il confronto U/G non regge per il maggiore sovraccarico di G» | Il confronto complessivo regge: a parità di budget il sovraccarico è un costo dell'architettura. Non regge la sola attribuzione causale alla rappresentazione | §7.1–7.2 |
| 3 | «G non è stato misurato» | G **come implementato** è stato misurato. Non è separabile il contributo di rappresentazione, costruttore e politica di recupero | Alias e ancoraggio sono comportamenti del costruttore, che fa parte di G |
| 4 | «Q4 richiede R08 senza motivo apparente» | R08 è difendibile: la risposta attesa nomina RULE-01 come regola sull'account. Il problema è un altro: `evidence_complete` è `false` per l'assenza di R08 mentre la lacuna reale — il contenuto di `M031` e `M032` — resta invisibile all'indicatore | L'indicatore dà l'esito giusto per la ragione sbagliata (§5.3) |
| 5 | «Riscrivere `expected_operations` sulle chiavi reali» | **Ritirata.** Si propongono criteri semantici C1–C4 e requisiti di lettura | Adattare il metro al risultato (§4) |
| 6 | «Q3: l'ordine R09→R08 è un'incoerenza» | È **ammissibile** per la definizione dichiarata (la catena può ripassare da un'entità già incontrata, e ACC-207 era già stata toccata). Resta un punto di leggibilità, non un difetto | `relation_chain_note` nell'annotazione |
| 7 | «G copre 5 relazioni su 7 su Q3» | **4 su 7**: R08 è un falso positivo di provenienza | §5.4 |
| 8 | FULL_HISTORY-Q2 «parziale» | Parziale con l'oracle attuale, **completa** con la domanda letterale e con `accepted_equivalents` #1 | §2 |

---

## 9. Decisioni metodologiche aperte

| # | Decisione | Perché ora | Chi la prende |
|---|---|---|---|
| 1 | **Voci di U: eventi o stati?** Definire `claim_key`, chiarire `status`, decidere se servono collegamenti fra eventi correlati | Da qui dipendono archivio, politica corrente/storia e significato di U. Oggi 34 ADD su 38 e archivio a 2 voci | studente |
| 2 | **Q2: opzione A o B** (§2.4). Va messa a verbale prima di annotare | Cambia il giudizio su FULL_HISTORY-Q2 | studente |
| 3 | **`expected_operations` come requisiti di lettura** (§4.3), eventualmente in `required_state_keys`, oggi vuoto in tutte le righe | Rende verificabile U senza dipendere dalle chiavi | studente |
| 4 | **Q3: `R05` fra i fatti obbligatori ma non fra le relazioni; `R03` nella risposta attesa ma in nessuno dei due elenchi** | Disallineamenti reali fra `mandatory_facts`, `required_relations` ed `expected_answer` | studente |
| 5 | **Soglia sul punteggio nullo**: ha escluso `M010`, `M018`, `M031`, `M032` in tre domande | È la regola che ha prodotto più fallimenti osservati | studente |
| 6 | **Budget di 200 token**, alla luce dei valori misurati in §7.1 | Già dichiarato aperto in `RQ2.md`; ora c'è la misura | studente |
| 7 | **Se e come separare i contributi dentro G** (rappresentazione / costruttore / recupero) con un'ablazione | Senza, nessuna affermazione causale su G è sostenibile | studente |
| 8 | **Significato di `negated`**: oggi sembra «la frase contiene una negazione», non «l'affermazione è ritirata». Vale sia nell'oracle sia nei fatti estratti | Non incide sui conteggi attuali, incide sull'analisi degli errori | studente |

---

## 10. Che cosa questa prova **non** dimostra

- Non dimostra che la rappresentazione a grafo sia meno efficace: G come implementato ha reso
  meno di U, ma il contributo della rappresentazione non è separato da quello del costruttore e
  della politica di recupero.
- Non dimostra che U gestisca male gli aggiornamenti: due UPDATE su due espliciti sono corretti;
  il caso RULE-01 è una divergenza di modello, non un errore.
- Non dimostra nulla sulla stabilità: nessuna replica.
- Non è una valutazione approvata: è una lettura assistita degli artefatti, da rivedere.
