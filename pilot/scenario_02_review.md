# Scenario 02 — Revisione metodologica iniziale

**Stato:** dry run completato; scenario validato; non congelato  
**Riferimento roadmap:** fasi 3 e 4

## Scopo

Controllare che lo Scenario 02 aggiunga casi di memoria locale senza eliminare la necessità della memoria condivisa.

## Controlli superati

- Gli obiettivi specifici compaiono soltanto nella Sessione 1.
- La decisione del CAPTCHA e la nuova regola non sono entrambe valide.
- Il valore di 15 minuti non viene ripetuto nella Sessione 4.
- Q3, Q4 e Q5 sono realmente risolvibili dalla Sessione 4.
- Q6 richiede di collegare la regola della Sessione 2 al test pendente della Sessione 4.
- La persona che approverà il rilascio non viene indicata.
- Le risposte dell'assistente non introducono fatti nuovi.
- Le domande non modificano lo stato delle prove successive.

## Correzioni prima del dry run

- La Sessione 2 non ripete più il nome del CAPTCHA: per identificare la decisione superata in Q2 serve anche la Sessione 1.
- La Sessione 4 non dichiara più esplicitamente l'assenza del responsabile dell'approvazione: Q7 verifica ora un'informazione realmente mai fornita.
- Q6 chiede esplicitamente il limite temporale da controllare, evitando di confonderlo con il momento in cui eseguire il test.

## Confronto con lo Scenario 01

| Scenario | C1 raggiungibile | C2 raggiungibile |
|---|---:|---:|
| Scenario 01 | 2/7 | 6/7 |
| Scenario 02 | 3/7 | 6/7 |

Lo Scenario 02 migliora la presenza della memoria locale, ma mantiene tre domande che richiedono informazioni precedenti e una domanda con informazione assente.

## Esito iniziale

Scenario, domande e oracle risultano coerenti dopo le correzioni preliminari.

## Esito del dry run

Il dry run completo è stato eseguito su Claude Opus 5, impostazione Alto, in 21 chat nuove e indipendenti. I risultati integrali sono registrati in `dry_run_scenario_02_results.md`.

- C0: 7 comportamenti appropriati su 7.
- C1: 6 comportamenti appropriati su 7.
- C2: 6 comportamenti appropriati su 7.
- Totale: 19 comportamenti appropriati su 21.

Q3 è stata sbagliata sia in C1 sia in C2: il modello ha indicato il test ancora aperto invece di quello completato. Poiché domanda ed evidenza sono esplicite, il problema è classificato come errore di risposta del modello e non come difetto del benchmark.

Lo Scenario 02 è validato come scenario del pilot, ma rimane non congelato fino alla chiusura del disegno sperimentale complessivo.
