# Verifica offline di GER — regole `ger-rules-0.2`

**Non sono risultati sperimentali.** Nessun modello è stato chiamato: nessuna
risposta è stata generata, e la memoria di SC05 nasce da **fixture dichiarate**
scritte a mano. Le prove precedenti non sono state toccate, compresa la verifica
delle regole `0.1` in `results/rq2/ger_dev/`, che resta leggibile per confronto.

Comando (scrive qui per impostazione predefinita):

```bash
python3 scripts/rq2/run_ger_check.py
```

## Che cosa è cambiato rispetto alle regole `0.1`

Due comportamenti verificati in revisione e corretti prima delle prove reali.

**1. Budget rigoroso.** La `0.1` faceva entrare il primo candidato anche quando
superava da solo il budget (una voce da 240 token con limite 200). L'eccezione è
stata eliminata per GER: una voce troppo grande viene **esclusa** con il proprio
motivo nella traccia (`supera da sola l'intero budget: esclusa, non troncata`) e
compare in `ger_excluded_over_budget`; niente troncamenti; se non entra nessuna
voce il contesto resta **vuoto**. Come per ogni altro elemento che non entra, la
voce troppo grande **chiude la fase** in cui viene incontrata, perché la
selezione resta un prefisso della classifica: è la regola di U, applicata anche
qui.

L'eccezione di U (`budget_exceeded_by_first_item` in `select_within_budget`)
**non è stata toccata**, per non cambiare i risultati già prodotti da T, F, U e
G. La verifica controlla a ogni esecuzione che non si attivi in nessuno dei casi
usati per confrontare U e GER: nessuna voce di memoria arriva da sola a 200
token, quindi il confronto avviene a regole uguali.

**2. Recenza rispetto alla sessione raggiunta.** La finestra non si deduce più
dalla sessione più alta fra le voci salvate: la sessione raggiunta viene
**dichiarata** da chi lancia la valutazione (`--session-reached`). Così la
finestra avanza anche quando una sessione non produce aggiornamenti. Una
dichiarazione precedente alle voci salvate viene rifiutata; senza dichiarazione
GER ripiega sull'ultima sessione con voci e lo **scrive nella traccia**. Questa
verifica dichiara la sessione raggiunta solo dopo aver controllato che lo stato
copra tutte le sessioni della conversazione: su uno stato intermedio si rifiuta
di dedurla dallo scenario.

## Gli elementi recuperati non sono cambiati

Confronto riga per riga con `results/rq2/ger_dev/retrieval_ger.jsonl`
(42 righe, 3 scenari × 7 domande × U e GER):

| | |
|---|---|
| differenze negli elementi selezionati | **0** |
| differenze nei token di contesto | **0** |

Era il risultato atteso: nessuna voce di memoria di SC03, SC04 o SC05 arriva da
sola a 200 token, quindi la garanzia minima non si era mai attivata; e in tutti
e tre gli stati l'ultima sessione produce voci, quindi la sessione dichiarata
coincide con quella che la `0.1` deduceva. **Le correzioni servono ai casi che
non si sono ancora presentati**, non a cambiare questi.

Cambiano solo i campi della traccia: `ger_rules_version` passa a `ger-rules-0.2`
e compaiono `ger_session_reached`, `ger_session_reached_source`,
`ger_recency_window`, `ger_excluded_over_budget`.

## Input e configurazione

| | |
|---|---|
| regole | `ger-rules-0.2` (`MEMORIA_GERARCHICA.md`) |
| finestra di recenza | 2 sessioni |
| quote | 100 / 100 token su un budget di 200 |
| sessione raggiunta dichiarata | SC05 = 9, SC03 = 4, SC04 = 4 (stati che coprono tutte le sessioni) |
| budget, conteggio, ranking, soglia sul punteggio nullo, etichette | invariati |
| stato di U per SC03 | `results/rq2/memory_repair_v3/scenario_03_state.json` |
| stato di U per SC04 | `results/rq2/sc04_repair_v3/scenario_04_state.json` |
| stato di U per SC05 | costruito qui in `memory/`, dalle fixture, con il codice vero |

## Correttezza tecnica (verificata)

- budget rispettato in tutte e 21 le prove GER (massimo 197 token su 200) e
  **nessuna eccezione sul primo elemento**;
- sessione raggiunta dichiarata in tutte le prove (nessun ripiego);
- nessun doppione, nessun troncamento; il blocco formattato misura i token
  dichiarati;
- punteggi identici a quelli di U voce per voce: il ranking è calcolato prima
  della divisione;
- stesso ambito corrente/storia e stesso numero di voci leggibili di U;
- spazio avanzato riutilizzato in 8 prove su 21;
- stati salvati identici dopo il retrieval: recuperare una voce non la rende
  recente.

335 test passano, `validate_rq2.py` invariato, U e G su SC04 riproducono
esattamente la prova salvata in `sc04_repair_v3`.

## Beneficio sperimentale: non verificato

Nessuna risposta è stata generata: **non si può dire se GER aiuti**. Le
osservazioni sulle tracce restano quelle della verifica precedente, perché la
selezione non è cambiata:

| | elementi | contenuto | overhead |
|---|---:|---:|---:|
| SC05 U | 6,0 | 97,6 | 90,0 |
| SC05 GER | 5,6 | 87,0 | 94,7 |
| SC03 U | 6,6 | 86,4 | 98,6 |
| SC03 GER | 6,0 | 77,1 | 102,0 |
| SC04 U | 5,4 | 101,1 | 81,4 |
| SC04 GER | 5,1 | 89,9 | 87,4 |

1. **SC05-Q4, la domanda a due livelli.** GER porta due voci recenti che U non
   aveva, ma la voce che serve davvero (`SC05-M029`) resta fuori in entrambe.
   `evidence_provenance_complete` dice `true` per GER perché `SC05-M028` cita lo
   stesso messaggio sorgente **dicendo un'altra cosa**: è il falso positivo di
   provenienza della sezione 9.4 di `RQ2.md`, su uno scenario nuovo.
2. **SC05-Q5, la quota recente sprecata.** Tutte le voci recenti hanno punteggio
   nullo (la domanda dice «verifiche… completate», la memoria «la verifica… è
   completata»). GER eredita la soglia sul punteggio nullo, non la risolve.
3. **Su SC03 GER perde copertura di provenienza in due domande su sette**
   rispetto a U: riservare metà budget può togliere spazio a informazioni vecchie
   decisive. È il rischio dichiarato in progettazione.

## Che cosa va controllato prima di una prova reale

1. **Annotazioni di SC05**: bozza da leggere e correggere
   (`data/rq2/annotations/scenario_05_rq2.json`).
2. **SC05-Q5**: decidere se è la domanda scritta male o la soglia sul punteggio
   nullo a dover cambiare — senza guardare quale delle due fa vincere GER.
3. **Finestra di due sessioni su nove**: solo 6 voci su 26 sono recenti.
4. **Ripartizione 50/50** ed **etichetta di livello**: costano, sono ipotesi.
5. **Regola di arresto**: ci si ferma al primo elemento che non entra, in fase 1
   e in fase 2. Su SC05-Q4 restano 31 token liberi mentre il candidato successivo
   ne chiedeva 28. Se si cambia, va cambiata **per U e GER insieme**.
6. **Contenuto, non provenienza**: i campi `*_by_provenance` restano
   inaffidabili. La traccia riporta le righe per intero per poterle leggere.
