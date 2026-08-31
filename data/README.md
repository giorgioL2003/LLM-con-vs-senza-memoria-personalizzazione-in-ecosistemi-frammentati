# Dati strutturati del pilot

Questa cartella contiene la versione **JSON** dei due scenari del pilot. È una
conversione dei documenti Markdown in `pilot/`, non un nuovo materiale
sperimentale: testo delle sessioni, domande, risposte attese, evidenze e matrici
di raggiungibilità sono riportati così come sono scritti nei Markdown.

I file Markdown restano la fonte da leggere per capire il pilot. I file JSON
servono al codice.

```
data/
  README.md
  scenarios/
    scenario_01.json    incidente Asteria Docs
    scenario_02.json    recupero password di Lumen Market
```

## 1. Cosa contiene un file di scenario

Ogni file descrive uno scenario completo:

| Campo | Contenuto |
|---|---|
| `scenario_id` | identificatore dello scenario (`scenario_01`, `scenario_02`) |
| `title` | nome dello scenario |
| `version` | versione della conversione; `frozen: false` perché il pilot non è congelato |
| `source_files` | documenti Markdown da cui il contenuto è stato ricavato |
| `abstention_rule` | regola di astensione dichiarata nell'oracle |
| `conditions` | perimetro di memoria di C0, C1 e C2 (quali sessioni sono accessibili) |
| `expected_reachability_totals` | domande raggiungibili attese per condizione |
| `sessions` | le quattro sessioni, ciascuna con i propri messaggi |
| `questions` | le sette domande con il relativo oracle |

Una sessione contiene `session_id`, `order`, `title` e `messages`.
Un messaggio contiene `message_id`, `order`, `role` (`user` o `assistant`),
`content` e il `session_id` della sessione a cui appartiene.

Una domanda contiene `question_id`, `category`, `text`, `expected_answer`,
`mandatory_facts`, `required_evidence_ids`, `obsolete_information`,
`accepted_equivalents`, `reachability` per C0/C1/C2,
`expected_behavior_when_unreachable`, `expected_behavior_by_condition` e
`fact_present_in_corpus`.

Le categorie ammesse sono: `goal`, `update_obsolete`, `completed_activity`,
`pending_activity`, `local_information`, `cross_session_link`,
`absent_information`.

Gli identificatori mantengono il riferimento ai Markdown tramite `source_label`:
per esempio il messaggio `SC01-S2-U1` corrisponde a `S2-U1` dello Scenario 01.
Il prefisso serve a rendere gli identificatori unici anche mettendo insieme i
due scenari.

## 2. Perché ogni messaggio ha un identificatore

L'architettura prevista è **Turn-level RAG**: l'unità recuperabile non è la
sessione né il documento, ma il singolo messaggio. Un identificatore stabile per
messaggio serve a tre cose:

1. l'oracle può dire esattamente quali messaggi sono l'evidenza obbligatoria di
   una domanda (`required_evidence_ids`);
2. il retriever viene valutato confrontando i messaggi recuperati con quelli
   obbligatori;
3. un errore può essere attribuito alla causa giusta: evidenza fuori dal
   perimetro, evidenza non recuperata, oppure risposta sbagliata pur avendo
   l'evidenza.

I punti 2 e 3 sono stati effettivamente usati nel pilot: si vedano
`results/retrieval_pilot.jsonl` e `results/error_analysis_pilot.jsonl`.

## 3. Come funzionano C0, C1 e C2

Le tre condizioni cambiano soltanto il **perimetro della memoria accessibile**:

| Condizione | Messaggi accessibili |
|---|---|
| C0 — nessuna memoria | nessuno: solo la domanda |
| C1 — memoria locale | soltanto i messaggi della Sessione 4 |
| C2 — memoria condivisa | i messaggi delle Sessioni 1, 2, 3 e 4 |

C1 e C2 useranno lo stesso retriever con gli stessi parametri. L'unica cosa che
cambia è l'insieme dei messaggi in cui è possibile cercare. In C0 il corpus è
vuoto.

Nei file JSON questo è scritto in `conditions[...].accessible_sessions`.

## 4. Raggiungibilità e retrieval non sono la stessa cosa

- **Raggiungibilità** (`reachability`): proprietà del benchmark. Vale `true` per
  una condizione quando *tutte* le evidenze obbligatorie della domanda si trovano
  dentro il perimetro di quella condizione. Si decide leggendo scenario e oracle,
  prima di eseguire qualsiasi cosa. È il massimo teorico della condizione.
- **Retrieval**: comportamento del sistema. Indica se il recuperatore, dato quel
  perimetro, mette davvero le evidenze obbligatorie nel contesto passato al
  modello. Si misura solo quando la domanda è raggiungibile. È stato misurato nel
  pilot: i risultati per domanda sono in `results/retrieval_pilot.jsonl` e le
  proporzioni aggregate in `pilot/metrics_pilot.md`.

Un'informazione raggiungibile può non essere recuperata; un'informazione
recuperata può comunque essere letta male dal modello. Per questo i due concetti
restano separati.

Caso particolare: le domande di categoria `absent_information` riguardano un
fatto **mai fornito** in nessuna sessione. Hanno `fact_present_in_corpus: false`,
`required_evidence_ids` vuoto e `reachability` falsa in tutte e tre le
condizioni, C2 compresa. Il comportamento corretto è sempre l'astensione:
l'assenza non viene rappresentata come un'evidenza raggiungibile.

Copertura attesa, uguale a quella registrata in `pilot/pilot_summary.md`:

| Condizione | Scenario 01 | Scenario 02 | Totale |
|---|---:|---:|---:|
| C0 | 0/7 | 0/7 | 0/14 |
| C1 | 2/7 | 3/7 | 5/14 |
| C2 | 6/7 | 6/7 | 12/14 |

## 5. Come eseguire validatore e test

Serve solo Python 3 con la libreria standard: nessuna dipendenza da installare.

Validatore (tutti gli scenari):

```bash
python3 scripts/validate_scenarios.py
```

Validatore su un singolo file:

```bash
python3 scripts/validate_scenarios.py data/scenarios/scenario_01.json
```

Controllo delle metriche aggregate, senza riscrivere i file:

```bash
python3 scripts/summarize_evaluation.py --check
```

Controllo dell'analisi causale dei due fallimenti, senza riscrivere i file:

```bash
python3 scripts/build_error_analysis.py --check
```

Test:

```bash
python3 -m unittest discover -s tests -v
```

Una dimostrazione completa e commentata di questi comandi è in `COMANDI_DEMO.md`,
nella radice del progetto.

Il validatore controlla campi obbligatori, unicità degli identificatori, ordine
di sessioni e messaggi, numero di sessioni e domande, esistenza delle evidenze e
loro appartenenza alle sessioni, coerenza dei perimetri di C0/C1/C2 con la
raggiungibilità dichiarata, rappresentazione delle informazioni mai fornite,
categorie ammesse e copertura complessiva attesa. Esce con codice `0` se non
trova errori, `1` altrimenti; ogni errore ha un codice come `[E-REACH]` o
`[E-EVIDENCE-MISSING]`.

I test verificano sia i due scenari reali sia una serie di corruzioni
intenzionali (identificatori duplicati, evidenze inesistenti, raggiungibilità
incoerente, perimetri alterati, informazione assente trattata come evidenza),
che devono essere segnalate.

## 6. Cosa è stato eseguito a partire da questi JSON

Il runner Turn-level RAG **esiste** e il pilot è stato eseguito per intero:

| Passaggio | Script | Risultato |
|---|---|---|
| Retrieval automatico su C0, C1, C2 | `scripts/run_retrieval_pilot.py` | `results/retrieval_pilot.jsonl` (42 righe) |
| Costruzione dei prompt | `scripts/build_generation_inputs.py` | `results/generation_inputs.jsonl` (56 righe) |
| Generazione delle risposte | `scripts/run_generation.py` | `results/generation_pilot.jsonl` (56 righe) |
| Valutazione manuale assistita | — | `results/evaluation_pilot.jsonl` (56 righe) |
| Metriche aggregate | `scripts/summarize_evaluation.py` | `results/metrics_pilot.json`, `pilot/metrics_pilot.md` |
| Analisi causale dei fallimenti | `scripts/build_error_analysis.py` | `results/error_analysis_pilot.jsonl`, `pilot/error_analysis_pilot.md` |

Le 56 righe sono 14 domande × 4 modalità: le tre condizioni sperimentali C0, C1,
C2 più `FULL_HISTORY`, che è un controllo diagnostico e non una quarta
condizione. Il retrieval riguarda soltanto C0, C1 e C2, da cui le 42 righe.

## 7. Cosa non c'è ancora

- Non sono stati convertiti in JSON i risultati dei dry run manuali: quelli sono
  stati ottenuti con contesti forniti a mano e servivano a validare il benchmark,
  non a misurare il retrieval.
- Il pilot non è congelato: se un documento del pilot cambia, questi JSON vanno
  rigenerati e rivalidati, e i risultati già prodotti vanno ricalcolati.
- L'esperimento finale non è stato eseguito: quanto c'è qui è un pilot, non un
  risultato definitivo.
