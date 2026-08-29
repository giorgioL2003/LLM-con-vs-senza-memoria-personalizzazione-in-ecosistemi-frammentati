# Roadmap del progetto di tirocinio

## Principio guida

Il progetto deve partire dagli esperimenti e dai risultati che si vogliono osservare, per poi risalire all'architettura e all'implementazione necessarie.

L'obiettivo non è costruire un prodotto end-to-end o un sistema pronto per la produzione. È sufficiente realizzare un esperimento piccolo, riproducibile e interpretabile, del quale sia possibile spiegare con chiarezza:

- il problema studiato;
- le condizioni confrontate;
- il funzionamento della pipeline;
- il significato delle metriche;
- l'origine degli errori;
- i limiti delle conclusioni.

La libertà concessa dal relatore deve essere utilizzata per circoscrivere il lavoro e scegliere il confronto più chiaro, non per aggiungere componenti non necessarie.

## Ipotesi di lavoro iniziale

Una possibile domanda di ricerca, sufficientemente circoscritta, è:

> Quanto influisce la frammentazione della memoria sulla capacità di un LLM di continuare il progetto di un utente tra conversazioni diverse?

Il confronto iniziale può comprendere tre condizioni:

1. **Nessuna memoria:** il sistema riceve soltanto la richiesta corrente.
2. **Memoria locale:** il sistema può accedere soltanto alle informazioni della sessione corrente.
3. **Memoria condivisa:** il sistema può cercare nelle diverse sessioni appartenenti allo stesso utente.

Tra le condizioni devono rimanere uguali, per quanto possibile:

- modello;
- prompt;
- conversazioni;
- domande;
- metodo di retrieval;
- parametri;
- criteri di valutazione.

Deve cambiare principalmente il perimetro della memoria accessibile.

---

## Fase 1 - Delimitare l'esperimento

### Attività

- Scegliere una sola domanda principale.
- Definire le condizioni da confrontare.
- Stabilire cosa rimane invariato tra le condizioni.
- Dichiarare esplicitamente cosa non viene studiato.

### Elementi esclusi dal primo esperimento

- applicazione web;
- interfaccia grafica;
- autenticazione;
- deployment;
- database complessi;
- sistemi multi-agente;
- knowledge graph;
- confronto tra numerosi modelli;
- benchmark di grandi dimensioni;
- architettura production-ready.

### Risultato della fase

Essere in grado di spiegare in una frase cosa viene studiato e quali aspetti rimangono fuori dal progetto.

---

## Fase 2 - Progettare i risultati prima del software

### Attività

Stabilire anticipatamente cosa misurare:

- evidenza raggiungibile;
- evidenza recuperata;
- risposta completa, parziale o errata;
- utilizzo di decisioni obsolete;
- astensione corretta;
- informazioni inventate;
- eventualmente token utilizzati e latenza.

Immaginare già la tabella finale e definire quali differenze ci si aspetta tra le condizioni.

### Risultato della fase

Sapere come riconoscere un successo e come classificare un errore prima di eseguire il sistema.

---

## Fase 3 - Costruire il pilot

### Attività

Creare inizialmente 2-3 progetti sintetici, ciascuno distribuito su 3-4 sessioni.

Ogni scenario dovrebbe contenere:

- uno scopo principale;
- una decisione iniziale;
- una decisione successiva che sostituisce quella precedente;
- un'attività completata;
- un'attività ancora in sospeso;
- un'informazione disponibile nella sessione corrente;
- un'informazione mai fornita.

Preparare circa 5-7 domande per scenario. Le domande dovrebbero verificare:

- ricordo dello scopo;
- decisione attualmente valida;
- attività completate;
- attività in sospeso;
- informazione locale;
- collegamento tra informazioni locali e precedenti;
- riconoscimento di informazioni mai fornite.

### Risultato della fase

Ottenere un piccolo benchmark che rappresenti il fenomeno studiato senza pretendere di coprire tutti i possibili sistemi di memoria.

---

## Fase 4 - Costruire l'oracle manuale

### Attività

Per ogni domanda stabilire manualmente:

- risposta attesa;
- fatti obbligatori;
- messaggi che costituiscono le evidenze;
- eventuali informazioni obsolete da non utilizzare;
- condizioni nelle quali le evidenze sono raggiungibili;
- comportamento corretto quando l'informazione manca.

Controllare che:

- la domanda non contenga già la risposta;
- la risposta sia ricavabile univocamente dalle evidenze;
- le informazioni considerate assenti siano realmente assenti;
- le domande non siano ambigue;
- l'esecuzione di una domanda non modifichi lo stato delle domande successive.

### Risultato della fase

Conoscere il massimo teorico ottenibile da ogni condizione prima di eseguire retrieval e generazione.

---

## Fase 5 - Primo confronto con il relatore

### Materiale da discutere

- domanda di ricerca;
- condizioni confrontate;
- variabili mantenute fisse;
- uno scenario completamente annotato;
- matrice di raggiungibilità;
- metriche previste;
- struttura della tabella finale;
- limiti del pilot;
- dubbi metodologici ancora aperti.

Il punto da validare è il disegno sperimentale, non l'architettura software.

### Risultato della fase

Ottenere la conferma del perimetro oppure correggere il protocollo prima di investire tempo nell'implementazione.

---

## Fase 6 - Progettare l'architettura minima

Soltanto dopo la validazione del protocollo, definire una pipeline essenziale:

```text
conversazioni sintetiche
-> memoria accessibile secondo la condizione
-> retrieval
-> costruzione del contesto
-> risposta
-> valutazione
-> esportazione dei risultati
```

### Componenti minimi

- caricamento degli scenari;
- separazione delle memorie in base alla condizione;
- retrieval delle informazioni;
- costruzione del contesto fornito al modello;
- generazione o estrazione della risposta;
- calcolo delle metriche;
- salvataggio di risultati e tracce.

### Risultato della fase

Disporre di uno schema semplice, nel quale ogni componente esiste perché serve direttamente all'esperimento.

---

## Fase 7 - Implementare con l'AI

L'AI può accelerare:

- scrittura del codice;
- validazione del dataset;
- test automatici;
- costruzione del runner;
- calcolo delle metriche;
- esportazione dei risultati;
- generazione dei grafici.

Lo studente deve invece controllare e comprendere:

- input e output di ogni componente;
- variabili che cambiano tra le condizioni;
- assunzioni introdotte dal codice;
- criteri di valutazione;
- motivazione delle scelte;
- significato delle metriche.

### Risultato della fase

Ottenere un runner minimo e riproducibile, non un prodotto end-to-end.

---

## Fase 8 - Eseguire e correggere il pilot

### Attività

- Eseguire tutte le condizioni sul piccolo benchmark.
- Controllare manualmente una parte significativa delle tracce.
- Verificare che risultati ed evidenze siano esportati correttamente.
- Classificare ogni fallimento.

### Diagnosi degli errori

```text
Informazione irraggiungibile
-> effetto del perimetro o della frammentazione della memoria

Informazione raggiungibile ma non recuperata
-> problema di retrieval o ranking

Informazione recuperata ma risposta errata
-> problema di lettura o generazione

Domanda ambigua o annotazione sbagliata
-> problema del benchmark
```

### Risultato della fase

Verificare che protocollo, benchmark e pipeline funzionino correttamente. I risultati del pilot servono per correggere il metodo, non per formulare conclusioni definitive.

---

## Fase 9 - Congelare l'esperimento

Quando il pilot è stabile:

- fissare scenari e domande;
- fissare evidenze e risposte attese;
- fissare modello, prompt e parametri;
- fissare metriche e criteri di valutazione;
- conservare la versione esatta del protocollo e del codice.

Dopo il congelamento, il benchmark non deve essere modificato sulla base dei risultati finali.

### Risultato della fase

Disporre di un esperimento definito e riproducibile.

---

## Fase 10 - Eseguire l'esperimento finale

### Attività

- Eseguire tutte le condizioni partendo dallo stesso stato iniziale.
- Conservare risultati aggregati e risultati per domanda.
- Conservare le tracce necessarie per diagnosticare gli errori.
- Verificare che ogni configurazione sia stata eseguita correttamente.

### Risultato della fase

Ottenere i dati finali sui quali basare l'analisi.

---

## Fase 11 - Analizzare e interpretare

Produrre poche tabelle e uno o due grafici utili. L'analisi deve spiegare:

- quali differenze dipendono dall'accesso alla memoria;
- quali errori dipendono dal retrieval;
- quali errori dipendono dal modello;
- se vengono utilizzate informazioni obsolete;
- se il sistema si astiene correttamente;
- quali vantaggi introduce la memoria condivisa;
- quali costi o limiti comporta;
- cosa dimostra realmente il piccolo esperimento;
- quali conclusioni non possono essere generalizzate.

### Risultato della fase

Trasformare i numeri in una spiegazione scientifica comprensibile, evitando conclusioni più ampie di quanto consentito dal pilot.

---

## Fase 12 - Concludere il progetto e scrivere la tesi

La scrittura finale può seguire la stessa struttura logica del lavoro:

1. problema e motivazione;
2. domanda di ricerca;
3. protocollo sperimentale;
4. benchmark e condizioni;
5. architettura minima;
6. risultati;
7. analisi degli errori;
8. limiti;
9. conclusioni e possibili sviluppi futuri.

Il valore principale del lavoro non dipende dalla quantità di codice o dalla lunghezza della tesi, ma dalla capacità di motivare le scelte e interpretare correttamente ciò che è stato osservato.

---

## Roadmap sintetica

```text
domanda di ricerca
-> risultati e metriche
-> pilot sintetico
-> oracle manuale
-> confronto con il relatore
-> architettura minima
-> implementazione assistita dall'AI
-> esecuzione e correzione del pilot
-> congelamento del protocollo
-> esperimento finale
-> analisi e interpretazione
-> tesi
```

## Criterio di completamento

Il progetto può considerarsi concluso quando esiste un esperimento piccolo e riproducibile del quale sia possibile spiegare:

- perché è stata scelta la domanda di ricerca;
- perché sono state scelte quelle condizioni;
- quali variabili sono controllate;
- come funziona la pipeline;
- come vengono calcolate le metriche;
- perché si verifica ogni classe di errore;
- cosa indicano i risultati;
- quali sono i limiti del lavoro.

