# Consegna per Claude Code — RQ4 / SC05

## Obiettivo

Realizzare la pipeline di RQ4 descritta in `data/rq4/RQ4_SC05_PROTOCOLLO.md`, senza effettuare chiamate reali ai modelli.

L'esperimento confronta, dopo il passaggio fra sessione 5 e 6, memoria separata e condivisa con due modelli B: `gemma3:4b` e `llama3.2:3b`. Claude Sonnet 5 Chat rappresenta il modello della fase precedente, ma RQ4 non deve generare nuove risposte di Claude né indicizzare risposte dell'assistente.

## Vincoli

- Leggere scenario e annotazioni SC05 in sola lettura.
- Leggere `data/rq3/config/rq5_sc06_v1_1.json` in sola lettura come fonte dei tag, digest e parametri già congelati per Gemma e Llama.
- Non modificare o rieseguire RQ1, RQ2, RQ3 o RQ5.
- Usare Turn-level RAG sui soli messaggi utente.
- Riutilizzare la semantica del ranking TF-IDF e del conteggio del budget già presenti nel progetto; non correggere i limiti lessicali osservati su SC05.
- Budget massimo del contesto: 200 token.
- Separare conversazioni, oracle, retrieval, richieste, risposte ed evaluazioni.
- Non usare l'oracle nel retrieval, nella costruzione dei prompt o nella generazione.
- Non chiamare Ollama durante la realizzazione e i test.

## Configurazione

Creare `data/rq4/config/rq4_sc05_v1.json` come unica configurazione autoritativa. Deve contenere almeno:

- hash di scenario, annotazioni, retriever e configurazione RQ5 da cui derivano i modelli;
- punto del passaggio 5/6;
- perimetri delle due condizioni;
- retriever e budget;
- prompt e schema JSON;
- tag, digest, quantizzazione e parametri dei due modelli;
- conteggi attesi;
- metriche e regole di valutazione;
- gate di smoke test e valutazione.

Non duplicare decisioni divergenti negli script: parametri, testi e percorsi sperimentali devono provenire dalla configurazione.

## Componenti da realizzare

Collocare gli script sotto `scripts/rq4/`.

1. **Costruzione del disegno**
   - verifica gli hash delle due sorgenti SC05;
   - proietta i soli messaggi utente con identificatori originali;
   - costruisce corpus separato (S6–S9) e condiviso (S1–S9);
   - copia nell'oracle RQ4 i fatti obbligatori e la provenienza, senza alterare l'annotazione originale.
2. **Retrieval Turn-level RAG**
   - usa lo stesso ranking TF-IDF del progetto;
   - applica il budget di 200 token con la regola già dichiarata;
   - salva corpus accessibile, ranking, punteggi, token, messaggi selezionati, raggiungibilità e copertura per fatto;
   - non legge risposte attese per ordinare o selezionare.
3. **Costruzione delle richieste**
   - produce 28 celle: 2 modelli × 2 condizioni × 7 domande;
   - mantiene prompt identico fra i due modelli per la stessa condizione e domanda;
   - richiede l'oggetto JSON `status`/`answer` del protocollo;
   - calcola un hash del prompt completo.
4. **Piano di riuso**
   - raggruppa soltanto celle dello stesso modello con prompt e configurazione identici;
   - una cella chiama il modello e le altre registrano `reused_identical_prompt` e `reused_from_cell_id`;
   - non riusa mai una risposta di Gemma per Llama o viceversa;
   - congela prima delle chiamate il numero di chiamate reali.
5. **Runner Ollama**
   - riusa le misure di sicurezza e tracciabilità del runner RQ5 senza modificarne gli artefatti;
   - verifica tag e digest prima di partire;
   - esegue un modello alla volta, tre warmup esclusi, temperatura 0, seed 42, `num_ctx=4096`, `num_predict=128`;
   - supporta dry-run, limite, ripresa e arresto dopo errori consecutivi;
   - conserva risposta grezza, testo, parser, metadati, modello e digest;
   - non carica mai l'oracle.
6. **Valutazione**
   - unisce risposte e oracle soltanto dopo la generazione;
   - produce una scheda strutturata per ogni cella;
   - calcola flag automatici di copertura, obsoleto e supporto senza sostituire la revisione umana;
   - lascia i giudizi qualitativi come `null` e li etichetta `proposti/in attesa di revisione` finché lo studente non li approva;
   - non usa un modello giudice.
7. **Riepilogo**
   - genera conteggi per modello, condizione e gruppo di domanda;
   - mostra sempre numeratori e denominatori;
   - tiene separati i due modelli B;
   - non media domande di passaggio, controlli e informazione assente in un solo punteggio.

## Struttura attesa

```text
data/rq4/config/rq4_sc05_v1.json
data/rq4/sc05_handoff_v1/
  source_manifest.json
  messages.jsonl
  questions.jsonl
  oracle.jsonl
  retrieval.jsonl
  requests.jsonl
  generation_plan.jsonl
  build_manifest.json

results/rq4/sc05/v1/
  smoke/
  evaluation/
    raw_responses.jsonl
    run_manifest.json
    annotation_template.jsonl
    evaluations.jsonl
    summary.json
    summary.csv
    SINTESI.md
```

La struttura può essere raffinata senza mescolare dati, oracle e risposte e senza sovrascrivere altre RQ.

## Test obbligatori

Usare fixture locali, senza rete né modelli. Verificare almeno:

- hash e sola lettura delle sorgenti;
- 16 messaggi utente e 9 sessioni;
- passaggio esatto fra S5 e S6;
- corpus separato composto soltanto da S6–S9;
- corpus condiviso composto da S1–S9;
- 7 domande e 28 celle uniche;
- Q1, Q2, Q4 e Q6 marcate dipendenti dal passaggio;
- Q3 e Q5 marcate come controlli successivi;
- Q7 marcata come informazione assente;
- ranking e budget deterministici;
- oracle assente da retrieval e richieste;
- prompt uguale fra modelli per stessa domanda/condizione;
- riuso soltanto entro lo stesso modello con input identico;
- parser per JSON valido, status non ammesso, chiavi aggiuntive e testo extra;
- risposte mancanti conservate;
- nessun file delle altre RQ modificato.

## Gate di consegna

Fermarsi quando:

1. tutti i test offline passano;
2. il validatore conferma 28 celle;
3. il piano dichiara quante chiamate reali e quanti riusi sono previsti;
4. il dry-run mostra esempi separato/condiviso per Q2, Q4 e Q7;
5. tag e digest locali sono verificati senza generare risposte;
6. nessun `raw_responses.jsonl` di RQ4 esiste;
7. nessun artefatto delle altre RQ è stato modificato.

Consegnare codice, test, manifest, conteggi e comandi futuri. Non eseguire smoke test o valutazione finché non vengono autorizzati separatamente.
