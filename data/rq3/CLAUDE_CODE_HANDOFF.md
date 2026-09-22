# Consegna operativa per Claude Code — RQ5 / SC06

## Obiettivo

Tradurre in codice il protocollo congelato in `data/rq3/RQ5_SC06_PROTOCOLLO.md`, usando come unica configurazione autoritativa `data/rq3/config/rq5_sc06_v1.json`.

La consegna riguarda preparazione, validazione, esecuzione e valutazione. **Non avviare la valutazione principale durante la realizzazione del codice.** Prima devono passare i controlli offline e la prova sullo split di sviluppo deve essere esaminata separatamente.

## File da realizzare

Collocare gli script in `scripts/rq3/`:

1. `build_rq5_inputs.py`
   - verifica gli SHA-256 delle quattro sorgenti dichiarate nella configurazione;
   - costruisce i due contesti con la regola esatta della configurazione;
   - produce richieste e oracle separati per sviluppo e valutazione;
   - non chiama Ollama.
2. `validate_rq5_inputs.py`
   - controlla conteggi, split disgiunti, unicità delle celle e assenza dei campi vietati nei prompt;
   - ricostruisce indipendentemente i blocchi e l'ordine;
   - verifica 216 richieste indipendenti dal modello nello sviluppo e 4.032 nella valutazione, corrispondenti a 432 e 8.064 celle dopo l'espansione sui due modelli;
   - non chiama Ollama.
3. `run_rq5_ollama.py`
   - interroga `/api/chat`, un modello alla volta;
   - verifica tag e digest locali prima di partire;
   - supporta `--split development|evaluation`, `--model`, `--limit`, `--resume` e `--dry-run`;
   - usa schema, parametri e prompt dalla configurazione;
   - conserva richiesta, risposta grezza, errore, timestamp e tutti i metadati Ollama;
   - non carica mai oracle o `case_mapping.jsonl`.
4. `evaluate_rq5.py`
   - unisce risposte e oracle soltanto dopo la generazione;
   - applica la normalizzazione dichiarata, senza modello giudice;
   - produce una riga di valutazione per ogni cella attesa, comprese quelle fallite.
5. `summarize_rq5.py`
   - calcola metriche e denominatori per modello, condizione e famiglia;
   - calcola il bootstrap appaiato per episodio con seed e ripetizioni della configurazione;
   - genera JSON, CSV e una sintesi Markdown; non modifica giudizi o risposte.

## Struttura degli artefatti

Usare directory versionate, senza sovrascrivere RQ1/RQ2:

```text
data/rq3/sc06_rq5_v1/
  development_requests.jsonl
  development_oracle.jsonl
  evaluation_requests.jsonl
  evaluation_oracle.jsonl
  build_manifest.json

results/rq5/sc06/v1/
  development/raw_responses.jsonl
  development/run_manifest.json
  evaluation/raw_responses.jsonl
  evaluation/run_manifest.json
  evaluation/evaluations.jsonl
  evaluation/summary.json
  evaluation/summary.csv
  evaluation/SINTESI.md
```

L'identificatore di cella deve derivare da `split`, tag del modello, condizione e `question_id`. Le scritture JSONL devono essere incrementali e sicure rispetto a interruzioni; `--resume` salta soltanto celle già concluse e valide.

## Controlli obbligatori

Scrivere test mirati per:

- hash e conteggi delle sorgenti;
- E001–E012 soltanto nello sviluppo ed E013–E236 soltanto nella valutazione;
- differenza fra sufficiente e insufficiente limitata al blocco del caso bersaglio;
- stessi distrattori e stesso ordine relativo nelle due condizioni;
- assenza di oracle, ID originali, fonti e valori di rilevazione nei prompt;
- stesso hash del prompt per i due modelli nella stessa domanda e condizione;
- parser di output valido, duplicati, ordine diverso, JSON errato e chiavi aggiuntive;
- esattezza, omissioni, aggiunte, astensione e confusione fra casi;
- bootstrap per episodio riproducibile;
- ripresa senza duplicazioni e conservazione degli errori.

Usare fixture locali e un server/funzione Ollama simulata nei test. I test non devono scaricare modelli, accedere alla rete o eseguire generazioni reali.

## Gate prima delle chiamate reali

La realizzazione è pronta per la revisione quando:

1. tutti i test passano;
2. il validatore offline conferma 216 richieste nello sviluppo e 4.032 nella valutazione, equivalenti rispettivamente a 432 e 8.064 celle sui due modelli;
3. `--dry-run` mostra richieste prive di risposte attese;
4. nessun file RQ1/RQ2 è stato modificato;
5. i comandi per avviare soltanto lo sviluppo sono documentati.

Dopo questi gate, fermarsi e consegnare codice, diff e istruzioni. L'esecuzione dello split di sviluppo è un passo successivo distinto; la valutazione principale resta ancora bloccata.
