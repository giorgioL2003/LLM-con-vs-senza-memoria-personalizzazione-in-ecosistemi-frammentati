# SC06 — verifica preliminare del dataset VERIS

**Stato:** fattibilità e progettazione concluse; protocollo RQ5/SC06 congelato e pronto per la realizzazione. Nessuna chiamata sperimentale SC06 è stata effettuata.

## Risultato in breve

VERIS offre una base concreta per studiare la memoria su molti casi di cybersecurity senza scrivere ogni incidente a mano. La copia esaminata contiene **2.445 schede candidate**, selezionate con criteri automatici dichiarati. Non sono 2.445 prove indipendenti: esistono campagne condivise e informazioni ripetute.

| Passaggio cumulativo | Schede rimaste |
|---|---:|
| Cartella upstream `validated` | 10.047 |
| Presenza di hacking, malware o social engineering | 4.040 |
| Incidente `Confirmed`, non marcato `Ineligible` | 4.008 |
| Identificativi non condivisi con altre schede | 3.952 |
| Presenza di almeno un riferimento HTTP/HTTPS | 3.900 |
| Almeno tre delle quattro famiglie tecniche sotto indicate | **2.445** |

Ci sono inoltre 7 schede `submitted`, escluse dall'analisi. `Validated` è una classificazione upstream relativa alla validazione dei dati: non certifica una verifica indipendente dei fatti. Il filtro tematico è una scelta operativa per SC06: anche altre categorie VERIS possono riguardare la cybersecurity.

## Quali informazioni possiamo usare

Le quattro famiglie sono: tipologia dell'azione, vettore dell'azione, risorse coinvolte, categorie di dati. Si conservano le etichette VERIS originali; i campi contenenti `Unknown`, `Other` o equivalenti non diventano risposte attese, nemmeno se mescolati a valori specifici.

| Campo | Schede candidate con valori utilizzabili |
|---|---:|
| Risorse coinvolte (anche persone, secondo la tassonomia VERIS) | 2.185 |
| Categorie di dati | 2.176 |
| Vettore dell'hacking | 1.983 |
| Tipologia dell'hacking | 1.492 |
| Tipologia del malware | 1.128 |
| Vettore del malware | 1.040 |
| Tipologia dell'ingegneria sociale | 455 |
| Vettore dell'ingegneria sociale | 435 |

I conteggi si sovrappongono. La soglia di tre famiglie è un criterio preliminare di sufficiente contenuto, da discutere prima di congelare il protocollo. Le risposte sono corrette **secondo la scheda**: i riferimenti sono conservati, ma non sono stati verificati uno per uno e possono essere obsoleti. Non si inventano valori per i campi mancanti.

## Quantità e varietà

- 747 candidate riportano la stessa descrizione relativa allo sfruttamento MOVEit.
- 88 riportano la stessa descrizione relativa alla campagna Red October.
- Complessivamente 952 candidate appartengono a 23 gruppi con descrizione identica non vuota.
- Esistono **717 combinazioni distinte dei campi tecnici utilizzabili**; questo numero non equivale al numero di incidenti indipendenti.
- Le date degli incidenti candidati vanno dal 2001 al 2026, con una distribuzione molto irregolare. Non è un campione rappresentativo degli attacchi odierni.

Le schede con descrizione uguale non sono state cancellate: possono riferirsi a vittime diverse. È però necessario raggruppare le campagne e limitare la loro concentrazione nella selezione sperimentale. Anche descrizioni diverse possono appartenere allo stesso evento: il controllo per testo identico non risolve da solo il problema.

## Esito della progettazione

SC06 è stato associato a RQ5. Il dataset selezionato comprende 708 casi organizzati in 236 episodi; 12 episodi sono riservati allo sviluppo e 224 alla valutazione. Gemma 3 4B IT e Llama 3.2 3B Instruct riceveranno, per ogni condizione, lo stesso contesto deterministico. Le due condizioni verificano l'uso di un'evidenza presente e l'astensione quando l'evidenza del caso richiesto manca.

Le conversazioni sono costruite; i fatti derivano dal dataset reale. Modelli, parametri, split, prompt, metriche e gate di esecuzione sono ora fissati nel protocollo corrente.

**Comandi di esecuzione:** [RQ5_SC06_ESECUZIONE.md](RQ5_SC06_ESECUZIONE.md) elenca gli script realizzati in `scripts/rq3/`, i controlli offline e i comandi per eseguire soltanto lo split di sviluppo. Gli input sono già costruiti in `sc06_rq5_v1/`; nessuna generazione è stata eseguita.

**Protocollo ora disponibile:** [RQ5_SC06_PROTOCOLLO.md](RQ5_SC06_PROTOCOLLO.md) associa SC06 a RQ5 e congela il confronto fra Gemma 3 4B IT e Llama 3.2 3B Instruct a parità di contesto. La [consegna per Claude Code](CLAUDE_CODE_HANDOFF.md) traduce le decisioni in requisiti operativi. Non sono state eseguite prove SC06 con i modelli. L'[esempio completo](sc06_design_v1/ESEMPIO.md) resta un esempio del dataset preparato.

## Provenienza e riproduzione

- Fonte: [VERIS Community Database, vz-risk e contributori](https://github.com/vz-risk/VCDB).
- Commit fissato: `230cf22b56a481dd1a994b21e4d94c59e2bccea9`, del 4 agosto 2026.
- Archivio originale: `source/vcdb/230cf22b56a481dd1a994b21e4d94c59e2bccea9.tar.gz`.
- URL, dimensione, SHA-256 e attribuzione: `source/vcdb/manifest.json`.
- Licenza dichiarata upstream: CC BY-SA 4.0; testo conservato in `source/vcdb/LICENSE.txt`. I record derivati mantengono l'attribuzione e la licenza della fonte.
- Record originali selezionati, senza riscrittura dei fatti: `vcdb_audit_v1/candidates.jsonl`.
- Ogni esclusione è documentata in `vcdb_audit_v1/exclusions.jsonl`, con il primo criterio non soddisfatto.
- Gruppi di descrizioni condivise: `vcdb_audit_v1/shared_summaries.json`.
- Conteggi e limiti: `vcdb_audit_v1/audit.json`.

Per rigenerare gli artefatti offline dalla copia conservata, dalla radice del progetto:

```sh
python3 scripts/rq3/audit_vcdb.py
```

La selezione usa solo `validated`; esclude tutte le schede coinvolte in identificativi `incident_id` o `plus.master_id` condivisi (normalizzati senza distinzione tra maiuscole e minuscole). L'hash `normalized_record_sha256` è calcolato sulla serializzazione JSON del record con chiavi ordinate; l'hash dell'archivio originale è separato nel manifest.
