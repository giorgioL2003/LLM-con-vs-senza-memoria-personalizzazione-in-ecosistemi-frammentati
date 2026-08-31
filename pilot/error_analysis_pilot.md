# Analisi causale dei fallimenti del pilot

**Stato:** risultati del pilot, non conclusioni finali.  
**Ambito:** step 3 - origine dei due problemi emersi nella valutazione.

Documento generato da `scripts/build_error_analysis.py`; il risultato
machine-readable e' `results/error_analysis_pilot.jsonl`.

Ogni fallimento e' ricondotto alla **prima causa osservabile** nella pipeline,
secondo la sezione 11 di `EXPERIMENT.md`:

1. `reachability` - evidenza irraggiungibile: il perimetro della condizione non contiene le informazioni necessarie;
2. `retrieval` - evidenza raggiungibile ma non recuperata: fallimento del retrieval o del ranking;
3. `answer` - evidenza recuperata ma risposta non corretta: fallimento di lettura, ragionamento o generazione;
4. `benchmark` - domanda o oracle difettosi: ambiguita' o errore nel benchmark;

I due casi analizzati sono gli unici fallimenti del pilot: le altre 54 prove
sono risposte complete o astensioni corrette. Le classificazioni sono quelle
gia' approvate e non vengono riviste qui; questo documento aggiunge soltanto
l'origine dell'errore.

Gli errori sono conservati come risultati reali del pilot: il retriever non e'
stato corretto e la domanda non e' stata modificata.

`FULL_HISTORY` non e' una condizione sperimentale. Compare una sola volta,
come controllo diagnostico del caso SC02-Q6/C2, per distinguere un fallimento
di retrieval da un fallimento di generazione.

## Sintesi

| Caso | Classe | Causa principale | Causa secondaria | Fatto non supportato | Difetto del benchmark |
|---|---|---|---|---|---|
| SC02-Q6/C1 | `incorrect` | `reachability` | `answer` | si | no |
| SC02-Q6/C2 | `partial` | `retrieval` | nessuna | no | no |

## Caso SC02-Q6/C1

**Prima causa osservabile:** reachability - evidenza irraggiungibile: il perimetro della condizione non contiene le informazioni necessarie  
**Causa secondaria:** answer - comportamento di risposta scorretto: il modello non si e' astenuto nonostante il contesto fosse insufficiente  
**Classe della risposta (gia' approvata):** `incorrect`  
**Affermazioni non supportate:** si  
**Uso di informazioni obsolete:** no  
**Difetto del benchmark:** no

### Domanda e oracle

> Quale comportamento deve confermare il test ancora pendente e quale limite temporale deve controllare?

Risposta attesa: Deve confermare che un link di recupero consegnato in ritardo non sia più utilizzabile dopo 15 minuti.

Fatti obbligatori: rifiuto del link oltre il limite; limite di 15 minuti; collegamento con il test ancora pendente

### Traccia

| Passaggio | Valore |
|---|---|
| Evidenze obbligatorie | `SC02-S2-U1`, `SC02-S4-U1` |
| Messaggi accessibili nella condizione | `SC02-S4-U1` |
| Messaggi recuperati (top_k=2) | `SC02-S4-U1` |
| Evidenza raggiungibile | no |
| Retrieval riuscito | non applicabile |
| Evidenze fuori dal perimetro | `SC02-S2-U1` |
| Evidenze accessibili ma non recuperate | nessuno |
| Comportamento atteso | abstention |
| Fatti obbligatori mancanti nella risposta | rifiuto del link oltre il limite; limite di 15 minuti; collegamento corretto con il test ancora pendente |

### Risposta del modello

> Il test pendente deve confermare che l'email di reset password venga effettivamente consegnata all'utente, verificando il limite temporale della sua consegna in ritardo (cioè controllare quanto tempo impiega ad arrivare).

### Motivazione finale

In C1 il perimetro contiene la sola Sessione 4: la regola dei 15 minuti, fissata in Sessione 2, non e' accessibile. La prima causa osservabile e' quindi il perimetro della memoria. A questa si aggiunge una causa secondaria di risposta: le istruzioni chiedevano di dichiarare l'insufficienza del contesto, ma il modello ha risposto ugualmente, reinterpretando il test pendente come una verifica della consegna dell'email e del tempo di arrivo. Nessuno dei due elementi compare nell'evidenza accessibile: da qui `unsupported_claim: true`. La domanda e l'oracle sono corretti e non richiedono modifiche.

## Caso SC02-Q6/C2

**Prima causa osservabile:** retrieval - evidenza raggiungibile ma non recuperata: fallimento del retrieval o del ranking  
**Causa secondaria:** nessuna  
**Classe della risposta (gia' approvata):** `partial`  
**Affermazioni non supportate:** no  
**Uso di informazioni obsolete:** no  
**Difetto del benchmark:** no

### Domanda e oracle

> Quale comportamento deve confermare il test ancora pendente e quale limite temporale deve controllare?

Risposta attesa: Deve confermare che un link di recupero consegnato in ritardo non sia più utilizzabile dopo 15 minuti.

Fatti obbligatori: rifiuto del link oltre il limite; limite di 15 minuti; collegamento con il test ancora pendente

### Traccia

| Passaggio | Valore |
|---|---|
| Evidenze obbligatorie | `SC02-S2-U1`, `SC02-S4-U1` |
| Messaggi accessibili nella condizione | `SC02-S1-U1`, `SC02-S2-U1`, `SC02-S3-U1`, `SC02-S4-U1` |
| Messaggi recuperati (top_k=2) | `SC02-S4-U1`, `SC02-S3-U1` |
| Evidenza raggiungibile | si |
| Retrieval riuscito | no |
| Evidenze fuori dal perimetro | nessuno |
| Evidenze accessibili ma non recuperate | `SC02-S2-U1` |
| Comportamento atteso | complete_answer |
| Fatti obbligatori mancanti nella risposta | rifiuto del link oltre il limite; limite di 15 minuti |

### Risposta del modello

> Il test ancora pendente deve confermare il comportamento di un'email di recupero consegnata dopo il limite di validità stabilito nella sessione precedente (SC02-S3-U1), verificando quindi cosa accade quando l'email arriva oltre tale scadenza.

### Controllo diagnostico FULL_HISTORY

Controllo diagnostico, non una condizione sperimentale: mostra che con tutta l'evidenza nel contesto il modello risponde in modo completo, quindi il fallimento di C2 non e' un fallimento di generazione.

Contesto ricevuto: `SC02-S1-U1`, `SC02-S2-U1`, `SC02-S3-U1`, `SC02-S4-U1`  
Classe della risposta: `complete`

> Il test pendente deve confermare che un'email di recupero consegnata dopo il limite di validità del token non consenta il cambio password, verificando il limite di scadenza di 15 minuti stabilito per il token.

### Motivazione finale

In C2 tutte e quattro le sessioni sono accessibili e l'evidenza completa e' raggiungibile. Con `top_k=2` il retrieval ha selezionato SC02-S4-U1 e SC02-S3-U1, lasciando fuori SC02-S2-U1, l'unico messaggio che enuncia la regola dei 15 minuti. SC02-S3-U1 rinvia al limite senza ripeterlo ("il limite di validita' stabilito nella sessione precedente"), quindi il contesto recuperato non permetteva di indicare il numero. La risposta riconosce il collegamento con l'email consegnata in ritardo ma omette il rifiuto del link e il limite numerico: e' parziale, non inventata. La prima causa osservabile e' il ranking del retrieval e non esiste una causa secondaria di risposta.

## Sorgenti

| File | SHA-256 |
|---|---|
| `data/scenarios/scenario_02.json` | `97fea57ea1b2d340a2307e01d0462deb6d3da2e5a2ab6b62ccb4e76727c25def` |
| `results/evaluation_pilot.jsonl` | `6a06f8a7e22b4e37edcb420a91ab2af733cdc52a39603bdb060f5d059023d845` |
| `results/generation_inputs.jsonl` | `b2703df19e119fb99d79dfeb73ae2684f23d6ad4cd1f70f287afc55034990f83` |
| `results/generation_pilot.jsonl` | `026e19b0392b9cd0ff343042cd3da80a24f03bab717c99bd7074a20364286500` |
| `results/retrieval_pilot.jsonl` | `957b78a703d4c57a7e2ebc89d212d978c8161934bcd9098dba93a5b9b9bebf9d` |
