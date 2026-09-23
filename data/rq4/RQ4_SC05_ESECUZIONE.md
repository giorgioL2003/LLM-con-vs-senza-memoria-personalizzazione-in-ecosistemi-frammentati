# RQ4 / SC05 — comandi di esecuzione (fase 1)

**Stato:** fase 1 (offline) e fase 2 (esecuzione reale) concluse il 23 settembre 2026.
Smoke test: 1 chiamata per modello, JSON valido. Valutazione: 14 celle `gemma3:4b`, poi 14 celle
`llama3.2:3b`, 28/28 risposte con formato valido, 0 errori, 0 riprese, nessuna chiamata a Claude.
I giudizi qualitativi sono in attesa della revisione dello studente
(`results/rq4/sc05/v1/evaluation/annotation_template.jsonl` → `annotations.jsonl`).

Modifiche al codice prima delle chiamate reali (nessuna su prompt, retrieval, configurazione o criteri):
il blocco «file già con risposte, usa `--resume`» del runner considera soltanto le righe del modello
richiesto, perché il file è condiviso da Gemma e Llama; `validate_rq4_inputs.py --phase generation`
controlla anche le risposte salvate (una riga conclusa per cella, digest, payload, prompt, warmup).

Configurazione autoritativa: `data/rq4/config/rq4_sc05_v1.json`. Comandi dalla radice del progetto.

## Script (`scripts/rq4/`)

| File | Cosa fa | Ollama |
|---|---|---|
| `rq4_common.py` | hash delle sorgenti, messaggi, retrieval (funzioni RQ2 importate), prompt, piano di riuso, parser | no |
| `build_rq4_design.py` | `source_manifest.json`, `messages.jsonl`, `questions.jsonl`, `oracle.jsonl` | no |
| `run_rq4_retrieval.py` | `retrieval.jsonl` (senza oracle) e `retrieval_coverage.jsonl` (copertura per fatto) | no |
| `build_rq4_requests.py` | `requests.jsonl` (28 celle), `generation_plan.jsonl`, `smoke_requests.jsonl`, `build_manifest.json` | no |
| `validate_rq4_inputs.py` | gate 1–9 del protocollo, offline | no |
| `run_rq4_ollama.py` | `--verify-models` (solo metadati), `--dry-run`, smoke e valutazione con gate | sì |
| `evaluate_rq4.py` | schede per cella, flag automatici, giudizi `null` in attesa di revisione | no |
| `summarize_rq4.py` | conteggi per modello, condizione e gruppo, con denominatori | no |

Test: `tests/test_rq4_sc05.py`.

## Fase 1 (eseguita)

```bash
python3 scripts/rq4/build_rq4_design.py
python3 scripts/rq4/run_rq4_retrieval.py
python3 scripts/rq4/build_rq4_requests.py
python3 scripts/rq4/run_rq4_ollama.py --verify-models
python3 scripts/rq4/validate_rq4_inputs.py
python3 -m unittest tests.test_rq4_sc05
python3 scripts/rq4/run_rq4_ollama.py --stage evaluation --dry-run
```

`--verify-models` interroga soltanto `/api/version` e `/api/tags`: nessun modello viene caricato
né genera testo. L'esito è in `results/rq4/sc05/v1/preflight/model_verification.json`.

## Conteggi congelati

| | Gemma 3 4B IT | Llama 3.2 3B Instruct | Totale |
|---|---:|---:|---:|
| Celle | 14 | 14 | 28 |
| Chiamate reali | 14 | 14 | 28 |
| Riusi | 0 | 0 | 0 |

Tutte le 14 coppie separata/condivisa hanno contesti diversi, quindi nessun prompt è identico
all'interno dello stesso modello. Il prompt è identico fra Gemma e Llama per ogni domanda e
condizione (14 prompt distinti).

## Fase 2 — comandi eseguiti

Smoke test (una chiamata per modello sulla fixture non SC05):

```bash
python3 scripts/rq4/run_rq4_ollama.py --stage smoke --model gemma3:4b --confirm-smoke
python3 scripts/rq4/run_rq4_ollama.py --stage smoke --model llama3.2:3b --confirm-smoke
```

Valutazione (richiede anche `results/rq4/sc05/v1/evaluation_gate.json` con `approved_by`,
`approved_at`, `config_sha256` e `build_manifest_sha256` correnti):

```bash
python3 scripts/rq4/run_rq4_ollama.py --stage evaluation --model gemma3:4b --confirm-evaluation
python3 scripts/rq4/run_rq4_ollama.py --stage evaluation --model llama3.2:3b --confirm-evaluation
python3 scripts/rq4/evaluate_rq4.py
python3 scripts/rq4/summarize_rq4.py
python3 scripts/rq4/validate_rq4_inputs.py --phase generation
```

Dopo la generazione i test sugli artefatti reali validano in fase `generation`: il controllo
`phase1.no_raw_responses` vale soltanto prima delle chiamate.

## Decisioni non fissate dal protocollo

- **Riuso delle funzioni esistenti:** `message_items`, `rank_items`, `select_within_budget` e
  `count_tokens` importati da `scripts/rq2/rq2_common.py`; `chat_payload` da
  `scripts/rq3/rq5_common.py`; `http_json`, `preflight`, `process_snapshot` e `unload` da
  `scripts/rq3/run_rq5_ollama.py`. Nessuno di questi file è stato modificato; i loro hash sono nel
  manifest.
- **Riga di contesto:** `[message_id] contenuto`, come la modalità T di RQ2; il budget di 200 token
  si applica alla riga intera, identificatore compreso.
- **Prompt:** istruzioni del pilot/RQ2 (`scripts/build_generation_inputs.py`) più il contratto JSON
  `status`/`answer` del protocollo; chat Ollama con `system` e `user` (`Contesto:` / `Domanda:`);
  schema JSON passato come `format`.
- **Retrieval e copertura separati:** `retrieval.jsonl` non contiene nulla dell'oracle; la copertura
  per fatto sta in `retrieval_coverage.jsonl`, calcolata dopo il ranking.
- **Attesa per condizione:** `answered` se tutte le fonti dei fatti obbligatori sono nel corpus
  (o nel contesto), altrimenti `insufficient`; Q7 sempre `insufficient`. È per provenienza e non
  sostituisce la revisione.
- **Flag automatici:** marcatori obsoleti dichiarati per Q2 (`SRV-12`), Q3 e Q4 (`bilanciatore`),
  e identificatori o numeri della risposta assenti dal contesto; sono segnali per la revisione.
- **Smoke:** fixture sintetica «ticket TST-3», esclusa da SC05 e dai risultati.
- **Verifica dei digest:** file separato `preflight/model_verification.json`; il validatore lo legge
  senza rete.

## Esito del retrieval (noto prima di ogni chiamata)

| Domanda | Gruppo | Fatti nel contesto: separata | Fatti nel contesto: condivisa |
|---|---|---:|---:|
| Q1 | passaggio | 0/2 (non raggiungibili) | 2/2 |
| Q2 | passaggio | 0/2 (non raggiungibili) | 2/2 |
| Q4 | passaggio | 1/2 (vincolo non raggiungibile) | 1/2 (manca S9-U1) |
| Q6 | passaggio | 0/1 (non raggiungibile) | 1/1 |
| Q3 | controllo | 0/1 (S9-U1 non recuperato) | 0/1 |
| Q5 | controllo | 1/2 | 0/2 |
| Q7 | assente | 0/0 | 0/0 |

Nella memoria condivisa Q4 recupera il vincolo della sessione 1 ma non S9-U1; nel contesto
compaiono S8-U1 e S3-U1, che presentano la verifica del bilanciatore come ancora aperta
(informazione superata). Nei controlli Q3 e Q5 la memoria condivisa non recupera l'evidenza
recente. Sono limiti lessicali noti del TF-IDF e non sono stati corretti.
