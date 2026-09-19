# Prova reale — 49 risposte senza tetto di token su SC02, SC03 e SC04

**19 settembre 2026.** 49 chiamate al modello, tutte di risposta, **0 errori**,
nessuna risposta vuota, nessun modello di ripiego. `claude-sonnet-5`, effort
`medium`, prompt comune del pilot: identici alle prove precedenti.

**I giudizi di questa scheda sono PROPOSTI e attendono la revisione dello
studente.** Non sono stati copiati dalle valutazioni esistenti: ogni risposta è
stata riletta rispetto alla domanda, all'oracle e al contesto realmente
ricevuto. Dove il mio giudizio coincide con quello precedente, coincide perché
la rilettura è arrivata alla stessa conclusione.

**Una sola generazione per condizione.** Le differenze rispetto alle prove con
`rq2-dev-0.1` sono **osservate, non spiegate**: il modello risponde in modo
diverso anche a parità di contesto, e almeno un caso qui sotto lo dimostra.

## 1. Che cosa è stato eseguito e che cosa è stato riusato

| | Generato ora | Riusato senza rigenerare |
|---|---|---|
| SC02 | T, F — **14** | FULL_HISTORY |
| SC03 | F, U — **14** | FULL_HISTORY |
| SC04 | T, U, G — **21** | FULL_HISTORY |
| SC05 | **0** | T, U, GER, FULL_HISTORY |
| | **49** | **28** |

**Il riuso è stato verificato prima, non assunto.** `check_before_generation.py`
ha confrontato i prompt carattere per carattere: 7/7 identici per ogni cella
riusata, 28 su 28 in totale, con le risposte storiche tutte presenti. La
provenienza di ogni cella riusata è dichiarata riga per riga:

| Cella riusata | Risposte da | Avvertenza |
|---|---|---|
| SC02 FULL_HISTORY | `results/rq2/generation_dev_sc02.jsonl` | stessa prova di T/F storici |
| SC03 FULL_HISTORY | `results/rq2/generation_dev_sc03.jsonl` | prima versione di SC03 |
| SC04 FULL_HISTORY | `results/rq2/generation_dev_sc04.jsonl` | **prova SC04 iniziale**, mai rigenerata nella correzione (`INVENTARIO.md` §5) |
| SC05 T | `results/rq2/t_ext_v1/generation_dev_t_sc05.jsonl` | estensione T dell'8 settembre |
| SC05 U, GER, FULL_HISTORY | `results/rq2/sc05_dev_v1/generation_dev_sc05.jsonl` | prova del 6 settembre, giudizi approvati dallo studente |

Le risposte riusate **mantengono lo stato di approvazione che avevano**: non
sono state rivalutate qui e non ereditano nulla da questa scheda.

## 2. Il confronto, scenario per scenario

Classi secondo `completezza-supporto-1`. «Compl.+supp.» conta solo le risposte
complete **e** supportate dalle conversazioni originali.

| Scen. | Arch. | Token contesto | Compl.+supp. | Parziali | Errate | Astensioni | Migliorate / Peggiorate / Uguali |
|---|:-:|---|:-:|:-:|:-:|:-:|:-:|
| SC02 | T | 160 → 296 | 5 → **5** | 1 → 1 | 0 → 0 | 1 → 1 | 0 / 0 / 7 |
| SC02 | F | 186 → 401 | 2 → **3** | 1 → 1 | 2 → **1** | 1 → 1 | 1 / 0 / 6 |
| SC03 | F | 190 → 701 | 1 → **1** | 4 → 5 | 1 → **0** | 1 → 1 | 1 / 0 / 6 |
| SC03 | U | 185 → 593 | 1 → **1** | 2 → 5 | 3 → **0** | 1 → 1 | 3 / 0 / 4 |
| SC04 | T | 136 → 495 | 4 → **4** | 2 → 2 | 0 → 0 | 1 → 1 | 0 / 0 / 7 |
| SC04 | U | 183 → 690 | 2 → **3** | 4 → 3 | 0 → 0 | 1 → 1 | 1 / 0 / 6 |
| SC04 | G | 179 → 812 | 2 → **3** | 4 → 3 | 0 → 0 | 1 → 1 | 1 / 0 / 6 |

**Nessuna risposta peggiora. Nessuna cella guadagna più di una risposta
completa e supportata.** Il guadagno complessivo è **+3 su 49**: SC02-F,
SC04-U, SC04-G. Il movimento più visibile è un altro: **cinque risposte escono
dalla classe `errata`** e diventano parziali o complete.

### Domande migliorate

| Domanda | Prima → dopo | Il contesto è cambiato? |
|---|---|---|
| SC02-Q3/F | errata → **completa** | **No, identico.** Vedi §4 |
| SC03-Q6/F | errata → parziale | sì, 195 → 723 token |
| SC03-Q4/U | errata → parziale | sì, 175 → 504 token |
| SC03-Q5/U | errata → parziale | sì, 194 → 397 token |
| SC03-Q6/U | errata → parziale | sì, 200 → 663 token |
| SC04-Q5/U | parziale → **completa** | sì, 183 → 706 token |
| SC04-Q5/G | parziale → **completa** | sì, 199 → 836 token |

Su SC03 le tre risposte `errata` di U avevano copertura del contenuto 0/4, 1/3 e
0/4: il contesto non conteneva quasi nulla di richiesto. Con il tetto tolto la
copertura sale e le risposte diventano parziali — corrette in quello che dicono,
ancora incomplete.

## 3. Messaggi sorgente ≠ fatti necessari

Questa è la distinzione che i numeri di provenienza non colgono.

| Scen. | Arch. | Provenienza completa | Fatti richiesti guadagnati nel contenuto |
|---|:-:|---|:-:|
| SC02 | T | 5/7 → 6/7 | +1 |
| SC02 | F | 5/7 → 6/7 | +1 |
| SC03 | F | 6/7 → 6/7 | **+5** |
| SC03 | U | 6/7 → 6/7 | **+7** |
| SC04 | T | 4/7 → 6/7 | +8 |
| SC04 | U | 5/7 → 6/7 | +5 |
| SC04 | G | 5/7 → 6/7 | **+9** |

**Su SC03 la provenienza non si muove e il contenuto guadagna 5 e 7 fatti.**
La conclusione che avevo scritto nella scheda di preparazione — «più contesto
non porta più evidenza» — era sbagliata: la provenienza era già al massimo e non
poteva salire. È stata corretta.

Il caso opposto esiste ed è più insidioso: **14 prove hanno provenienza completa
e fatti richiesti mancanti.** Esempi:

- **SC02-Q6/F**: provenienza completa, ma `SC02-F013` — l'unico fatto che porta
  i «15 minuti» — non è fra i 13 elementi. Il messaggio `SC02-S2-U1` risulta
  citato tramite altri due fatti che quel numero non lo contengono. La risposta
  infatti dice «il limite stabilito nella sessione precedente», senza il numero.
- **SC04-Q4/U**: provenienza completa, fatti nel contenuto **1 su 3**.

## 4. Osservazioni: quali reggono e quali vanno riviste

### Confermate

**1. Il messaggio intero porta più contenuto della memoria frammentata.** Era
l'osservazione principale di `t_ext_v1`. Regge, e ora se ne vede il meccanismo.
Su **SC04-Q4** T risponde completa con tutte e tre le azioni; U ne riporta una
sola e dichiara di non avere il resto; G ne riporta due. Le voci `SC04-M033`
(«RULE-01 è stata rimossa») e `SC04-M034` («la password di ACC-207 è stata
reimpostata alle 08:05») sono **attive nello stato di U** e hanno punteggio
**0,0000** rispetto alla domanda «Quali azioni risultano completate
sull'account e sul numero mittente?»: non condividono nessuna parola con essa.
Il messaggio originale le contiene tutte e tre insieme e viene recuperato
intero. **Togliere il tetto non cambia nulla di tutto questo.**

**2. Il collo di bottiglia di G era l'ancoraggio, non lo spazio.** G guadagna
una risposta e resta indietro rispetto a T su SC04 (3 contro 4). Però
l'espansione relazionale un merito ce l'ha: su **SC04-Q2** G recupera l'arco
`SC04-E005` sullo spam generico, che in U ha punteggio nullo e resta fuori. G
riporta due valutazioni superate su due, U una sola.

**3. Il budget non era la causa degli usi di informazione obsoleta.**
**SC02-Q4/F** resta `errata` con lo stesso identico contesto: `SC02-F017`,
fatto superato, è nel contesto; `SC02-F019`, che lo chiude, no. F non tiene lo
stato temporale. Nessuno spazio in più lo risolve.

### Da rivedere

**4. «Più contesto non porta più evidenza» su SC03: FALSA.** Già corretta sopra
e nella scheda di preparazione.

**5. «Senza tetto T non è più una strategia di recupero»: troppo netta.** Il
retrieval di T viene eseguito sempre — ranking, soglia di pertinenza e regola di
arresto restano quelli di sempre. In 6 prove su 7 in SC02 e 5 su 7 in SC04 non
esclude nulla, e in quelle prove il **contenuto** coincide con FULL_HISTORY, ma
**l'ordine no**: T presenta i messaggi per punteggio, FULL_HISTORY in ordine
cronologico. Il confronto resta definito e misura l'effetto dell'ordine.

**6. La soglia sul punteggio nullo è ora il vero limite, e la prova lo mostra.**
Tutti i fatti richiesti che continuano a mancare hanno punteggio **0,0000** e
sono presenti e attivi nella memoria:

| Fatto mancante | Dove | Rango / punteggio |
|---|---|---|
| famiglia Kelpie (`SC03-F024`) | SC03-Q2, Q6 | 37 / 0,0000 |
| isolamento alle 09:40 (`SC03-F028`) | SC03-Q4 | 33 / 0,0000 |
| verifica accessi cloud (`SC03-F036`, `F037`) | SC03-Q4 | 39, 40 / 0,0000 |
| vettore iniziale non determinato (`SC03-F039`) | SC03-Q5 | 41 (ultimo) / 0,0000 |
| nessuna cifratura osservata (`SC03-F021`) | SC03-Q6 | 33 / 0,0000 |
| RULE-01 rimossa (`SC04-M033`) | SC04-Q4/U | 0,0000 |
| password reimpostata (`SC04-M034`) | SC04-Q4/U | 0,0000 |
| spam generico (`SC04-M010`, `M018`) | SC04-Q2/U | 0,0000 |

**Nessuno di questi può entrare togliendo il budget.** La questione aperta non è
più quanto spazio dare al contesto: è che il ranking lessicale non collega la
domanda al fatto.

**7. Una risposta è cambiata senza che il contesto cambiasse.** **SC02-Q3/F**
passa da `errata` a `completa` con **lo stesso identico contesto**: prima
presentava un solo test come «due verifiche completate», ora lo riporta
correttamente. **Non è un effetto del budget.** È la variabilità fra due
generazioni, ed è la misura di quanto vada preso con cautela ogni altro
cambiamento di questa tabella — compresi i cinque miglioramenti dove il
contesto *è* cambiato.

## 5. Nodi lasciati aperti per la revisione

1. **SC04-Q6, tutte e tre le architetture**: la risposta attesa è che il punto
   resti non determinato. T la dà, ma la introduce con «le informazioni
   disponibili non sono sufficienti». È lo stesso nodo già aperto in
   `sc05_dev_v1`: se una dichiarazione di insufficienza su una domanda
   raggiungibile debba pesare sulla classe. Qui ho classificato `completa`
   perché il contenuto atteso c'è tutto.
2. **SC04-Q2/U**: la risposta presenta come «valutazione superata» un fatto che
   riguarda la memoria e non il caso (un accesso registrato «senza ulteriori
   dettagli», poi precisato con l'IP). L'ho contata come affermazione non
   supportata, classe `parziale`. Va deciso se un'architettura che espone i
   propri stati interni al generatore debba essere penalizzata nella classe.
3. **SC02-Q4/F**: ho valutato la copertura del fatto come 0/1 perché il fatto
   richiede l'esclusività («soltanto») e il contesto non la sostiene. È lo
   stesso criterio della scheda r3 esistente, raggiunto rileggendo il testo del
   fatto; il mio primo giudizio diceva 1/1 ed era più permissivo.
4. **SC04-Q3, tutte e tre**: manca in tutte l'anello esplicito fra UT-207 e
   ACC-207, presente nel contesto in tutte. Le ho classificate parziali. Se si
   accetta il collegamento implicito, diventano tre complete.

## 6. File

| File | Contenuto |
|---|---|
| `generation_dev_budget_per_scenario.jsonl` | le 49 risposte, con modello ed effort registrati |
| `valutazioni_budget_per_scenario.jsonl` | 49 valutazioni proposte, schema `completezza-supporto-1` |
| `giudizi_proposti.json` | i giudizi scritti a mano, con la motivazione di ciascuno |
| `riepilogo_budget_per_scenario.json` | conteggi e metriche per scenario e architettura |
| `confronto_risposte.json` | il confronto prima/dopo, domanda per domanda |
| `controllo_pre_generazione.json` | l'esito dei controlli fatti prima di chiamare il modello |

```bash
python3 scripts/rq2/check_evaluation_consistency.py
```

## 7. Limiti

- **Una sola esecuzione per condizione, sette domande per cella.** Nessuna
  replica. `+3 risposte complete e supportate su 49` è una differenza che una
  seconda esecuzione potrebbe non riprodurre, come mostra SC02-Q3/F.
- Le due prove hanno **configurazioni diverse**: non vanno messe nella stessa
  tabella se non dichiarando il budget di ciascuna.
- Senza tetto le architetture non sono più confrontate a parità di spazio. Il
  contesto di SC04-G arriva a 1092 token contro i 529 di T: **un confronto fra
  architetture che ricevono quantità di testo molto diverse.**
- I giudizi sono **proposti**. Le annotazioni di SC02, SC03 e SC04 restano in
  bozza e non approvate. Il protocollo resta **non congelato**.
