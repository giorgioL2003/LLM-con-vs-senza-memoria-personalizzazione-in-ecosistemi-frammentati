# Valutazione delle risposte del pilot

**Data:** 2026-08-31  
**Stato:** prima classificazione assistita dall'AI, da approvare prima delle metriche aggregate  
**Ambito:** step 1 - valutazione delle 56 risposte; non include ancora l'analisi causale degli errori

## Scopo

Questo documento accompagna `results/evaluation_pilot.jsonl`, che contiene una
riga per ogni combinazione tra scenario, domanda e modalità. Le risposte sono
state confrontate con l'oracle manuale, i fatti obbligatori, le informazioni
obsolete vietate e il comportamento atteso quando l'evidenza non è accessibile.

`FULL_HISTORY` è mantenuto come controllo diagnostico e non viene trattato
come una quarta condizione sperimentale.

## Regole di classificazione

- `complete`: contiene tutti i fatti obbligatori e non presenta contraddizioni;
- `partial`: contiene almeno un elemento corretto, ma omette una parte necessaria;
- `incorrect`: non risponde correttamente, contraddice l'oracle o sostituisce
  l'astensione con una risposta non supportata;
- `correct_abstention`: dichiara correttamente che le informazioni non sono
  sufficienti quando l'evidenza non è accessibile o il fatto è assente.

I campi `obsolete_used` e `unsupported_claim` rimangono separati dalla classe
principale. `format_compliant` permette di non confondere correttezza semantica
e rispetto della forma richiesta.

## Casi con priorità alta per la revisione umana

### SC02-Q6 / C1

L'evidenza necessaria non è accessibile. La risposta avrebbe dovuto astenersi,
ma interpreta il test come una verifica della consegna dell'email e del tempo
impiegato per arrivare. Non indica né il rifiuto del link scaduto né il limite
di 15 minuti. La proposta di classificazione è `incorrect`, con
`unsupported_claim: true`.

### SC02-Q6 / C2

Nel perimetro C2 l'evidenza completa è teoricamente raggiungibile, ma il
retrieval non ha recuperato la Sessione 2 con la regola dei 15 minuti. La
risposta collega correttamente il test all'email arrivata oltre il limite, ma
non specifica che il link deve essere rifiutato e omette il limite numerico.
La proposta di classificazione è `partial`.

## Controlli da approvare

Prima dello step 2 lo studente deve confermare:

1. che i due casi sopra siano classificati come `incorrect` e `partial`;
2. che nessuna risposta adotti come valida un'informazione obsoleta;
3. che soltanto SC02-Q6/C1 contenga un'affermazione non supportata;
4. che la distinzione tra risposta completa e astensione corretta sia coerente
   con l'oracle.

Le metriche aggregate verranno calcolate soltanto dopo questa approvazione.

