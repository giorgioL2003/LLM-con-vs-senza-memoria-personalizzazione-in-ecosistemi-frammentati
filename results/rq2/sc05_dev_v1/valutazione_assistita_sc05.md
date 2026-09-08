# SC05 — valutazione assistita delle 21 risposte (revisione 1)

> **Superata da `valutazione_assistita_sc05_rev2.md`.** Conservata com'era.
> Contiene due imprecisioni numeriche e alcune attribuzioni riviste: l'elenco
> delle differenze è in fondo alla revisione 2.

**Giudizi proposti, non approvati.** Questa è una lettura fatta confrontando
ogni risposta con il **contesto che ha davvero ricevuto** e con i fatti
obbligatori dell'annotazione `sc05-rq2-ger-0.2`. I campi manuali di
`annotation_template_sc05.jsonl` restano tutti `null`: l'approvazione dei
giudizi è un passaggio separato e non è compresa nell'autorizzazione alle
chiamate.

Una sola esecuzione, sette domande, nessuna replica: **osservazioni di sviluppo,
non una dimostrazione che una architettura sia migliore dell'altra.**

La presenza di un'evidenza è stata giudicata **leggendo il testo** delle righe di
contesto, non la corrispondenza degli identificatori sorgente.

## Quadro d'insieme (proposto)

| | completa | parziale | errata | astensione corretta | uso di info obsolete | affermazioni non supportate |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| **U** | 2 | 2 | 2 | 1 | **0** | 2 |
| **GER** | 1 | 3 | 2 | 1 | **0** | 3 |
| **FULL_HISTORY** | 6 | 0 | 0 | 1 | **0** | 0 |

**Nessuna delle 21 risposte ha usato informazione obsoleta.** In particolare
nessuna ha presentato la verifica del registro del bilanciatore come ancora
aperta, né SRV-12 come server esposto attuale: la catena di supersessione
costruita da U ha funzionato.

## Domanda per domanda

### SC05-Q1 — obiettivo del caso

| | classe proposta | evidenze necessarie nel contesto | note |
|---|---|---|---|
| U | **parziale** | obiettivo (a) sì (`M002`); obiettivo (b) solo dentro `M041`, formulato come già soddisfatto | risponde con il solo obiettivo (a) |
| GER | **parziale** | idem | idem |
| FULL_HISTORY | **completa** | entrambi | — |

**Origine dell'errore: gestione**, con una parte di risposta. Nella prova reale
U ha trattato «il portale è tornato in servizio… soddisfacendo l'obiettivo di
ripristino senza interruzioni» (`SC05-M041`, sessione 9) come **UPDATE**
dell'obiettivo dichiarato nella sessione 1 (`SC05-M003`, ora `superato`). Con una
domanda sullo stato corrente, l'obiettivo (b) non è più leggibile come obiettivo:
resta solo dentro l'enunciato che ne dichiara il compimento.

→ **Caso ambiguo da leggere di persona**: se `M041` conti come evidenza presente
dell'obiettivo (b). Se sì, l'origine si sposta su *risposta*; se no, resta
*gestione*. È la questione «eventi o stati» della sezione 10 di `RQ2.md`,
osservata su un caso nuovo.

### SC05-Q2 — server indicato inizialmente e server corretto

| | classe proposta | evidenze necessarie nel contesto | note |
|---|---|---|---|
| U | **completa** | SRV-12 superato (`M008`, stato `superato`) **e** SRV-14 corretto (`M018`) | «Inizialmente indicato: SRV-12. Dopo la revisione, risulta corretto: SRV-14.» |
| GER | **parziale** | SRV-12 superato sì; **SRV-14 assente dal contesto** | dichiara esplicitamente: «Il contesto non specifica quale sia il server corretto» |
| FULL_HISTORY | **completa** | entrambe | — |

**Origine dell'errore per GER: retrieval.** È il caso più netto della prova ed è
interamente spiegato dalla traccia: la quota dell'archivio (100 token) ha tenuto
`M008` (30) e `M020` (53), e `M018` (37, rango 5) non ci entrava più; la fase 2
aveva solo 24 token di residuo. U, con un budget unico da 200, prende gli stessi
quattro elementi **più** `M018` e chiude a 187 token. La metà riservata alla
memoria recente era andata a 97 token di voci sulla revisione delle regole di
esportazione e sui backup, che con questa domanda non c'entrano.

GER non inventa: dichiara ciò che non ha. La risposta è prudente e sbagliata per
difetto, non per eccesso.

### SC05-Q3 — verifiche ancora aperte

| | classe proposta | evidenze necessarie nel contesto | note |
|---|---|---|---|
| U | **errata** | `M040` (la revisione ancora aperta) **assente** | elenca come «aperte» l'obiettivo del caso e il vettore delle credenziali, che non sono verifiche |
| GER | **errata** | idem | stessa risposta nella sostanza |
| FULL_HISTORY | **completa** | — | «Resta aperta soltanto la revisione delle regole di esportazione su SRV-14» |

**Origine dell'errore: retrieval** per entrambe. `M040` è in memoria, attiva e
corretta, ma non entra nel contesto. Affermazioni non supportate in entrambe:
presentare l'obiettivo del caso e il punto non determinato come *verifiche
aperte* è un'inferenza che il contesto non autorizza. Nessuna delle due ha
riportato aperta la verifica del bilanciatore: **l'informazione obsoleta è stata
evitata.**

### SC05-Q4 — la domanda a due livelli

| | classe proposta | evidenze necessarie nel contesto | note |
|---|---|---|---|
| U | **parziale** | vincolo sì (`M004`); revisione aperta **no** | dichiara di non poter indicare le verifiche aperte e risponde correttamente sul vincolo |
| GER | **parziale**, con **affermazione non supportata** | vincolo sì (`M004`); revisione aperta **no** | «non risultano verifiche pendenti indicate»: il contesto non lo dice |
| FULL_HISTORY | **completa** | entrambe | — |

**Origine dell'errore: retrieval** per entrambe; per GER si aggiunge *risposta*.
La metà d'archivio ha funzionato — il vincolo della sessione 1 è nel contesto di
tutte e due — ma la metà recente non ha portato `M040` in nessuna delle due.
Qui la differenza fra le due modalità non è la copertura, è la prudenza: U
dichiara il vuoto, GER lo colma con una conclusione che il contesto non sostiene.

### SC05-Q5 — verifiche completate

| | classe proposta | evidenze necessarie nel contesto | note |
|---|---|---|---|
| U | **errata** | **nessuna** delle due verifiche | presenta `M031` (coordinate bancarie non coinvolte) come una verifica completata |
| GER | **errata** | **nessuna** delle due | dichiara l'insufficienza, ma chiama anche lei «verifica» ciò che non lo è |
| FULL_HISTORY | **completa** | entrambe, con i rispettivi esiti | — |

**Origine dell'errore: retrieval**, ed è il caso previsto. Il limite lessicale
registrato in `review_note` **si è ripresentato con i fatti estratti davvero dal
modello**: per la domanda «Quali verifiche tecniche risultano completate», tutte
e sette le voci delle sessioni 8-9 hanno punteggio **0,0000**, comprese «La
verifica di integrità dei backup è completata» e «La verifica del registro del
bilanciatore è completata». Il TF-IDF non riduce alla radice: «verifiche» non
incontra «verifica», «completate» non incontra «completata». In GER questo si
vede anche nel budget: la quota recente resta a **0 su 100** token e passa
tutta all'archivio.

→ **Caso ambiguo da leggere di persona**: GER dichiara l'insufficienza e U no. Se
si vuole riconoscere quella differenza, GER andrebbe classificata `parziale`
invece che `errata`. Con i criteri approvati entrambe restano errate, perché
nessuna delle due porta un fatto obbligatorio e tutte e due presentano
impropriamente come verifica un'osservazione che non lo è.

### SC05-Q6 — scadenza chiesta dal cliente

Tutte e tre **complete**: «Entro dieci giorni lavorativi». L'evidenza (`M011`) è
nel contesto in tutte le modalità. È l'unica domanda su informazione lontana in
cui la quota d'archivio non ha dovuto competere con nulla.

### SC05-Q7 — informazione mai fornita

Tutte e tre **astensione corretta**, senza inventare nessun fornitore, malgrado
il contesto di U e GER contenesse due voci sui backup. La sovrapposizione
lessicale su «fornitore», che avevo segnalato come possibile difficoltà, non ha
prodotto errori.

## Che cosa mostra questa prova

**Successo tecnico: pieno.** 39 chiamate, 0 errori di esecuzione, 0 errori di
parsing, 0 operazioni rifiutate, 0 risposte vuote, modello effettivamente usato
`claude-sonnet-5` in tutte le chiamate, budget rispettato in tutte e 14 le prove
di retrieval, stato di U identico per U e GER, punteggi identici voce per voce,
sessione raggiunta dichiarata. Il confronto è valido: le due modalità hanno visto
la stessa memoria con lo stesso budget.

**Qualità delle risposte: nessun vantaggio di GER.** Su queste sette domande GER
non fa meglio di U e su Q2 fa **peggio in modo spiegato**: la ripartizione 50/50
ha tolto all'archivio lo spazio che serviva a `M018`. Su Q4 la memoria recente
non ha portato l'attività aperta in nessuna delle due modalità, quindi la
domanda «a due livelli» non ha esercitato il vantaggio che GER avrebbe dovuto
mostrare — non perché la partizione non funzioni, ma perché il ranking non ha
mai fatto salire `M040`.

**Il risultato più netto non è U contro GER.** È che **FULL_HISTORY risponde a
6 domande su 7** con 645 token di cronologia integrale, mentre U ne completa 2 e
GER 1 con 200 token selezionati. Come già su SC04, il collo di bottiglia non è la
disponibilità dell'informazione: è la selezione. Le evidenze mancanti erano tutte
in memoria, corrette e attive.

**Che cosa questa prova non dice.** Non dice che la memoria gerarchica sia
peggiore: dice che *questa* ripartizione, con *questo* budget, *questo* ranking e
*questo* scenario, non ha aiutato e in un caso ha tolto. Sette domande, una
esecuzione, nessuna replica.

## I due casi che devi leggere tu

1. **Q1**: se `SC05-M041` («il portale è tornato in servizio… soddisfacendo
   l'obiettivo di ripristino senza interruzioni») conti come evidenza presente
   del secondo obiettivo. Da questo dipende se l'origine dell'errore è la
   gestione della memoria o la risposta.
2. **Q5**: se la dichiarazione di insufficienza di GER meriti `parziale` invece
   di `errata`, dato che nessuna delle due porta un fatto obbligatorio.

Sul resto i giudizi proposti mi sembrano leggibili direttamente dalle tracce, ma
restano proposte: nessuno è approvato.
