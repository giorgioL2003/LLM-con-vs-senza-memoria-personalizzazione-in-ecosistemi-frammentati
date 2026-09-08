# SC05 — revisione delle domande e proposte di correzione

**Nessuna di queste proposte è stata applicata.** `scenario_05.json` e
`scenario_05_rq2.json` sono invariati e restano dichiarati **bozza non
approvata**. Questo file è materiale per la revisione dello studente: decide lui
che cosa accettare, prima della prima prova reale.

Controllo fatto leggendo i sedici messaggi utente delle nove sessioni, non gli
esiti del retrieval. **Il successo o il fallimento del recupero non è stato usato
come criterio**: una domanda naturale e rispondibile resta com'è anche quando il
retrieval la sbaglia.

## 1. Le sette domande

| | Domanda | Risposta attesa | Evidenze (messaggio) | Livello atteso | Lettura |
|---|---|---|---|---|---|
| **Q1** goal | Qual è l'obiettivo dichiarato del caso ARD-19 sul portale fornitori? | Stabilire quali dati dei fornitori siano stati esposti e riportare il portale in servizio senza interruzioni per i fornitori attivi. | S1-U1 (due fatti) | archivio | corrente |
| **Q2** update_obsolete | Quale server era stato indicato inizialmente come esposto e quale risulta corretto dopo la revisione? | Inizialmente SRV-12; dopo la correzione SRV-14, che ospita il modulo di esportazione delle anagrafiche. | S2-U1, S4-U1 | archivio (voce superata + voce corretta) | **storica** |
| **Q3** pending_activity | Quali verifiche restano aperte in questo momento sul caso ARD-19? | Resta aperta soltanto la revisione delle regole di esportazione su SRV-14, prevista per la settimana prossima. | S9-U1 | recente | corrente |
| **Q4** cross_session_link | Quali verifiche restano da completare e il rapporto può già essere condiviso fuori dal gruppo di risposta? | Resta da completare la revisione delle regole di esportazione su SRV-14; il rapporto non può ancora essere condiviso, perché il vincolo vale fino alla chiusura formale del caso. | S9-U1 **e** S1-U1 | **recente + archivio** | corrente |
| **Q5** completed_activity | Quali verifiche tecniche risultano completate sul caso ARD-19? | Verifica di integrità dei backup, esito regolare; verifica del registro del bilanciatore, una sola sessione anomala. | S8-U1, S9-U1 | recente | corrente |
| **Q6** local_information | Entro quanto tempo il cliente chiede di sapere se i dati dei fornitori sono stati esportati? | Entro dieci giorni lavorativi. | S2-U2 | archivio | corrente |
| **Q7** absent_information | Quale fornitore esterno gestisce i backup del portale? | Le informazioni disponibili non sono sufficienti. | — (astensione) | — | corrente |

L'ambito di lettura è quello che `question_scope()` assegna davvero al testo
della domanda: solo Q2 risulta storica, per la parola «inizialmente». È la
classificazione che serve, perché l'indicazione iniziale SRV-12 vive in una voce
`superato` e senza lettura storica non sarebbe recuperabile.

## 2. Che cosa risulta verificato sul testo delle sessioni

- **Q1.** S1-U1 contiene entrambi gli obiettivi con quelle parole. Nessuna
  sessione successiva li cambia. La domanda chiede l'obiettivo *dichiarato*, e
  il fatto che il portale sia poi tornato in servizio (S9-U2) non lo modifica.
- **Q2.** S2-U1 indica SRV-12; S4-U1 dice «il server esposto non è SRV-12 ma
  SRV-14, che ospita il modulo di esportazione delle anagrafiche». Le due
  evidenze e l'informazione obsoleta dichiarata sono corrette.
- **Q3.** S9-U1 dice «Resta aperta **soltanto** la revisione…»: la parola
  «soltanto» è ciò che rende determinabile «l'unica verifica ancora aperta».
  L'informazione obsoleta dichiarata (il bilanciatore ancora aperto) è quella
  giusta: era aperta in S8, chiusa in S9.
- **Q4.** Le due metà stanno davvero a nove sessioni di distanza: l'attività
  aperta è in S9-U1, il vincolo in S1-U1. Il vincolo è **ancora valido**: la
  parola «chiusura» compare una sola volta in tutto lo scenario, dentro il
  vincolo stesso, e nessun messaggio dichiara il caso chiuso. Il ritorno in
  servizio del portale (S9-U2) non è la chiusura formale del caso.
- **Q5.** S8-U1 e S9-U1 dichiarano completate le due verifiche con i rispettivi
  esiti. La domanda è naturale e ha una risposta determinabile: **resta com'è.**
- **Q6.** S2-U2 dice «entro dieci giorni lavorativi», mai ripetuto altrove.
- **Q7.** Ricerca su tutti e sedici i messaggi: «backup» compare **una sola
  volta**, in S8-U1, come oggetto di una verifica; «fornitore» al singolare,
  «esterno», «azienda», «provider», «gestisce» e «gestito» **non compaiono mai**.
  Nessun soggetto che gestisca i backup è mai stato indicato: l'astensione è la
  risposta corretta.

## 3. Correzioni proposte

### P1 — Q4, informazione obsoleta mancante (proposta: accettare)

*Attuale:* `SC05-Q4.obsolete_information: []`

*Correzione:* `["presentare la verifica del registro del bilanciatore come ancora aperta"]`

*Motivo:* Q4 chiede «quali verifiche restano da completare», la stessa cosa che
chiede Q3, dove quel rischio è già dichiarato. Oggi la stessa risposta
sbagliata sarebbe contata come obsoleta in Q3 e no in Q4. È un'incoerenza fra
due domande che condividono lo stesso fatto obbligatorio, non un adattamento ai
risultati.

### P2 — `required_state_keys` ricalcati sulle chiavi della fixture (proposta: svuotare)

*Attuale:* le sette domande dichiarano chiavi come `vincolo-rapporto`,
`server-esposto`, `verifica-backup`, `revisione-regole-esportazione`.

*Correzione:* portarle a `[]`, oppure riscriverle come **requisiti di
significato** (conservazione dell'evento, correttezza dello stato corrente,
tracciabilità della sostituzione) verificabili quale che sia la chiave prodotta.

*Motivo:* quelle chiavi sono esattamente i `claim_key` che ho scritto io nella
fixture di sviluppo. Nella prova reale i `claim_key` li sceglie il modello e non
coincideranno. La sezione 10 di `RQ2.md` dice già, per SC04, che le attese non
vanno annotate sulle chiavi generate dal modello: «sarebbe adattare il metro al
risultato». Qui il rischio è lo stesso al contrario — il metro è stato scritto
guardando la fixture.

### P3 — Q2, testo di un'evidenza mal formulato (proposta: accettare)

*Attuale:* `server-esposto-iniziale.text` = «il server esposto era stato indicato
in SRV-12»

*Correzione:* «l'indicazione iniziale del server esposto era SRV-12»

*Motivo:* «indicato in SRV-12» si legge male e questo testo serve proprio a
giudicare a mano se il contenuto è nel contesto. Nessun effetto sulla provenienza
né sulla difficoltà.

### P4 — Q7, sovrapposizione lessicale su «fornitore» (proposta: **decisione dello studente**)

*Attuale:* «Quale fornitore esterno gestisce i backup del portale?»

*Alternativa:* «Quale azienda esterna si occupa dei backup del portale?»

*Motivo, in entrambe le direzioni:* nello scenario «fornitori» indica sempre le
aziende registrate nel portale, cioè i soggetti i cui dati sono stati esposti.
La domanda usa «fornitore» in un altro senso (chi eroga un servizio). La
risposta resta determinabile — l'informazione non c'è, quindi si deve astenere —
e l'ambiguità è una difficoltà legittima. **Consiglio di lasciarla com'è**: la
riformulazione renderebbe la domanda più facile, e non c'è un errore da
correggere. Va però messo a verbale che, se il modello risponde parlando dei
fornitori del portale, il caso va classificato leggendo la risposta, non come
astensione mancata.

### P5 — Q5, registrare il limite del recupero lessicale (proposta: **decisione dello studente**)

*Attuale:* `review_note` di Q5 parla solo delle attività di contenimento.

*Aggiunta proposta:* «La domanda dice "verifiche… completate", la memoria dice
"la verifica… è completata": il ranking TF-IDF non riduce alla radice e assegna
punteggio nullo alle voci che servono. È un limite del recupero, già registrato
per SC03 e SC04, **non un difetto della domanda**: la domanda resta invariata.»

*Motivo:* la nota serve a chi leggerà i risultati, perché il fallimento su Q5 non
venga scambiato per una domanda scritta male. La domanda **non** viene cambiata.

## 4. Che cosa richiede una tua decisione

1. **P2**, `required_state_keys`: svuotarle, riscriverle come requisiti di
   significato, o lasciarle sapendo che nella prova reale non combaceranno.
2. **P4**, riformulare o no Q7.
3. **P5**, aggiungere o no la nota sul limite lessicale in Q5.
4. **Q5 e le attività di contenimento**: isolamento di SRV-12, revoca delle
   chiavi API e reimpostazione delle password oggi **non** sono fatti
   obbligatori. Se una risposta le elenca in più, va contata completa o
   imprecisa? La scelta va messa a verbale prima di annotare.
5. P1 e P3 sono correzioni piccole e mi sembrano senza controindicazioni, ma
   restano da approvare come tutte le altre.

## 5. Osservazioni che non sono correzioni

- **La risposta attesa di Q3 coincide parola per parola con il testo del fatto
  `SC05-F029` della fixture.** Non è una fuga dell'oracle nei prompt — nella
  prova reale i fatti li estrae il modello — ma rende gli esiti offline un po'
  più lusinghieri del dovuto: nella verifica offline il ranking confronta la
  domanda con un testo scritto insieme all'oracle. Un motivo in più per non
  leggere i numeri di `results/rq2/ger_dev_v2/` come risultati.
- **Rischio da osservare nella prova reale, non da correggere ora.** In S8 la
  verifica del bilanciatore è aperta e in S9 è completata: perché Q3 e Q4
  funzionino, U deve trattarla come **UPDATE** della stessa affermazione. Se il
  modello la registra come evento nuovo (`ADD`), la vecchia voce resta `attivo` e
  la verifica può essere riportata come ancora aperta. È esattamente la questione
  «eventi o stati» aperta nella sezione 10 di `RQ2.md`: SC05 la mette alla prova,
  e l'esito va osservato, non aggiustato.
- **Refuso in un artefatto precedente.** `results/rq2/sc04_repair_v3/README.md`
  dichiara «istruzioni di U `u-instructions-0.3`, sha `919b6c7ee5e4f53c`», ma il
  registro `scenario_04_update_log.json` della stessa cartella riporta
  `288ea8b51428c651`; `919b6c7ee5e4f53c` è l'impronta delle istruzioni `0.2`. La
  prova è giusta, la riga del README no. Non l'ho toccata: è un artefatto di una
  prova precedente e la correzione spetta a te.
