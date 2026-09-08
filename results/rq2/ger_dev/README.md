# Verifica offline della memoria gerarchica GER

**Non sono risultati sperimentali.** Nessun modello è stato chiamato: nessuna
risposta è stata generata, e la memoria di SC05 nasce da **fixture dichiarate**
scritte a mano, non da un'uscita del modello. Le prove precedenti
(`results/rq2/memory/`, `graph/`, `memory_repair_v3/`, `retrieval_repair_v3/`,
`sc04_repair_v3/`, `offline_check/`) non sono state toccate.

Comando:

```bash
python3 scripts/rq2/run_ger_check.py
```

## Input e versioni

| | |
|---|---|
| regole di GER | `ger-rules-0.1`, scritte in `MEMORIA_GERARCHICA.md` |
| finestra di recenza | 2 sessioni |
| quote | 100 / 100 token su un budget di 200 |
| budget, conteggio, ranking, istruzioni di risposta | invariati rispetto a U |
| stato di U per SC03 | `results/rq2/memory_repair_v3/scenario_03_state.json` (istruzioni `u-instructions-0.3`) |
| stato di U per SC04 | `results/rq2/sc04_repair_v3/scenario_04_state.json` (istruzioni `u-instructions-0.3`) |
| stato di U per SC05 | costruito qui in `memory/`, dalle fixture, con il codice vero di `build_memory_updates.py` |
| fixture di SC05 | `tests/fixtures/rq2/scenario_05_facts_fixture.jsonl`, `..._update_answers_fixture.json` |
| etichetta | `fixture-ger (nessuna chiamata al modello)` |

## File

- `memory/scenario_05_*` — operazioni, stato e registro di U per SC05 (30 proposte, 30 applicate, 0 rifiutate)
- `retrieval_ger.jsonl` — 42 righe: 7 domande × U e GER × SC03, SC04, SC05
- `generation_inputs_sc05.jsonl` — 21 prompt (U, GER, FULL_HISTORY) **costruiti e mai inviati**, `model_answer` sempre `null`
- `traccia_ger_sc05.md` — traccia leggibile: elementi selezionati, livello, punteggio, consumo del budget, motivi di esclusione, righe riportate per intero

## Che cosa mostra la partizione su SC05

Nove sessioni, 26 voci di memoria, ultima sessione 9. Con una finestra di due
sessioni: **6 voci recenti** (sessioni 8-9) e **20 in archivio** (sessioni 1-7).
La storia completa misura **645 token contro un budget di 200**: il retrieval
deve davvero scegliere, e l'archiviazione viene esercitata.

I due assi restano indipendenti, come previsto: 17 voci in archivio sono ancora
`attive` (fra cui il vincolo sul rapporto della sessione 1) e una voce dentro la
finestra recente è già `superata`.

## Correttezza tecnica (verificata)

- budget rispettato in tutte e 21 le prove GER; nessun doppione, nessun
  troncamento; il blocco formattato misura i token dichiarati;
- i punteggi di GER coincidono voce per voce con quelli di U: il ranking è
  calcolato prima della divisione;
- U e GER leggono lo stesso numero di voci con lo stesso ambito corrente/storia;
- lo spazio avanzato viene davvero riutilizzato in **8 prove su 21**;
- gli stati salvati sono identici dopo il retrieval: **recuperare una voce non la
  rende recente**.

## Beneficio sperimentale: non verificato

Nessuna risposta è stata generata, quindi **non si può dire se GER aiuti**. Quel
che si vede oggi nelle sole tracce:

| | elementi | contenuto | overhead |
|---|---:|---:|---:|
| SC05 U | 6,0 | 97,6 | 90,0 |
| SC05 GER | 5,6 | 87,0 | 94,7 |
| SC03 U | 6,6 | 86,4 | 98,6 |
| SC03 GER | 6,0 | 77,1 | 102,0 |
| SC04 U | 5,4 | 101,1 | 81,4 |
| SC04 GER | 5,1 | 89,9 | 87,4 |

**A parità di budget GER porta meno contenuto di U**: l'etichetta di livello
costa circa due token per elemento. È un costo dell'architettura, contato
apposta, non un difetto nascosto — lo stesso fenomeno già osservato su G.

Tre osservazioni che valgono più dei conteggi:

1. **SC05-Q4, la domanda a due livelli.** GER porta nel contesto due voci
   recenti che U non aveva, e il vincolo della sessione 1 c'è in tutte e due le
   modalità. Ma la voce recente che serve davvero (`SC05-M029`, «resta aperta
   soltanto la revisione delle regole di esportazione») **resta fuori in
   entrambe**. L'indicatore automatico dichiara `evidence_provenance_complete:
   true` per GER perché `SC05-M028` cita lo stesso messaggio sorgente **dicendo
   un'altra cosa**: è di nuovo il falso positivo di provenienza già registrato
   nella sezione 9.4 di `RQ2.md`, qui su uno scenario nuovo.
2. **SC05-Q5, la quota recente sprecata.** Tutte le voci recenti hanno punteggio
   nullo: la domanda dice «verifiche… completate», la memoria dice «la verifica…
   è completata», e il tokenizzatore non fa radice. La memoria recente resta a
   0/100 token e il suo spazio finisce all'archivio. GER non risolve la soglia
   sul punteggio nullo: **la eredita**.
3. **Su SC03, GER perde copertura di provenienza in due domande su sette**
   (Q2 e Q3) rispetto a U. Non è una misura di qualità delle risposte, ma è il
   segnale che riservare metà budget può togliere spazio a informazioni vecchie
   decisive: esattamente il rischio dichiarato in progettazione.

## Che cosa va controllato prima di una prova reale

1. **Annotazioni di SC05**: domande, risposte attese, fatti obbligatori ed
   evidenze sono una **bozza** (`data/rq2/annotations/scenario_05_rq2.json`,
   `review_status: bozza da rivedere`). Vanno lette e corrette.
2. **SC05-Q5**: la formulazione al plurale («verifiche completate») non incontra
   il testo della memoria al singolare. Va deciso se è la domanda a essere
   scritta male o se è la soglia sul punteggio nullo a dover cambiare — e la
   decisione non va presa guardando quale delle due fa vincere GER.
3. **Finestra di due sessioni su nove**: solo 6 voci su 26 sono recenti. Se la
   finestra resta 2, la quota recente sarà spesso sottoutilizzata.
4. **Ripartizione 50/50** e **etichetta di livello**: entrambe costano, entrambe
   sono ipotesi.
5. **Regola di arresto**: come in U ci si ferma al primo elemento che non entra,
   anche in fase 2. Su SC05-Q4 restano 31 token liberi mentre il candidato
   successivo ne chiedeva 28. È la regola di U applicata due volte, non
   un'eccezione nuova: va confermata o cambiata **per U e GER insieme**.
6. **Contenuto, non provenienza**: i campi `*_by_provenance` restano inaffidabili
   come già dichiarato per U e G. La traccia riporta le righe per intero proprio
   per poterle leggere.
