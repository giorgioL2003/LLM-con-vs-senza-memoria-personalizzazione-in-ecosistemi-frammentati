# Prova di sviluppo — SC04 con U ricostruito (`u-instructions-0.3`)

**Non sono i risultati dell'esperimento.** La prova precedente resta immutata in
`results/rq2/memory/`, `results/rq2/graph/`, `results/rq2/retrieval_sc04.jsonl`,
`results/rq2/generation_dev_sc04.jsonl`.

## Input, versioni, chiamate

| | |
|---|---|
| fatti candidati | `results/rq2/facts/scenario_04_facts.jsonl` (**non riestratti**) |
| stato di U | prodotto qui, `scenario_04_state.json` |
| base di G | lo **stesso** stato di U (`state_source` lo dichiara) |
| istruzioni di U | `u-instructions-0.3`, sha `919b6c7ee5e4f53c` |
| impronta del codice di U | `01489de9e6d1a0d5` |
| configurazione | `data/rq2/config/experiment_rq2.json`, `rq2-dev-0.1` |
| modello / effort | `claude-sonnet-5` / `medium` |
| budget, ranking, parametri di G | invariati (200 token, TF-IDF, `max_hops` 3, semi 3) |
| etichetta | `prova-riparazione-u-instructions-0.3` |
| **chiamate effettive** | **21** = 6 per U (4 sessioni + 2 riparazioni) + 1 per G + 14 risposte |

FULL_HISTORY non è stata rigenerata: le risposte precedenti restano il riferimento
diagnostico.

## 1. Completezza ed errori

7 domande × U e G in retrieval, prompt e risposte: 14 righe per file, **0 errori
di chiamata**, nessuna risposta vuota, nessun errore di parsing.

**Operazioni di U:** 41 proposte (32 ADD, 7 UPDATE, 2 NOOP), 38 applicate,
**3 rifiutate e tutte e 3 recuperate** dalla passata di riparazione. Tutti i
rifiuti sono `UPDATE senza target_entry_id`; nessuno indica più un `fact_id` al
posto di una voce. **Nessun fatto candidato resta senza operazione applicata.**

Nella riparazione il modello ha ridecidiso davvero, non solo ricorretto il
riferimento: `SC04-OP038` (UPDATE invalido) è tornato come **NOOP** applicato.

## 2. Fatti persi e informazione superata tenuta per attuale

Nessun fatto perso. Quattro supersessioni tracciate: spam→corretta,
nessun-contatto→contatto avvenuto, e due consolidamenti interni alla sessione 3
(accesso anomalo e regola di inoltro), effetto della nuova regola sull'ordine di
applicazione.

**Il caso RULE-01 non cambia:** la rimozione resta un ADD separato
(`SC04-M033`, `rule01-rimozione`) accanto alla creazione ancora attiva
(`SC04-M032`), senza collegamento fra le due. Le istruzioni nuove non toccano
questo comportamento — conferma che è la questione aperta «eventi o stati», non
un difetto delle istruzioni.

## 3. Grafo

10 nodi, 16 archi. Nessun nodo o arco cita fatti inesistenti. **4 archi con
provenienza non valida**, tutti per lo stesso motivo di prima: l'oggetto è un
valore letterale e non un nodo dichiarato (`smishing`, `spam generico`, `08:05`,
`gateway aziendale`).

Migliora la struttura: compare l'arco `RULE-01 configurata_su ACC-207`, che nel
grafo precedente **mancava** ed era la relazione `SC04-R08` dell'oracle.

Peggiora l'ancoraggio: **nessuna delle 7 domande trova nodi dal proprio testo**
(prima 1 su 7, grazie al nodo `RIEPILOGO-01` che ora non esiste). **Gli alias
restano vuoti su tutti e 10 i nodi.** I nodi iniziali vengono quindi solo dalle
voci di U.

Difetto nuovo da registrare: `SC04-E014 RULE-01 -rimossa-> ACC-207` ha stato
`superato`, che dice che *l'arco* è stato superato, non che la regola è stata
rimossa.

## 4. Budget e contenuto

Budget rispettato in tutte e 14 le prove (159–199 token), nessun superamento per
primo elemento, provenienza tracciata su ogni elemento. Sovraccarico di G ancora
superiore a quello di U (105 contro 81 token medi).

Presenza **verificata sul testo** degli elementi selezionati, non sulla
provenienza:

| | U ora / prima | G ora / prima |
|---|---|---|
| Q2 (smishing, spam, contatto) | 2/3 = 2/3 | **2/3 ← 1/3** |
| Q3 (SMS-01, URL-01, ACC-207, LOGIN-07, RULE-01) | 4/5 = 4/5 | 3/5 = 3/5 (ma ora con `SMS-01`) |
| Q4 (rimossa, password, bloccato) | 1/3 = 1/3 | 1/3 = 1/3 |
| Q5 (revisione, riepilogo) | 1/2 = 1/2 | 1/2 = 1/2 |

## 5. Cambiamenti nelle risposte

**Una sola esecuzione: differenze osservate, non cause dimostrate.** Le risposte
variano anche a parità di contesto.

- **Q2 G migliora**: prima diceva di non avere informazioni sulle valutazioni
  superate, ora ne riporta una («spam generico»), ed è **sostenuta dal contesto**
  — l'arco `CASO-SC04 -valutato_inizialmente_come-> spam generico`, stato
  `superato`, leggibile perché Q2 è una domanda storica. Resta incompleta:
  l'altra valutazione superata non c'è. U copre l'altra metà e non questa: nessuna
  delle due è completa, e sono complementari.
- **Q3 U migliora sul piano delle affermazioni non supportate**: sparisce il ponte
  inventato «da questa segnalazione risulta la sessione LOGIN-07». Resta
  incompleta: mancano `SMS-01 contiene URL-01` e l'apertura del collegamento.
- **Q3 G cambia carattere**: prima dichiarava l'insufficienza e mostrava una
  scorciatoia via `CASE-01`; ora produce una catena con le entità giuste
  (UT-207 → ACC-207 → RULE-01) **senza dichiarare che è incompleta**. Più
  pertinente, meno prudente.
- **Q5 U migliora**: prima affermava che «resta da completare il riepilogo», che è
  un requisito e non l'attività aperta; ora dice che il contesto non lo specifica.
- **Q1, Q4, Q6, Q7 invariati** nella sostanza, in entrambe le modalità.

FULL_HISTORY resta molto sopra: risponde per intero a Q3, Q4 e Q5, dove U e G
restano parziali.

## Esito

Nessun problema tecnico bloccante. Questa è la **versione di riferimento di
sviluppo** per SC04, con i limiti elencati sopra: ancoraggio ai nodi a zero,
alias vuoti, archi con oggetti letterali, la questione «eventi o stati» aperta e
il ranking come collo di bottiglia principale. Non è una validazione del sistema
e il protocollo non è congelato.
