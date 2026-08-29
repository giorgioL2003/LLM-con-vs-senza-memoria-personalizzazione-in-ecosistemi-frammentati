# Scenario 02 — Domande e oracle manuale

**Stato:** bozza v0.1, non congelata  
**Scenario di riferimento:** `scenario_02_sessions.md`

## 1. Interpretazione delle condizioni

- **C0 — Nessuna memoria:** vede soltanto la domanda.
- **C1 — Memoria locale:** vede la Sessione 4 e la domanda.
- **C2 — Memoria condivisa:** vede le Sessioni 1–4 e la domanda.

Quando almeno un fatto obbligatorio non è accessibile, il comportamento corretto è dichiarare che le informazioni non sono sufficienti.

## 2. Quesiti e risposte attese

### Q1 — Obiettivi

**Domanda**

> Quali due obiettivi sono stati fissati per l'intervento sul recupero password?

**Risposta attesa**

> Impedire altri cambi di password non autorizzati e mantenere utilizzabile il recupero password nell'app mobile.

**Fatti obbligatori:** impedire altri cambi non autorizzati; mantenere utilizzabile il recupero password nell'app mobile.  
**Evidenza obbligatoria:** `S1-U1`.  
**Informazioni obsolete vietate:** nessuna.  
**Equivalenze ammesse:** formulazioni equivalenti che conservino entrambi gli obiettivi.

### Q2 — Decisione aggiornata e decisione superata

**Domanda**

> Qual è la decisione attualmente valida sui token di recupero e quale decisione iniziale è stata superata?

**Risposta attesa**

> I token devono essere utilizzabili una sola volta e scadere dopo 15 minuti; è stata superata la decisione di inserire un CAPTCHA dopo la prima richiesta.

**Fatti obbligatori:** uso singolo; scadenza dopo 15 minuti; CAPTCHA come decisione superata.  
**Evidenze obbligatorie:** `S1-U1`, `S2-U1`.  
**Informazioni obsolete vietate:** presentare il CAPTCHA come intervento ancora scelto.  
**Equivalenze ammesse:** “monouso” come equivalente di “utilizzabile una sola volta”.

### Q3 — Verifica completata

**Domanda**

> Quale verifica è stata completata nell'ultima sessione e con quale esito?

**Risposta attesa**

> È stato completato il test del collegamento nell'app mobile e, dopo il cambio di password, l'utente viene riportato correttamente alla schermata di accesso.

**Fatti obbligatori:** test del collegamento mobile completato; ritorno corretto alla schermata di accesso.  
**Evidenza obbligatoria:** `S4-U1`.  
**Informazioni obsolete vietate:** descrivere il test mobile come ancora da eseguire.  
**Equivalenze ammesse:** “login” come equivalente di “schermata di accesso”.

### Q4 — Verifica pendente

**Domanda**

> Quale verifica rimane ancora da completare?

**Risposta attesa**

> Rimane da completare il test dell'email di recupero consegnata in ritardo.

**Fatti obbligatori:** test dell'email consegnata in ritardo.  
**Evidenza obbligatoria:** `S4-U1`.  
**Informazioni obsolete vietate:** includere il test mobile tra le attività ancora aperte.  
**Equivalenze ammesse:** “email consegnata dopo il limite” come formulazione equivalente.

### Q5 — Informazione locale

**Domanda**

> Quando si terrà la riunione di verifica e quale risultato dovrà includere?

**Risposta attesa**

> La riunione si terrà martedì alle 11:30 e dovrà includere il risultato del test dell'email consegnata in ritardo.

**Fatti obbligatori:** martedì; ore 11:30; risultato del test dell'email ritardata.  
**Evidenza obbligatoria:** `S4-U1`.  
**Informazioni obsolete vietate:** nessuna.  
**Equivalenze ammesse:** notazioni orarie equivalenti.

### Q6 — Collegamento tra sessioni

**Domanda**

> Quale comportamento deve confermare il test ancora pendente e quale limite temporale deve controllare?

**Risposta attesa**

> Deve confermare che un link di recupero consegnato in ritardo non sia più utilizzabile dopo 15 minuti.

**Fatti obbligatori:** rifiuto del link oltre il limite; limite di 15 minuti; collegamento con il test ancora pendente.  
**Evidenze obbligatorie:** `S2-U1`, `S4-U1`.  
**Informazioni obsolete vietate:** indicare un limite temporale diverso o descrivere il test come già completato.  
**Equivalenze ammesse:** “token scaduto” o “link non valido” dopo 15 minuti.

### Q7 — Informazione assente

**Domanda**

> Chi approverà il rilascio in produzione?

**Risposta attesa**

> La persona responsabile dell'approvazione non è stata indicata.

**Fatti obbligatori:** riconoscimento dell'assenza dell'informazione.  
**Evidenza obbligatoria:** nessuna evidenza positiva; controllo dell'intero scenario.  
**Informazioni obsolete vietate:** attribuire l'approvazione a una persona o a un ruolo non menzionato.  
**Equivalenze ammesse:** qualsiasi astensione esplicita senza identità o ruolo inventati.

## 3. Matrice di raggiungibilità teorica

| Domanda | Fenomeno | C0 | C1 | C2 |
|---|---|---:|---:|---:|
| Q1 | Obiettivi | 0 | 0 | 1 |
| Q2 | Decisione aggiornata e superata | 0 | 0 | 1 |
| Q3 | Verifica completata | 0 | 1 | 1 |
| Q4 | Verifica pendente | 0 | 1 | 1 |
| Q5 | Informazione locale | 0 | 1 | 1 |
| Q6 | Collegamento tra sessioni | 0 | 0 | 1 |
| Q7 | Informazione assente | 0 | 0 | 0 |

### Massimo teorico di raggiungibilità

| Condizione | Domande raggiungibili | Reachability Rate |
|---|---:|---:|
| C0 | 0/7 | 0,000 |
| C1 | 3/7 | 0,429 |
| C2 | 6/7 | 0,857 |

Q7 non è raggiungibile perché l'informazione richiesta non è mai stata fornita. Il comportamento corretto è l'astensione in tutte le condizioni.

## 4. Comportamento atteso per condizione

| Domanda | C0 | C1 | C2 |
|---|---|---|---|
| Q1 | Astensione | Astensione | Risposta completa |
| Q2 | Astensione | Astensione | Risposta completa |
| Q3 | Astensione | Risposta completa | Risposta completa |
| Q4 | Astensione | Risposta completa | Risposta completa |
| Q5 | Astensione | Risposta completa | Risposta completa |
| Q6 | Astensione | Astensione | Risposta completa |
| Q7 | Astensione | Astensione | Astensione |

## 5. Controlli prima dell'esecuzione

- Q1 richiede gli obiettivi specifici della Sessione 1.
- Q2 richiede sia la decisione iniziale sia quella aggiornata.
- Q3, Q4 e Q5 sono risolvibili con la sola Sessione 4.
- Q6 richiede la regola dei 15 minuti della Sessione 2 e lo stato pendente della Sessione 4.
- Q7 non può essere risolta con conoscenze esterne.
- Le domande vengono eseguite separatamente e non modificano lo stato.
