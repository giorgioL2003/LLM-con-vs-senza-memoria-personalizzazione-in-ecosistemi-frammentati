# Inventario delle prove e dei risultati

**Ricognizione del 17 settembre 2026.** Questo documento raccoglie ciò che esiste e ciò che manca. Non modifica valutazioni, non ricalcola metriche, non approva giudizi e non congela il protocollo. Le denominazioni degli scenari sono quelle descrittive scelte per la presentazione.

## 1. Quadro complessivo

| Gruppo | Risposte salvate | Stato |
|---|---:|---|
| Pilot automatico RQ1 | 56 | Valutazione strutturata, metriche e analisi degli errori presenti |
| Prove di sviluppo RQ2 ed estensioni | 119 | Comprendono prime versioni, prove corrette, GER e baseline T aggiuntive |
| Demo, smoke test e verifiche singole | 25 | Da conservare in appendice tecnica; non sono repliche di un protocollo finale |
| **Totale delle righe nei file di risposta** | **200** | **18 file JSONL; include FULL_HISTORY e riesecuzioni** |

Il totale è un conteggio dei materiali, non una misura di qualità né un campione di 200 domande indipendenti. Nessuna delle 200 righe riporta un errore di chiamata o una risposta vuota; questo non implica correttezza della risposta.

Separatamente, due rapporti documentano **42 celle di dry run manuale** (21 per scenario). Una prova preliminare su Q6 è documentata a parte: non la sommiamo alle 42 celle, perché occorre chiarire se le sue acquisizioni siano già incluse nel rapporto completo.

L'[inventario strutturato](/Users/giorgiolai/Desktop/progetto_tirocinio/RACCOLTA_RISULTATI/inventario.json) registra file, conteggi, modelli dichiarati nelle risposte, collegamenti agli input e alle valutazioni, e impronte SHA-256 di **206 artefatti sorgente**. Le impronte identificano i file letti, non attestano un'approvazione scientifica.

## 2. Regole per leggere la raccolta

- Ogni esecuzione resta identificata dal proprio file e dalla propria versione. Le vecchie versioni restano documentate accanto alle successive.
- `FULL_HISTORY` è un controllo diagnostico separato; in RQ2 è fuori dal budget di 200 token del conteggio locale.
- Un template con giudizi `null` è una scheda da compilare, non una valutazione conclusa.
- Le tabelle già presenti nei rapporti sono distinte da un calcolo completo e riproducibile delle metriche.
- Le copie in `tesi_anonimizzata/` sono presentazioni degli stessi risultati e non nuove esecuzioni. Quando una copia non esiste, il file originale può essere privo di nomi da sostituire: la cartella anonimizzata non è un duplicato completo del progetto.
- I dati calcolati sul testo originale (token, punteggi di retrieval, impronte) descrivono il testo dell'esecuzione originale, anche quando una copia editoriale mostra denominazioni diverse.
- Il protocollo risulta non congelato nei file ispezionati. I giudizi approvati dallo studente su SC05 non equivalgono all'approvazione del relatore.

## 3. Prove manuali iniziali

| Prova | Risposte e valutazione | Misure disponibili | Da completare |
|---|---|---|---|
| SC01, portale documentale, C0/C1/C2 | 21 celle nel [rapporto SC01](/Users/giorgiolai/Desktop/progetto_tirocinio/pilot/dry_run_scenario_01_results.md) | 20/21 comportamenti appropriati dopo la correzione dell'oracle | Presentare la correzione di Q4 e i limiti della raccolta manuale |
| SC02, servizio online, C0/C1/C2 | 21 celle nel [rapporto SC02](/Users/giorgiolai/Desktop/progetto_tirocinio/pilot/dry_run_scenario_02_results.md) | 19/21 comportamenti appropriati | Riportare i due errori su Q3 e distinguere correttezza da rispetto del formato |
| SC01-Q6, prova preliminare | Tre condizioni nel [rapporto Q6](/Users/giorgiolai/Desktop/progetto_tirocinio/pilot/dry_run_q6_results.md) | Esito delle tre risposte | Chiarire eventuale sovrapposizione con il dry run completo; nessun conteggio aggiuntivo per ora |

I rapporti dichiarano Claude Opus 5, impostazione Alto, mostrato nell'interfaccia. Il contesto era fornito manualmente: queste prove non misurano il retrieval automatico. Fonte complessiva: [storia del pilot](/Users/giorgiolai/Desktop/progetto_tirocinio/pilot/pilot_summary.md).

## 4. Pilot automatico RQ1

**Obiettivo:** effetto del perimetro accessibile, confrontando C0, C1 e C2 su SC01 e SC02. Modello registrato: `claude-sonnet-5`, effort `medium`. Retrieval TF-IDF/coseno, top-k 2; il budget RQ2 di 200 token non va attribuito retroattivamente al pilot.

| Materiale | Fonte | Stato |
|---|---|---|
| 56 risposte | [generation_pilot.jsonl](/Users/giorgiolai/Desktop/progetto_tirocinio/results/generation_pilot.jsonl) | 28 per scenario, 7 per modalità e scenario |
| Contesti e prompt | [generation_inputs.jsonl](/Users/giorgiolai/Desktop/progetto_tirocinio/results/generation_inputs.jsonl) | Presenti |
| 42 tracce di retrieval | [retrieval_pilot.jsonl](/Users/giorgiolai/Desktop/progetto_tirocinio/results/retrieval_pilot.jsonl) | C0/C1/C2; FULL_HISTORY non ha retrieval |
| 56 valutazioni | [evaluation_pilot.jsonl](/Users/giorgiolai/Desktop/progetto_tirocinio/results/evaluation_pilot.jsonl) | Compilate; documentate come classificazione assistita |
| Metriche | [metrics_pilot.json](/Users/giorgiolai/Desktop/progetto_tirocinio/results/metrics_pilot.json), [rapporto](/Users/giorgiolai/Desktop/progetto_tirocinio/pilot/metrics_pilot.md) | Già disponibili, aggregate sui due scenari |
| Analisi degli errori | [rapporto causale](/Users/giorgiolai/Desktop/progetto_tirocinio/pilot/error_analysis_pilot.md) | Due fallimenti analizzati |

Risposte complete già riportate: C0 0/14, C1 5/14, C2 11/14; FULL_HISTORY 12/14, separato. C0 ha 14/14 astensioni corrette.

**Da completare nella raccolta:** aggiungere la vista distinta SC01/SC02 mantenendo anche l'aggregazione RQ1; chiarire lo stato di approvazione. Il documento [evaluation_pilot.md](/Users/giorgiolai/Desktop/progetto_tirocinio/pilot/evaluation_pilot.md) contiene ancora la dicitura «da approvare», mentre le metriche successive esistono già. Non si deduce automaticamente un'approvazione dalla presenza delle metriche.

## 5. RQ2: inventario per scenario e versione

Le 119 risposte di questa sezione sono prove di sviluppo, non una nuova campagna finale. Tutti i file di risposta censiti registrano `claude-sonnet-5`, effort `medium`.

| Scenario e versione | Modalità e risposte | Valutazioni disponibili | Metriche e conteggi disponibili | Lavoro mancante |
|---|---|---|---|---|
| SC01, portale documentale | T e FULL_HISTORY: **0/14 previste** | Annotazioni del benchmark presenti | Nessun risultato RQ2 | Decidere se mantenere questa riga nel protocollo finale ed eventualmente eseguirla |
| SC02, servizio online | T/F/FULL_HISTORY: **21** | Template con giudizi null; osservazioni qualitative in RQ2.md | Descrizioni di contenuto/overhead, non riepilogo completo delle metriche | Compilare e verificare tutte le valutazioni; aggregare |
| SC03, impresa logistica, prima versione | F/U/FULL_HISTORY: **21** | Template con giudizi null; analisi delle operazioni e dei fallimenti | Diagnostica della memoria e del retrieval | Conservare lo storico; formalizzare i giudizi delle risposte |
| SC03, U corretto, istruzioni 0.3 | U: **7** | Confronto qualitativo domanda per domanda nel README | Differenze rispetto alla prima U; nessun riepilogo completo | Completare la valutazione strutturata e dichiarare le fonti di F/FULL_HISTORY riutilizzate |
| SC04, azienda committente, prima versione | U/G/FULL_HISTORY: **21** | Valutazione assistita in Markdown; template JSONL non compilato | Conteggi e diagnosi nel rapporto | Conservare lo storico; rendere espliciti i criteri ambigui, soprattutto Q2 |
| SC04, U/G corretti, istruzioni 0.3 | U/G: **14** | Cambiamenti documentati; giudizi riportati nel confronto con T | Conteggi per classe nel confronto, non suite completa delle metriche | Consolidare una tabella strutturata e controllare i giudizi riportati |
| SC04, baseline T aggiunta | T: **7** | Annotazioni compilate, **proposte e non approvate** | Conteggi per classe e indicatori nel rapporto | Revisione dei giudizi e aggregazione uniforme |
| SC05, società di mobilità, prova GER | U/GER/FULL_HISTORY: **21** | Annotazioni compilate, **approvate dallo studente** per questa prova | Conteggi per classe e indicatori già presenti | Calcolare/documentare le metriche applicabili dalle annotazioni |
| SC05, baseline T aggiunta | T: **7** | Annotazioni compilate, **proposte e non approvate** | Conteggi per classe e indicatori nel rapporto | Revisione dei giudizi e aggregazione uniforme |

### File delle risposte

| Prova | File |
|---|---|
| SC02 | [21 risposte](/Users/giorgiolai/Desktop/progetto_tirocinio/results/rq2/generation_dev_sc02.jsonl) |
| SC03, prima versione | [21 risposte](/Users/giorgiolai/Desktop/progetto_tirocinio/results/rq2/generation_dev_sc03.jsonl) |
| SC03, U corretto | [7 risposte](/Users/giorgiolai/Desktop/progetto_tirocinio/results/rq2/retrieval_repair_v3/generation_dev_sc03_u.jsonl) |
| SC04, prima versione | [21 risposte](/Users/giorgiolai/Desktop/progetto_tirocinio/results/rq2/generation_dev_sc04.jsonl) |
| SC04, U/G corretti | [14 risposte](/Users/giorgiolai/Desktop/progetto_tirocinio/results/rq2/sc04_repair_v3/generation_dev_sc04_ug.jsonl) |
| SC04, T | [7 risposte](/Users/giorgiolai/Desktop/progetto_tirocinio/results/rq2/t_ext_v1/generation_dev_t_sc04.jsonl) |
| SC05, U/GER/FULL_HISTORY | [21 risposte](/Users/giorgiolai/Desktop/progetto_tirocinio/results/rq2/sc05_dev_v1/generation_dev_sc05.jsonl) |
| SC05, T | [7 risposte](/Users/giorgiolai/Desktop/progetto_tirocinio/results/rq2/t_ext_v1/generation_dev_t_sc05.jsonl) |

### Come comporre le viste di confronto senza duplicare le prove

- **SC02:** le 21 risposte della prima prova formano un unico confronto T/F/FULL_HISTORY.
- **SC03:** per una vista sull'ultima U disponibile, affiancare le 7 risposte U corrette alle sole righe F e FULL_HISTORY della prima prova. Le prime 7 risposte U restano in una vista storica separata. Il riuso e le diverse esecuzioni vanno dichiarati.
- **SC04:** affiancare T aggiunta a U/G corretti. Il controllo FULL_HISTORY proviene dalla prima esecuzione, poiché non è stato rigenerato nella correzione; va segnalato nella tabella. Le prime U/G rimangono nella storia dello sviluppo.
- **SC05:** affiancare T aggiunta alla prova U/GER/FULL_HISTORY. Le esecuzioni sono distinte e gli stati di approvazione diversi; le 21 valutazioni approvate non approvano automaticamente le 7 di T.

Queste sono viste di sviluppo per organizzare la raccolta, non una dichiarazione che il protocollo finale sia già definito. Fonti: [RQ2](/Users/giorgiolai/Desktop/progetto_tirocinio/RQ2.md), [correzione SC03](/Users/giorgiolai/Desktop/progetto_tirocinio/results/rq2/retrieval_repair_v3/README.md), [correzione SC04](/Users/giorgiolai/Desktop/progetto_tirocinio/results/rq2/sc04_repair_v3/README.md), [confronti SC04/SC05](/Users/giorgiolai/Desktop/progetto_tirocinio/results/rq2/t_ext_v1/confronti_per_scenario.md).

## 6. Demo e verifiche singole: appendice separata

| Materiale | Risposte | Ruolo |
|---|---:|---|
| [Smoke test](/Users/giorgiolai/Desktop/progetto_tirocinio/results/generation_smoke_test.jsonl) | 4 | Verifica iniziale del generatore |
| [SC02-Q6/C2](/Users/giorgiolai/Desktop/progetto_tirocinio/results/prova_manuale_01/risposta_sc02_q6_c2.jsonl) | 1 | Prova singola |
| [SC05-Q2, prova 1](/Users/giorgiolai/Desktop/progetto_tirocinio/results/prova_manuale_01/risposte_sc05_q2_confronto.jsonl) | 3 | U/GER/FULL_HISTORY |
| [SC05-Q2, prova 2](/Users/giorgiolai/Desktop/progetto_tirocinio/results/prova_manuale_02/risposte_sc05_q2_confronto.jsonl) | 3 | U/GER/FULL_HISTORY |
| [Demo professore 1](/Users/giorgiolai/Desktop/progetto_tirocinio/results/demo_professore_01/sc05_risposte.jsonl) | 3 | SC05 U/GER/FULL_HISTORY |
| [Demo professore 2](/Users/giorgiolai/Desktop/progetto_tirocinio/results/demo_professore_02/sc05_risposte.jsonl) | 3 | SC05 U/GER/FULL_HISTORY |
| [Demo con T](/Users/giorgiolai/Desktop/progetto_tirocinio/results/demo_professore_t_01/sc05_risposte.jsonl) | 4 | SC05 T/U/GER/FULL_HISTORY |
| [Demo SC03](/Users/giorgiolai/Desktop/progetto_tirocinio/results/demo_scenari_01/sc03_f_full.jsonl) | 2 | F/FULL_HISTORY |
| [Demo SC04](/Users/giorgiolai/Desktop/progetto_tirocinio/results/demo_scenari_01/sc04.jsonl) | 2 | U/G |

Non sono state individuate schede formali di valutazione associate a queste prove. La ripetizione della stessa domanda in una demo non costituisce, da sola, un piano di repliche sperimentali.

## 7. Costruzione della memoria e controlli offline

Le chiamate di estrazione, aggiornamento e costruzione del grafo **non sono comprese nelle 200 risposte alle domande**. I loro artefatti sono censiti separatamente nell'inventario strutturato:

- `results/rq2/facts/`, `memory/`, `graph/`: prima costruzione di F, U e G;
- `results/rq2/memory_repair_v2/` e `memory_repair_v3/`: revisioni della gestione U su SC03; v2 è una versione intermedia;
- `results/rq2/sc04_repair_v3/`: U/G ricostruiti su SC04;
- `results/rq2/sc05_dev_v1/facts/` e `memory/`: memoria reale della prova SC05.

I file in `results/rq2/offline_check/`, `ger_dev/`, `ger_dev_v2/` e `t_ext_check/` documentano controlli tecnici, retrieval e prompt. Le fixture in `tests/fixtures/rq2/` sono dati predisposti per verificare il codice: non sono nuove risposte sperimentali del modello.

I prompt in `generation_inputs*.jsonl` non sono risposte generate, anche quando contengono un campo `model_answer` vuoto. Gli `annotation_template*.jsonl` non vanno sommati alle copie compilate.

## 8. Cosa manca prima delle tabelle definitive

1. **Rendere espliciti gli stati di approvazione.** Pilot: stato documentale da chiarire; SC04: giudizi assistiti; T aggiunta: giudizi proposti; SC05 U/GER/FULL_HISTORY: approvazione dello studente già registrata.
2. **Completare i giudizi strutturati di SC02 e SC03 e consolidare SC04.** Un riepilogo automatico deve partire da righe valutate, non dedurre giudizi dai template vuoti.
3. **Chiarire le ambiguità dei criteri senza riscrivere le prove precedenti.** Esempi da sottoporre a revisione: criteri alternativi per SC04-Q2; SC05-Q4/T classificata parziale ma con `obsolete_used: true`, mentre la definizione iniziale del pilot include l'uso di informazioni obsolete fra le risposte errate. Conservare il giudizio proposto e documentare la regola scelta prima del riepilogo definitivo.
4. **Verificare le evidenze sul contenuto.** Nei fatti estratti e nei grafi la corrispondenza degli identificatori di provenienza non dimostra che il contenuto richiesto sia stato conservato o recuperato.
5. **Preparare le metriche RQ2.** Riportare classi, uso di obsoleto, affermazioni non supportate, recupero dell'evidenza e cause d'errore. Misure di estrazione, aggiornamento e grafo richiedono i rispettivi giudizi; i valori mancanti restano non disponibili, non zero.
6. **Preparare le tabelle per scenario e versione.** Nessuna classifica generale ottenuta mescolando scenari, demo e versioni di sviluppo; FULL_HISTORY rimane separato.

## 9. Esperimenti progettati, senza risultati da raccogliere

| Esperimento | Stato e decisioni necessarie |
|---|---|
| Passaggio tra assistenti su SC02 e SC03 | Proposto con Gemma e Llama locali per le risposte. Definire punto del passaggio, memoria trasferita, ruolo degli output del primo assistente e condizioni di confronto. Non è la semplice ripetizione indipendente delle stesse domande con due modelli. |
| SC05 allungato con informazioni secondarie | Definire varianti di lunghezza, mantenimento dei fatti decisivi, domande, modello e budget; poi costruire ed eseguire. |

Queste due righe descrivono il piano discusso il 17 settembre, non implementazioni o risultati già verificati.

## 10. Prossimo passo operativo

Completare una prima sezione della raccolta con il **pilot RQ1**, perché dispone già di risposte, giudizi, metriche e analisi degli errori. Procedere poi con SC02, SC03, SC04 e SC05, usando questo inventario per mostrare ciò che manca.

Il file `src/risultati.tex` resta per ora il documento da compilare nelle fasi successive. Questo inventario non sostituisce la valutazione delle singole risposte e non introduce nuovi risultati scientifici.
