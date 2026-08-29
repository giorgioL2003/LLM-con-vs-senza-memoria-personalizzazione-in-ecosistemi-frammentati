# Scenario 01 — Revisione metodologica

**Stato:** revisione della bozza v0.1  
**Riferimento roadmap:** fasi 3 e 4

## Scopo della revisione

Controllare che le domande misurino realmente l'accesso alla memoria e non possano essere risolte facilmente attraverso risposte generiche o indizi contenuti nella domanda.

## Problemi individuati e correzioni

### 1. Q1 era troppo generica

La risposta “identificare la causa e contenere l'incidente” poteva essere indovinata senza leggere lo scenario. Gli obiettivi sono stati resi specifici: uso di `svc-reporting`, generazione dei report mensili e continuità della consultazione.

### 2. Q2 non richiedeva entrambe le evidenze dichiarate

La sessione 2 ripeteva per intero sia l'ipotesi iniziale sia quella aggiornata. È stata modificata affinché identifichi la nuova ipotesi e faccia riferimento alla spiegazione precedente; per nominare l'ipotesi superata serve ora anche la sessione 1.

### 3. Q3 poteva essere risposta in modo plausibile per conoscenza generale

“Revocare il token e limitarlo alla sola lettura” è una risposta standard. Sono stati introdotti identificatori e una risorsa specifica: `reporting-v1`, `reporting-v2` e `monthly-reports`.

### 4. Q6 non richiedeva davvero un collegamento tra sessioni

Esisteva una sola attività pendente, quindi la risposta poteva essere ricavata dalla sessione 3 senza usare la sessione 4. Sono state introdotte due verifiche pendenti. La sessione 4 stabilisce quale deve entrare nel rapporto preliminare; la sessione 3 contiene i controlli concreti associati.

## Controlli superati

- L'informazione locale rimane confinata alla sessione 4.
- L'identità dell'autore dell'accesso non viene mai fornita.
- Le domande non modificano lo stato dello scenario.
- Le risposte dell'assistente non introducono fatti nuovi.
- Le dipendenze dichiarate corrispondono alle evidenze realmente necessarie.

## Limite ancora aperto

Nel primo scenario C1 può rispondere completamente a Q4 e Q5. Rimane meno rappresentata di C2, ma lo sbilanciamento è accettabile per una prima prova diagnostica e potrà essere compensato nello Scenario 02.

## Esito

Lo scenario ha superato il dry run manuale dopo la correzione di Q4. Rimane una bozza non congelata fino al completamento del pilot complessivo, ma al momento non sono emerse altre ambiguità del benchmark.

Il dry run manuale di Q6 è stato successivamente eseguito su Claude in tre chat separate. C0 e C1 hanno prodotto l'astensione prevista; C2 ha identificato correttamente cronologia del repository e configurazione della pipeline CI. I dettagli sono registrati in `dry_run_q6_results.md`.

## Secondo audit e protocollo completo

È stato successivamente controllato l'allineamento tra le sette domande, le evidenze obbligatorie e la matrice di raggiungibilità. Il controllo non ha individuato ulteriori correzioni necessarie prima delle esecuzioni.

Il protocollo uniforme per le 21 combinazioni tra sette domande e tre condizioni è registrato in `scenario_01_validation.md`. Il precedente dry run di Q6 resta una prova preliminare utile, ma Q6 verrà ripetuta nel protocollo completo per non aggregare automaticamente esecuzioni svolte con modalità diverse.

## Correzione dopo il dry run completo

Il dry run completo ha mostrato che Q4 è raggiungibile anche in C1: la Sessione 4 nomina entrambe le verifiche ancora in sospeso. L'oracle è stato quindi corretto senza modificare la domanda. Q4 richiede ora di identificare le due verifiche, mentre Q6 continua a richiedere il collegamento tra sessioni per ricostruire i controlli concreti.

Dopo la correzione, 20 risposte su 21 risultano appropriate. L'unico errore del modello è C1-Q1, dove le verifiche pendenti sono state scambiate per gli obiettivi iniziali dell'indagine.
