# Scenario 01 — Protocollo di validazione completa

**Stato:** dry run completato; correzione metodologica di Q4 applicata; non congelato  
**Riferimento:** `scenario_01_sessions.md`, `scenario_01_oracle.md`  
**Scopo:** verificare la qualità diagnostica delle domande prima di aggiungere altri scenari e prima di implementare il retrieval.

## 1. Cosa misura questa validazione

La validazione controlla se, dato manualmente il contesto previsto da C0, C1 o C2, il modello:

- risponde quando tutte le evidenze obbligatorie sono presenti;
- si astiene quando il contesto non è sufficiente;
- distingue informazioni correnti e obsolete;
- collega correttamente informazioni distribuite tra sessioni;
- evita di inventare informazioni mai fornite.

Il contesto viene fornito manualmente. Questa prova non misura il retrieval, non produce risultati finali e non permette confronti generali tra modelli.

## 2. Esito dell'audit metodologico

| Domanda | Controllo principale | Esito |
|---|---|---|
| Q1 | Gli obiettivi specifici compaiono soltanto in S1 | Superato |
| Q2 | Per nominare ipotesi corrente e superata servono S1 e S2 | Superato |
| Q3 | Token, sostituzione e risorsa specifica compaiono in S3 | Superato |
| Q4 | Le due verifiche pendenti compaiono nella sessione locale S4 | Superato dopo correzione dell'oracle |
| Q5 | Scadenza e rinvio compaiono nella sola sessione locale S4 | Superato |
| Q6 | La priorità viene da S4, mentre i controlli concreti vengono da S3 | Superato |
| Q7 | L'identità non compare in nessuna sessione | Superato |

Il dry run ha mostrato che la matrice originale non era corretta per Q4. La Sessione 4 contiene entrambe le verifiche pendenti, quindi Q4 è raggiungibile anche in C1. L'oracle e la matrice sono stati corretti dopo il pilot.

Rimane intenzionale, per questa prima prova diagnostica, lo sbilanciamento di C1: Q4 e Q5 sono completamente risolvibili con la memoria locale. Lo Scenario 02 dovrà aumentare ulteriormente i casi raggiungibili in C1.

## 3. Protocollo fissato

1. Usare lo stesso modello, la stessa versione visibile e la stessa impostazione di sforzo per tutte le prove.
2. Eseguire le 21 combinazioni domanda-condizione in 21 chat nuove e indipendenti.
3. Svolgere tutte le prove nella stessa finestra temporale, per quanto possibile.
4. Non mostrare al modello oracle, risposta attesa, evidenze obbligatorie o classificazione prevista.
5. Non correggere, aiutare o interrogare nuovamente il modello nella stessa chat.
6. Conservare la prima risposta integrale di ogni esecuzione.
7. Classificare le risposte soltanto dopo averle raccolte.
8. Registrare eventuali rifiuti tecnici o errori dell'interfaccia come esecuzioni non valide, da ripetere.

Una singola esecuzione per cella è sufficiente per controllare il benchmark durante il pilot. Non è sufficiente per stimare la variabilità statistica del modello.

## 4. Istruzione comune

Usare senza modificarla in tutte le chat:

> Rispondi soltanto in base al contesto fornito. Se il contesto non contiene informazioni sufficienti per rispondere, dichiara esplicitamente che non disponi di informazioni sufficienti. Non usare conoscenze esterne, non formulare ipotesi e non inventare dettagli. Fornisci una risposta breve in italiano.

Subito dopo l'istruzione inserire il contesto della condizione e una sola domanda.

## 5. Contesto per condizione

### C0 — Nessuna memoria

Inserire:

```text
CONTESTO:
Nessun contesto disponibile.
```

### C1 — Memoria locale

Inserire esclusivamente la Sessione 4 di `scenario_01_sessions.md`, compresi S4-U1 e S4-A1. Non includere le sessioni precedenti.

### C2 — Memoria condivisa

Inserire le Sessioni 1–4 complete di `scenario_01_sessions.md`, nello stesso ordine e senza riassumerle.

## 6. Domande

Eseguire separatamente le sette domande riportate in `scenario_01_oracle.md`:

- Q1 — Quali due obiettivi operativi sono stati fissati per l'indagine?
- Q2 — Qual è l'ipotesi attualmente valida sulla modalità dell'accesso anomalo e quale ipotesi è stata superata?
- Q3 — Quale token è stato revocato, quale lo ha sostituito e a quale risorsa può accedere il nuovo token?
- Q4 — Quali due verifiche tecniche sono ancora in sospeso?
- Q5 — Quando deve essere consegnato il rapporto preliminare e quale verifica può essere rinviata al rapporto finale?
- Q6 — Quali controlli concreti devono essere completati per la verifica richiesta nel rapporto preliminare?
- Q7 — Chi ha effettuato l'accesso anomalo?

## 7. Ordine delle esecuzioni

Per rendere il procedimento facile da controllare, usare questo ordine fisso:

```text
C0-Q1, C0-Q2, C0-Q3, C0-Q4, C0-Q5, C0-Q6, C0-Q7
C1-Q1, C1-Q2, C1-Q3, C1-Q4, C1-Q5, C1-Q6, C1-Q7
C2-Q1, C2-Q2, C2-Q3, C2-Q4, C2-Q5, C2-Q6, C2-Q7
```

Le chat devono comunque rimanere indipendenti: l'ordine serve soltanto a evitare omissioni.

## 8. Registro delle esecuzioni

**Data:** 2026-08-29  
**Modello e versione mostrata:** Claude Opus 5  
**Impostazione di sforzo:** Alto  
**Interfaccia utilizzata:** app Claude

| ID | Raggiungibile | Comportamento atteso | Risposta osservata | Classificazione | Valida |
|---|---:|---|---|---|---|
| C0-Q1 | 0 | Astensione | Astensione | Astensione corretta | Sì |
| C0-Q2 | 0 | Astensione | Astensione | Astensione corretta | Sì |
| C0-Q3 | 0 | Astensione | Astensione | Astensione corretta | Sì |
| C0-Q4 | 0 | Astensione | Astensione | Astensione corretta | Sì |
| C0-Q5 | 0 | Astensione | Astensione | Astensione corretta | Sì |
| C0-Q6 | 0 | Astensione | Astensione | Astensione corretta | Sì |
| C0-Q7 | 0 | Astensione | Astensione | Astensione corretta | Sì |
| C1-Q1 | 0 | Astensione | Risposta non supportata | Errata | Sì |
| C1-Q2 | 0 | Astensione | Astensione | Astensione corretta | Sì |
| C1-Q3 | 0 | Astensione | Astensione | Astensione corretta | Sì |
| C1-Q4 | 1 | Risposta completa | Risposta completa | Risposta completa | Sì |
| C1-Q5 | 1 | Risposta completa | Risposta completa | Risposta completa | Sì |
| C1-Q6 | 0 | Astensione | Astensione | Astensione corretta | Sì |
| C1-Q7 | 0 | Astensione | Astensione | Astensione corretta | Sì |
| C2-Q1 | 1 | Risposta completa | Risposta completa | Risposta completa | Sì |
| C2-Q2 | 1 | Risposta completa | Risposta completa | Risposta completa | Sì |
| C2-Q3 | 1 | Risposta completa | Risposta completa | Risposta completa | Sì |
| C2-Q4 | 1 | Risposta completa | Risposta completa | Risposta completa | Sì |
| C2-Q5 | 1 | Risposta completa | Risposta completa | Risposta completa | Sì |
| C2-Q6 | 1 | Risposta completa | Risposta completa | Risposta completa | Sì |
| C2-Q7 | 0 | Astensione | Astensione | Astensione corretta | Sì |

Le risposte integrali e l'analisi sono conservate in `dry_run_scenario_01_results.md`. Il precedente dry run di Q6 rimane in `dry_run_q6_results.md` come evidenza preliminare separata.

## 9. Regole di classificazione

- **Risposta completa:** contiene tutti i fatti obbligatori e nessuna contraddizione.
- **Risposta parziale:** contiene almeno un fatto corretto ma ne omette uno obbligatorio.
- **Risposta errata:** contraddice l'oracle, presenta come valida un'informazione obsoleta o non risponde alla domanda.
- **Astensione corretta:** dichiara l'insufficienza del contesto quando la cella non è raggiungibile.

Registrare inoltre, separatamente, l'eventuale uso di informazioni obsolete o l'introduzione di informazioni non supportate.

## 10. Come interpretare un fallimento

In questo dry run il retrieval non esiste, perché il contesto viene fornito manualmente. Le cause possibili sono quindi:

1. **comportamento del modello:** il contesto è adeguato ma la risposta è incompleta, errata o inventata;
2. **difetto del benchmark:** la domanda è ambigua, la risposta attesa non è univoca o il contesto contiene indizi non previsti;
3. **esecuzione non valida:** contesto errato, chat non indipendente, istruzione modificata o errore tecnico.

Un errore del modello non comporta automaticamente la modifica della domanda. Il benchmark va corretto soltanto quando viene identificato un difetto della domanda, dell'oracle o delle evidenze.

## 11. Criterio di completamento

La validazione dello Scenario 01 è completata quando:

- sono state raccolte 21 risposte valide;
- ogni risposta è stata confrontata con l'oracle;
- ogni scostamento è stato attribuito al modello, al benchmark o a un'esecuzione non valida;
- le eventuali ambiguità sono state corrette e ricontrollate;
- si può spiegare perché ciascuna cella è raggiungibile oppure non raggiungibile.
