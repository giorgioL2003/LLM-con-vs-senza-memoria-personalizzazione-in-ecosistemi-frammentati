# Comandi essenziali per la demo

Tre passaggi: controllare gli scenari, mostrare il contesto recuperato e chiedere le risposte a Claude. La demo usa gli artefatti di sviluppo già salvati; non ricostruisce fatti, memoria o grafo.

Prima entra nella cartella del progetto:

```bash
cd /Users/giorgiolai/Desktop/progetto_tirocinio
```

## 1. Controllare gli scenari

**Non chiama Claude.** Verifica il dataset principale SC01–SC04; non è una valutazione della correttezza delle risposte né il controllo specifico di SC05.

```bash
python3 scripts/rq2/validate_rq2.py
```

## 2. Mostrare il contesto recuperato per SC05

**Non chiama Claude.** Legge la traccia già salvata e mostra le informazioni selezionate da U e GER per la domanda sul server corretto, con i token occupati.

```bash
python3 - <<'PYTHON'
import json
from pathlib import Path
file = Path("results/rq2/sc05_dev_v1/retrieval_sc05_u_ger.jsonl")
for line in file.read_text().splitlines():
    r = json.loads(line)
    if r["question_id"] == "SC05-Q2":
        print(f"\n=== {r['mode']} — {r['context_tokens']}/{r['budget_tokens']} token ===")
        for voce in r["selected"]:
            print(voce["render"])
PYTHON
```

**Da mostrare:** U recupera la voce che identifica SRV-14 come server corretto; GER recupera la smentita di SRV-12, ma non quella voce. La semplice presenza del nome SRV-14 in altre informazioni non basta.

## 3. Generare tre nuove risposte con Claude

**Chiama Claude: fino a 3 chiamate nuove**, una per U, GER e FULL_HISTORY. Usa i prompt già preparati per la stessa prova. Serve Claude Code autenticato.

```bash
python3 -u scripts/run_generation.py \
  --inputs results/rq2/sc05_dev_v1/generation_inputs_sc05.jsonl \
  --question-id SC05-Q2 \
  --modes U GER FULL_HISTORY \
  --out results/demo_professore_01/sc05_risposte.jsonl
```

`ok` significa che la chiamata è riuscita, non che la risposta è corretta. FULL_HISTORY riceve tutta la cronologia: è un controllo diagnostico fuori dal budget delle altre due modalità.

Se stampa **«Niente da fare»**, le risposte sono già in quel file. Per una nuova replica cambia `demo_professore_01` in `demo_professore_02`, anche nel comando di lettura qui sotto.

### Leggere le risposte in modo chiaro

**Non chiama Claude.** Stampa soltanto modalità, risposta ed eventuale errore.

```bash
python3 - <<'PYTHON'
import json
from pathlib import Path
file = Path("results/demo_professore_01/sc05_risposte.jsonl")
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
