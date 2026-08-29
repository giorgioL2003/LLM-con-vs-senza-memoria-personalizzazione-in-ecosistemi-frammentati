# Scenario 02 — Conversazioni sintetiche

**Stato:** bozza v0.1, non congelata  
**Scenario:** recupero password di Lumen Market  
**Numero di sessioni:** 4

## Regole di lettura

- Ogni sessione rappresenta una conversazione distinta.
- I messaggi dell'utente sono la fonte autorevole dei fatti.
- Le risposte dell'assistente non introducono nuovi fatti.
- Le domande vengono eseguite separatamente dopo la Sessione 4.
- Per ogni domanda si riparte dallo stesso stato iniziale.

## Sessione 1 — Apertura e decisione iniziale

**S1-U1 — Utente**

> Sto seguendo un problema nel recupero password di Lumen Market. Tre account hanno subito un cambio di password non autorizzato tramite il portale `account-portal`. Abbiamo due obiettivi: impedire altri cambi non autorizzati e mantenere utilizzabile il recupero password nell'app mobile. La decisione iniziale è inserire un CAPTCHA dopo la prima richiesta di recupero effettuata dallo stesso account. Prima di applicarla dobbiamo controllare il registro `reset_audit`.

**S1-A1 — Assistente**

> Registrato. Tratterò il CAPTCHA come decisione iniziale da verificare in base alle evidenze.

## Sessione 2 — Evidenza e cambio di decisione

**S2-U1 — Utente**

> Il controllo di `reset_audit` è terminato. Per ciascuno dei tre account risulta una sola richiesta di recupero, ma lo stesso link è stato utilizzato due volte. La decisione iniziale non impedirebbe quindi il problema osservato e non è più l'intervento scelto. La decisione aggiornata è usare token validi una sola volta e con scadenza dopo 15 minuti.

**S2-A1 — Assistente**

> Decisione aggiornata: il controllo deve impedire il riutilizzo del token e limitarne la durata.

## Sessione 3 — Implementazione e verifiche

**S3-U1 — Utente**

> L'uso singolo del token è stato implementato nel componente `ResetTokenService`: dopo il primo cambio di password riuscito, il token viene segnato come consumato. I test di integrazione del portale web sono stati superati. Rimangono da eseguire due verifiche: controllare che il collegamento aperto dall'app mobile riporti correttamente alla schermata di accesso e provare un'email di recupero consegnata dopo il limite di validità stabilito nella sessione precedente.

**S3-A1 — Assistente**

> Terrò separati il lavoro già completato e le due verifiche ancora da eseguire.

## Sessione 4 — Stato locale e riunione

**S4-U1 — Utente**

> Il test del collegamento nell'app mobile è stato completato: dopo il cambio di password l'utente viene riportato correttamente alla schermata di accesso. Rimane da completare soltanto il test dell'email consegnata in ritardo. La riunione di verifica del rilascio è fissata per martedì alle 11:30 e deve includere il risultato di questo test ancora pendente.

**S4-A1 — Assistente**

> Stato aggiornato. Considererò completato il test mobile e ancora aperto il test dell'email ritardata.
