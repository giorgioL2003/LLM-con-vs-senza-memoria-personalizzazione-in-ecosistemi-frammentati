# RQ3 / SC07 — verifica dello sviluppo

**Data della verifica:** 23 settembre 2026  
**Stato:** sviluppo completato e verificato; valutazione finale non ancora eseguita.

Questo documento conserva l'esito della prova di sviluppo. I numeri riportati servono a decidere se la pipeline può passare alla valutazione finale e **non sono i risultati conclusivi di RQ3**.

## Esecuzione

- Modello richiesto: `claude-sonnet-5`.
- Modello realmente usato: `claude-sonnet-5`.
- Canale: Claude Code CLI, effort `medium`, nessun fallback.
- Celle previste e prodotte: **36/36**.
- Chiamate reali: **23/23**, tutte riuscite.
- Celle con prompt identico riutilizzate: **13**.
- Errori di trasporto o generazione: **0**.
- Risposte con formato non valido: **0**.

## Metriche di sviluppo

| Metrica | Memoria separata | Memoria condivisa/interlacciata |
|---|---:|---:|
| Exact Match | 18/18 (100%) | 18/18 (100%) |
| Evidenza raggiungibile | 18/18 (100%) | 18/18 (100%) |
| Retrieval success | 18/18 (100%) | 18/18 (100%) |
| Risposta supportata | 18/18 (100%) | 18/18 (100%) |
| Confusione fra attività | 0/18 | 0/18 |
| Messaggi contaminanti nel contesto | 0/36 (0%) | 4/36 (11,1%) |

Il confronto appaiato dello sviluppo produce una differenza di Exact Match pari a **0,0 punti percentuali**. Questo dato non va interpretato come risultato finale perché deriva da soli tre episodi di sviluppo.

## Controlli indipendenti

- Validatore offline: **70/70 controlli superati**.
- Test automatici: **62/62 superati**.
- Coerenza del riuso: verificata.
- Modifiche alle RQ precedenti: nessuna rilevata.
- File di risposte della valutazione finale: assente.
- Gate della valutazione finale: assente al momento della verifica.

## Artefatti conservati

| Artefatto | Contenuto | SHA-256 |
|---|---|---|
| `raw_responses.jsonl` | risposte grezze e celle riutilizzate | `dc8c7cc68a1a62d63403d894b3624ecbcc818f512933169c068e63453d75c25c` |
| `evaluations.jsonl` | valutazione deterministica delle 36 celle | `78dc99314806b46f49ed75c3c55e2c8ee0038c8d9524fbd2162b561f04b4c4b0` |
| `summary.json` | metriche strutturate | `f55e1eecf9824453da1d6d3a06b2a8d2975769323eb964ae852423e4365830e0` |
| `summary.csv` | metriche tabellari | `ede586793c8e4dce921c8cfbc32903c149970746db5800396a82cf3158c771e0` |
| `SINTESI.md` | riepilogo prodotto dalla pipeline | `5cf91daa4f1ca85588ed19ca6a321d0f4119f453dd289bcafe2352b11d83e24a` |
| `run_manifest.json` | modello, comando, conteggi e ambiente | `20c6d2c3032b16de59d1fe6e6204c23e52657bad1509e81355e030a7db9eb381` |

Configurazione usata: `data/rq3/config/rq3_sc07_v1.json`, SHA-256 `480a49c3ee5ccbc0ba42be47e20eec3537adb0e1e66f2d34deb25d43bd6b0f7a`.

## Decisione operativa

Lo sviluppo non ha evidenziato problemi di dati, retrieval, formato o generazione. La pipeline è pronta per la valutazione finale, che dovrà essere autorizzata separatamente e produrrà 240 celle mediante 139 chiamate reali e 101 riusi.
