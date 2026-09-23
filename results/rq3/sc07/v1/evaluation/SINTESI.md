# RQ3 / SC07 — sintesi (evaluation)

Modello: Claude Sonnet 5 Chat (`claude-sonnet-5`, Claude Code CLI). Celle attese: 240; episodi: 20.

| Metrica | Memoria separata | Memoria condivisa | Denominatore |
|---|---:|---:|---|
| exact_match | 120/120 (100.0%) | 120/120 (100.0%) | tutte le celle attese |
| evidence_reachable | 120/120 (100.0%) | 120/120 (100.0%) | tutte le celle attese |
| retrieval_success | 120/120 (100.0%) | 120/120 (100.0%) | tutte le celle attese |
| missing_response | 0/120 (0.0%) | 0/120 (0.0%) | tutte le celle attese |
| format_error | 0/120 (0.0%) | 0/120 (0.0%) | celle con risposta |
| null_answer | 0/120 (0.0%) | 0/120 (0.0%) | celle con formato valido |
| null_despite_evidence | 0/120 (0.0%) | 0/120 (0.0%) | celle con formato valido ed evidenza recuperata |
| supported_answer | 120/120 (100.0%) | 120/120 (100.0%) | celle con valore non null |
| cross_activity_confusion | 0/0 (n/d) | 0/0 (n/d) | celle con valore non null errato |
| cross_activity_confusion_all_cells | 0/120 (0.0%) | 0/120 (0.0%) | tutte le celle attese |
| context_contamination | 0/240 (0.0%) | 17/240 (7.1%) | messaggi recuperati |

Chiamate reali: 139; celle con prompt identico riusato: 101; modelli usati: {'claude-sonnet-5': 240}.

## Confronto appaiato

Coppie: 120; entrambe corrette 120, solo separata 0, solo condivisa 0, nessuna 0.

- exact_match: +0.0 punti (shared_interleaved - separated), IC 95% bootstrap per episodio [+0.0; +0.0], 20 episodi.
- retrieval_success: +0.0 punti (shared_interleaved - separated), IC 95% bootstrap per episodio [+0.0; +0.0], 20 episodi.

## Attribuzione degli errori

| Categoria | Separata | Condivisa |
|---|---:|---:|
| missing_response | 0 | 0 |
| evidence_unreachable | 0 | 0 |
| retrieval | 0 | 0 |
| format | 0 | 0 |
| generation | 0 | 0 |

## Limiti

- Non si dimostra: universal behaviour of all datasets, retrievers or models.
- Non si dimostra: real enterprise conversations.
- Non si dimostra: stochastic variability of the model.
- Non si dimostra: comparison with other memory architectures.
- Una sola generazione per cella: la variabilità stocastica del modello non è misurata.
- Nessun p-value.
