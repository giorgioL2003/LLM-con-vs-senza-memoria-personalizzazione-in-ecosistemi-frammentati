# Dry run completo — Scenario 01

**Data:** 2026-08-29  
**Modello mostrato nell'interfaccia:** Claude Opus 5  
**Impostazione:** Alto  
**Interfaccia:** app Claude  
**Prove considerate:** 21 chat nuove e indipendenti

## Procedura

Le sette domande sono state eseguite separatamente nelle tre condizioni:

- C0: nessun contesto;
- C1: soltanto la Sessione 4;
- C2: tutte le Sessioni 1–4.

In ogni prova è stata usata la stessa istruzione: rispondere soltanto in base al contesto, non fare supposizioni e dichiarare l'insufficienza delle informazioni quando necessario.

Durante la raccolta alcune celle sono state ripetute perché l'interfaccia restituiva come testo accessibile il tempo di ragionamento invece della risposta. Le prime acquisizioni incomplete non sono state usate. Questo è stato un problema tecnico di raccolta, non un risultato del modello.

## Risposte e classificazione proposta

### C0 — Nessuna memoria

| ID | Risposta osservata | Classificazione |
|---|---|---|
| C0-Q1 | Non dispongo di informazioni sufficienti per rispondere. | Astensione corretta |
| C0-Q2 | Non dispongo di informazioni sufficienti per rispondere. | Astensione corretta |
| C0-Q3 | Non dispongo di informazioni sufficienti per rispondere. | Astensione corretta |
| C0-Q4 | Non dispongo di informazioni sufficienti per rispondere. | Astensione corretta |
| C0-Q5 | Non dispongo di informazioni sufficienti per rispondere. | Astensione corretta |
| C0-Q6 | Non dispongo di informazioni sufficienti per rispondere. | Astensione corretta |
| C0-Q7 | Non dispongo di informazioni sufficienti per rispondere. | Astensione corretta |

### C1 — Memoria locale

| ID | Risposta osservata | Classificazione proposta |
|---|---|---|
| C1-Q1 | Gli obiettivi sono verificare l'origine dell'esposizione del token, il cui esito deve essere incluso nel rapporto preliminare di venerdì alle 17:00, e verificare l'eventuale consultazione di documenti, che può essere completata per il rapporto finale. | Errata: scambia le verifiche pendenti per gli obiettivi iniziali |
| C1-Q2 | Non dispongo di informazioni sufficienti per rispondere. | Astensione corretta |
| C1-Q3 | Non dispongo di informazioni sufficienti per rispondere. | Astensione corretta |
| C1-Q4 | Sono ancora in sospeso la verifica sull'origine dell'esposizione del token e la verifica sull'eventuale consultazione di documenti. | Risposta completa dopo la correzione dell'oracle |
| C1-Q5 | Il rapporto preliminare deve essere consegnato venerdì alle 17:00, mentre la verifica sull'eventuale consultazione di documenti può essere rinviata al rapporto finale. | Risposta completa |
| C1-Q6 | Non dispongo di informazioni sufficienti per rispondere. | Astensione corretta |
| C1-Q7 | Non dispongo di informazioni sufficienti per rispondere. | Astensione corretta |

### C2 — Memoria condivisa

| ID | Risposta osservata | Classificazione |
|---|---|---|
| C2-Q1 | Gli obiettivi fissati sono capire come sia stato usato l'account di servizio `svc-reporting` e mettere in sicurezza la generazione automatica dei report mensili senza interromperne la consultazione da parte degli utenti. | Risposta completa |
| C2-Q2 | L'ipotesi attualmente valida è che sia stato esposto il vecchio token API `reporting-v1`, mentre è stata superata l'ipotesi iniziale della compromissione della password dell'account `svc-reporting`. | Risposta completa |
| C2-Q3 | È stato revocato il token `reporting-v1`, sostituito da `reporting-v2`, autorizzato soltanto alla lettura della cartella `monthly-reports`. | Risposta completa |
| C2-Q4 | Restano in sospeso l'esame della cronologia del repository e della configurazione della pipeline CI per individuare dove sia stato esposto il vecchio token, e il controllo dei log di download per stabilire se siano stati consultati documenti. | Risposta completa |
| C2-Q5 | Il rapporto preliminare deve essere consegnato venerdì alle 17:00 e può essere rinviata al rapporto finale la verifica dei log di download sull'eventuale consultazione di documenti. | Risposta completa |
| C2-Q6 | Per la verifica sull'origine dell'esposizione del vecchio token occorre esaminare la cronologia del repository e la configurazione della pipeline CI. | Risposta completa |
| C2-Q7 | Non dispongo di informazioni sufficienti per rispondere. | Astensione corretta |

## Riepilogo

- C0: 7 comportamenti su 7 corrispondono all'oracle.
- C1: dopo la correzione di Q4, 6 comportamenti su 7 sono appropriati; Q1 è un errore del modello.
- C2: 7 comportamenti su 7 corrispondono all'oracle.
- Totale dopo la correzione: 20 celle su 21 hanno il comportamento appropriato; una contiene un errore del modello.

## Problema individuato e corretto in Q4

L'oracle originale considera Q4 non raggiungibile in C1 e richiede l'astensione. Tuttavia, la Sessione 4 nomina entrambe le verifiche ancora in sospeso:

- origine dell'esposizione del token;
- eventuale consultazione di documenti.

La risposta di C1-Q4 è quindi sostenuta dal contesto locale. La domanda chiede quali siano le due verifiche, ma l'oracle richiede anche i controlli concreti presenti nella Sessione 3. Domanda e fatti obbligatori non sono perfettamente allineati.

### Correzione applicata

La domanda Q4 è rimasta invariata e l'oracle è stato corretto in questo modo:

- fatti obbligatori: verifica sull'origine dell'esposizione; verifica sull'eventuale consultazione di documenti;
- evidenza obbligatoria: `S4-U1` per C1 e C2;
- raggiungibilità: C0 = 0, C1 = 1, C2 = 1;
- risposta C1 osservata: completa.

La correzione rende l'oracle coerente con ciò che la domanda chiede realmente. Dopo la correzione, 20 risposte su 21 risultano appropriate; l'unico errore del modello rimane C1-Q1.

## Interpretazione limitata

Il dry run mostra che il benchmark è quasi pronto, ma ha svolto correttamente la sua funzione facendo emergere il problema di Q4. Non è stato usato alcun retrieval: i contesti sono stati forniti manualmente. I risultati non sono quindi risultati finali del sistema e non permettono conclusioni generali sul modello.
