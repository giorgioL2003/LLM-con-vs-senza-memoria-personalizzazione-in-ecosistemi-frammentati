# Confronti dentro lo scenario, con T come baseline

**Che cosa si confronta.** Le strategie di memoria **dentro uno stesso scenario**,
a parità di budget (200 token), stesse domande, stesso oracle, stesso prompt,
stesso modello ed effort. **Non è una classifica generale delle architetture**: i
numeri di SC04 e quelli di SC05 non vanno sommati né mediati, e le due tabelle
non si confrontano fra loro.

**FULL_HISTORY è un controllo diagnostico**, non una strategia in gara: riceve
l'intera cronologia fuori dal budget (SC04 529 token, SC05 645) contro i 200
selezionati dalle altre. Serve a dire se l'informazione era raggiungibile, non a
vincere il confronto.

**Da dove vengono i giudizi.**

| | origine |
|---|---|
| **T** (entrambi gli scenari) | **nuovi**: `valutazione_assistita_t.md`, giudizi **proposti e non approvati** |
| U, G su SC04 | **riportati** da `evaluation_dev_sc04.md` §5.2, aggiornati con i cambiamenti registrati in `sc04_repair_v3/README.md` §5. Non rivalutati qui |
| FULL_HISTORY su SC04 | **riportato** da `evaluation_dev_sc04.md` §5.1–5.2 |
| U, GER, FULL_HISTORY su SC05 | **riportati** da `sc05_dev_v1/valutazione_approvata_sc05.md`, giudizi **approvati dallo studente** il 6 settembre 2026 |

I giudizi delle altre modalità **non sono stati rivisti**. Hanno stati di
approvazione diversi — approvati su SC05, assistiti su SC04, proposti per T — e
la tabella li mescola nella lettura ma non nel loro stato: va detto ogni volta
che si riporta il confronto.

---

## SC04 — T / U / G, più FULL_HISTORY

**Prova di riferimento:** `results/rq2/sc04_repair_v3/` (istruzioni
`u-instructions-0.3`, RQ2.md §9.6) per U e G; `results/rq2/t_ext_v1/` per T.

⚠️ **FULL_HISTORY viene da un'esecuzione diversa**: nella riparazione non è stato
rigenerato e resta quello della prova iniziale (`generation_dev_sc04.jsonl`,
RQ2.md §9.3). Non è un'incompatibilità di configurazione — stesso prompt, stesso
modello, e FULL_HISTORY non dipende dallo stato di U — ma è un'altra esecuzione.

| Domanda | **T** | U | G | FULL_HISTORY *(diagnostico)* |
|---|---|---|---|---|
| **Q1** obiettivo | **completa** | completa | completa | completa |
| **Q2** classificazione + superate | **parziale** — smishing **+ motivo**, nessuna valutazione superata | parziale — smishing + «nessun contatto» superata | parziale — smishing + «spam generico» superata | parziale (completa con il criterio B) |
| **Q3** catena | **parziale** — 1 passaggio su 6, dichiara l'insufficienza | parziale — segnalazione, account, LOGIN-07, RULE-01; manca il collegamento SMS→URL e l'apertura | parziale — catena con le entità giuste, senza dichiarare l'incompletezza | completa |
| **Q4** azioni completate | **completa** — tutte e tre | parziale — solo il blocco del numero | parziale — solo il blocco del numero | completa |
| **Q5** aperto + riepilogo | **completa** — entrambi | parziale — solo il riepilogo | parziale — solo il riepilogo | completa |
| **Q6** punto non determinato | **completa** | completa | completa | completa |
| **Q7** informazione assente | **astensione corretta** | astensione corretta | astensione corretta | astensione corretta |

| | completa | parziale | errata | astensione corretta | obsoleta | non supportata |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| **T** | **4** | 2 | 0 | 1 | **0** | **0** |
| **U** | 2 | 4 | 0 | 1 | 0 | 0 |
| **G** | 2 | 4 | 0 | 1 | 0 | 0 |
| **FULL_HISTORY** *(diagnostico)* | 5 | 1 | 0 | 1 | 0 | 1 (lieve) |

### Che cosa dice questo confronto

**T recupera più contenuto utile di U e G a parità di budget, su questo
scenario.** Il vantaggio è concentrato su Q4 e Q5, e la causa è leggibile negli
artefatti: entrambe le risposte stanno dentro il solo messaggio `SC04-S4-U1`, che
T recupera intero (88 token). In U e G quello stesso messaggio è stato spezzato
in voci separate, e su Q4 le due che contengono la risposta hanno punteggio
TF-IDF **0,0** e restano fuori (`evaluation_dev_sc04.md` §5.3). **La
frammentazione in fatti costa massa lessicale al ranking**: qui il costo si
misura, ed è di due domande su sette.

**Su Q2 le tre modalità sono complementari, nessuna è completa.** T porta il
motivo e nessuna valutazione superata; U porta «nessun contatto»; G porta «spam
generico». Nessuna delle tre copre l'oracle, e mettendole insieme si coprirebbe.

**Su Q3 T è la peggiore delle tre.** Riceve un solo messaggio su sei e dichiara
l'insufficienza. È il caso in cui i messaggi interi costano troppo: 124 token per
un solo passaggio, e il secondo messaggio non entra nel budget. U e G, con unità
più piccole, ne portano di più.

**Sul rischio dell'informazione obsoleta questo scenario non discrimina.** Nessuna
delle tre modalità ha usato informazione superata. Ma il dato **non dice che T sia
al sicuro**: su Q3 T ripete la valutazione iniziale «nessun contatto con il
collegamento», ed è salva solo perché il messaggio originale la qualifica come
*iniziale*. Il rischio si vede su SC05.

---

## SC05 — T / U / GER, più FULL_HISTORY

**Prova di riferimento:** `results/rq2/sc05_dev_v1/` (prova reale del 6 settembre
2026) per U, GER e FULL_HISTORY; `results/rq2/t_ext_v1/` per T. Stessa
esecuzione, stessa configurazione, nessuna avvertenza da aggiungere.

**Ruolo di SC05:** è lo scenario di sviluppo dell'estensione gerarchica — nove
sessioni, sedici messaggi utente, 645 token di cronologia contro 200 di budget —
nato per il confronto U/GER. Non è nella matrice della roadmap e non entra nel
conteggio delle 77 celle. È lo scenario dove la cronologia è più lunga, dove la
distinzione fra memoria recente e archivio ha senso, e dove l'informazione
superata è più lontana dalla sua correzione.

| Domanda | **T** | U | GER | FULL_HISTORY *(diagnostico)* |
|---|---|---|---|---|
| **Q1** obiettivo | **completa** | parziale · *risposta* | parziale · *risposta* | completa |
| **Q2** server corretto | **completa** | completa | parziale · *retrieval* | completa |
| **Q3** verifiche aperte | **errata** · *retrieval* · **obsoleta** | errata · *retrieval* · non supportata | errata · *retrieval* · non supportata | completa |
| **Q4** due livelli | **parziale** · *retrieval* · **obsoleta** | parziale · *retrieval* | parziale · *retrieval* | completa |
| **Q5** verifiche completate | **errata** · *retrieval* | errata · *retrieval* · non supportata | errata · *retrieval* · non supportata | completa |
| **Q6** scadenza cliente | **completa** | completa | completa | completa |
| **Q7** informazione assente | **astensione corretta** | astensione corretta | astensione corretta | astensione corretta |

| | completa | parziale | errata | astensione corretta | obsoleta | non supportata |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| **T** | **3** | 1 | 2 | 1 | **2** | **0** |
| **U** | 2 | 2 | 2 | 1 | 0 | 2 |
| **GER** | 1 | 3 | 2 | 1 | 0 | 2 |
| **FULL_HISTORY** *(diagnostico)* | 6 | 0 | 0 | 1 | 0 | 0 |

### Che cosa dice questo confronto

**T è l'unica modalità che ha usato informazione obsoleta, e lo fa due volte.** È
il primo `obsolete_used: true` di tutto il progetto. Su Q3 e Q4 T presenta la
verifica del registro del bilanciatore come ancora aperta, mentre nella sessione
9 risulta completata:

| | rango su Q3 | punteggio | selezionato |
|---|---:|---:|:-:|
| `SC05-S8-U1` — «restano aperte… il bilanciatore e la revisione» *(superato)* | 2 | 0,2034 | **sì** |
| `SC05-S9-U1` — «il bilanciatore è completata: resta aperta soltanto la revisione» | 16 | **0,0000** | no |

U e GER non commettono questo errore, e non per merito del ranking: la loro
politica di lettura ammette le voci superate **solo** nelle domande storiche, e
Q3 e Q4 non lo sono. **È esattamente ciò che la gestione degli aggiornamenti deve
fare**, e questo confronto lo mostra su dati reali per la prima volta.

**Ma T ha più risposte complete di U e GER.** Su Q1 il messaggio originale
dichiara il secondo obiettivo come obiettivo, mentre in memoria era stato
sostituito dall'enunciato del suo compimento: T lo riporta, U e GER no. Su Q2 T
distingue SRV-12 da SRV-14 **senza avere alcuno stato**, perché la correzione è
scritta dentro il messaggio originale («il server esposto non è `SRV-12` ma
`SRV-14`»). È il rovescio della medaglia di Q3 e Q4: quando la correzione è
esplicita nel testo T se la cava, quando è implicita nella successione delle
sessioni T non ha modo di accorgersene.

**Quando fallisce, T fallisce in modo più prudente.** Su Q5 tutte e tre sbagliano,
ma U e GER aggiungono un'affermazione non supportata — qualificano le coordinate
bancarie non coinvolte come verifica completata — mentre T dichiara
l'insufficienza senza inventare. Il conto delle classi non distingue i due modi
di sbagliare: gli indicatori `obsolete_used` e `unsupported_claim` sì, ed è per
questo che vanno letti insieme alla tabella e non separatamente.

**Il collo di bottiglia resta la selezione, per tutte e quattro.** FULL_HISTORY
risponde a 6 domande su 7 con la stessa memoria e lo stesso modello: nei tre casi
in cui T, U e GER falliscono, l'informazione era nel corpus e non è stata
recuperata.

---

## Sintesi onesta

Le due tabelle dicono cose diverse, e vanno lette separatamente.

| | SC04 | SC05 |
|---|---|---|
| T contro le altre | più complete (4 contro 2 e 2) | più complete (3 contro 2 e 1) |
| ma | peggiore sulla catena (Q3), dove i messaggi interi costano troppo | **unica a usare informazione obsoleta**, due volte |
| causa leggibile | la frammentazione in fatti azzera il punteggio TF-IDF delle voci giuste | T non ha stato temporale: il messaggio superato e quello che lo corregge sono indistinguibili |

**Il confronto non stabilisce un vincitore.** Mostra un compromesso: a 200 token
il messaggio originale porta più contenuto e più contesto lessicale, ma non porta
il tempo. Le architetture con stato pagano in massa lessicale quello che
guadagnano in gestione dell'informazione superata. Con sette domande per cella e
una sola esecuzione, questo è un compromesso **osservato**, non misurato.

**Limiti che valgono per entrambe le tabelle:** una sola esecuzione, nessuna
replica, sette domande per cella, annotazioni degli scenari in bozza, giudizi di
T non approvati, giudizi di SC04 assistiti e giudizi di SC05 approvati solo dallo
studente. Il protocollo resta **non congelato**. SC01, SC02 e SC03 non sono
toccati da questa estensione.
