# Progettazione della memoria gerarchica (GER)

Data: progettazione 5 settembre 2026, implementazione e correzioni 6 settembre 2026.

Stato: **Prova di sviluppo SC05 eseguita e valutata; giudizi approvati dallo studente. Protocollo finale della tesi non congelato. Prossimo passo: consolidamento delle conoscenze e confronto con il relatore.**

GER è implementata, verificata offline e provata una volta con risposte reali (SC05, 6 settembre 2026, `claude-sonnet-5`, 39 chiamate). Su quella prova GER **non ha fatto meglio di U**: 1 risposta completa su 7 contro le 2 di U, con una domanda in cui la ripartizione 50/50 ha tolto dal contesto l'evidenza decisiva. Una esecuzione, sette domande, nessuna replica: **osservazioni di sviluppo, non una conclusione sull'architettura**. L'approvazione dei giudizi è dello studente e riguarda solo questa prova: non è del relatore, non congela il protocollo, non rivede gli altri esperimenti. Questo non dichiara conclusa né RQ2 né la tesi.

Le sezioni che seguono sono la progettazione del 5 settembre, lasciata com'era; le regole applicate oggi dal codice sono quelle di `ger-rules-0.2`, più in basso.

**Tre materiali da non confondere.**

| | che cos'è | dove |
|---|---|---|
| **fixture** | dati finti scritti a mano, per far girare il codice senza chiamare il modello | `tests/fixtures/rq2/scenario_05_*` |
| **verifiche offline** | il comportamento del codice controllato sulle fixture e sugli stati salvati: nessuna risposta generata | `results/rq2/ger_dev/` (regole 0.1), `results/rq2/ger_dev_v2/` (regole 0.2) |
| **prova reale di sviluppo** | memoria costruita da Claude e 21 risposte vere | `results/rq2/sc05_dev_v1/` |

I numeri delle verifiche offline **non sono risultati**: la memoria da cui
vengono è inventata. I numeri della prova reale sono risultati di sviluppo di
una sola esecuzione.

## Obiettivo

> A parità di informazioni disponibili e di budget di contesto, separare memoria recente e archivio aiuta a continuare un'attività distribuita su conversazioni lunghe?

GER estende U, riutilizzando fatti e aggiornamenti già costruiti. Il vantaggio non è presupposto: riservare spazio alle informazioni recenti può aiutare la continuità, ma sottrarre spazio a informazioni vecchie decisive. La sigla GER evita confusione con il controllo FULL_HISTORY.

## Livelli

| Livello | Contenuto | Accesso del modello che risponde |
|---|---|---|
| Contesto corrente | Informazioni selezionate per la domanda | Direttamente nel prompt; ricostruito per ogni domanda |
| Memoria recente | Voci di U create o aggiornate nelle ultime due sessioni | Solo gli elementi recuperati entrano nel prompt |
| Archivio a lungo termine | Voci delle sessioni precedenti, con provenienza e stato temporale | Recupero esplicito prima della risposta |

Due sessioni è il valore iniziale da verificare. Memoria recente e archivio persistono mentre la conversazione avanza; il contesto corrente è una vista temporanea delle informazioni selezionate.

**Vecchio non significa superato.** Posizione nella gerarchia e validità sono proprietà distinte: una vecchia decisione può essere valida e una recente ipotesi già smentita. L'archivio a lungo termine di GER non coincide con l'archivio delle voci superate o ritirate di U.

## Arrivo di una sessione

1. La pipeline estrae i fatti e U applica gli aggiornamenti.
2. Le voci nuove o aggiornate entrano nella memoria recente.
3. Le voci che escono dalla finestra delle ultime due sessioni passano nell'archivio senza essere eliminate.
4. U continua a poter aggiornare anche informazioni archiviate: la partizione non limita le sorgenti accessibili alla gestione della memoria.

La recenza riguarda creazione o aggiornamento della voce. Recuperare una voce per rispondere non la rende automaticamente recente.

## Arrivo di una domanda

1. Applicare la politica corrente/storia di U.
2. Cercare elementi pertinenti sia nella memoria recente sia nell'archivio.
3. Comporre il contesto entro il budget.
4. Generare la risposta con il modello e le istruzioni comuni.

Nella prima versione si interrogano sempre entrambi i gruppi: non si introduce un decisore aggiuntivo che stabilisca quando consultare l'archivio. Le domande e le risposte di valutazione non aggiornano la memoria delle prove successive.

## Selezione e budget

U ordina insieme le voci ammesse. GER divide gli stessi candidati in due gruppi e ripartisce lo spazio:

- metà budget alla memoria recente e metà all'archivio;
- spazio inutilizzato disponibile all'altro gruppo;
- nessuna voce duplicata o troncata;
- conteggio dell'intero blocco di contesto, inclusi identificatori, provenienza, stato ed eventuali etichette di livello.

Mantenere TF-IDF/coseno: calcolare il ranking sull'insieme delle voci ammesse prima di dividerle nei due gruppi, evitando di cambiare anche il criterio di pertinenza. Usare per U e GER lo stesso budget e lo stesso conteggio locale, distinguendolo dai token effettivi del modello.

Ripartizione 50/50 e finestra di due sessioni sono ipotesi iniziali, non scelte validate. Prima dell'implementazione precisare in modo deterministico l'ordine del riempimento e del riutilizzo dello spazio, le parità e il comportamento quando una voce supera la quota o l'intero budget. Non ereditare silenziosamente eccezioni del retriever precedente.

## Esempio

Sessione 1: «Prima della chiusura del caso, il rapporto deve rimanere interno».

Dopo varie sessioni il vincolo passa nell'archivio. La sessione 8 contiene gli ultimi aggiornamenti sulle verifiche tecniche.

Domanda: «Quali verifiche restano da fare e possiamo già condividere il rapporto?»

La risposta richiede attività aperte dalla memoria recente e vincolo dall'archivio. La traccia deve indicare livello di provenienza, elementi selezionati, motivi della selezione e consumo del budget. Un vincolo conservato ma non recuperato è un possibile fallimento da osservare.

## Prima prova prevista

Preparare uno scenario di sviluppo di circa 8–10 sessioni con:

- una decisione lontana ancora valida;
- una vecchia informazione successivamente corretta;
- attività recenti;
- dettagli plausibili ma irrilevanti per alcune domande;
- una domanda che richieda entrambi i livelli;
- un'informazione mai fornita, per verificare l'astensione.

Confrontare U e GER sugli stessi stati salvati, alle stesse domande, con identici modello, istruzioni di risposta, informazioni accessibili e budget. FULL_HISTORY resta diagnostico e fuori dal limite di contesto recuperato.

Osservare correttezza delle risposte, uso di informazioni obsolete, evidenze realmente presenti nel contesto e spazio occupato dai livelli. La sola corrispondenza degli identificatori sorgente non dimostra la conservazione del contenuto. Controllare anche che la storia superi davvero il budget scelto e che l'archiviazione venga esercitata.

## Riferimento e perimetro

Ispirazione: [MemGPT: Towards LLMs as Operating Systems, sezioni 2.1–2.3](https://arxiv.org/html/2310.08560v2). MemGPT distingue contesto principale e memoria esterna e usa funzioni tramite cui il modello gestisce la memoria. GER propone inizialmente regole esplicite di archiviazione e selezione: adattamento semplificato, non replica di MemGPT.

Prima versione: stessa memoria U, partizione per recenza, archivio recuperabile, budget ripartito. Riassunti automatici, integrazione del grafo e scelte autonome del modello sull'archiviazione non fanno parte di questa prima progettazione.

La memoria U e il retrieval attuali hanno limiti noti; GER non li risolve automaticamente. I confronti precedenti restano separati e conservati. La priorità dello studente è comprendere e spiegare al relatore il funzionamento e le motivazioni delle scelte.

## Punto di ripresa

Per oggi fermarsi alla progettazione. Alla ripresa, leggere questo documento, verificare la versione di riferimento di U e precisare le regole di selezione ancora aperte prima di implementare. Nessuna chiamata al modello è necessaria per questa fase progettuale.

---

# Regole deterministiche di GER — versione `ger-rules-0.2`

Data: 6 settembre 2026. Restano scelte di sviluppo: parametri non tarati,
protocollo non congelato, nessuna approvazione del relatore.

## Che cosa cambia dalla `0.1`

Due comportamenti verificati in revisione, corretti prima delle prove reali.

1. **Budget rigoroso (R5).** La `0.1` faceva entrare il primo candidato anche
   quando superava da solo il budget: una voce da 240 token entrava con limite
   200. L'eccezione è stata **eliminata per GER**. Nessuna voce può far superare
   il budget, nessuna voce viene troncata, e se non entra niente il contesto
   resta vuoto.
2. **Recenza rispetto alla sessione raggiunta (R1).** La `0.1` deduceva la
   finestra dalla sessione più alta fra le voci salvate: se le ultime sessioni
   non producevano aggiornamenti, la finestra restava indietro. Ora la sessione
   raggiunta viene **passata esplicitamente** a GER.

Sugli stati usati per il confronto (SC03, SC04, SC05) le due correzioni **non
cambiano nemmeno un elemento selezionato**: nessuna voce arriva da sola a 200
token e in tutti e tre gli stati l'ultima sessione produce voci. La verifica
delle regole `0.1` resta leggibile in `results/rq2/ger_dev/`, quella della `0.2`
in `results/rq2/ger_dev_v2/`.

## Versione di riferimento di U

GER riusa **gli stati già salvati** di U, senza riestrarre fatti e senza
ricostruire aggiornamenti:

| Scenario | Stato usato | Perché |
|---|---|---|
| SC03 | `results/rq2/memory_repair_v3/scenario_03_state.json` | ultima ricostruzione con `u-instructions-0.3` e passata di riparazione |
| SC04 | `results/rq2/sc04_repair_v3/scenario_04_state.json` | idem, ed è la base dichiarata «versione di riferimento di sviluppo» nella sezione 9.6 di `RQ2.md` |
| SC05 | costruito qui dalle fixture dichiarate | scenario nuovo, nessuna prova reale |

Le prime prove (`results/rq2/memory/`, `results/rq2/graph/`) restano dov'erano e
non vengono toccate: sono state costruite con le istruzioni vecchie.

GER non tocca `build_memory_updates.py`: estrazione dei fatti, proposta delle
operazioni, rifiuto atomico e politica corrente/storia restano quelli di U. Il
codice di GER **legge** lo stato e non lo scrive mai.

## R1 — Recenza: quale sessione conta

Finestra iniziale `W = 2` sessioni. Sia `S_raggiunta` la **sessione a cui la
conversazione, o lo stato che si sta valutando, è arrivata**: una voce è
**recente** se la sua `session_order` è `>= S_raggiunta - W + 1`, altrimenti sta
in **archivio**.

`S_raggiunta` **viene passata a GER da chi lancia la valutazione**
(`--session-reached`, oppure `current_session` nel codice). Non è la sessione
più alta fra le voci salvate: se la sessione 9 non produce nessun aggiornamento,
la finestra deve comunque essere 8-9, altrimenti resta ferma indietro e
l'archivio si gonfia da solo.

Due protezioni, perché il dato è dichiarato da fuori:

- dichiarare una sessione **precedente** alle voci salvate è un errore e viene
  rifiutato: vorrebbe dire che lo stato contiene sessioni successive a quella
  dichiarata;
- se non viene dichiarata nulla, GER **ripiega** sull'ultima sessione con voci
  salvate — è il comportamento prudente, non inventa sessioni future — e lo
  scrive nella traccia come `session_reached_source: "ripiego"`, così un ripiego
  non passa per una dichiarazione.

**Stati intermedi.** Valutando lo stato dopo la sessione 3 di uno scenario da 9,
la sessione raggiunta è 3 e la finestra è 2-3: la sessione finale dello scenario
**non** viene usata automaticamente. Chi valuta uno stato intermedio lo dichiara;
la verifica offline si rifiuta di dedurlo dallo scenario quando lo stato non
copre tutte le sessioni.

La sessione raggiunta è un dato della conversazione, non della valutazione:
domande, risposte attese e sessioni future non entrano da nessuna parte.

`session_order` di una voce è la sessione dell'operazione che l'ha prodotta.
Poiché in U un UPDATE **crea una voce nuova**, «creata o aggiornata nelle ultime
due sessioni» coincide con «la voce è stata prodotta nelle ultime due sessioni»:
la versione aggiornata di un'affermazione è recente, la versione superata resta
dove sta il suo contenuto, cioè nell'archivio, con lo stato `superato` scritto
nel contesto.

Alternativa scartata: far risalire la voce superata alla sessione in cui è stata
superata. La versione vecchia diventerebbe «recente» proprio quando smette di
essere attuale, e occuperebbe la metà di budget riservata alle novità.

**Limite dichiarato.** Un DELETE marca la voce `ritirato` senza creare una voce
nuova, e lo stato salvato non registra in quale sessione sia avvenuto il ritiro.
Una voce ritirata conserva quindi la sessione in cui era stata creata. Si legge
nella traccia come `recency_basis: "creazione"`.

Regola distinta da quella di U: **posizione e validità restano separate.** Una
decisione della sessione 1 può essere `attivo` e stare in archivio; una voce
della sessione 9 può essere `superato` e stare nella memoria recente.

**Recuperare non ringiovanisce.** Il livello dipende dallo stato salvato e dalla
sessione raggiunta, non dalle domande: GER non scrive nulla, quindi la stessa
domanda ripetuta dà la stessa partizione, e una voce recuperata mille volte resta
dov'era.

## R2 — Candidati e ranking

1. Si applica la politica corrente/storia di U (`question_scope`), identica.
2. Le voci leggibili diventano elementi di contesto **come in U**, con
   un'etichetta di livello in più (R6).
3. Il TF-IDF/coseno si calcola su **tutto l'insieme dei candidati ammessi**,
   prima della divisione: la classifica e i punteggi di GER coincidono con
   quelli di U voce per voce.
4. Restano fuori gli elementi con punteggio nullo, come in U.
5. Le parità restano risolte dall'ordine di comparsa nello scenario. Il livello
   **non** entra nell'ordinamento.

## R3 — Quote

`quota_recente = budget // 2`, `quota_archivio = budget - quota_recente`. Con
budget 200: 100 e 100. Con un budget dispari il token in più va all'archivio,
così l'arrotondamento non favorisce l'ipotesi che si vuole verificare.

## R4 — Ordine di riempimento

**Fase 1, quote.** Ogni gruppo scorre la classifica globale limitata ai propri
elementi e si ferma al **primo elemento del gruppo che non entra nella propria
quota**. Dentro ciascun gruppo la selezione resta un prefisso della classifica,
come in U. I due gruppi sono indipendenti: l'esito non dipende da quale gruppo
viene servito per primo.

**Fase 2, riutilizzo.** Lo spazio non speso resta uno solo:
`residuo = budget - token già usati`. Si riscorre la classifica globale dei soli
elementi non ancora selezionati, di entrambi i livelli, e ci si ferma al primo
che non entra nel residuo. È il momento in cui un livello usa lo spazio
avanzato dall'altro.

Nessun elemento viene esaminato due volte come candidato e nessuno può essere
selezionato due volte.

## R5 — Voci troppo grandi: budget rigoroso

**Nessuna voce può far superare il budget del contesto formattato.** Non ci sono
eccezioni e non si tronca niente.

- **Voce che supera la quota del proprio livello ma non il budget:** esclusa
  dalla fase 1, può entrare in fase 2 se il residuo la contiene.
- **Voce che supera l'intero budget:** **esclusa**, con il proprio motivo nella
  traccia (`supera da sola l'intero budget: esclusa, non troncata`) e nell'elenco
  `excluded_over_budget`. Non viene troncata, non viene divisa, non entra
  «tanto per non lasciare il contesto vuoto».
- **Se non entra nessuna voce:** il contesto resta **vuoto**. Meglio un contesto
  vuoto e dichiarato che un budget sforato di nascosto.
- **Gruppo senza candidati:** la sua quota resta intera e passa all'altro in
  fase 2.

**Che cosa succede alle voci successive nella classifica.** Una voce troppo
grande si comporta come qualunque altra voce che non entra: **chiude la fase in
cui viene incontrata**, perché la selezione resta un prefisso della classifica
(R4, la regola di U). In fase 1 chiude la quota del proprio livello — l'altro
livello continua per conto suo — e in fase 2 chiude il riutilizzo per entrambi.
Se la voce troppo grande è al primo posto della classifica e il suo livello è
l'unico con candidati, il contesto resta vuoto. È una conseguenza voluta della
regola di prefisso, non un caso non trattato: se un giorno si decide di saltare
gli elementi che non entrano invece di fermarsi, la decisione va presa **per U e
GER insieme**, altrimenti il confronto non è più a parità di regole.

**L'eccezione residua di U.** `select_within_budget()` in `rq2_common.py`
conserva la propria garanzia minima: se il primo elemento supera da solo il
budget entra lo stesso, marcato `budget_exceeded_by_first_item`. Non è stata
toccata, per non cambiare i risultati già prodotti da T, F, U e G. Un test
verifica che su **tutti** i casi usati per confrontare U e GER (SC03, SC04, SC05,
7 domande ciascuno) quell'eccezione **non si attivi mai**: nessuna voce di
memoria arriva da sola a 200 token, quindi il confronto avviene a regole uguali.
La verifica offline lo controlla di nuovo a ogni esecuzione.

## R6 — Che cosa viene contato

La riga di GER è quella di U con l'etichetta di livello in più:

```
[SC05-M004 | recente | attivo | da: SC05-S8-U1] la verifica dei backup è completata
```

L'etichetta costa circa 2 token per elemento e **rientra nel budget**, come
identificatori, provenienza e stato. È un costo dell'architettura, non un
dettaglio di presentazione: senza etichetta la gerarchia sarebbe invisibile al
modello e GER differirebbe da U solo per quali elementi entrano.

Gli elementi vengono scritti nel prompt **in ordine di classifica**, non
raggruppati per livello: così l'unica differenza rispetto a U resta la
selezione più l'etichetta, e non anche l'ordine di lettura.

Budget, metodo di conteggio, istruzioni di risposta e testo delle domande
restano identici a quelli di U. FULL_HISTORY resta fuori dal budget, come
controllo diagnostico.

## R7 — Che cosa la traccia deve registrare

Per ogni domanda: sessione raggiunta e da dove arriva, finestra recente, ambito
di lettura, dimensione dei due gruppi, quote, token spesi per livello, residuo
riutilizzato, voci escluse perché più grandi dell'intero budget, e per ogni
candidato ammesso identificatore, livello, punteggio, rango, token, esito
(`fase 1`, `fase 2`, escluso) e motivo dell'esclusione.

**La provenienza non è una prova.** Come già per U e G, un elemento che cita il
`message_id` giusto non dimostra che il contenuto necessario sia nel contesto:
i giudizi di contenuto restano da leggere a mano.

## Che cosa resta aperto

`W = 2`, la ripartizione 50/50, la soglia sul punteggio nullo e il budget di 200
token restano ipotesi non tarate. GER non risolve i limiti noti di U e del
retrieval elencati nella sezione 10 di `RQ2.md`: li eredita.

**GER può fare peggio di U** e questo non sarebbe un guasto: riservare metà
budget all'archivio toglie spazio alle novità e viceversa. È esattamente ciò che
il confronto deve misurare.

---

# Che cosa è stato implementato (6 settembre 2026)

Codice, dati e verifiche esistono; **nessuna prova reale è stata eseguita** e
nessun modello è stato chiamato.

| File | Ruolo |
|---|---|
| `scripts/rq2/hierarchical_memory.py` | GER: livello di una voce, elementi di contesto, quote, riempimento in due fasi, traccia |
| `scripts/rq2/run_retrieval_rq2.py` | ramo `GER` aggiunto accanto a T, F, U e G |
| `scripts/rq2/run_ger_check.py` | verifica offline U/GER, senza chiamate al modello |
| `data/rq2/scenarios/scenario_05.json` | scenario di sviluppo, 9 sessioni |
| `data/rq2/annotations/scenario_05_rq2.json` | 7 domande, **bozza da rivedere** |
| `tests/fixtures/rq2/scenario_05_*` | fixture dichiarate: fatti candidati e risposte finte del costruttore di U |
| `tests/test_rq2_ger.py` | proprietà essenziali e controlli di non regressione |
| `results/rq2/ger_dev/` | verifica delle regole `0.1`, conservata come riferimento |
| `results/rq2/ger_dev_v2/` | verifica delle regole `0.2`, quella corrente |

**GER sta fuori dalla matrice della roadmap.** `scenario_05` non è in
`SCENARIO_IDS` e `GER` non è in `matrix`: validatore della roadmap, verifica
offline della matrice, conteggio delle 77 celle e confronti T/F, F/U, U/G
restano identici. GER gira solo chiedendola:

```bash
python3 scripts/rq2/run_ger_check.py
```

**Aggiornamento dell'8 settembre 2026.** GER è ora dichiarata fra le `modes` di
`experiment_rq2.json` e SC05 compare nel blocco **`matrix_extension`**, che è la
matrice estesa dei confronti (RQ2.md, sezione 12): la riga di SC05 diventa
`T / U / GER` con FULL_HISTORY come controllo diagnostico. È una dichiarazione,
non un cambio di comportamento: `matrix` resta la matrice della roadmap, le 77
celle non cambiano, gli script continuano a ricevere le modalità con `--modes` e
le regole, le quote e il budget di GER restano `ger-rules-0.2`. La prova
`results/rq2/sc05_dev_v1/` resta valida così com'è: T non tocca né lo stato di U
né la selezione di GER, e si affianca come baseline dentro lo stesso scenario.

## Che cosa mostrano le verifiche

**Correttezza tecnica, verificata** (regole `0.2`, 21 prove GER su tre stati):
quote rispettate, spazio riutilizzato in 8 prove su 21, nessun doppione, nessun
troncamento, **budget mai superato e nessuna eccezione sul primo elemento**,
sessione raggiunta sempre dichiarata, punteggi identici a quelli di U, stessa
politica di lettura e stesse voci leggibili, stati salvati invariati dopo il
retrieval. L'eccezione residua di U non si attiva in nessuno dei casi di
confronto.

**Beneficio sperimentale: non deciso da queste verifiche.** Qui nessuna risposta
è stata generata — le risposte vere sono arrivate dopo, con la prova su SC05, ed
è quella che va letta per il merito. Le verifiche offline mostrano soltanto i
costi della partizione: a parità di budget GER porta meno contenuto di U
(l'etichetta di livello costa circa due token per elemento), su SC03 perde
copertura di provenienza in due domande su sette, e sulle fixture di SC05 la
soglia sul punteggio nullo lascia inutilizzata l'intera quota recente in una
domanda — cosa che nella prova reale si è ripresentata. Il dettaglio è in
`results/rq2/ger_dev_v2/README.md`.

## Prima prova reale: eseguita il 6 settembre 2026

La prima prova reale di sviluppo **U / GER / FULL_HISTORY su SC05** è stata
eseguita con `claude-sonnet-5`: **39 chiamate** (9 estrazione + 9 aggiornamento +
0 riparazioni + 21 risposte), nessun errore, nessuna operazione rifiutata.

**Successo tecnico pieno, nessun vantaggio di GER.** Giudizi proposti: U 2
risposte complete su 7, GER 1, FULL_HISTORY 6 — ma FULL_HISTORY riceve 645 token
di cronologia contro i 200 selezionati, quindi è un **controllo diagnostico**,
non un confronto a parità di budget. Nessuna delle 21 risposte usa informazione
obsoleta, e in sei domande su sette non avrebbe potuto: la politica di lettura
rende le voci superate accessibili solo alle domande storiche.

Su **SC05-Q2** GER fa peggio di U per una ragione leggibile nella traccia: la
quota dell'archivio (100 token) ha tenuto due voci per 83 token e la terza, la
sola che identifica SRV-14 come server esposto corretto, ne chiedeva 37; la metà
riservata alla memoria recente aveva intanto speso 93 token in voci estranee alla
domanda. U, con un budget unico da 200, la prende e chiude a 177 token.

I giudizi sulle 21 risposte sono **approvati dallo studente**:
`results/rq2/sc05_dev_v1/valutazione_approvata_sc05.md`, con la copia compilata
in `annotation_compilata_sc05.jsonl` e il template originale lasciato intatto.

| | |
|---|---|
| configurazione | `data/rq2/config/run_sc05_ger_dev.json` (`sc05-ger-dev-1`), verificata da un test |
| comandi e taccuino | `results/rq2/sc05_dev_v1/README.md` |
| revisione delle domande e proposte | `data/rq2/annotations/scenario_05_proposte_di_revisione.md` |
| chiamate effettive | 9 estrazione + 9 aggiornamento + 0 riparazioni + 21 risposte = **39** |
| valutazione assistita | `results/rq2/sc05_dev_v1/valutazione_assistita_sc05.md` (proposte, non approvate) |

La memoria usata nella prova è quella **costruita da Claude** in
`results/rq2/sc05_dev_v1/memory/`. Le fixture restano quello che erano — dati
finti per le verifiche offline di `ger_dev/` e `ger_dev_v2/` — e non vanno
confuse con questa.

## Punto di ripresa

**Prova di sviluppo SC05 eseguita e valutata; giudizi approvati dallo studente. Protocollo finale della tesi non congelato. Prossimo passo: consolidamento delle conoscenze e confronto con il relatore.**

La valutazione è chiusa: i giudizi sono approvati e i conteggi verificati riga
per riga. Il materiale da portare al relatore parte da
`results/rq2/sc05_dev_v1/chiusura_prova_sc05.md` e
`valutazione_approvata_sc05.md`. **Le attività sperimentali si fermano qui.**

Non servono altre esecuzioni per chiudere questa prova. Restano aperte, per
dopo, le stesse questioni di prima — soglia sul punteggio nullo, finestra di due
sessioni, ripartizione 50/50, etichetta di livello, e se la regola di arresto sul
primo elemento che non entra debba cambiare **per U e per GER insieme** — più
quelle che la prova ha aggiunto: che cosa fare quando un UPDATE sostituisce un
obiettivo con il suo compimento, e il fatto che `DELETE` non è stato usato
nemmeno qui. Il protocollo resta non congelato e nulla di tutto questo è
approvato dal relatore.
