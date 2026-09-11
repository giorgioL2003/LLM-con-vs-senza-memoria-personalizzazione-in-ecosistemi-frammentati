# Prova reale di sviluppo — T come baseline su SC04 e SC05

**Eseguita l'8 settembre 2026.** 14 chiamate al modello, tutte di risposta,
nessun errore. Estensione della matrice descritta in `RQ2.md` §12;
impostazioni trascritte in `data/rq2/config/run_t_ext_sc04_sc05.json`
(`run_id: t-ext-sc04-sc05-1`).

Sono **risultati di sviluppo**: una sola esecuzione, sette domande per cella,
nessuna replica, annotazioni degli scenari in bozza, giudizi **non approvati**.
Non sono risultati dell'esperimento e non vanno riportati come tali. Il
protocollo resta **non congelato**.

## Che cosa è stato eseguito

| | |
|---|---|
| Celle nuove | SC04 × T (7 domande), SC05 × T (7 domande) |
| Chiamate | **14**, tutte di risposta; **0** di costruzione della memoria |
| Errori | 0 di esecuzione, 0 di parsing, 0 risposte vuote |
| Modello | `claude-sonnet-5` in tutte e 14, effort `medium`, nessun modello di ripiego |
| Configurazione | `rq2-dev-0.1`, estensione `matrice-estesa-0.1`, budget 200 token |
| Retrieval | 14 righe, 88–200 token, nessuna eccezione sul primo elemento |

**T non costruisce memoria.** Recupera i messaggi originali dello scenario: non
estrae fatti, non applica ADD/UPDATE/DELETE/NOOP, non costruisce grafi. Fatti,
stato di U, grafo e stato di GER non sono stati ricostruiti né toccati, e nessun
artefatto precedente è stato riscritto.

## File

| | |
|---|---|
| `retrieval_t_sc04.jsonl`, `retrieval_t_sc05.jsonl` | 7 righe ciascuno: selezione, classifica completa, token, arresto |
| `generation_inputs_t_sc04.jsonl`, `..._sc05.jsonl` | i prompt inviati, `model_answer` null |
| `generation_dev_t_sc04.jsonl`, `..._sc05.jsonl` | le 14 risposte, con modello ed effort registrati |
| `annotation_template_t_sc04.jsonl`, `..._sc05.jsonl` | template originali, giudizi `null`, **intatti** |
| `annotation_compilata_t_sc04.jsonl`, `..._sc05.jsonl` | copie compilate con i giudizi **proposti** |
| `valutazione_assistita_t.md` | motivazioni ed evidenze dei giudizi |
| `confronti_per_scenario.md` | i confronti dentro SC04 e dentro SC05 |

La verifica offline che precede questa prova, senza chiamate al modello, sta in
`results/rq2/t_ext_check/`.

## Esito in breve

| SC04 | completa | parziale | errata | astensione corretta | obsoleta | non supportata |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| **T** | **4** | 2 | 0 | 1 | 0 | 0 |
| U *(riportato)* | 2 | 4 | 0 | 1 | 0 | 0 |
| G *(riportato)* | 2 | 4 | 0 | 1 | 0 | 0 |
| FULL_HISTORY *(diagnostico, altra esecuzione)* | 5 | 1 | 0 | 1 | 0 | 1 |

| SC05 | completa | parziale | errata | astensione corretta | obsoleta | non supportata |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| **T** | **3** | 1 | 2 | 1 | **2** | 0 |
| U *(approvato)* | 2 | 2 | 2 | 1 | 0 | 2 |
| GER *(approvato)* | 1 | 3 | 2 | 1 | 0 | 2 |
| FULL_HISTORY *(diagnostico)* | 6 | 0 | 0 | 1 | 0 | 0 |

I giudizi di U, G, GER e FULL_HISTORY **non sono stati rivisti**: sono riportati
dagli artefatti esistenti e hanno stati di approvazione diversi (approvati su
SC05, assistiti su SC04, proposti per T).

## Le due osservazioni principali

**1. T usa informazione obsoleta, su SC05, due volte.** È il primo
`obsolete_used: true` del progetto. Su Q3 e Q4 T presenta la verifica del
registro del bilanciatore come ancora aperta: nel contesto entra `SC05-S8-U1`
(sessione 8, rango 2, punteggio 0,2034) e resta fuori `SC05-S9-U1` (sessione 9,
che la chiude, punteggio **0,0000**, rango 16). T non ha stato temporale: anche
se fossero entrati entrambi, nulla avrebbe detto quale dei due è superato. U e
GER non commettono questo errore perché la loro politica di lettura ammette le
voci superate solo nelle domande storiche.

**2. Il messaggio intero porta più contenuto della memoria frammentata.** Su
SC04-Q4 e Q5, T è completa dove U e G sono parziali: entrambe le risposte stanno
dentro il solo `SC04-S4-U1`, che T recupera intero, mentre in U e G quel messaggio
è spezzato in voci con punteggio TF-IDF 0,0. Su SC05-Q1 lo stesso: nel messaggio
originale il secondo obiettivo è dichiarato come obiettivo, in memoria era stato
sostituito dall'enunciato del suo compimento.

**È lo stesso fenomeno visto da due lati.** Non frammentare conserva contenuto e
massa lessicale ma rinuncia allo stato; frammentare e tenere lo stato protegge
dall'informazione superata ed espone al ranking. Il confronto **non stabilisce un
vincitore**: mostra un compromesso, su sette domande e una sola esecuzione.

## Decisioni aperte

Elencate in `valutazione_assistita_t.md` §7. In sintesi: se l'uso di informazione
obsoleta debba portare a `errata` per sé; come classificare una dichiarazione di
insufficienza su una domanda a cui il corpus permette di rispondere (questione
già aperta in `sc05_dev_v1/valutazione_approvata_sc05.md`); la soglia sul
punteggio nullo, che qui ha escluso il messaggio con la risposta corrente.
