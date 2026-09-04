# Roadmap del progetto di tirocinio

**Aggiornamento:** 4 settembre 2026, dopo il confronto con il relatore.

**Direzione concordata:** organizzare il progetto intorno a due domande di ricerca complementari: **Quanto** influisce il perimetro della memoria e **Come** cambia il comportamento quando la stessa memoria viene organizzata con architetture differenti. La prima domanda è stata affrontata nel pilot preliminare; la seconda guida l'esperimento principale con scenari cybersecurity più articolati. `FULL_HISTORY` accompagna tutti gli scenari dell'esperimento principale come controllo diagnostico.

**Stato:** RQ1 affrontata nel pilot preliminare, eseguito, valutato e analizzato; confronto con il relatore avvenuto; esperimento principale per RQ2 progettato a livello di roadmap, da costruire e validare. L'aggiornamento di questo documento non costituisce un congelamento del protocollo né l'esecuzione delle nuove prove.

## 1. Principio guida

Il progetto parte dalle domande sperimentali, dai risultati da osservare e dai criteri di valutazione. L'architettura e il codice servono a rendere quei confronti eseguibili.

L'obiettivo resta un lavoro piccolo, riproducibile e interpretabile, del quale sia possibile spiegare:

- problema e motivazione;
- condizioni e architetture confrontate;
- variabili controllate;
- funzionamento della pipeline;
- significato delle metriche;
- origine degli errori;
- limiti delle conclusioni.

La cybersecurity fornisce scenari concreti per studiare continuità, aggiornamenti e collegamenti tra conversazioni. Le risposte devono essere ricavabili dalle evidenze dello scenario: la conoscenza generale del modello sui malware non è l'oggetto della valutazione.

Il perimetro software comprende caricamento degli scenari, costruzione e gestione della memoria, retrieval, generazione, valutazione e salvataggio delle tracce. Interfacce, deployment, database complessi, sistemi multi-agente e addestramento di nuovi modelli restano fuori dal lavoro previsto.

### Le due domande del progetto

| Domanda | Parola chiave | Aspetto che cambia | Fase che la affronta |
|---|---|---|---|
| RQ1 | **Quanto** | Perimetro della memoria: C0, C1 e C2 | Pilot preliminare |
| RQ2 | **Come** | Organizzazione della memoria: T, F, U e G | Esperimento principale |

Le due domande appartengono allo stesso progetto e vengono affrontate sperimentalmente. RQ1 misura l'effetto della quantità di memoria accessibile; RQ2 mantiene disponibili le stesse sessioni e confronta il modo in cui le informazioni vengono conservate, aggiornate e recuperate.

## 2. RQ1 - Quanto influisce il perimetro della memoria?

### Domanda di ricerca

> In che misura il perimetro della memoria accessibile influenza la capacità di un LLM di continuare correttamente un'attività distribuita tra più conversazioni?

### Disegno e stato acquisiti

Il pilot contiene due scenari, Asteria Docs e Lumen Market, ciascuno con quattro sessioni, sette domande e oracle manuale. Le condizioni principali sono:

| Condizione | Informazioni accessibili |
|---|---|
| C0 - Nessuna memoria | Soltanto la domanda corrente |
| C1 - Memoria locale | Messaggi della sessione corrente |
| C2 - Memoria condivisa | Messaggi di tutte le sessioni dello scenario |

C1 e C2 applicano lo stesso Turn-level RAG: messaggi utente, TF-IDF, similarità coseno e `top-k=2`. Cambia il corpus accessibile. `FULL_HISTORY` riceve tutti i messaggi utente dello scenario in ordine cronologico, senza retrieval.

Sono disponibili 42 esecuzioni di retrieval, 56 risposte generate, le relative annotazioni, le metriche e l'analisi causale dei due fallimenti. I dry run manuali precedenti restano distinti dalle esecuzioni automatiche.

Il pilot costituisce la prova preliminare della metodologia e fornisce le prime evidenze per RQ1. Ha permesso di validare dataset, oracle, pipeline, metriche e classificazione causale degli errori prima di affrontare il confronto architetturale.

Scenari, oracle, configurazioni, risposte e analisi già prodotti devono rimanere identificabili nella loro versione originale. Le 56 risposte del pilot non entrano nelle medie o nei confronti dell'esperimento principale, perché rispondono a RQ1 con un protocollo differente. Nella tesi il pilot viene presentato in forma sintetica come prima fase sperimentale e come motivazione delle scelte successive.

## 3. RQ2 - Come viene organizzata la memoria?

### Domanda di ricerca dell'esperimento principale

> Come cambia la capacità di un LLM di continuare correttamente un'attività distribuita tra più conversazioni quando, a parità di informazioni accessibili, la memoria viene organizzata e gestita attraverso architetture differenti?

L'esperimento principale mantiene per tutte le architetture il perimetro condiviso, equivalente a C2. La matrice assegna a ogni scenario soltanto le architetture utili per il fenomeno osservato:

1. **Continuità con i messaggi originali:** Turn-level RAG su SC01, con FULL_HISTORY come supporto.
2. **Rappresentazione:** confronto diretto tra Turn-level RAG e Fact-based RAG su SC02.
3. **Gestione:** confronto diretto tra Fact-based RAG e Fact-based con aggiornamenti su SC03.
4. **Relazioni:** confronto diretto tra Fact-based con aggiornamenti e Graph memory su SC04.

C0, C1 e C2 descrivono il perimetro studiato nel pilot preliminare. Le sigle T, F, U e G identificano le architetture dell'unico esperimento principale. Non si moltiplica ogni architettura per tutte le condizioni del pilot.

### Architetture previste

| Sigla | Architettura | Elemento distintivo |
|---|---|---|
| T | Turn-level RAG | Conserva e recupera i messaggi originali |
| F | Fact-based RAG | Estrae e recupera fatti brevi, conservando la provenienza |
| U | Fact-based con aggiornamenti | Gestisce i fatti tramite ADD, UPDATE, DELETE e NOOP |
| G | Graph memory | Organizza gli stessi fatti aggiornati come entità e relazioni e recupera collegamenti pertinenti |
| H | FULL_HISTORY | Controllo diagnostico comune con tutti i messaggi originali ammessi |

### Matrice dei confronti

Le architetture vengono assegnate agli scenari prima delle esecuzioni finali, in base al fenomeno studiato.

| Scenario | T | F | U | G | H |
|---|:---:|:---:|:---:|:---:|:---:|
| SC01 - Asteria Docs | sì | - | - | - | sì |
| SC02 - Lumen Market | sì | sì | - | - | sì |
| SC03 - Infezione malware | - | sì | sì | - | sì |
| SC04 - Campagna di smishing | - | - | sì | sì | sì |

Questa matrice utilizza T su SC01 e SC02, F su SC02 e SC03, U su SC03 e SC04 e G soltanto su SC04. Forma una catena di confronti diretti sulle stesse domande: T/F in SC02, F/U in SC03 e U/G in SC04. SC01 osserva il Turn-level RAG già costruito con il supporto di FULL_HISTORY.

La catena permette di attribuire ogni confronto a un passaggio preciso: dai messaggi ai fatti, dai fatti statici ai fatti aggiornabili e dai fatti aggiornabili al grafo. Non si costruisce comunque una classifica generale usando medie su scenari differenti: le conclusioni derivano dalle prove abbinate all'interno di ciascuno scenario.

Il confronto U/G è uno studio esplorativo su SC04. Una sua eventuale estensione a un secondo scenario richiederebbe un nuovo passo dichiarato, senza modificare il benchmark finale in risposta ai risultati.

### Dimensione prevista

Con sette domande per scenario e una generazione per ciascuna cella prevista:

| Scenario | Calcolo | Generazioni |
|---|---|---:|
| SC01 | 7 domande × 2 modalità | 14 |
| SC02 | 7 domande × 3 modalità | 21 |
| SC03 | 7 domande × 3 modalità | 21 |
| SC04 | 7 domande × 3 modalità | 21 |
| **Totale esperimento principale** | | **77** |

Le 77 prove includono 28 generazioni FULL_HISTORY. Non includono le 56 risposte del pilot preliminare, i dry run, le chiamate per costruire la memoria o eventuali repliche. Il piano delle repliche, se previste, va fissato prima delle esecuzioni finali; una singola esecuzione per cella non misura la variabilità del generatore.

## 4. Dataset cybersecurity

Si conservano SC01 e SC02 e si aggiungono due scenari. La struttura iniziale resta di quattro sessioni e sette domande per scenario, con identificatori stabili per messaggi, fatti e domande.

Le nuove conversazioni devono contenere evidenze distribuite, aggiornamenti e collegamenti reali tra sessioni. L'ultima sessione non deve ripetere tutta la storia. La difficoltà deve derivare dall'uso della memoria e le domande devono avere risposte verificabili nell'oracle.

### SC03 - Diagnosi progressiva di un'infezione malware

**Fenomeno principale:** distinguere sintomi, ipotesi iniziali, diagnosi confermata e stato delle attività.

Traccia narrativa da sviluppare:

1. Segnalazione di sintomi e formulazione esplicita di un'ipotesi iniziale di ransomware.
2. Nuove evidenze portano a rivedere l'ipotesi verso un infostealer.
3. Un esito di analisi dichiarato nello scenario conferma la classificazione; vengono registrate le azioni di contenimento completate.
4. Aggiornamento sulle verifiche ancora pendenti, vincolo locale del rapporto e un'informazione rimasta sconosciuta, per esempio il vettore iniziale dell'infezione.

La classificazione finale deve essere fornita dalle evidenze del caso. Sintomi generici o assenza di cifratura, da soli, non vengono trattati come prova sufficiente per identificare o escludere una famiglia di malware. Eventuali nomi di famiglie possono essere sintetici e non richiedere conoscenze esterne.

Lo scenario confronta F e U, con FULL_HISTORY come supporto. Deve contenere aggiornamenti riconoscibili e, dove narrativamente appropriato, conferme duplicate o informazioni ritirate, così da valutare anche NOOP e DELETE. Il significato delle operazioni viene annotato prima dell'esecuzione. In questo modo si può misurare direttamente l'effetto della gestione degli aggiornamenti rispetto agli stessi fatti conservati senza operazioni di stato.

### SC04 - Campagna di smishing e social engineering

**Fenomeno principale:** ricostruire relazioni distribuite tra messaggi, persone, account ed eventi.

Traccia narrativa da sviluppare:

1. Un dipendente segnala un SMS che imita un servizio di consegna.
2. Le verifiche documentano il collegamento a una pagina falsa e confermano la classificazione come smishing.
3. Vengono registrati l'account coinvolto, un accesso anomalo e una modifica successiva, per esempio una regola di inoltro.
4. Si aggiorna lo stato delle azioni e si collega la segnalazione iniziale agli eventi successivi, lasciando almeno un fatto non determinato.

Relazioni esemplificative:

```text
SMS -> contiene -> URL
dipendente -> ha aperto -> URL
dipendente -> usa -> account
account -> coinvolto in -> accesso anomalo
account -> presenta -> regola di inoltro
```

Lo scenario confronta U e G, con FULL_HISTORY come supporto. Deve contenere sia almeno un aggiornamento o fatto obsoleto sia relazioni distribuite tra più sessioni. U e G partono dagli stessi fatti e dallo stesso stato aggiornato; G aggiunge l'organizzazione in entità e relazioni. Le domande relazionali devono richiedere fatti distribuiti, senza inserire nel testo della domanda la catena già risolta. Ransomware, infostealer e worm sono possibili contenuti relativi al malware; phishing, smishing e social engineering descrivono tecniche o modalità dell'attacco e non vanno confusi con famiglie di malware.

## 5. Oracle e confronto equo

Per ogni domanda si annotano risposta attesa, fatti obbligatori, messaggi sorgente, informazioni obsolete, eventuali relazioni necessarie e comportamento corretto in assenza di evidenze.

L'oracle dell'esperimento principale deve identificare i fatti richiesti indipendentemente dall'architettura. Un messaggio, un fatto estratto o un insieme di archi possono esprimere la stessa evidenza. Il collegamento a un messaggio sorgente non basta, da solo, a dimostrare che un fatto estratto ne conservi il contenuto corretto.

Per U si aggiungono lo stato atteso dopo gli aggiornamenti e le operazioni attese. Per G si annotano relazioni e percorsi accettabili quando richiesti dalla domanda. Le annotazioni servono alla valutazione e non entrano nell'estrazione, nel retrieval o nel prompt di risposta.

Tra le architetture confrontate rimangono uguali:

- scenario, ordine dei messaggi e punto temporale della domanda;
- informazioni sorgente accessibili;
- modello di risposta, prompt comune e parametri di generazione;
- criteri di valutazione e stato iniziale delle prove;
- budget massimo del contesto recuperato, espresso in token.

Il modello comune del progetto è **Claude Sonnet 5**. Viene usato per generare le risposte in tutte le modalità T, F, U, G e FULL_HISTORY. Se la costruzione di fatti, operazioni o relazioni richiede un LLM, viene utilizzato ancora Claude Sonnet 5 con prompt specifici fissati per ciascun ruolo; le chiamate di scrittura della memoria restano distinte dalle chiamate di risposta. La valutazione finale continua a usare l'oracle e il controllo manuale, non Claude come giudice.

Due messaggi e due fatti brevi non hanno necessariamente lo stesso contenuto informativo. Nell'esperimento principale il solo `top-k=2` non costituisce quindi un controllo sufficiente del budget: si definiscono prima delle prove finali un limite di token e una regola deterministica di selezione. Il numero di elementi e i token effettivi vengono comunque registrati. FULL_HISTORY resta fuori da questo limite perché il suo ruolo è fornire l'intera cronologia ammessa.

Per T, F e U si mantiene inizialmente lo stesso metodo di ranking TF-IDF/coseno, per isolare rappresentazione e gestione. G aggiunge una procedura esplicita di recupero relazionale; questo confronto riguarda tale differenza architetturale. Parametri, gestione degli elementi che superano il budget e criterio di arresto vanno fissati nel protocollo.

La memoria viene costruita in ordine cronologico. L'estrattore non riceve domande di valutazione, oracle o sessioni future. Le risposte alle domande non aggiornano la memoria delle prove successive.

## 6. Architettura minima

### Pipeline comune

```text
conversazioni dello scenario
-> costruzione della memoria T / F / U / G
-> retrieval entro il budget
-> contesto con provenienza delle evidenze
-> risposta del modello
-> valutazione e analisi degli errori
```

FULL_HISTORY segue un percorso separato: messaggi originali ammessi, in ordine cronologico, poi lo stesso modello di risposta e la stessa valutazione, senza selezione tramite retrieval.

### F - Fatti con provenienza

Un estrattore produce fatti brevi con identificatore, testo, messaggi sorgente e ordine temporale. Le ipotesi devono restare distinguibili dalle conferme e le negazioni devono essere conservate.

Modello e prompt di estrazione vengono fissati e le uscite automatiche vengono salvate. Eventuali errori non vengono corretti manualmente negli output finali: si registrano e si valutano. I fatti annotati manualmente costituiscono l'oracle, non l'input nascosto del sistema.

### U - Fatti e operazioni di aggiornamento

U parte dagli stessi fatti candidati usati da F e applica una politica esplicita:

- **ADD:** aggiunge una nuova informazione;
- **UPDATE:** sostituisce o aggiorna un fatto precedente riferito allo stesso oggetto e ambito;
- **DELETE:** rende inattiva un'informazione ritirata senza sostituzione;
- **NOOP:** lascia invariata la memoria, per esempio davanti a una conferma equivalente.

Le operazioni e i relativi identificatori vengono salvati. I fatti superati restano nell'archivio con stato e collegamento alla versione successiva, per rendere verificabile l'evoluzione della memoria.

La politica di lettura deve distinguere domande sullo stato corrente da domande storiche o sui cambiamenti. Queste ultime devono poter recuperare anche i fatti superati con lo stato esplicito: alcune domande esistenti chiedono sia la decisione corrente sia quella precedente. La regola di accesso allo storico viene definita prima della valutazione.

### G - Entità e relazioni

La prima versione può usare nodi e archi salvati in JSON, senza database dedicato. Ogni relazione conserva le evidenze sorgente. Il recupero individua nodi iniziali pertinenti e segue un numero limitato e dichiarato di collegamenti, entro il budget comune.

Su SC04, U e G condividono i fatti candidati e le operazioni di aggiornamento. G aggiunge la trasformazione in entità e relazioni; tutte le trasformazioni vengono registrate, così da distinguere un errore di aggiornamento, di costruzione del grafo o di recupero.

## 7. Metriche e diagnosi

Si mantengono le classi della risposta e gli indicatori del pilot: completa, parziale, errata, astensione corretta, uso di informazioni obsolete e affermazioni non supportate. La raggiungibilità viene valutata sulle informazioni sorgente accessibili, prima delle trasformazioni: un fatto perso dall'estrattore non diventa un fatto mai fornito.

| Livello | Misura prevista |
|---|---|
| Scrittura | Quota dei fatti obbligatori estratti correttamente; fatti aggiunti senza supporto |
| Aggiornamento | Accuratezza delle operazioni ADD/UPDATE/DELETE/NOOP e correttezza dello stato risultante |
| Retrieval | Copertura dei fatti obbligatori nel contesto e presenza dell'evidenza completa |
| Grafo | Copertura delle relazioni o dei percorsi richiesti, dove applicabile |
| Risposta | Risposte complete, parziali, errate e astensioni; uso di fatti obsoleti o non supportati |
| Costo descrittivo | Token nel contesto, chiamate e tempo per costruire/aggiornare la memoria, tempo di retrieval e generazione |

Denominatori, equivalenze ammesse e casi non applicabili vanno definiti prima dell'esperimento finale. Le metriche di estrazione, aggiornamento o grafo si applicano soltanto ai sistemi che eseguono quelle operazioni. FULL_HISTORY non riceve metriche di retrieval.

La diagnosi segue la prima causa osservabile:

```text
evidenza assente dalle sorgenti accessibili -> raggiungibilità
evidenza presente ma persa o alterata in memoria -> estrazione / gestione / grafo
evidenza conservata ma non recuperata -> retrieval / ranking
evidenza recuperata ma risposta errata -> lettura / generazione
domanda o annotazione ambigua -> benchmark
```

FULL_HISTORY aiuta a localizzare gli errori, ma non sostituisce l'ispezione delle tracce e non è un oracle infallibile. Se risponde correttamente e un'altra architettura fallisce, si controlla la pipeline di memoria. Se fallisce anche FULL_HISTORY, si verificano contesto, lettura, domanda e annotazioni.

## 8. Collegamento con la letteratura

Le ispirazioni derivano dalla sintesi dei paper già discussa; le architetture previste sono adattamenti piccoli e controllati, non repliche complete dei sistemi pubblicati.

| Lavoro | Contributo utilizzato nel progetto |
|---|---|
| Survey sulla memoria degli agenti | Distinzione tra scrittura, gestione e lettura della memoria |
| LoCoMo | Confronto tra messaggi e osservazioni strutturate; domande distribuite tra sessioni |
| LongMemEval | Separazione indexing/retrieval/reading, evidenze annotate e arricchimento delle chiavi con fatti |
| Mem0 | Memorie sintetiche e operazioni ADD/UPDATE/DELETE/NOOP |
| Mem0g e A-MEM | Relazioni esplicite, collegamenti ed evoluzione della memoria |

L'arricchimento delle chiavi con fatti di LongMemEval è distinto dalla sostituzione dei messaggi con soli fatti nel Fact-based RAG proposto. Mem0g e la rete di note di A-MEM forniscono ispirazioni differenti per G, senza implicare un'implementazione identica.

LongMem, MemGPT, Generative Agents e la survey sulla personalizzazione restano riferimenti per contestualizzare il lavoro. Non sono previste ulteriori architetture, reti da addestrare o moduli agentici in questa estensione.

## 9. Fasi operative e criteri di passaggio

| Fase | Attività | Risultato necessario per proseguire |
|---|---|---|
| 1. Consolidare RQ1 | Registrare versioni, protocollo e stato del pilot preliminare, mantenendo separati i suoi risultati | Prima domanda documentata e confine chiaro con RQ2 |
| 2. Definire il protocollo di RQ2 | Precisare confronti, matrice, budget, metriche e limiti | Tabella finale compilabile con criteri stabiliti in anticipo |
| 3. Costruire SC03 e SC04 | Scrivere conversazioni, sette domande e oracle per ciascuno | Domande univoche, evidenze verificabili e fenomeni nuovi |
| 4. Completare le annotazioni | Collegare fatti e messaggi; annotare operazioni e relazioni richieste senza riscrivere gli artefatti del pilot preliminare | Valutazione confrontabile tra rappresentazioni |
| 5. Implementare e provare T/F | Riutilizzare T su SC01 e SC02 e introdurre F su SC02 e SC03, con confronto diretto T/F su SC02 | Rappresentazione eseguibile e confronto abbinato tracciabile |
| 6. Implementare e provare U | Aggiungere su SC03 e SC04 la gestione degli aggiornamenti e l'accesso esplicito allo storico | Confronto F/U su SC03 e stato della memoria verificabile |
| 7. Implementare e provare G | Costruire su SC04 il grafo dagli stessi fatti aggiornati di U e aggiungere il recupero relazionale | Confronto U/G eseguibile senza infrastruttura superflua |
| 8. Correggere il pilot dell'esperimento principale | Controllare dataset, oracle, pipeline e metriche su prove dichiarate di sviluppo | Difetti corretti e limiti documentati, senza nascondere errori del sistema |
| 9. Congelare il protocollo principale | Fissare dataset, oracle, matrice, modelli, prompt, parametri, budget e codice | Versione esatta riproducibile prima delle esecuzioni finali |
| 10. Eseguire e valutare | Eseguire le celle previste, salvare tutte le tracce e applicare i criteri fissati | Risultati completi per domanda e confronto |
| 11. Interpretare e scrivere | Rispondere separatamente a RQ1 e RQ2; per RQ2 analizzare T su SC01 e la catena T/F, F/U, U/G sugli altri scenari | Conclusioni circoscritte, analisi degli errori e tesi spiegabile |

Le prove di sviluppo restano distinte da quelle finali. Le vecchie risposte C2 e FULL_HISTORY del pilot preliminare non vengono mescolate alle nuove come se provenissero dallo stesso protocollo. Tutte le modalità previste vengono eseguite nella configurazione congelata dell'esperimento principale.

L'AI può assistere nella costruzione dei dati, nel codice, nelle verifiche e nella prima classificazione. Lo studente deve controllare oracle, casi ambigui, criteri di valutazione e interpretazione, e comprendere input e output di ogni componente.

## 10. Criterio di completamento

Il lavoro è completo quando sono disponibili:

- RQ1 documentata attraverso il pilot preliminare, mantenendo i suoi risultati separati da quelli di RQ2;
- quattro scenari annotati e protocollo dell'esperimento principale congelato;
- T su SC01 e confronti T/F su SC02, F/U su SC03 e U/G su SC04, con FULL_HISTORY su ogni scenario;
- risultati e tracce delle prove previste;
- analisi distinta di scrittura, gestione, retrieval e risposta;
- costi descrittivi e limiti espliciti, incluso il carattere esplorativo del grafo;
- una spiegazione comprensibile di cosa dimostrano i confronti e cosa rimane aperto.

La tesi può seguire questo ordine: problema, letteratura, RQ1 e pilot preliminare, passaggio da **Quanto** a **Come**, RQ2 e protocollo principale, dataset, architetture, risultati, analisi degli errori, limiti e conclusioni.
