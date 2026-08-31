# Comandi per la dimostrazione

Sequenza minima per mostrare che il pilot è riproducibile, senza modificare
nulla e senza consumare utilizzo del modello.

**Cosa serve:** solo Python 3 con la libreria standard. Nessuna dipendenza da
installare, nessuna chiave API.

Tutti i comandi qui sotto sono in **sola lettura**: validano e ricalcolano in
memoria, ma non riscrivono scenari, risultati, metriche o classificazioni.

## 0. Entrare nella cartella del progetto

```bash
cd /Users/giorgiolai/Desktop/progetto_tirocinio
```

## 1. Validare gli scenari

```bash
python3 scripts/validate_scenarios.py
```

Controlla i due scenari JSON: campi obbligatori, unicità degli identificatori,
ordine di sessioni e messaggi, esistenza delle evidenze, coerenza dei perimetri
di C0/C1/C2 con la raggiungibilità dichiarata e copertura complessiva attesa
(0/14, 5/14, 12/14).

**Cosa mostra:** che il benchmark è integro e che la matrice di raggiungibilità
non è stata alterata. Stampa una riga per scenario ed esce con codice `0`.

## 2. Controllare le metriche aggregate

```bash
python3 scripts/summarize_evaluation.py --check
```

Rilegge le 56 annotazioni, verifica che siano coerenti con il retrieval e con
gli input di generazione, e ricalcola le metriche di C0, C1 e C2.

**Cosa mostra:** che le metriche pubblicate in `pilot/metrics_pilot.md` derivano
davvero dai dati e non sono state scritte a mano. Con `--check` i file **non**
vengono riscritti.

Da notare durante la demo: la Retrieval Success Rate di C0 vale `non calcolabile`
e non `0%`, perché in C0 nessuna domanda è raggiungibile e il denominatore è zero.

## 3. Controllare l'analisi causale degli errori

```bash
python3 scripts/build_error_analysis.py --check
```

Ricostruisce le tracce dei due fallimenti del pilot e verifica che la causa
dichiarata sia sostenuta dai dati: `reachability` richiede evidenze fuori dal
perimetro, `retrieval` richiede evidenze accessibili ma non recuperate.

**Cosa mostra:** che i due errori cadono in due punti diversi della pipeline —
SC02-Q6/C1 per il perimetro della memoria, SC02-Q6/C2 per il ranking del
retrieval — e che l'analisi non contraddice le classificazioni approvate. Con
`--check` i file **non** vengono riscritti.

## 4. Eseguire tutti i test

```bash
python3 -m unittest discover -s tests -v
```

Esegue l'intera suite: validatore degli scenari, retrieval, generazione (con un
runner finto, senza chiamate reali), metriche e analisi degli errori. Molti test
verificano corruzioni intenzionali dei dati, che devono essere segnalate.

**Cosa mostra:** che i controlli funzionano davvero, perché sanno riconoscere sia
i dati corretti sia quelli sbagliati.

## 5. Leggere i risultati

Nessun comando: sono documenti Markdown già pronti.

| File | Contenuto |
|---|---|
| `pilot/pilot_summary.md` | stato complessivo e storia del pilot |
| `pilot/metrics_pilot.md` | metriche di C0, C1, C2 con formule e denominatori |
| `pilot/error_analysis_pilot.md` | tracce complete dei due fallimenti |

---

## Comando opzionale: rigenerare le 56 risposte

> ⚠️ **Non fa parte della demo.** La generazione chiama Claude e consuma
> utilizzo. Le risposte del pilot sono già state generate e salvate:
> rigenerarle produrrebbe testi diversi e renderebbe incoerenti valutazione,
> metriche e analisi degli errori già prodotte.

Il comando che ha prodotto le risposte del pilot è:

```bash
python3 scripts/run_generation.py
```

Eseguito così com'è **non fa nulla e non consuma utilizzo**: lo script rilegge
`results/generation_pilot.jsonl` e salta le prove già completate, quindi stampa
`Niente da fare`. Questo è di per sé un buon comando da mostrare, perché rende
evidente che le 56 risposte sono già state generate una volta sola e conservate.

Se durante il confronto serve davvero mostrare una chiamata dal vivo, si scrive
su un file separato, così il risultato del pilot non viene toccato:

```bash
python3 scripts/run_generation.py --limit 1 --out results/generation_demo.jsonl
```

Questa esegue **una** chiamata e crea un file nuovo, che può essere cancellato
subito dopo. Rigenerare invece tutte e 56 le risposte obbligherebbe a rifare a
mano la valutazione e a ricalcolare metriche e analisi degli errori.
