# RQ4 / SC05 — protocollo del passaggio tra modelli

**Stato:** disegno sperimentale fissato il 23 settembre 2026. Nessuna nuova chiamata ai modelli è stata eseguita per RQ4.

## Domanda di ricerca

**RQ4:** quando il modello generativo viene sostituito, l'accesso alla memoria esterna accumulata prima del passaggio permette al nuovo modello di continuare il lavoro rispettando obiettivi, correzioni, vincoli e stato delle attività?

L'esperimento usa SC05 e colloca il passaggio fra le sessioni 5 e 6:

- **fase A, sessioni 1–5:** Claude Sonnet 5 Chat è il modello precedente;
- **fase B, sessioni 6–9 e domande finali:** il nuovo modello è, in due repliche separate, Gemma 3 4B IT oppure Llama 3.2 3B Instruct.

La variabile principale è la memoria disponibile al modello B. Ogni replica confronta gli stessi input e lo stesso modello B in due condizioni:

1. **separata:** il retriever può cercare soltanto nei messaggi delle sessioni 6–9;
2. **condivisa:** il retriever può cercare nei messaggi delle sessioni 1–9, includendo quindi la storia accumulata durante la fase A.

## Significato del passaggio

RQ4 valuta la **portabilità della memoria esterna quando cambia il generatore di risposta**. Turn-level RAG indicizza soltanto i messaggi dell'utente, considerati fonte autorevole. Le risposte intermedie dell'assistente non vengono indicizzate e non introducono nuovi fatti.

Di conseguenza non servono nuove generazioni di Claude per le sessioni 1–5: quelle sessioni definiscono la storia precedente al passaggio. L'identità del modello A non modifica il contenuto della memoria, che resta esterno e basato sui messaggi dell'utente. Il risultato non misura come Claude scrive o riassume la memoria; misura se due nuovi modelli riescono a usare la stessa memoria precedente.

Questo confine deve essere dichiarato nella tesi: si tratta di un passaggio controllato del generatore sopra una memoria esterna, non del trasferimento di uno stato interno nascosto fra modelli.

## Materiale sperimentale congelato

Si riusano, in sola lettura:

- `data/rq2/scenarios/scenario_05.json`, SHA-256 `be57e57c4c133dda015d6c955cef59058f514e896dde9a94e50e0b85e87bc0fa`;
- `data/rq2/annotations/scenario_05_rq2.json`, SHA-256 `454be8c6c7a7bc17bce349a356aa872075bf8dc27ca600d2ff0ba7d51f67e3a8`.
- `data/rq3/config/rq5_sc06_v1_1.json`, usato soltanto come riferimento congelato per modelli e runtime, SHA-256 `01662ccb0980ae24552b91942663cffe97b390ded23f74ccdd9d3946d4debc14`.

RQ4 non modifica gli artefatti o i risultati di RQ2. Copia nei propri manifest gli hash, gli identificatori delle sessioni e le regole di valutazione usate.

SC05 contiene nove sessioni sul caso `ARD-19`. Fra le informazioni rilevanti:

- obiettivo e vincolo di riservatezza nella sessione 1;
- scadenza richiesta dal cliente nella sessione 2;
- indicazione iniziale `SRV-12` e correzione in `SRV-14` entro la sessione 4;
- ritiro dell'evidenza `export_fornitori.csv` nella sessione 5;
- aggiornamenti, verifiche e chiusure nelle sessioni 6–9.

## Domande

Si riusano le sette domande già annotate di SC05, senza riscriverle dopo il retrieval:

| Gruppo | Domande | Ruolo in RQ4 |
|---|---|---|
| Dipendenti dal passaggio | Q1, Q2, Q4, Q6 | richiedono almeno un fatto delle sessioni 1–5 |
| Controlli successivi al passaggio | Q3, Q5 | richiedono fatti delle sessioni 6–9 |
| Informazione assente | Q7 | richiede astensione in entrambe le condizioni |

Q4 è la domanda centrale: combina una verifica ancora aperta nella sessione 9 con il vincolo di riservatezza stabilito nella sessione 1.

## Turn-level RAG

L'unità recuperabile è il singolo messaggio utente. Si riusa senza taratura successiva il retriever elementare del progetto:

- TF-IDF con similarità del coseno;
- tokenizzazione in minuscolo che conserva parole, numeri, trattini e underscore;
- query uguale al testo della domanda;
- messaggi con punteggio nullo esclusi;
- ordine deterministico a parità di punteggio;
- budget massimo del contesto: 200 token secondo il conteggio deterministico già usato in RQ2;
- nessun troncamento del singolo messaggio.

Il metodo e il budget restano identici nelle due condizioni e per entrambi i modelli B. Cambia soltanto il corpus accessibile: sessioni 6–9 oppure sessioni 1–9.

La configurazione è intenzionalmente conservativa: su SC05 sono già noti limiti lessicali del TF-IDF. Non vengono corretti dopo aver osservato le prove precedenti. Per ogni domanda si conservano separatamente:

- evidenza richiesta dall'oracle;
- evidenza raggiungibile nel corpus della condizione;
- messaggi effettivamente recuperati;
- copertura del contenuto richiesto nel contesto finale;
- risposta del modello B.

Un'informazione disponibile ma non recuperata è un errore di retrieval; un'informazione recuperata ma usata male è un errore di generazione. Le due cause non devono essere fuse.

## Modelli B e generazione

Le due repliche usano le stesse copie locali già congelate per RQ5:

| Modello B | Tag Ollama | Digest | Quantizzazione |
|---|---|---|---|
| Gemma 3 4B IT | `gemma3:4b` | `a2af6cc3eb7fa8be8504abaf9b04e88f17a119ec3f04a3addf55f92841195f5a` | Q4_K_M |
| Llama 3.2 3B Instruct | `llama3.2:3b` | `a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72` | Q4_K_M |

Runtime: Ollama 0.34.2, un modello caricato alla volta, temperatura 0, seed 42, finestra 4.096 token e massimo 128 token in uscita. Prima di ciascun modello si eseguono tre richieste di riscaldamento escluse dai risultati.

Il modello riceve soltanto contesto recuperato e domanda. L'output richiesto è:

```json
{"status": "answered", "answer": "testo della risposta"}
```

oppure, quando il contesto non consente di rispondere completamente:

```json
{"status": "insufficient", "answer": "eventuali informazioni supportate, senza completare con supposizioni"}
```

Una sola generazione viene effettuata per modello B, condizione e domanda. Se, per lo stesso modello B, due celle hanno prompt e configurazione identici, la risposta viene generata una volta e riutilizzata con provenienza esplicita. Il riuso non può avvenire fra Gemma e Llama.

## Numero di celle

| Modelli B | Condizioni | Domande | Celle finali |
|---:|---:|---:|---:|
| 2 | 2 | 7 | 28 |

Il numero effettivo di chiamate può essere inferiore a 28 soltanto per prompt identici all'interno dello stesso modello. Il conteggio deve essere calcolato e congelato offline prima delle generazioni.

Poiché Gemma e Llama sono già stati eseguiti e verificati nella pipeline RQ5, RQ4 non usa SC05 per tarare prompt o criteri dopo le risposte. Prima della valutazione sono ammessi soltanto test offline e un eventuale smoke test su fixture esclusa da SC05, uno per modello.

## Valutazione condizionata all'evidenza

La valutazione non usa un modello giudice. Le classificazioni sono prodotte come proposta strutturata e devono essere riviste dallo studente leggendo risposta, contesto e oracle.

Classi principali:

- **completa e supportata:** tutti i fatti obbligatori accessibili e richiesti sono riportati correttamente;
- **parziale:** almeno un fatto obbligatorio è corretto, ma ne manca un altro accessibile;
- **errata:** contiene una contraddizione, usa un fatto obsoleto come attuale o fallisce nonostante l'evidenza sufficiente;
- **insufficienza riconosciuta:** dichiara correttamente che il contesto non permette una risposta completa e non inventa;
- **affermazione non supportata:** introduce un fatto non presente nel contesto.

L'attesa dipende dalla condizione e dalla copertura del contesto:

- nella memoria condivisa, le domande dipendenti dal passaggio devono poter essere complete quando il retriever recupera tutte le evidenze;
- nella memoria separata, Q1, Q2 e Q6 non hanno evidenze delle sessioni 1–5: il comportamento corretto è riconoscere l'insufficienza;
- nella memoria separata, Q4 può avere la parte recente ma non il vincolo della sessione 1: il modello deve evitare di inventare la risposta mancante;
- Q3 e Q5 controllano che il modello B sappia usare le informazioni successive al passaggio;
- Q7 richiede astensione in entrambe le condizioni.

Metriche e conteggi, sempre separati per Gemma e Llama:

- copertura delle evidenze nel corpus accessibile;
- copertura delle evidenze nel contesto recuperato;
- risposte complete e supportate;
- insufficienze riconosciute correttamente;
- risposte parziali ed errate;
- uso di informazioni obsolete;
- affermazioni non supportate;
- confronto appaiato domanda per domanda fra memoria condivisa e separata.

La metrica centrale è il comportamento sulle quattro domande dipendenti dal passaggio. Q3, Q5 e Q7 sono controlli e non devono essere mescolate in un unico punteggio senza mostrare i denominatori.

Gemma e Llama vengono riportati separatamente. L'eventuale confronto fra i due modelli B è secondario e descrittivo: RQ4 non sostituisce RQ5 e non produce una classifica generale.

## Limiti e interpretazione ammessa

RQ4 è un caso di studio controllato su un solo scenario. Può mostrare se, in SC05 e con questa configurazione, la memoria precedente rende possibile la continuità dopo il cambio di generatore. Non dimostra che ogni modello possa sostituirne un altro in qualunque attività.

Il passaggio riguarda memoria esterna esplicita, non pesi, cache, stato latente o ragionamento interno di Claude. I messaggi e le domande di SC05 sono costruiti, non conversazioni aziendali reali. Una sola generazione per cella non misura la variabilità stocastica.

Un risultato nullo o negativo resta valido: può indicare che l'evidenza non è stata recuperata oppure che il nuovo modello non l'ha usata correttamente. La diagnosi deve indicare quale dei due livelli ha fallito.

## Gate prima delle chiamate

Prima di qualsiasi chiamata reale devono risultare verificati:

1. hash immutati di scenario, annotazioni, retriever e configurazione dei modelli;
2. 28 celle attese, tutte uniche;
3. perimetri separato e condiviso ricostruiti correttamente;
4. oracle assente da retrieval, richieste e generazione;
5. prompt identici fra modelli nella stessa condizione e domanda, salvo il tag tecnico esterno;
6. piano di riuso basato soltanto su prompt e configurazione;
7. digest locali dei due modelli uguali a quelli dichiarati;
8. test offline e dry-run completati;
9. nessuna modifica agli artefatti RQ1, RQ2, RQ3 o RQ5.

Gli artefatti di RQ4 devono vivere esclusivamente sotto `data/rq4`, `scripts/rq4`, `tests` con nomi RQ4 e `results/rq4`.
