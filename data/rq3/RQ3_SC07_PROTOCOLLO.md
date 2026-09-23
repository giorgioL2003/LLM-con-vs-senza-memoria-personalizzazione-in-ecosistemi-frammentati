# RQ3 / SC07 — protocollo sperimentale

**Stato:** disegno sperimentale fissato il 23 settembre 2026. La selezione dei record, il codice e le chiamate al modello non sono ancora stati eseguiti. Lo split di valutazione resta bloccato finché lo sviluppo e tutti i controlli offline non sono stati esaminati.

## Domanda di ricerca

**RQ3:** quando nello stesso scenario vengono interlacciate conversazioni relative ad attività diverse, quanto cambia la capacità del sistema di recuperare l'informazione dell'attività richiesta e produrre una risposta corretta?

SC07 confronta due perimetri di memoria usando la stessa architettura **Turn-level RAG**:

1. **memoria separata:** il retriever può cercare soltanto nei messaggi dell'attività richiesta;
2. **memoria condivisa:** il retriever può cercare nei messaggi interlacciati di tutte e tre le attività.

Modello, domande, messaggi bersaglio, algoritmo di retrieval, `top-k` e prompt restano identici. Cambia soltanto l'insieme dei messaggi accessibili al retriever.

## Fonte dei dati e limite della loro realtà

I fatti provengono dal **GitHub Advisory Database**, repository pubblico in formato OSV e con licenza CC-BY 4.0:

> GitHub, *GitHub Advisory Database*, repository pubblico di advisory di sicurezza, s.d.  
> https://github.com/github/advisory-database

Prima della selezione devono essere registrati:

- URL del repository;
- commit SHA esatto della sorgente;
- data di acquisizione;
- SHA-256 dei file o dell'archivio usato;
- testo della licenza.

Si usano soltanto advisory nella cartella `advisories/github-reviewed`, non ritirate e non appartenenti alla categoria malware. Le informazioni sulle vulnerabilità sono reali; conversazioni, ordine dei messaggi e domande sono costruiti per l'esperimento. SC07 non rappresenta conversazioni aziendali reali.

Il repository è mantenuto da GitHub e dalla comunità, ma aggrega anche fonti esterne, fra cui NVD. Questa provenienza indiretta deve essere dichiarata nella descrizione del dataset.

## Attività nello stesso scenario

Ogni episodio descrive tre attività dello stesso dominio, associate a tre advisory differenti ma appartenenti allo stesso ecosistema software:

1. **Triage della vulnerabilità:** identificazione del pacchetto e registrazione della severità.
2. **Analisi dell'impatto:** identificazione del pacchetto e dell'intervallo di versioni vulnerabili.
3. **Pianificazione della correzione:** identificazione del pacchetto e della prima versione corretta.

Ogni attività contiene due messaggi utente derivati dai campi dell'advisory. I sei messaggi dell'episodio vengono interlacciati in ordine fisso:

`triage-1 → impatto-1 → correzione-1 → triage-2 → impatto-2 → correzione-2`.

Ogni messaggio ha un identificatore stabile e un riferimento al campo OSV di origine. Gli identificatori originali dell'advisory e la provenienza rimangono negli artefatti di tracciabilità, non nel prompt destinato al modello.

## Ammissibilità e selezione degli advisory

Un advisory è ammissibile soltanto se:

- è GitHub-reviewed, non ritirato e non malware;
- riguarda esattamente un pacchetto;
- appartiene a uno degli ecosistemi fissati: `npm`, `PyPI`, `Maven`, `Go`, `RubyGems`;
- possiede una severità categoriale non vuota;
- contiene un intervallo di versioni interpretabile e una sola versione `fixed` utilizzabile senza inferenze;
- i valori destinati ai messaggi sono stringhe non vuote e non richiedono conoscenza esterna;
- non è già stato assegnato a un altro episodio o split.

La selezione è deterministica. Gli advisory ammissibili vengono ordinati tramite SHA-256 calcolato su seed, ecosistema e GHSA ID. Il seed fissato è `20260923`. Non si sostituisce un record dopo aver visto le risposte del modello.

La valutazione contiene quattro episodi per ciascuno dei cinque ecosistemi. Dentro ogni episodio le tre advisory appartengono allo stesso ecosistema ma a pacchetti differenti. Se uno strato non contiene abbastanza record ammissibili, la preparazione deve fermarsi e documentare il problema: i criteri non possono essere allentati automaticamente.

## Dimensione della prova

| Split | Episodi | Advisory | Domande per episodio | Condizioni | Celle valutate | Chiamate reali |
|---|---:|---:|---:|---:|---:|---:|
| Sviluppo | 3 | 9 | 6 | 2 | 36 | 23 |
| Valutazione | 20 | 60 | 6 | 2 | 240 | 139 |

Lo sviluppo serve a controllare dati, conversazioni, domande, parser e tempi. Non entra nei risultati finali. Le 240 celle della valutazione corrispondono a 120 confronti appaiati fra memoria separata e memoria condivisa. Le chiamate reali sono meno delle celle perché i prompt identici fra le due condizioni ricevono una sola generazione (vedi «Modello di risposta»).

Le sei domande di ogni episodio sono due per attività:

- **triage:** pacchetto; severità;
- **analisi dell'impatto:** pacchetto; intervallo vulnerabile;
- **pianificazione della correzione:** pacchetto; versione corretta.

Tutte le domande finali devono essere risolvibili dai messaggi dell'attività bersaglio. Ogni risposta attesa è una stringa canonica presente testualmente in un solo messaggio bersaglio. Domande e oracle vengono conservati separatamente dalle conversazioni.

## Turn-level RAG

L'unità recuperabile è il singolo messaggio utente. I messaggi dell'assistente non vengono indicizzati e non introducono fatti autorevoli.

Il retriever riusa la configurazione elementare già adottata nel pilot del progetto:

- TF-IDF con similarità del coseno;
- tokenizzazione in minuscolo che conserva parole, numeri, trattini e underscore;
- query uguale al testo della domanda;
- `top-k = 2`;
- spareggio deterministico secondo l'ordine dei messaggi.

Nella memoria separata il corpus contiene i due messaggi dell'attività richiesta. Nella memoria condivisa contiene tutti i sei messaggi interlacciati. In entrambe le condizioni il contesto finale contiene al massimo due messaggi e viene presentato nello stesso formato.

Per ogni domanda si salvano corpus accessibile, punteggi, messaggi recuperati, evidenza obbligatoria e successo del retrieval. La raggiungibilità dell'evidenza e l'effettivo recupero restano due misure distinte.

## Modello di risposta

Tutte le risposte vengono generate da **Claude Sonnet 5 Chat**. Claude Code è soltanto lo strumento incaricato di realizzare gli script e non costituisce il modello valutato.

Prima dello sviluppo devono essere registrati il nome mostrato all'utente, l'identificatore tecnico esatto del modello e il canale usato per accedervi. Lo stesso snapshot disponibile, lo stesso prompt e gli stessi parametri devono essere usati nelle due condizioni.

Registrazione (23 settembre 2026): identificatore `claude-sonnet-5`, canale **Claude Code CLI**, con lo stesso meccanismo di `scripts/run_generation.py`: `claude --print` non interattivo con prompt su stdin, `--effort medium`, nessun modello di fallback, strumenti disabilitati (`--tools ""`), nessun server MCP né impostazione utente o di progetto, nessuna persistenza della sessione, una directory di lavoro temporanea e vuota. Per ogni chiamata si salva il modello realmente usato, dichiarato dall'output `stream-json`. Non si usano l'SDK `anthropic` né una API key.

Il modello riceve soltanto il contesto recuperato e la domanda. Deve rispondere nel formato JSON:

```json
{"value": "risposta"}
```

Se il contesto non consente di rispondere, il valore deve essere `null`. Si effettua una sola generazione per condizione e domanda. Le prove non misurano quindi la variabilità stocastica di Claude Sonnet 5 Chat.

Quando le due celle di una domanda hanno lo stesso prompt (stesso `prompt_sha256`, cioè stesso testo di sistema e utente) e la stessa configurazione del modello, si effettua **una sola chiamata reale** e la stessa risposta viene assegnata anche all'altra cella. Accade quando il retrieval restituisce gli stessi due messaggi, nello stesso ordine, in entrambe le condizioni. La cella riusata resta nella valutazione, riporta `generation_kind="reused_identical_prompt"` e `reused_from_cell_id`, e non conta come chiamata al modello. La decisione dipende soltanto dalle richieste, mai dall'oracle. Con i dati congelati: sviluppo 36 celle e 23 chiamate reali; valutazione 240 celle e 139 chiamate reali. Di conseguenza, nelle domande con prompt identico le due condizioni hanno per costruzione la stessa risposta: la differenza fra condizioni può nascere solo dalle domande con contesto diverso.

## Valutazione

La metrica primaria è l'**Exact Match** della risposta, calcolato separatamente nelle due condizioni. La normalizzazione ammessa è Unicode NFC e rimozione dei soli spazi esterni; maiuscole, minuscole e grafia restano significative.

Metriche secondarie:

- **retrieval success:** il messaggio con l'evidenza obbligatoria è nei due recuperati;
- **contaminazione del contesto:** quota dei messaggi recuperati appartenenti ad attività diverse da quella richiesta;
- **risposta supportata:** il valore prodotto compare nel contesto recuperato;
- **confusione fra attività:** il valore errato coincide con un fatto appartenente a un'altra attività dello stesso episodio;
- **errore di formato** o risposta `null` nonostante l'evidenza recuperata.

Gli errori vengono attribuiti, nell'ordine osservabile, a: evidenza non raggiungibile, retrieval, generazione o formato. Non si corregge manualmente una risposta e non si ripete una singola cella fallita.

Il confronto è appaiato per domanda. Si riporta la differenza in punti percentuali fra memoria condivisa e memoria separata, con conteggi e denominatori. Un intervallo bootstrap al 95% può essere calcolato ricampionando interi episodi per 10.000 volte con seed fissato; le sei domande dello stesso episodio non sono trattate come osservazioni indipendenti. Non sono previsti p-value.

I risultati descrivono SC07, i cinque ecosistemi selezionati, il retriever fissato e Claude Sonnet 5 Chat. Non dimostrano un comportamento universale di tutti i dataset, retriever o modelli.

## Versionamento e blocchi di esecuzione

Gli artefatti devono essere separati in:

- snapshot e manifest della sorgente;
- audit di ammissibilità ed esclusioni;
- selezione e assegnazione agli episodi;
- conversazioni;
- richieste prive di oracle;
- oracle con valori attesi e provenienza;
- tracce del retrieval;
- risposte grezze;
- valutazioni e riepiloghi derivati.

Prima di qualsiasi chiamata reale devono passare controlli offline su hash, conteggi, unicità, split disgiunti, campi obbligatori, assenza di oracle nei prompt, identità degli input fra le due condizioni salvo il corpus accessibile, numero di chiamate reali previste e riuso ammesso soltanto fra prompt, modello e parametri identici.

Dopo le 36 celle di sviluppo (23 chiamate reali) ci si ferma. Una modifica a template, selezione, retriever, prompt, parser o metriche richiede una nuova versione. Dopo l'avvio della valutazione nessuna regola può essere cambiata.

