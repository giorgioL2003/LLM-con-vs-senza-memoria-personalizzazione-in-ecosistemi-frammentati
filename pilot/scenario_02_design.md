# Scenario 02 — Disegno del recupero password

**Stato:** bozza v0.1, non congelata  
**Dominio:** cybersecurity difensiva  
**Tipo di attività:** correzione multi-sessione di un flusso di recupero password  
**Scopo del documento:** definire i fatti e la loro distribuzione prima del dry run.

## 1. Confine del caso

Lo scenario riguarda la continuità di un'attività tecnica tra conversazioni. Non valuta la conoscenza generale del modello in materia di autenticazione e non richiede conoscenze esterne.

Tutti i nomi, i componenti e gli eventi sono sintetici. La correttezza delle risposte dipende soltanto dalle informazioni contenute nelle quattro sessioni.

## 2. Contesto narrativo

Lumen Market è una piattaforma di commercio elettronico fittizia. Tre account hanno subito un cambio di password non autorizzato attraverso il flusso di recupero. Il gruppo deve correggere il problema senza rendere inutilizzabile il recupero password nell'app mobile.

L'attività viene distribuita su quattro sessioni. Una decisione iniziale viene superata dalle evidenze, una parte del lavoro viene completata e rimane aperta una verifica legata alla consegna ritardata delle email.

## 3. Stato che deve evolvere

| Elemento | Stato previsto |
|---|---|
| Obiettivo | Impedire altri cambi di password non autorizzati e mantenere utilizzabile il recupero password nell'app mobile |
| Decisione iniziale | Inserire un CAPTCHA dopo la prima richiesta di recupero |
| Evidenza successiva | Per ogni account risulta una sola richiesta, ma lo stesso link è stato usato due volte |
| Decisione aggiornata | Token utilizzabile una sola volta e con scadenza dopo 15 minuti |
| Informazione obsoleta | Il CAPTCHA come intervento principale scelto per correggere il problema |
| Attività completata | Implementazione del consumo singolo in `ResetTokenService` e test web superati |
| Verifica completata | Test del collegamento nell'app mobile, con ritorno corretto alla schermata di accesso |
| Attività in sospeso | Test di un'email consegnata dopo il limite di validità |
| Informazione locale | Riunione di verifica fissata per martedì alle 11:30 e risultato richiesto |
| Informazione mai fornita | Persona responsabile dell'approvazione del rilascio in produzione |

## 4. Distribuzione tra le sessioni

### Sessione 1 — Apertura e decisione iniziale

- descrivere i cambi di password non autorizzati;
- fissare i due obiettivi;
- scegliere inizialmente il CAPTCHA;
- non anticipare il riutilizzo dei link.

### Sessione 2 — Evidenza e cambio di decisione

- mostrare che non ci sono richieste ripetute;
- mostrare che lo stesso link è stato utilizzato due volte;
- superare esplicitamente la decisione del CAPTCHA;
- fissare uso singolo e scadenza di 15 minuti.

### Sessione 3 — Implementazione e verifiche

- confermare l'implementazione in `ResetTokenService`;
- confermare il superamento dei test web;
- lasciare aperti il test del collegamento mobile e il test dell'email ritardata;
- non ripetere il valore di 15 minuti.

### Sessione 4 — Stato locale

- confermare il completamento del test mobile e il suo esito;
- lasciare aperto soltanto il test dell'email ritardata;
- fissare la riunione di verifica;
- richiedere il risultato del test ancora pendente;
- non ripetere la regola dei 15 minuti.

## 5. Obiettivo di bilanciamento

Lo Scenario 01 rende raggiungibili in C1 Q4 e Q5. Lo Scenario 02 deve portare a tre domande raggiungibili con la memoria locale:

- verifica completata;
- verifica ancora pendente;
- scadenza e contenuto della riunione.

Le domande su obiettivo, decisione aggiornata e collegamento tra stato locale e regola precedente devono invece richiedere la memoria condivisa.

## 6. Passo successivo

Dopo la revisione del disegno vengono controllati i messaggi, le sette domande, l'oracle e la matrice. Lo scenario rimane modificabile fino al dry run completo.

