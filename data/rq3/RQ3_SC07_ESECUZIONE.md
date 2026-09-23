# RQ3 / SC07 — comandi di esecuzione

**Stato (23 settembre 2026):** sviluppo concluso (36/36 celle, 23 chiamate) e valutazione finale
conclusa e congelata: 240/240 celle, 139/139 chiamate reali riuscite, 101 riusi, 0 errori, nessuna
ripresa, modello usato `claude-sonnet-5`. Manifest di congelamento:
`results/rq3/sc07/v1/evaluation/freeze_manifest.json` (verifica: `python3 scripts/rq3/freeze_rq3_sc07.py --verify`).
Dopo la valutazione il test di fase sugli artefatti reali verifica la coerenza delle risposte e il
gate, non più la loro assenza.
Canale registrato: Claude Code CLI (`claude-sonnet-5`, effort medium), come `scripts/run_generation.py`.

Configurazione autoritativa: `data/rq3/config/rq3_sc07_v1.json`. Gli script non contengono
soglie, template, prompt o parametri propri. Tutti i comandi vanno lanciati dalla radice del progetto.

## Script (`scripts/rq3/`)

| File | Cosa fa | Rete | Modello |
|---|---|---|---|
| `rq3_sc07_common.py` | regole condivise: hash, snapshot, ammissibilità, selezione, template, retrieval, prompt, parser | no | no |
| `acquire_rq3_sc07_source.py` | fetch del commit esatto (sparse), snapshot tar.gz deterministico, manifest; `--verify` offline | sì (solo acquisizione) | no |
| `select_rq3_sc07_advisories.py` | audit di ammissibilità, esclusioni motivate, selezione deterministica | no | no |
| `build_rq3_sc07_episodes.py` | conversazioni, domande, oracle, provenienza per messaggio | no | no |
| `run_rq3_sc07_retrieval.py` | Turn-level RAG sulle due condizioni (ranking con oracle vietato, poi annotazione) | no | no |
| `build_rq3_sc07_requests.py` | 36 + 240 richieste dal contesto salvato, piani delle chiamate, `build_manifest.json` | no | no |
| `validate_rq3_sc07_inputs.py` | 70 controlli offline (anche chiamate previste e coerenza dei riusi) | no | no |
| `run_rq3_sc07_claude.py` | generazioni via `claude --print`, riuso dei prompt identici, gate, `--dry-run`, `--limit`, `--resume` | sì | **sì** |
| `evaluate_rq3_sc07.py` | unisce oracle e risposte dopo la generazione | no | no |
| `summarize_rq3_sc07.py` | metriche, confronto appaiato, bootstrap per episodio | no | no |

Test: `tests/test_rq3_sc07.py` (fixture locali, nessuna rete).

## 1. Preparazione offline (già eseguita)

```bash
python3 scripts/rq3/acquire_rq3_sc07_source.py --verify
python3 scripts/rq3/select_rq3_sc07_advisories.py
python3 scripts/rq3/build_rq3_sc07_episodes.py
python3 scripts/rq3/run_rq3_sc07_retrieval.py
python3 scripts/rq3/build_rq3_sc07_requests.py
python3 scripts/rq3/validate_rq3_sc07_inputs.py
python3 -m unittest tests.test_rq3_sc07
```

La ricostruzione produce file identici byte per byte (salvo `built_at` in `build_manifest.json`).

## 2. Anteprima senza chiamate

```bash
python3 scripts/rq3/run_rq3_sc07_claude.py --split development --dry-run
```

Non esegue `claude`, non apre connessioni, non scrive file. Mostra celle, chiamate reali previste,
comando, gate e lo stdin esatto di una coppia con prompt identico e di una con contesti diversi.

## 3. Meccanismo di chiamata e riuso

Registrati in `data/rq3/config/rq3_sc07_v1.json` (`model`, `generation`):

```text
claude --print --model claude-sonnet-5 --effort medium --tools '' --strict-mcp-config
       --setting-sources '' --no-session-persistence --output-format stream-json --verbose
```

- `build_command` e `parse_stream` sono importati da `scripts/run_generation.py`, non copiati;
- prompt su stdin: `system` + riga vuota + `user` (`generation.cli_input_template`);
- nessun `--fallback-model`; directory di lavoro temporanea, vuota e verificata prima di ogni
  chiamata; `model_used` salvato per ogni chiamata;
- nessun SDK `anthropic`, nessuna API key: serve un `claude` autenticato nel terminale.

Riuso: `*_call_plan.jsonl` stabilisce, dalle sole richieste, quali celle hanno una chiamata reale
(`model_call`) e quali ricevono la risposta di una cella con prompt identico
(`reused_identical_prompt`, con `reused_from_cell_id`). Chiave: `prompt_sha256` +
`model_config_sha256`; il runner confronta anche i testi carattere per carattere. La cella generata
è sempre la `separated`, quella riusata la `shared_interleaved` della stessa domanda.

| Split | Celle | Chiamate reali | Celle riusate |
|---|---:|---:|---:|
| sviluppo | 36 | 23 | 13 |
| valutazione | 240 | 139 | 101 |

## 4. Sviluppo (23 chiamate reali, 36 celle) — non ancora autorizzato

```bash
python3 scripts/rq3/run_rq3_sc07_claude.py --split development
```

Poi, senza altre chiamate:

```bash
python3 scripts/rq3/evaluate_rq3_sc07.py --split development
python3 scripts/rq3/summarize_rq3_sc07.py --split development
```

`--limit N` esegue al massimo N chiamate reali (più i riusi che ne derivano); `--resume` salta le
celle concluse con `status: ok`, riprova soltanto gli errori di trasporto (che restano nel file) e
completa i riusi rimasti in sospeso senza nuove chiamate. Una risposta errata o non conforme è una
cella conclusa e non viene rigenerata. Dopo le 36 celle ci si ferma.

## 5. Valutazione (139 chiamate reali, 240 celle) — eseguita e congelata

Il runner rifiuta lo split `evaluation` finché:

1. lo sviluppo non ha 36 celle concluse (23 chiamate reali + 13 riusi);
2. esiste `results/rq3/sc07/v1/evaluation_gate.json` con `approved_by`, `approved_at`,
   `development_raw_responses_sha256` (SHA-256 dell'attuale file di risposte dello sviluppo) e
   `config_sha256` (SHA-256 dell'attuale configurazione);
3. si passa `--confirm-evaluation`.

## Decisioni operative non fissate dal protocollo

- **Commit della sorgente:** `2f3ffd6f…` (HEAD del 23/09/2026, 06:36 UTC). Snapshot limitato a
  `advisories/github-reviewed` e `LICENSE.md` (28 MB); SHA-256 e albero git nel manifest.
- **Malware:** CWE-506 fra i `cwe_ids`, oppure sommario che inizia con «Malicious Package» o
  contiene la parola «malware».
- **Un pacchetto:** un solo `(ecosistema, nome)` distinto in `affected`; più voci dello stesso
  pacchetto cadono nel criterio dell'intervallo.
- **Intervallo interpretabile:** una voce `affected`, un solo range `ECOSYSTEM`/`SEMVER`, eventi
  esattamente `introduced`, `fixed`. Reso come `< fixed` se `introduced = 0`, altrimenti
  `>= introduced, < fixed`. `last_known_affected_version_range` non è usato.
- **Unicità del valore atteso** applicata come criterio di ammissibilità, per tutte e tre le attività
  possibili, prima dell'ordinamento (4 advisory esclusi, es. pacchetto `st`).
- **Chiave di ordinamento:** `SHA-256("20260923:" + ecosistema + ":" + GHSA ID)`.
- **Sviluppo:** un episodio per `npm`, `PyPI`, `Maven` (primi tre ecosistemi dell'elenco),
  estratti prima della valutazione.
- **Composizione:** primo candidato non usato con pacchetto diverso (confronto senza maiuscole);
  attività assegnate nell'ordine di estrazione. Uno stesso pacchetto può ricorrere in episodi
  diversi con advisory diversi (succede per `zeppelin-server` e `loofah`).
- **Template e domande** in italiano, scritti una volta e non ritoccati dopo aver visto il
  retrieval. Ogni messaggio e ogni domanda nominano l'attività.
- **Contesto:** `[rank] testo`, in ordine di rank, come nel pilot.
- **Metriche:** celle mancanti contano come non corrette; seed del bootstrap `20260923`.
- **Canale:** Claude Code CLI al posto dell'API; lo schema JSON non è imposto dal canale, quindi gli
  errori di formato sono osservabili. Prompt su stdin come `system` + riga vuota + `user`.
- **Riuso dei prompt identici:** una chiamata per prompt distinto; la risposta della cella
  `separated` è assegnata alla cella `shared_interleaved` con prompt identico.

## Esito del retrieval offline (già noto prima di ogni chiamata)

| Split | Condizione | Evidenza recuperata | Messaggi di altre attività nel contesto |
|---|---|---:|---:|
| sviluppo | separata | 18/18 | 0/36 |
| sviluppo | condivisa | 18/18 | 4/36 |
| valutazione | separata | 120/120 | 0/240 |
| valutazione | condivisa | 120/120 | 17/240 |

In valutazione il contesto è identico nelle due condizioni per 101 domande su 120. Delle 19
diverse, 17 contengono un messaggio di un'altra attività (tutte domande sul pacchetto: 13 impatto,
4 correzione) e 2 contengono gli stessi messaggi in ordine inverso, perché l'idf cambia con il
corpus. Con questo disegno, un'eventuale differenza fra condizioni può nascere solo da questi 19
contesti.
