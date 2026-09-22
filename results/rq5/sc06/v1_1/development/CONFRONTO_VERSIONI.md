# RQ5 / SC06 — confronto rq5-sc06-v1.0 contro rq5-sc06-v1.1

Stessi dati, stesso split, stessi distrattori, stesso oracle. Cambia soltanto l'istruzione di sistema.

## gemma3:4b

| Metrica | rq5-sc06-v1.0 | rq5-sc06-v1.1 |
|---|---|---|
| Exact Match (sufficiente) | 92/108 (85.2%) | 90/108 (83.3%) |
| Exact Match famiglia asset | 10/25 (40.0%) | 10/25 (40.0%) |
| Astensione corretta | 87/108 (80.6%) | 93/108 (86.1%) |
| Errori di formato (suff.) | 0/108 (0.0%) | 0/108 (0.0%) |
| Errori di formato (insuff.) | 0/108 (0.0%) | 0/108 (0.0%) |
| Valori non supportati (suff.) | 15/108 (13.9%) | 17/108 (15.7%) |
| Valori non supportati (insuff.) | 21/108 (19.4%) | 15/108 (13.9%) |
| Intrusioni fra casi (suff.) | 0/74 (0.0%) | 0/74 (0.0%) |
| Intrusioni fra casi (insuff.) | 14/74 (18.9%) | 10/74 (13.5%) |
| Etichette divise o senza prefisso | 21 | 24 |
| Etichette abbreviate | 1 | 1 |
| Celle con almeno una frammentazione | 15 | 15 |
| Tempo mediano (s) | 0.38 | 0.48 |
| Tempo p95 (s) | 0.51 | 0.61 |
| Token/s mediani | 51.5 | 51.1 |
| Risposte con tempi | 216 | 216 |

## llama3.2:3b

| Metrica | rq5-sc06-v1.0 | rq5-sc06-v1.1 |
|---|---|---|
| Exact Match (sufficiente) | 84/108 (77.8%) | 89/108 (82.4%) |
| Exact Match famiglia asset | 6/25 (24.0%) | 11/25 (44.0%) |
| Astensione corretta | 88/108 (81.5%) | 87/108 (80.6%) |
| Errori di formato (suff.) | 1/108 (0.9%) | 1/108 (0.9%) |
| Errori di formato (insuff.) | 1/108 (0.9%) | 1/108 (0.9%) |
| Valori non supportati (suff.) | 23/107 (21.5%) | 18/107 (16.8%) |
| Valori non supportati (insuff.) | 19/107 (17.8%) | 20/107 (18.7%) |
| Intrusioni fra casi (suff.) | 2/74 (2.7%) | 1/74 (1.4%) |
| Intrusioni fra casi (insuff.) | 16/74 (21.6%) | 15/73 (20.5%) |
| Etichette divise o senza prefisso | 27 | 18 |
| Etichette abbreviate | 0 | 0 |
| Celle con almeno una frammentazione | 17 | 12 |
| Tempo mediano (s) | 0.26 | 0.25 |
| Tempo p95 (s) | 0.52 | 0.48 |
| Token/s mediani | 58.9 | 60.0 |
| Risposte con tempi | 216 | 216 |

## Esempi di frammentazione osservata

- rq5-sc06-v1.0 — llama3.2:3b: atteso `S - Web application`, restituito `['S']`
- rq5-sc06-v1.0 — gemma3:4b: atteso `P - Human resources`, restituito `['Human resources']`
- rq5-sc06-v1.0 — llama3.2:3b: atteso `P - Human resources`, restituito `['P']`
- rq5-sc06-v1.0 — gemma3:4b: atteso `S - Web application`, restituito `['File', 'Web application']`
- rq5-sc06-v1.1 — llama3.2:3b: atteso `S - Web application`, restituito `['S']`
- rq5-sc06-v1.1 — gemma3:4b: atteso `P - Human resources`, restituito `['Human resources']`
- rq5-sc06-v1.1 — llama3.2:3b: atteso `P - Human resources`, restituito `['P']`
- rq5-sc06-v1.1 — gemma3:4b: atteso `S - Web application`, restituito `['File', 'Web application']`

## Come leggere questo confronto

- La v1.1 non cambia dataset, domande, distrattori, oracle, modelli, parametri, schema o metriche: l'unica differenza e' l'istruzione.
- Lo scopo dichiarato della v1.1 e' togliere un'ambiguita' sul formato delle etichette, non far salire un punteggio.
- Lo split di sviluppo e' 12 episodi: serve a controllare il meccanismo, non a stabilire un risultato.
