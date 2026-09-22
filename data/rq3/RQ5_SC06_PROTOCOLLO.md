# RQ5 / SC06 — protocollo congelato per la realizzazione

**Stato:** scelte di progettazione concluse il 22 settembre 2026. Il protocollo è pronto per essere tradotto in codice; nessuna prova SC06 è stata eseguita.

## Domanda e confine del risultato

**RQ5:** A parità di contesto recuperato, come varia la capacità di produrre una risposta corretta e supportata al variare del modello generativo?

SC06 usa schede reali del VERIS Community Database. I fatti derivano dal dataset; alias, messaggi, ordine e domande sono costruiti. Il confronto riguarda due specifiche copie quantizzate eseguite con Ollama sul computer usato per le prove. Non produrrà una classifica generale delle famiglie Gemma e Llama.

Per isolare il modello di risposta, SC06 non confronterà strategie di memoria. Il contesto viene costruito offline con una regola deterministica e viene inviato identico ai due modelli. Si potrà quindi attribuire una differenza osservata alla fase di generazione entro i limiti del disegno, senza confonderla con contesti recuperati diversi.

## Dati e suddivisione

Le 708 schede già selezionate formano 236 episodi di tre casi. La separazione sviluppo/valutazione è fissata prima delle generazioni:

| Insieme | Episodi | Casi | Domande per condizione |
|---|---:|---:|---:|
| Sviluppo | E001–E012 | 36 | 108 |
| Valutazione | E013–E236 | 672 | 2.016 |

Lo sviluppo serve soltanto per controllare costruzione dei contesti, parser, formato e tempi. Non entra nei risultati. Una modifica dopo lo sviluppo richiede una nuova versione della configurazione; dopo l'avvio della valutazione la configurazione non cambia.

## Due condizioni di contesto

Per ogni domanda vengono creati due input:

1. **Sufficiente:** contiene il blocco con il valore richiesto del caso bersaglio e due blocchi di distrazione, uno per ciascun altro caso dell'episodio.
2. **Insufficiente:** rimuove ogni blocco del caso bersaglio e conserva gli stessi due blocchi di distrazione. La risposta corretta è `{"values": []}`.

Per ciascun altro caso si usa lo stesso campo della domanda, se disponibile; altrimenti il primo campo disponibile in ordine lessicografico. I blocchi vengono ordinati mediante SHA-256, così il caso bersaglio non occupa sempre la stessa posizione. Gli input non contengono identificativi VERIS, fonti, risposte attese o valori usati per riconoscere le confusioni.

Questa scelta permette di osservare due capacità distinte:

- usare correttamente un'evidenza presente;
- riconoscere che l'evidenza del caso richiesto manca, anche quando sono presenti dati di casi simili.

Le informazioni obsolete restano fuori da SC06: il dataset preparato non contiene una sequenza controllata di revisioni temporali.

## Modelli e generazione

| Modello | Tag e copia locale | Quantizzazione |
|---|---|---|
| Gemma 3 4B IT, Google | `gemma3:4b`, digest `a2af6cc3...195f5a` | Q4_K_M |
| Llama 3.2 3B Instruct, Meta | `llama3.2:3b`, digest `a80c4f17...b72` | Q4_K_M |

Entrambi sono già installati e hanno superato un controllo locale di avvio. Verranno eseguiti uno alla volta con Ollama 0.34.2, temperatura 0, seed 42, finestra di contesto 4.096 e massimo 128 token in uscita. Prima di ogni blocco si eseguono tre richieste di riscaldamento escluse dai risultati.

Ogni modello riceve lo stesso testo di sistema, lo stesso contesto, la stessa domanda e lo stesso schema JSON. Tokenizzazione e template interni restano propri del modello e vanno dichiarati come limite.

Si produce una sola risposta per modello, condizione e domanda. Le 8.064 risposte della valutazione danno ampia copertura del dataset, ma non sono repliche stocastiche della stessa cella.

## Valutazione automatica

L'output ammesso è un oggetto JSON con la sola chiave `values`, contenente una lista di stringhe. Le stringhe vengono normalizzate in Unicode NFC e private dei soli spazi esterni. Maiuscole, minuscole e grafia restano significative; ordine e duplicati nella lista non contano.

Metriche principali, sempre separate:

- **Exact Match nella condizione sufficiente:** insieme previsto uguale all'insieme atteso.
- **Correct Abstention nella condizione insufficiente:** lista vuota.

Metriche secondarie:

- precisione e richiamo delle etichette nella condizione sufficiente;
- presenza di valori non supportati;
- confusione fra casi, quando un valore errato coincide con quello di un altro caso dello stesso episodio;
- errore di formato.

La confusione fra casi è rilevabile per 1.310 delle 2.016 domande di valutazione. Va riportata su questo denominatore, senza considerare le altre domande come assenza dimostrata di confusione.

I risultati vengono riportati per modello, condizione e famiglia di domanda. Sufficiente e insufficiente non vengono fusi in un unico punteggio; SC06 non viene mediato con SC01–SC05.

Il confronto fra modelli è appaiato perché entrambi rispondono agli stessi input. Si riporta la differenza assoluta in punti percentuali con intervallo al 95% ottenuto tramite bootstrap di 10.000 campioni, ricampionando interi episodi. Le nove domande dello stesso episodio non vengono trattate come repliche indipendenti. Non sono previsti p-value.

## Prestazioni locali

Tempo e velocità sono risultati secondari ed esplorativi. Per ogni risposta si conservano durate e conteggi restituiti da Ollama; si riassumono mediana, 95º percentile e token generati al secondo, escludendo il riscaldamento.

Dopo il caricamento di ogni modello si registra anche `size_vram` da Ollama. È un'allocazione dichiarata dal runtime, non una misura del picco di RAM del sistema, e deve essere descritta con questa limitazione.

## Tracciabilità e separazione degli artefatti

La configurazione eseguibile è in `data/rq3/config/rq5_sc06_v1.json` e contiene hash, prompt, schema, opzioni, digest dei modelli, metriche e gate di esecuzione.

Gli artefatti devono restare separati:

- richieste inviate ai modelli, prive di oracle;
- oracle con risposte attese e provenienza;
- risposte grezze e metadati Ollama;
- valutazione deterministica;
- riepilogo derivato.

Il runner deve poter riprendere un'esecuzione senza duplicare celle già complete. Ogni riga è identificata univocamente da split, modello, condizione e `question_id`. Errori e risposte non conformi vengono conservati, non corretti mediante un'altra chiamata.

## Cosa resta fuori dalla realizzazione iniziale

- confronto fra architetture di memoria o qualità del recupero;
- controllo `FULL_HISTORY` e condizioni RQ2;
- aggiornamento o obsolescenza delle informazioni;
- valutazione mediante un modello giudice;
- riscrittura libera delle etichette VERIS;
- inferenze su tutti i modelli Gemma, Llama o su tutti gli incidenti reali.

Queste esclusioni tengono RQ5 centrata sulla sola variabile scelta: il modello che genera la risposta a partire dallo stesso contesto.
