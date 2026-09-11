# Verifica offline dell'estensione T — SC04 e SC05

**Non sono risultati sperimentali.** Nessun modello è stato chiamato: nessuna
risposta è stata generata. Qui ci sono soltanto il retrieval di T, i prompt
costruiti e mai inviati, la scheda di annotazione vuota e il riepilogo di
compatibilità. Nessuna prova precedente è stata toccata: lo script lo verifica
per impronta a ogni esecuzione (passo 7).

Comando (scrive qui per impostazione predefinita):

```bash
python3 scripts/rq2/run_t_extension_check.py
```

## Che cosa aggiunge l'estensione

Turn-level RAG (T) come **baseline anche in SC04 e SC05**, per confrontare le
strategie di memoria dentro lo stesso scenario:

| Scenario | A parità di budget | Controllo diagnostico | Nuovo qui |
|---|---|---|---|
| SC01 | T | FULL_HISTORY | – |
| SC02 | T / F | FULL_HISTORY | – |
| SC03 | F / U | FULL_HISTORY | – |
| SC04 | **T** / U / G | FULL_HISTORY | **T** |
| SC05 | **T** / U / GER | FULL_HISTORY | **T** |

La matrice originale (`matrix` in `experiment_rq2.json`, 77 celle) **non
cambia**: l'estensione vive nel blocco `matrix_extension`, accanto e non al
posto. SC05 resta fuori da `SCENARIO_IDS` e dal conteggio delle 77 celle. Il
dettaglio è nella sezione 12 di `RQ2.md`.

## Input e configurazione

| | |
|---|---|
| configurazione | `rq2-dev-0.1`, estensione `matrice-estesa-0.1` |
| budget | 200 token sul contesto formattato |
| ranking | TF-IDF / coseno, parità per ordine di comparsa |
| soglia sul punteggio nullo, garanzia minima, troncamento | invariati |
| unità di T | messaggio originale dell'utente |
| istruzioni del prompt | `473799a0ff4a6ab1`, le stesse del pilot e di tutte le prove precedenti |
| perimetro | tutti i messaggi con ruolo `user`, tutte le sessioni |
| memoria costruita per l'estensione | **nessuna**: T non estrae fatti, non aggiorna, non costruisce grafi |

Il perimetro è stato verificato (passo 2): SC04 ha 4 sessioni e 7 messaggi
utente, con lo stato di U che arriva alla sessione 4; SC05 ha 9 sessioni e 16
messaggi utente, con lo stato di U che arriva alla sessione 9. Se uno stato si
fermasse a una sessione intermedia lo script lo segnalerebbe come errore: T
vedrebbe messaggi che le altre modalità non hanno mai visto.

## Che cosa recupera T (retrieval, non risposte)

Le prime due righe sono nuove; le altre vengono dalle prove già salvate e sono
riportate per contesto. Sono numeri di **retrieval**: dicono che cosa entra nel
contesto, non se la risposta sarà corretta.

| | prove | elementi | contenuto | overhead | max token | provenienza completa |
|---|---:|---:|---:|---:|---:|:-:|
| SC04 T | 7 | 1,6 | 125,1 | 11,0 | 184 | 4/6 |
| SC04 U | 7 | 5,4 | 101,1 | 81,4 | 194 | 5/6 |
| SC04 G | 7 | 6,1 | 74,4 | 105,0 | 199 | 5/6 |
| SC05 T | 7 | 3,7 | 147,7 | 26,0 | 200 | 3/6 |
| SC05 U | 7 | 5,6 | 94,3 | 83,6 | 199 | 3/6 |
| SC05 GER | 7 | 5,6 | 88,6 | 94,7 | 197 | 3/6 |

Budget rispettato in tutte e 14 le prove nuove, **nessuna eccezione sul primo
elemento**. Si vede la differenza che l'estensione serve a misurare: a parità di
200 token T porta pochi elementi ma quasi solo contenuto (11 e 26 token di
overhead), mentre U, G e GER pagano identificatori, provenienza, stato e
relazioni (81–105 token). Quale delle due cose serva alla risposta è esattamente
la domanda aperta.

**La copertura di provenienza non è una misura di correttezza.** Dice solo che
nel contesto c'è un elemento che dichiara di venire dai messaggi giusti: un
elemento può citare il messaggio sorgente e dire un'altra cosa (il falso
positivo già osservato in `RQ2.md`, sezione 9.4). I giudizi vanno letti a mano.

## Che cosa è riusabile accanto a T

T non dipende da fatti, stato di U o grafo: dipende solo dai messaggi dello
scenario, dalla domanda, dal ranking e dal budget. Le risposte già generate
restano valide e **non vanno rieseguite**.

| Scenario | Prova | Uso |
|---|---|---|
| SC04 | `sc04_repair_v3/generation_dev_sc04_ug.jsonl` (U, G) | riusabile: stessa configurazione |
| SC04 | `generation_dev_sc04.jsonl` (FULL_HISTORY) | riusabile **con avvertenza**: altra esecuzione |
| SC04 | `generation_dev_sc04.jsonl` (U, G) | **non riusabile** nella stessa tabella |
| SC05 | `sc05_dev_v1/generation_dev_sc05.jsonl` (U, GER, FULL_HISTORY) | riusabile: stessa configurazione |

**L'incompatibilità segnalata riguarda SC04.** Nella riparazione descritta in
`RQ2.md` 9.6 FULL_HISTORY non è stato rigenerato: viene dalla prova iniziale
(9.3). Non è un'incompatibilità di configurazione — stesso prompt, stesso
modello, e FULL_HISTORY non dipende dallo stato di U — ma è un'altra esecuzione e
nella tabella di SC04 va indicata come tale. Le risposte U e G della prova
iniziale, invece, **non** vanno messe accanto a quelle della riparazione: le
istruzioni di U e lo stato risultante sono diversi.

## File

| | |
|---|---|
| `retrieval_t.jsonl` | 14 righe: 7 domande × T, per SC04 e SC05 |
| `generation_inputs_t.jsonl` | 14 prompt, `model_answer` sempre `null` |
| `annotation_template_t.jsonl` | scheda di valutazione, tutti i giudizi `null` |
| `compatibilita.json` | riepilogo di che cosa è riusabile, con gli avvisi |

## Prima della prova reale

Impostazioni trascritte in `data/rq2/config/run_t_ext_sc04_sc05.json`
(`executed: false`, autorizzazione in attesa). Sono **14 chiamate**, tutte di
risposta, e le uscite vanno in `results/rq2/t_ext_v1/`, cartella nuova. I comandi
esatti sono nella sezione 12 di `RQ2.md`.

Restano aperti i punti già dichiarati: annotazioni di SC04 e SC05 in bozza, una
sola esecuzione senza repliche, sette domande per scenario. Il confronto vale
**dentro lo scenario**: non è una classifica generale delle architetture, e i
risultati di T su SC04 e su SC05 non vanno sommati o mediati fra loro.
