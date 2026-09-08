# Prima prova reale di sviluppo U / GER / FULL_HISTORY su SC05

**Prova di sviluppo SC05 eseguita e valutata; giudizi approvati dallo studente. Protocollo finale della tesi non congelato. Prossimo passo: consolidamento delle conoscenze e confronto con il relatore.**

Criteri di valutazione e giudizi sulle 21 risposte approvati dallo studente
(annotazione `sc05-rq2-ger-0.2`); chiamate autorizzate per questa sola prova.
**Non è approvazione del relatore.** Sono risultati di sviluppo: una sola
esecuzione, sette domande, nessuna replica.

**39 chiamate** a `claude-sonnet-5`: 9 di estrazione, 9 di aggiornamento,
**0 riparazioni** (nessuna operazione rifiutata), 21 risposte. Più una sonda di
autenticazione da una riga, fuori dal conteggio dell'esperimento. Nessun errore
di esecuzione, nessun errore di parsing, nessuna risposta vuota, nessun modello
di ripiego: nei registri il modello che ha prodotto ogni risposta è
`claude-sonnet-5`.

## Esito in breve

| | fatti | operazioni | stato | retrieval | risposte |
|---|---|---|---|---|---|
| | 41, provenienza valida | 41 proposte, 41 applicate, 0 rifiutate (27 ADD, 7 UPDATE, 7 NOOP, **0 DELETE**) | 34 voci: 27 attive, 7 superate | 14 righe, 158-199 token, budget sempre rispettato | 21 su 21 |

Con la sessione raggiunta dichiarata a 9: **8 voci recenti** (sessioni 8-9) e
**26 in archivio**.

**Rapporto di riferimento:**
[`valutazione_approvata_sc05.md`](valutazione_approvata_sc05.md) — giudizi
approvati dallo studente. La copia compilata riga per riga è
`annotation_compilata_sc05.jsonl`; il template originale
`annotation_template_sc05.jsonl` resta **intatto, con tutti i giudizi `null`**.
Le due versioni proposte prima dell'approvazione restano in
`valutazione_assistita_sc05.md` (revisione 1) e
`valutazione_assistita_sc05_rev2.md` (revisione 2).

Riepilogo in parole semplici per il confronto con il relatore:
[`chiusura_prova_sc05.md`](chiusura_prova_sc05.md).

**In sintesi:** successo tecnico pieno, nessun vantaggio di GER. Giudizi
approvati: U completa 2 domande su 7, GER 1; **FULL_HISTORY 6, ma con 645 token
di cronologia contro 200** — è un controllo diagnostico, non un confronto a
parità di budget. Nessuna delle 21 risposte ha usato informazione obsoleta, e in
sei domande su sette non avrebbe potuto: la politica di lettura rende le voci
superate accessibili solo alle domande storiche. Il collo di bottiglia è la
selezione, non la disponibilità: tutte le evidenze mancanti erano in memoria,
attive e corrette.

**La memoria di SC05 che esiste oggi viene da fixture scritte a mano**
(`tests/fixtures/rq2/scenario_05_*`, usate in `results/rq2/ger_dev/` e
`ger_dev_v2/`). **Non è memoria costruita da Claude** e non va presentata come
tale. La prova descritta qui la ricostruisce da zero con chiamate vere, in
questa cartella, senza toccare né le fixture né nessuna prova precedente.

Configurazione completa e verificata da un test:
`data/rq2/config/run_sc05_ger_dev.json` (`run_id: sc05-ger-dev-1`).

## Impostazioni

| | |
|---|---|
| scenario | `scenario_05`, 9 sessioni, 16 messaggi utente, 7 domande |
| modalità | **U** e **GER** a parità di budget; **FULL_HISTORY** come controllo diagnostico fuori budget |
| budget | 200 token sull'intero contesto formattato (etichette e metadati compresi) |
| ranking | TF-IDF/coseno, soglia sul punteggio nullo, parità e ordine di selezione invariati |
| GER | regole `ger-rules-0.2`, finestra 2 sessioni, quote 100/100, **sessione raggiunta dichiarata: 9** |
| memoria | `u-instructions-0.3` (sha `288ea8b51428c651`), `--repair-attempts 1` |
| modello | `claude-sonnet-5`, effort `medium`, per estrazione, aggiornamenti e risposte |
| etichetta | `prova-reale-sviluppo-sc05-v1` |

## Comandi (quelli davvero eseguiti, in quest'ordine)

### Prima: controlli offline (nessuna chiamata al modello)

```bash
python3 -m unittest discover -s tests && python3 scripts/rq2/validate_rq2.py && python3 scripts/rq2/run_ger_check.py
```

### Passo 1 — estrazione dei fatti · 9 chiamate

Una sessione alla volta, in ordine: il prompt della sessione *k* contiene le
istruzioni, i fatti già estratti e i soli messaggi utente della sessione *k*.
Niente domande, oracle, risposte attese o sessioni future.

```bash
python3 scripts/rq2/extract_facts.py --scenario scenario_05 --out-dir results/rq2/sc05_dev_v1/facts
```

### Passo 2 — costruzione di U · 9 chiamate + 1 per ogni sessione con rifiuti

Il modello propone ADD/UPDATE/DELETE/NOOP, il codice applica o rifiuta; le
proposte rifiutate tornano al modello una volta sola, con lo stato aggiornato.

```bash
python3 scripts/rq2/build_memory_updates.py --scenario scenario_05 --facts results/rq2/sc05_dev_v1/facts/scenario_05_facts.jsonl --out-dir results/rq2/sc05_dev_v1/memory --repair-attempts 1 --label prova-reale-sviluppo-sc05-v1
```

### Passo 3 — retrieval di U e GER sullo stesso stato · 0 chiamate

```bash
python3 scripts/rq2/run_retrieval_rq2.py --scenario scenario_05 --facts results/rq2/sc05_dev_v1/facts/scenario_05_facts.jsonl --state results/rq2/sc05_dev_v1/memory/scenario_05_state.json --session-reached 9 --modes U GER --label prova-reale-sviluppo-sc05-v1 --out results/rq2/sc05_dev_v1/retrieval_sc05_u_ger.jsonl
```

`--state` è lo stesso file per U e per GER: è ciò che rende il confronto a parità
di informazioni disponibili.

### Passo 4 — i 21 prompt · 0 chiamate

```bash
python3 scripts/rq2/build_generation_inputs_rq2.py --scenario scenario_05 --retrieval results/rq2/sc05_dev_v1/retrieval_sc05_u_ger.jsonl --modes U GER FULL_HISTORY --out results/rq2/sc05_dev_v1/generation_inputs_sc05.jsonl
```

Lo script controlla da sé che il contesto coincida con quello contato dal
retrieval, che il budget sia rispettato, che nel prompt non finiscano oracle o
altre domande e che FULL_HISTORY resti fuori budget e in ordine cronologico.

### Passo 5 — le 21 risposte · 21 chiamate

```bash
python3 scripts/run_generation.py --inputs results/rq2/sc05_dev_v1/generation_inputs_sc05.jsonl --out results/rq2/sc05_dev_v1/generation_dev_sc05.jsonl
```

Una chiamata per prompt, senza sessione, senza strumenti, senza modello di
ripiego. **Le risposte non rientrano in memoria**: ogni prova parte dallo stesso
stato salvato. Lo script è riprendibile: rilanciarlo salta le prove già fatte.

### Passo 6 — scheda di valutazione da compilare · 0 chiamate

```bash
python3 scripts/rq2/build_annotation_template_rq2.py --retrieval results/rq2/sc05_dev_v1/retrieval_sc05_u_ger.jsonl --inputs results/rq2/sc05_dev_v1/generation_inputs_sc05.jsonl --out results/rq2/sc05_dev_v1/annotation_template_sc05.jsonl
```

21 righe con i campi automatici già calcolati e **tutti i giudizi a `null`**:
`answer_class`, `obsolete_used`, `unsupported_claim`, `wrong_abstention`,
`error_origin`, più `fact_preserved_in_memory` e
`fact_content_correct_in_context` per ogni evidenza. Vanno compilati leggendo le
risposte e il **contenuto** delle righe di contesto: i campi `*_by_provenance`
dicono solo che il `message_id` giusto è citato, non che il fatto ci sia.

## Chiamate previste

| Fase | Chiamate |
|---|---:|
| estrazione dei fatti | 9 |
| costruzione di U | 9 |
| riparazioni | 0–9 (una per sessione con rifiuti; SC03 ne ha avuta 1, SC04 2) |
| risposte | 21 |
| **totale atteso** | **39–41** |

Retrieval, prompt e scheda di valutazione non chiamano nulla.

## Che cosa controllare a prova finita

1. **Gli invarianti** elencati in `run_sc05_ger_dev.json`: stesso stato e stesse
   voci leggibili per U e GER, punteggi identici, budget mai superato, sessione
   raggiunta dichiarata e non ripiegata, nessun oracle nei prompt.
2. **Le operazioni rifiutate**, se ce ne sono: contano come errori di gestione
   della memoria, non come guasti dello script.
3. **Il caso della verifica del bilanciatore**: aperta in S8, completata in S9.
   Se U la registra come evento nuovo invece che come UPDATE, la voce vecchia
   resta `attivo` e Q3 e Q4 possono riportarla come ancora aperta. È la questione
   «eventi o stati» aperta nella sezione 10 di `RQ2.md`: va osservata, non
   aggiustata.
4. **Il contenuto delle evidenze**, non la provenienza: nelle prove offline
   `SC05-M028` citava il messaggio giusto dicendo un'altra cosa.
5. Una sola esecuzione, nessuna replica: **differenze osservate, non cause
   dimostrate.**
