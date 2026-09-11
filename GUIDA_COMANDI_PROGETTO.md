# Comandi essenziali per la demo

Tre passaggi: controllare gli scenari, mostrare il contesto recuperato e chiedere le risposte a Claude. La demo usa gli artefatti di sviluppo già salvati; non ricostruisce fatti, memoria o grafo.

Turn-level RAG (T) è stato provato anche su SC04 e SC05: le 14 risposte sono già salvate in `results/rq2/t_ext_v1/`. I confronti sono T/U/G su SC04 e T/U/GER su SC05; FULL_HISTORY resta il controllo diagnostico.

Prima entra nella cartella del progetto:

```bash
cd /Users/giorgiolai/Desktop/progetto_tirocinio
```

## 1. Controllare gli scenari

**Non chiama Claude.** Verifica il dataset principale SC01–SC04; non è una valutazione della correttezza delle risposte né il controllo specifico di SC05.

```bash
python3 scripts/rq2/validate_rq2.py
```

Stampa anche la **matrice estesa**: SC01 T, SC02 T/F, SC03 F/U, SC04 T/U/G,
SC05 T/U/GER, con FULL_HISTORY come controllo diagnostico in ogni scenario. La
matrice originale di 77 celle non cambia (RQ2.md, sezione 12).

## 2. Mostrare il contesto recuperato per SC05

**Non chiama Claude.** Legge le tracce già salvate e mostra le informazioni selezionate da T, U e GER per la domanda sul server corretto, con i token occupati.

```bash
python3 - <<'PYTHON'
import json
from pathlib import Path
files = [
    Path("results/rq2/t_ext_v1/retrieval_t_sc05.jsonl"),
    Path("results/rq2/sc05_dev_v1/retrieval_sc05_u_ger.jsonl"),
]
for file in files:
    for line in file.read_text().splitlines():
        r = json.loads(line)
        if r["question_id"] == "SC05-Q2":
            print(f"\n=== {r['mode']} — {r['context_tokens']}/{r['budget_tokens']} token ===")
            for voce in r["selected"]:
                print(voce["render"])
PYTHON
```

**Da mostrare:** T recupera i messaggi iniziale e di correzione; U recupera la voce che identifica SRV-14 come server corretto; GER recupera la smentita di SRV-12, ma non quella voce. La semplice presenza del nome SRV-14 in altre informazioni non basta.

### Leggere le risposte già salvate

**Non chiama Claude.** Mostra le quattro risposte della prova di sviluppo alla stessa domanda.

```bash
python3 - <<'PYTHON'
import json
from pathlib import Path
files = [
    Path("results/rq2/t_ext_v1/generation_dev_t_sc05.jsonl"),
    Path("results/rq2/sc05_dev_v1/generation_dev_sc05.jsonl"),
]
for file in files:
    for line in file.read_text().splitlines():
        r = json.loads(line)
        if r["question_id"] == "SC05-Q2":
            print(f"\n=== {r['question_id']} — {r['mode']} ===")
            print(r.get("model_answer") or r.get("error"))
PYTHON
```

Per vedere il caso delle informazioni obsolete, sostituisci `SC05-Q2` con `SC05-Q3` nei due comandi di lettura: T indica come aperta anche la verifica del bilanciatore, già completata. Nel contesto manca il messaggio finale che la chiude.

I [confronti per scenario](results/rq2/t_ext_v1/confronti_per_scenario.md) raccolgono anche i risultati di SC04. I giudizi di T restano proposti; le nuove risposte non rendono definitivo il protocollo.

## 3. Generare quattro nuove risposte con Claude

**Chiama Claude: fino a 4 chiamate nuove**, una per T, U, GER e FULL_HISTORY. Esegui entrambi i comandi: usano i prompt già salvati nelle due prove e scrivono nello stesso file della nuova demo. Serve Claude Code autenticato.

```bash
python3 -u scripts/run_generation.py \
  --inputs results/rq2/t_ext_v1/generation_inputs_t_sc05.jsonl \
  --question-id SC05-Q2 \
  --modes T \
  --out results/demo_professore_t_01/sc05_risposte.jsonl
```

```bash
python3 -u scripts/run_generation.py \
  --inputs results/rq2/sc05_dev_v1/generation_inputs_sc05.jsonl \
  --question-id SC05-Q2 \
  --modes U GER FULL_HISTORY \
  --out results/demo_professore_t_01/sc05_risposte.jsonl
```

`ok` significa che la chiamata è riuscita, non che la risposta è corretta. T, U e GER hanno un budget di 200 token del conteggio locale. FULL_HISTORY riceve tutta la cronologia: è un controllo diagnostico fuori budget.

Se stampa **«Niente da fare»**, le risposte selezionate sono già in quel file. Per una nuova replica usa una cartella non ancora utilizzata, per esempio `demo_professore_t_02`, in entrambi i comandi e nel comando di lettura qui sotto.

### Leggere le risposte in modo chiaro

**Non chiama Claude.** Stampa soltanto modalità, risposta ed eventuale errore.

```bash
python3 - <<'PYTHON'
import json
from pathlib import Path
file = Path("results/demo_professore_t_01/sc05_risposte.jsonl")
for line in file.read_text().splitlines():
    r = json.loads(line)
    print(f"\n=== {r['question_id']} — {r['mode']} ===")
    print(r.get("model_answer") or r.get("error"))
PYTHON
```

Il punto della demo è confrontare **le informazioni date al modello con la risposta che produce**. Le nuove risposte vanno lette: non ereditano i giudizi della prova precedente.

## Immagini da affiancare alla demo

- [Grafo SC04](/Users/giorgiolai/Desktop/progetto_tirocinio/slides/immagini/sc04_grafo_memoria.png)
- [Memoria Gerarchica SC05](/Users/giorgiolai/Desktop/progetto_tirocinio/slides/immagini/sc05_memoria_gerarchica.png)

Sono viste esplicative dei dati già salvati, non immagini aggiornate automaticamente dai comandi.
