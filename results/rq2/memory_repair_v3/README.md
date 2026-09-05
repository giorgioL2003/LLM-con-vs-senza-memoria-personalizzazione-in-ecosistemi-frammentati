# Prova di sviluppo — U su SC03 con passata di riparazione (istruzioni 0.3)

**Non sono i risultati dell'esperimento.** La prova reale precedente resta
immutata in `results/rq2/memory/`; la prova intermedia è in `memory_repair_v2/`.

- fatti candidati: `results/rq2/facts/scenario_03_facts.jsonl` (gli stessi di F, non riestratti)
- istruzioni: `u-instructions-0.3` = 0.2 più la richiesta esplicita di rispondere
  con un array JSON anche quando il fatto da rivalutare è uno solo
- `repair_attempts`: 1
- chiamate al modello: 5 (4 sessioni + 1 riparazione)
- esito: 42 operazioni, 41 applicate, 1 rifiutata e poi riproposta con successo;
  nessun fatto candidato resta senza operazione applicata

Versione del codice, delle istruzioni e della configurazione: campi
`code_sha256`, `instructions_version`, `instructions_sha256`, `config_id`,
`model`, `effort`, `label` in `scenario_03_update_log.json`.
