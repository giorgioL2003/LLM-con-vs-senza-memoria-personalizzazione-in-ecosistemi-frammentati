# Generare manualmente un grafico per scenario

Lo script genera un grafico a barre verticali per lo scenario scelto.
Asse X: architetture. Asse Y: risposte complete e supportate, da 0 a 7.
Non genera una vista d'insieme. Non rigenera risposte e non modifica i giudizi.

## Da terminale

```bash
cd /Users/giorgiolai/Desktop/progetto_tirocinio
.venv-grafici/bin/python scripts/plot_rq2_results.py --scenario SC02
```

Sostituisci `SC02` con `SC03`, `SC04` o `SC05` quando vuoi un altro scenario.
Troverai PNG e SVG in `results/rq2/budget_per_scenario_v1/grafici/`.
Una nuova esecuzione aggiorna soltanto i due file dello scenario scelto.

## Da PyCharm

1. Imposta l'interprete su `/Users/giorgiolai/Desktop/progetto_tirocinio/.venv-grafici/bin/python`.
2. Apri `scripts/plot_rq2_results.py`.
3. Modifica `SCENARIO = "SC02"` scegliendo lo scenario desiderato.
4. Premi **Run** sullo script.

Il grafico viene salvato e poi mostrato tramite `plt.show()`. Per vederlo dentro
PyCharm, abilita **Settings → Tools → Python Plots → Show plots in tool window**.
Altrimenti può aprirsi in una finestra separata.

In alternativa, imposta `--scenario SC03` nel campo Parameters della
configurazione Run. Il parametro prevale sulla variabile `SCENARIO`.

## Come funziona

- `tables.verify()` verifica e restituisce gli stessi numeri della tabella.
- `plt.subplots()` crea figura e assi.
- `ax.bar()` disegna le colonne e `ax.text()` scrive le frazioni.
- `fig.savefig()` salva PNG e SVG.

Le altezze corrispondono alla colonna **C&S**, non a tutte le risposte corrette:
le astensioni corrette sono escluse. Una domanda su sette richiede astensione,
quindi sei risposte complete più un'astensione corretta coprono tutti i casi.
Il grafico non mostra la distribuzione delle risposte parziali ed errate.

Full history è rosso e separato: controllo diagnostico senza tetto.
Le architetture sono indicate con i nomi estesi, con colori coerenti tra scenari.
SC02–SC04 usano la nuova prova; SC05 e FULL_HISTORY sono storici riutilizzati.
Le nuove valutazioni restano proposte. Rigenera i grafici se aggiorni i giudizi
ed i riepiloghi.

## Installazione su un altro computer

```bash
python3 -m venv .venv-grafici
.venv-grafici/bin/python -m pip install -r requirements-grafici.txt
```
