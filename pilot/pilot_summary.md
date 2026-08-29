# Stato complessivo del pilot

**Data:** 2026-08-29  
**Stato:** due scenari validati con dry run; pilot non congelato

## 1. Materiale disponibile

Il pilot contiene:

- 2 scenari sintetici;
- 4 sessioni per scenario;
- 7 domande per scenario;
- 14 domande complessive;
- un oracle manuale per ogni domanda;
- una matrice di raggiungibilità per C0, C1 e C2;
- 42 esecuzioni di dry run, una per ogni combinazione tra domanda e condizione.

## 2. Copertura teorica

| Condizione | Scenario 01 | Scenario 02 | Totale |
|---|---:|---:|---:|
| C0 — Nessuna memoria | 0/7 | 0/7 | 0/14 |
| C1 — Memoria locale | 2/7 | 3/7 | 5/14 |
| C2 — Memoria condivisa | 6/7 | 6/7 | 12/14 |

La differenza tra C1 e C2 è intenzionale: alcune informazioni sono presenti nell'ultima sessione, mentre altre richiedono di recuperare decisioni o regole stabilite in sessioni precedenti.

## 3. Risultati diagnostici dei dry run

| Scenario | C0 | C1 | C2 | Totale appropriato |
|---|---:|---:|---:|---:|
| Scenario 01 | 7/7 | 6/7 | 7/7 | 20/21 |
| Scenario 02 | 7/7 | 6/7 | 6/7 | 19/21 |
| Totale | 14/14 | 12/14 | 13/14 | 39/42 |

Questi valori servono soltanto a validare il benchmark. I contesti sono stati forniti manualmente, quindi non è stato misurato il retrieval.

## 4. Problemi emersi

### Difetto del benchmark corretto

Nel primo scenario Q4 era stata considerata non raggiungibile in C1, ma la Sessione 4 conteneva entrambe le verifiche richieste. L'oracle e la matrice sono stati corretti durante il pilot.

### Errori del modello conservati

- Scenario 01, C1-Q1: il modello ha scambiato le verifiche pendenti per gli obiettivi iniziali.
- Scenario 02, C1-Q3: il modello ha indicato il test pendente invece di quello completato.
- Scenario 02, C2-Q3: lo stesso errore è comparso anche con il contesto completo.

Queste domande non sono state rese più facili, perché le evidenze sono chiare e gli errori appartengono alla fase di lettura o risposta del modello.

## 5. Cosa è stato dimostrato finora

Il pilot mostra che:

- le condizioni C0, C1 e C2 producono perimetri di informazione realmente diversi;
- le domande distinguono informazioni locali, informazioni distribuite e informazioni assenti;
- l'oracle consente di separare un difetto del benchmark da un errore del modello;
- il protocollo è abbastanza chiaro da essere discusso prima dell'implementazione.

Il pilot non mostra ancora la qualità di un retriever e non permette conclusioni finali sull'efficacia della memoria condivisa.

## 6. Decisione consigliata

Non aggiungere automaticamente uno Scenario 03. I due scenari soddisfano il minimo previsto dalla roadmap e coprono già i fenomeni principali. Un terzo scenario dovrebbe essere aggiunto soltanto se introduce un caso metodologicamente diverso oppure se viene richiesto durante il confronto con il relatore.

Il prossimo passo è il primo confronto metodologico: presentare domanda di ricerca, condizioni, matrice, due esempi di oracle, problemi emersi e limiti. L'architettura e il codice vengono dopo questo controllo.

## 7. Cosa deve saper spiegare lo studente

- C0 non riceve informazioni precedenti.
- C1 vede soltanto l'ultima sessione.
- C2 vede tutte le sessioni dello scenario.
- La raggiungibilità indica se il contesto contiene le evidenze necessarie.
- Un'informazione raggiungibile può comunque essere letta o usata male dal modello.
- Il dry run usa contesti manuali e non valuta ancora il retrieval.
- Il benchmark viene corretto soltanto quando domanda, evidenza o oracle sono difettosi, non ogni volta che il modello sbaglia.

