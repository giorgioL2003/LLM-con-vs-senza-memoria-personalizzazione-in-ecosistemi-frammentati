# Stato complessivo del pilot

**Prima stesura:** 2026-08-29 (dry run manuali)

**Aggiornamento:** 2026-08-31 (pilot automatico eseguito e valutato)

**Stato:** pilot eseguito, misurato e analizzato; **non congelato**

**Prossimo passo:** confronto metodologico con il relatore

Questo documento conserva la storia del pilot in ordine cronologico. Le due fasi
non vanno confuse:

| Fase | Contesto fornito al modello | A cosa serviva |
|---|---|---|
| **Dry run manuali** (§3) | costruito a mano | validare benchmark e oracle |
| **Pilot automatico** (§4–§8) | costruito dal retriever | misurare la pipeline |

I numeri delle due fasi non sono confrontabili: nei dry run il retrieval non
esisteva ancora, quindi quei risultati dicono soltanto se le domande e l'oracle
erano formulati bene.

## 1. Materiale disponibile

Il pilot contiene:

- 2 scenari sintetici;
- 4 sessioni per scenario;
- 7 domande per scenario;
- 14 domande complessive;
- un oracle manuale per ogni domanda;
- una matrice di raggiungibilità per C0, C1 e C2;
- 42 esecuzioni di dry run manuale, una per ogni combinazione tra domanda e condizione;
- 42 esecuzioni di retrieval automatico su C0, C1 e C2;
- 56 risposte generate (14 domande × 4 modalità);
- 56 annotazioni di valutazione;
- le metriche aggregate delle tre condizioni;
- l'analisi causale dei due fallimenti.

Le modalità sono quattro perché oltre alle tre condizioni sperimentali C0, C1 e
C2 viene eseguito `FULL_HISTORY`, che riceve l'intero storico senza selezione.
`FULL_HISTORY` è un **controllo diagnostico**, non una quarta condizione: non
applica il retrieval e non entra nel confronto tra le condizioni.

## 2. Copertura teorica

| Condizione | Scenario 01 | Scenario 02 | Totale |
|---|---:|---:|---:|
| C0 — Nessuna memoria | 0/7 | 0/7 | 0/14 |
| C1 — Memoria locale | 2/7 | 3/7 | 5/14 |
| C2 — Memoria condivisa | 6/7 | 6/7 | 12/14 |

La differenza tra C1 e C2 è intenzionale: alcune informazioni sono presenti nell'ultima sessione, mentre altre richiedono di recuperare decisioni o regole stabilite in sessioni precedenti.

Questa matrice è stata decisa leggendo scenario e oracle, prima di eseguire
qualsiasi cosa, e non è stata modificata dopo aver visto i risultati.

## 3. Fase 1 — Dry run manuali (2026-08-29)

| Scenario | C0 | C1 | C2 | Totale appropriato |
|---|---:|---:|---:|---:|
| Scenario 01 | 7/7 | 6/7 | 7/7 | 20/21 |
| Scenario 02 | 7/7 | 6/7 | 6/7 | 19/21 |
| Totale | 14/14 | 12/14 | 13/14 | 39/42 |

Questi valori servono soltanto a validare il benchmark. I contesti sono stati forniti manualmente, quindi non è stato misurato il retrieval.

### Problemi emersi nei dry run

**Difetto del benchmark, corretto.** Nel primo scenario Q4 era stata considerata
non raggiungibile in C1, ma la Sessione 4 conteneva entrambe le verifiche
richieste. L'oracle e la matrice sono stati corretti durante il pilot, prima di
qualsiasi esecuzione automatica.

**Errori del modello, conservati.**

- Scenario 01, C1-Q1: il modello ha scambiato le verifiche pendenti per gli obiettivi iniziali.
- Scenario 02, C1-Q3: il modello ha indicato il test pendente invece di quello completato.
- Scenario 02, C2-Q3: lo stesso errore è comparso anche con il contesto completo.

Queste domande non sono state rese più facili, perché le evidenze sono chiare e gli errori appartengono alla fase di lettura o risposta del modello.

## 4. Fase 2 — Retrieval automatico

Il retrieval Turn-level RAG è stato eseguito su C0, C1 e C2 con gli stessi
parametri per tutte le condizioni: l'unica cosa che cambia è il perimetro dei
messaggi in cui è possibile cercare. Risultati per domanda in
`results/retrieval_pilot.jsonl` (42 righe).

## 5. Fase 3 — Generazione delle 56 risposte

I prompt sono stati costruiti da `scripts/build_generation_inputs.py`
(`results/generation_inputs.jsonl`) e le risposte generate con Claude Sonnet 5,
una chiamata indipendente per prova, senza che una risposta entri nel contesto
di quelle successive. Risposte in `results/generation_pilot.jsonl` (56 righe).

## 6. Fase 4 — Valutazione

Ogni risposta è stata confrontata con l'oracle e classificata come `complete`,
`partial`, `incorrect` o `correct_abstention`, con `obsolete_used` e
`unsupported_claim` registrati separatamente. Annotazioni in
`results/evaluation_pilot.jsonl`, criteri e casi da rivedere in
`pilot/evaluation_pilot.md`.

Le annotazioni sono una prima classificazione assistita dall'AI, approvata dallo
studente per i due casi a priorità alta.

## 7. Fase 5 — Metriche aggregate

Calcolate da `scripts/summarize_evaluation.py`; riepilogo completo con formule,
numeratori e denominatori in `pilot/metrics_pilot.md`.

| Metrica | C0 | C1 | C2 |
|---|---|---|---|
| Reachability Rate | 0.0% (0/14) | 35.7% (5/14) | 85.7% (12/14) |
| Retrieval Success Rate | null (0/0) | 100.0% (5/5) | 91.7% (11/12) |
| Complete Answer Rate | 0.0% (0/14) | 35.7% (5/14) | 78.6% (11/14) |
| Answer Success Rate | null (0/0) | 100.0% (5/5) | 100.0% (11/11) |
| Correct Abstention Rate | 100.0% (14/14) | 88.9% (8/9) | 100.0% (2/2) |
| Obsolete Information Use Rate | 0.0% | 0.0% | 0.0% |
| Unsupported Claim Rate | 0.0% | 7.1% (1/14) | 0.0% |

Quando il denominatore è zero la metrica non è calcolabile e vale `null`, mai
zero. `FULL_HISTORY` è riportato in una sezione diagnostica separata di
`pilot/metrics_pilot.md`, senza metriche di retrieval.

Questi numeri descrivono un pilot di 14 domande su 2 scenari: servono a
verificare che la pipeline misuri quello che deve misurare, non a sostenere
conclusioni finali.

## 8. Fase 6 — Analisi causale dei due fallimenti

Su 56 prove i fallimenti sono due, entrambi sulla stessa domanda. Ognuno è
ricondotto alla prima causa osservabile nella pipeline (EXPERIMENT.md, sezione
11). Tracce complete in `pilot/error_analysis_pilot.md` e
`results/error_analysis_pilot.jsonl`.

| Caso | Classe | Causa principale | Causa secondaria |
|---|---|---|---|
| SC02-Q6/C1 | `incorrect` | perimetro della memoria (`reachability`) | mancata astensione (`answer`) |
| SC02-Q6/C2 | `partial` | retrieval/ranking (`retrieval`) | nessuna |

**SC02-Q6/C1.** La regola dei 15 minuti è fissata in Sessione 2 e in C1 il
perimetro contiene la sola Sessione 4: l'evidenza non era accessibile. Il
modello avrebbe dovuto dichiarare il contesto insufficiente, ma ha risposto
reinterpretando il test pendente come una verifica della consegna dell'email e
del tempo di arrivo; da qui `unsupported_claim: true`.

**SC02-Q6/C2.** L'evidenza completa era accessibile, ma con `top_k=2` il
retrieval ha selezionato `SC02-S4-U1` e `SC02-S3-U1`, lasciando fuori
`SC02-S2-U1`, l'unico messaggio che enuncia il limite. La risposta riconosce il
collegamento con l'email consegnata in ritardo ma omette il rifiuto del link e
il limite numerico.

`FULL_HISTORY` è citato una sola volta, come controllo diagnostico di
SC02-Q6/C2: con tutta l'evidenza nel contesto la risposta è `complete`, quindi
quel fallimento è di retrieval e non di generazione.

## 9. Cosa è stato dimostrato finora

Il pilot mostra che:

- le condizioni C0, C1 e C2 producono perimetri di informazione realmente diversi;
- le domande distinguono informazioni locali, informazioni distribuite e informazioni assenti;
- l'oracle consente di separare un difetto del benchmark da un errore del modello;
- il protocollo è abbastanza chiaro da essere discusso;
- la pipeline sperimentale completa funziona ed è riproducibile;
- le metriche separano il perimetro della memoria, il retrieval e la generazione,
  e i due fallimenti osservati cadono effettivamente in due punti diversi della
  pipeline.

Il pilot **non** mostra la qualità generale di un retriever, non permette
conclusioni finali sull'efficacia della memoria condivisa e non ha una
dimensione sufficiente per un'analisi statistica: 14 domande, 2 scenari, un solo
modello, una sola esecuzione per prova.

## 10. Decisione dello step 4 (2026-08-31)

Controllo finale del pilot prima del confronto con il relatore. Registrato
esplicitamente:

1. **Nessun nuovo difetto rilevato nella versione corrente del benchmark o
   dell'oracle.** I due fallimenti dell'esecuzione automatica hanno
   `benchmark_defect: false`: SC02-Q6 ha evidenze chiare, risposta attesa
   univoca e raggiungibilità dichiarata correttamente. Sono errori del sistema,
   non della domanda.
2. **Nessuna correzione agli scenari.** Scenari, domande, oracle, evidenze e
   matrici di raggiungibilità restano invariati. Non è stato aggiunto uno
   Scenario 03.
3. **Nessuna modifica retroattiva dei risultati.** Non sono stati toccati
   `top_k`, retrieval, prompt, risposte generate, classificazioni né metriche.
   Gli errori sono conservati come risultati reali del pilot: renderli migliori
   dopo averli visti invaliderebbe l'esperimento.
4. **Pilot valutato ma non congelato.** La fase 9 della roadmap non è stata
   avviata: il protocollo può ancora cambiare.
5. **Prossimo passaggio: confronto con il relatore** (fase 5 della roadmap),
   sul disegno sperimentale e non sull'architettura software.

L'unico difetto del benchmark trovato nell'intero pilot resta quello dei dry run
(§3), corretto prima di qualsiasi esecuzione automatica.

Resta valida anche la decisione presa il 2026-08-29 di **non** aggiungere
automaticamente uno Scenario 03: i due scenari soddisfano il minimo previsto
dalla roadmap e coprono già i fenomeni principali. Un terzo scenario andrebbe
aggiunto soltanto se introducesse un caso metodologicamente diverso, oppure se
venisse richiesto durante il confronto con il relatore.

## 11. Cosa deve saper spiegare lo studente

- C0 non riceve informazioni precedenti.
- C1 vede soltanto l'ultima sessione.
- C2 vede tutte le sessioni dello scenario.
- `FULL_HISTORY` non è una condizione: è un controllo diagnostico che serve a
  distinguere un fallimento di retrieval da un fallimento di generazione.
- La raggiungibilità indica se il perimetro contiene le evidenze necessarie ed è
  una proprietà del benchmark, decisa prima di eseguire.
- Il retrieval indica se quelle evidenze finiscono davvero nel contesto, ed è una
  proprietà del sistema.
- Un'informazione raggiungibile può non essere recuperata; un'informazione
  recuperata può comunque essere letta o usata male dal modello.
- Perché una metrica con denominatore zero vale `null` e non zero.
- Il dry run usa contesti manuali e non valuta il retrieval; il pilot automatico
  sì.
- Il benchmark viene corretto soltanto quando domanda, evidenza o oracle sono
  difettosi, non ogni volta che il modello sbaglia.
