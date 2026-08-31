# Metriche aggregate del pilot

**Stato:** risultati del pilot, non conclusioni finali.  
**Ambito:** step 2 - calcolo delle metriche a partire dalle 56 annotazioni gia'
classificate. L'analisi causale dei fallimenti (EXPERIMENT.md, sezione 11) non fa parte di questo documento.

Documento generato da `scripts/summarize_evaluation.py`; il risultato machine-readable e' `results/metrics_pilot.json`.
Le definizioni delle metriche sono quelle di EXPERIMENT.md, sezioni 9 e 10.

## Avvertenza

Questi numeri descrivono un pilot di 14 domande su 2 scenari.
Il campione e' piccolo, le annotazioni sono una prima classificazione assistita
dall'AI e l'esperimento non e' congelato: i valori servono a verificare che la
pipeline misuri quello che deve misurare, non a sostenere conclusioni finali.

Quando il denominatore di una metrica e' zero, la metrica non e' calcolabile:
viene riportata come `null` e mai come zero (EXPERIMENT.md, sezioni 10.2 e 10.4).

## Sorgenti

| File | SHA-256 |
|---|---|
| `results/evaluation_pilot.jsonl` | `6a06f8a7e22b4e37edcb420a91ab2af733cdc52a39603bdb060f5d059023d845` |
| `results/generation_inputs.jsonl` | `b2703df19e119fb99d79dfeb73ae2684f23d6ad4cd1f70f287afc55034990f83` |
| `results/retrieval_pilot.jsonl` | `957b78a703d4c57a7e2ebc89d212d978c8161934bcd9098dba93a5b9b9bebf9d` |

## Condizioni sperimentali

C0, C1 e C2 sono le sole condizioni sperimentali principali.

### Condizione C0

- prove totali: 14
- domande raggiungibili: 0
- domande non raggiungibili: 14

| Classe della risposta | Conteggio | Proporzione |
|---|---|---|
| complete | 0 | 0 / 14 = 0 (0.0%) |
| partial | 0 | 0 / 14 = 0 (0.0%) |
| incorrect | 0 | 0 / 14 = 0 (0.0%) |
| correct_abstention | 14 | 14 / 14 = 1 (100.0%) |

| Metrica | Formula | Numeratore / Denominatore | Valore |
|---|---|---|---|
| Reachability Rate | domande raggiungibili / prove totali | 0 / 14 | 0.0% |
| Retrieval Success Rate | evidenza completa recuperata / domande raggiungibili | 0 / 0 | null (non calcolabile) |
| Complete Answer Rate | risposte complete / prove totali | 0 / 14 | 0.0% |
| Answer Success Rate | risposte complete con evidenza recuperata / domande con evidenza recuperata | 0 / 0 | null (non calcolabile) |
| Correct Abstention Rate | astensioni corrette / domande non raggiungibili | 14 / 14 | 100.0% |
| Obsolete Information Use Rate | risposte che usano informazioni obsolete / prove totali | 0 / 14 | 0.0% |
| Unsupported Claim Rate | risposte con almeno un fatto non supportato / prove totali | 0 / 14 | 0.0% |

### Condizione C1

- prove totali: 14
- domande raggiungibili: 5
- domande non raggiungibili: 9

| Classe della risposta | Conteggio | Proporzione |
|---|---|---|
| complete | 5 | 5 / 14 = 0.357143 (35.7%) |
| partial | 0 | 0 / 14 = 0 (0.0%) |
| incorrect | 1 | 1 / 14 = 0.071429 (7.1%) |
| correct_abstention | 8 | 8 / 14 = 0.571429 (57.1%) |

| Metrica | Formula | Numeratore / Denominatore | Valore |
|---|---|---|---|
| Reachability Rate | domande raggiungibili / prove totali | 5 / 14 | 35.7% |
| Retrieval Success Rate | evidenza completa recuperata / domande raggiungibili | 5 / 5 | 100.0% |
| Complete Answer Rate | risposte complete / prove totali | 5 / 14 | 35.7% |
| Answer Success Rate | risposte complete con evidenza recuperata / domande con evidenza recuperata | 5 / 5 | 100.0% |
| Correct Abstention Rate | astensioni corrette / domande non raggiungibili | 8 / 9 | 88.9% |
| Obsolete Information Use Rate | risposte che usano informazioni obsolete / prove totali | 0 / 14 | 0.0% |
| Unsupported Claim Rate | risposte con almeno un fatto non supportato / prove totali | 1 / 14 | 7.1% |

### Condizione C2

- prove totali: 14
- domande raggiungibili: 12
- domande non raggiungibili: 2

| Classe della risposta | Conteggio | Proporzione |
|---|---|---|
| complete | 11 | 11 / 14 = 0.785714 (78.6%) |
| partial | 1 | 1 / 14 = 0.071429 (7.1%) |
| incorrect | 0 | 0 / 14 = 0 (0.0%) |
| correct_abstention | 2 | 2 / 14 = 0.142857 (14.3%) |

| Metrica | Formula | Numeratore / Denominatore | Valore |
|---|---|---|---|
| Reachability Rate | domande raggiungibili / prove totali | 12 / 14 | 85.7% |
| Retrieval Success Rate | evidenza completa recuperata / domande raggiungibili | 11 / 12 | 91.7% |
| Complete Answer Rate | risposte complete / prove totali | 11 / 14 | 78.6% |
| Answer Success Rate | risposte complete con evidenza recuperata / domande con evidenza recuperata | 11 / 11 | 100.0% |
| Correct Abstention Rate | astensioni corrette / domande non raggiungibili | 2 / 2 | 100.0% |
| Obsolete Information Use Rate | risposte che usano informazioni obsolete / prove totali | 0 / 14 | 0.0% |
| Unsupported Claim Rate | risposte con almeno un fatto non supportato / prove totali | 0 / 14 | 0.0% |

## Confronto sintetico tra le condizioni

| Metrica | C0 | C1 | C2 |
|---|---|---|---|
| Reachability Rate | 0.0% (0 / 14) | 35.7% (5 / 14) | 85.7% (12 / 14) |
| Retrieval Success Rate | null (0 / 0) | 100.0% (5 / 5) | 91.7% (11 / 12) |
| Complete Answer Rate | 0.0% (0 / 14) | 35.7% (5 / 14) | 78.6% (11 / 14) |
| Answer Success Rate | null (0 / 0) | 100.0% (5 / 5) | 100.0% (11 / 11) |
| Correct Abstention Rate | 100.0% (14 / 14) | 88.9% (8 / 9) | 100.0% (2 / 2) |
| Obsolete Information Use Rate | 0.0% (0 / 14) | 0.0% (0 / 14) | 0.0% (0 / 14) |
| Unsupported Claim Rate | 0.0% (0 / 14) | 7.1% (1 / 14) | 0.0% (0 / 14) |

## Sezione diagnostica separata: FULL_HISTORY

FULL_HISTORY e' un controllo diagnostico separato, non una quarta condizione sperimentale: non applica la procedura di retrieval e non ha metriche di retrieval.

I valori qui sotto non vanno confrontati con C0, C1 e C2 come se fossero una
quarta condizione: servono solo a osservare il comportamento del modello quando
riceve l'intero storico senza selezione.

### Controllo FULL_HISTORY

- prove totali: 14
- domande raggiungibili: 12
- domande non raggiungibili: 2

| Classe della risposta | Conteggio | Proporzione |
|---|---|---|
| complete | 12 | 12 / 14 = 0.857143 (85.7%) |
| partial | 0 | 0 / 14 = 0 (0.0%) |
| incorrect | 0 | 0 / 14 = 0 (0.0%) |
| correct_abstention | 2 | 2 / 14 = 0.142857 (14.3%) |

| Metrica | Formula | Numeratore / Denominatore | Valore |
|---|---|---|---|
| Reachability Rate | domande raggiungibili / prove totali | 12 / 14 | 85.7% |
| Complete Answer Rate | risposte complete / prove totali | 12 / 14 | 85.7% |
| Correct Abstention Rate | astensioni corrette / domande non raggiungibili | 2 / 2 | 100.0% |
| Obsolete Information Use Rate | risposte che usano informazioni obsolete / prove totali | 0 / 14 | 0.0% |
| Unsupported Claim Rate | risposte con almeno un fatto non supportato / prove totali | 0 / 14 | 0.0% |
