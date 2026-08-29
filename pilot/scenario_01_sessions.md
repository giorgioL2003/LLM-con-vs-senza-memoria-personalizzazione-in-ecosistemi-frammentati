# Scenario 01 — Conversazioni sintetiche

**Stato:** bozza v0.1, non congelata  
**Scenario:** incidente Asteria Docs  
**Numero di sessioni:** 4

## Regole di lettura

- Ogni sessione rappresenta una conversazione distinta.
- I messaggi dell'utente sono la fonte autorevole dei fatti dello scenario.
- Le risposte dell'assistente mantengono la forma conversazionale ma non introducono nuovi fatti.
- Le domande di valutazione vengono aggiunte, una alla volta, dopo la sessione 4.
- Per ogni domanda si riparte da una copia indipendente dello stesso stato.

## Sessione 1 — Apertura dell'indagine

**S1-U1 — Utente**

> Sto coordinando la risposta a un incidente per Asteria Docs, una piattaforma di condivisione documenti. Alle 09:10 è stato rilevato un accesso anomalo tramite l'account di servizio `svc-reporting`. Abbiamo fissato due obiettivi: capire come sia stato usato questo account e mettere in sicurezza la generazione automatica dei report mensili senza interromperne la consultazione da parte degli utenti. La nostra prima ipotesi è che sia stata compromessa la password dell'account. Prima di decidere come intervenire dobbiamo confrontare i log di accesso dell'applicazione con quelli di autenticazione.

**S1-A1 — Assistente**

> Procediamo mantenendo separati ipotesi, evidenze, azioni completate e attività ancora aperte.

## Sessione 2 — Nuove evidenze

**S2-U1 — Utente**

> Il confronto dei log è terminato. Nella finestra temporale dell'incidente non risultano autenticazioni riuscite tramite password. Il record dell'accesso anomalo riporta invece `auth_method=api_token` e identifica il vecchio token `reporting-v1`. Queste evidenze superano la spiegazione formulata nella sessione precedente: l'ipotesi aggiornata è che sia stato esposto il vecchio token API. Abbiamo deciso di revocarlo e sostituirlo con `reporting-v2`, autorizzato soltanto a leggere la cartella `monthly-reports`.

**S2-A1 — Assistente**

> Stato dell'indagine aggiornato. Nella prossima sessione potremo verificare l'esito del contenimento.

## Sessione 3 — Contenimento

**S3-U1 — Utente**

> Il token `reporting-v1` è stato revocato alle 11:40 e `reporting-v2`, limitato alla lettura di `monthly-reports`, è attivo. Dopo la revoca non sono stati osservati altri accessi anomali. Consideriamo quindi completata l'azione di contenimento. Rimangono aperte due verifiche. Per individuare dove sia stato esposto il vecchio token dobbiamo esaminare la cronologia del repository e la configurazione della pipeline CI. Separatamente, dobbiamo controllare i log di download per stabilire se durante l'accesso anomalo siano stati consultati documenti.

**S3-A1 — Assistente**

> Registrato. Terrò distinta l'azione completata dalle verifiche ancora in sospeso.

## Sessione 4 — Vincolo locale

**S4-U1 — Utente**

> Il rapporto preliminare sull'incidente deve essere consegnato venerdì alle 17:00. Deve includere il risultato della verifica sull'origine dell'esposizione del token. La verifica sull'eventuale consultazione di documenti può invece essere completata per il rapporto finale. Al momento non abbiamo ancora l'esito di nessuna delle due verifiche.

**S4-A1 — Assistente**

> Ricevuto. Considererò la scadenza come vincolo corrente dell'attività.
