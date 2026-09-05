# Prova di sviluppo — U su SC03 con passata di riparazione (istruzioni 0.2)

**Non sono i risultati dell'esperimento.** La prova reale precedente resta
immutata in `results/rq2/memory/`.

- fatti candidati: `results/rq2/facts/scenario_03_facts.jsonl` (gli stessi di F, non riestratti)
- istruzioni: `u-instructions-0.2` — chiariscono `fact_id` contro `target_entry_id` e l'ordine di applicazione
- `repair_attempts`: 1 — le proposte rifiutate tornano al modello con lo stato aggiornato
- chiamate al modello: 6 (4 sessioni + 2 riparazioni)
- esito: 42 operazioni, 40 applicate, 2 rifiutate; l'informazione sui 240 MB è stata recuperata

**Difetto emerso qui:** nella riparazione della sessione 4 il modello ha risposto
con un oggetto JSON singolo invece di un array, e il parser l'ha scartato: il
fatto `SC03-F041` è andato perso. La correzione è in `u-instructions-0.3`, provata
in `results/rq2/memory_repair_v3/`. Questa cartella resta come traccia del difetto.

Versione del codice, delle istruzioni e della configurazione: campi
`code_sha256`, `instructions_version`, `instructions_sha256`, `config_id`,
`model`, `effort`, `label` in `scenario_03_update_log.json`.
