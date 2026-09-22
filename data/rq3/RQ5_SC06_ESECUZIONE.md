# RQ5 / SC06 — comandi di esecuzione

**Stato:** codice realizzato e controllato offline. Nessuna chiamata reale a Gemma o Llama è
stata eseguita; `results/rq5/` non esiste ancora.

La configurazione autoritativa è `data/rq3/config/rq5_sc06_v1.json`. Gli script non
contengono soglie, prompt o parametri propri: leggono tutto da lì. Tutti i comandi vanno
lanciati dalla radice del progetto.

## Script

| File | Cosa fa | Chiama Ollama |
|---|---|---|
| `scripts/rq3/rq5_common.py` | regole condivise: hash, contesti, identificatori, parser | no |
| `scripts/rq3/build_rq5_inputs.py` | costruisce richieste e oracle separati | no |
| `scripts/rq3/validate_rq5_inputs.py` | 31 controlli offline sugli input | no |
| `scripts/rq3/run_rq5_ollama.py` | esegue le generazioni, un modello alla volta | sì |
| `scripts/rq3/evaluate_rq5.py` | unisce risposte e oracle, giudizio deterministico | no |
| `scripts/rq3/summarize_rq5.py` | metriche, bootstrap per episodio, sintesi | no |

## 1. Preparazione e controlli offline

```bash
python3 scripts/rq3/build_rq5_inputs.py
```

```bash
python3 scripts/rq3/validate_rq5_inputs.py
```

```bash
python3 -m unittest tests.test_rq5_sc06
```

Il validatore deve dichiarare 216 richieste nello sviluppo e 4.032 nella valutazione,
cioè 432 e 8.064 celle sui due modelli.

## 2. Anteprima senza chiamate

```bash
python3 scripts/rq3/run_rq5_ollama.py --split development --dry-run
```

Non apre nessuna connessione e non scrive niente: stampa i conteggi e una richiesta
completa, per verificare a occhio che non contenga risposte attese.

## 3. Prova sullo split di sviluppo

Solo `SC06-E001`–`SC06-E012`. Un modello alla volta, nell'ordine della configurazione.
Prima di ogni blocco lo script verifica versione di Ollama, tag e digest locale, poi
esegue tre richieste di riscaldamento escluse dai risultati.

Assaggio da sei celle, per controllare formato e tempi prima di impegnare la macchina:

```bash
python3 scripts/rq3/run_rq5_ollama.py --split development --model gemma3:4b --limit 3
```

Blocco completo del primo modello (216 celle):

```bash
python3 scripts/rq3/run_rq5_ollama.py --split development --model gemma3:4b
```

Blocco completo del secondo modello (216 celle):

```bash
python3 scripts/rq3/run_rq5_ollama.py --split development --model llama3.2:3b
```

Ripresa dopo un'interruzione o un errore di trasporto:

```bash
python3 scripts/rq3/run_rq5_ollama.py --split development --model gemma3:4b --resume
```

`--limit N` vale sulle richieste indipendenti dal modello: `--limit 3` sono 3 celle per
ogni modello indicato. `--resume` salta soltanto le celle concluse con `status: ok`; le
righe di errore restano nel file e quelle celle vengono rieseguite. Un output non
conforme è una cella conclusa: viene conservato così com'è e non viene rigenerato.

Lettura dei risultati dello sviluppo (facoltativa, serve a guardare i fallimenti):

```bash
python3 scripts/rq3/evaluate_rq5.py --split development
```

## 4. Valutazione principale — ancora bloccata

I comandi seguenti **non vanno eseguiti** finché la prova di sviluppo non è stata
esaminata e la versione della configurazione non è stata congelata.

```bash
python3 scripts/rq3/run_rq5_ollama.py --split evaluation --model gemma3:4b
python3 scripts/rq3/run_rq5_ollama.py --split evaluation --model llama3.2:3b
python3 scripts/rq3/evaluate_rq5.py --split evaluation
python3 scripts/rq3/summarize_rq5.py --split evaluation
```

## Artefatti

```text
data/rq3/sc06_rq5_v1/
  development_requests.jsonl    216 richieste, nessuna risposta attesa
  development_oracle.jsonl      216 righe di oracle
  evaluation_requests.jsonl     4.032 richieste
  evaluation_oracle.jsonl       4.032 righe di oracle
  build_manifest.json

results/rq5/sc06/v1/<split>/
  raw_responses.jsonl           una riga per tentativo; vale l'ultima per cella
  warmup_responses.jsonl        riscaldamento, escluso dai risultati
  run_manifest.json             una voce per ogni esecuzione
  evaluations.jsonl             una riga per cella attesa, comprese quelle fallite
  summary.json, summary.csv, SINTESI.md
```

Identificatori: la richiesta è `split|condizione|question_id` ed è la stessa per i due
modelli; la cella è `split|tag|condizione|question_id`.

## Cose da sapere prima di lanciare

- I due modelli devono essere già installati. Nessuno script scarica modelli: se il tag
  manca o il digest è diverso da quello della configurazione, l'esecuzione si ferma.
- Se Ollama non è alla versione verificata `0.34.2` l'esecuzione si ferma. Si può
  proseguire con `--allow-version-mismatch`, ma la differenza va dichiarata nei risultati.
- A fine blocco il modello viene scaricato (`keep_alive: 0`) perché ne resti caricato uno
  alla volta; `--no-unload` disattiva questo comportamento.
- `size_vram` registrato in `run_manifest.json` è un'allocazione dichiarata dal runtime,
  non il picco di RAM misurato.
- La valutazione è deterministica e non usa nessun modello giudice.
