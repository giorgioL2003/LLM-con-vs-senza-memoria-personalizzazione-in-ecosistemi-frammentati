# Dry run completo — Scenario 02

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

È stata usata la stessa istruzione del dry run dello Scenario 01: rispondere soltanto in base al contesto, non fare supposizioni, astenersi quando le informazioni non sono sufficienti e usare una sola frase negli altri casi.

## Risposte e classificazione

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

| ID | Risposta osservata | Classificazione |
|---|---|---|
| C1-Q1 | Non dispongo di informazioni sufficienti per rispondere. | Astensione corretta |
| C1-Q2 | Non dispongo di informazioni sufficienti per rispondere. | Astensione corretta |
| C1-Q3 | Prossimo punto aperto: il test dell'email consegnata in ritardo. | Errata: indica l'attività pendente invece della verifica completata |
| C1-Q4 | Rimane da completare il test dell'email consegnata in ritardo. | Risposta completa |
| C1-Q5 | La riunione di verifica del rilascio si terrà martedì alle 11:30 e dovrà includere il risultato del test dell'email consegnata in ritardo, ancora pendente. | Risposta completa |
| C1-Q6 | Non dispongo di informazioni sufficienti per rispondere. | Astensione corretta |
| C1-Q7 | Non dispongo di informazioni sufficienti per rispondere. | Astensione corretta |

### C2 — Memoria condivisa

| ID | Risposta osservata | Classificazione |
|---|---|---|
| C2-Q1 | Gli obiettivi fissati sono impedire altri cambi di password non autorizzati e mantenere utilizzabile il recupero password nell'app mobile. | Risposta completa |
| C2-Q2 | La decisione attualmente valida è usare token di recupero validi una sola volta e con scadenza dopo 15 minuti, mentre la decisione iniziale superata era l'inserimento di un CAPTCHA dopo la prima richiesta di recupero effettuata dallo stesso account. Prossimo punto utile: resta aperto il test dell'email consegnata dopo il limite di validità. | Risposta completa; formato di una frase non rispettato |
| C2-Q3 | Prossimo punto: resta aperto il test dell'email di recupero consegnata in ritardo. | Errata: indica l'attività pendente invece della verifica completata |
| C2-Q4 | Rimane da completare il test dell'email di recupero consegnata dopo il limite di validità di 15 minuti. | Risposta completa |
| C2-Q5 | La riunione di verifica del rilascio si terrà martedì alle 11:30 e dovrà includere il risultato del test ancora pendente sull'email di recupero consegnata dopo il limite di validità di 15 minuti. | Risposta completa |
| C2-Q6 | Il test pendente deve confermare che un'email di recupero consegnata in ritardo non consenta più il cambio di password, verificando il limite di validità di 15 minuti stabilito per il token. | Risposta completa |
| C2-Q7 | Non dispongo di informazioni sufficienti per rispondere. | Astensione corretta |

## Riepilogo per condizione

| Condizione | Comportamenti appropriati | Errori del modello | Difetti del benchmark |
|---|---:|---:|---:|
| C0 | 7/7 | 0 | 0 |
| C1 | 6/7 | 1 | 0 |
| C2 | 6/7 | 1 | 0 |
| Totale | 19/21 | 2 | 0 |

## Lettura diagnostica

- C0 si astiene correttamente in tutte le domande.
- C1 risponde correttamente a Q4 e Q5 e fallisce Q3, pur avendo il contesto necessario.
- C2 risponde correttamente a cinque delle sei domande raggiungibili e fallisce nuovamente Q3.
- Q3 produce lo stesso errore in C1 e C2: il modello indica l'attività ancora aperta invece di quella completata.
- C2-Q2 contiene tutti i fatti obbligatori, ma aggiunge una seconda frase non richiesta. La risposta resta completa sul contenuto; la violazione di formato viene registrata separatamente.

## Perché Q3 non viene corretta

La Sessione 4 dichiara esplicitamente che il test del collegamento mobile è stato completato e descrive il risultato. La domanda chiede esplicitamente la verifica completata e il suo esito. Non sono emerse due risposte plausibili né una mancanza di evidenza.

Il fallimento viene quindi classificato come errore di lettura o risposta del modello, non come difetto della domanda o dell'oracle. Modificare Q3 sulla base di questo errore renderebbe il benchmark più facile senza correggere un problema metodologico reale.

## Indicatori descrittivi del dry run

Questi valori descrivono soltanto la validazione manuale del benchmark; non sono risultati finali del sistema e non includono retrieval.

| Condizione | Domande raggiungibili | Risposte complete sulle raggiungibili | Astensioni corrette sulle non raggiungibili |
|---|---:|---:|---:|
| C0 | 0/7 | Non applicabile | 7/7 |
| C1 | 3/7 | 2/3 | 4/4 |
| C2 | 6/7 | 5/6 | 1/1 |

## Esito

Il dry run non ha individuato difetti ulteriori nel benchmark dopo le correzioni preliminari. Lo Scenario 02 può essere considerato validato come scenario del pilot, ma rimane non congelato fino alla chiusura del disegno sperimentale complessivo.

