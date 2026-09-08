# SC05 — valutazione assistita, revisione 2 (giudizi proposti)

> **Rapporto di riferimento: `valutazione_approvata_sc05.md`.** Questo file
> resta com'era e documenta i giudizi *proposti* prima dell'approvazione.
> Nella versione approvata le classi non cambiano; cambiano l'indicatore delle
> affermazioni non supportate (Q3 e Q5 per U e GER, senza metrica autonoma per
> le attribuzioni improprie) e l'attribuzione dell'errore su Q1.

**Giudizi proposti, non approvati.** I *criteri* sono stati approvati dallo
studente prima della prova (annotazione `sc05-rq2-ger-0.2`); i **giudizi sulle
singole risposte restano proposte** fino alla sua revisione. I campi manuali di
`annotation_template_sc05.jsonl` restano tutti `null` e non sono stati toccati.

Sostituisce `valutazione_assistita_sc05.md` (revisione 1), che resta nella
cartella. Le differenze sono elencate in fondo.

**Metodo.** Ogni risposta è stata letta insieme al **contesto che ha davvero
ricevuto** e ai fatti obbligatori. La presenza di un'evidenza è giudicata sul
**contenuto** delle righe di contesto: la corrispondenza degli identificatori
sorgente non basta, e in questa prova si è rivelata sbagliata almeno due volte
(vedi «Il falso positivo di provenienza»).

**FULL_HISTORY non è un termine di confronto a parità di budget**: riceve 645
token di cronologia integrale contro i 200 token selezionati di U e GER. Serve a
dire se l'informazione fosse disponibile, non se un'architettura sia migliore.

Classi come in `EXPERIMENT.md` §9.3: *completa* (tutti i fatti obbligatori, senza
contraddizioni), *parziale* (almeno un fatto corretto, ma omette parte della
risposta richiesta), *errata* (contraddice l'oracle, usa informazione obsoleta
come valida, o non risponde alla domanda), *astensione corretta*.

## Tabella dei giudizi proposti

| | U | GER | FULL_HISTORY (diagnostico) |
|---|---|---|---|
| **Q1** obiettivo | parziale | parziale | completa |
| **Q2** server corretto | **completa** | parziale | completa |
| **Q3** verifiche aperte | errata | errata | completa |
| **Q4** due livelli | parziale | parziale | completa |
| **Q5** verifiche completate | errata | errata | completa |
| **Q6** scadenza cliente | completa | completa | completa |
| **Q7** informazione assente | astensione corretta | astensione corretta | astensione corretta |

| | completa | parziale | errata | astensione corretta | affermazioni non supportate | attribuzioni improprie | uso di info obsoleta |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| **U** | 2 | 2 | 2 | 1 | 1 | 2 | 0 |
| **GER** | 1 | 3 | 2 | 1 | 1 | 2 | 0 |
| **FULL_HISTORY** | 6 | 0 | 0 | 1 | 0 | 0 | 0 |

I conteggi delle prime quattro colonne fanno 7 per riga e coincidono con i
giudizi individuali qui sotto.

## Domanda per domanda

### SC05-Q1 — obiettivo dichiarato del caso · U parziale, GER parziale

Fatti obbligatori: (a) stabilire quali dati dei fornitori siano stati esposti;
(b) riportare il portale in servizio senza interruzioni per i fornitori attivi.

Contesto (U 188 token, GER 187): entrambe hanno `SC05-M002` («Obiettivo del caso:
stabilire quali dati dei fornitori siano stati esposti») e `SC05-M041` («Il
portale è tornato in servizio per i fornitori attivi lunedì mattina,
**soddisfacendo l'obiettivo di ripristino senza interruzioni**»).

**`M041` contiene il secondo obiettivo in misura sufficiente per rispondere.**
Nomina l'obiettivo («l'obiettivo di ripristino senza interruzioni») e i
destinatari («per i fornitori attivi»): un lettore può ricavarne che il secondo
obiettivo del caso era riportare il portale in servizio senza interruzioni per i
fornitori attivi, e che risulta raggiunto. Manca la forma dichiarativa, non il
contenuto.

Le tre cose vanno tenute distinte:

| | esito |
|---|---|
| **contenuto recuperato** | **sì**: il contenuto dell'obiettivo (b) è nel contesto di U e di GER, dentro `M041` |
| **correttezza della trasformazione in memoria** | **discutibile ma non distruttiva**: U ha applicato un UPDATE che sostituisce l'obiettivo (`SC05-M003`, ora `superato`) con l'enunciato del suo compimento. Il contenuto sopravvive, si perde il *tipo* dell'affermazione: l'obiettivo non è più leggibile come obiettivo, ma come risultato |
| **omissione nella risposta** | **sì**: il materiale c'era e non è stato usato. Entrambe le risposte si fermano all'obiettivo (a) |

**Origine dell'errore: risposta**, con concausa nella **gestione** (la
trasformazione rende il secondo obiettivo meno riconoscibile come tale). Questa
è una revisione rispetto alla revisione 1, che attribuiva l'errore
principalmente alla gestione.

*Nota sull'indicatore automatico:* la scheda segna
`obiettivo-ritorno-servizio: fact_in_context_by_provenance = true`, ma per la
ragione sbagliata — perché nel contesto ci sono voci che citano `SC05-S1-U1`,
non perché ci sia `SC05-M003`. Il contenuto c'è davvero, ma attraverso un
messaggio diverso (`SC05-S9-U2`) da quello annotato.

### SC05-Q2 — server iniziale e server corretto · U completa, GER parziale

Contesto **U (177 token, 5 elementi)**: `M008` (SRV-12, stato `superato`),
`M020` (l'indicazione di SRV-12 era errata), `M035`, `M040`, **`M018`**
(«L'accesso anomalo non è arrivato da SRV-12, ma dal server esposto SRV-14»).
Entrambi i fatti obbligatori sono presenti nel contenuto → **completa**.

Contesto **GER (176 token, 5 elementi)**: `M008`, `M020`, `M035`, `M040`, `M032`.
**Il nome SRV-14 compare nel contesto di GER**, dentro `M035` e `M040` («La
revisione delle regole di esportazione su SRV-14…»), ma **manca l'evidenza che
identifica SRV-14 come il server esposto corretto**, cioè `M018`. Le due voci che
nominano SRV-14 parlano di un'altra cosa: un'attività di revisione, non
l'attribuzione dell'accesso anomalo. La risposta di GER lo dice con esattezza:
«il contesto non specifica quale sia il server corretto» → **parziale**, prudente,
senza inventare.

**Origine dell'errore: retrieval.** Il meccanismo è leggibile nella traccia:

- quota archivio 100 token: `M008` (30) + `M020` (53) = 83; `M018` chiede 37 e
  non entra → il livello archivio si chiude al rango 5;
- quota recente 100 token: `M035` (30) + `M040` (37) + `M032` (26) = 93, tutti
  irrilevanti per questa domanda;
- fase 2: residuo 24 token, `M018` ne chiede 37 → resta fuori.

U, con budget unico da 200, prende gli stessi quattro elementi **più** `M018` e
si ferma a 177 token.

*Controfattuale calcolato sulla traccia salvata (nessuna riesecuzione):* con le
stesse quote 50/50 ma il costo di riga di U (cioè senza l'etichetta di livello,
che vale ~2 token per riga), `M018` resterebbe fuori lo stesso, per **un solo
token** (ne chiede 35, il residuo sarebbe 34). **La causa decisiva è la
ripartizione 50/50, non l'etichetta.**

*Il falso positivo di provenienza:* la scheda segna per GER
`server-esposto-corretto: fact_in_context_by_provenance = true`, perché `M020`
cita `SC05-S4-U1`, lo stesso messaggio di `M018`. Ma `M020` **non nomina SRV-14**.
È la conferma su dati reali che i campi `*_by_provenance` non misurano il
contenuto — qui proprio nel caso che decide il confronto.

### SC05-Q3 — verifiche ancora aperte · U errata, GER errata

Fatto obbligatorio: la revisione delle regole di esportazione su SRV-14 è
l'unica verifica ancora aperta (`M040`).

`M040` **non è nel contesto di nessuna delle due**. Nei due contesti non c'è
alcuna voce che parli di verifiche: U ha `M001, M002, M006, M016, M027, M024`,
GER `M001, M002, M006, M016, M027, M041`.

Entrambe rispondono elencando come «aperte» l'obiettivo del caso e il vettore
delle credenziali. Nessun fatto obbligatorio, e la domanda non riceve risposta →
**errata** per entrambe.

- **affermazione non supportata** (una per modalità): «obiettivo del caso non
  ancora concluso» — il contesto enuncia l'obiettivo, non dice che sia aperto;
- **attribuzione impropria** (una per modalità): l'obiettivo e un punto non
  determinato vengono presentati come *verifiche*, che non sono.

**Origine dell'errore: retrieval** (evidenza in memoria, attiva e corretta, ma
non recuperata), con una componente di **risposta**: entrambe elencano invece di
dichiarare l'insufficienza.

### SC05-Q4 — verifiche aperte e vincolo sul rapporto · U parziale, GER parziale

Fatti obbligatori: (a) la revisione su SRV-14 resta da completare; (b) il
rapporto non può essere condiviso prima della chiusura formale del caso.

Entrambe hanno `M004` (il vincolo) e **nessuna** ha `M040`. Entrambe rispondono
correttamente sulla seconda metà → **parziale** per entrambe.

**Revisione rispetto alla revisione 1: a GER non va attribuita un'affermazione
non supportata.** La frase intera è: «*In base al contesto*, la verifica di
integrità dei backup risulta completata e con esito regolare, quindi **non
risultano verifiche pendenti indicate**». È un enunciato su ciò che il contesto
indica, non sull'esistenza di verifiche pendenti nel mondo, ed è **vero**: nel
contesto di GER nessuna verifica pendente è indicata. Il nesso «quindi» è debole
— dal fatto che una verifica sia conclusa non segue che non ve ne siano altre —
ma la conclusione, come è scritta, resta dentro il contesto.

Resta una differenza di prudenza, non di correttezza: U dice «il contesto non
contiene informazioni sufficienti per indicare quali verifiche restino da
completare», che è meno equivocabile.

**Origine dell'errore: retrieval** per entrambe. La metà d'archivio ha fatto il
suo lavoro — il vincolo della sessione 1 è nel contesto di tutte e due — mentre
la metà recente non ha portato `M040` in nessuna delle due: il ranking non lo ha
mai fatto salire abbastanza.

### SC05-Q5 — verifiche completate · U errata, GER errata

Fatti obbligatori: verifica dei backup completata con esito regolare; verifica
del registro del bilanciatore completata, con una sola sessione anomala.

**Nessuno dei due è nel contesto di nessuna delle due modalità.** Applicando il
criterio approvato — si guarda quali fatti obbligatori sono presenti — nessuna
delle due può essere completa o parziale: **errata** per entrambe. La
dichiarazione di insufficienza di GER, da sola, non cambia la classe.

Valutate a parte, le affermazioni improprie: **entrambe** presentano `M031` («le
coordinate bancarie non risultano coinvolte nel file prodotto dal modulo di
esportazione») come una *verifica* completata. È un'attribuzione impropria in
tutte e due, non un fatto inventato: il contenuto di `M031` è nel contesto, è la
qualifica di «verifica» a non esserci.

**Origine dell'errore: retrieval**, con una componente di **risposta**
(l'attribuzione impropria). Il meccanismo è la soglia sul punteggio nullo, e il
limite lessicale messo a verbale prima della prova **si è ripresentato con i
fatti estratti davvero dal modello**: per la domanda «Quali verifiche tecniche
risultano completate», tutte e sette le voci delle sessioni 8-9 hanno punteggio
**0,0000** — comprese «La verifica di integrità dei backup è completata» e «La
verifica del registro del bilanciatore è completata». Il TF-IDF non riduce alla
radice: «verifiche» non incontra «verifica», «completate» non incontra
«completata». In GER si vede anche nel budget: la quota recente resta a **0 su
100** token e passa tutta all'archivio.

### SC05-Q6 — scadenza chiesta dal cliente · tutte complete

`M011` è nel contesto di U e di GER con il contenuto giusto, e tutte e tre le
risposte dicono «Entro dieci giorni lavorativi». Nessun errore.

### SC05-Q7 — informazione mai fornita · tutte astensioni corrette

Nessuna delle tre inventa un fornitore, malgrado il contesto di U e GER
contenesse due voci sui backup. La sovrapposizione lessicale su «fornitore»,
segnalata in revisione come possibile difficoltà, non ha prodotto errori.

## Sull'assenza di informazione obsoleta

Nessuna delle 21 risposte usa informazione obsoleta. **Questo però non dipende
soltanto dalla gestione della memoria**, e va detto con precisione: in sei
domande su sette **l'informazione obsoleta non era nemmeno recuperabile**, perché
la politica di lettura di U ammette le voci superate solo nelle domande storiche,
e l'unica domanda storica è Q2.

L'unico caso in cui il rischio è stato davvero esercitato è quindi **Q2**, dove
`M008` (SRV-12, `superato`) e `M035` (`superato`) sono entrati nel contesto di
entrambe le modalità: lì U e GER hanno correttamente presentato SRV-12 come
indicazione iniziale, senza spacciarla per attuale.

Che la catena di supersessione sia stata costruita bene (7 UPDATE applicati, fra
cui la chiusura della verifica del bilanciatore) è vero e verificabile nello
stato; ma il merito dell'assenza di errori nelle risposte va diviso fra la
gestione della memoria e il **filtro della politica di lettura**, che nelle altre
sei domande ha semplicemente tolto di mezzo le voci superate.

## Che cosa cambia rispetto alla revisione 1

| | revisione 1 | revisione 2 | perché |
|---|---|---|---|
| Q4 GER | parziale **+ affermazione non supportata** | parziale, **senza** affermazione non supportata | letta la frase intera: «in base al contesto… non risultano verifiche pendenti *indicate*» è un enunciato sul contesto, ed è vero |
| Q1, origine | gestione (principale) | **risposta** (principale), gestione come concausa | `M041` contiene il secondo obiettivo in misura sufficiente: il materiale c'era e non è stato usato |
| Q2 GER | «SRV-14 assente dal contesto» | «SRV-14 **compare** nel contesto, ma manca l'evidenza che lo identifica come server esposto corretto» | `M035` e `M040` nominano SRV-14 parlando d'altro |
| Q2 U, token | 187 | **177** (M008 28 + M020 51 + M035 28 + M040 35 + M018 35) | conteggio sbagliato nella revisione 1: erano i costi di riga di GER |
| Q2, causa | quote **e** costo dell'etichetta | **quote**; l'etichetta non è decisiva | controfattuale sulla traccia: senza etichetta `M018` resterebbe fuori per 1 token |
| affermazioni non supportate | U 2, GER 3 | U 1, GER 1 (più 2 «attribuzioni improprie» per parte) | separate le affermazioni non sostenute dalle qualifiche improprie |
| info obsoleta | attribuita alla gestione della memoria | attribuita **anche** al filtro della politica di lettura | in 6 domande su 7 le voci superate non erano leggibili |
| FULL_HISTORY | presentato accanto a U e GER | presentato come **controllo diagnostico fuori budget** (645 token contro 200) | non è un confronto a parità di budget |

Le classi delle 21 risposte **non cambiano** rispetto alla revisione 1: cambiano
motivazioni, origini degli errori e conteggi degli indicatori.

## I punti che restano da decidere

1. **Q1 — se accettare che `M041` valga come evidenza del secondo obiettivo.**
   La proposta è sì, e con essa l'origine dell'errore diventa *risposta*. Se lo
   consideri insufficiente, l'origine torna a *gestione* e cambia la diagnosi di
   due righe su ventuno. È la stessa questione «eventi o stati» già aperta per U.
2. **Q5 — se una risposta che dichiara l'insufficienza, quando l'evidenza
   obbligatoria non è stata recuperata, debba restare `errata`.**
   `EXPERIMENT.md` §9.3 definisce l'astensione corretta come dichiarare
   l'indisponibilità «quando le evidenze obbligatorie non sono accessibili *nella
   condizione eseguita*»: presa alla lettera, un'astensione pulita su Q5 potrebbe
   ricadere lì. Qui la questione non cambia il giudizio — nessuna delle due
   risposte è un'astensione pulita, entrambe aggiungono un'attribuzione impropria
   — ma la definizione va chiarita prima di annotare, perché riguarda tutto RQ2.
3. **Q3 — se «attribuzione impropria» debba essere un indicatore a sé** o vada
   ricondotta a «informazione inventata» di `EXPERIMENT.md` §9.4. Qui le ho tenute
   separate perché i fatti citati erano nel contesto: era sbagliata la qualifica,
   non il fatto.
