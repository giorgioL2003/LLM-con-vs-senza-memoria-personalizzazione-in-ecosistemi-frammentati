# Scheda dell'esperimento

**Stato:** bozza metodologica v0.1  
**Fasi della roadmap:** 1 — delimitazione; 2 — progettazione dei risultati  
**Nota:** questa scheda precede la costruzione del dataset. Le scelte potranno essere corrette durante il pilot, prima del congelamento dell'esperimento.

## 1. Domanda di ricerca

> In che misura il perimetro della memoria accessibile influenza la capacità di un LLM di continuare correttamente un'attività distribuita tra più conversazioni?

Il fenomeno osservato è la continuità tra sessioni. Il dominio della cybersecurity fornirà un contesto narrativo concreto, ma l'esperimento non valuterà le capacità generali del modello in materia di sicurezza informatica.

## 2. Unità sperimentale

Un'unità sperimentale è formata da:

- uno scenario sintetico distribuito su quattro sessioni ordinate;
- una domanda di valutazione;
- un oracle manuale con risposta attesa ed evidenze obbligatorie;
- una delle condizioni di memoria definite sotto.

Ogni domanda viene eseguita su una copia indipendente dello stesso stato iniziale. Le risposte precedenti non entrano nella memoria e non possono influenzare le prove successive.

## 3. Condizioni confrontate

### C0 — Nessuna memoria

Il modello riceve le istruzioni di sistema e la domanda corrente. Non può accedere ai messaggi precedenti dello scenario.

### C1 — Memoria locale

Il modello può cercare soltanto nei messaggi della sessione nella quale viene posta la domanda. Non può accedere alle sessioni precedenti dello stesso scenario.

### C2 — Memoria condivisa

Il modello può cercare nei messaggi di tutte le sessioni precedenti e della sessione corrente appartenenti allo stesso scenario.

Nelle condizioni C1 e C2 verrà applicata la stessa procedura di retrieval. Cambierà soltanto l'insieme dei messaggi nel quale il sistema può cercare. In C0 il corpus di memoria è vuoto.

## 4. Variabile indipendente

La variabile modificata è il **perimetro della memoria accessibile**:

- nessun messaggio precedente;
- sola sessione corrente;
- tutte le sessioni dello scenario.

## 5. Variabili controllate

Tra le condizioni devono rimanere uguali:

- modello e relativa versione;
- prompt di sistema e istruzioni di risposta;
- scenario e ordine dei messaggi;
- domanda di valutazione;
- procedura e parametri di retrieval;
- numero massimo di evidenze recuperate;
- parametri di generazione;
- criteri di valutazione;
- stato iniziale di ogni prova.

La versione concreta di modello, prompt e parametri verrà scelta prima dell'implementazione e fissata prima dell'esperimento finale.

## 6. Aspetti esclusi

Il primo esperimento non studia:

- quale modello sia complessivamente migliore;
- quale tecnica di embedding o retrieval sia migliore;
- memoria a lungo termine di utenti reali;
- apprendimento o aggiornamento dei pesi del modello;
- sicurezza offensiva o efficacia di contromisure reali;
- correttezza generale delle conoscenze di cybersecurity del modello;
- interfacce grafiche, autenticazione o deployment;
- database complessi, knowledge graph o sistemi multi-agente;
- prestazioni in produzione o generalizzazione a tutti i domini.

## 7. Fenomeni che il pilot deve contenere

Ogni scenario deve includere almeno:

- uno scopo principale;
- un'ipotesi o decisione iniziale;
- un aggiornamento che renda obsoleta l'ipotesi o decisione precedente;
- un'attività completata;
- un'attività ancora in sospeso;
- un'informazione presente nella sessione corrente;
- un collegamento che richieda informazioni da sessioni diverse;
- un'informazione mai fornita, per verificare l'astensione.

## 8. Oracle manuale

Per ciascuna domanda l'oracle deve indicare:

- risposta attesa;
- fatti obbligatori;
- messaggi che costituiscono le evidenze;
- informazioni obsolete da non utilizzare;
- raggiungibilità teorica in C0, C1 e C2;
- comportamento corretto quando l'informazione è assente;
- eventuali risposte equivalenti ammesse.

La raggiungibilità è determinata prima di eseguire retrieval e generazione.

## 9. Annotazioni per singola domanda

### 9.1 Indicatore di raggiungibilità

Valore binario per domanda e condizione:

- **1:** tutte le evidenze obbligatorie sono contenute nel perimetro accessibile;
- **0:** almeno un'evidenza obbligatoria non è contenuta nel perimetro accessibile.

Misura il massimo teorico della condizione e non le capacità del retriever o del modello.

Per una domanda che richiede un fatto mai fornito, la raggiungibilità vale **0** in tutte le condizioni: il fatto non è disponibile e il comportamento corretto è l'astensione. Il controllo del corpus completo serve a verificare l'assenza durante la costruzione dell'oracle, ma non trasforma il fatto assente in evidenza raggiungibile.

### 9.2 Indicatore di recupero

Valore binario, calcolato soltanto quando l'evidenza è raggiungibile:

- **1:** tutte le evidenze obbligatorie sono presenti nel contesto recuperato;
- **0:** almeno un'evidenza obbligatoria raggiungibile non viene recuperata.

### 9.3 Classe della risposta

Ogni risposta viene classificata manualmente come:

- **completa:** contiene tutti i fatti obbligatori e non contiene contraddizioni;
- **parziale:** contiene almeno un fatto corretto, ma omette parte della risposta richiesta;
- **errata:** contraddice l'oracle, usa come valida un'informazione obsoleta oppure non risponde alla domanda;
- **astensione corretta:** dichiara che l'informazione non è disponibile quando le evidenze obbligatorie non sono accessibili nella condizione eseguita.

### 9.4 Indicatori di errore

Vengono inoltre registrati separatamente:

- **uso di informazione obsoleta:** la risposta adotta una decisione o ipotesi superata;
- **informazione inventata:** la risposta introduce un fatto non sostenuto dalle evidenze accessibili;
- **astensione errata:** il modello non risponde nonostante l'evidenza necessaria sia stata recuperata.

Questi valori descrivono una singola esecuzione. Diventano metriche soltanto quando vengono aggregati su più domande della stessa condizione.

## 10. Metriche aggregate

Per ogni condizione `c`, si indica con `N_c` il numero totale di domande eseguite in quella condizione.

### 10.1 Reachability Rate

Proporzione di domande per le quali tutte le evidenze obbligatorie sono presenti nel perimetro accessibile:

```text
ReachabilityRate(c) = domande raggiungibili in c / N_c
```

Questa metrica dipende dal perimetro della memoria e dall'oracle, non dal comportamento del retriever o del modello.

### 10.2 Retrieval Success Rate condizionato alla raggiungibilità

Proporzione di domande raggiungibili per le quali il retrieval recupera tutte le evidenze obbligatorie:

```text
RetrievalSuccess(c) = domande con evidenza completa recuperata in c
                      / domande raggiungibili in c
```

Se nessuna domanda è raggiungibile, la metrica non viene calcolata e deve essere registrata come non applicabile, non come zero.

### 10.3 Complete Answer Rate

Proporzione di tutte le esecuzioni che producono una risposta completa e supportata:

```text
CompleteAnswer(c) = risposte complete in c / N_c
```

Questa è la metrica end-to-end principale per misurare quante domande ricevono effettivamente una risposta utile. Le risposte parziali non vengono contate come complete, ma sono riportate separatamente.

### 10.4 Answer Success Rate condizionato al recupero

Proporzione di domande per le quali il modello risponde completamente quando tutte le evidenze obbligatorie sono state recuperate:

```text
AnswerSuccess(c) = risposte complete in c con evidenza completa recuperata
                   / domande in c con evidenza completa recuperata
```

Permette di separare gli errori di risposta dagli errori di retrieval. Se nessuna domanda dispone di evidenza completa recuperata, la metrica è non applicabile.

### 10.5 Correct Abstention Rate

Calcolata sulle esecuzioni nelle quali almeno un'evidenza obbligatoria non è accessibile nella condizione:

```text
CorrectAbstention(c) = astensioni corrette in c
                       / domande non raggiungibili in c
```

Questa metrica viene riportata separatamente dalla Complete Answer Rate: un sistema che si astiene sempre può essere prudente, ma non è utile quando l'evidenza è disponibile.

### 10.6 Obsolete Information Use Rate

```text
ObsoleteUse(c) = risposte che adottano informazioni obsolete in c / N_c
```

### 10.7 Unsupported Claim Rate

```text
UnsupportedClaim(c) = risposte con almeno un fatto non supportato in c / N_c
```

Per ogni condizione vengono inoltre riportate le proporzioni di risposte complete, parziali ed errate. Token e latenza potranno essere registrati in modo descrittivo, ma non costituiscono metriche principali del primo pilot.

## 11. Classificazione causale dei fallimenti

Ogni fallimento deve essere ricondotto alla prima causa osservabile nella pipeline:

1. **evidenza irraggiungibile:** il perimetro della condizione non contiene le informazioni necessarie;
2. **evidenza raggiungibile ma non recuperata:** fallimento del retrieval o del ranking;
3. **evidenza recuperata ma risposta non corretta:** fallimento di lettura, ragionamento o generazione;
4. **domanda o oracle difettosi:** ambiguità o errore nel benchmark.

Una domanda difettosa non deve essere interpretata come errore del sistema: va corretta durante il pilot e prima del congelamento.

## 12. Risultati attesi prima dell'esecuzione

Queste sono previsioni qualitative, non risultati già osservati:

| Condizione | Raggiungibilità attesa | Comportamento atteso | Rischio caratteristico |
|---|---|---|---|
| C0 — Nessuna memoria | Bassa | Risponde solo quando la domanda è autosufficiente; negli altri casi dovrebbe astenersi | Invenzione di informazioni |
| C1 — Memoria locale | Media | Risponde alle domande basate sulla sessione corrente | Perdita delle decisioni prese nelle sessioni precedenti |
| C2 — Memoria condivisa | Alta | Collega informazioni distribuite tra sessioni | Mancato retrieval o selezione di informazioni obsolete |

L'aspettativa principale è che C2 aumenti la raggiungibilità delle evidenze necessarie. Non si assume in anticipo che una maggiore raggiungibilità produca sempre una risposta corretta: retrieval e generazione possono ancora fallire.

## 13. Struttura minima della futura tabella per domanda

| Campo | Descrizione |
|---|---|
| scenario_id | Identificatore dello scenario |
| question_id | Identificatore della domanda |
| condition | C0, C1 o C2 |
| reachable | Tutte le evidenze obbligatorie sono accessibili |
| retrieved | Tutte le evidenze obbligatorie sono state recuperate |
| answer_class | completa, parziale, errata, astensione corretta |
| obsolete_used | È stata utilizzata un'informazione superata |
| unsupported_claim | È stata introdotta un'informazione non supportata |
| error_origin | reachability, retrieval, answer oppure benchmark |
| trace_ref | Riferimento alla traccia completa |

## 14. Criteri per passare alla costruzione del pilot

La fase di progettazione può considerarsi sufficiente quando:

- la domanda di ricerca è spiegabile in una frase;
- C0, C1 e C2 sono distinguibili senza ambiguità;
- è chiaro cosa cambia e cosa rimane fisso;
- ogni metrica ha una regola di assegnazione;
- la tabella finale può essere compilata senza inventare nuovi criteri dopo aver visto le risposte;
- il dominio della cybersecurity rimane un contesto e non diventa un secondo oggetto di valutazione.

Superati questi controlli, il passo successivo sarà costruire un solo scenario di incidente sintetico con quattro sessioni, 5–7 domande e oracle manuale. Gli scenari successivi verranno aggiunti soltanto se introducono fenomeni non coperti dal primo.
