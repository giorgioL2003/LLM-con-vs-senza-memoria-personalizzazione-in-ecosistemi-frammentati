# Dry run manuale — Q6

**Data:** 2026-08-29  
**Modello mostrato nell'interfaccia:** Claude Opus 5, impostazione Alto  
**Tipo di prova:** tre chat nuove e separate, una per condizione  
**Domanda:** Quali controlli concreti devono essere completati per la verifica richiesta nel rapporto preliminare?

## Procedura

- In C0 è stata fornita soltanto la domanda.
- In C1 sono stati forniti sessione 4 e domanda.
- In C2 sono stati forniti sessioni 1–4 e domanda.
- È stata usata la stessa istruzione: rispondere soltanto in base al contesto e astenersi se le informazioni non erano sufficienti.
- Il contesto è stato inserito manualmente; non è stato utilizzato alcun sistema di retrieval.

## Risultati osservati

| Condizione | Raggiungibile secondo l'oracle | Risposta osservata | Classificazione | Corrisponde all'atteso |
|---|---:|---|---|---|
| C0 — Nessuna memoria | 0 | «Non dispongo di informazioni sufficienti per rispondere.» | Astensione corretta | Sì |
| C1 — Memoria locale | 0 | «Non dispongo di informazioni sufficienti per rispondere.» | Astensione corretta | Sì |
| C2 — Memoria condivisa | 1 | «Per il rapporto preliminare occorre completare l'esame della cronologia del repository e della configurazione della pipeline CI, al fine di individuare dove sia stato esposto il vecchio token reporting-v1.» | Risposta completa | Sì |

## Confronto con l'oracle

La risposta C2 contiene entrambi i fatti obbligatori:

- cronologia del repository;
- configurazione della pipeline CI.

Non introduce informazioni obsolete e non sostituisce i controlli richiesti con l'analisi dei log di download. C0 e C1 seguono il comportamento previsto quando le evidenze obbligatorie non sono accessibili.

## Interpretazione limitata

Il dry run supporta tre osservazioni preliminari:

- Q6 non sembra ambigua nel contesto completo;
- la sola sessione 4 non consente di ricostruire i controlli concreti;
- il collegamento tra sessione 3 e sessione 4 è sufficiente per produrre la risposta attesa.

Questa prova non misura il retrieval, perché i contesti sono stati forniti manualmente. Non costituisce un risultato finale e non permette conclusioni generali: riguarda una sola domanda, un solo modello e una sola esecuzione per condizione.

## Evidenza fornita

L'utente ha fornito tre screenshot delle risposte, acquisiti alle 17:24:23, 17:24:50 e 17:25:14. Le trascrizioni riportate sopra corrispondono al contenuto visibile negli screenshot.
