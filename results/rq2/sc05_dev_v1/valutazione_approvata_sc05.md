# SC05 — valutazione approvata delle 21 risposte

**Rapporto di riferimento.** I giudizi qui riportati sono **approvati dallo
studente** il 6 settembre 2026, per la sola prova di sviluppo SC05
(`sc05-ger-dev-1`).

L'approvazione **non** è del relatore, **non** congela il protocollo finale della
tesi, **non** rivede retroattivamente le valutazioni degli altri esperimenti e
**non** stabilisce una regola generale sulle astensioni.

| file | ruolo |
|---|---|
| `annotation_template_sc05.jsonl` | template originale, tutti i giudizi `null`, **intatto** |
| `annotation_compilata_sc05.jsonl` | **copia compilata**: classi, indicatori, evidenze, motivazioni, con l'approvazione registrata riga per riga |
| `valutazione_assistita_sc05.md` | revisione 1, conservata |
| `valutazione_assistita_sc05_rev2.md` | revisione 2, i giudizi **proposti**, conservata |
| questo file | i giudizi **approvati** |

**Metodo.** Ogni risposta è stata letta insieme al contesto che ha davvero
ricevuto e ai fatti obbligatori; la presenza di un'evidenza è giudicata sul
**contenuto** delle righe di contesto, non sulla corrispondenza degli
identificatori sorgente. **FULL_HISTORY è un controllo diagnostico**: riceve 645
token di cronologia contro i 200 selezionati di U e GER, quindi non è un
confronto a parità di budget.

## Precisazioni approvate

1. **Q1 (U e GER): parziali.** Il secondo obiettivo è riconoscibile nel contesto
   attraverso `SC05-M041`; l'errore principale è l'**omissione nella risposta**.
   La trasformazione dell'obiettivo nel suo compimento resta una **possibile
   concausa, non una causa dimostrata**.
2. **Q4 (U e GER): parziali.** Per GER la frase «*in base al contesto… non
   risultano verifiche pendenti indicate*», letta per intero, **non** conta come
   affermazione non supportata.
3. **Q5 (U e GER): errate.** Nessuna delle due contiene i fatti obbligatori, e la
   dichiarazione di insufficienza di GER non elimina l'affermazione impropria che
   aggiunge.
4. **Le attribuzioni improprie di Q3 e Q5 sono registrate nell'indicatore
   esistente `unsupported_claim`**, con la spiegazione nelle note: attribuire uno
   stato o una qualifica non sostenuti dal contesto è un'affermazione non
   supportata. **Nessuna metrica autonoma introdotta.**

## Giudizi approvati

| | U | GER | FULL_HISTORY *(diagnostico)* |
|---|---|---|---|
| **Q1** obiettivo | parziale · *risposta* | parziale · *risposta* | completa |
| **Q2** server corretto | **completa** | parziale · *retrieval* | completa |
| **Q3** verifiche aperte | errata · *retrieval* · unsupported | errata · *retrieval* · unsupported | completa |
| **Q4** due livelli | parziale · *retrieval* | parziale · *retrieval* | completa |
| **Q5** verifiche completate | errata · *retrieval* · unsupported | errata · *retrieval* · unsupported | completa |
| **Q6** scadenza cliente | completa | completa | completa |
| **Q7** informazione assente | astensione corretta | astensione corretta | astensione corretta |

### Tabella aggregata

| | completa | parziale | errata | astensione corretta | `unsupported_claim` | `obsolete_used` | astensioni errate |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| **U** | 2 | 2 | 2 | 1 | 2 (Q3, Q5) | 0 | 0 |
| **GER** | 1 | 3 | 2 | 1 | 2 (Q3, Q5) | 0 | 0 |
| **FULL_HISTORY** | 6 | 0 | 0 | 1 | 0 | 0 | 0 |

Le prime quattro colonne fanno 7 per riga. I conteggi sono stati verificati
contando le righe di `annotation_compilata_sc05.jsonl`: coincidono.

Origini degli errori: U — 3 `nessuno`, 3 `retrieval`, 1 `risposta`;
GER — 2 `nessuno`, 4 `retrieval`, 1 `risposta`; FULL_HISTORY — 7 `nessuno`.

## Motivazioni ed evidenze, in breve

**Q1 · parziale in U e GER, origine *risposta*.** Nel contesto di entrambe c'è
`SC05-M002` (primo obiettivo) e `SC05-M041` («il portale è tornato in servizio
per i fornitori attivi lunedì mattina, **soddisfacendo l'obiettivo di ripristino
senza interruzioni**»), che rende riconoscibile il secondo obiettivo. Entrambe
rispondono con il solo primo obiettivo: il materiale c'era e non è stato usato.
Concausa possibile e non dimostrata: in memoria l'obiettivo è stato sostituito
dall'enunciato del suo compimento, quindi si legge come risultato più che come
obiettivo dichiarato.

**Q2 · completa in U, parziale in GER, origine *retrieval*.** U ha sia
`SC05-M008` (SRV-12, stato `superato`) sia `SC05-M018`, che identifica SRV-14
come server esposto. In GER **il nome SRV-14 compare** — dentro `SC05-M035` e
`SC05-M040`, che però parlano della revisione delle regole di esportazione — ma
**manca la voce che lo identifica come server esposto corretto**. La risposta di
GER lo dichiara invece di inventare. Meccanismo leggibile nella traccia: la quota
archivio (100 token) ha tenuto `M008` (30) e `M020` (53), `M018` ne chiedeva 37;
la quota recente aveva speso 93 token in voci estranee alla domanda; il residuo
della seconda fase era 24 token. U, con budget unico da 200, prende anche `M018`
e chiude a 177 token. **Falso positivo di provenienza da segnalare:**
`fact_in_context_by_provenance` risulta `true` per il fatto mancante, perché
`M020` cita lo stesso messaggio sorgente senza esprimerlo.

**Q3 · errata in U e GER, origine *retrieval*, `unsupported_claim`.**
`SC05-M040` è in memoria, attiva e corretta, ma nessuna voce sulle verifiche
entra nel contesto. Entrambe elencano come «aperte» l'obiettivo del caso e il
vettore delle credenziali: attribuiscono all'obiettivo lo stato «non ancora
concluso», che il contesto non dice, e la qualifica di «verifiche» a due elementi
che non lo sono. Componente secondaria di risposta: elencano invece di dichiarare
l'insufficienza.

**Q4 · parziali, origine *retrieval*.** Il vincolo (`SC05-M004`) è nel contesto di
entrambe ed è riportato correttamente; `SC05-M040` manca in entrambe. Nessuna
affermazione non supportata: la frase di GER è un enunciato su ciò che il
contesto indica, ed è vera. Resta annotato, non conteggiato, che il nesso
«quindi» è debole.

**Q5 · errate, origine *retrieval*, `unsupported_claim`.** Nessuno dei due fatti
obbligatori è nel contesto: per questa domanda tutte e sette le voci delle
sessioni 8-9 hanno punteggio **0,0000**, perché la domanda dice «verifiche…
completate» e la memoria «la verifica… è completata», e il TF-IDF non riduce alla
radice. In GER la quota recente resta a 0 su 100 token. Entrambe qualificano
`SC05-M031` (coordinate bancarie non coinvolte) come verifica completata: è
l'affermazione impropria, e in GER la dichiarazione di insufficienza non la
elimina.

**Q6 · complete.** `SC05-M011` è nel contesto con il contenuto giusto.

**Q7 · astensioni corrette.** L'informazione non è mai stata fornita in nessuna
sessione; nessuna delle tre inventa un fornitore, malgrado due voci sui backup
nel contesto di U e GER.

## Sull'assenza di informazione obsoleta

Nessuna delle 21 risposte usa informazione obsoleta. Il dato **non basta da solo
a dire che la gestione della memoria sia sempre corretta**: in sei domande su
sette le voci superate non erano nemmeno recuperabili, perché la politica di
lettura le ammette solo nelle domande storiche, e l'unica storica è Q2. È lì che
il rischio è stato davvero esercitato — `SC05-M008` e `SC05-M035`, entrambi
`superato`, sono entrati nel contesto di U e di GER — e lì entrambe hanno
presentato SRV-12 come indicazione iniziale, correttamente.

## Stato

Prova di sviluppo SC05 eseguita e valutata; giudizi approvati dallo studente.
Protocollo finale della tesi non congelato. Prossimo passo: consolidamento delle
conoscenze e confronto con il relatore.

Per questa prova non restano decisioni aperte. La questione definitoria sul
significato di «astensione corretta» quando l'evidenza obbligatoria non è stata
recuperata resta **aperta e non decisa**: qui non cambiava il giudizio, e
l'approvazione non stabilisce una regola generale.
