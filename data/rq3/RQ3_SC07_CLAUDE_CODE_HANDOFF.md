# Consegna per Claude Code — RQ3 / SC07

## Ruoli e obiettivo

Realizzare il codice necessario a eseguire il protocollo in `data/rq3/RQ3_SC07_PROTOCOLLO.md`.

- **Claude Sonnet 5 Chat** è l'unico modello che risponde alle domande ed è il modello valutato.
- **Claude Code** realizza e verifica il codice.
- Non modificare né rieseguire RQ1, RQ2 o RQ5/SC06.
- Non avviare automaticamente chiamate reali al modello: prima servono revisione del codice, controlli offline e autorizzazione distinta per lo sviluppo.

## Configurazione da materializzare

Creare una configurazione versionata per `rq3-sc07-v1` che traduca senza reinterpretazioni le decisioni del protocollo:

- dataset GitHub Advisory Database;
- commit SHA, data di acquisizione, hash e licenza registrati;
- split di 3 episodi di sviluppo e 20 di valutazione;
- 3 attività e 2 messaggi per attività;
- 6 domande per episodio;
- condizioni `separated` e `shared_interleaved`;
- Turn-level RAG TF-IDF, soli messaggi utente, `top_k = 2`;
- modello `Claude Sonnet 5 Chat`, con identificatore tecnico e canale di accesso registrati prima delle chiamate;
- una generazione per cella;
- output `{"value": string|null}`;
- seed di selezione `20260923` e bootstrap di 10.000 ricampionamenti per episodio.

Qualunque dettaglio tecnico non ancora disponibile, soprattutto l'identificatore esatto del modello, deve diventare un gate bloccante e non essere inventato.

## Componenti richiesti

Collocare gli script sotto `scripts/rq3/` con nomi che includano `rq3_sc07`, senza sovrascrivere quelli di RQ5.

1. **Acquisizione e manifest della sorgente**
   - acquisisce o legge uno snapshot del repository al commit dichiarato;
   - registra URL, commit, data, hash e licenza;
   - non seleziona record se la sorgente non coincide con il manifest.
2. **Audit e selezione deterministica**
   - applica esattamente i criteri di ammissibilità;
   - salva candidati, esclusioni con motivazione e record selezionati;
   - bilancia la valutazione in 4 episodi per ciascuno dei 5 ecosistemi;
   - garantisce GHSA ID unici, pacchetti diversi dentro l'episodio e split disgiunti;
   - si arresta se uno strato è insufficiente.
3. **Costruzione di conversazioni, domande e oracle**
   - produce due messaggi per attività e l'ordine interlacciato fissato;
   - mantiene la provenienza campo-per-campo nell'oracle;
   - salva conversazioni/richieste e oracle in file separati;
   - non espone GHSA ID, URL, fonte o risposta attesa al modello.
4. **Retrieval Turn-level RAG**
   - riusa, senza cambiarne la semantica, TF-IDF e tokenizzazione di `scripts/run_retrieval_pilot.py`;
   - esegue lo stesso retrieval sulle due condizioni cambiando soltanto il corpus accessibile;
   - salva corpus, punteggi, messaggi recuperati, evidenza obbligatoria e metriche del retrieval;
   - non legge le risposte attese per ordinare o filtrare i messaggi.
5. **Costruzione e validazione delle richieste**
   - usa esattamente il contesto già salvato dal retrieval;
   - costruisce 36 richieste di sviluppo e 240 di valutazione;
   - verifica che domanda e parametri coincidano fra le due condizioni e che cambi soltanto il contesto dovuto al diverso corpus;
   - offre un `dry-run` leggibile senza contattare il modello.
6. **Runner Claude Sonnet 5 Chat**
   - supporta esecuzione separata di `development` e `evaluation`, limite, ripresa e dry-run;
   - salva richiesta, risposta grezza, errore, timestamp, identificatore del modello e metadati disponibili;
   - non carica mai l'oracle durante la generazione;
   - non ritenta automaticamente celle con risposta errata o non conforme;
   - impedisce l'avvio della valutazione senza un gate esplicito successivo allo sviluppo.
7. **Valutazione e riepilogo**
   - unisce oracle e risposte soltanto dopo la generazione;
   - calcola tutte le metriche e i denominatori del protocollo;
   - conserva una riga anche per errori e celle mancanti;
   - produce JSONL, JSON, CSV e una sintesi Markdown;
   - calcola il bootstrap appaiato ricampionando episodi, non singole domande.

## Struttura proposta degli artefatti

```text
data/rq3/config/rq3_sc07_v1.json
data/rq3/sc07_design_v1/
  source_manifest.json
  eligibility_audit.json
  candidates.jsonl
  exclusions.jsonl
  selection.jsonl
  episodes.jsonl
  development_requests.jsonl
  development_oracle.jsonl
  evaluation_requests.jsonl
  evaluation_oracle.jsonl
  build_manifest.json

results/rq3/sc07/v1/
  development/
    retrieval.jsonl
    raw_responses.jsonl
    run_manifest.json
    evaluations.jsonl
    summary.json
  evaluation/
    retrieval.jsonl
    raw_responses.jsonl
    run_manifest.json
    evaluations.jsonl
    summary.json
    summary.csv
    SINTESI.md
```

I nomi possono essere adattati solo se la separazione logica resta identica e viene documentata.

## Controlli obbligatori

I test devono restare offline e usare fixture locali. Verificare almeno:

- snapshot e hash della fonte;
- applicazione di ogni criterio di ammissibilità;
- selezione riproducibile con seed e commit invariati;
- 3 episodi di sviluppo e 20 di valutazione;
- 9 advisory di sviluppo e 60 di valutazione, tutti distinti;
- 4 episodi di valutazione per ecosistema;
- 3 attività, 6 messaggi e 6 domande per episodio;
- ordine interlacciato esatto;
- valore atteso presente in un solo messaggio bersaglio;
- nessuna sovrapposizione fra split;
- memoria separata composta dai soli 2 messaggi bersaglio;
- memoria condivisa composta dagli stessi 2 messaggi più i 4 distrattori;
- `top-k = 2` e spareggio deterministico;
- nessuna lettura dell'oracle durante retrieval o generazione;
- prompt senza fonte, GHSA ID o risposta attesa;
- identità di modello, prompt e parametri fra condizioni;
- parser JSON per valore stringa, `null`, JSON errato e chiavi aggiuntive;
- Exact Match, supporto, contaminazione e confusione fra attività;
- ripresa senza duplicati e conservazione degli errori;
- bootstrap riproducibile per episodio.

## Gate di consegna

Fermarsi e consegnare codice, test, diff e istruzioni quando:

1. tutti i test offline passano;
2. il manifest della sorgente è completo e verificabile;
3. audit e selezione soddisfano tutti i conteggi;
4. il validatore conferma 36 richieste di sviluppo e 240 di valutazione;
5. il dry-run mostra richieste prive di oracle e provenienza;
6. l'identificatore tecnico di Claude Sonnet 5 Chat è stato registrato;
7. nessun file o risultato delle RQ precedenti è stato modificato.

Non eseguire ancora le 36 chiamate di sviluppo. Saranno autorizzate e controllate in un passaggio separato; le 240 chiamate di valutazione restano bloccate fino all'approvazione dello sviluppo.

