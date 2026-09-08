# SC05 — chiusura della prova, in parole semplici

Materiale per il confronto con il relatore.

**Prova di sviluppo SC05 eseguita e valutata; giudizi approvati dallo studente. Protocollo finale della tesi non congelato. Prossimo passo: consolidamento delle conoscenze e confronto con il relatore.**

Una sola esecuzione, sette domande, nessuna replica.

## Che cosa mette a confronto U con GER

Le due modalità hanno **la stessa identica memoria**: gli stessi fatti estratti
dalle nove sessioni e lo stesso file di stato costruito da U. Hanno anche lo
stesso budget di contesto (200 token del **conteggio locale del progetto** —
un'unità di misura interna, non il tokenizzatore del modello), lo stesso metodo
di ricerca (TF-IDF/coseno) e le stesse istruzioni di risposta.

**Cambiano due cose, e contano entrambe per quello che finisce nel contesto:**

1. **Come viene spartito lo spazio.** U ordina tutte le voci per pertinenza e
   riempie i 200 token dall'alto, finché ci stanno. GER divide prima le voci in
   *memoria recente* (create nelle ultime due sessioni) e *archivio* (tutte le
   altre), riserva 100 token a ciascun gruppo, e solo dopo lascia che lo spazio
   avanzato passi all'altro gruppo.
2. **L'etichetta di livello.** Ogni riga di GER porta scritto «recente» o
   «archivio». È dentro il budget e costa circa **due token del conteggio
   locale** per riga: spazio che non va al contenuto.

La domanda dell'esperimento è: **riservare metà spazio alle informazioni recenti
aiuta a continuare un lavoro lungo, o toglie spazio a informazioni vecchie ma
decisive?**

## Che cosa è stato eseguito

Uno scenario nuovo di nove sessioni (un caso di sicurezza informatica su un
portale fornitori), sette domande, tre modalità: U, GER e FULL_HISTORY.

**39 chiamate a Claude Sonnet 5**, tutte riuscite: 9 per estrarre i fatti una
sessione alla volta, 9 per costruire la memoria con gli aggiornamenti (nessuna
proposta rifiutata, quindi nessuna riparazione), 21 per le risposte (7 domande ×
3 modalità). Nessun errore, nessuna risposta vuota.

**FULL_HISTORY è un controllo diagnostico, non un concorrente.** Riceve tutta la
cronologia — 645 token contro i 200 selezionati — e non è soggetta al budget:
serve a capire se l'informazione fosse disponibile, non a dire quale
architettura sia migliore.

## Che cosa emerge su questo scenario

**Tecnicamente ha funzionato tutto.** Le due modalità hanno letto la stessa
memoria, con gli stessi punteggi di pertinenza voce per voce; nessuna ha superato
il budget; le tracce dicono per ogni voce perché è entrata o è rimasta fuori.

**GER non ha aiutato.** Giudizi approvati: U risponde in modo completo a 2
domande su 7, GER a 1. In una domanda GER fa peggio in modo spiegabile, in
un'altra è più prudente. Nessuna delle 21 risposte ha usato un'informazione
superata.

**Il collo di bottiglia principale è stato il recupero, ma non spiega tutto.**
In quattro domande su sette l'informazione che serviva era in memoria, corretta e
valida, e non è entrata nel contesto. In **Q1**, invece, l'informazione **era nel
contesto** di entrambe le modalità — dentro la frase che dice che il portale è
tornato in servizio soddisfacendo l'obiettivo di ripristino — e la risposta l'ha
semplicemente **omessa**: lì l'errore è nella risposta, non nel recupero.

Due esempi di fallimento del recupero:

- in una domanda la memoria conteneva la frase che serviva, ma la ricerca le ha
  dato punteggio zero perché la domanda diceva «verifiche completate» e la
  memoria «la verifica è completata»: parole diverse per la stessa cosa;
- in un'altra la voce giusta c'era, era al quinto posto per pertinenza, e non è
  entrata per pochi token.

## Perché GER può peggiorare pur funzionando tecnicamente

Perché **riservare spazio significa anche toglierlo**, e in questa prova si è
visto in un caso preciso.

Nella domanda sul server sbagliato (SC05-Q2), la metà riservata all'archivio ha
tenuto due voci e la terza — l'unica che diceva quale fosse il server corretto —
non ci stava più per pochi token. Nel frattempo la metà riservata alla memoria
recente aveva speso quasi tutto il suo spazio in voci che con quella domanda non
c'entravano. U, che non divide niente, ha preso anche quella voce ed è arrivata
alla risposta completa. GER se n'è accorta e l'ha detto: «il contesto non
specifica quale sia il server corretto».

**È il meccanismo osservato in questo caso, e va raccontato così.** Non dimostra
che una memoria gerarchica danneggi in generale, né che lo faccia ogni volta che
la risposta sta in una informazione vecchia: dice che *qui*, con queste quote e
questo budget, una voce decisiva dell'archivio ha perso la competizione dentro la
propria metà mentre l'altra metà restava mezza vuota di roba utile.

**Il beneficio che la partizione dovrebbe portare — proteggere le informazioni
recenti quando la risposta sta nelle novità — in questa prova non si è
osservato.** Resta un'ipotesi di progetto: la domanda pensata apposta per
richiedere insieme un'informazione recente e una lontana (SC05-Q4) non l'ha
messa alla prova, perché la voce recente che serviva non è entrata nel contesto
di **nessuna** delle due modalità.

Sull'etichetta di livello: costa spazio reale, ma **non è stata la causa** del
peggioramento su Q2. Ricalcolando sulla traccia salvata, anche senza etichetta
quella voce sarebbe rimasta fuori per un token.

## Su «nessuna risposta ha usato informazioni superate»

È vero, ed è un buon segno, ma **da solo non dimostra che la gestione della
memoria sia sempre corretta**. Contano due cose in più:

- **il filtro di lettura**: in sei domande su sette le voci superate non erano
  nemmeno recuperabili, perché il sistema le mostra solo alle domande che parlano
  esplicitamente di cambiamenti. L'unica domanda di quel tipo è stata SC05-Q2;
- **che cosa è stato davvero recuperato**: il rischio si corre solo quando
  un'informazione superata entra nel contesto. È successo appunto in SC05-Q2, e
  lì entrambe le modalità l'hanno trattata correttamente come indicazione
  iniziale.

Quindi: un caso superato bene, e sei casi in cui il problema non si è presentato.

## Perché non si possono trarre conclusioni generali

- **Una sola esecuzione**, senza repliche: le risposte del modello variano anche
  a parità di contesto.
- **Sette domande e uno scenario solo**: troppo poco per una misura.
- **I parametri non sono tarati**: finestra di due sessioni, metà e metà, budget
  di 200 token sono ipotesi iniziali, non valori scelti dopo una prova.
- **GER eredita i limiti di ciò su cui poggia**: la ricerca per parole che non
  riconosce singolare e plurale, e la soglia che scarta le voci senza parole in
  comune con la domanda. Diversi fallimenti visti qui sarebbero successi anche a
  U, e infatti sono successi a U.
- **L'oracle dello scenario è stato scritto insieme allo scenario**, e i giudizi
  sono approvati dallo studente per questa prova, non dal relatore.

Quello che questa prova sostiene è: *su SC05, con questi parametri e questa
implementazione, separare memoria recente e archivio non ha migliorato le
risposte e in un caso le ha peggiorate, per un motivo che si legge nelle tracce.*
Non sostiene che una memoria gerarchica sia inutile.

## Prossimo passo

Consolidamento delle conoscenze e confronto con il relatore.
