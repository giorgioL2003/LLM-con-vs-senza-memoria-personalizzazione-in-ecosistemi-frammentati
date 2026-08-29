# Scenario 01 — Domande e oracle manuale

**Stato:** bozza v0.1, non congelata  
**Scenario di riferimento:** `scenario_01_sessions.md`

## 1. Interpretazione delle condizioni

- **C0 — Nessuna memoria:** vede soltanto la domanda.
- **C1 — Memoria locale:** vede la sessione 4 e la domanda.
- **C2 — Memoria condivisa:** vede le sessioni 1–4 e la domanda.

Una condizione è segnata come raggiungibile soltanto se contiene tutte le evidenze obbligatorie. Quando la condizione non è raggiungibile, il comportamento corretto è dichiarare che non si dispone di informazioni sufficienti, senza inventare una risposta.

## 2. Quesiti e risposte attese

### Q1 — Scopo

**Domanda**

> Quali due obiettivi operativi sono stati fissati per l'indagine?

**Risposta attesa**

> Capire come è stato usato `svc-reporting` e mettere in sicurezza la generazione automatica dei report mensili senza interromperne la consultazione da parte degli utenti.

**Fatti obbligatori:** capire come è stato usato `svc-reporting`; mettere in sicurezza la generazione automatica dei report mensili; non interrompere la consultazione.  
**Evidenza obbligatoria:** `S1-U1`.  
**Informazioni obsolete vietate:** nessuna.  
**Equivalenze ammesse:** formulazioni che conservino entrambi gli obiettivi e il vincolo di continuità della consultazione.

### Q2 — Aggiornamento e obsolescenza

**Domanda**

> Qual è l'ipotesi attualmente valida sulla modalità dell'accesso anomalo e quale ipotesi è stata superata?

**Risposta attesa**

> L'ipotesi corrente è l'esposizione del vecchio token API `reporting-v1`; l'ipotesi superata è la compromissione della password dell'account.

**Fatti obbligatori:** esposizione del vecchio token; password compromessa come ipotesi superata.  
**Evidenze obbligatorie:** `S1-U1`, `S2-U1`.  
**Informazioni obsolete vietate:** presentare la password compromessa come spiegazione ancora valida.  
**Equivalenze ammesse:** “token esposto” o “token compromesso”; non sono ammesse formulazioni come “rubato” o “pubblicato”, perché introdurrebbero una modalità specifica non fornita.

### Q3 — Azione completata

**Domanda**

> Quale token è stato revocato, quale lo ha sostituito e a quale risorsa può accedere il nuovo token?

**Risposta attesa**

> `reporting-v1` è stato revocato e sostituito da `reporting-v2`, che può soltanto leggere la cartella `monthly-reports`.

**Fatti obbligatori:** revoca di `reporting-v1`; attivazione di `reporting-v2`; sola lettura di `monthly-reports`.  
**Evidenza obbligatoria:** `S3-U1`.  
**Informazioni obsolete vietate:** descrivere la revoca come ancora da eseguire.  
**Equivalenze ammesse:** “read-only” come equivalente di “sola lettura”, mantenendo gli identificatori dei token e della cartella.

### Q4 — Attività pendente

**Domanda**

> Quali due verifiche tecniche sono ancora in sospeso?

**Risposta attesa**

> Sono ancora in sospeso la verifica sull'origine dell'esposizione del vecchio token e la verifica sull'eventuale consultazione di documenti.

**Fatti obbligatori:** verifica sull'origine dell'esposizione del vecchio token; verifica sull'eventuale consultazione di documenti.  
**Evidenza obbligatoria:** `S4-U1`.  
**Informazioni obsolete vietate:** affermare che una delle due verifiche sia già completata.  
**Equivalenze ammesse:** formulazioni equivalenti che mantengano distinte le due verifiche.

### Q5 — Informazione locale

**Domanda**

> Quando deve essere consegnato il rapporto preliminare e quale verifica può essere rinviata al rapporto finale?

**Risposta attesa**

> Deve essere consegnato venerdì alle 17:00; la verifica sull'eventuale consultazione di documenti può essere completata per il rapporto finale.

**Fatti obbligatori:** venerdì; ore 17:00; verifica sull'eventuale consultazione di documenti rinviabile.  
**Evidenza obbligatoria:** `S4-U1`.  
**Informazioni obsolete vietate:** nessuna.  
**Equivalenze ammesse:** notazioni orarie equivalenti, per esempio 5 PM, mantenendo corretta la verifica rinviabile.

### Q6 — Collegamento tra sessioni

**Domanda**

> Quali controlli concreti devono essere completati per la verifica richiesta nel rapporto preliminare?

**Risposta attesa**

> Devono essere esaminate la cronologia del repository e la configurazione della pipeline CI per individuare l'origine dell'esposizione del vecchio token.

**Fatti obbligatori:** collegamento tra la verifica prioritaria della sessione 4 e i controlli definiti nella sessione 3; repository e pipeline CI.  
**Evidenze obbligatorie:** `S3-U1`, `S4-U1`.  
**Informazioni obsolete vietate:** sostituire questi controlli con l'analisi dei log di download oppure affermare che la verifica sia già completata.  
**Equivalenze ammesse:** formulazioni equivalenti che identifichino entrambi i controlli richiesti.

### Q7 — Informazione assente

**Domanda**

> Chi ha effettuato l'accesso anomalo?

**Risposta attesa**

> L'identità dell'autore non è stata fornita e non può essere determinata dalle informazioni disponibili.

**Fatti obbligatori:** riconoscimento dell'assenza dell'informazione.  
**Evidenza obbligatoria:** nessuna evidenza positiva; controllo dell'intero scenario.  
**Informazioni obsolete vietate:** attribuire l'accesso a una persona, un gruppo o una categoria non menzionati.  
**Equivalenze ammesse:** qualsiasi astensione esplicita che non introduca sospetti o identità.

## 3. Matrice di raggiungibilità teorica

`1` indica che tutte le evidenze obbligatorie sono accessibili; `0` indica che almeno una evidenza obbligatoria non è accessibile.

| Domanda | Fenomeno | C0 | C1 | C2 |
|---|---|---:|---:|---:|
| Q1 | Scopo | 0 | 0 | 1 |
| Q2 | Informazione aggiornata e obsoleta | 0 | 0 | 1 |
| Q3 | Attività completata | 0 | 0 | 1 |
| Q4 | Attività pendente | 0 | 1 | 1 |
| Q5 | Informazione locale | 0 | 1 | 1 |
| Q6 | Collegamento tra sessioni | 0 | 0 | 1 |
| Q7 | Informazione assente | 0 | 0 | 0 |

### Massimo teorico di raggiungibilità

| Condizione | Domande raggiungibili | Reachability Rate |
|---|---:|---:|
| C0 | 0/7 | 0,000 |
| C1 | 2/7 | 0,286 |
| C2 | 6/7 | 0,857 |

Q7 non è considerata raggiungibile perché il fatto richiesto non è presente. Il comportamento desiderato è l'astensione corretta in tutte le condizioni.

## 4. Comportamento atteso per condizione

| Domanda | C0 | C1 | C2 |
|---|---|---|---|
| Q1 | Astensione | Astensione | Risposta completa |
| Q2 | Astensione | Astensione | Risposta completa |
| Q3 | Astensione | Astensione | Risposta completa |
| Q4 | Astensione | Risposta completa | Risposta completa |
| Q5 | Astensione | Risposta completa | Risposta completa |
| Q6 | Astensione | Astensione | Risposta completa |
| Q7 | Astensione | Astensione | Astensione |

Questa tabella rappresenta il comportamento corretto dato il perimetro accessibile. Non è una previsione che il modello si comporterà effettivamente così.

## 5. Controlli prima dell'esecuzione

- Nessuna domanda contiene direttamente la propria risposta.
- Q2 richiede di distinguere informazione corrente e obsoleta.
- Q4 e Q5 sono risolvibili con la sola sessione locale.
- Q6 richiede la sessione 3 per conoscere i controlli concreti e la sessione 4 per sapere quale delle due verifiche è prioritaria.
- Q7 non può essere risolta tramite conoscenze esterne sul mondo reale.
- Le sette domande verranno eseguite separatamente e non diventeranno memoria per le prove successive.
- Eventuali ambiguità osservate nelle prime tracce comporteranno una correzione del pilot, non una modifica retroattiva dei risultati finali.
