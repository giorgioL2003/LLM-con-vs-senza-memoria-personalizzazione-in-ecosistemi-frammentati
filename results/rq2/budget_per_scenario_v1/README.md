# Preparazione — budget specifico per scenario (`budget-per-scenario-v1`)

**19 settembre 2026.** Questa parte del documento descrive la **preparazione
offline**: il retrieval ricostruito e i prompt. Le 49 risposte sono state
generate in un secondo momento, su autorizzazione esplicita: valutazioni,
riepiloghi e confronto sulle risposte stanno in
[`README_valutazione.md`](README_valutazione.md).

**Questi numeri non appartengono alle prove storiche e non le correggono.** Le
prove eseguite con `rq2-dev-0.1` restano dove sono, intatte, con i loro giudizi
e i loro stati di approvazione. Questa è una prova diversa, con una
configurazione diversa: i due gruppi non vanno messi nella stessa tabella.

## 1. Che cosa cambia

| | |
|---|---|
| Configurazione | `rq2-dev-0.2-budget-per-scenario` ([file](/Users/giorgiolai/Desktop/progetto_tirocinio/data/rq2/config/experiment_rq2_budget_per_scenario.json)) |
| Derivata da | `rq2-dev-0.1`, **non modificata** (impronta invariata) |
| Unica differenza | il budget del contesto diventa specifico per scenario |
| SC02, SC03, SC04 | **nessun tetto sperimentale** |
| SC05 | **200 token**, come prima |
| Scheda della prova | [`run_budget_per_scenario_v1.json`](/Users/giorgiolai/Desktop/progetto_tirocinio/data/rq2/config/run_budget_per_scenario_v1.json) |

**Che cosa significa «nessun tetto».** Cade solo il passo 4 della regola di
selezione, il riempimento. Tutto il resto resta identico: ranking TF-IDF,
parità risolta dall'ordine dello scenario, **soglia sul punteggio nullo**,
nessun troncamento, e le regole proprie di ogni architettura — la politica di
lettura corrente/storia di U, i percorsi e gli archi ammessi di G. La selezione
è ancora un prefisso del ranking. **Non è FULL_HISTORY e non sostituisce il
retrieval:** gli elementi senza alcun termine in comune con la domanda restano
fuori, e restano fuori anche gli archi che le regole di G non ammettono.

**Perché SC05 tiene il tetto.** GER *è* la ripartizione del budget fra memoria
recente e archivio. Toglierlo non allargherebbe il contesto: cancellerebbe
l'architettura in esame. Il retrieval di SC05 è quindi rimasto identico, ed è
stato usato come controllo della modifica (vedi §4).

Modello, effort, istruzioni, prompt comune, perimetro della memoria e
isolamento sono quelli di sempre: `claude-sonnet-5`, effort `medium`.

## 2. Da dove arriva la memoria

Conversazioni, domande, fatti, stati e grafi sono **riusati** dalle prove
attuali, nelle versioni dichiarate in [INVENTARIO](/Users/giorgiolai/Desktop/progetto_tirocinio/RACCOLTA_RISULTATI/INVENTARIO.md) §5. Niente è stato riestratto
né ricostruito: **0 chiamate di costruzione della memoria.**

| Scenario | Modalità | Fatti | Stato di U | Grafo |
|---|---|---|---|---|
| SC02 | T, F, FULL_HISTORY | `results/rq2/facts/scenario_02_facts.jsonl` | — | — |
| SC03 | F, U, FULL_HISTORY | `results/rq2/facts/scenario_03_facts.jsonl` | `memory_repair_v3/` (**versione corretta**) | — |
| SC04 | T, U, G, FULL_HISTORY | `results/rq2/facts/scenario_04_facts.jsonl` | `sc04_repair_v3/` (**versione corretta**) | `sc04_repair_v3/` (**versione corretta**) |
| SC05 | T, U, GER, FULL_HISTORY | `sc05_dev_v1/facts/` | `sc05_dev_v1/memory/` (sessione raggiunta: 9) | — |

T su SC04 e SC05 è la riga dell'**estensione T** (`matrice-estesa-0.1`), non una
riga della matrice originale. SC01 resta fuori: non ha prove reali.

## 3. Che cosa è cambiato nel contesto

Medie sulle sette domande di ogni cella. «Aggiunti» conta gli elementi entrati
in più e i messaggi sorgente che prima non comparivano nel contesto.

| Scenario | Arch. | Budget | Token prima → dopo | Elementi prima → dopo | Aggiunti | Contesti cambiati |
|---|:-:|---|---|---|---|:-:|
| SC02 | T | nessun tetto | 160 → **296** | 2,0 → 3,7 | 12 el. / 12 msg | **6/7** |
| SC02 | F | nessun tetto | 186 → **401** | 6,4 → 13,9 | 52 el. / 4 msg | **5/7** |
| SC03 | F | nessun tetto | 190 → **701** | 7,6 → 27,0 | 136 el. / 23 msg | **7/7** |
| SC03 | U | nessun tetto | 185 → **593** | 6,6 → 20,3 | 96 el. / 17 msg | **7/7** |
| SC04 | T | nessun tetto | 136 → **495** | 1,6 → 6,4 | 34 el. / 34 msg | **7/7** |
| SC04 | U | nessun tetto | 183 → **690** | 5,4 → 21,0 | 109 el. / 20 msg | **7/7** |
| SC04 | G | nessun tetto | 179 → **812** | 6,1 → 25,7 | 137 el. / 20 msg | **7/7** |
| SC05 | T | 200 token | 174 → 174 | 3,7 → 3,7 | 0 | 0/7 |
| SC05 | U | 200 token | 178 → 178 | 5,6 → 5,6 | 0 | 0/7 |
| SC05 | GER | 200 token | 183 → 183 | 5,6 → 5,6 | 0 | 0/7 |

**Nessun elemento è stato perso**: senza tetto il prefisso del ranking può solo
allungarsi, e in nessuna cella compaiono elementi presenti prima e assenti ora.

Copertura dell'evidenza **per provenienza** (non misura il contenuto: dice solo
che il messaggio sorgente è nel contesto, non che l'informazione sia stata
conservata correttamente):

| | SC02-T | SC02-F | SC03-F | SC03-U | SC04-T | SC04-U | SC04-G |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| prima | 5/6 | 5/6 | 6/6 | 6/6 | 4/6 | 5/6 | 5/6 |
| dopo | **6/6** | **6/6** | 6/6 | 6/6 | **6/6** | **6/6** | **6/6** |

Le quattro lacune di provenienza di SC02-Q6, SC04-Q2 e SC04-Q3 erano dovute allo
spazio. Su SC03 la provenienza era già completa prima e non poteva salire —
**il che non significa che non entri nuova evidenza**: la provenienza conta i
messaggi sorgente citati, non i fatti leggibili nel testo. La verifica sul
contenuto, fatta in sede di valutazione, mostra che su SC03 entrano **+5 fatti
richiesti in F e +7 in U** a provenienza invariata. Il conto è in
[`README_valutazione.md`](README_valutazione.md).

Su SC05 il tetto resta e non cambia nulla: 0 contesti modificati.

## 4. Controlli

| Controllo | Esito |
|---|---|
| `data/rq2/config/experiment_rq2.json` non modificata | impronta `df4b066a…` invariata, quella registrata in `RACCOLTA_RISULTATI` |
| SC05 riproduce il retrieval già eseguito | **21 righe su 21** identiche per elementi e token |
| SC05 riproduce i prompt già inviati | **28 prompt su 28** identici carattere per carattere |
| Nessun artefatto precedente riscritto | tutte le uscite stanno in questa cartella |
| Nessun oracle nei prompt | controlli di `build_generation_inputs_rq2.py` superati sui quattro scenari |
| SC02/SC03/SC04: FULL_HISTORY invariato | **21 prompt su 21** identici allo storico: il controllo diagnostico non va rigenerato |
| Nessuna risposta generata | `model_answer` null in tutte le righe |
| Validatore sulla nuova configurazione | superato |
| Suite dei test | 416 test, nessun fallimento |

Il controllo su SC05 è il più importante: **dove il budget non cambia, la
modifica al codice non cambia assolutamente nulla.**

## 5. Dove togliere il tetto cambia il comportamento, non solo la quantità

Queste non sono conclusioni sui risultati — non ci sono ancora risposte. Sono
osservazioni sul **retrieval**, da decidere prima di generare.

**1. In scenari corti il retrieval di T smette di escludere.** Su SC02 in
**6 prove su 7**, su SC04 in **5 prove su 7**, il ranking di T arriva a
includere tutti i messaggi utente dello scenario. Il retrieval viene eseguito
comunque — ranking, soglia di pertinenza e regola di arresto sono quelli di
sempre — ma in quelle prove non lascia fuori nulla. Il contenuto coincide allora
con quello di FULL_HISTORY; **l'ordine no**: T presenta i messaggi in ordine di
punteggio, FULL_HISTORY in ordine cronologico. Il confronto fra le due resta
quindi definito, ma in quelle prove misura l'effetto dell'ordine, non quello
della selezione. È l'effetto di scenari corti: 4 messaggi in SC02, 7 in SC04.

**2. L'overhead strutturale smette di essere la variabile misurata.** I
confronti T/F, F/U e U/G di `rq2-dev-0.1` misuravano proprio il costo di
identificatori, provenienza e stato: a parità di spazio, un fatto costa ~13
token di overhead, una voce di U ~15, un arco di G ~20, e questo limitava
quanti elementi entravano. Senza tetto l'overhead si paga ma non esclude più
nulla. Il contesto cresce fino a ×4,5 (SC04-G, 179 → 812 token). **Il confronto
non è più "a parità di spazio" ma "a parità di pertinenza", e va dichiarato
così.**

**3. Per G non resta nessun criterio di esclusione basato sul ranking.** In
tutte e 7 le domande di SC04, gli elementi selezionati coincidono con l'intera
classifica: la soglia sul punteggio nullo non scarta nulla, perché G assegna un
punteggio positivo a ogni elemento che le sue regole producono. Le regole
relazionali però tengono: da 7 a 14 archi restano fuori in ogni domanda perché
non incidenti a un nodo iniziale o non leggibili con lo stato della domanda.
**G non diventa "tutto il grafo".**

**4. Il tetto non stava nascondendo i limiti relazionali di G.** I percorsi
topologici trovati erano già completi nel contesto prima della modifica (3 su 3
in Q3, 1 su 1 in Q5 e Q7) e restano gli stessi. Quello che cresce sono gli archi
periferici: da 3 a 9 in Q3. **Il collo di bottiglia di G era l'ancoraggio ai
nodi, non lo spazio, e togliere il tetto non lo ripara.**

**5. Dove si fermava già la pertinenza, non cambia niente.** SC02-Q4 in T,
SC02-Q3 e SC02-Q4 in F hanno esattamente lo stesso contesto di prima: lì il
budget non escludeva nulla. Con il tetto tolto la soglia sul punteggio nullo
resta l'unico criterio di esclusione, e i casi in cui escludeva già un elemento
decisivo restano identici — per esempio `SC05-S9-U1` in T, punteggio 0,0000,
che chiude la verifica presentata come aperta in SC05-Q3 e Q4. **Quel problema
non è un problema di budget e questa modifica non lo tocca.**

La generazione ha poi mostrato quanto questo pesi: nelle risposte di SC03 e SC04
i fatti che continuano a mancare nel contesto hanno tutti punteggio **0,0000**
— la famiglia Kelpie, l'isolamento delle 09:40, la verifica degli accessi cloud,
il vettore iniziale, l'assenza di cifratura, la rimozione di RULE-01, il reset
della password. Sono nella memoria, sono attivi, e restano fuori perché non
condividono parole con la domanda. Il dettaglio è in `README_valutazione.md`.

## 6. File

| File | Contenuto |
|---|---|
| `retrieval_sc02.jsonl` … `retrieval_sc05.jsonl` | selezione, classifica completa, token, motivo dell'arresto |
| `generation_inputs_sc02.jsonl` … `_sc05.jsonl` | i prompt pronti, `model_answer` null |
| `confronto_budget.csv` | il riepilogo della §3, una riga per cella |
| `confronto_budget.json` | il confronto completo, domanda per domanda, con le segnalazioni |

Ricostruibili con i comandi trascritti in
[`run_budget_per_scenario_v1.json`](/Users/giorgiolai/Desktop/progetto_tirocinio/data/rq2/config/run_budget_per_scenario_v1.json).
Il confronto si rifà con:

```bash
python3 scripts/rq2/compare_budget_change.py
```

## 7. Limiti e stato

- **Nessuna risposta è stata generata**: di conseguenza nessun risultato, nessuna
  metrica e nessuna conclusione. Le conclusioni delle prove precedenti **non si
  trasferiscono** a questa configurazione.
- Le architetture di uno stesso scenario non sono più confrontate a parità di
  spazio: la differenza di massa del contesto va riportata insieme a qualunque
  risultato.
- Nessuna replica prevista: resterebbe una sola esecuzione per cella, sette
  domande per cella.
- Le annotazioni di SC02, SC03 e SC04 restano in bozza e non approvate.
- Il protocollo resta **non congelato**.

**Prossimo passo.** Decidere se autorizzare la generazione. Sarebbero **49
chiamate di risposta**, non 70:

| Scenario | Da generare | Riusabile senza rigenerare |
|---|---|---|
| SC02 | T, F — **14** | FULL_HISTORY (prompt identico) |
| SC03 | F, U — **14** | FULL_HISTORY (prompt identico) |
| SC04 | T, U, G — **21** | FULL_HISTORY (prompt identico) |
| SC05 | **0** | tutto: T, U, GER e FULL_HISTORY hanno contesti identici a quelli già eseguiti |
| | **49** | |

Il riuso vale per il *prompt*, che è identico: resta comunque un'esecuzione
diversa e va dichiarata come tale. Per SC04 il FULL_HISTORY riusabile è quello
della prima prova, mai rigenerato nella correzione — la stessa avvertenza già
registrata in `INVENTARIO.md` §5.
