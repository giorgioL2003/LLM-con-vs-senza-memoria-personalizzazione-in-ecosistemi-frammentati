# Valutazione assistita delle 14 risposte di T — SC04 e SC05

**Stato:** giudizi **proposti dall'assistente, non approvati**. Nessuna
approvazione dello studente, nessuna approvazione del relatore, protocollo non
congelato. I giudizi già registrati di U, G, GER e FULL_HISTORY **non sono stati
rivisti**: sono riportati come stanno negli artefatti esistenti.

**Natura dei risultati:** risultati **di sviluppo**. Una sola esecuzione, sette
domande per cella, nessuna replica, annotazioni degli scenari ancora in bozza.
Non sono risultati dell'esperimento e non vanno riportati come tali.

**Metodo, identico a quello usato per le altre modalità.** Ogni risposta è stata
letta insieme al contesto che ha davvero ricevuto e ai fatti obbligatori; la
presenza di un'evidenza è giudicata sul **contenuto** delle righe di contesto,
non sulla corrispondenza degli identificatori sorgente. Classi ammesse:
`completa`, `parziale`, `errata`, `astensione corretta`. Indicatori separati:
`obsolete_used`, `unsupported_claim`, `wrong_abstention`. Ordine diagnostico
delle cause: raggiungibilità → estrazione → gestione → grafo → retrieval →
risposta.

**Artefatti letti e non modificati:** `data/rq2/scenarios/scenario_04.json`,
`scenario_05.json`, le annotazioni dei due scenari,
`results/rq2/sc04_repair_v3/`, `results/rq2/generation_dev_sc04.jsonl`,
`results/rq2/sc05_dev_v1/`, `results/rq2/evaluation_dev_sc04.md`.

| file | ruolo |
|---|---|
| `annotation_template_t_sc04.jsonl`, `annotation_template_t_sc05.jsonl` | template originali, giudizi `null`, **intatti** |
| `annotation_compilata_t_sc04.jsonl`, `annotation_compilata_t_sc05.jsonl` | copie compilate con i giudizi **proposti** |
| questo file | motivazioni ed evidenze |
| `confronti_per_scenario.md` | i confronti dentro SC04 e dentro SC05 |

---

## 1. Esecuzione

| | |
|---|---|
| Chiamate | **14**, tutte di risposta; 0 di costruzione della memoria |
| Errori | 0 di esecuzione, 0 di parsing, 0 risposte vuote |
| Modello | `claude-sonnet-5` in tutte e 14, effort `medium`, nessun modello di ripiego |
| Configurazione | `rq2-dev-0.1`, estensione `matrice-estesa-0.1`, budget 200 token |
| Retrieval | 14 righe, 88–200 token, **nessuna eccezione sul primo elemento** |
| Artefatti precedenti | invariati, verificati per impronta |

## 2. Giudizi proposti

### SC04 — T

| Domanda | Classe | Origine | Indicatori |
|---|---|---|---|
| **Q1** obiettivo | **completa** | – | – |
| **Q2** classificazione + superate | **parziale** (2/4) | retrieval | – |
| **Q3** catena | **parziale** (1/6) | retrieval | astensione impropria |
| **Q4** azioni completate | **completa** | – | – |
| **Q5** aperto + riepilogo | **completa** | – | – |
| **Q6** punto non determinato | **completa** | – | – |
| **Q7** informazione assente | **astensione corretta** | – | – |

**4 complete, 2 parziali, 0 errate, 1 astensione corretta.** Nessuna informazione
obsoleta, nessuna affermazione non supportata, 1 astensione impropria.

### SC05 — T

| Domanda | Classe | Origine | Indicatori |
|---|---|---|---|
| **Q1** obiettivo | **completa** | – | – |
| **Q2** server corretto | **completa** | – | – |
| **Q3** verifiche aperte | **errata** | retrieval | **informazione obsoleta** |
| **Q4** due livelli | **parziale** | retrieval | **informazione obsoleta** |
| **Q5** verifiche completate | **errata** (0/2) | retrieval | astensione impropria |
| **Q6** scadenza cliente | **completa** | – | – |
| **Q7** informazione assente | **astensione corretta** | – | – |

**3 complete, 1 parziale, 2 errate, 1 astensione corretta.** **2 usi di
informazione obsoleta**, nessuna affermazione non supportata, 1 astensione
impropria.

---

## 3. Il risultato principale: T usa informazione obsoleta, e si vede il perché

È la **prima volta nel progetto** che `obsolete_used` risulta vero. Succede due
volte, entrambe su SC05, entrambe con lo stesso meccanismo.

La domanda SC05-Q3 chiede quali verifiche restano aperte *in questo momento*.
Nel contesto di T entra `SC05-S8-U1` (sessione 8):

> «Restano aperte la verifica del registro del bilanciatore e la revisione delle
> regole di esportazione su `SRV-14`.»

Il messaggio che la supera, `SC05-S9-U1` (sessione 9), dice:

> «La verifica del registro del bilanciatore è completata: conferma una sola
> sessione anomala. Resta aperta soltanto la revisione delle regole di
> esportazione su `SRV-14`.»

| | rango | punteggio | token | selezionato |
|---|---:|---:|---:|:-:|
| `SC05-S8-U1` (superato) | 2 | 0,2034 | 47 | **sì** |
| `SC05-S9-U1` (che lo supera) | 16 | **0,0000** | 44 | no |

Su Q4 la stessa cosa: `SC05-S8-U1` rango 2 con 0,1891, `SC05-S9-U1` rango 13 con
0,0120, fuori dal contesto.

**Due cause distinte, entrambe osservabili.** La prima è il ranking: il messaggio
che corregge ha punteggio nullo o quasi, perché la domanda dice «verifiche
restano aperte» e il messaggio dice «è completata… resta aperta soltanto». La
seconda è architetturale e non dipende dal ranking: **in T non esiste uno stato
temporale**. Anche se `SC05-S9-U1` fosse entrato, nulla nel contesto avrebbe
detto che `SC05-S8-U1` è superato: sarebbero stati due messaggi in
contraddizione, e la scelta sarebbe rimasta al modello. In U e in GER
l'informazione superata non entra affatto, perché la politica di lettura ammette
le voci superate solo nelle domande storiche, e Q3 e Q4 non lo sono.

**Su SC04 il rischio non si è presentato, e per un motivo fragile.** Su SC04-Q3 T
ripete dal contesto che «la valutazione iniziale è di spam generico senza alcun
contatto con il link». Non è conteggiata come informazione obsoleta perché è
riportata come valutazione **iniziale**, esattamente come la qualifica il
messaggio originale `SC04-S1-U1`. A proteggere la risposta è stata la
formulazione del messaggio, non una proprietà dell'architettura: un messaggio
scritto al presente avrebbe prodotto lo stesso errore di SC05-Q3.

## 4. Il risultato opposto: il messaggio intero porta più contenuto della memoria

Su SC04-Q4 e SC04-Q5, T è **completa** dove U e G sono parziali. La causa è
leggibile: entrambe le risposte stanno dentro un solo messaggio,
`SC04-S4-U1`, che T recupera intero.

> «`RULE-01` è stata rimossa e la password di `ACC-207` è stata reimpostata alle
> 08:05; il numero mittente è stato bloccato sul gateway aziendale. Resta da
> completare la revisione dei messaggi inoltrati fra le 07:20 e la rimozione
> della regola. Il riepilogo per il responsabile deve indicare…»

In U e in G lo stesso messaggio è stato spezzato in voci separate, e su Q4 le due
voci che contengono la risposta (`SC04-M031` «RULE-01 è stata rimossa» e
`SC04-M032` «la password è stata reimpostata alle 08:05») hanno punteggio TF-IDF
**0,0** e restano fuori: è il caso già documentato in `evaluation_dev_sc04.md`,
§5.3. T non paga quel prezzo perché non frammenta.

Lo stesso vale su SC05-Q1, dove T è completa e U e GER sono parziali: nel
messaggio originale il secondo obiettivo è dichiarato come obiettivo, mentre in
memoria era stato sostituito dall'enunciato del suo compimento.

**È lo stesso fenomeno visto da due lati.** Non frammentare conserva la massa
lessicale e il contenuto, ma rinuncia allo stato temporale. Frammentare e tenere
lo stato protegge dall'informazione superata, ma espone al ranking che non trova
più i pezzi.

## 5. Motivazioni per domanda

**SC04-Q1 · completa.** Entrambi gli obiettivi da `SC04-S1-U1`.

**SC04-Q2 · parziale (2/4), origine *retrieval*.** Classificazione smishing e
motivo — «una pagina falsa che riproduce il modulo di accesso di
`accessi.corvara.example`» — presenti da `SC04-S2-U1`. Nessuna delle due
valutazioni superate: `SC04-S1-U1` non entra nel budget (arresto registrato) e
`SC04-S2-U2` non è selezionato. La risposta dichiara l'assenza invece di
inventare. **T è l'unica delle quattro modalità a riportare il motivo**, che
l'oracle attuale richiede fra i fatti obbligatori. Con il criterio alternativo B
di `evaluation_dev_sc04.md` §2.4 resta parziale, perché mancano comunque
entrambe le valutazioni superate: il giudizio non dipende dalla decisione aperta.

**SC04-Q3 · parziale (1/6), origine *retrieval*, astensione impropria.** T riceve
il solo `SC04-S1-U1` — 124 token su 200, arresto perché `SC04-S4-U1` non entra —
e dichiara l'insufficienza. Lettura più severa possibile: senza alcun passaggio
ricostruito la risposta sarebbe **errata**. Il confronto non cambia in nessuno
dei due casi, perché su questa domanda U e G portano più passaggi di T.

**SC04-Q4 · completa.** Tutte e tre le azioni (§4).

**SC04-Q5 · completa.** Attività aperta e contenuto del riepilogo, entrambi da
`SC04-S4-U1`.

**SC04-Q6 · completa.** Chiusura senza esito e punto non determinato, da
`SC04-S4-U2`.

**SC04-Q7 · astensione corretta.** Nessun fornitore introdotto.

**SC05-Q1 · completa.** §4.

**SC05-Q2 · completa.** `SC05-S2-U1` (SRV-12) e `SC05-S4-U1` (correzione) sono
entrambi nel contesto. Qui la correzione è scritta **dentro** il messaggio
originale — «il server esposto non è `SRV-12` ma `SRV-14`» — quindi T distingue
l'indicazione iniziale da quella corretta senza avere uno stato. È il caso
fortunato di cui SC05-Q3 e SC05-Q4 sono il rovescio.

**SC05-Q3 · errata, informazione obsoleta.** §3. Il fatto obbligatorio richiede
la revisione delle regole come **unica** verifica aperta: non è soddisfatto.

**SC05-Q4 · parziale, informazione obsoleta.** §3. Entrambi i fatti obbligatori
sono enunciati — la revisione delle regole da completare e il divieto di
condivisione fino alla chiusura formale — ma la risposta aggiunge il bilanciatore
fra le verifiche da completare. Classificata parziale e non errata **solo**
perché il fatto obbligatorio di Q4, a differenza di quello di Q3, non contiene
«unica». È una distinzione che regge sul testo dell'oracle ed è sottile: va
rivista prima di consolidare i criteri (§7).

**SC05-Q5 · errata (0/2), origine *retrieval*, astensione impropria.**
`SC05-S8-U1` è rango 4 con 0,0812 e resta fuori per budget; `SC05-S9-U1` ha
punteggio 0,0000. La risposta dichiara l'insufficienza e descrive correttamente
il contesto ricevuto: **nessuna affermazione non supportata**. U e GER falliscono
la stessa domanda in modo peggiore, con `unsupported_claim`: qualificano
`SC05-M031` (coordinate bancarie non coinvolte) come verifica completata.

**SC05-Q6 · completa.** Dieci giorni lavorativi, da `SC05-S2-U2`.

**SC05-Q7 · astensione corretta.** Nessun fornitore introdotto, malgrado nel
contesto compaiano i backup.

## 6. Falsi positivi di provenienza in T

Il retrieval dichiara `evidence_provenance_complete: true` su SC04-Q1, Q4, Q5, Q6
e su SC05-Q1, Q2, Q6, e in tutti questi casi il contenuto c'è davvero. Non è
merito della misura: **in T provenienza e contenuto coincidono per costruzione**,
perché l'unità recuperata è il messaggio sorgente stesso. Il campo resta
inaffidabile come indicatore di correttezza — su SC04-Q2, Q3 e su SC05-Q3, Q4, Q5
segnala infatti correttamente `false` — ma in T non può produrre il falso
positivo osservato in F, U, G e GER, dove un elemento cita il messaggio sorgente
senza esprimerne il contenuto. **Questo rende i numeri di provenienza di T non
confrontabili con quelli delle altre modalità**, e va detto ogni volta che si
mettono nella stessa tabella.

## 7. Decisioni aperte che questa valutazione lascia aperte

1. **Q3 errata contro Q4 parziale su SC05.** La differenza sta tutta nella parola
   «unica» nel fatto obbligatorio di Q3. Va deciso se l'uso di informazione
   obsoleta debba portare a `errata` per sé, indipendentemente dai fatti
   obbligatori consegnati. **Va deciso sul piano metodologico, non guardando
   quale delle due dà il numero preferito.**
2. **Dichiarazione di insufficienza su una domanda a cui il corpus permette di
   rispondere** (SC04-Q3, SC05-Q5): la questione era già dichiarata aperta in
   `valutazione_approvata_sc05.md` e resta aperta. Qui è registrata con
   `wrong_abstention` e la classe è assegnata sui fatti obbligatori consegnati.
3. **SC04-Q2**: resta aperta la scelta fra oracle attuale e criterio B
   (`evaluation_dev_sc04.md` §2.4). Non cambia il giudizio di T.
4. **Soglia sul punteggio nullo**: su SC05-Q3 e Q5 ha escluso il messaggio che
   contiene la risposta corrente. È lo stesso punto già aperto per U e GER, e ora
   è osservato anche su T.

## 8. Che cosa questa prova **non** dimostra

- Non dimostra che T sia migliore o peggiore di U, G o GER: sette domande, una
  esecuzione, nessuna replica, oracle non approvato.
- Non permette classifiche fra scenari: i risultati di T su SC04 e su SC05 non
  vanno sommati né mediati.
- Non dimostra le cause: le origini indicate sono **prime cause osservabili**
  negli artefatti, non cause dimostrate. Che con `SC05-S9-U1` nel contesto la
  risposta sarebbe stata corretta è un'ipotesi, verificabile solo con altre
  chiamate al modello.
- Non rivede i giudizi di U, G, GER e FULL_HISTORY, che restano quelli già
  registrati.
